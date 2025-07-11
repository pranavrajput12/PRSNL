# PRSNL - Personal Knowledge Management System v2.2

> **Advanced AI-powered knowledge management with comprehensive observability and hybrid transcription**

PRSNL is a cutting-edge personal knowledge management system that captures, processes, and intelligently organizes your digital content using advanced AI technologies. Version 2.2 introduces enterprise-grade monitoring, offline transcription capabilities, and automated code quality tools.

## 🌟 **Key Features**

### **🧠 Universal AI-Powered Content Processing**
- **Intelligent Capture**: Web articles, YouTube videos, documents, images, and more
- **AI Summarization**: GPT-4 powered content analysis and key insights extraction
- **Smart Categorization**: Automatic tagging and topic classification
- **Knowledge Graphs**: Dynamic relationship mapping between content items

### **🎙️ Hybrid Transcription System (NEW in v2.2)**
- **Offline Speech Recognition**: Vosk-powered local transcription for privacy
- **Cloud Fallback**: Azure OpenAI Whisper for high-quality transcription
- **Smart Routing**: Automatically chooses optimal service based on context
- **Privacy Mode**: Force offline processing for sensitive content

### **🔍 Advanced Search & Discovery**
- **Semantic Search**: Vector-based similarity search with pgvector
- **Full-Text Search**: PostgreSQL-powered content indexing
- **AI-Suggested Content**: Intelligent content recommendations
- **Timeline Views**: Chronological content organization

### **📊 Enterprise-Grade Observability (NEW in v2.2)**
- **Comprehensive Monitoring**: OpenTelemetry + Grafana + Loki stack
- **Performance Tracking**: Request latency, error rates, resource usage
- **Business Metrics**: Content processing rates, search performance
- **Real-time Dashboards**: Visual monitoring and alerting

### **💻 Developer Experience (NEW in v2.2)**
- **Automated Code Quality**: Pre-commit hooks with formatting, linting, security
- **Consistent Development**: Black, isort, flake8, mypy, bandit integration
- **Documentation**: Comprehensive setup and deployment guides

## 🚀 **Quick Start**

### **Prerequisites**
- **Rancher Desktop** (NOT Docker Desktop)
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+** with pgvector extension
- **Redis 7+**

### **1. Clone and Setup**
```bash
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL

# Run automated setup script
./setup-development.sh
```

### **2. Configure Environment**
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Update with your API keys
nano backend/.env
```

**Required API Keys:**
- **Azure OpenAI**: For GPT-4 and Whisper transcription
- **GitHub Token**: For enhanced API rate limits (optional)

### **3. Start Services**
```bash
# Start core services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Start monitoring stack (optional)
./start-monitoring.sh
```

### **4. Access Applications**
| Service | URL | Purpose |
|---------|-----|---------|
| **PRSNL Web App** | http://localhost:3003 | Main application |
| **API Documentation** | http://localhost:8000/docs | Backend API docs |
| **Grafana Monitoring** | http://localhost:3000 | Performance dashboards |
| **Prometheus Metrics** | http://localhost:9090 | Raw metrics data |

## 🏗️ **Architecture Overview**

### **Backend (FastAPI)**
```
📁 backend/
├── 🔧 app/
│   ├── 🚦 api/           # API endpoints (22 routers)
│   ├── 🧠 services/      # Business logic & AI services
│   ├── 🗄️ db/            # Database models & migrations
│   ├── 🔍 core/          # Core utilities & observability
│   └── 🎛️ middleware/    # Request processing middleware
├── 📊 monitoring/        # Observability configurations
└── 🗃️ storage/          # File storage & Vosk models
```

### **Frontend (SvelteKit)**
```
📁 frontend/
├── 🎨 src/
│   ├── 📄 routes/        # Page components
│   ├── 🧩 lib/           # Shared components & utilities
│   └── 🎭 static/        # Static assets & 3D models
└── 📦 build/             # Production build
```

### **Key Technologies**
- **AI**: Azure OpenAI (GPT-4, Whisper, Ada-002), Vosk offline speech
- **Database**: PostgreSQL + pgvector for semantic search
- **Cache**: Redis for performance optimization
- **Monitoring**: OpenTelemetry + Grafana + Loki + Prometheus
- **Quality**: Pre-commit hooks + automated testing

## 📖 **Core Capabilities**

### **Content Types Supported**
| Type | Processing | Features |
|------|------------|----------|
| **Web Articles** | ✅ AI Summary + OCR fallback | Readability extraction, metadata |
| **YouTube Videos** | ✅ Hybrid transcription | Offline/cloud speech-to-text |
| **Documents** | ✅ OCR + AI analysis | PDF, DOC, images with tesseract |
| **Images** | ✅ Vision AI + OCR | Text extraction, visual analysis |
| **Code Repositories** | ✅ GitHub integration | README parsing, rich previews |

### **AI-Powered Features**
- **Content Summarization**: Key insights and takeaways
- **Automatic Tagging**: Smart categorization and topic extraction
- **Knowledge Relationships**: Dynamic content connections
- **Search Enhancement**: Semantic similarity and context understanding
- **Learning Path Generation**: Intelligent content sequencing

### **Privacy & Security**
- **Offline Processing**: Vosk transcription for sensitive content
- **Local OCR**: Tesseract processing without cloud dependencies
- **Secure Configuration**: Environment-based secrets management
- **Input Validation**: Comprehensive request sanitization

## 🔧 **Development & Deployment**

### **Development Workflow**
```bash
# Install pre-commit hooks (automatic code quality)
pre-commit install

