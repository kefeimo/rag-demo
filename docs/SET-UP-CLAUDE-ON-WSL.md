# End-to-End Setup: Claude Code on WSL

## Overview

This guide covers:
1. Installing Claude Code CLI (avoiding the npm "interrupted" issue)
2. Configuring model providers:
   - **PNNL AI Incubator** (internal PNNL API gateway for Claude models)
   - **AWS Bedrock** (direct AWS access)
3. Project settings and CLAUDE.md files
4. IDE integration and MCP servers

---

## Internal References (PNNL)

> These internal wiki pages contain org-specific configuration, approved models, and account details.
>
> - **[Claude Code — PNNL Wiki](https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS/pages/39616804/Claude+Code)** — General setup and usage
> - **[PNNL AI Incubator](https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS/pages/39616808/PNNL+AI+Incubator)** — Internal API gateway (recommended for most users)
> - **[Amazon Bedrock](https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS/pages/39616807/Amazon+Bedrock)** — Direct AWS access option

---

## Prerequisites

- WSL2 with Ubuntu (or similar)
- VSCode with the Claude Code extension (optional but recommended)
- For **PNNL AI Incubator**:
  - API key from internal team
  - Network access to `https://pnnl-ai-incubator.pnnl.gov/api` (see verification below)
- For **AWS Bedrock**: AWS account with Bedrock access enabled

> **Note on corporate proxy:** If your environment has a proxy, ensure `HTTPS_PROXY` / `NO_PROXY`
> env vars are set before running any Claude commands.

### Verify PNNL AI Incubator Network Access

Before proceeding with PNNL AI Incubator setup, verify you can reach the endpoint:

```bash
# Test basic connectivity
curl -I https://pnnl-ai-incubator.pnnl.gov/api

# Expected response: HTTP/2 401 (Unauthorized - this is correct, means endpoint is reachable)
# Bad response: Connection timeout, Connection refused, or SSL errors
```

**Common Issues:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Not on VPN** | `Connection timed out` or `Connection refused` | Connect to PNNL VPN before accessing |
| **SSL Certificate Error** | `SSL certificate problem` | Install PNNL root CA certificates |
| **Proxy Blocking** | `Connection refused` or `502 Bad Gateway` | Set `HTTPS_PROXY` or add to `NO_PROXY` list |
| **DNS Resolution** | `Could not resolve host` | Check DNS settings, may need PNNL DNS servers |
| **Wrong Region/Network** | `Connection timed out` | Endpoint may only be accessible from specific PNNL networks |

**If you see HTTP 401 Unauthorized**, the endpoint is reachable and you can proceed with setup.

**If you cannot reach the endpoint**, contact your team lead or IT support, or use AWS Bedrock instead (Option B in Step 2).

---

## Step 1: Install Claude CLI

### Remove any existing npm-installed version first

The npm-installed version has two known issues:
1. Causes "interrupted — what should Claude do instead?" prompts that break non-interactive flows
2. May be blocked by the PNNL AI Incubator proxy at `https://pnnl-ai-incubator.pnnl.gov/api`

Uninstall it:

```bash
npm uninstall -g @anthropic-ai/claude-code
```

### Install via the official installer (preferred)

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Verify the install:

```bash
claude --version
```

---

## Step 2: Configure Model Provider

Choose **Option A (PNNL AI Incubator)** or **Option B (AWS Bedrock)** based on your access.

---

### Option A: PNNL AI Incubator (Recommended)

The PNNL AI Incubator provides a managed API gateway for Claude models with centralized billing
and access control. This is the recommended option for most PNNL users.

#### Get your API key

Contact your team lead or the AI Incubator team for:
- API base URL
- API key (birthright or project-specific)

#### Configure environment variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# PNNL AI Incubator
export ANTHROPIC_BASE_URL="https://pnnl-ai-incubator.pnnl.gov/api"
export ANTHROPIC_API_KEY="your-api-key-here"
```

Reload your shell:
```bash
source ~/.bashrc
```

#### Set Claude Code to use the API

```bash
# Use custom API endpoint
claude config set --global apiProvider anthropic

