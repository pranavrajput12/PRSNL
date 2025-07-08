# PRSNL - Personal Knowledge Management System

A powerful personal knowledge management system with AI-powered search, video processing, and intelligent content organization. Built using AI-collaborative development.

## 🚀 Quick Start

```bash
# Clone and enter directory
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL

# Start backend with Docker
docker-compose up -d

# Start frontend
cd frontend
npm install
npm run dev

# Open application
open http://localhost:3002

# API docs
open http://localhost:8000/docs
```

## 🎯 Features

- **Universal Capture**: Save articles, videos, tweets, GitHub repos, and more
- **AI-Powered Search**: Semantic search with RAG-based knowledge chat
- **Video Support**: YouTube, Twitter, Instagram video processing with transcripts
- **Smart Organization**: AI categorization, duplicate detection, and summarization
- **Knowledge Graph**: Discover relationships between your saved content
- **Real-time Chat**: Chat with your knowledge base using Azure OpenAI
- **Beautiful UI**: Manchester United themed interface with premium animations

## 🏗️ Architecture

- **Frontend**: SvelteKit with TypeScript, TailwindCSS
- **Backend**: FastAPI with PostgreSQL, pgvector, Redis
- **AI Processing**: Azure OpenAI (GPT-4.1) exclusive
- **Media Storage**: Local file system with thumbnail generation
- **Real-time**: WebSocket support for chat and streaming

## 📖 Documentation

### Key References
- **[PROJECT_STRUCTURE.md](./PRSNL/PROJECT_STRUCTURE.md)** - Complete file organization
- **[DATABASE_SCHEMA.md](./PRSNL/DATABASE_SCHEMA.md)** - Database structure and mappings
- **[API_DOCUMENTATION.md](./PRSNL/API_DOCUMENTATION.md)** - All API endpoints
- **[PROJECT_STATUS.md](./PRSNL/PROJECT_STATUS.md)** - Current system status

### Guides
- **[DEVELOPER_GUIDE.md](./PRSNL/DEVELOPER_GUIDE.md)** - Development setup
- **[DEPLOYMENT_GUIDE.md](./PRSNL/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[PORT_ALLOCATION.md](./PRSNL/PORT_ALLOCATION.md)** - Service port assignments

## 🤖 AI Development Team

This project is built collaboratively by AI agents (as of 2025-01-08):

- **Claude**: All complex features, frontend, backend, and integration
- **Windsurf**: Simple frontend tasks (styling, tooltips, UI polish)
- **Gemini**: Simple backend tasks (tests, scripts, logging)

See [MODEL_COORDINATION_RULES.md](./PRSNL/MODEL_COORDINATION_RULES.md) for details.

## 🛠️ Development

```bash
# Backend (Docker)
cd PRSNL
docker-compose up -d

# Frontend
cd frontend
npm install
npm run dev

# View logs
docker logs prsnl_backend -f

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up -d
```

## 📱 Usage

### Main Features
- **Timeline**: http://localhost:3002 - Browse all your saved content
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
DATABASE_URL=postgresql://postgres:postgres@db:5432/prsnl
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview
REDIS_URL=redis://redis:6379
```

### Frontend (.env file in /PRSNL/frontend)
```env
PUBLIC_API_URL=http://localhost:8000
```

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

Built with AI collaboration using Claude, Windsurf, and Gemini.