# Start development environment
docker-compose up -d
cd frontend && npm run dev

# Monitor application performance
./start-monitoring.sh
```

### **Code Quality Tools**
- **Formatting**: Black (Python), Prettier (Frontend)
- **Linting**: flake8, ESLint, mypy type checking
- **Security**: Bandit security scanning
- **Documentation**: pydocstyle compliance checking

### **Monitoring & Observability**
```bash
# View application metrics
curl http://localhost:8000/metrics

# Access monitoring dashboards
open http://localhost:3000  # Grafana (admin/admin)

# Check application logs
tail -f backend/logs/prsnl.log
```

### **Production Deployment**
1. **Environment Setup**: Configure production environment variables
2. **Security**: Use proper secrets management (Azure Key Vault, AWS Secrets)
3. **Monitoring**: Deploy Grafana stack with persistent storage
4. **Scaling**: Configure load balancing and database replication

## 📚 **Documentation**

### **Technical Documentation**
- **[Third-Party Integrations](docs/THIRD_PARTY_INTEGRATIONS.md)**: Complete integration inventory
- **[Monitoring Guide](docs/MONITORING_DEPLOYMENT_GUIDE.md)**: Observability setup
- **[CLAUDE.md](CLAUDE.md)**: Development configuration for AI assistants

### **API Documentation**
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Alternative documentation)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🤝 **Contributing**

### **Getting Started**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks (`pre-commit install`)
4. Make your changes (automatic code quality checks will run)
5. Commit with descriptive messages
6. Push and create a Pull Request

### **Development Standards**
- **Code Quality**: All code passes pre-commit hooks
- **Testing**: Add tests for new functionality
- **Documentation**: Update docs for API changes
- **Security**: No hardcoded secrets or credentials

## 📊 **Performance & Scalability**

### **Current Capabilities**
- **Content Items**: Handles 100K+ items efficiently
- **Search Performance**: Sub-second semantic search
- **Concurrent Users**: Supports 50+ simultaneous users
- **Processing Speed**: Real-time content analysis

### **Optimization Features**
- **Redis Caching**: API response and embedding caching
- **Database Indexing**: Optimized PostgreSQL queries
- **Lazy Loading**: Frontend component optimization
- **CDN Ready**: Static asset optimization

## 🔮 **Roadmap**

### **v2.3 (Planned)**
- **Multi-user Support**: User authentication and workspaces
- **Advanced Analytics**: Usage patterns and content insights
- **Custom AI Models**: Domain-specific model training
- **Mobile App**: React Native companion app

### **v3.0 (Future)**
- **Distributed Deployment**: Kubernetes orchestration
- **Advanced Security**: End-to-end encryption
- **Plugin System**: Extensible integration framework
- **Enterprise Features**: SSO, audit logs, compliance

## 🛟 **Support & Community**

### **Getting Help**
- **Documentation**: Comprehensive guides in `/docs`
- **Issues**: GitHub Issues for bug reports and features
- **Discussions**: GitHub Discussions for community support

### **Troubleshooting**
- **Setup Issues**: Check `setup-development.sh` output
- **Database Problems**: Verify PostgreSQL connection and migrations
- **API Errors**: Check backend logs and environment configuration
- **Performance**: Use Grafana dashboards for monitoring

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **OpenAI/Azure**: AI capabilities and transcription services
- **PostgreSQL/pgvector**: Semantic search infrastructure  
- **Grafana Labs**: Observability and monitoring stack
- **Vosk**: Offline speech recognition technology
- **SvelteKit**: Modern frontend framework
- **FastAPI**: High-performance API framework

---

**Built with ❤️ for knowledge workers who want to stay organized and discover insights in their digital content.**

*PRSNL v2.2 - Advanced Integrations • Released 2025-07-11*