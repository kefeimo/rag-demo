# TODO: Evaluation Module Containerization Plan

## Overview

This document describes the design for containerizing the evaluation module in the repository while keeping it separate from the FastAPI backend service.

**Goals:**

- Maintain a clean separation between online serving and offline evaluation
- Avoid dependency conflicts between backend and evaluation environments
- Improve reproducibility
- Provide a transparent Python CLI interface for running evaluation jobs
- Enable easy integration with Docker and CI pipelines

---

## Design Principles

### 1. Separation of Concerns

The repository contains two distinct runtime modes:

| Layer | Purpose |
|---|---|
| Backend (FastAPI) | Online RAG inference service |
| Evaluation module | Offline benchmarking and RAGAS evaluation |

Evaluation should **not** be part of the serving path and should **not** run inside the backend container.

Instead, evaluation will run as a separate containerized batch job.

### 2. Containerized but Not a Service

Evaluation will be implemented as a **Docker job container**, not a persistent service.

**Architecture:**

```
Backend container (FastAPI)
        ↑
Evaluation container (batch job)
        ↑
Python CLI orchestrator
```

**Key characteristics:**

- Runs on demand
- Calls backend API through the Docker network
- Shares the repository data directory

---

## Docker Architecture

### `docker-compose-dev.yml`

Add an `evaluation` service as optional using a [Docker Compose profile](https://docs.docker.com/compose/how-tos/profiles/) so it is **excluded from the default `up` command** and only started on demand:

```yaml
evaluation:
  build:
    context: ./evaluation
  profiles:
    - eval
  volumes:
    - ./evaluation:/app/evaluation
    - ./data:/app/data
  depends_on:
    - backend
  environment:
    - RAG_API_BASE_URL=http://backend:8000
```

The `profiles: [eval]` entry means:

- `docker compose -f docker-compose-dev.yml up` — starts backend + frontend only; evaluation container is **not started**
- `docker compose -f docker-compose-dev.yml --profile eval run --rm evaluation <cmd>` — starts the evaluation container on demand

**Notes:**

- No ports are exposed
- Backend is accessed via `http://backend:8000`
- Evaluation shares the same `data/` directory

---

## Evaluation Container

### `evaluation/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash"]
```

**Purpose:**

- Isolate evaluation dependencies
- Avoid conflicts with backend environment
- Ensure reproducibility across machines

---

## Python CLI for Evaluation

Instead of using a Makefile, evaluation will be orchestrated through a **Python CLI interface**.

**Advantages:**

- Built-in `-h` help support
- Better parameter handling
- Easier extensibility
- Clearer developer UX

### CLI Architecture

**File:** `evaluation/eval_cli.py`

The CLI will:

1. Invoke evaluation scripts
2. Run them inside the evaluation container
3. Pass parameters to each stage

### Help

```bash
python evaluation/eval_cli.py -h
```

Example output:

```
usage: eval_cli.py [-h] {stage1,stage1b,stage2,full}

RAG evaluation pipeline
```

---

## Evaluation Pipeline Stages

| Stage | Script | Purpose |
|---|---|---|
| Stage 1 | `run_ragas_stage1_query.py` | Query the RAG system |
| Stage 1B | `run_ragas_stage1b_generate_references.py` | Generate reference answers |
| Stage 2 | `run_ragas_stage2_eval.py` | Run RAGAS evaluation |

---

## Example CLI Implementation

**Orchestration pattern (`evaluation/eval_cli.py`):**

```python
import argparse
import subprocess

COMPOSE = ["docker", "compose", "-f", "docker-compose-dev.yml"]

def run_container(cmd):
    subprocess.run(COMPOSE + ["run", "--rm", "evaluation"] + cmd, check=True)
```

**Example stage invocation (internal):**

```bash
docker compose run --rm evaluation python run_ragas_stage1_query.py ...
```

---

## CLI Usage Examples

### Run Stage 1

```bash
python evaluation/eval_cli.py stage1 \
  --input data/test_queries/baseline_3.json \
  --output data/results/baseline_3_stage1.json
```

### Run Stage 1B

```bash
python evaluation/eval_cli.py stage1b \
  --input data/results/baseline_3_stage1.json \
  --output data/results/baseline_3_stage1b.json
```

### Run Stage 2

```bash
python evaluation/eval_cli.py stage2 \
  --input data/results/baseline_3_stage1b.json \
  --output data/results/baseline_3_stage2_eval.json
```

### Run Full Pipeline

```bash
python evaluation/eval_cli.py full --dataset baseline_3
```

**Pipeline order:** Stage 1 → Stage 1B → Stage 2

---

## Developer Workflow

**1. Start backend:**

```bash
docker compose -f docker-compose-dev.yml up backend
```

**2. Run evaluation:**

```bash
python evaluation/eval_cli.py full --dataset baseline_3
```

---

## Benefits of This Architecture

| Benefit | Description |
|---|---|
| **Clean Architecture** | Online serving and offline evaluation are fully separated |
| **Reproducibility** | Docker ensures consistent evaluation environments |
| **Developer Experience** | Python CLI provides `-h` help, structured arguments, and easy automation |
| **CI/CD Friendly** | Evaluation can run in CI with a single command: `python evaluation/eval_cli.py full --dataset baseline_3` |

---

## Future Extensions

Potential improvements:

- Dataset registry
- Model comparison runs
- Automated benchmark dashboards
- Scheduled evaluation jobs

**Example future CLI command:**

```bash
python eval_cli.py run baseline_3 --model gpt-4o-mini
```

---

## Final Architecture

```
                 +-------------------+
                 |   FastAPI Backend |
                 |    (RAG Service)  |
                 +---------+---------+
                           ↑
                    HTTP API calls
                           ↑
               +-----------+-----------+
               |   Evaluation Container |
               |    (Batch Execution)   |
               +-----------+-----------+
                           ↑
               Python CLI (eval_cli.py)
```
