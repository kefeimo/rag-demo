# Backend FastAPI Reference

Canonical scaffolding conventions and how this project implements them.

---

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py          # exposes __version__ = "1.0.0"
│   ├── main.py              # FastAPI app instance, middleware, startup, all routes
│   ├── config.py            # pydantic-settings Settings class + singleton
│   ├── models.py            # all Pydantic request/response schemas
│   ├── dependencies.py      # ← NOT YET CREATED (see "Future" section below)
│   ├── routers/             # ← NOT YET CREATED (routes still in main.py)
│   │   ├── query.py
│   │   ├── ingest.py
│   │   └── health.py
│   ├── rag/                 # domain logic — pure Python, zero FastAPI imports
│   │   ├── embeddings.py        # EmbeddingProvider (openai / sentence-transformers)
│   │   ├── ingestion.py         # document loading, chunking, ChromaDB write
│   │   ├── retrieval.py         # Retriever — semantic vector search
│   │   ├── hybrid_retrieval.py  # HybridRetriever — BM25 + semantic fusion
│   │   ├── generation.py        # LLM client, generate_answer(), extract_sources()
│   │   ├── query_classifier.py  # classify_query() → 'api'|'how_to'|'troubleshooting'|'general'
│   │   └── utils.py             # ChromaDB client singleton
│   └── utils/
│       ├── logging.py       # logging configuration helpers
│       └── validators.py    # input validation helpers
├── tests/
│   ├── conftest.py
│   ├── test_generation.py
│   ├── test_hybrid_search.py
│   ├── test_ingestion.py
│   ├── test_rag_pipeline.py
│   └── test_retrieval.py
├── requirements.txt
├── .env / .env.example
├── Dockerfile
└── Dockerfile.render        # built from project root (context = ../)
```

---

## Layer 1 — Config (`app/config.py`)

Use `pydantic-settings` `BaseSettings`. It reads environment variables and `.env`
automatically, validates types, and provides a **module-level singleton** imported
everywhere.

### `.env` → `Settings` field mapping

`pydantic-settings` maps `UPPER_SNAKE_CASE` env var names to `lower_snake_case`
Python field names automatically (case-insensitive by default via `case_sensitive = False`).

```
# .env                                    # config.py field
LLM_PROVIDER=openai                  →    llm_provider: str
OPENAI_API_KEY=sk-...                →    openai_api_key: str
OPENAI_EMBEDDING_MODEL=text-emb-3    →    openai_embedding_model: str
CHROMA_PERSIST_DIRECTORY=./data/...  →    chroma_persist_directory: str
CHROMA_COLLECTION_NAME=vcc_docs      →    chroma_collection_name: str
RELEVANCE_THRESHOLD=0.65             →    relevance_threshold: float    # str→float auto-cast
API_PORT=8000                        →    api_port: int                 # str→int auto-cast
API_RELOAD=true                      →    api_reload: bool              # "true"→True auto-cast
CORS_ORIGINS=http://localhost:5173   →    cors_origins: str             # parsed by @property
```

The type casting (`"0.65"` → `float`, `"8000"` → `int`, `"true"` → `bool`) is done
by pydantic automatically — everything in `.env` is a raw string on disk.

Fields that can't be cast raise a `ValidationError` at **import time**, before the
server starts, which is why misconfigured envs fail fast and loudly.

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(default="")
    chroma_persist_directory: str = Field(default="./data/chroma_db")
    cors_origins: str = Field(default="http://localhost:5173")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()   # ← import this everywhere, never re-instantiate
```

**This project adds:** `cors_origins_list` and `ragas_metrics_list` as `@property`
helpers that parse comma-separated env vars into Python lists — avoids repeating
`.split(",")` at call sites.

---

## Layer 2 — Schemas (`app/models.py`)

One `BaseModel` per request body, one per response. FastAPI uses `response_model=`
to validate output and generate OpenAPI docs automatically.

