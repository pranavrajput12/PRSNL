# Claude Code Prompt: Integrate Cipher AI Memory System

Please help me integrate Cipher, an AI memory layer that provides persistent context across development sessions. Here's what I need:

## 1. Initial Setup
- Install Cipher: `npm install -g @cipher-ai/cli`
- Run `cipher init` in project root
- Create `.cipher/config.json` with Azure OpenAI configuration
- Add `.cipher/memory/` to `.gitignore`

## 2. Configuration Files Needed

### .cipher/config.json
```json
{
  "version": "0.2.0",
  "ai": {
    "provider": "azure-openai",
    "apiKey": "${AZURE_OPENAI_API_KEY}",
    "endpoint": "${AZURE_OPENAI_ENDPOINT}",
    "deployments": {
      "chat": "gpt-4",
      "embeddings": "text-embedding-ada-002"
    }
  },
  "memory": {
    "vectorStore": "local",
    "maxMemories": 1000
  }
}
```

### Environment Variables (.env)
```
AZURE_OPENAI_API_KEY=<my-key>
AZURE_OPENAI_ENDPOINT=<my-endpoint>
AZURE_OPENAI_API_VERSION=2023-12-01-preview
CIPHER_AUTO_SYNC=true
```

## 3. Key Integration Points

1. **Update CLAUDE.md** with Cipher commands and usage patterns
2. **Pre-seed memories** about our architecture:
   - Database configuration and ports
   - API structure and authentication method
   - Key dependencies and their versions
   - Common debugging solutions

3. **Add MCP server configuration** for Claude Code integration:
```json
{
  "servers": {
    "cipher": {
      "command": "npx",
      "args": ["@cipher-ai/mcp-server", "--project", "${workspaceFolder}"]
    }
  }
}
```

## 4. Implementation Tasks

1. Create initial setup script at `scripts/setup-cipher.js`
2. Add Cipher commands to package.json scripts:
   ```json
   "cipher:recall": "cipher recall",
   "cipher:sync": "cipher sync",
   "cipher:stats": "cipher stats"
   ```
3. Document team usage patterns in README
4. Set up CI/CD memory sync (optional)

## 5. Usage Examples I Want Working

```bash
# Store solutions
cipher "Fixed [issue] by [solution]"

# Recall context
cipher recall "database configuration"
cipher recall "error: connection refused"

# Pattern management
cipher pattern "Controller pattern: [example]" --tag patterns
```

## Key Benefits to Highlight
- Persistent memory across Claude Code sessions
- Never re-explain architecture or debug the same issue twice
- Team knowledge sharing through exportable memories
- Automatic context loading via MCP integration

Please implement this step by step, starting with the basic setup and then adding the advanced features. Make sure to test the integration with a few sample memories.

Project context: [Add your specific project details here - framework, database, key features]