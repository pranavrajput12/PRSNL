# PRSNL - Personal Knowledge Management System

Your AI-powered personal knowledge base. Capture anything from the web, process it with AI, and find it instantly.

## 🎯 Current Status (2025-07-07)

✅ **PRODUCTION READY**
- **Full Stack Application**: Complete with all core features working
- **Backend APIs**: All endpoints implemented with proper database integration
- **Frontend UI**: Complete with Manchester United red design (#dc143c)
- **Video Support**: Instagram, YouTube, Twitter, TikTok video capture & processing
- **AI Processing**: Multi-provider support (OpenAI, Azure, Anthropic, Ollama)
- **Vision AI**: Image analysis and OCR capabilities
- **Real-time Search**: Full-text search with PostgreSQL
- **Chrome Extension**: Full implementation with context menus & shortcuts
- **Development Environment**: Docker setup with PostgreSQL, Ollama, and all services
- **Production Config**: Docker production setup with monitoring

✅ **WORKING FEATURES**
- **AI-Powered Capture**: Automatic summarization and tagging with LLMs
- **Multi-Provider AI Router**: Intelligent routing between AI providers
- **Universal Video Support**: Download from YouTube, Instagram, Twitter, TikTok
- **Timeline View**: Browse captured content chronologically
- **Smart Search**: Full-text search across all content
- **Individual Item Pages**: View, edit, and manage each item
- **Tag Management**: AI-generated and manual tags
- **Vision Processing**: Extract text and analyze images
- **Modern UI**: Dark theme with smooth animations
- **Storage Management**: Automatic cleanup and optimization
- **Health Monitoring**: Service status and metrics
- **Telegram Bot**: Capture content via Telegram (API ready)

✅ **RECENTLY COMPLETED**
- **Semantic Search**: Find similar content using embeddings (Backend: Gemini, UI: Windsurf)
- **WebSocket Streaming**: Real-time AI responses (Backend: Claude)
- **Video Transcription**: Speech-to-text for searchable transcripts (Gemini)

🚧 **IN DEVELOPMENT**
- **AI Insights Dashboard**: Visualize knowledge patterns (Not started)

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd PRSNL
```

### 2. Start all services with Docker
```bash
# Start PostgreSQL, Ollama, and other services
docker compose up -d

# Check service health
docker compose ps
```

### 3. Start the Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API available at http://localhost:8000
```

### 4. Start the Frontend
```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:3002
```

### 5. Load Chrome Extension (Optional)
```bash
# 1. Go to chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select the /extension folder
```

### 6. Access the Application
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

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
- **Multi-AI Support**: OpenAI, Azure OpenAI, Anthropic, and Ollama
- **Privacy**: Your data stays under your control
- **Speed**: Sub-second search on 100k+ items
- **Scalable**: Microservices architecture with Docker
- **Design**: Manchester United red (#dc143c) with Mulish + Poppins fonts

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

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

### Core Documentation
- [API Documentation](./API_DOCUMENTATION.md) - Complete API reference
- [Architecture Overview](./ARCHITECTURE.md) - System design and components
- [Design Language](./DESIGN_LANGUAGE.md) - UI/UX guidelines
- [Developer Guide](./DEVELOPER_GUIDE.md) - Development setup and workflow
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Production deployment instructions

### AI Model Guides
- [GEMINI Guide](./GEMINI.md) - Backend AI infrastructure specialist guide
- [WINDSURF Guide](./WINDSURF.md) - Frontend AI features specialist guide
- [Project Status](./PROJECT_STATUS.md) - Single source of truth for current state

### Project Management
- [Model Activity Log](./MODEL_ACTIVITY_LOG.md) - Detailed work tracking
- [Task Summary](./TASK_SUMMARY.md) - Current progress
- [Consolidated Task Tracker](./CONSOLIDATED_TASK_TRACKER.md) - Unified task management

## 🤝 Contributing

This project uses a multi-AI development workflow:
- **Claude Code**: Architecture, complex implementations, documentation
- **Windsurf**: Frontend scaffolding, multi-file generation
- **Gemini CLI**: Utility functions, minor fixes, data generation

See [AI_AGENTS.md](../docs/ai-collaboration/AI_AGENTS.md) for collaboration details.

## 📝 License

MIT License - see LICENSE file for details.