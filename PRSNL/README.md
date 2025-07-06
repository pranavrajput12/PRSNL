# PRSNL - Personal Knowledge Base

Your keyboard-first, zero-friction second brain. Capture anything with Ctrl+Shift+S, find it in < 1s.

## 🎯 Current Status (2025-01-06)

✅ **COMPLETED FEATURES**
- **Frontend UI**: Complete with Manchester United red design (#dc143c)
- **Chrome Extension**: Full implementation with context menus & shortcuts
- **Sample Data**: 25 realistic items across all pages  
- **Settings Page**: Complete configuration interface
- **Development Environment**: Ready with Docker, scripts, and database

🚧 **NEXT STEPS**
- Backend API integration
- Real-time search functionality
- Production deployment

## 🚀 Quick Start

### Frontend Development
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

### Chrome Extension
```bash
# Load extension in Chrome
# 1. Go to chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select the /extension folder
```

### Full Stack (Docker)
```bash
# Start all services
docker-compose up -d

# Install backend dependencies
cd backend && pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload
```

## 📁 Project Structure

```
PRSNL/
├── backend/          # FastAPI backend
│   ├── app/          # Application code
│   ├── core/         # Core services (capture, search)
│   └── db/           # Database schemas and init
├── frontend/         # SvelteKit dashboard  
│   ├── src/lib/      # Components and utilities
│   └── src/routes/   # Pages (home, timeline, search, settings)
├── extension/        # Chrome extension
│   ├── manifest.json # Extension configuration
│   ├── popup.html    # Popup interface
│   └── options.html  # Settings page
├── overlay/          # Electron overlay (global search)
├── docker/           # Docker configurations
├── scripts/          # Development and deployment scripts
└── tests/            # Test suites
```

## 🧠 Architecture

- **Local-First**: Everything runs on your machine
- **Cost**: $0/month (uses Ollama for local LLM)
- **Privacy**: Your data never leaves your computer
- **Speed**: Sub-second search on 100k+ items
- **Design**: Manchester United red (#dc143c) with Mulish + Poppins fonts

See [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for detailed system design.

## 🎨 Design System

### Colors
- **Primary**: Manchester United Red (#dc143c)
- **Background**: Dark theme (#0a0a0a, #1a1a1a, #2a2a2a)
- **Text**: White (#ffffff) with gray variants (#b3b3b3, #666)

### Typography
- **Display Font**: Poppins (headings, buttons)
- **Body Font**: Mulish (body text, interface)

### Keyboard Shortcuts
- **⌘N**: Quick capture
- **⌘K**: Search
- **⌘T**: Timeline
- **⌘H**: Home
- **⌘+Shift+S**: Capture page (extension)
- **⌘+Shift+E**: Capture selection (extension)

## 🔧 Development

### Prerequisites
- Node.js 18+
- Python 3.8+
- Docker & Docker Compose
- Chrome browser (for extension testing)

### Environment Setup
```bash
# Run setup script
./scripts/setup_dev.sh

# Copy environment template
cp .env.example .env

# Start development servers
npm run dev        # Frontend (port 3000)
python app/main.py # Backend (port 8000)
```

### Sample Data
The frontend includes 25 realistic sample items covering:
- Tech articles (GitHub, Medium, Verge)
- Learning content (Coursera, Khan Academy)
- Design resources (Figma, Behance)
- Personal notes and recipes
- Science and space content

## 📖 Documentation

- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Implementation Plan](../docs/IMPLEMENTATION_PLAN.md)
- [Progress Tracker](../PROGRESS_TRACKER.md)
- [Task Summary](../TASK_SUMMARY.md)
- [AI Collaboration Workflow](../docs/ai-collaboration/SIMPLIFIED_WORKFLOW.md)

## 🤝 Contributing

This project uses a multi-AI development workflow:
- **Claude Code**: Architecture, complex implementations, documentation
- **Windsurf**: Frontend scaffolding, multi-file generation
- **Gemini CLI**: Utility functions, minor fixes, data generation

See [AI_AGENTS.md](../docs/ai-collaboration/AI_AGENTS.md) for collaboration details.

## 📝 License

MIT License - see LICENSE file for details.