```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    collection: Optional[str] = Field(default=None)   # falls back to env var

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]
    confidence: float = Field(..., ge=0.0, le=1.0)
    model: str
    response_time: Optional[float] = None
    api_version: Optional[str] = None
```

**Rules:**
- Request fields use `Field(...)` (required) or `Field(default=...)` (optional).
- Response fields with `ge=` / `le=` constraints are validated on the way *out*,
  not just on the way in — FastAPI will raise a 500 if your code returns an
  out-of-range value.
- Keep all schemas in `models.py` until the count exceeds ~15; then split by domain.

---

## Layer 3 — App + Routes (`app/main.py`)

### App factory

```python
app = FastAPI(
    title="RAG System API",
    version=__version__,   # imported from app/__init__.py
    docs_url="/docs",
    redoc_url="/redoc",
)
```

### CORS middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins` accepts either a list of exact origins or `["*"]` (wildcard).  
**`["*"]` works fine as long as the frontend does not send credentials** (cookies or
`Authorization` headers via `credentials: "include"`). This project's frontend makes
plain unauthenticated fetch calls, so `CORS_ORIGINS=*` is used in production on Render.

The restriction only matters if you add cookie-based auth or token headers later —
at that point `allow_origins` must list exact origins (e.g. `https://your-app.vercel.app`)
because browsers reject `Access-Control-Allow-Origin: *` combined with credentialed requests.

### Route declaration

```python
@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    ...
```

