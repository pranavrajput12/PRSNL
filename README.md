# Knowledge Vault - Local-First Personal Knowledge Management

A keyboard-first, zero-friction vault that captures any digital artifact with one shortcut and resurfaces it in < 1s. Built using AI-collaborative development.

## 🤖 AI Agents

- **Claude Code**: Primary architect and complex feature lead
- **Windsurf**: Scaffolds new modules and performs large-scale refactors. See [WINDSURF.md](WINDSURF.md).
- **Gemini CLI**: Minor edits and quick fixes. See [GEMINI.md](GEMINI.md).

## 📋 Getting Started

### For Users
1. **Start here**: [User Guide](USER_GUIDE.md) - How to work with multiple AIs
2. Understand [Git Merge Strategy](GIT_MERGE_STRATEGY.md) - Automated conflict prevention

### For AI Agents
1. Read the [AI Collaboration Guide](AI_COLLABORATION_GUIDE.md)
2. Review [AI Boundaries](BOUNDARIES.md) to understand agent limits
3. Check [Progress Tracker](PROGRESS_TRACKER.md) for active work
4. Check [open issues](../../issues) for available tasks
5. Review [open pull requests](../../pulls) to avoid duplicate work
6. Update Progress Tracker before starting work
7. Create a feature branch and start contributing

## 🚀 Quick Start (Local Development)

```bash
# Clone the repository
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL

# Start the vault locally
docker-compose up -d

# Install browser extension
# Chrome: chrome://extensions → Load unpacked → select /extension

# Access the vault
# Press Ctrl+Shift+Space (or Cmd+Shift+Space on Mac)
```

## 🎯 Key Features

- **One-Key Capture**: Ctrl+Shift+S saves any webpage instantly
- **Instant Search**: < 1s hybrid search across 100k+ items
- **Local-First**: Everything runs on YOUR machine, zero cloud costs
- **Keyboard-Only**: Navigate without touching your mouse
- **AI-Powered**: Local Llama 3 for smart summaries and tags

## 📁 Project Structure

```
.
├── backend/              # FastAPI backend application
│   ├── api/             # API endpoints
│   ├── core/            # Core business logic
│   ├── models/          # Database models
│   └── services/        # External services
├── frontend/            # SvelteKit web interface
│   ├── src/            # Frontend source
│   └── static/         # Static assets
├── extension/          # Browser extension
│   ├── manifest.json   # Extension config
│   └── src/           # Extension source
├── docker/            # Docker configurations
├── scripts/           # Utility scripts
├── docs/              # Project documentation
│   ├── ARCHITECTURE.md # System design
│   └── AI_GUIDES/     # AI collaboration docs
└── docker-compose.yml # Local development setup
```

## 💻 Tech Stack

- **Backend**: FastAPI + PostgreSQL (pgvector) + Redis + Celery
- **Frontend**: SvelteKit + TypeScript  
- **Search**: Hybrid (BM25 + Vector embeddings)
- **LLM**: Ollama + Llama 3 (local) / Azure OpenAI (fallback)
- **Extension**: Chrome/Firefox Manifest V3
- **Deployment**: Docker Compose (local)

## 📊 Performance Targets

- Capture latency: < 3s (90th percentile)
- Search latency: < 1s (95th percentile)  
- Zero monthly costs (local deployment)
- 100k+ items capacity

## 📝 Contributing

All contributions must follow the guidelines in [AI_COLLABORATION_GUIDE.md](AI_COLLABORATION_GUIDE.md).

## 📄 License

[To be determined]

---

*Generated and maintained by AI agents following strict collaboration protocols.*