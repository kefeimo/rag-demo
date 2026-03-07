# TODO: Deploy to Cloud

## Target Architecture

| Layer | Service |
|---|---|
| Frontend | Vercel |
| Backend (FastAPI) | Render |
| LLM generation | OpenAI API |
| Embeddings | OpenAI API *(recommended)* or local CPU |
| Vector store | ChromaDB persisted on Render disk |

---

## Embedding Strategy Decision

**The key question is not "can CPU do embeddings?" — it is "when do embeddings happen?"**

### ✅ Good: Embed once, reuse

- During deploy/init when data folder is empty
- In a one-time ingestion task (separate job or startup check)
- Manually when docs change

### ❌ Bad: Embed repeatedly

- During every query
- During every container restart without persistence

---

### Why CPU embedding is usually fine for this repo

Embedding is typically:

- A **one-time or occasional ingestion task**
- Much lighter than serving a local generative model
- Tolerable even if it takes a few minutes

The expensive part is **LLM generation**, not embedding. CPU embedding becomes a concern only if:

- The corpus is very large
- Embeddings are recomputed on every deploy
- A very large local embedding model is used
- Ingestion must finish very quickly

For a coding exercise demo, none of those are blockers.

---

### Option A: OpenAI for both chat and embeddings ✅ Recommended (simplest)

- No local embedding model download
- No extra inference dependencies
- Less memory pressure on Render
- More predictable deployment
- Lowest-friction path for reviewers

### Option B: OpenAI for chat, local CPU for embeddings (acceptable)

- Works as long as corpus is not too large
- Ingestion must not be repeated on every container restart
- Requires ensuring `sentence-transformers` and dependencies are installed in the container

---

## Deployment Steps

### Phase 1 — Backend on Render

- [ ] Create a new **Web Service** on [render.com](https://render.com) pointing to the `backend/` directory
- [ ] Add a **Render Disk** and mount it at the Chroma persistence path (e.g., `/app/data/chroma_db`)
- [ ] Set environment variables on Render (see [Environment Variables](#environment-variables) below)
- [ ] Verify the startup command runs ingestion **only when the data folder is empty**, not on every restart
- [ ] Confirm `/health` endpoint returns `{"status": "healthy"}` after deploy

### Phase 2 — Frontend on Vercel

- [ ] Import the repo into [vercel.com](https://vercel.com) and set the root directory to `frontend/`
- [ ] Set `VITE_API_BASE_URL` to the Render backend URL (e.g., `https://your-backend.onrender.com`)
- [ ] Verify CORS on the backend allows the Vercel frontend origin
- [ ] Confirm queries reach the backend from the deployed frontend

### Phase 3 — Smoke Test

- [ ] Run one clean ingestion against the Render deployment
- [ ] Verify subsequent restarts do **not** rebuild embeddings unnecessarily
- [ ] Test the full query flow end-to-end (frontend → backend → OpenAI → response)
- [ ] Check confidence scores and source attribution in the response

---

## Environment Variables

### Render (Backend)

| Variable | Value |
|---|---|
| `LLM_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | `sk-...` |
| `EMBEDDING_PROVIDER` | `openai` *(if switching to OpenAI embeddings)* or `local` |
| `CHROMA_PERSIST_DIR` | `/app/data/chroma_db` *(or wherever Render disk is mounted)* |
| `ALLOWED_ORIGINS` | Vercel frontend URL, e.g. `https://your-app.vercel.app` |

### Vercel (Frontend)

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | Render backend URL, e.g. `https://your-backend.onrender.com` |

---

## Watch Out For

| Risk | Mitigation |
|---|---|
| **Cold start** | Render free tier sleeps after inactivity; use a paid plan or a keep-alive ping for demos |
| **Missing persistent storage** | Mount a Render disk; without it, ChromaDB is wiped on every redeploy |
| **Re-embedding on restart** | Guard ingestion behind an "empty data dir" check |
| **CORS errors** | Set `ALLOWED_ORIGINS` to the exact Vercel URL |
| **API key exposure** | Never commit `.env`; use Render/Vercel secret env vars |
| **Embed model download on startup** | If using local embeddings, ensure the model is either baked into the Docker image or cached on the Render disk |

---

## Future Improvements

- Add a dedicated ingestion endpoint or CLI command so docs can be re-ingested without redeploying
- Switch to OpenAI embeddings to eliminate the local model dependency entirely
- Add a `/health` check that also verifies ChromaDB connectivity and collection existence
- Consider a [Render Cron Job](https://render.com/docs/cronjobs) for scheduled re-ingestion when docs change