- `request: QueryRequest` — function argument typed with a Pydantic model; FastAPI treats it as the JSON request body schema. → see [Appendix A](#appendix-a--route-decorator-parameters-in-depth)
- `tags=` groups routes in `/docs`. → see [Appendix A](#appendix-a--route-decorator-parameters-in-depth)
- `response_model=` strips undeclared fields from the response and generates the
  OpenAPI response schema. → see [Appendix A](#appendix-a--route-decorator-parameters-in-depth)
- Always `raise HTTPException(status_code=..., detail=...)` for expected errors;
  let the global handler catch unexpected ones. → see [Appendix A](#appendix-a--route-decorator-parameters-in-depth)

### Why `POST` for `/api/v1/query` (not `GET`)

Semantically a query is a read operation, which would suggest `GET` — but `POST`
is the right choice here for three practical reasons:

1. **Structured JSON body.** `QueryRequest` bundles `query`, `top_k`, and
   `collection` as a typed JSON object. `GET` has no body; the equivalent URL
   params (`?query=...&top_k=3&collection=fastapi_docs`) don't support nested
   objects or lists, and become unwieldy as the schema grows.

2. **URL length limits.** Natural language queries can be long. Browsers and
   proxies typically cap URLs at ~2000 characters. A POST body has no practical
   size limit.

3. **Sensitive input not exposed in logs.** `GET` URLs appear in server access
   logs, browser history, and CDN/proxy logs in plain text. A user's query
   (`"What is my Visa credit limit?"`) appearing in access logs is undesirable.
   POST body content is not logged by default.

The general rule: use `GET` when the URL alone fully and safely describes the
operation (e.g. `/health`). Use `POST` when you have a structured payload,
potentially long input, or content that shouldn't be exposed in URLs.

### Global exception handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

---

## Startup Initialisation

`@app.on_event("startup")` was deprecated in FastAPI 0.93. This project
(FastAPI 0.109.0) has been migrated to the `lifespan` context manager.

The `lifespan` function must be **defined before `FastAPI()` is instantiated**
so it can be passed in as an argument. This is why `KNOWN_COLLECTIONS`,
`hybrid_retrievers`, and `lifespan` all appear above `app = FastAPI(...)` in
`main.py`.

```python
from contextlib import asynccontextmanager

# Must be defined before app = FastAPI(...)
KNOWN_COLLECTIONS = ["fastapi_docs", "vcc_docs"]
hybrid_retrievers: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup — runs once before the server starts accepting requests
    for cname in KNOWN_COLLECTIONS:
        try:
            hr = HybridRetriever(collection_name=cname, auto_classify=True)
            hybrid_retrievers[cname] = hr
        except Exception as e:
            logger.warning(f"Could not init retriever for '{cname}': {e}")
    yield
    # shutdown — release resources here if needed (DB connections, etc.)

app = FastAPI(lifespan=lifespan, ...)
```

Key differences from `@app.on_event`:
- `global hybrid_retrievers` declaration is no longer needed — `lifespan` is
  in the same module scope and mutates the dict in place
- Shutdown logic goes **after** `yield` — the old `on_event("shutdown")` had
  to be a separate function
- No deprecation warning on startup

---

## Dependency Injection (`Depends()`)

Currently the project instantiates `Retriever` and `HybridRetriever` directly
inside route handlers. The idiomatic FastAPI alternative uses `Depends()` so
the framework manages lifetime and makes unit testing easy (override with
`app.dependency_overrides`).

### Pattern to adopt (`app/dependencies.py`)

```python
from functools import lru_cache
from app.rag.hybrid_retrieval import HybridRetriever

@lru_cache          # created once per process
def get_retriever(collection: str = "fastapi_docs") -> HybridRetriever:
    return HybridRetriever(collection_name=collection)
```

```python
# in a router or main.py:
@app.post("/api/v1/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_retriever),
):
    ...
```

```python
# in tests — swap the real retriever for a mock:
app.dependency_overrides[get_retriever] = lambda: MockRetriever()
```

> **TODO:** Create `app/dependencies.py` and migrate the `hybrid_retrievers` dict
> + retriever instantiation out of `main.py`.

---

## Router Splitting (`app/routers/`)

All routes currently live in `main.py`. When the file grows unwieldy, split by
domain using `APIRouter`:

```python
# app/routers/query.py
from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1", tags=["RAG"])

@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest): ...
```

```python
# app/main.py
from app.routers import query, ingest, health

app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(health.router)
```

The `prefix` on the router means you don't repeat `/api/v1` on every route.

> **TODO:** Extract `/api/v1/query`, `/api/v1/ingest`, `/api/v1/ingest/visa-docs`,
> and `/health` into `app/routers/`.

---

## Domain Logic (`app/rag/`)

**Rule:** No `fastapi`, `HTTPException`, or request/response models inside `rag/`.
These modules are plain Python and should be independently testable without
starting a server.

| File | Responsibility |
|---|---|
| `embeddings.py` | `EmbeddingProvider` — wraps OpenAI / sentence-transformers behind a single `.encode()` |
| `ingestion.py` | Load documents, chunk, generate embeddings, write to ChromaDB |
| `retrieval.py` | `Retriever` — semantic vector search via ChromaDB |
| `hybrid_retrieval.py` | `HybridRetriever` — BM25 + semantic fusion with `query_classifier` weights |
| `generation.py` | LLM client factory, `generate_answer()`, `extract_sources()` |
| `query_classifier.py` | `classify_query()` → `'api' \| 'how_to' \| 'troubleshooting' \| 'general'` |
| `utils.py` | ChromaDB client singleton (shared across ingestion and retrieval) |

The RAG pipeline in `main.py` follows this sequence per query:

```
QueryRequest
    → Retriever.retrieve()          # semantic search
    → confidence < 0.65?
        → HybridRetriever.search()  # BM25 + semantic fusion
        → pick higher confidence result
    → Retriever.check_confidence()  # hard reject if still below threshold
    → generate_answer()             # LLM call
    → extract_sources()             # format Source list
→ QueryResponse
```

---

## `__version__` Convention

`app/__init__.py` declares the single source of truth for the version:

```python
__version__ = "1.0.0"
```

Imported in `main.py` as `from app import __version__` and injected into both the
`FastAPI()` constructor and every `QueryResponse` as `api_version`.

---

## Appendix A — Route Decorator Parameters In Depth

### `request: QueryRequest` — request body parameter

**How FastAPI knows it's a body:** When a function argument is typed with a
Pydantic `BaseModel`, FastAPI automatically treats it as the **JSON request body**
— no extra annotation needed. The argument name (`request`) is arbitrary; the type
(`QueryRequest`) is what matters.

```python
async def query_rag(request: QueryRequest):
    #               ^^^^^^^^  ^^^^^^^^^^^^
    #               arg name  Pydantic model → FastAPI reads this from the POST body
    collection = request.collection   # access validated fields directly
    query      = request.query
```

**What FastAPI does with it at runtime:**
1. Reads the raw JSON from the POST body
2. Validates it against `QueryRequest` (required fields present, types correct,
   `min_length`/`max_length`/`ge`/`le` constraints satisfied)
3. If validation fails → automatically returns `422 Unprocessable Entity` with
   field-level error details (the `HTTPValidationError` schema in `/docs`)
4. If validation passes → constructs a `QueryRequest` instance and passes it to
   the handler

**GET routes have no body parameter** — input comes from URL query params
declared as plain typed function arguments instead (e.g. `top_k: int = 5`).

---

### `tags=["RAG"]`

**Where it's defined:** Directly in the route decorator as a plain Python list of
strings. No import needed — it's a built-in FastAPI parameter on `@app.post()`,
`@app.get()`, etc.

**What it does:** Purely a documentation organisational tool. FastAPI passes it to
the OpenAPI schema generator, which groups routes under collapsible sections in
`/docs` (Swagger UI):

```
▶ Health        ← @app.get("/health",  tags=["Health"])
▶ RAG           ← @app.post("/query",  tags=["RAG"])
▶ Admin         ← @app.post("/ingest", tags=["Admin"])
```

Without `tags=`, every route lands in a single default group labelled **"default"**.

`tags=` is a list, so a route can appear in more than one group —
e.g. `tags=["RAG", "Internal"]`. In practice most routes have exactly one tag.

**No runtime effect:** Tags are completely ignored at request time. They don't
affect routing, authentication, validation, or anything else — they only change
how `/docs` renders.

---

### `response_model=QueryResponse`

**Two things happen:**

1. **OpenAPI schema generation.** FastAPI inspects the `QueryResponse` Pydantic
   model and generates the "200 response" schema in `/docs`, so API consumers
   know exactly what fields to expect.

2. **Output filtering and validation at runtime.** Before sending the response,
   FastAPI serialises the return value *through* `QueryResponse`:
   - Extra fields the handler accidentally returns are **silently stripped**
   - Fields with `ge=`/`le=` constraints are **validated on the way out** — if
     `confidence` somehow exceeds `1.0`, FastAPI raises a 500 before the client
     ever sees it
   - Nested models like `List[Source]` are recursively serialised

Without `response_model=`, FastAPI sends back whatever the function returns with
no filtering or validation.

---

### `raise HTTPException` vs the global exception handler

The distinction is **expected errors vs unexpected errors**:

```python
# Expected — you know this can happen, you control the message and status code
if not documents:
    raise HTTPException(status_code=404, detail="No documents found")

# Unexpected — something crashed that shouldn't have
# → falls through to @app.exception_handler(Exception)
# → returns generic {"detail": "Internal server error"}
# → logs the full traceback with exc_info=True
```

`HTTPException` produces a clean JSON response with your chosen status code and
message. The global handler catches everything else, logs it for debugging, but
deliberately returns a **vague** message to the client — internal stack traces
should never leak to users.

---

## Key Patterns Summary

| Concern | Convention | Status |
|---|---|---|
| Config | `pydantic-settings` `BaseSettings` singleton | ✅ Done |
| Schemas | `models.py` — one model per request/response | ✅ Done |
| Domain logic isolation | `rag/` has zero FastAPI imports | ✅ Done |
| Embedding abstraction | `EmbeddingProvider` hides OpenAI vs ST | ✅ Done |
| Startup | `lifespan` context manager | ✅ Done |
| Singleton injection | Module-level dict in `main.py` | ⚠️ Migrate to `Depends()` |
| Route organisation | All routes in `main.py` | ⚠️ Split into `routers/` |
| `dependencies.py` | Not created | ⚠️ Create when adding `Depends()` |
