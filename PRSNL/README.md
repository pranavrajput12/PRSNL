# PRSNL - Personal Knowledge Base

Your keyboard-first, zero-friction second brain. Capture anything with Ctrl+Shift+S, find it in < 1s.

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Install dependencies
cd backend && pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload
```

## 📁 Project Structure

```
PRSNL/
├── backend/          # FastAPI backend
├── frontend/         # SvelteKit dashboard  
├── extension/        # Browser extension
├── docker/          # Docker configs
├── scripts/         # Utility scripts
└── tests/           # Test suites
```

## 🧠 Architecture

- **Local-First**: Everything runs on your machine
- **Cost**: $0/month (uses Ollama for local LLM)
- **Privacy**: Your data never leaves your computer
- **Speed**: Sub-second search on 100k+ items

See [ARCHITECTURE.md](../ARCHITECTURE.md) for details.