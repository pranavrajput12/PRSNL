# PROJECT_ANALYSIS.md

## Project Type Detection

### Primary Classification
**Project Type**: Multi-Component Knowledge Management System
- **Web Application** (SvelteKit frontend)
- **Browser Extension** (Chrome extension)
- **Backend API** (FastAPI)
- **Desktop Overlay** (Electron)

### Technology Stack Analysis

#### Frontend (Web Application)
- **Framework**: SvelteKit 2.0
- **Language**: JavaScript/TypeScript
- **Styling**: CSS with CSS Custom Properties
- **Build Tool**: Vite 5.4.19
- **Package Manager**: npm

#### Backend API
- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL with Full-Text Search
- **Task Queue**: PostgreSQL LISTEN/NOTIFY
- **AI Integration**: Ollama (local), Azure OpenAI (backup)
- **Containerization**: Docker & Docker Compose

#### Browser Extension
- **Type**: Chrome Extension (Manifest V3)
- **Languages**: JavaScript, HTML, CSS
- **Architecture**: Service Worker + Content Scripts + Popup

#### Desktop Component
- **Framework**: Electron
- **Purpose**: Global search overlay

### Project Structure Pattern

#### Architecture Pattern
**Microservices + Component-Based Frontend**
```
PRSNL/
├── frontend/         # SvelteKit component-based web app
├── backend/          # FastAPI microservice architecture
├── extension/        # Chrome extension with modular components
├── overlay/          # Electron desktop overlay
├── docker/           # Container orchestration
└── scripts/          # Automation and utilities
```

#### Design Pattern
- **Frontend**: Component-based with reactive state management
- **Backend**: Layered architecture (API → Core → Database)
- **Extension**: Event-driven with message passing
- **Overall**: Event-driven microservices

### Build System and Tooling

#### Frontend Build System
- **Primary**: Vite (ES modules, fast HMR)
- **Bundler**: Rollup (via Vite)
- **Dev Server**: Vite dev server with hot reload
- **Type Checking**: svelte-check with TypeScript

#### Backend Build System
- **Development**: uvicorn with auto-reload
- **Production**: Docker multi-stage builds
- **Dependencies**: pip with requirements.txt
- **Database**: PostgreSQL with custom init scripts

#### Extension Build System
- **Manual**: Direct file loading for development
- **Production**: Manual packaging (zip archive)
- **Assets**: Static HTML, CSS, JS files

### Package Management

#### Frontend
- **Manager**: npm
- **Lock File**: package-lock.json
- **Dependencies**: Minimal (primarily SvelteKit ecosystem)
- **Dev Dependencies**: ESLint, Prettier, TypeScript tools

#### Backend
- **Manager**: pip
- **Requirements**: requirements.txt + requirements-dev.txt
- **Virtual Environment**: Recommended
- **Container**: Docker image with Python 3.8+

#### Extension
- **Dependencies**: None (vanilla JavaScript)
- **Assets**: Self-contained HTML/CSS/JS

### Entry Points and Main Files

#### Frontend Entry Points
- **Main**: `src/app.html` (HTML template)
- **Root Layout**: `src/routes/+layout.svelte`
- **Home Page**: `src/routes/+page.svelte`
- **Config**: `vite.config.ts`, `svelte.config.js`

#### Backend Entry Points
- **Main**: `app/main.py` (FastAPI application)
- **API Routes**: `app/api/` directory
- **Worker**: `app/worker.py` (background tasks)
- **Config**: `app/config.py`

#### Extension Entry Points
- **Manifest**: `manifest.json` (extension configuration)
- **Background**: `background.js` (service worker)
- **Popup**: `popup.html` + `popup.js`
- **Content**: `content.js` (page injection)
- **Options**: `options.html` + `options.js`

#### Desktop Overlay Entry Points
- **Main**: `main.js` (Electron main process)
- **Renderer**: `renderer.js` (UI process)
- **Preload**: `preload.js` (security bridge)

### Configuration Files and Purposes

#### Frontend Configuration
```
frontend/
├── package.json          # Dependencies and scripts
├── vite.config.ts        # Build configuration
├── svelte.config.js      # Svelte compiler config
├── tsconfig.json         # TypeScript configuration
├── .eslintrc.js          # Code linting rules
└── .prettierrc           # Code formatting rules
```

#### Backend Configuration
```
backend/
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── Dockerfile           # Container build instructions
├── app/config.py        # Application settings
└── .env.example         # Environment variables template
```

#### Extension Configuration
```
extension/
├── manifest.json        # Extension metadata and permissions
├── icons/              # Extension icon assets
└── (no build config - vanilla JS)
```

#### Project-Level Configuration
```
PRSNL/
├── docker-compose.yml   # Multi-container orchestration
├── .gitignore          # Version control exclusions
├── README.md           # Project documentation
└── scripts/            # Development automation
```

### Development vs Production Considerations

#### Development Environment
- **Frontend**: Vite dev server (localhost:3000)
- **Backend**: uvicorn with reload (localhost:8000)
- **Database**: Docker PostgreSQL
- **Extension**: Chrome developer mode loading

#### Production Environment
- **Frontend**: Static build served by backend or CDN
- **Backend**: Docker container with gunicorn
- **Database**: PostgreSQL with persistent volumes
- **Extension**: Chrome Web Store distribution

### Key Architectural Decisions

1. **Local-First**: All data processing happens locally
2. **Zero-Cost**: No cloud dependencies or recurring fees
3. **Privacy-Focused**: Data never leaves user's machine
4. **Keyboard-Centric**: Maximum 4 keystrokes to any action
5. **Performance-First**: Sub-second search on 100k+ items
6. **Design-Consistent**: Manchester United red (#dc143c) theme throughout

### Technology Maturity Assessment

- **Frontend**: Modern, stable (SvelteKit 2.0)
- **Backend**: Production-ready (FastAPI + PostgreSQL)
- **Extension**: Standard Manifest V3 (Chrome standard)
- **Containerization**: Industry standard (Docker)
- **AI Integration**: Cutting-edge but stable (Ollama)

### Project Complexity Classification

**Complexity Level**: High
- **Multiple Components**: 4 separate applications
- **Multiple Languages**: JavaScript, Python, HTML/CSS
- **Multiple Environments**: Browser, Desktop, Server
- **Advanced Features**: AI integration, real-time search, cross-platform

### Success Metrics Identified

1. **Performance**: <1s search response time
2. **Usability**: <4 keystrokes to any action
3. **Privacy**: 100% local data processing
4. **Cost**: $0 recurring operational costs
5. **Design**: Consistent Manchester United red theming
6. **Compatibility**: Works across modern browsers and OS

### Next Analysis Steps

This project requires specialized documentation for:
1. Multi-component data flow mapping
2. AI integration patterns
3. Cross-platform development workflow
4. Local-first architecture patterns
5. Privacy-preserving design principles