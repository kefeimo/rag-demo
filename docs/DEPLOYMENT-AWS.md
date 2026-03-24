# AWS Deployment Guide

This guide covers deploying the RAG backend to AWS App Runner with Bedrock integration and pre-baked ChromaDB data.

> **Note:** This guide is for **production cloud deployment**. For local development, see [SET-UP-CLAUDE-ON-WSL.md](SET-UP-CLAUDE-ON-WSL.md) which covers using PNNL AI Incubator for faster iteration with access to multiple model providers.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Deployment Steps](#deployment-steps)
- [Configuration](#configuration)
- [Updating Deployment](#updating-deployment)
- [Troubleshooting](#troubleshooting)
- [Cost Estimate](#cost-estimate)

---

## Overview

**Current Deployment:**
- **Backend URL:** https://pm73uxrya8.us-west-2.awsapprunner.com
- **Frontend URL:** https://ai-engineer-coding-exercise.vercel.app
- **Service:** AWS App Runner (us-west-2)
- **Registry:** Amazon ECR Public
- **Image:** `public.ecr.aws/u9a7e4x8/rag-backend:latest`

**Key Features:**
- ✅ AWS Bedrock Claude Sonnet 4.5 for LLM generation
- ✅ AWS Bedrock Cohere v3 for embeddings (1024-dim)
- ✅ IAM role-based authentication (no credential management)
- ✅ Pre-baked ChromaDB data (4,245 chunks across 3 collections)
- ✅ Startup script handles ephemeral storage
- ✅ Automatic health checks and container restart

---

## Prerequisites

**AWS Requirements:**
- AWS account with Bedrock access
- AWS CLI configured with appropriate credentials
- Docker installed locally

**Model Access:**
- Bedrock model access enabled for:
  - `us.anthropic.claude-sonnet-4-20250514-v1:0` (inference profile)
  - `cohere.embed-english-v3` (embedding model)

**Repository:**
- Code pushed to GitHub (for CI/CD, optional)
- Docker Hub or ECR access for image storage

---

## Architecture

### Deployment Flow

```
Local Build → ECR Public → App Runner → Bedrock
     ↓           ↓             ↓           ↓
  Docker     Push Image   IAM Role    Claude + Cohere
   Image                 (no keys)
```

### Data Strategy

```
Image Build:
  /app/data_baked/
    ├── chroma_db/      (70MB - Cohere v3 embeddings)
    └── documents/      (docs for re-ingestion)

Container Startup:
  1. start.sh checks /app/data/chroma_db/
  2. If empty → copy from /app/data_baked/
  3. Start uvicorn server

Runtime:
  /app/data/
    ├── chroma_db/      (ephemeral, copied from baked)
    └── documents/      (ephemeral, copied from baked)
```

**Why this approach?**
- App Runner mounts `/app/data` as ephemeral storage
- Baked data stored separately at `/app/data_baked`
- Startup script copies data only if needed
- Supports both ephemeral (App Runner) and persistent (ECS+EFS) storage

---

## Deployment Steps

### 1. Create IAM Role

```bash
# Create trust policy
cat > /tmp/apprunner-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name rag-backend-apprunner-role \
  --assume-role-policy-document file:///tmp/apprunner-trust-policy.json \
  --description "IAM role for RAG backend on App Runner with Bedrock access"
```

### 2. Attach Bedrock Permissions

```bash
# Create Bedrock policy
cat > /tmp/bedrock-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ],
    "Resource": [
      "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-*",
      "arn:aws:bedrock:us-west-2::foundation-model/cohere.embed-*",
      "arn:aws:bedrock:us-west-2:276304618444:inference-profile/*",
      "arn:aws:bedrock:*::foundation-model/*"
    ]
  }]
}
EOF

# Attach policy to role
aws iam put-role-policy \
  --role-name rag-backend-apprunner-role \
  --policy-name BedrockAccessPolicy \
  --policy-document file:///tmp/bedrock-policy.json
```

**⚠️ Important:** Include `inference-profile/*` for Claude Sonnet 4.5 access.

### 3. Build and Push Docker Image

```bash
# Build image with baked data (run from project root)
docker build -f backend/Dockerfile.ecs -t rag-backend:latest .

# Create ECR Public repository (first time only)
aws ecr-public create-repository \
  --repository-name rag-backend \
  --region us-east-1

# Login to ECR Public
aws ecr-public get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin public.ecr.aws

# Tag and push
docker tag rag-backend:latest public.ecr.aws/u9a7e4x8/rag-backend:latest
docker push public.ecr.aws/u9a7e4x8/rag-backend:latest
```

### 4. Create App Runner Service

```bash
aws apprunner create-service \
  --service-name rag-backend-service \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "public.ecr.aws/u9a7e4x8/rag-backend:latest",
      "ImageRepositoryType": "ECR_PUBLIC",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "LLM_PROVIDER": "bedrock",
          "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-20250514-v1:0",
          "EMBEDDING_PROVIDER": "bedrock",
          "BEDROCK_EMBEDDING_MODEL": "cohere.embed-english-v3",
          "AWS_REGION": "us-west-2",
          "CHROMA_PERSIST_DIRECTORY": "/app/data/chroma_db",
          "CHROMA_COLLECTION_NAME": "fastapi_docs",
          "CHUNK_SIZE": "500",
          "CHUNK_OVERLAP": "50",
          "TOP_K_RESULTS": "5",
          "RELEVANCE_THRESHOLD": "0.65",
          "PROMPT_COT_ENABLED": "true",
          "API_HOST": "0.0.0.0",
          "API_RELOAD": "false",
          "CORS_ORIGINS": "https://ai-engineer-coding-exercise.vercel.app,http://localhost:5173",
          "LOG_LEVEL": "INFO"
        }
      }
    },
    "AutoDeploymentsEnabled": false
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "arn:aws:iam::276304618444:role/rag-backend-apprunner-role"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }' \
  --region us-west-2
```

### 5. Wait for Deployment

```bash
# Check status
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:276304618444:service/rag-backend-service/3628dbff630941848d55be9f7e60af6e \
  --region us-west-2 \
  --query 'Service.Status'

# Get service URL
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:276304618444:service/rag-backend-service/3628dbff630941848d55be9f7e60af6e \
  --region us-west-2 \
  --query 'Service.ServiceUrl' \
  --output text
```

### 6. Verify Deployment

```bash
# Health check
curl https://pm73uxrya8.us-west-2.awsapprunner.com/health

# Collections
curl https://pm73uxrya8.us-west-2.awsapprunner.com/api/v1/collections

# Test query
curl -X POST https://pm73uxrya8.us-west-2.awsapprunner.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?", "collection_name": "fastapi_docs"}'
```

### 7. Configure Frontend (Vercel)

```bash
# Set environment variable in Vercel dashboard:
VITE_API_BASE_URL=https://pm73uxrya8.us-west-2.awsapprunner.com

# Or via CLI:
cd frontend
vercel env add VITE_API_BASE_URL production
# Enter: https://pm73uxrya8.us-west-2.awsapprunner.com
vercel --prod  # Redeploy
```

---

## Configuration

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `LLM_PROVIDER` | `bedrock` | Use AWS Bedrock for LLM |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Claude Sonnet 4.5 inference profile |
| `EMBEDDING_PROVIDER` | `bedrock` | Use AWS Bedrock for embeddings |
| `BEDROCK_EMBEDDING_MODEL` | `cohere.embed-english-v3` | Cohere v3 (1024-dim) |
| `AWS_REGION` | `us-west-2` | Bedrock service region |
| `CHROMA_PERSIST_DIRECTORY` | `/app/data/chroma_db` | ChromaDB storage path |
| `CORS_ORIGINS` | `https://ai-engineer-coding-exercise.vercel.app,...` | Allowed frontend origins |

> **Cloud Deployment Configuration**
>
> These environment variables are for **AWS Bedrock** which is recommended for production cloud deployments. This configuration:
> - Uses IAM roles for authentication (no API keys to manage)
> - Ensures public internet accessibility from cloud services
> - Provides production-grade SLA and reliability
>
> For **local development**, use PNNL AI Incubator instead, which provides:
> - Access to multiple model providers (Claude, GPT, Gemini)
> - Single API key for all models
> - Faster iteration without AWS credential management
>
> See [SET-UP-CLAUDE-ON-WSL.md](SET-UP-CLAUDE-ON-WSL.md#deployment-considerations-local-vs-cloud) for local development configuration.

### Key Technical Details

**Embedding Configuration:**
- **Model:** Cohere Embed English v3
- **Dimensions:** 1024
- **Batch Size:** 96 (max for Cohere v3)
- **Performance:** ~100 chunks/second

**Collections:**
- `fastapi_docs`: 165 chunks
- `at_docs`: 2,408 chunks
- `tspr_docs`: 1,672 chunks
- **Total:** 4,245 chunks with 1024-dim embeddings

**Startup Script (`backend/start.sh`):**
```bash
#!/bin/bash
set -e

echo "🚀 Starting RAG backend..."

# Check if runtime data directory is empty
if [ ! -f "/app/data/chroma_db/chroma.sqlite3" ]; then
    echo "📦 Runtime data directory empty - copying baked data..."
    cp -r /app/data_baked/chroma_db/* /app/data/chroma_db/
    cp -r /app/data_baked/documents/* /app/data/documents/
    echo "✓ Data initialization complete"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
```

---

## Updating Deployment

### Quick Update (Code Changes Only)

```bash
# 1. Rebuild image
docker build -f backend/Dockerfile.ecs -t rag-backend:latest .

# 2. Push to ECR
docker tag rag-backend:latest public.ecr.aws/u9a7e4x8/rag-backend:latest
docker push public.ecr.aws/u9a7e4x8/rag-backend:latest

# 3. Trigger redeployment
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-west-2:276304618444:service/rag-backend-service/3628dbff630941848d55be9f7e60af6e \
  --region us-west-2
```

### Update with New Data

If you've re-ingested documents with updated embeddings:

```bash
# 1. Re-ingest locally with Bedrock Cohere v3
docker run --rm \
  -e AWS_PROFILE=AssetScore \
  -e AWS_REGION=us-west-2 \
  -e EMBEDDING_PROVIDER=bedrock \
  -e BEDROCK_EMBEDDING_MODEL=cohere.embed-english-v3 \
  -v ~/.aws:/root/.aws \
  -v $(pwd)/data:/app/data \
  rag-backend:latest \
  python -c "
from app.rag.ingestion import ingest_documents
ingest_documents('/app/data/documents/fastapi-docs', 'fastapi_docs', True)
"

# 2. Rebuild image (now includes new data)
docker build --no-cache -f backend/Dockerfile.ecs -t rag-backend:latest .

# 3. Push and deploy (as above)
```

### One-Line Deploy Script

```bash
# Save this as deploy.sh
docker build --no-cache -f backend/Dockerfile.ecs -t rag-backend:latest . && \
docker tag rag-backend:latest public.ecr.aws/u9a7e4x8/rag-backend:latest && \
docker push public.ecr.aws/u9a7e4x8/rag-backend:latest && \
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-west-2:276304618444:service/rag-backend-service/3628dbff630941848d55be9f7e60af6e \
  --region us-west-2
```

---

## Troubleshooting

### Issue: "User is not authorized to perform bedrock:InvokeModel"

**Symptom:**
```
BedrockException - User: arn:aws:sts::xxx:assumed-role/rag-backend-apprunner-role/xxx
is not authorized to perform: bedrock:InvokeModel on resource:
arn:aws:bedrock:us-west-2:xxx:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0
```

**Solution:**
Update IAM policy to include inference profiles:
```bash
# Add this resource to your policy:
"arn:aws:bedrock:us-west-2:276304618444:inference-profile/*"
```

### Issue: "Embedding dimension mismatch"

**Symptom:**
```
ERROR - Retrieval error: Embedding dimension 1024 does not match collection dimensionality 3072
```

**Root Cause:**
- Baked data uses OpenAI embeddings (3072-dim)
- Runtime uses Cohere v3 (1024-dim)

**Solution:**
Re-ingest all collections with Bedrock Cohere v3 and rebuild image:
```bash
# 1. Delete old data
rm -rf data/chroma_db/*

# 2. Re-ingest with Cohere v3
docker run --rm \
  -e AWS_PROFILE=AssetScore \
  -e EMBEDDING_PROVIDER=bedrock \
  -e BEDROCK_EMBEDDING_MODEL=cohere.embed-english-v3 \
  -v ~/.aws:/root/.aws \
  -v $(pwd)/data:/app/data \
  rag-backend:latest \
  python -c "
from app.rag.ingestion import ingest_documents
ingest_documents('/app/data/documents/fastapi-docs', 'fastapi_docs', True)
ingest_documents('/app/data/documents/at-docs', 'at_docs', True)
ingest_documents('/app/data/documents/tspr-docs', 'tspr_docs', True)
"

# 3. Rebuild with --no-cache
docker build --no-cache -f backend/Dockerfile.ecs -t rag-backend:latest .
```

### Issue: "Invalid parameter combination" (Cohere batch size)

**Symptom:**
```
BedrockException - {"message":"Invalid parameter combination. Please check and try again."}
```

**Root Cause:**
Cohere v3 max batch size is 96, but code used 128.

**Solution:**
Fixed in `backend/app/rag/embeddings.py`:
```python
BATCH_SIZE = 96 if self._provider == "bedrock" else 500
```

### Issue: Collections empty after deployment

**Symptom:**
```json
{"collections": []}
```

**Root Cause:**
- Startup script didn't run
- Data not copied from `/app/data_baked/`

**Solution:**
1. Check logs:
```bash
aws logs tail /aws/apprunner/rag-backend-service/xxx/application \
  --since 5m --region us-west-2
```

2. Verify environment variable:
```bash
# Should be /app/data/chroma_db (NOT /mnt/data/chroma_db)
aws apprunner describe-service --service-arn xxx --region us-west-2 \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.CHROMA_PERSIST_DIRECTORY'
```

### Issue: Deployment stuck in OPERATION_IN_PROGRESS

**Solution:**
Wait 3-5 minutes. App Runner deployments typically take:
- First deployment: ~5 minutes
- Updates: ~3 minutes

Check status:
```bash
watch -n 10 'aws apprunner describe-service --service-arn xxx --region us-west-2 --query "Service.Status"'
```

---

## Cost Estimate

### AWS App Runner

| Component | Spec | Cost |
|-----------|------|------|
| **Compute** | 1 vCPU, 2 GB RAM | ~$0.007/hour = ~$5/month |
| **Memory** | 2 GB provisioned | ~$0.008/hour = ~$6/month |
| **Requests** | First 100k free | ~$0 for moderate use |
| **Build time** | Minimal (pre-built image) | ~$1/month |

**Subtotal:** ~$12-15/month

### AWS Bedrock

| Model | Usage | Cost |
|-------|-------|------|
| **Claude Sonnet 4.5** | Input: $0.003/1K tokens<br>Output: $0.015/1K tokens | ~$10-20/month (moderate) |
| **Cohere v3** | $0.0001/1K tokens | ~$1/month |

**Subtotal:** ~$11-21/month

### Amazon ECR Public

- **Storage:** Free for public images
- **Bandwidth:** Free egress to internet

**Subtotal:** $0/month

### Total Monthly Cost

**Estimated:** $25-40/month for moderate usage (100-500 queries/day)

**Cost Optimization:**
- Use App Runner with auto-scaling (scale to 0 during low traffic)
- Consider ECS Fargate Spot for ~70% savings
- Cache responses in frontend to reduce LLM calls

---

## Alternative: ECS Fargate Deployment

For production with persistent storage, consider ECS Fargate + EFS:

**Advantages:**
- Persistent storage (EFS)
- Better control over networking/VPC
- Spot instances for cost savings (~70% cheaper)
- Native IAM role integration

**Setup:**
See [AWS-DEPLOYMENT.md](./AWS-DEPLOYMENT.md) for ECS Fargate guide.

---

## Summary

**Deployment Checklist:**
- ✅ IAM role created with Bedrock permissions (including inference profiles)
- ✅ Docker image built with Cohere v3 embeddings (1024-dim)
- ✅ Image pushed to ECR Public
- ✅ App Runner service deployed with correct env vars
- ✅ Health check passes
- ✅ Collections loaded (4,245 chunks)
- ✅ Queries working end-to-end
- ✅ Frontend connected to backend

**Key Files:**
- `backend/Dockerfile.ecs` - ECS/App Runner optimized Dockerfile
- `backend/start.sh` - Startup script for data initialization
- `backend/app/rag/embeddings.py` - Fixed Cohere v3 batch size (96)

**Production URLs:**
- Backend: https://pm73uxrya8.us-west-2.awsapprunner.com
- Frontend: https://ai-engineer-coding-exercise.vercel.app

---

**Last Updated:** March 23, 2026
**Deployment Status:** ✅ Operational
