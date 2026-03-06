# Docker GPU Support

## Current Status
- ✅ GPU acceleration working in **local backend** (8-10x speedup)
- ✅ GPU acceleration working in **Docker** (NVIDIA Container Toolkit enabled)

## Problem (RESOLVED)
Docker containers can now access the host's GPU after installing NVIDIA Container Toolkit. Previously:
- GPU was not accessible
- Fell back to CPU mode
- Queries took 80-125 seconds instead of 12-15 seconds

**Current state:** GPU acceleration enabled in Docker with similar performance to local backend.

## Why This Matters
- **Local backend with GPU:** 12-15 seconds per query
- **Docker backend (CPU only):** 80-125 seconds per query
- **Impact:** 8-10x slower in Docker

## Solution Options

### Option 1: NVIDIA Container Toolkit (Recommended for Production)

**What it does:** Allows Docker containers to access host GPU

## Solution Implementation

### NVIDIA Container Toolkit (✅ IMPLEMENTED)

**What it does:** Allows Docker containers to access host GPU

**Requirements:**
- ✅ NVIDIA GPU with proper drivers installed (Quadro RTX 3000, Driver 595.71, CUDA 13.2)
- ✅ NVIDIA Container Toolkit installed on host (v1.18.2)
- ✅ Docker Compose configuration updated

**Setup Steps Completed:**

1. **✅ Installed NVIDIA Container Toolkit:**
   ```bash
   # Added NVIDIA GPG key and repository
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
     sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   
   # Installed nvidia-container-toolkit
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   
   # Configured Docker runtime
   sudo nvidia-ctk runtime configure --runtime=docker
   
   # Restarted Docker Desktop (on WSL2)
   ```

2. **✅ Updated docker-compose-dev.yml and docker-compose.yml:**
   ```yaml
   services:
     backend:
       # ... existing config ...
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

3. **✅ Verified GPU in Docker:**
   - Log output shows: `Use pytorch device_name: cuda`
   - Sentence transformers using GPU for embeddings
   - Similar performance to local backend

**Results:**
- ✅ GPU accessible in Docker containers
- ✅ Embeddings running on CUDA
- ✅ Expected 8-10x speedup over CPU mode
- ✅ Works with Docker Desktop on WSL2

## Alternative Options (Not Implemented)

### Option 2: Hybrid Approach (Local GPU + Docker CPU)

**What it does:** Run different components based on workload

**Usage:**
- **Development/Evaluation:** Run backend locally with GPU
  ```bash
  cd backend
  source venv/bin/activate
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

- **Production/Deployment:** Run in Docker (CPU mode)
  ```bash
  docker-compose up
  ```

**Pros:**
- ✅ No additional setup needed
- ✅ Simple to understand

**Cons:**
- ❌ Not fully containerized during development
- ❌ Production deployment slower without GPU

### Option 3: Cloud GPU Deployment

**What it does:** Deploy to cloud with GPU support

**Options:**
- AWS ECS with GPU instances
- Google Cloud Run with GPU
- Azure Container Instances with GPU

**Pros:**
- ✅ Scalable
- ✅ Managed infrastructure

**Cons:**
- ❌ Costs money
- ❌ More complex deployment
- ❌ Not for local development

## Benefits

With GPU enabled in Docker:

1. **Performance:**
   - Embeddings: GPU-accelerated (CUDA)
   - Query time: 12-15 seconds (vs 80-125 seconds CPU)
   - 8-10x speedup over CPU mode

2. **Development:**
   - Full containerization with GPU support
   - Consistent performance between local and Docker
   - No need to switch between environments

3. **Production:**
   - Production-ready GPU configuration
   - Works on WSL2, Linux, cloud GPU instances
   - Industry-standard setup

## Testing

To verify GPU is working:

```bash
# Check GPU visibility in container
docker exec rag-backend-dev nvidia-smi

# Check logs for CUDA confirmation
docker logs rag-backend-dev 2>&1 | grep "pytorch device_name"
# Should show: "Use pytorch device_name: cuda"

# Test query performance
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of the Visa Cashback Program?"}'
# Should complete in 12-15 seconds (vs 80-125 seconds on CPU)
```

## Troubleshooting

### ❓ "nvidia-smi shows CUDA 13.x — do I need to downgrade?"

**No. Do not downgrade anything.**

