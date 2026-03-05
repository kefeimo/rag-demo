# Docker Compose Configurations

This project provides two Docker Compose configurations for different use cases.

## Files

### `docker-compose.yml` - Production Build

**Use for:** Testing production builds, deployment simulation

**Features:**
- ✅ Multi-stage builds for minimal image size
- ✅ Optimized for performance
- ✅ Serves pre-built static files
- ❌ Requires rebuild for code changes

**Usage:**
```bash
# Build and start
docker-compose up --build

# Rebuild after code changes
docker-compose build
docker-compose up
```

### `docker-compose-dev.yml` - Development Mode

**Use for:** Active development, hot reloading

**Features:**
- ✅ Hot reload on file changes (no rebuild needed)
- ✅ Source code mounted as volumes
- ✅ Development servers running
- ✅ Faster iteration cycle
- ⚠️ Larger image size, slower startup

**Usage:**
```bash
# Build and start in development mode
docker-compose -f docker-compose-dev.yml up --build

# Subsequent starts (no rebuild needed)
docker-compose -f docker-compose-dev.yml up

# View logs
docker-compose -f docker-compose-dev.yml logs -f
```

## Key Differences

| Feature | Production (`docker-compose.yml`) | Development (`docker-compose-dev.yml`) |
|---------|-----------------------------------|----------------------------------------|
| **Backend** | Standard run | uvicorn with `--reload` |
| **Frontend** | Built + served | Vite dev server with HMR |
| **Code Changes** | Requires rebuild | Hot reload (instant) |
| **Source Mounts** | No | Yes (volumes) |
| **Build Time** | Fast (after first build) | Slower (installs deps) |
| **Image Size** | Smaller (multi-stage) | Larger (dev deps) |
| **Use Case** | Testing, deployment | Active development |

## Development Workflow

### 1. Initial Setup

```bash
# First time - build images
docker-compose -f docker-compose-dev.yml up --build
```

### 2. Daily Development

```bash
# Start services (reuses existing images)
docker-compose -f docker-compose-dev.yml up

# Make changes to code
# Changes are automatically reflected!
# - Backend: uvicorn auto-reloads on .py changes
# - Frontend: Vite HMR updates browser instantly
```

### 3. After Dependency Changes

```bash
# Rebuild only if you modify requirements.txt or package.json
docker-compose -f docker-compose-dev.yml build
docker-compose -f docker-compose-dev.yml up
```

## Volume Mounts (Development Mode)

### Backend
```yaml
volumes:
  - ./backend/app:/app/app              # Python source code
  - ./data:/app/data                    # Data persistence
  - ~/.cache/gpt4all:/root/.cache/gpt4all  # Model cache
```

### Frontend
```yaml
volumes:
  - ./frontend/src:/app/src             # React components
  - ./frontend/public:/app/public       # Static assets
  - ./frontend/index.html:/app/index.html
  - ./frontend/vite.config.js:/app/vite.config.js
  - /app/node_modules                   # Exclude (use container's)
```

## Testing Production Build

Before deploying, test the production configuration:

```bash
# Build production images
docker-compose build

# Start production containers
docker-compose up

# Test the application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000

# Stop
docker-compose down
```

## Switching Between Modes

```bash
# Stop development containers
docker-compose -f docker-compose-dev.yml down

# Start production containers
docker-compose up -d

# Or vice versa
docker-compose down
docker-compose -f docker-compose-dev.yml up -d
```

## Tips

### Development Mode
- ✅ **Faster iteration:** Code changes reflect immediately
- ✅ **Better debugging:** More verbose logs from dev servers
- ✅ **Source maps:** Easier debugging in browser
- ⚠️ **First startup slower:** Installs all dependencies

### Production Mode
- ✅ **Closer to deployment:** Tests actual build process
- ✅ **Performance testing:** Optimized build with minification
- ✅ **Smaller images:** Multi-stage builds reduce size
- ⚠️ **Slow iteration:** Must rebuild after changes

## Troubleshooting

### Issue: Changes not reflecting in dev mode

**Backend:**
```bash
# Check uvicorn is running with --reload
docker-compose -f docker-compose-dev.yml logs backend | grep reload
```

**Frontend:**
```bash
# Check Vite dev server is running
docker-compose -f docker-compose-dev.yml logs frontend | grep "ready in"
```

### Issue: Port conflicts

```bash
# Check what's using the ports
lsof -ti:8000
lsof -ti:5173

# Kill processes
kill -9 $(lsof -ti:8000)
kill -9 $(lsof -ti:5173)
```

### Issue: Volume permission errors

```bash
# Fix ownership (if needed)
sudo chown -R $USER:$USER ./data
sudo chown -R $USER:$USER ./backend/app
sudo chown -R $USER:$USER ./frontend/src
```

## Recommended Workflow

1. **Start development:** `docker-compose -f docker-compose-dev.yml up`
2. **Code and test:** Edit files, changes auto-reload
3. **Before committing:** Test with `docker-compose up` (production build)
4. **Before deploying:** Verify production build works correctly

---

**Quick Reference:**
```bash
# Development (hot reload)
docker-compose -f docker-compose-dev.yml up

# Production (test build)
docker-compose up --build
```