# Set default model (use -project suffix for project keys)
claude config set --global model claude-sonnet-4-5-20250929-v1:0-project
```

#### Available models

For **birthright keys** (no `-project` suffix):
- `claude-sonnet-4-20250514-v1:0` — Sonnet 4.0
- `claude-sonnet-4-5-20250929-v1:0` — Sonnet 4.5 (Sept 2025)
- `claude-haiku-4-5-20251001-v1:0` — Haiku 4.5

For **project keys** (add `-project` suffix):
- `claude-sonnet-4-20250514-v1:0-project`
- `claude-sonnet-4-5-20250929-v1:0-project`
- `claude-haiku-4-5-20251001-v1:0-project`

#### Test the connection

**Verify API key works:**

```bash
# Test with curl first
curl https://pnnl-ai-incubator.pnnl.gov/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-haiku-4-5-20251001-v1:0-project",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hi"}]
  }'

# Expected: JSON response with model output
# If error: Check API key, model name, or network access
```

**Test with Claude Code CLI:**

```bash
claude -p "say hello"
```

**Troubleshooting:**

- **401 Unauthorized**: Invalid API key or wrong format
- **404 Not Found**: Wrong base URL or model name
- **Connection timeout**: Network/VPN issue (see Prerequisites section)
- **Model not found**: Use correct model name with `-project` suffix for project keys

#### Note on WAF blocking (resolved)

> **Historical issue (now fixed):** Earlier versions of Azure Application Gateway WAF blocked
> requests containing security-related keywords (DoS, SQL injection, XSS, etc.). This issue has
> been resolved by the PNNL infrastructure team. Claude Code requests now pass through without
> modification.

---

### Option B: AWS Bedrock

#### Enable model access in Bedrock console

1. Go to **AWS Console → Amazon Bedrock → Model access**
2. Click **Manage model access**
3. Enable the Claude models you need (e.g. `Claude Sonnet 3.5 v2`)
4. Wait for status to show **Access granted**

#### Create an IAM user or role for Bedrock access

Attach the following policy to your IAM identity:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.*"
    }
  ]
}
```

#### Configure AWS credentials in WSL

> **AWS CLI and CDK Credential SSO Setup**
>
> At PNNL, credentials are managed via AWS SSO (IAM Identity Center) rather than static access keys.
> Follow the org-specific SSO configuration steps in the internal wiki before proceeding:
> [Amazon Bedrock — PNNL Wiki](https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS/pages/39616807/Amazon+Bedrock)
>
> Key steps typically include:
> - Running `aws configure sso` and entering the SSO start URL and account/role provided by your team
> - Running `aws sso login --profile <your-profile>` to authenticate
> - Setting `AWS_PROFILE=<your-profile>` in your shell so Claude CLI picks up the right credentials
>
> For CDK usage, ensure `cdk bootstrap` is run with the SSO profile:
> ```bash
> AWS_PROFILE=<your-profile> cdk bootstrap
> ```

For non-SSO / static key environments:

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID:     <your-access-key>
AWS Secret Access Key: <your-secret-key>
Default region name:   us-east-1          # or your Bedrock-enabled region
Default output format: json
```

Verify credentials work:

```bash
aws sts get-caller-identity
```

---

## Step 3: Set Up CloudWatch Logging (Optional - Bedrock only)

### Create the log group

```bash
aws logs create-log-group \
  --log-group-name /aws/bedrock/model-invocations \
  --region us-east-1
```

### Create an IAM role for Bedrock to write logs

Create a trust policy file:

```bash
cat > bedrock-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "bedrock.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create the role and attach permissions:

