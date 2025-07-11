# PRSNL Third-Party Integrations Documentation

This document catalogs all third-party libraries, APIs, and integrations used in the PRSNL knowledge management system.

## **🏗️ Core Infrastructure**

### **Database & Storage**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `PostgreSQL` | - | Primary database with pgvector | PostgreSQL | Low |
| `pgvector` | 0.2.0 | Vector similarity search | PostgreSQL | Low |
| `asyncpg` | 0.29.0 | Async PostgreSQL driver | Apache 2.0 | Low |
| `Redis` | 5.0.1 | Caching & session storage | BSD | Low |
| `SQLAlchemy` | 2.0.25 | ORM and query builder | MIT | Low |

### **Web Framework & API**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `FastAPI` | 0.109.0 | Backend API framework | MIT | Low |
| `Uvicorn` | 0.27.0 | ASGI web server | BSD | Low |
| `Pydantic` | - | Data validation | MIT | Low |
| `slowapi` | 0.1.9 | Rate limiting | MIT | Low |
| `python-multipart` | 0.0.6 | File upload support | Apache 2.0 | Low |

## **🎨 Frontend Stack (SvelteKit)**

### **Core Framework**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `SvelteKit` | Latest | Frontend framework | MIT | Low |
| `Vite` | Latest | Build tool | MIT | Low |
| `TypeScript` | Latest | Type safety | Apache 2.0 | Low |

### **UI Components & Styling**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `Three.js` | Latest | 3D graphics (Mac3D, Fan3D) | MIT | Low |
| `D3.js` | Latest | Data visualizations | BSD | Low |
| `DOMPurify` | Latest | XSS prevention | Apache 2.0 | **Critical** |

### **Markdown & Code Highlighting**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `marked` | Latest | Markdown parser | MIT | Low |
| `highlight.js` | Latest | Syntax highlighting | BSD | Low |
| `Shiki` | - | VS Code themes (planned) | MIT | Low |

## **🔗 External API Integrations**

### **GitHub Integration**
| Service | Purpose | Authentication | Rate Limits | Risk Level |
|---------|---------|---------------|-------------|------------|
| `GitHub API v3` | Repository metadata, README content | Token-based | 5000/hour (authenticated) | Medium |
| `GitHub Raw Content` | File content fetching | Public access | Varies | Low |

**Environment Variables:**
- `GITHUB_TOKEN` - Personal access token for higher rate limits

### **Stack Overflow Integration**
| Service | Purpose | Authentication | Rate Limits | Risk Level |
|---------|---------|---------------|-------------|------------|
| `Stack Exchange API 2.3` | Question/answer metadata | Public API | 300/day (no key) | Low |

### **AI/ML Services**
| Service | Purpose | Authentication | Rate Limits | Risk Level |
|---------|---------|---------------|-------------|------------|
| `OpenAI API` | Content summarization, embeddings | API Key | Varies by plan | **High** |
| `scikit-learn` | Local ML processing | - | - | Low |

**Environment Variables:**
- `OPENAI_API_KEY` - Required for AI features

## **📊 Data Processing & Analysis**

### **Web Scraping**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `BeautifulSoup4` | 4.12.3 | HTML parsing | MIT | Low |
| `httpx` | 0.26.0 | HTTP client | BSD | Low |
| `aiohttp` | 3.9.3 | Async HTTP requests | Apache 2.0 | Low |
| `readability-lxml` | Latest | Content extraction | Apache 2.0 | Low |
| `lxml_html_clean` | Latest | HTML sanitization | BSD | Medium |

### **Document Processing**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `PyPDF2` | 3.0.1 | PDF text extraction | BSD | Low |
| `python-docx` | 0.8.11 | Word document processing | MIT | Low |
| `openpyxl` | 3.1.2 | Excel file processing | MIT | Low |
| `odfpy` | 1.4.1 | OpenDocument processing | Apache 2.0 | Low |
| `python-magic` | 0.4.27 | File type detection | MIT | Low |

### **Media Processing**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `Pillow` | 10.2.0 | Image processing | PIL License | Low |
| `yt-dlp` | Latest | YouTube video download | Unlicense | Medium |
| `youtube-transcript-api` | 0.6.2 | YouTube transcript extraction | MIT | Medium |
| `pytesseract` | 0.3.10 | **OCR text extraction (ACTIVE)** | Apache 2.0 | Low |
| `tesseract-ocr` | Latest | **OCR engine (ACTIVE)** | Apache 2.0 | Low |
| `vosk` | 0.3.45 | **NEW: Offline speech recognition** | Apache 2.0 | Low |

## **🔐 Security & Authentication**

### **Security Libraries**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `DOMPurify` | Latest | Frontend XSS prevention | Apache 2.0 | **Critical** |
| `python-dotenv` | 1.0.0 | Environment variable management | BSD | Low |

### **Authentication (Planned)**
| Service | Purpose | Implementation Status | Risk Level |
|---------|---------|---------------------|------------|
| `Auth0` | User authentication | Planned | Medium |
| `JWT` | Token-based auth | Planned | Medium |

## **📈 Monitoring & Logging**

