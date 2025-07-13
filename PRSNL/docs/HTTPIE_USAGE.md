# HTTPie Usage Guide for PRSNL API

HTTPie is a user-friendly command-line HTTP client that makes API debugging much easier than curl. It has been installed for improved developer experience when testing AI API integrations.

## Installation

```bash
brew install httpie
```

## Basic Syntax

```bash
http [METHOD] URL [REQUEST_ITEMS...]
```

## PRSNL API Examples

### Health Check Endpoints

```bash
# Backend health check
http GET localhost:8000/health

# API health check
http GET localhost:8000/api/health

# RAG service health
http GET localhost:8000/api/rag/stats

# AutoAgent status
http GET localhost:8000/api/autoagent/agent-status

# OpenCLIP health
http GET localhost:8000/api/openclip/health

# FireCrawl status
http GET localhost:8000/api/firecrawl/status
```

### Search and Timeline

```bash
# Search for items
http GET localhost:8000/api/search query=="test" limit==5

# Get timeline
http GET localhost:8000/api/timeline limit==10

# Enhanced search
http POST localhost:8000/api/enhanced-search query="machine learning" limit=10
```

### RAG Queries

```bash
# Query RAG system
http POST localhost:8000/api/rag/query \
  Content-Type:application/json \
  query="What is FastAPI?"

# RAG with context
http POST localhost:8000/api/rag/query \
  Content-Type:application/json \
  query="Explain async Python" \
  context_window=10 \
  use_embeddings=true
```

### AutoAgent Integration

```bash
# Process content with AutoAgent
http POST localhost:8000/api/autoagent/process-content \
  Content-Type:application/json \
  content="FastAPI is a modern web framework" \
  title="FastAPI Introduction" \
  existing_tags:='["python", "api"]'

# Create learning path
http POST localhost:8000/api/autoagent/create-learning-path \
  Content-Type:application/json \
  goal="Master FastAPI and async Python" \
  current_knowledge:='["Python basics", "HTTP"]' \
  time_commitment="intensive"

# Explore topic
http POST localhost:8000/api/autoagent/explore-topic \
  Content-Type:application/json \
  topic="AI-powered knowledge management" \
  interests:='["AI", "productivity"]'
```

### LibreChat Integration

```bash
# Chat completion (non-streaming)
http POST localhost:8000/api/ai/chat/completions \
  Content-Type:application/json \
  model="prsnl-gpt-4" \
  messages:='[{"role": "user", "content": "What is PRSNL?"}]'

# Chat completion (streaming)
http --stream POST localhost:8000/api/ai/chat/completions \
  Content-Type:application/json \
  model="prsnl-gpt-4" \
  messages:='[{"role": "user", "content": "Explain async programming"}]' \
  stream=true

# List available models
http GET localhost:8000/api/ai/models
```

### Content Capture

```bash
# Capture URL content
http POST localhost:8000/api/capture \
  Content-Type:application/json \
  url="https://example.com/article" \
  enable_ai_processing=true \
  enable_summarization=true

# Check for duplicates
http POST localhost:8000/api/capture/check-duplicate \
  Content-Type:application/json \
  url="https://example.com/article"
```

### File Upload

```bash
# Upload a file
http --form POST localhost:8000/api/upload \
  file@/path/to/document.pdf \
  enable_ai_processing=true

# Upload with metadata
http --form POST localhost:8000/api/upload \
  file@/path/to/image.png \
  title="Architecture Diagram" \
  tags="architecture,design"
```

### Advanced Features

```bash
# Headers and authentication
http GET localhost:8000/api/protected \
  Authorization:"Bearer YOUR_TOKEN" \
  X-PRSNL-Integration:librechat

# JSON data with nested objects
http POST localhost:8000/api/items \
  Content-Type:application/json \
  title="Test Item" \
  metadata:='{"author": "John", "tags": ["test", "demo"]}'

# Query parameters
http GET localhost:8000/api/search \
  q=="machine learning" \
  limit==20 \
  offset==0 \
  sort==relevance

# Download response
http GET localhost:8000/api/export/json --download

# Pretty print JSON
http GET localhost:8000/api/items/123 --json

# Verbose output for debugging
http --verbose POST localhost:8000/api/rag/query \
  query="test"

# Print only headers
http --headers GET localhost:8000/api/health

# Custom timeout
http --timeout=30 POST localhost:8000/api/heavy-processing
```

## HTTPie vs curl Comparison

### Simple GET request
```bash
# curl
curl http://localhost:8000/api/health

# HTTPie
http localhost:8000/api/health
```

### POST with JSON
```bash
# curl
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?"}'

# HTTPie
http POST localhost:8000/api/rag/query query="What is FastAPI?"
```

### File upload
```bash
# curl
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# HTTPie
http --form POST localhost:8000/api/upload file@document.pdf
```

## Tips and Tricks

1. **Shortcuts**: HTTPie assumes localhost, so `http :8000/api/health` works
2. **JSON by default**: No need to set Content-Type for JSON
3. **Syntax highlighting**: Output is automatically formatted and colored
4. **Sessions**: Use `--session=NAME` to persist cookies/headers
5. **Offline mode**: Use `--offline` to see the request without sending it
6. **Config file**: Create `~/.httpie/config.json` for defaults

## Common Debugging Scenarios

### Debug AutoAgent Integration
```bash
# Check agent status
http GET localhost:8000/api/autoagent/agent-status

# Test with verbose output
http --verbose POST localhost:8000/api/autoagent/process-content \
  content="Test content" \
  title="Test"

# Check response headers
http --headers POST localhost:8000/api/autoagent/analyze \
  content="Sample text"
```

### Debug LibreChat API
```bash
# Test OpenAI compatibility
http POST localhost:8000/api/ai/chat/completions \
  model="prsnl-gpt-4" \
  messages:='[{"role": "user", "content": "Hello"}]' \
  --print=HhBb  # Print request and response headers and body
```

### Debug File Processing
```bash
# Test file upload with AI processing
http --form --verbose POST localhost:8000/api/upload \
  file@test.pdf \
  enable_ai_processing=true \
  --timeout=60
```

## Integration with Development Workflow

1. Add to Makefile for common API tests
2. Create shell scripts for complex API workflows
3. Use in pre-commit hooks to verify API changes
4. Include in CI/CD for API testing

## Resources

- [HTTPie Documentation](https://httpie.io/docs)
- [HTTPie Cheatsheet](https://httpie.io/docs#cheatsheet)
- [PRSNL API Documentation](/docs/API.md)