```bash
aws iam create-role \
  --role-name BedrockLoggingRole \
  --assume-role-policy-document file://bedrock-trust-policy.json

aws iam attach-role-policy \
  --role-name BedrockLoggingRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

Get the role ARN:

```bash
ROLE_ARN=$(aws iam get-role --role-name BedrockLoggingRole --query 'Role.Arn' --output text)
echo $ROLE_ARN
```

### Enable logging in Bedrock

```bash
aws bedrock put-model-invocation-logging-configuration \
  --logging-config "{
    \"cloudWatchConfig\": {
      \"logGroupName\": \"/aws/bedrock/model-invocations\",
      \"roleArn\": \"$ROLE_ARN\",
      \"largeDataDeliveryS3Config\": {
        \"bucketName\": \"\",
        \"keyPrefix\": \"\"
      }
    },
    \"s3Config\": null,
    \"textDataDeliveryEnabled\": true,
    \"imageDataDeliveryEnabled\": false,
    \"embeddingDataDeliveryEnabled\": false
  }"
```

---

## Step 4: Disable the Logging Consent Page in VSCode Extension

The VSCode Claude extension shows a logging/telemetry consent page on first launch.
To skip it and go straight to the chat UI:

1. Open VSCode **Settings** (`Ctrl+,`)
2. Search for `claude`
3. Find **Claude Code: Enable Telemetry** → set to `false`
4. Alternatively, add to your `settings.json`:

```json
{
  "claude.enableTelemetry": false,
  "claude.autoAcceptedLoggingConsent": true
}
```

Or via the Claude Code settings file:

```bash
# Disable telemetry/logging consent prompt
claude config set --global autoAcceptedLoggingConsent true
```

Restart VSCode after changing these settings.

---

## Step 5: Verify Full Integration

### From WSL terminal

```bash
# Confirm provider is Bedrock
claude config list

# Send a test prompt
claude -p "what model are you running on?"
```

### From VSCode

1. Open VSCode in WSL: `code .` from your project directory
2. Open the Claude panel (sidebar or `Ctrl+Shift+P → Claude`)
3. You should land directly on the chat UI (no logging consent page)
4. Send a test message — responses should route through Bedrock

### Check CloudWatch logs (if enabled)

```bash
# View recent invocations
aws logs filter-log-events \
  --log-group-name /aws/bedrock/model-invocations \
  --start-time $(date -d '10 minutes ago' +%s000) \
  --query 'events[*].message' \
  --output text
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `interrupted — what should Claude do instead?` | Uninstall npm version, reinstall via curl installer |
| Proxy blocking Claude CLI | Set `HTTPS_PROXY=http://your-proxy:port` in `~/.bashrc` |
| `Could not connect to Bedrock` | Verify `aws sts get-caller-identity` works; check region |
| Model access denied | Confirm model is enabled in Bedrock → Model access console |
| Log group does not exist | Run `aws logs create-log-group` before enabling logging |
| VSCode still shows logging page | Set `autoAcceptedLoggingConsent: true` in Claude config |

---

## Quick Reference

### PNNL AI Incubator setup
```bash
# Install Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Set environment variables (add to ~/.bashrc)
export ANTHROPIC_BASE_URL="https://pnnl-ai-incubator.pnnl.gov/api"
export ANTHROPIC_API_KEY="your-api-key-here"

# Configure Claude Code
claude config set --global apiProvider anthropic
claude config set --global model claude-sonnet-4-5-20250929-v1:0-project
claude config set --global autoAcceptedLoggingConsent true

# Test
claude -p "hello"
```

### AWS Bedrock setup
```bash
# Install Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Configure AWS credentials (if needed)
aws configure

# Configure Claude Code
claude config set --global apiProvider bedrock
claude config set --global awsRegion us-east-1
claude config set --global model anthropic.claude-sonnet-4-5
claude config set --global autoAcceptedLoggingConsent true

# Test
claude -p "hello from bedrock"
```

---

## Project Settings

Claude Code supports per-project configuration via `.claude/settings.json` files. These override
global settings and allow team-wide consistency.

### Creating project settings

```bash
cd /path/to/your/project
mkdir -p .claude
```

Create `.claude/settings.json`:

```json
{
  "model": "claude-sonnet-4-5-20250929-v1:0-project",
  "apiProvider": "anthropic",
  "temperature": 0.7,
  "maxTokens": 8096,
  "allowedTools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
  "permissions": {
    "bash": "ask",
    "edit": "allow",
    "read": "allow"
  }
}
```