The `CUDA Version` shown in `nvidia-smi` is the **maximum** CUDA version your driver supports — not a requirement. CUDA is fully backward compatible: a driver that supports 13.2 can run binaries compiled for older CUDA versions (11.x, 12.x).

Our stack uses `torch==2.10.0` which ships with its own bundled CUDA 12.8 runtime libraries via pip. The Dockerfile is `python:3.12-slim` (no CUDA base image) — PyTorch brings everything it needs.

```
Driver (CUDA 13.2 max) → runs → PyTorch CUDA 12.8 runtime → ✅ works fine
```

**Confirmed working:** Quadro RTX 3000, Driver 595.71, CUDA 13.2 max, PyTorch CUDA 12.8 — verified March 6, 2026.

---

### ❗ GPU not visible in Docker container

**Symptoms:** `docker exec rag-backend-dev nvidia-smi` fails, or logs show `device_name: cpu`

**Checklist:**
1. **NVIDIA Container Toolkit installed?**
   ```bash
   nvidia-ctk --version
   # Should show: NVIDIA Container Toolkit CLI version 1.x.x
   ```
2. **`nvidia` runtime registered in Docker?**
   ```bash
   docker info | grep -i runtime
   # Should show: Runtimes: ... nvidia ...
   ```
3. **Did you restart Docker after installing the toolkit?**
   - On WSL2: restart Docker Desktop from the Windows system tray
   - On Linux: `sudo systemctl restart docker`
4. **`deploy.resources` block present in docker-compose?**
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

---

### ❗ Verification command fails with image not found or CUDA mismatch

Use an image that matches your PyTorch CUDA runtime (12.8), not an older one:

```bash
# ✅ Correct — matches PyTorch CUDA 12.8 runtime
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi

# ❌ Outdated — CUDA 11.4 / Ubuntu 20.04 (unnecessary)
docker run --rm --gpus all nvidia/cuda:11.4.3-base-ubuntu20.04 nvidia-smi
```

Both will work if the driver is compatible, but use the matching version to avoid confusion.

---

### OpenAI API Key Issues

If you see `401 - Incorrect API key provided` errors:

1. **Check key format in .env file:**
   ```bash
   # ❌ Wrong - long keys without quotes may have parsing issues
   OPENAI_API_KEY=sk-proj-very-long-key-here...
   
   # ✅ Correct - wrap in double quotes
   OPENAI_API_KEY="sk-proj-very-long-key-here..."
   ```

2. **Verify key is loaded in container:**
   ```bash
   docker exec rag-backend-dev printenv | grep OPENAI_API_KEY
   # Should show the full key (164 characters for project keys)
   ```

3. **Test key validity:**
   ```bash
   cd evaluation
   export OPENAI_API_KEY="your-key-here"
   python test_openai_key.py
   ```

4. **Fallback mechanism:**
   - System automatically falls back to GPT4All (CPU) if OpenAI fails
   - Check logs for: "⚠️ OpenAI failed, attempting fallback to GPT4All"
   - Answers will include warning message when using fallback

### GPT4All GPU Issues

- **Issue:** GPT4All requires CUDA 11.0 runtime libraries for GPU support
- **Current:** Only CUDA 12 libraries in Docker, GPT4All runs in CPU mode
- **Impact:** GPT4All fallback is slower (80-125s vs 12-15s with OpenAI)
- **Workaround:** Use OpenAI as primary (fast), GPT4All as fallback (slower but works)

## Notes

- **WSL2 Specifics:** NVIDIA Container Toolkit works on WSL2 with Windows 11
- **Docker Desktop:** Requires restart after installing NVIDIA Container Toolkit
- **GPU Driver:** Requires NVIDIA GPU with compatible drivers (CUDA 11.0+)
- **Fallback:** If GPU unavailable, automatically falls back to CPU mode
- **Embeddings:** Always GPU-accelerated when available (sentence-transformers)
- **LLM:** OpenAI (cloud API, fast) or GPT4All (local, slower fallback)

## References

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker Compose GPU Support](https://docs.docker.com/compose/gpu-support/)
- [WSL2 GPU Support](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

---

**Status:** ✅ CONFIRMED WORKING - GPU acceleration enabled in Docker containers (verified March 6, 2026)  
**Priority:** LOW - Not blocking, system works without it  
**Effort:** MEDIUM - Requires system-level changes  
**Decision:** Document current approach, add GPU Docker as optional enhancement
