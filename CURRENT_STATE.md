# Current Project State - PRSNL Knowledge Vault

## 🎯 Project Overview
Building **PRSNL** - A keyboard-first, zero-friction personal knowledge vault that runs entirely locally.

## 📁 Current Structure
```
Knowledge-Base/
├── PRSNL/                    # Main application (NEW!)
│   ├── backend/             # FastAPI (Claude Code owns)
│   ├── frontend/            # SvelteKit (Windsurf scaffolds)
│   ├── extension/           # Browser ext (Windsurf scaffolds)
│   ├── docker/              # Docker configs
│   ├── scripts/             # Utilities
│   └── tests/               # Test suites
├── docs/                     # Documentation (MOVED!)
│   ├── ARCHITECTURE.md      # System design
│   └── IMPLEMENTATION_PLAN.md # Roadmap
└── [AI config files in root]
```

## 🔄 Key Updates
1. **Project renamed**: Knowledge Vault → PRSNL
2. **Docs moved**: `/ARCHITECTURE.md` → `/docs/ARCHITECTURE.md`
3. **Code location**: All application code in `/PRSNL/` subfolder
4. **Tech decision**: Using Ollama for local LLM (not cloud-only)

## 👥 Current Task Division

### Claude Code (Me - Lead):
- ✅ Architecture design complete
- ✅ Implementation plan complete
- 🔄 Starting core backend implementation
- Next: Capture API, Search engine, LLM processor

### Windsurf (Scaffolding Specialist):
- ⏳ Waiting for issue to scaffold `/PRSNL/backend/` structure
- ⏳ Will create FastAPI boilerplate
- ⏳ Will scaffold SvelteKit frontend
- ⏳ Will create browser extension structure

### Gemini CLI (Minor Fixes):
- ⏳ Waiting for scaffolding to complete
- ⏳ Will fix import paths
- ⏳ Will update configurations
- ⏳ Will fix any linting issues

## 📋 Active Work
See `/PROGRESS_TRACKER.md` for real-time status.

## 🚀 Next Steps
1. Claude Code creates GitHub issues for scaffolding
2. Windsurf scaffolds project structure
3. Claude Code implements core features
4. Gemini CLI fixes minor issues

## ⚠️ Important Notes
- Everything runs locally (zero cloud costs)
- Using PostgreSQL with pgvector (not separate DBs)
- Ollama for local LLM, Azure only as fallback
- Target: < 1s search on 100k items