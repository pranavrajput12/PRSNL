# PRSNL - Personal Knowledge Management System v10.0

> **Enterprise-grade AI-powered knowledge management with intelligent knowledge graphs, semantic clustering, and self-improving AI memory**

PRSNL is a cutting-edge personal knowledge management system that captures, processes, and intelligently organizes your digital content using advanced AI technologies. Version 10.0 introduces a complete Knowledge Graph System with AI-powered analytics, automated content processing, and CrewAI pattern analysis automation.

## 🚨 **Latest Release v10.0 (August 2025) - Knowledge Graph Revolution**

### **🧠 Complete Knowledge Graph System (NEW in v10.0)**
- **140+ Entities & 176+ Relationships**: AI-powered cross-content knowledge discovery
- **Semantic Clustering**: 3 algorithms (semantic, structural, hybrid) for intelligent grouping
- **Knowledge Gap Analysis**: Domain coverage analysis with completeness scoring
- **Learning Path Discovery**: Graph traversal algorithms for knowledge connections
- **Real-time Visualization**: Advanced D3.js force-directed graphs with clustering
- **AI-Powered Analytics**: Comprehensive dashboard with insights and recommendations

### **⚡ Auto-Processing System (NEW in v10.0)**
- **4-Step AI Pipeline**: Analysis → Categorization → Summarization → Entity Extraction
- **Background Processing**: Non-blocking with progress monitoring and concurrency controls
- **Entity Extraction**: Cross-feature entity and relationship creation
- **Vector Embeddings**: Automatic semantic search enhancement
- **Queue Management**: Up to 10 concurrent items with intelligent scheduling

### **🤖 CrewAI Pattern Analysis Automation (NEW in v10.0)**
- **Self-Improving AI Memory**: Automated pattern quality improvement using CrewAI
- **Weekly Analysis**: Automated pattern analysis for 20-30% quality improvement
- **Gap Detection**: Identifies missing knowledge areas for targeted improvements
- **Agent Effectiveness**: Claude Code agents become more effective over time
- **Quality Metrics**: Pattern completeness scoring (target: 90%+)

### **🎯 AI Memory Layer Integration (v9.0)**
- **Cipher Integration**: Persistent development context across Claude Code sessions
- **Azure OpenAI Powered**: Intelligent memory storage with embeddings and reasoning
- **Cross-Session Memory**: 50% reduction in development context re-explanation time
- **MCP Protocol**: Seamless integration with Claude Code's Model Context Protocol

### **🎭 Playwright Testing Migration (v8.1)**
- **Complete Puppeteer Replacement**: Removed 146 packages, migrated all test files
- **Cross-Browser Support**: Chromium, Firefox, and WebKit testing capabilities
- **MCP Agent Integration**: playwright-console-monitor for automated testing

## 🚨 **Major Release v8.0 (July 2025) - Authentication & UI Revolution**

### **🔐 Dual Authentication System (NEW in v8.0)**
- **Keycloak Integration**: Enterprise SSO with SAML/OIDC support
- **FusionAuth**: Advanced user lifecycle management with analytics
- **Unified Auth**: Seamless switching between providers
- **Role-Based Access**: Admin, user, and premium role management
- **JWT Tokens**: Secure token-based authentication with refresh
- **User Migration**: Automated migration tools for existing users

### **🎮 Revolutionary 3D Navigation (NEW in v8.0)**
- **Interactive 3D Homepage**: Computer museum aesthetic with functional navigation
- **Component Mapping**: Mac for dashboard, Fan for analytics, Neural board for AI
- **Spatial Memory**: Visual metaphors matching component functions
- **WebGL Performance**: Smooth 60fps 3D rendering with Three.js
- **Responsive Design**: Adaptive 3D elements for all screen sizes

### **🆔 Unique Element ID System (NEW in v8.0)**
- **Automatic ID Generation**: Every UI element gets unique, human-readable IDs
- **Precise Design Communication**: Replace vague descriptions with exact element targeting
- **Visual Inspector Overlay**: Press `Ctrl+Shift+I` to explore element IDs in development
- **10x Faster Design Changes**: "Change `#voice-chat-button-1` color to blue" vs "the third button"
- **Development Tools**: Element registry, copy templates, hover tooltips
- **AI-Friendly**: Perfect for AI-assisted frontend development and debugging

