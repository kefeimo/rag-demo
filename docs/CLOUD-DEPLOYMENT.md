# Cloud Deployment

## Live URLs

| Layer | URL |
|---|---|
| **Frontend** | https://ai-engineer-coding-exercise.vercel.app/ |
| **Backend** | https://rag-backend-latest-ccmo.onrender.com |
| **Health check** | https://rag-backend-latest-ccmo.onrender.com/health |
| **API docs** | https://rag-backend-latest-ccmo.onrender.com/docs |

---

## Architecture

| Component | Provider | Details |
|---|---|---|
| Frontend (React/Vite) | Vercel | Free tier, global CDN, auto-deploy from GitHub |
| Backend (FastAPI) | Render | Free tier, deployed from Docker Hub image |
| LLM generation | OpenAI | `gpt-3.5-turbo` |
| Embeddings | OpenAI | `text-embedding-3-small` (1536 dims) |
| Vector store | ChromaDB | **Baked into Docker image** — no Render Disk needed |

---

## Docker Images (Docker Hub: `mynameismo`)

| Image | Tag | Size | Notes |
|---|---|---|---|
| `mynameismo/rag-backend` | `latest` | ~2.2 GB | ChromaDB snapshot baked in |
| `mynameismo/rag-frontend` | `latest` | — | Serves pre-built Vite bundle |

### What's baked into the backend image

- `fastapi_docs` — 165 chunks (FastAPI tutorial documentation)

Built from `Dockerfile.render` at the project root (broader build context than `backend/Dockerfile`):

```bash
docker build -f Dockerfile.render -t rag-backend-baked:latest .
docker tag rag-backend-baked:latest mynameismo/rag-backend:latest
docker push mynameismo/rag-backend:latest
```

---

## Render — Backend Configuration

**Deploy method:** Existing image from Docker Hub (`mynameismo/rag-backend:latest`)  
**Port:** `8000`  
**Instance type:** Free

### Environment variables set on Render

| Variable | Value |
|---|---|
| `LLM_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | `sk-...` |
| `OPENAI_MODEL` | `gpt-3.5-turbo` |
| `EMBEDDING_PROVIDER` | `openai` |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma_db` |
| `CHROMA_COLLECTION_NAME` | `fastapi_docs` |
| `CORS_ORIGINS` | `*` |
| `LOG_LEVEL` | `INFO` |
| `RELEVANCE_THRESHOLD` | `0.65` |
| `TOP_K_RESULTS` | `5` |
| `CHUNK_SIZE` | `500` |
| `CHUNK_OVERLAP` | `50` |
| `API_RELOAD` | `false` |

> **Note:** Render env vars are entered as raw values — no surrounding quotes (unlike `backend/.env`).

---

## Vercel — Frontend Configuration

**Deploy method:** GitHub repo (`kefeimo/ai-engineer-coding-exercise`), root directory `frontend/`  
**Framework preset:** Vite (auto-detected)

### Environment variables set on Vercel

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://rag-backend-latest-ccmo.onrender.com` |

Vite bakes `VITE_*` variables into the JS bundle at build time. No runtime config file needed.

---

## Cold Start (Free Tier)

Render's free tier suspends the container after ~15 minutes of inactivity. The first request after suspension takes **~30–60 seconds** to wake up. Subsequent requests are instant.

**For reviewers:** Hit the health URL first, wait for `{"status":"healthy"}`, then use the frontend normally.

```bash
curl https://rag-backend-latest-ccmo.onrender.com/health
```

---

## Re-deploying After Changes

### Backend changes (code or ChromaDB data)

```bash
# Rebuild baked image from project root
docker build -f Dockerfile.render -t rag-backend-baked:latest .
docker tag rag-backend-baked:latest mynameismo/rag-backend:latest
docker push mynameismo/rag-backend:latest
```

Then on Render → **Manual Deploy**.

### Frontend changes

Push to `main` → Vercel auto-redeploys from GitHub.  
If `VITE_API_BASE_URL` changes, update it in Vercel's environment settings and trigger a redeploy.

---

## Verified End-to-End

- [x] `GET /health` → `{"status":"healthy","version":"1.0.0","model":"openai"}`
- [x] `POST /api/v1/query` with `fastapi_docs` collection returns answers with sources
- [x] Frontend loads at deployed URL
- [x] Frontend queries reach the Render backend (CORS headers OK)
- [x] ChromaDB collection intact in baked image: `fastapi_docs` (165 chunks)
| **API key exposure** | Never commit `.env`; use Render/Vercel secret env vars |
| **Embed model download on startup** | If using local embeddings, ensure the model is either baked into the Docker image or cached on the Render disk |

---

## Future Improvements

- Add a dedicated ingestion endpoint or CLI command so docs can be re-ingested without redeploying
- Switch to OpenAI embeddings to eliminate the local model dependency entirely
- Add a `/health` check that also verifies ChromaDB connectivity and collection existence
- Consider a [Render Cron Job](https://render.com/docs/cronjobs) for scheduled re-ingestion when docs change
