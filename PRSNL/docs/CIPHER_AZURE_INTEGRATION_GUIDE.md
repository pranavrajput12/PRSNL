# Cipher Azure OpenAI Integration Guide

This guide documents the complete setup and troubleshooting process for integrating Cipher AI memory layer with Azure OpenAI in Claude Code.

## Overview

Cipher is an open-source memory layer for coding agents that integrates with Claude Code via MCP (Model Context Protocol). This guide specifically covers Azure OpenAI integration, which has unique challenges due to Cipher's CLI validation bug.

## Prerequisites

- Claude Code installed
- Node.js with npm/npx
- Azure OpenAI subscription with:
  - API Key
  - Endpoint URL (e.g., `https://your-resource.openai.azure.com/`)
  - Deployment name (e.g., `gpt-4.1`)

## Installation

```bash
# Install Cipher globally
npm install -g @byterover/cipher

# Verify installation
cipher --version
```

## Configuration Structure

### 1. Project Directory Structure
```
/your-project/
├── .mcp.json              # MCP server configuration
└── memAgent/
    └── cipher.yml         # Cipher agent configuration
```

### 2. Create `memAgent/cipher.yml`

```yaml
# MCP Servers (optional)
mcpServers: {}

# LLM Configuration for Azure OpenAI
llm:
  provider: azure
  model: your-deployment-name    # e.g., gpt-4.1
  apiKey: $AZURE_OPENAI_API_KEY
  maxIterations: 50
  azure:
    endpoint: $AZURE_OPENAI_ENDPOINT
    deploymentName: your-deployment-name

# System Prompt
systemPrompt:
  enabled: true
  content: |
    You are an AI assistant with access to a persistent memory system.
    You can store and retrieve information across conversations.
```

### 3. Configure `.mcp.json`

```json
{
  "mcpServers": {
    "cipher": {
      "command": "cipher",
      "args": [
        "--mode",
        "mcp",
        "--agent",
        "/absolute/path/to/your/project/memAgent/cipher.yml"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-dummy-key-for-cli-validation",
        "AZURE_OPENAI_API_KEY": "your-actual-azure-api-key",
        "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/"
      }
    }
  }
}
```

**CRITICAL NOTES:**
1. Use absolute path for `--agent` argument
2. Include dummy `OPENAI_API_KEY` to bypass CLI validation bug
3. Set real Azure credentials in environment variables

## Known Issues and Solutions

### Issue 1: CLI Validation Bug
**Symptom**: "No API key or Ollama configuration found" error  
**Cause**: Cipher CLI only checks for OPENAI_API_KEY, not AZURE_OPENAI_API_KEY  
**Solution**: Set dummy `OPENAI_API_KEY="sk-dummy-key-for-cli-validation"`

### Issue 2: Configuration Not Found
**Symptom**: "Failed to load agent config" error  
**Cause**: Relative path issues or missing config structure  
**Solution**: 
- Use absolute path in `--agent` argument
- Ensure cipher.yml has all required sections

### Issue 3: Invalid LLM Configuration
**Symptom**: "Invalid LLM configuration provided to createContextManager"  
**Cause**: Incorrect provider name or missing Azure configuration  
**Solution**: 
- Use `provider: azure` (not `azure_openai`)
- Include nested `azure:` section in config

### Issue 4: Project Config Override
**Symptom**: Only seeing some MCP servers, not all configured ones  
**Cause**: Project-level `.mcp.json` overrides global settings  
**Solution**: Add all desired MCP servers to project `.mcp.json`

## Debugging Steps

### 1. Check MCP Server Status
```bash
# In Claude Code, run:
/mcp
```

Expected output should show cipher as "connected".

### 2. Check Cipher Logs
```bash
# Find log location (varies by system)
tail -f /var/folders/*/T/cipher-mcp.log

# Look for:
# - "Azure OpenAI service initialized"
# - "MCP server initialized successfully"
```

### 3. Test Cipher Directly
```bash
# Set environment variables
export OPENAI_API_KEY="sk-dummy-key-for-cli-validation"
export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Test MCP mode
cipher --mode mcp --agent /path/to/memAgent/cipher.yml
```

### 4. Verify Configuration Loading
Look for log entries showing:
- "Loading agent config from /path/to/memAgent/cipher.yml"
- "Azure OpenAI service initialized with deployment: your-deployment"

## Working Configuration Example

Here's a complete working example for PRSNL project:

**memAgent/cipher.yml:**
```yaml
mcpServers: {}

llm:
  provider: azure
  model: gpt-4.1
  apiKey: $AZURE_OPENAI_API_KEY
  maxIterations: 50
  azure:
    endpoint: $AZURE_OPENAI_ENDPOINT
    deploymentName: gpt-4.1

systemPrompt:
  enabled: true
  content: |
    You are an AI assistant helping with the PRSNL personal knowledge management system.
```

**.mcp.json:**
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {}
    },
    "playwright": {
      "command": "node",
      "args": [
        "/Users/pronav/.nvm/versions/node/v20.18.1/bin/mcp-server-playwright"
      ],
      "env": {}
    },
    "cipher": {
      "command": "cipher",
      "args": [
        "--mode",
        "mcp",
        "--agent",
        "/Users/pronav/Personal Knowledge Base/memAgent/cipher.yml"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-dummy-key-for-cli-validation",
        "AZURE_OPENAI_API_KEY": "1U6RGbb4XrVh4LUqG5qrNLHd1hvHeCDqseSThAayqhclju9nUCtTJQQJ99BAACHYHv6XJ3w3AAABACOG6tdK",
        "AZURE_OPENAI_ENDPOINT": "https://airops.openai.azure.com/"
      }
    }
  }
}
```

## Populating Cipher Memory

Once configured, populate Cipher with project context:

```bash
# Add project overview
cipher "PRSNL is a Personal Knowledge Management system with FastAPI backend, SvelteKit frontend, PostgreSQL database, and AI integrations"

# Add technical details
cipher "PRSNL uses port 3004 for frontend dev, 8000 for backend API, 5432 for PostgreSQL"

# Add architecture notes
cipher "PRSNL runs on ARM64 architecture with local PostgreSQL, not Docker database"
```

## Verification

Test the integration in Claude Code:
```
/mcp
# Select cipher > ask_cipher
# Ask: "What is PRSNL?"
```

## Troubleshooting Checklist

- [ ] Cipher installed globally: `which cipher`
- [ ] Config directory exists: `ls -la memAgent/`
- [ ] cipher.yml has all sections: mcpServers, llm, systemPrompt
- [ ] Provider is `azure`, not `azure_openai`
- [ ] Absolute path used in .mcp.json
- [ ] Dummy OPENAI_API_KEY set for CLI bypass
- [ ] Real Azure credentials in environment
- [ ] Claude Code restarted after config changes
- [ ] Logs show "Azure OpenAI service initialized"

## References

- [Cipher GitHub Repository](https://github.com/campfirein/cipher)
- [Cipher Documentation](https://docs.byterover.dev/cipher)
- [MCP Documentation](https://modelcontextprotocol.io/)

Last Updated: 2025-08-01