# Quick Start: Claude Code on WSL

## Overview

This is a minimal quick-start guide to get Claude Code working as your coding assistant on WSL.

**What you'll set up:**
1. Installing Claude Code CLI
2. Configuring model provider (choose one):
   - **PNNL AI Incubator** (recommended for PNNL users)
   - **AWS Bedrock** (alternative option)
3. Verifying the setup works

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
- VSCode with the Claude Code extension (optional)
  - **Note**: The official VSCode extension only works with AWS Bedrock, not PNNL AI Incubator
  - For VSCode integration, choose **Option B (AWS Bedrock)**
  - For terminal-only usage, either option works
- For **PNNL AI Incubator**:
  - API key from internal team
  - Network access to `https://ai-incubator-api.pnnl.gov` (see verification below)
  - ⚠️ **Terminal CLI only** - VSCode extension not supported
- For **AWS Bedrock**:
  - AWS account with Bedrock access enabled
  - ✅ **Full VSCode extension support**

> **Note on corporate proxy:** If your environment has a proxy, ensure `HTTPS_PROXY` / `NO_PROXY`
> env vars are set before running any Claude commands.

### Verify PNNL AI Incubator Network Access

Before proceeding with PNNL AI Incubator setup, verify you can reach the endpoint:

```bash
# Test basic connectivity
curl -I https://ai-incubator-api.pnnl.gov

# Expected response: HTTP/2 200 (means endpoint is reachable)
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

**If you see HTTP 200 OK**, the endpoint is reachable and you can proceed with setup.

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

Choose **Option A (PNNL AI Incubator)** or **Option B (AWS Bedrock)** based on your needs:

**Quick Decision Guide:**

| Feature | Option A: PNNL AI Incubator | Option B: AWS Bedrock |
|---------|----------------------------|----------------------|
| **Terminal CLI** | ✅ Works | ✅ Works |
| **VSCode Extension** | ❌ Not supported | ✅ Fully supported |
| **Model Access** | Claude, GPT, Gemini, etc. | Claude only |
| **Billing** | PNNL centralized | Direct AWS |
| **Recommendation** | Terminal-only users | VSCode users |

**💡 For most users:** Choose **Option B (AWS Bedrock)** for reliable VSCode extension support.

---

### Option A: PNNL AI Incubator (Terminal CLI Only) ✅

**✅ Status: Confirmed working setup** - The configuration below has been tested and works with Claude Code terminal CLI.

The PNNL AI Incubator provides a managed API gateway for Claude models with centralized billing
and access control.

**✅ Works with:**
- Terminal CLI (`claude -p "prompt"` and interactive `claude` mode)
- Custom integrations and scripts

**❌ Does NOT work with:**
- Official Claude Code VSCode extension (only connects to Anthropic servers)
- Extensions requiring Anthropic's official API endpoints

**💡 Recommendation:**
- If you need **VSCode extension support**, use **Option B (AWS Bedrock)** instead
- If you only need **terminal CLI**, this option works great

#### Get your API key

Contact your team lead or the AI Incubator team for:
- API base URL
- API key (birthright or project-specific)

#### Configure environment variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# PNNL AI Incubator (✅ confirmed working setup)
export ANTHROPIC_API_KEY="sk-nTj47WE6-xxxxxx"  # Replace with your actual API key
export ANTHROPIC_BASE_URL="https://ai-incubator-api.pnnl.gov"

# For project keys
export ANTHROPIC_MODEL="claude-sonnet-4-20250514-v1-project"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-haiku-20241022-project"

# For debugging
export ANTHROPIC_LOG="debug"
export DISABLE_TELEMETRY=1
```

Reload your shell:
```bash
source ~/.bashrc
```

#### Set Claude Code to use the API

Configuration is done entirely through environment variables (already set in previous step):

```bash
# Verify environment variables are set correctly
echo "ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:20}..."
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"
echo "ANTHROPIC_SMALL_FAST_MODEL: $ANTHROPIC_SMALL_FAST_MODEL"

# Note: No 'claude config set' commands needed - Claude Code reads these env vars automatically
```

#### Available models

For **project keys** (✅ confirmed working):
- `claude-sonnet-4-20250514-v1-project` — Sonnet 4.0 (working as primary model)
- `claude-3-5-haiku-20241022-project` — Haiku 3.5 (working as fast model)

