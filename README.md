# PRSNL - Personal Knowledge Vault

A keyboard-first, zero-friction vault that captures any digital artifact with one shortcut and resurfaces it in < 1s. Built using AI-collaborative development.

## 🚀 Quick Start

```bash
# Clone and enter directory
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL

# Start everything with one command
make dev

# Open frontend
open http://localhost:3000

# API docs
open http://localhost:8000/docs
```

## 🎯 Features

- **One-Key Capture**: Press `Cmd+Shift+S` to capture any webpage
- **Instant Search**: Press `Cmd+Shift+Space` for global search overlay
- **Smart Processing**: Automatic summarization and tagging with Ollama
- **Local-First**: Everything runs on your machine, no cloud dependencies
- **Zero-Friction**: Keyboard-driven interface for maximum speed

## 🏗️ Architecture

- **Frontend**: SvelteKit with TypeScript
- **Backend**: FastAPI with PostgreSQL
- **Extension**: Chrome extension for web capture
- **Overlay**: Electron app for global search
- **Processing**: Ollama (local) or Azure OpenAI (optional)

## 📖 Documentation

- **[Full Documentation](./docs/)** - All project documentation
- **[Architecture](./docs/ARCHITECTURE.md)** - System design details
- **[AI Collaboration](./docs/ai-collaboration/)** - How we build with AI
- **[Progress Tracker](./PROGRESS_TRACKER.md)** - Current development status

## 🤖 AI Development Team

This project is built collaboratively by AI agents:

- **Claude Code**: Architecture and complex features
- **Windsurf**: Frontend and UI implementation
- **Gemini CLI**: Backend and infrastructure

See [AI Collaboration Guide](./docs/ai-collaboration/) for details.

## 🛠️ Development

```bash
# Install dependencies
cd PRSNL/frontend && npm install
cd ../backend && pip install -r requirements.txt

# Run tests
make test

# Format code
make format

# Stop services
make stop

# Reset database
make reset
```

## 📱 Usage

### Capture
- Browser: Click extension or press `Cmd+Shift+S`
- Direct: Go to http://localhost:3000/capture

### Search
- Global: Press `Cmd+Shift+Space` anywhere
- Web: Go to http://localhost:3000/search

### Browse
- Timeline: http://localhost:3000/timeline
- Tags: Coming soon

## 🔧 Configuration

Create `.env` file:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/prsnl
OLLAMA_BASE_URL=http://localhost:11434
AZURE_OPENAI_API_KEY=your_key_here (optional)
```

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

Built with AI collaboration using Claude, Windsurf, and Gemini.