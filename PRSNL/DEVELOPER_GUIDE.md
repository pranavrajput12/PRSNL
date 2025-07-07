# PRSNL Developer Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Testing](#testing)
7. [Debugging](#debugging)
8. [Deployment](#deployment)
9. [Contributing](#contributing)

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL 15+ (or use Docker)
- Git

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd PRSNL

# Start all services with Docker
docker-compose up -d

# Access the application
# Frontend: http://localhost:3002
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development Environment

### Docker Setup (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Reset everything (including volumes)
docker-compose down -v
```

### Local Development

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/prsnl
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
OLLAMA_BASE_URL=http://localhost:11434

# Storage
MEDIA_ROOT=/app/media
MAX_VIDEO_SIZE_MB=500

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3002"]
```

#### Frontend (.env)
```env
PUBLIC_API_URL=http://localhost:8000/api
PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── capture.py    # Content capture endpoints
│   │   ├── search.py     # Search functionality
│   │   ├── timeline.py   # Timeline view
│   │   └── ...
│   ├── core/             # Core business logic
│   │   ├── capture_engine.py
│   │   └── exceptions.py
│   ├── db/               # Database models and utilities
│   │   ├── database.py
│   │   └── models.py
│   ├── services/         # Service layer
│   │   ├── ai_router.py  # AI service routing
│   │   ├── llm_processor.py
│   │   ├── video_processor.py
│   │   └── ...
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── tests/                # Test suite
└── requirements.txt      # Dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── lib/              # Shared libraries
│   │   ├── api.ts        # API client
│   │   ├── stores/       # Svelte stores
│   │   └── components/   # Reusable components
│   ├── routes/           # SvelteKit routes
│   │   ├── +page.svelte  # Home page
│   │   ├── timeline/     # Timeline view
│   │   ├── search/       # Search interface
│   │   └── ...
│   └── app.html          # HTML template
├── static/               # Static assets
├── tests/                # Test suite
└── package.json          # Dependencies
```

## Development Workflow

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/your-feature-name

# Create pull request
```

### Commit Convention
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

### Code Review Process
1. Create pull request with description
2. Ensure all tests pass
3. Request review from team members
4. Address feedback
5. Merge after approval

## Code Standards

### Python (Backend)
```python
# Follow PEP 8
# Use type hints
from typing import List, Optional, Dict
from pydantic import BaseModel

class VideoData(BaseModel):
    """Document all classes and functions"""
    url: str
    title: str
    duration: Optional[int] = None
    
async def process_video(url: str) -> Dict[str, Any]:
    """
    Process a video from URL.
    
    Args:
        url: Video URL to process
        
    Returns:
        Processed video data
        
    Raises:
        ValueError: If URL is invalid
    """
    # Implementation
```

### TypeScript (Frontend)
```typescript
// Use TypeScript strictly
// Define interfaces for data structures
interface VideoItem {
  id: string;
  title: string;
  url: string;
  duration?: number;
  createdAt: Date;
}

// Use proper error handling
export async function fetchVideo(id: string): Promise<VideoItem> {
  try {
    const response = await api.get<VideoItem>(`/videos/${id}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch video:', error);
    throw new Error('Video fetch failed');
  }
}
```

### CSS/Styling
```css
/* Use CSS custom properties */
:root {
  --primary-color: #2563eb;
  --spacing-unit: 8px;
}

/* Follow BEM naming convention */
.video-card {
  /* Block */
}

.video-card__title {
  /* Element */
}

.video-card--featured {
  /* Modifier */
}

/* Mobile-first responsive design */
.container {
  width: 100%;
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
  }
}
```

## Testing

### Backend Testing
```python
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_video_processor.py

# Run with verbose output
pytest -v
```

### Frontend Testing
```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run in watch mode
npm run test:watch
```

### Writing Tests

#### Backend Test Example
```python
import pytest
from app.services.video_processor import VideoProcessor

@pytest.mark.asyncio
async def test_video_download():
    processor = VideoProcessor()
    result = await processor.download_video("https://example.com/video")
    
    assert result.title is not None
    assert result.video_path.exists()
```

#### Frontend Test Example
```typescript
import { render, screen } from '@testing-library/svelte';
import VideoCard from '$lib/components/VideoCard.svelte';

test('renders video title', () => {
  render(VideoCard, {
    props: {
      video: {
        id: '1',
        title: 'Test Video',
        url: 'https://example.com'
      }
    }
  });
  
  expect(screen.getByText('Test Video')).toBeInTheDocument();
});
```

## Debugging

### Backend Debugging

#### Using VS Code
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

#### Debug Logging
```python
import logging

logger = logging.getLogger(__name__)

# Add debug logging
logger.debug(f"Processing video: {url}")
logger.info(f"Video processed successfully: {video_id}")
logger.error(f"Failed to process video: {error}")
```

### Frontend Debugging

#### Browser DevTools
```javascript
// Use console methods effectively
console.log('Data:', data);
console.table(items);
console.time('API Call');
// ... API call
console.timeEnd('API Call');

// Use debugger statement
debugger; // Pauses execution
```

#### Svelte DevTools
- Install Svelte DevTools browser extension
- Inspect component props and state
- Monitor store updates

### Docker Debugging
```bash
# View container logs
docker-compose logs -f backend

# Execute commands in container
docker-compose exec backend bash

# Inspect container
docker inspect prsnl_backend_1

# View resource usage
docker stats
```

## Deployment

### Production Build

#### Backend
```bash
# Build Docker image
docker build -t prsnl-backend:latest ./backend

# Run production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### Frontend
```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Build Docker image
docker build -t prsnl-frontend:latest ./frontend
```

### Environment Configuration

#### Production Settings
```python
# backend/app/config.py
class Settings(BaseSettings):
    # Production overrides
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["https://your-domain.com"]
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    class Config:
        env_file = ".env.production"
```

### Monitoring

#### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "storage": check_storage_space()
    }
```

#### Metrics
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
```

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Set up development environment
4. Make changes with tests
5. Submit pull request

### Code Review Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance considered
- [ ] Error handling implemented

### Release Process
1. Update version in `pyproject.toml` and `package.json`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Build and test Docker images
6. Tag release
7. Deploy to production

### Documentation
- Update API docs for new endpoints
- Add inline code documentation
- Update README for new features
- Create migration guides if needed

## Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check PostgreSQL is running
docker-compose ps db

# Test connection
docker-compose exec backend python -c "from app.db.database import get_db_pool; import asyncio; asyncio.run(get_db_pool())"
```

#### Port Conflicts
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Module Import Errors
```bash
# Ensure you're in virtual environment
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Apple Silicon (M1/M2) Architecture Issues
If you encounter errors like `mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64')`:

```bash
# Check your Python architecture
python3 -c "import platform; print(platform.machine())"  # Should show 'arm64'

# Common problematic packages
pip uninstall -y pydantic pydantic-core asyncpg pandas

# Reinstall with ARM64 binaries
pip install --no-cache-dir pydantic asyncpg pandas

# If issues persist, use Rosetta emulation (not recommended)
arch -x86_64 pip install package-name

# Better solution: Use native ARM64 Python
brew install python@3.11  # Install ARM64 Python via Homebrew
```

**Common ARM64 Issues:**
- `pydantic_core`: Binary incompatibility
- `asyncpg`: PostgreSQL connection library
- `pandas`: Data processing library
- `msgpack`: Serialization library
- `cffi`: Foreign function interface

**Prevention:**
1. Always use `--no-cache-dir` when installing packages
2. Create fresh virtual environments for ARM64
3. Use Docker for consistent environment across architectures

### Getting Help
- Check existing issues on GitHub
- Search documentation
- Ask in development chat
- Create detailed bug report

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [pgAdmin](https://www.pgadmin.org/) - Database management
- [Redis Commander](https://github.com/joeferner/redis-commander) - Redis GUI
- [Portainer](https://www.portainer.io/) - Docker management

### Learning Resources
- FastAPI Tutorial
- SvelteKit Tutorial
- PostgreSQL Performance Tuning
- Docker Best Practices