### **🚀 Performance & Reliability (v7.1 Features)**
- **50-70% Faster Processing**: Multimodal document analysis with CrewAI
- **Zero Data Loss**: LangGraph persistent workflows with crash recovery
- **100% Reliable JSON**: OpenAI structured outputs guarantee valid data
- **85%+ Cache Hit Rate**: DragonflyDB (25x faster than Redis)
- **3x Task Throughput**: Celery priority queues for critical operations
- **40% Search Improvement**: LangChain hybrid search (BM25 + embeddings)

## 🌟 **Core Features**

### **🧠 Advanced AI Orchestration**
- **Multi-Agent Workflows**: LangGraph state-based content processing
- **Intelligent Router**: ReAct agent for provider selection and cost optimization
- **Azure OpenAI Integration**: GPT-4 for complex reasoning, GPT-4-mini for speed
- **LibreChat API**: OpenAI-compatible endpoint for third-party integrations
- **Multimodal Processing**: Text, image, code, and document analysis
- **Knowledge Graphs**: 140+ entities with semantic clustering and gap analysis
- **Dreamscape AI**: 5-agent personal intelligence system with CrewAI orchestration
- **Auto-Processing**: 4-step AI pipeline with entity extraction and embeddings

### **📡 Capture & Processing**
- **Universal Capture**: Screenshots, documents, code, web articles, videos
- **AI Summarization**: Intelligent content analysis and key insights
- **Smart Categorization**: Automatic tagging and topic classification
- **OCR Processing**: Extract text from images and PDFs
- **Metadata Extraction**: Rich contextual information preservation

### **🔍 Search & Discovery**
- **Hybrid Search**: Combining keyword and semantic search
- **Vector Similarity**: pgvector-powered content recommendations
- **Natural Language**: Ask questions about your captured content
- **Timeline View**: Visual history of your digital footprint
- **Tag Management**: Hierarchical organization system

### **🛡️ Security & Privacy**
- **Enterprise SSO**: Keycloak SAML/OIDC integration
- **Role-Based Access**: Granular permission management
- **Data Encryption**: At-rest and in-transit protection
- **API Key Management**: Secure token generation and rotation
- **Audit Logging**: Complete activity tracking

### **📊 Analytics & Insights**
- **User Analytics**: Login patterns, activity tracking
- **Content Metrics**: Capture rates, processing statistics
- **AI Insights**: Pattern detection and trend analysis
- **Custom Reports**: Export data in multiple formats
- **Real-time Dashboards**: WebSocket-powered live updates
- **Dreamscape Intelligence**: Personal behavior analysis and persona generation

## 🚀 **Quick Start**

### **Prerequisites**
- **PostgreSQL 16+** with pgvector extension (ARM64 for M1/M2 Macs)
- **Docker** (Rancher Desktop recommended for Mac)
- **Python 3.11+**
- **Node.js 20+**
- **Minimum 8GB RAM**

### **1. Clone and Setup**
```bash
git clone https://github.com/your-username/PRSNL.git
cd PRSNL

# Run automated setup
./setup-development.sh
```

### **2. Configure Authentication**
```bash
# Start auth services
docker-compose -f docker-compose.auth.yml up -d

# Access consoles
# Keycloak: http://localhost:8080 (admin/admin123)
# FusionAuth: http://localhost:9011 (configured during setup)
```