### Settings hierarchy

1. **Global settings** (`~/.claude/settings.json`) — Apply to all projects
2. **Project settings** (`.claude/settings.json`) — Override global for this project
3. **CLI flags** — Override both for single invocation

Example CLI override:
```bash
claude -m claude-haiku-4-5-20251001-v1:0-project -p "fast query"
```

---

## CLAUDE.md Files

`CLAUDE.md` files provide persistent context and instructions to Claude Code. Place them at the
project root or in subdirectories for scoped guidance.

### Example CLAUDE.md

Create `CLAUDE.md` in your project root:

```markdown
# Project Context

This is a RAG demo application using FastAPI, ChromaDB, and AWS Bedrock.

## Architecture

- **Backend**: FastAPI (app/main.py)
- **Vector Store**: ChromaDB (data/chroma_db/)
- **LLM**: AWS Bedrock (Claude Sonnet 4.5 via LiteLLM)
- **Embeddings**: Cohere v3 via Bedrock

## Development Guidelines

- Use type hints for all Python functions
- Follow PEP 8 style guide
- Write docstrings for public functions
- Run tests before committing: `pytest backend/tests/`

## Common Tasks

### Running locally
\`\`\`bash
cd backend
uvicorn app.main:app --reload --port 8000
\`\`\`

### Building Docker image
\`\`\`bash
docker build -f backend/Dockerfile.render -t rag-backend:latest .
\`\`\`

## File Structure

- `backend/app/` — FastAPI application
- `backend/app/rag/` — RAG logic (embeddings, retrieval, generation)
- `data/documents/` — Source documents
- `data/chroma_db/` — Vector database
```

### Scoped CLAUDE.md files

You can place `CLAUDE.md` files in subdirectories for context-specific guidance:

```
project/
├── CLAUDE.md                    # General project context
├── backend/
│   ├── CLAUDE.md               # Backend-specific guidelines
│   └── app/
│       └── rag/CLAUDE.md       # RAG module specifics
└── frontend/
    └── CLAUDE.md               # Frontend-specific rules
```

Claude Code automatically loads the nearest `CLAUDE.md` file based on your current working directory.

---

## IDE Plugins

### VSCode Extension

The official **Claude Code** extension provides deep IDE integration:

- **Inline chat** — Ask questions about selected code
- **File context** — Automatically includes open files
- **Terminal integration** — Execute commands from chat
- **Diff view** — Review changes before applying

#### Installation

1. Open VSCode
2. Search for "Claude Code" in Extensions marketplace
3. Install and reload
4. Configure via VSCode settings or `.claude/settings.json`

#### Usage

- **Open Claude panel**: `Ctrl+Shift+P` → "Claude: Open Panel"
- **Ask about selection**: Highlight code → Right-click → "Ask Claude"
- **Apply changes**: Claude will show diffs; click "Apply" to accept

### JetBrains Plugin (Community)

A community-maintained plugin is available for IntelliJ IDEA, PyCharm, and other JetBrains IDEs.
Search for "Claude Code" in the JetBrains Marketplace.

---

## MCP Servers (Model Context Protocol)

MCP allows Claude Code to connect to external data sources and tools. This enables access to
databases, APIs, file systems, and more.

### What is MCP?

MCP is a protocol that lets Claude Code interact with external systems through standardized
"servers" that expose tools and resources.

**Example use cases:**
- Query a PostgreSQL database
- Search Confluence or Jira
- Access Git history
- Read from S3 buckets
- Interact with Slack or email

### Installing MCP servers

MCP servers are configured in `.claude/settings.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_yourtoken"
      }
    }
  }
}
```

### Available MCP servers

Official Anthropic servers:
- `@modelcontextprotocol/server-filesystem` — File system access
- `@modelcontextprotocol/server-postgres` — PostgreSQL queries
- `@modelcontextprotocol/server-github` — GitHub API
- `@modelcontextprotocol/server-slack` — Slack integration
- `@modelcontextprotocol/server-puppeteer` — Browser automation

