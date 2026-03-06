# Docker Deployment Guide

This guide covers running the FastAPI RAG system using Docker Compose.

> 📝 **Note:** For active development with hot reloading, see [DOCKER-COMPOSE.md](docs/DOCKER-COMPOSE.md) for the difference between production and development modes.

## Prerequisites

- Docker 20.10+
- Docker Compose v2.0+
- At least 8GB RAM (for GPT4All model)
- At least 10GB disk space

## GPU Support (WSL2)

GPU acceleration gives **8-10x speedup** (12-15s vs 80-125s per query). The `docker-compose.yml` is already configured — you just need the NVIDIA Container Toolkit installed once.

> 📝 See [DOCKER-GPU.md](docs/DOCKER-GPU.md) for full details and troubleshooting.

### Requirements
- NVIDIA GPU with drivers installed on Windows
- WSL2 (kernel `5.10.43+`)
- Docker Desktop 3.1.0+

### Setup

**1. Add the NVIDIA repository:**
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

**2. Install the toolkit:**
```bash
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
```

**3. Configure the Docker runtime:**
```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

**4. Restart Docker Desktop** from the Windows system tray (right-click → Restart).

**5. Verify GPU is accessible inside containers:**
```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

You should see your GPU listed. The `ERR!` in the `GPU-Util` column is a **known WSL2 cosmetic issue** — it does not affect performance.

**6. Verify the backend is using CUDA after `docker-compose up`:**
```bash
docker logs rag-backend 2>&1 | grep "pytorch device_name"
# Expected: Use pytorch device_name: cuda
```

## Quick Start

### Production Build (Recommended for Testing)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d

# Access the application:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Development Mode (Hot Reload)

```bash
# Build and start with hot reloading
docker-compose -f docker-compose-dev.yml up --build

# Code changes automatically reflect:
# - Backend: Python files reload on save
# - Frontend: Vite HMR updates browser instantly

# See DOCKER-COMPOSE.md for detailed comparison
```

## Services

### Backend (Port 8000)
- **Image**: Python 3.12 slim
- **Framework**: FastAPI + uvicorn
- **LLM**: GPT4All (Mistral 7B)
- **Vector DB**: ChromaDB
- **Health Check**: `/health` endpoint

### Frontend (Port 5173)
- **Image**: Node 20 slim
- **Framework**: React 19 + Vite 7
- **Styling**: Tailwind CSS 4
- **Build**: Multi-stage (build + serve)

## Volume Mounts

```yaml
backend:
  volumes:
    - ./data:/app/data                    # Data persistence
    - ~/.cache/gpt4all:/root/.cache/gpt4all  # Model cache
```

**Important**: GPT4All model (~4GB) is cached to avoid re-downloading on container restart.

## Common Commands

### Start Services
```bash
# Start in foreground
docker-compose up

# Start in background (detached)
docker-compose up -d

# Build and start
docker-compose up --build

# Start specific service
docker-compose up backend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### View Logs
```bash
# All services
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Service Management
```bash
# Restart services
docker-compose restart

# Restart specific service
docker-compose restart backend

# Check status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec backend python -c "import torch; print(torch.__version__)"
```

## Environment Variables

Configure in `docker-compose.yml`:

```yaml
environment:
  # LLM
  - LLM_PROVIDER=gpt4all
  - GPT4ALL_MODEL=mistral-7b-instruct-v0.1.Q4_0.gguf
  
  # RAG
  - CHUNK_SIZE=500
  - CONFIDENCE_THRESHOLD=0.65
  
  # CORS
  - CORS_ORIGINS=http://localhost:5173
```

## Health Checks

Both services have health checks:

```bash
# Check health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:5173
```

## Troubleshooting

### Issue: Port already in use
```bash
# Find process using port
lsof -ti:8000
lsof -ti:5173

# Kill process
kill -9 <PID>
```

### Issue: Backend takes long to start
- First run downloads GPT4All model (~4GB)
- Subsequent runs use cached model
- Wait for "Application startup complete" in logs

### Issue: ChromaDB data lost on restart
- Check volume mount: `./data:/app/data`
- Verify data directory exists
- Check permissions: `chmod -R 755 data/`

### Issue: Out of memory
```bash
# Check container stats
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8GB+
```

### Issue: CORS errors
- Check `CORS_ORIGINS` in docker-compose.yml
- Ensure frontend URL is included
- Default: `http://localhost:5173,http://localhost:3000`

## Development vs Production

### Development (Current)
```yaml
# docker-compose.yml
restart: unless-stopped
```

### Production
```yaml
# docker-compose.prod.yml
restart: always
environment:
  - CORS_ORIGINS=https://yourdomain.com
```

## Data Persistence

### ChromaDB Vector Store
```
./data/chroma_db/
├── chroma.sqlite3
└── [vector data]
```

### Documents
```
./data/documents/
└── [markdown files]
```

## Performance Optimization

### 1. Multi-stage Builds
Frontend uses multi-stage build to reduce image size:
- Build stage: Install deps + build
- Production stage: Only serve built files

### 2. Layer Caching
- Dependencies installed before code copy
- Changes to code don't invalidate dependency layers

### 3. Slim Images
- `python:3.12-slim`: ~140MB (vs 900MB full image)
- `node:20-slim`: ~200MB (vs 1GB full image)

## Security Considerations

### Current Setup (Development)
- No authentication
- HTTP only
- Open CORS

### Production Recommendations
1. **Add Authentication**: API keys, OAuth
2. **Use HTTPS**: Reverse proxy (nginx, Caddy)
3. **Restrict CORS**: Specific domains only
4. **Environment Secrets**: Use Docker secrets
5. **Network Isolation**: Internal network for backend

## Resource Requirements

| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| Backend   | 2 cores | 4GB | 5GB |
| Frontend  | 1 core  | 512MB | 100MB |
| GPT4All Model | - | 4GB | 4GB |
| **Total** | 3+ cores | 8GB+ | 10GB |

## Next Steps

1. ✅ Run `docker-compose up --build`
2. ✅ Access http://localhost:5173
3. ✅ Test query: "What is FastAPI?"
4. ⏳ Deploy to cloud (AWS, GCP, Azure)
5. ⏳ Add monitoring (Prometheus, Grafana)
6. ⏳ Setup CI/CD pipeline

---

**Status**: Stage 1B Complete ✅  
**Last Updated**: March 6, 2026