### **Logging & Monitoring**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `structlog` | 24.1.0 | Structured logging | Apache 2.0 | Low |
| `prometheus-client` | 0.19.0 | Metrics collection | Apache 2.0 | Low |
| `starlette-exporter` | 0.21.0 | FastAPI metrics | Apache 2.0 | Low |
| `psutil` | 5.9.0 | System monitoring | BSD | Low |

### **NEW: OpenTelemetry Observability Stack**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `opentelemetry-api` | 1.21.0 | **Tracing & metrics API** | Apache 2.0 | Low |
| `opentelemetry-sdk` | 1.21.0 | **Core SDK implementation** | Apache 2.0 | Low |
| `opentelemetry-instrumentation-fastapi` | 0.42b0 | **Auto-instrument FastAPI** | Apache 2.0 | Low |
| `opentelemetry-instrumentation-asyncpg` | 0.42b0 | **Auto-instrument database** | Apache 2.0 | Low |
| `opentelemetry-exporter-otlp` | 1.21.0 | **Export to Grafana/Loki** | Apache 2.0 | Low |
| `prometheus-fastapi-instrumentator` | 6.1.0 | **Enhanced metrics** | Apache 2.0 | Low |

### **NEW: Grafana Observability Stack**
| Service | Purpose | Implementation Status | Risk Level |
|---------|---------|---------------------|------------|
| `Grafana` | **Dashboards & visualization** | **Implemented** | Low |
| `Loki` | **Log aggregation** | **Implemented** | Low |
| `Prometheus` | **Metrics collection** | **Enhanced** | Low |
| `Promtail` | **Log collection agent** | **Implemented** | Low |
| `OTEL Collector` | **Traces & metrics pipeline** | **Implemented** | Low |

### **External Monitoring (Optional)**
| Service | Purpose | Implementation Status | Risk Level |
|---------|---------|---------------------|------------|
| `Sentry` | Error tracking | Not implemented | Low |
| `DataDog` | APM monitoring | Not implemented | Low |

## **🧪 Development & Testing**

### **Development Tools**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `black` | 24.1.1 | Python code formatting | MIT | Low |
| `isort` | 5.13.2 | Import sorting | MIT | Low |
| `flake8` | 7.0.0 | Linting | MIT | Low |
| `mypy` | 1.8.0 | Type checking | MIT | Low |
| `pytest` | 7.4.4 | Testing framework | MIT | Low |
| `pytest-asyncio` | 0.23.3 | Async testing support | Apache 2.0 | Low |
| `pre-commit` | 3.6.0 | **NEW: Git hooks automation** | MIT | Low |
| `bandit` | 1.7.5 | **NEW: Security scanning** | Apache 2.0 | Low |
| `pydocstyle` | 6.3.0 | **NEW: Documentation linting** | MIT | Low |

## **🔧 Utility Libraries**

### **Background Processing**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `APScheduler` | 3.11.0 | Job scheduling | MIT | Low |
| `aiofiles` | 23.2.1 | Async file operations | Apache 2.0 | Low |

### **Data Science & Analysis**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `numpy` | 1.26.2 | Numerical computing | BSD | Low |
| `scikit-learn` | 1.3.2 | Machine learning | BSD | Low |

### **Communication (Optional)**
| Library | Version | Purpose | License | Risk Level |
|---------|---------|---------|---------|------------|
| `python-telegram-bot` | 20.8 | Telegram notifications | GPL v3 | Medium |
| `tenacity` | 8.2.3 | Retry mechanisms | Apache 2.0 | Low |

## **🚨 Risk Assessment & Security Considerations**

### **Critical Risk Components**
1. **DOMPurify** - Essential for XSS prevention
2. **OpenAI API** - Handles sensitive content, API key exposure risk
3. **GitHub Token** - Repository access, rate limiting

### **Medium Risk Components**
1. **yt-dlp** - External video downloading, potential legal/policy issues
2. **YouTube APIs** - Rate limiting, terms of service compliance
3. **lxml_html_clean** - HTML processing, potential parsing vulnerabilities

### **Security Best Practices**
- All external API keys stored in environment variables
- Content sanitization on both frontend (DOMPurify) and backend
- Rate limiting implemented for all external API calls
- Redis-based caching to reduce external API dependencies
- Input validation using Pydantic schemas

## **📝 Environment Variables Required**

```env
# Required for AI features
OPENAI_API_KEY=your_openai_api_key

# Optional for enhanced GitHub integration
GITHUB_TOKEN=your_github_personal_access_token

# Database connections
DATABASE_URL=postgresql://user:pass@localhost:5432/prsnl
REDIS_URL=redis://localhost:6379

# Development
DEBUG=false
LOG_LEVEL=INFO
```

## **🔄 Update Schedule & Maintenance**

### **Regular Updates (Monthly)**
- Security patches for all dependencies
- Framework updates (SvelteKit, FastAPI)
- API rate limit and usage monitoring

### **Quarterly Reviews**
- Third-party service terms of service changes
- Performance impact assessment
- Alternative library evaluation

### **Annual Reviews**
- Complete dependency audit
- License compliance review
- Security vulnerability assessment

## **📞 Support & Documentation**

For issues with specific integrations:
1. Check the respective library's GitHub repository
2. Review API documentation for external services
3. Monitor service status pages for outages
4. Check rate limiting and usage quotas

**Last Updated:** 2025-07-11  
**Next Review:** 2025-10-11