For **birthright keys** (if available):
- `claude-sonnet-4-20250514-v1-birthright` — Sonnet 4.0
- `claude-3-5-haiku-20241022-birthright` — Haiku 3.5

**Note:** The exact model names may vary. Use the models shown in your working configuration above.

#### Test the connection

**Verify API key works:**

```bash
# Test with curl first (OpenAI-compatible format)
# ✅ This is the confirmed working configuration:
curl https://ai-incubator-api.pnnl.gov/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  -d '{
    "model": "claude-3-5-haiku-20241022-project",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

**Expected successful response:**
```json
{
  "id": "chatcmpl-5168dd90-3029-4319-be33-be8c3a0d3e30",
  "created": 1774379126,
  "model": "claude-3-5-haiku-20241022-project",
  "object": "chat.completion",
  "choices": [{
    "finish_reason": "stop",
    "index": 0,
    "message": {
      "content": "Hello! 👋 How can I help you today?",
      "role": "assistant"
    }
  }],
  "usage": {
    "completion_tokens": 16,
    "prompt_tokens": 8,
    "total_tokens": 24,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "cache_creation_tokens": 0
    },
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

**If error:** Check API key, model name, or network access

**Verify billing:** Your usage should appear at https://ai-incubator-depot.pnnl.gov/ within a few minutes

**Test with Claude Code CLI:**

```bash
claude -p "say hello"
```

**Verify billing:**

After making API calls, check your usage at the PNNL AI Incubator Depot:
```bash
# Open in browser
https://ai-incubator-depot.pnnl.gov/
```

Your API calls should appear in the usage dashboard within a few minutes.

**Troubleshooting:**

- **401 Unauthorized / team_model_access_denied**: Invalid API key, wrong model name, or insufficient permissions
- **404 Not Found**: Wrong endpoint URL
- **Connection timeout**: Network/VPN issue (see Prerequisites section)
- **Model not found**: Use correct model name with `-project` suffix for project keys (not `:0-project`)

#### Important: API Format

> The PNNL AI Incubator uses an **OpenAI-compatible API format** for all models, including Claude.
> This means you use `/v1/chat/completions` endpoint and `Authorization: Bearer` header, not the
> native Anthropic API format. Claude Code CLI handles this automatically when you set the base URL.

---

### Option B: AWS Bedrock (Recommended for VSCode Users)

**✅ Full support for:**
- Terminal CLI
- Official Claude Code VSCode extension
- All Claude models via AWS Bedrock

**This is the most reliable option for full Claude Code integration.**

#### Enable model access in Bedrock console

1. Go to **AWS Console → Amazon Bedrock → Model access**
2. Click **Manage model access**
3. Enable the Claude models you need (e.g. `Claude Sonnet 4`)
4. Wait for status to show **Access granted**

#### Configure AWS credentials

Set up AWS SSO (at PNNL):
```bash
# Configure SSO profile
aws configure sso

# Login to SSO
aws sso login --profile your-profile-name
```

#### Configure environment variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# AWS Bedrock Configuration
export AWS_PROFILE=your-profile-name
export AWS_REGION=us-west-2
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
export ANTHROPIC_SMALL_FAST_MODEL=us.anthropic.claude-3-5-haiku-20241022-v1:0
export DISABLE_TELEMETRY=1

# Optional: Enable debug logging
# export ANTHROPIC_LOG=debug
```

Reload your shell:
```bash
source ~/.bashrc
```

#### Test the connection

```bash
# Verify environment variables
echo "AWS_PROFILE: $AWS_PROFILE"
echo "AWS_REGION: $AWS_REGION"
echo "CLAUDE_CODE_USE_BEDROCK: $CLAUDE_CODE_USE_BEDROCK"
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"

# Test with Claude Code
claude -p "say hello"
```

---

## Step 3: Verify Integration

### From terminal

```bash
# Send a test prompt
claude -p "what model are you running on?"
```

### From VSCode

**⚠️ Important Note for PNNL AI Incubator Users:**

The official Claude Code VSCode extension currently **does NOT support custom API endpoints** like `https://ai-incubator-api.pnnl.gov`. It only connects to Anthropic's official servers (api.anthropic.com).

**Recommended for VSCode integration:**
- Use **Option B (AWS Bedrock)** for more reliable VSCode extension support
- The Bedrock option works seamlessly with the official Claude Code extension
- Terminal CLI works fine with PNNL AI Incubator

**If you need VSCode integration with PNNL endpoint:**
- Consider alternative extensions that support custom endpoints
- Continue using terminal-based `claude` CLI for PNNL access

**Testing VSCode (Bedrock users only):**
1. Open VSCode in WSL: `code .` from your project directory
2. Open the Claude panel (sidebar or `Ctrl+Shift+P → Claude`)
3. Authenticate with Bedrock (the extension will guide you)
4. Send a test message

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `interrupted — what should Claude do instead?` | Uninstall npm version (`npm uninstall -g @anthropic-ai/claude-code`), reinstall via curl |
| Connection refused / timeout | Check VPN connection (PNNL users) or verify network access |
| 401 Unauthorized | Check API key is correct: `echo ${ANTHROPIC_API_KEY:0:20}...` |
| Model not found | Verify model name format (use `-project` suffix for project keys) |
| AWS credentials not working | Run `aws sso login --profile your-profile` and verify `AWS_PROFILE` env var |
| Config not working | Verify env vars: `echo $ANTHROPIC_BASE_URL`, `echo $CLAUDE_CODE_USE_BEDROCK` |

---

## Quick Reference

### PNNL AI Incubator setup (✅ confirmed working)
```bash
# Install Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Add to ~/.bashrc - Working configuration:
export ANTHROPIC_API_KEY="sk-nTj47WE6-xxxxxx"  # Replace with your actual key
export ANTHROPIC_BASE_URL="https://ai-incubator-api.pnnl.gov"
export ANTHROPIC_MODEL="claude-sonnet-4-20250514-v1-project"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-haiku-20241022-project"
export ANTHROPIC_LOG="debug"
export DISABLE_TELEMETRY=1

# Reload shell
source ~/.bashrc

# Verify environment variables
echo "ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:20}..."
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"

# Test
claude -p "hello"
```

### AWS Bedrock setup
```bash
# Install Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Configure AWS credentials (if needed)
aws configure

# Add to ~/.bashrc or ~/.zshrc
export AWS_PROFILE=your-profile-name
export AWS_REGION=us-west-2
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
export ANTHROPIC_SMALL_FAST_MODEL=us.anthropic.claude-3-5-haiku-20241022-v1:0
export DISABLE_TELEMETRY=1

# Optional: Enable debug logging
# export ANTHROPIC_LOG=debug

# Reload shell
source ~/.bashrc

# Verify environment variables
echo "AWS_PROFILE: $AWS_PROFILE"
echo "AWS_REGION: $AWS_REGION"
echo "CLAUDE_CODE_USE_BEDROCK: $CLAUDE_CODE_USE_BEDROCK"
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"

# Test
claude -p "hello from bedrock"
```

---

## Optional: Override Model Per Query

Use CLI flags to override the default model:

```bash
# Use Haiku for a quick query
claude --model claude-haiku-4-5-20251001-v1-project -p "fast query"

# For Bedrock users
claude --model us.anthropic.claude-3-5-haiku-20241022-v1:0 -p "fast query"
```

---

## Optional: Project-Specific Settings

Create `.claude/settings.json` in your project for tool permissions:

```bash
mkdir -p .claude
```

Create `.claude/settings.json`:
```json
{
  "permissions": {
    "bash": "ask",
    "edit": "allow",
    "read": "allow"
  }
}
```

**Note:** API keys and model settings go in `~/.bashrc` environment variables, NOT in settings files

---

## Next Steps

- **Use Claude in terminal**: `claude -p "your prompt"` or `claude` for interactive mode
- **Use Claude in VSCode**: Install Claude Code extension and use sidebar panel
- **For advanced usage**: See full documentation at https://docs.anthropic.com/claude-code

## Additional Resources

- **PNNL Wiki**: https://wiki.pnnl.gov/spaces/AICODINGASSISTANTSFORSOFTWAREENGINEERS
- **Claude Code GitHub**: https://github.com/anthropics/claude-code