### **3. Configure Environment**
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Required configurations:
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT
# - DATABASE_URL (postgresql://user@localhost:5432/prsnl)
```

### **4. Start Services**
```bash
# Backend (port 8000)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (port 3004)
cd frontend
npm install
npm run dev -- --port 3004
```

### **5. Access PRSNL**
- **Application**: http://localhost:3004
- **API Documentation**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080
- **FusionAuth Admin**: http://localhost:9011

## 📦 **Technology Stack**

### **Frontend**
- **Svelte 5**: Latest reactive framework with runes
- **SvelteKit 2**: Full-stack application framework
- **Three.js**: 3D graphics and WebGL rendering
- **TailwindCSS**: Utility-first styling
- **TypeScript**: Type-safe development

### **Backend**
- **FastAPI**: High-performance Python framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Celery**: Distributed task processing
- **LangChain/LangGraph**: AI orchestration
- **Azure OpenAI**: GPT-4 and Whisper integration

### **Infrastructure**
- **PostgreSQL 16**: Primary database with pgvector
- **DragonflyDB**: Ultra-fast caching (25x Redis performance)
- **Keycloak**: Enterprise SSO and identity management
- **FusionAuth**: User lifecycle and analytics
- **Docker**: Container orchestration

### **AI & ML**
- **OpenAI GPT-4**: Advanced reasoning and analysis
- **CrewAI**: Multi-agent collaboration framework
- **LangChain**: Hybrid search and RAG pipeline
- **pgvector**: Vector similarity search
- **whisper.cpp**: High-quality offline speech recognition

## 🔧 **Development**

### **Code Quality**
```bash
# Backend
cd backend
ruff check .          # Fast Python linter
mypy .               # Type checking
pytest               # Run tests

# Frontend  
cd frontend
npm run lint         # ESLint
npm run check        # Type checking
npm run test         # Playwright tests
```

## 🧪 **Testing**

### **Frontend Testing with Playwright**
PRSNL uses Playwright for comprehensive cross-browser testing with built-in console monitoring.

```bash
# Run all tests
npm test

# Run tests with UI mode
npm run test:ui

# Run specific test suites
npm run test:suite      # Comprehensive test suite
npm run test:chat       # Chat functionality tests
npm run test:codemirror # CodeMirror editor tests

# Debug tests
npm run test:debug
npm run test:headed     # Run with browser visible
```

### **Key Testing Features**
- **Multi-browser Support**: Tests run on Chromium, Firefox, and WebKit
- **Console Monitoring**: Automatic detection of console errors and warnings
- **Visual Testing**: Screenshots and videos on test failures
- **Accessibility Testing**: Built-in a11y checks
- **Performance Metrics**: Page load and interaction timings
- **Network Mocking**: API response simulation

### **Playwright MCP Integration**
The `playwright-console-monitor` agent provides real-time console error detection:
- Captures all console messages during page execution
- Categorizes errors, warnings, and debug messages
- Provides detailed reporting for CI/CD pipelines
- Supports automated frontend testing workflows

### **Database Migrations**
```bash
cd backend
alembic upgrade head  # Apply migrations
alembic revision -m "description"  # Create new migration
```

### **Authentication Development**
- Test users are pre-migrated during setup
- Use `prsnlfyi@gmail.com` for admin access
- OAuth2 flow configured for local development
- JWT tokens: 1-hour access, 7-day refresh

## 🚢 **Deployment**

### **Docker Deployment**
```bash
# Build and run all services
docker-compose up -d

# Services:
# - frontend: http://localhost:3003
# - backend: http://localhost:8000
# - keycloak: http://localhost:8080
# - fusionauth: http://localhost:9011
```

### **Production Considerations**
- Configure proper SSL/TLS certificates
- Set up reverse proxy (Nginx/Caddy)
- Enable production auth providers
- Configure email services (SMTP)
- Set up monitoring (Grafana/Prometheus)

## 📚 **Documentation**

- **[API Documentation](http://localhost:8000/docs)**: Interactive API explorer
- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and patterns
- **[Authentication Guide](docs/AUTH_GUIDE.md)**: Dual auth system setup
- **[Development Guide](docs/DEVELOPMENT.md)**: Contributing guidelines
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production setup
- **[Dreamscape Documentation](docs/DREAMSCAPE_FEATURE_DOCUMENTATION.md)**: AI-powered personal intelligence system

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **OpenAI** for GPT-4 and Whisper APIs
- **Anthropic** for Claude integration
- **LangChain** community for AI orchestration tools
- **Three.js** for amazing 3D graphics capabilities
- **Svelte** team for the revolutionary framework

---

**PRSNL v8.0** - Your AI-powered second brain with enterprise authentication 🧠🔐

For support: [GitHub Issues](https://github.com/your-username/PRSNL/issues) | [Discord](https://discord.gg/prsnl)