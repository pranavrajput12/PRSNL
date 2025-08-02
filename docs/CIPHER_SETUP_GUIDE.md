# Cipher MCP Setup Guide

## 🎯 Quick Status: ✅ WORKING - 21 Tools Available in Aggregator Mode

Successfully configured Cipher MCP with Azure OpenAI integration, providing 21 AI development tools through Claude Code.

## 🚀 Overview

Cipher MCP (Model Context Protocol) integration transforms your development workflow by providing:
- **21 AI development tools** via aggregator mode
- **Persistent memory** across development sessions  
- **File operations** with AI context
- **Reasoning patterns** for complex problem solving
- **Azure OpenAI integration** through OpenAI-compatible interface

## 📋 Prerequisites

### Required Services
- **Azure OpenAI** subscription with deployments:
  - GPT-4.1 (or gpt-4) for language modeling
  - text-embedding-ada-002 for embeddings
- **Claude Code CLI** installed and configured
- **Node.js** v18+ for @byterover/cipher package
- **PostgreSQL** database (optional, for team features)
- **Qdrant Cloud** account (optional, for vector search)

### Installation
```bash
# Install Cipher package globally
npm install -g @byterover/cipher

# Verify installation
cipher --version
```

## ⚙️ Configuration Steps

### Step 1: Create Environment Configuration

Create `.env.cipher` in your project root:

```bash
# Cipher AI Memory Layer Environment Configuration
# Add your API keys here - DO NOT commit this file to version control

# Azure OpenAI Configuration (Primary LLM & Embedding Provider)
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_GPT4_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# OpenAI-compatible configuration for Cipher
OPENAI_API_KEY=your_azure_api_key_here
OPENAI_BASE_URL=https://your-endpoint.openai.azure.com
ANTHROPIC_API_KEY=sk-ant-dummy-key-for-cipher-fallback

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DATABASE_POOL_SIZE=10
DATABASE_SSL=false
DATABASE_SCHEMA=public

# Cipher Configuration
CIPHER_CONFIG_PATH=./memAgent/cipher.yml
CIPHER_LOG_LEVEL=info
CIPHER_MEMORY_AUTO_GENERATE=true
CIPHER_MEMORY_MAX_ENTRIES=1000

# 🚨 CRITICAL: MCP Server Configuration for Aggregator Mode
MCP_SERVER_PORT=3001
MCP_SERVER_HOST=localhost
MCP_SERVER_MODE=aggregator              # Enables 21 tools instead of just 1
MCP_CONFLICT_RESOLUTION=prefix          # Handle tool name conflicts
MCP_TOOL_TIMEOUT=30000                  # 30 second timeout

# Vector Store Configuration (Optional)
VECTOR_STORE_TYPE=qdrant
QDRANT_URL=https://your-qdrant-url:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=cipher_patterns

# Team Synchronization Settings (Optional)
TEAM_SYNC_ENABLED=true
TEAM_SYNC_INTERVAL=5000
TEAM_NAMESPACE=your-project-name
```

### Step 2: Configure cipher.yml

Update `memAgent/cipher.yml` with the correct provider settings:

```yaml
# Primary LLM Configuration - OpenAI-compatible with Azure OpenAI
llm:
  # 🚨 CRITICAL: Use 'openai' provider, NOT 'azure'
  provider: openai
  model: gpt-4.1
  apiKey: $OPENAI_API_KEY
  baseUrl: $OPENAI_BASE_URL
  maxIterations: 50

# Embedding Configuration for Vector Search
embedding:
  type: openai
  model: text-embedding-ada-002
  apiKey: $OPENAI_API_KEY
  baseUrl: $OPENAI_BASE_URL
  dimensions: 1536
  timeout: 30000
  maxRetries: 3

# Vector Store Configuration
vectorStore:
  type: qdrant
  url: $QDRANT_URL
  apiKey: $QDRANT_API_KEY
  collection: $QDRANT_COLLECTION
  embedDimension: 1536
  similarity: cosine

# Database Configuration for Team Collaboration
database:
  type: postgresql
  connectionString: $DATABASE_URL
  poolSize: $DATABASE_POOL_SIZE
  ssl: $DATABASE_SSL
  schema: $DATABASE_SCHEMA

# 🚨 CRITICAL: MCP Tools Configuration - Enables all tools in aggregator mode
mcpTools:
  # Core memory operations
  - ask_cipher
  - add_to_cipher
  - update_cipher
  - delete_from_cipher
  
  # Search and retrieval
  - search_cipher
  - list_cipher_entries
  - export_cipher_memory

# Memory Configuration
memory:
  autoGenerate: true
  maxEntries: 1000
  categories:
    - components
    - architecture
    - api-endpoints
    - bug-fixes
    - architectural-decisions

# Team Collaboration Features
collaboration:
  realTimeSync: true
  broadcastUpdates: true
  attributeMemories: true
  collectiveIntelligence:
    enabled: true
    patternRecognition: true
    solutionSharing: true
```

