# PRSNL - Personal Knowledge Management System

A powerful personal knowledge management system with AI-powered search, video processing, and intelligent content organization. Built using AI-collaborative development.

## 🎯 Quick Status

**FULLY OPERATIONAL** - Version 2.0+ with latest web scraping fixes (2025-07-09)

📊 **[Complete Project Status](PROJECT_STATUS_CONSOLIDATED.md)** - Single source of truth for all project information

🏠 **[Local Development Guide](LOCAL_DEVELOPMENT_GUIDE.md)** - Setup and development workflow

## 🚀 Quick Start

### Development Environment
```bash
# Start PostgreSQL (ARM64)
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start Backend
cd PRSNL/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend  
cd PRSNL/frontend
npm install
npm run dev

# Access Application
open http://localhost:3002

# API Documentation
open http://localhost:8000/docs
```

### Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:3002
```

## 🌟 Key Features

1. **Universal Capture**: Articles, videos, notes with meta-tag extraction
2. **AI-Powered Search**: Semantic and keyword search with RAG
3. **Video Support**: YouTube, Vimeo, Twitter with streaming and transcription  
4. **Knowledge Chat**: Chat with your captured content via WebSocket
5. **Smart Processing**: AI-generated summaries, tags, and insights
6. **Import System**: JSON, bookmarks, bulk URL import
7. **Timeline View**: Chronological feed with infinite scroll
8. **Beautiful UI**: Manchester United themed interface (#dc143c)

## 🏗️ Architecture

- **Frontend**: SvelteKit on port 3002 (TypeScript, TailwindCSS)
- **Backend**: FastAPI on port 8000 (Python, PostgreSQL)
- **Database**: PostgreSQL 16 with pgvector on port 5433
- **AI**: Azure OpenAI exclusive (GPT-4, Whisper, Embeddings)
- **Platform**: ARM64 (Apple Silicon) optimized

## 📚 Documentation Structure

### Root Level (You Are Here)
- **[PROJECT_STATUS_CONSOLIDATED.md](PROJECT_STATUS_CONSOLIDATED.md)** - Complete project overview
- **[LOCAL_DEVELOPMENT_GUIDE.md](LOCAL_DEVELOPMENT_GUIDE.md)** - Development setup
- **[README.md](README.md)** - This file

### Main Project Documentation
- **[PRSNL/CLAUDE.md](PRSNL/CLAUDE.md)** - Main development guide
- **[PRSNL/QUICK_REFERENCE.md](PRSNL/QUICK_REFERENCE.md)** - Quick commands
- **[PRSNL/PROJECT_STATUS_REPORT.md](PRSNL/PROJECT_STATUS_REPORT.md)** - Detailed status

### Technical Documentation  
- **[docs/](docs/)** - Architecture, interfaces, collaboration guides
- **[PRSNL-iOS/](PRSNL-iOS/)** - iOS application documentation

## 🤖 AI Team Coordination

This project is built collaboratively by AI agents:

- **🎨 Claude**: Complex features, architecture, integration, debugging
- **🚀 Windsurf**: Simple frontend tasks, UI polish  
- **🧠 Gemini**: Simple backend tasks, testing, scripts

## 🎉 Recent Major Updates

### Web Scraping System Fixed (2025-07-09)
- ✅ Meta-tag extraction working perfectly
- ✅ AI suggestions returning proper content
- ✅ All backend APIs integrated with new scraper
- ✅ HTTP compression issues resolved

### Version 2.0 Foundation (2025-01-08)  
- ✅ Complete Azure OpenAI integration
- ✅ Duplicate detection system
- ✅ Video streaming with download-on-demand
- ✅ WebSocket chat with RAG
- ✅ Frontend-backend connection stabilized

## 📱 Usage

### Main Features
- **Timeline**: http://localhost:3002 - Browse all saved content
- **Capture**: http://localhost:3002/capture - Save new content with AI suggestions
- **Search**: http://localhost:3002/search - Keyword and semantic search
- **Chat**: http://localhost:3002/chat - Chat with your knowledge base
- **Videos**: http://localhost:3002/videos - Video library with transcripts
- **Insights**: http://localhost:3002/insights - AI-generated insights

### API Endpoints
- **REST API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/chat/{client_id}

## 🔧 Configuration

### Backend (.env file in /PRSNL/backend)
```env
DATABASE_URL=postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### Frontend (.env file in /PRSNL/frontend)
```env
PUBLIC_API_URL=http://localhost:8000
```

---

**📋 For Complete Details**: See [PROJECT_STATUS_CONSOLIDATED.md](PROJECT_STATUS_CONSOLIDATED.md)

**🛠️ For Development Setup**: See [LOCAL_DEVELOPMENT_GUIDE.md](LOCAL_DEVELOPMENT_GUIDE.md)

**📄 License**: MIT License

**🙏 Built with AI collaboration** using Claude, Windsurf, and Gemini.