Find more at: https://github.com/modelcontextprotocol/servers

### Testing MCP servers

```bash
# List available MCP tools
claude mcp list

# Test a specific tool
claude -p "use the filesystem MCP to list files in /tmp"
```

---

## Appendix: PNNL AI Incubator Unified API Key

The PNNL AI Incubator provides a **single API key** that works with multiple endpoints and model providers. This unified key simplifies access management and billing across different LLM services.

### How it works

One API key (`sk-...`) can be used with:

1. **Claude models** (Anthropic API format)
   - Base URL: `https://pnnl-ai-incubator.pnnl.gov/api`
   - For: Claude Code CLI, Anthropic SDK
   - Environment variable: `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`

2. **OpenAI and other models** (OpenAI-compatible API)
   - Base URL: `https://ai-incubator-api.pnnl.gov`
   - For: OpenAI SDK, LiteLLM, Cline, Continue, etc.
   - Environment variable: `OPENAI_API_KEY` or `LLM_API_KEY`

### Example: Using the same key for both Claude and OpenAI

**For Claude Code CLI** (already configured in Step 2, Option A):
```bash
export ANTHROPIC_BASE_URL="https://pnnl-ai-incubator.pnnl.gov/api"
export ANTHROPIC_API_KEY="sk-nTj47WE6-A2ykMGRtCNo0A"
```

**For OpenAI SDK or LiteLLM**:
```bash
export OPENAI_BASE_URL="https://ai-incubator-api.pnnl.gov"
export OPENAI_API_KEY="sk-nTj47WE6-A2ykMGRtCNo0A"  # Same key!
```

**Python example with OpenAI SDK**:
```python
import openai

client = openai.OpenAI(
    api_key="sk-nTj47WE6-A2ykMGRtCNo0A",
    base_url="https://ai-incubator-api.pnnl.gov"
)

response = client.chat.completions.create(
    model="gpt-4o-birthright",  # or claude-sonnet-4-5-20250929-v1:0-project
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**Python example with LiteLLM** (used in this RAG project):
```python
import os
from litellm import completion

os.environ["OPENAI_API_KEY"] = "sk-nTj47WE6-A2ykMGRtCNo0A"
os.environ["OPENAI_API_BASE"] = "https://ai-incubator-api.pnnl.gov"