### Step 3: Configure Claude Code MCP

Update your `.mcp.json` configuration file:

```json
{
  "mcpServers": {
    "cipher": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd '/path/to/your/project' && source .env.cipher && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_BASE_URL=\"$OPENAI_BASE_URL\" MCP_SERVER_MODE=\"aggregator\" npx @byterover/cipher --mode mcp --agent memAgent/cipher.yml"
      ],
      "env": {}
    }
  }
}
```

**Key Points:**
- Use `/bin/bash` command to source environment variables
- Include `source .env.cipher` to load configuration
- Explicitly pass critical environment variables
- Remove any conflicting MCP servers that might cause EPIPE errors

## 🛠️ Available Tools (21 Total)

### File Operations (14 tools)
- `read_file` - Read file contents
- `read_text_file` - Read text files specifically
- `read_media_file` - Read media file metadata
- `read_multiple_files` - Read multiple files at once
- `write_file` - Write content to files
- `edit_file` - Edit existing files
- `create_directory` - Create directories
- `list_directory` - List directory contents
- `list_directory_with_sizes` - List with file sizes
- `directory_tree` - Show directory tree structure
- `move_file` - Move/rename files
- `search_files` - Search within files
- `get_file_info` - Get file metadata
- `list_allowed_directories` - List accessible directories

### Memory & AI Operations (7 tools)
- `ask_cipher` - General AI interactions with memory context
- `cipher_extract_and_operate_memory` - Extract and store patterns
- `cipher_memory_search` - Search stored memories
- `cipher_store_reasoning_memory` - Store reasoning patterns
- `cipher_extract_reasoning_steps` - Extract reasoning steps
- `cipher_evaluate_reasoning` - Evaluate reasoning quality
- `cipher_search_reasoning_patterns` - Search reasoning patterns

## 🧪 Testing Your Setup

### 1. Verify Environment Loading
```bash
cd /path/to/your/project
source .env.cipher
echo "MCP_SERVER_MODE: $MCP_SERVER_MODE"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
```

### 2. Test Cipher Installation
```bash
npx @byterover/cipher --version
```

### 3. Test MCP Mode
```bash
# This should start without errors and show aggregator mode in logs
source .env.cipher && npx @byterover/cipher --mode mcp --agent memAgent/cipher.yml
```

### 4. Verify in Claude Code
- Restart Claude Code completely (Cmd+Q, reopen)
- Check that "cipher" MCP server shows 21 tools (not just 1)
- Test a simple file operation or memory search

## 🔧 Troubleshooting

### Problem: Only 1 tool visible (ask_cipher)
**Solution:**
- Verify `MCP_SERVER_MODE=aggregator` in .env.cipher
- Check that .mcp.json sources the environment file
- Restart Claude Code completely

### Problem: "No API key found" error
**Solution:**
- Verify Azure OpenAI credentials in .env.cipher
- Ensure OPENAI_API_KEY and AZURE_OPENAI_API_KEY are identical
- Check that baseUrl doesn't have trailing slash

### Problem: Connection timeout or EPIPE errors
**Solution:**
- Remove conflicting MCP servers from .mcp.json
- Use only the cipher server initially
- Check that file paths in .mcp.json are absolute

### Problem: 404 Resource not found
**Solution:**
- Verify Azure OpenAI endpoint URL format
- Check deployment names match your Azure setup
- Ensure API version is correct (2025-01-01-preview)

### Problem: Embedding/Vector search failures
**Solution:**
- Verify Qdrant Cloud URL includes port :6333
- Check Qdrant API key and collection name
- Test with local vector store as fallback

## 📊 Success Indicators

Your setup is working correctly when:
- ✅ Claude Code shows 21 tools under "cipher" MCP server
- ✅ File operations work without errors
- ✅ Memory search returns relevant results
- ✅ No API key or connection errors in logs
- ✅ Tools respond within reasonable time (< 10 seconds)

## 🎯 Development Workflow Enhancement

With Cipher MCP properly configured, you gain:

### Automatic Context Capture
- Code patterns are automatically stored
- Solutions are indexed for future reference
- Architectural decisions are preserved

### Enhanced Problem Solving
- Search previous solutions to similar problems
- Access reasoning patterns from past work
- Build on collective development intelligence

### Seamless File Operations
- AI-aware file reading and writing
- Context-preserving code modifications
- Intelligent directory navigation

## 🔗 Related Documentation

- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Full development environment setup
- [EXTERNAL_INTERFACES.md](EXTERNAL_INTERFACES.md) - API and tool interfaces
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture including Cipher
- [README.md](../README.md) - Project overview and quick start

## 📝 Additional Resources

- [Cipher GitHub Repository](https://github.com/campfirein/cipher)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)  
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

---

**Status**: ✅ Successfully implemented and tested with 21 tools available in aggregator mode.
**Last Updated**: August 2, 2025
**Configuration Verified**: Azure OpenAI + Cipher MCP + Claude Code integration working perfectly.