response = completion(
    model="openai/gpt-4o-birthright",  # LiteLLM format
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Available models

See the full list at: https://ai-incubator-depot.pnnl.gov/models

Common models include:
- **Claude**: `claude-sonnet-4-5-20250929-v1:0-project`, `claude-haiku-4-5-20251001-v1:0-project`
- **GPT**: `gpt-4o-birthright`, `gpt-4o-mini-birthright`
- **Gemini**: `gemini-1.5-pro-birthright`, `gemini-2.0-flash-exp-birthright`
- **Embeddings**: `text-embedding-3-small-birthright`, `cohere-embed-english-v3.0-birthright`

### Benefits of unified key

- **Single billing point**: All usage tracked under one key
- **Simplified access control**: One key to manage and rotate
- **Multi-provider support**: Access Azure OpenAI, AWS Bedrock, GCP models with one credential
- **OpenAI-compatible interface**: Works with existing OpenAI-based tools and libraries

### More information

- **API Key Depot**: https://ai-incubator-depot.pnnl.gov/
- **Instructions**: https://ai-incubator-depot.pnnl.gov/instructions
- **Model list**: https://ai-incubator-depot.pnnl.gov/models

---

## Deployment Considerations: Local vs Cloud

### PNNL API Incubator vs AWS Bedrock

The choice between PNNL AI Incubator and AWS Bedrock depends on your deployment environment:

| Aspect | PNNL AI Incubator | AWS Bedrock |
|--------|-------------------|-------------|
| **Best for** | Local development | Cloud deployment (Render, AWS, etc.) |
| **Network access** | Requires VPN or PNNL network | Public internet accessible |
| **Authentication** | API key | IAM credentials or access keys |
| **Security risk** | Key exposure if deployed externally | IAM roles (no hardcoded secrets) |
| **Model access** | Claude, GPT, Gemini via one key | Claude models only |
| **Cost** | Centralized PNNL billing | Direct AWS billing |
| **Production readiness** | Not designed for external workloads | Production-grade SLA |

### Recommended Pattern

```
┌─────────────────────────────────────┐
│  Local Development (WSL/Laptop)     │
│                                     │
│  ✓ PNNL AI Incubator                │
│  ✓ Fast iteration                   │
│  ✓ All models (Claude/GPT/Gemini)   │
│  ✓ Single API key                   │
└─────────────────────────────────────┘
              │
              │ git push
              ▼
┌─────────────────────────────────────┐
│  Cloud Deployment (Render/AWS)      │
│                                     │
│  ✓ AWS Bedrock + IAM                │
│  ✓ No API key exposure              │
│  ✓ Public internet accessible       │
│  ✓ Production SLA                   │
└─────────────────────────────────────┘
```

### Environment Variable Configuration

#### For Local Development (PNNL API Incubator)

**Claude Code CLI:**
```bash
# ~/.bashrc or ~/.zshrc
export ANTHROPIC_BASE_URL="https://pnnl-ai-incubator.pnnl.gov/api"
export ANTHROPIC_API_KEY="sk-nTj47WE6-A2ykMGRtCNo0A"
```

**RAG Backend (`backend/.env`):**
```bash
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-nTj47WE6-A2ykMGRtCNo0A
OPENAI_API_BASE=https://ai-incubator-api.pnnl.gov
OPENAI_MODEL=claude-sonnet-4-5-20250929-v1:0-project

# Embedding Configuration
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small-birthright

# Or use Cohere embeddings
# EMBEDDING_PROVIDER=bedrock
# BEDROCK_EMBEDDING_MODEL=cohere.embed-english-v3
```

#### For Cloud Deployment (AWS Bedrock)

**Render/App Runner Environment Variables:**
```bash
# LLM Configuration
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# For Render: Use AWS access keys (stored in Render secrets)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Embedding Configuration
EMBEDDING_PROVIDER=bedrock
BEDROCK_EMBEDDING_MODEL=cohere.embed-english-v3
```

**AWS ECS with IAM Task Role (Recommended):**
```bash
# LLM Configuration
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# No AWS credentials needed - uses IAM Task Role
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not required

# Embedding Configuration
EMBEDDING_PROVIDER=bedrock
BEDROCK_EMBEDDING_MODEL=cohere.embed-english-v3
```

### Why Not Use PNNL API in Cloud?

**Network accessibility issues:**
- PNNL endpoints may require VPN or be restricted to internal network
- External cloud services (Render, AWS) may not be able to reach `pnnl-ai-incubator.pnnl.gov`
- No guaranteed uptime or SLA for external access

**Security concerns:**
- Deploying internal PNNL API keys to external services creates security risks
- PNNL security policy may prohibit using internal credentials in external environments
- Key rotation more complex when deployed across external services

**Production readiness:**
- Internal API gateways not designed for production external workloads
- AWS Bedrock provides better reliability, monitoring, and support

### Testing Both Configurations

**Test PNNL API locally:**
```bash
cd backend
cp .env.example .env
# Edit .env with PNNL settings above
uvicorn app.main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?"}'
```

**Test Bedrock configuration:**
```bash
# Update .env with Bedrock settings
# Run the same tests
```

### Related Documentation

- **AWS Deployment Guide**: [DEPLOYMENT-AWS.md](DEPLOYMENT-AWS.md)
- **Backend Configuration**: [backend/app/config.py](../backend/app/config.py)
- **Docker Configuration**: [backend/Dockerfile.render](../backend/Dockerfile.render)

---

## Additional Resources

- **Claude Code Documentation**: https://docs.anthropic.com/claude-code
- **PNNL Wiki**: https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS
- **MCP Protocol Spec**: https://modelcontextprotocol.io
- **GitHub Issues**: https://github.com/anthropics/claude-code/issues
