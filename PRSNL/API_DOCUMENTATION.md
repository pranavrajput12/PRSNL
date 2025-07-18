# 📚 PRSNL API Documentation - Phase 3 AI Second Brain

## Base URL
- Development: `http://localhost:8000/api`
- Frontend Proxy: `http://localhost:3004/api` (updated from 3003)
- iOS App: Configured in iOS app settings
- **NEW**: AI API: `http://localhost:8000/api/ai`
- **NEW**: LibreChat API: `http://localhost:8000/api/ai`

## Client Applications
- **SvelteKit Frontend**: Web application (port 3004 dev, 3003 container)
- **iOS App (PRSNL APP)**: Native iOS application - *separate codebase*
- **Chrome Extension**: Browser extension
- **NEW**: LibreChat Integration - OpenAI-compatible chat interface
- **NEW**: AI Services - Intelligent content analysis and suggestions

## Navigation Structure (Neural Nest Theme)
- **Neural Nest** (`/`) - Main dashboard and knowledge hub
- **Ingest** (`/capture`) - Content capture and ingestion
- **Thought Stream** (`/timeline`) - Chronological content timeline
- **Cognitive Map** (`/insights`) - AI-powered insights and analysis
- **Mind Palace** (`/chat`) - Conversational interface with knowledge base
- **Visual Cortex** (`/videos`) - Video content management
- **Code Cortex** (`/code-cortex`) - Development content management hub
- **Knowledge Sync** (`/import`) - External data import and synchronization

## Authentication

### JWT Authentication System
PRSNL uses JWT (JSON Web Token) based authentication with access and refresh tokens. The system supports email verification and magic link (passwordless) authentication.

**Authentication Flow:**
1. User registers with email and password
2. Email verification sent via Resend API
3. User verifies email or uses magic link
4. Access and refresh tokens issued
5. Tokens automatically refresh on expiry

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully. Please check your email for verification.",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "is_verified": false
  }
}
```

#### POST /api/auth/login
Login with email and password

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "is_verified": true
  }
}
```

#### POST /api/auth/refresh
Refresh access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /api/auth/verify-email
Verify email address with token from email

**Request Body:**
```json
{
  "token": "verification_token_from_email"
}
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /api/auth/send-magic-link
Request a magic link for passwordless login

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Magic link sent to your email"
}
```

#### POST /api/auth/verify-magic-link
Login using magic link token

**Request Body:**
```json
{
  "token": "magic_link_token_from_email"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "is_verified": true
  }
}
```

#### POST /api/auth/resend-verification
Resend email verification

**Headers:**
- `Authorization: Bearer {access_token}`

**Response:**
```json
{
  "message": "Verification email sent"
}
```

#### GET /api/auth/me
Get current user profile

**Headers:**
- `Authorization: Bearer {access_token}`

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "is_verified": true,
  "created_at": "2025-07-16T08:00:00Z",
  "updated_at": "2025-07-16T08:00:00Z"
}
```

#### PUT /api/auth/profile
Update user profile

**Headers:**
- `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "Jane Doe"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "Jane Doe",
    "is_verified": true
  }
}
```

### Authentication Headers
All protected endpoints require the Authorization header:
```
Authorization: Bearer {access_token}
```

### Token Expiration
- **Access Token**: 15 minutes
- **Refresh Token**: 7 days

### Email Templates
The system uses customizable email templates for:
- Email verification
- Magic link login
- Password reset (future feature)

**Note**: Email functionality requires `RESEND_API_KEY` environment variable to be set.

## Phase 4 AI API Endpoints - Advanced Orchestration

### 🤖 AI Services - Intelligent Analysis

#### GET /api/ai/health
Get the health status of AI services

**Response:**
```json
{
  "total_agents": 4,
  "agents": [
    {
      "name": "knowledge_curator",
      "status": "active",
      "capabilities": ["analyze_content", "find_connections", "suggest_enhancements"]
    },
    {
      "name": "research_synthesizer",
      "status": "active", 
      "capabilities": ["synthesize_sources", "identify_patterns", "generate_insights"]
    },
    {
      "name": "content_explorer",
      "status": "active",
      "capabilities": ["explore_connections", "suggest_exploration_paths", "find_serendipitous_connections"]
    },
    {
      "name": "learning_pathfinder",
      "status": "active",
      "capabilities": ["create_learning_path", "track_progress", "adapt_path"]
    }
  ],
  "memory_status": "connected",
  "timestamp": "2025-07-13T02:44:11.779449"
}
```

#### POST /api/ai-suggest
Process content through AI-powered analysis and suggestions

**Request Body:**
```json
{
  "content": "Content to analyze and process",
  "title": "Optional title",
  "tags": ["tag1", "tag2"],
  "url": "https://example.com",
  "type": "article"
}
```

**Response:**
```json
{
  "request_id": "content-1752355349.848207",
  "status": "completed",
  "results": {
    "agent_outputs": {
      "knowledge_curator": "Detailed categorization and enhancement suggestions...",
      "research_synthesizer": "Comprehensive synthesis and insights..."
    },
    "processing_result": {
      "enrichments": {
        "categories": ["programming", "web-development"],
        "tags": ["python", "api", "fastapi"],
        "key_concepts": ["async programming", "web frameworks"],
        "insights": ["Key insights and patterns identified..."]
      }
    }
  },
  "agents_involved": ["knowledge_curator", "research_synthesizer"],
  "execution_time": 10.546185,
  "timestamp": "2025-07-13T02:52:40.394418"
}
```

#### POST /api/ai-suggest
Create AI-powered suggestions and recommendations

**Request Body:**
```json
{
  "goal": "Master FastAPI and async Python for building high-performance APIs",
  "current_knowledge": ["Python basics", "HTTP fundamentals", "REST APIs"],
  "time_commitment": "intensive"
}
```

**Response:**
```json
{
  "status": "completed",
  "agent": "learning_pathfinder",
  "results": {
    "learning_path": "Comprehensive 5-stage learning plan with milestones, resources, and exercises..."
  },
  "timestamp": "2025-07-13T02:51:53.385826"
}
```

#### POST /api/ai-suggest
Explore topics with AI-powered insights

**Request Body:**
```json
{
  "topic": "Machine Learning for Knowledge Management",
  "user_interests": ["python", "ai", "automation"],
  "depth": 3
}
```

**Response:**
```json
{
  "topic": "Machine Learning for Knowledge Management",
  "status": "completed",
  "results": {
    "explorations": {
      "content_explorer": "Exploration paths and discovery suggestions...",
      "learning_pathfinder": "Structured learning approach..."
    }
  },
  "timestamp": "2025-07-13T02:52:29.848995"
}
```

#### POST /api/summarization/summarize/batch
Generate comprehensive summaries across content

**Query Parameters:**
- `time_period` (string, default: "week") - Time period for analysis

**Response:**
```json
{
  "status": "completed",
  "report": {
    "period": "week",
    "sections": {
      "synthesis": "Pattern analysis and insights...",
      "exploration_suggestions": "Areas to explore based on insights..."
    }
  },
  "generated_at": "2025-07-13T02:52:29.848995"
}
```

#### GET /api/ai/health
AI service health check

**Response:**
```json
{
  "status": "healthy",
  "service": "prsnl-ai",
  "memory_connected": true,
  "agents_loaded": true,
  "agent_count": 4,
  "timestamp": "2025-07-13T02:44:11.779449"
}
```

### 💬 LibreChat - Conversational AI Bridge

#### POST /api/ai/chat/completions
OpenAI-compatible chat completions with knowledge base integration

**Headers:**
- `Content-Type: application/json`
- `X-PRSNL-Integration: test-client` (optional)

**Request Body:**
```json
{
  "model": "prsnl-gpt-4",
  "messages": [
    {"role": "user", "content": "Hello! Can you help me understand how PRSNL works as a second brain system?"}
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-1752374596",
  "object": "chat.completion",
  "created": 1752374596,
  "model": "prsnl-gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'd be happy to explain how PRSNL works as a second brain system...",
        "name": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 350,
    "total_tokens": 364
  }
}
```

**Streaming Response** (when `"stream": true`):
```
data: {"id": "chatcmpl-1752374627", "object": "chat.completion.chunk", "created": 1752374627, "model": "prsnl-gpt-4", "choices": [{"index": 0, "delta": {"content": " Enhanced Information"}, "finish_reason": null}]}

data: {"id": "chatcmpl-1752374627", "object": "chat.completion.chunk", "created": 1752374627, "model": "prsnl-gpt-4", "choices": [{"index": 0, "delta": {"content": " Retrieval: AI can"}, "finish_reason": null}]}

data: [DONE]
```

#### GET /api/ai/models
List available models for LibreChat integration

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "prsnl-gpt-4",
      "object": "model",
      "created": 1752374596,
      "owned_by": "prsnl"
    },
    {
      "id": "prsnl-gpt-35-turbo",
      "object": "model", 
      "created": 1752374596,
      "owned_by": "prsnl"
    }
  ]
}
```

#### GET /api/ai/health
LibreChat bridge health check

**Response:**
```json
{
  "status": "healthy",
  "service": "prsnl-librechat-bridge",
  "timestamp": "2025-07-13T02:44:11.779449",
  "models": 2
}
```

### 🚀 AI Router - Enhanced Routing System

#### GET /api/ai-router/status
Get AI Router health and configuration status

**Response:**
```json
{
  "enabled": true,
  "enhanced_routing_available": true,
  "enhanced_routing_enabled": true,
  "basic_usage": {
    "total_requests": 42,
    "total_tokens": 12500,
    "estimated_cost": 0.375,
    "provider_breakdown": {
      "azure_openai": {
        "requests": 40,
        "tokens": 12000,
        "errors": 0,
        "cost": 0.36,
        "avg_response_time_ms": 485,
        "health": true
      },
      "fallback": {
        "requests": 2,
        "tokens": 500,
        "errors": 0,
        "cost": 0.0,
        "avg_response_time_ms": 10,
        "health": true
      }
    }
  }
}
```

#### POST /api/ai-router/test-routing
Test AI Router provider selection with enhanced routing

**Request Body:**
```json
{
  "content": "Test complex routing decision",
  "task_type": "text_generation",
  "priority": 8,
  "requires_vision": false,
  "requires_streaming": false
}
```

**Response:**
```json
{
  "routing_decision": {
    "provider": "azure_openai",
    "complexity": "moderate",
    "reasoning": "High priority task with complex content requires premium provider",
    "confidence": 0.8,
    "estimated_tokens": 1500,
    "recommended_model": "gpt-4.1-mini",
    "fallback_options": ["fallback"],
    "optimization_notes": ["Using premium provider for high priority"]
  },
  "enhanced_routing_used": true,
  "response_time_ms": 342
}
```

#### GET /api/ai-router/enhanced-insights
Get enhanced AI Router insights and analytics

**Response:**
```json
{
  "enhanced_insights": {
    "total_routings": 42,
    "provider_distribution": {
      "azure_openai": 40,
      "fallback": 2
    },
    "complexity_analysis": {
      "simple": 15,
      "moderate": 20,
      "complex": 7
    },
    "performance_metrics": {
      "avg_response_time": 425,
      "success_rate": 0.98,
      "cost_efficiency": 0.85
    },
    "recommendations": [
      "Routing patterns appear optimal",
      "Consider caching for frequently requested content types"
    ]
  }
}
```

### 🔄 LangGraph Workflows - State-based Processing

#### POST /api/ai-suggest (Enhanced with LangGraph)
Process content through LangGraph state-based workflows with quality loops

**Request Body:**
```json
{
  "content": "Content to process through workflows",
  "title": "Optional title",
  "context": {
    "type": "document",
    "use_workflow": true,
    "analysis_depth": "standard"
  }
}
```

**Response:**
```json
{
  "workflow_enabled": true,
  "processing_result": {
    "content_id": "wf_12345",
    "title": "Processed Title",
    "summary": "AI-generated summary",
    "category": "technology",
    "tags": ["ai", "workflow", "automation"],
    "entities": {
      "technologies": ["LangGraph", "AI", "Workflows"],
      "concepts": ["state-based processing", "quality loops"]
    },
    "quality_score": 0.85,
    "processing_path": [
      "route_content",
      "analyze_content", 
      "enrich_content",
      "quality_check",
      "store_content",
      "index_content"
    ],
    "workflow_metadata": {
      "workflow_type": "content_processing",
      "quality_loops": 1,
      "total_processing_time": 1250
    }
  }
}
```

### 🧠 Conversation Intelligence - Multi-Agent Analysis

#### POST /api/conversations/intelligence/{conversation_id}/process
Process conversation intelligence using specialized AI agents

**Path Parameters:**
- `conversation_id` (UUID) - The conversation ID to analyze

**Response:**
```json
{
  "message": "Intelligence processing started for conversation {conversation_id}",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

#### GET /api/conversations/intelligence/{conversation_id}
Get conversation intelligence results

**Path Parameters:**
- `conversation_id` (UUID) - The conversation ID to retrieve intelligence for

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "processing_time_ms": 8500,
  "summary": {
    "title": "Technical Discussion on AI Implementation",
    "key_points": ["API integration", "Database optimization", "User experience"],
    "word_count": 1250
  },
  "learning_journey": {
    "progress_stage": "implementation",
    "skill_areas": ["FastAPI", "PostgreSQL", "Frontend optimization"],
    "knowledge_gained": "Understanding of real-time progress tracking"
  },
  "concepts": {
    "technical_concepts": ["async programming", "database migrations", "UI/UX"],
    "business_concepts": ["user engagement", "performance optimization"]
  },
  "insights": {
    "key_insights": ["Real-time feedback improves user experience"],
    "recommendations": ["Implement progress tracking for all long-running operations"]
  },
  "technical_content": {
    "code_solutions": ["Progress bar implementation", "Database optimization"],
    "technical_patterns": ["Multi-agent AI architecture", "Real-time synchronization"]
  },
  "learning_analysis": {
    "progression": "From basic UI to advanced interactive systems",
    "understanding_evolution": "Deeper grasp of user experience principles"
  },
  "actionable_insights": {
    "immediate_actions": ["Test progress synchronization", "Gather user feedback"],
    "future_considerations": ["Expand to other processing workflows"]
  },
  "knowledge_gap_analysis": {
    "missing_areas": ["Advanced animation techniques", "Performance monitoring"],
    "learning_opportunities": ["CSS animations", "Real-time analytics"]
  }
}
```

#### POST /api/conversations/intelligence/batch/process
Process intelligence for multiple conversations

**Query Parameters:**
- `platform` (string, optional) - Filter by platform (e.g., "chatgpt", "claude")

**Response:**
```json
{
  "message": "Batch intelligence processing started",
  "conversations_found": 15,
  "processing_started": 12,
  "already_processed": 3,
  "status": "processing"
}
```

## 🔍 CodeMirror - AI Repository Intelligence

CodeMirror provides deep AI-powered analysis of code repositories, detecting patterns, generating insights, and providing intelligent code understanding.

### Repository Analysis

#### POST /api/codemirror/analyze/{repo_id}
Start AI-powered analysis of a GitHub repository

**Path Parameters:**
- `repo_id` (UUID) - The repository ID from github_repos table

**Request Body:**
```json
{
  "repo_id": "1cbb79ce-8994-490c-87ce-56911ab03807",
  "analysis_depth": "standard",
  "include_patterns": true,
  "include_insights": true
}
```

**Analysis Depth Options:**
- `quick` - Fast surface-level analysis
- `standard` - Balanced depth and speed (default)
- `deep` - Comprehensive analysis with advanced patterns

**Response:**
```json
{
  "job_id": "codemirror_1cbb79ce-8994-490c-87ce-56911ab03807_1752491022.319806",
  "status": "pending",
  "message": "CodeMirror analysis started with standard depth",
  "monitor_url": "/api/persistence/status/codemirror_1cbb79ce-8994-490c-87ce-56911ab03807_1752491022.319806",
  "websocket_channel": "codemirror.codemirror_1cbb79ce-8994-490c-87ce-56911ab03807_1752491022.319806"
}
```

#### GET /api/codemirror/analyses/{user_id}
Get all analyses for a user

**Response:**
```json
{
  "analyses": [
    {
      "id": "analysis_123",
      "repo_id": "1cbb79ce-8994-490c-87ce-56911ab03807",
      "repo_name": "PRSNL",
      "status": "completed",
      "analysis_type": "repository_analysis",
      "analysis_depth": "standard",
      "progress": 100,
      "created_at": "2025-07-14T11:03:41Z",
      "completed_at": "2025-07-14T11:05:22Z"
    }
  ]
}
```

#### GET /api/codemirror/patterns/{analysis_id}
Get detected code patterns from an analysis

**Response:**
```json
{
  "patterns": [
    {
      "id": "pattern_456",
      "pattern_signature": "singleton_pattern",
      "pattern_type": "design_pattern",
      "description": "Singleton pattern detected in service classes",
      "occurrence_count": 12,
      "solutions": [
        {
          "type": "refactor",
          "description": "Consider dependency injection",
          "code_example": "..."
        }
      ],
      "confidence": 0.92
    }
  ]
}
```

#### GET /api/codemirror/insights/{analysis_id}
Get AI-generated insights from an analysis

**Response:**
```json
{
  "insights": [
    {
      "id": "insight_789",
      "insight_type": "architecture",
      "title": "Microservices Architecture Recommendation",
      "description": "The codebase shows patterns that would benefit from service separation",
      "severity": "medium",
      "recommendation": "Consider extracting authentication logic into a separate service",
      "confidence_score": 0.87
    }
  ]
}
```

#### POST /api/codemirror/cli/sync
Sync analysis results from CodeMirror CLI

**Request Body:**
```json
{
  "cli_analysis_id": "cli_analysis_123",
  "cli_version": "1.0.0",
  "machine_id": "machine_abc123",
  "analysis_results": {
    "patterns": [...],
    "insights": [...],
    "metrics": {...}
  },
  "local_path": "/Users/dev/projects/myrepo",
  "repo_name": "myrepo"
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "analysis_456",
  "message": "CLI analysis synced successfully"
}
```

#### GET /api/codemirror/health
CodeMirror service health check

**Response:**
```json
{
  "status": "healthy",
  "service": "codemirror",
  "agents_available": true,
  "timestamp": "2025-07-14T11:04:00Z"
}
```

### WebSocket Progress Updates

Connect to WebSocket for real-time analysis progress:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws?channel=${websocket_channel}`);
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress}%, Stage: ${update.stage}`);
};
```

### Integration with Job Persistence

CodeMirror analyses are tracked through the unified job persistence system:
- Job type: `codemirror_analysis`
- Monitor progress via `/api/persistence/status/{job_id}`
- Results stored in job persistence for reliability

## 🔄 Job Persistence & Processing - Unified Job Management

### Job Lifecycle Management

The unified job persistence system provides comprehensive tracking and coordination for all processing operations including media processing, AI analysis, and background tasks.

#### POST /api/persistence/save
Save job results with jobId coordination (idempotent operation)

**Request Body:**
```json
{
  "job_id": "media_image_20250713_abc123",
  "result_data": {
    "ocr_text": "Sample text extracted from image",
    "objects_detected": ["person", "computer", "desk"],
    "confidence": 0.95,
    "processing_time": 2.3
  },
  "status": "completed"
}
```

**Response:**
```json
{
  "message": "Results saved successfully for job media_image_20250713_abc123",
  "job_id": "media_image_20250713_abc123",
  "status": "completed",
  "completed_at": "2025-07-13T18:49:10.377177+00:00",
  "result_size": 143
}
```

#### GET /api/persistence/status/{jobId}
Get comprehensive job status and results

**Path Parameters:**
- `jobId` (string, required) - Job identifier

**Response:**
```json
{
  "job_id": "media_image_20250713_abc123",
  "job_type": "media_image",
  "status": "completed",
  "item_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress_percentage": 100,
  "current_stage": "database_save",
  "stage_message": "Analysis results saved to database",
  "error_message": null,
  "result_data": {
    "ocr_text": "Sample text",
    "objects": ["cat", "dog"],
    "confidence": 0.95
  },
  "created_at": "2025-07-13T18:48:51.163023Z",
  "started_at": "2025-07-13T18:48:52.100000Z",
  "completed_at": "2025-07-13T18:49:10.377177Z",
  "last_updated": "2025-07-13T18:49:10.377177Z",
  "retry_count": 0,
  "tags": ["media", "image_analysis"]
}
```

#### PUT /api/persistence/update
Update job status during processing

**Query Parameters:**
- `job_id` (string, required) - Job identifier
- `status` (string, optional) - New job status (pending, processing, completed, failed, cancelled)
- `progress` (integer, optional) - Progress percentage (0-100)
- `stage` (string, optional) - Current processing stage
- `message` (string, optional) - Stage message
- `error` (string, optional) - Error message

**Example:**
```bash
PUT /api/persistence/update?job_id=media_image_20250713_abc123&status=processing&progress=75&stage=analysis&message=Analyzing image content
```

**Response:**
```json
{
  "message": "Job media_image_20250713_abc123 updated successfully",
  "job_id": "media_image_20250713_abc123",
  "status": "processing",
  "progress_percentage": 75,
  "updated_at": "now"
}
```

#### GET /api/persistence/jobs
List jobs with filtering and pagination

**Query Parameters:**
- `job_type` (string, optional) - Filter by job type (media_image, media_video, media_audio, etc.)
- `status` (string, optional) - Filter by status (pending, processing, completed, failed, cancelled)
- `item_id` (UUID, optional) - Filter by associated item
- `limit` (integer, optional, default: 50, max: 200) - Maximum results
- `offset` (integer, optional, default: 0) - Pagination offset

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "media_image_20250713_abc123",
      "job_type": "media_image",
      "status": "completed",
      "progress_percentage": 100,
      "created_at": "2025-07-13T18:48:51.163023Z",
      "completed_at": "2025-07-13T18:49:10.377177Z",
      "tags": ["media", "image_analysis"]
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/persistence/create
Create a new processing job

**Request Body:**
```json
{
  "job_type": "media_image",
  "input_data": {
    "file_path": "/uploads/image.jpg",
    "item_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "metadata": {
    "source": "api",
    "priority": "normal"
  },
  "tags": ["media", "user_upload"]
}
```

**Response:**
```json
{
  "message": "Job created successfully",
  "job_id": "media_image_20250713_def456",
  "job_type": "media_image",
  "status": "pending"
}
```

#### POST /api/persistence/retry/{jobId}
Retry a failed job (increments retry count)

**Response:**
```json
{
  "message": "Job media_image_20250713_abc123 marked for retry",
  "job_id": "media_image_20250713_abc123",
  "status": "pending"
}
```

#### DELETE /api/persistence/cancel/{jobId}
Cancel a pending or processing job

**Response:**
```json
{
  "message": "Job media_image_20250713_abc123 cancelled successfully",
  "job_id": "media_image_20250713_abc123",
  "status": "cancelled"
}
```

#### GET /api/persistence/health
Health check for job persistence service

**Response:**
```json
{
  "status": "healthy",
  "service": "job_persistence",
  "database_connected": true,
  "timestamp": "now"
}
```

### Job Status Values
- `pending` - Job created, waiting to be processed
- `processing` - Job currently being processed
- `completed` - Job completed successfully
- `failed` - Job failed (can be retried)
- `retrying` - Job is being retried after failure
- `cancelled` - Job was manually cancelled

### Job Types
- `media_image` - Image processing (OCR, analysis)
- `media_video` - Video processing (transcription, analysis) 
- `media_audio` - Audio processing (transcription, analysis)
- `embedding` - Embedding generation
- `crawl_ai` - Web crawling and analysis
- `ai_analysis` - AI-powered content analysis

### Integration with Media Processing
The job persistence system is fully integrated with media processing agents. When processing media through `/api/crawl-ai/process-*` endpoints, jobs are automatically created and tracked, providing real-time progress updates and result persistence.

## Core API Endpoints

### 📊 Timeline

#### GET /api/timeline
Get paginated timeline items

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "url": "string",
      "summary": "string",
      "platform": "string",
      "item_type": "article|video|note",
      "thumbnail_url": "string",
      "duration": 120,
      "file_path": "string",
      "createdAt": "2025-07-06T10:00:00Z",
      "updatedAt": "2025-07-06T10:00:00Z",
      "tags": ["string"]
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

### 📝 Capture

#### POST /api/capture
Capture a new item (article, video, note)

**Request Body:**
```json
{
  "url": "https://example.com",
  "title": "Optional title",
  "content": "Optional content for notes",
  "content_type": "auto|document|video|article|tutorial|image|note|link",
  "enable_summarization": true,
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "message": "Item capture initiated",
  "item_id": "uuid",
  "item_type": "article|video|document|note",
  "processing_status": "pending|completed"
}
```

**Notes:**
- Either `url` or `content` must be provided
- Videos are automatically detected and processed asynchronously
- Supported video platforms: Instagram, YouTube, Twitter, TikTok
- AI summarization can be enabled/disabled per content type
- All content types supported: auto, document, video, article, tutorial, image, note, link

### 📁 File Upload

#### POST /api/file/upload
Upload and process files (documents, PDFs, images, etc.)

**Request Body:** `multipart/form-data`
- `files`: File(s) to upload (max 50MB each)
- `url`: Optional URL associated with files
- `title`: Optional title for the item
- `highlight`: Optional highlight text
- `content_type`: Content type classification (auto|document|video|article|tutorial|image|note|link)
- `enable_summarization`: Whether to enable AI summarization (boolean)
- `tags`: JSON string of tags array

**Response:**
```json
{
  "file_id": "uuid",
  "item_id": "uuid", 
  "original_filename": "document.pdf",
  "file_size": 1024000,
  "file_category": "document",
  "processing_status": "completed|processing",
  "message": "File uploaded and processed successfully"
}
```

#### GET /api/file/status/{file_id}
Get file processing status

**Response:**
```json
{
  "file_id": "uuid",
  "status": "completed|processing|failed|ai_failed",
  "progress": 100.0,
  "message": "File processed successfully",
  "extracted_text_length": 5000,
  "word_count": 850,
  "ai_analysis_complete": true
}
```

#### GET /api/file/content/{file_id}
Get file content and metadata

**Response:**
```json
{
  "file_id": "uuid",
  "item_id": "uuid",
  "original_filename": "document.pdf",
  "file_category": "document",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "extracted_text": "Full extracted text content...",
  "word_count": 850,
  "page_count": 5,
  "processing_status": "completed",
  "thumbnail_path": "/path/to/thumbnail.jpg",
  "title": "Document Title",
  "summary": "AI-generated summary",
  "tags": ["tag1", "tag2"],
  "created_at": "2025-07-09T10:00:00Z",
  "processed_at": "2025-07-09T10:01:00Z"
}
```

#### DELETE /api/file/{file_id}
Delete a file and its associated item

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

#### GET /api/file/stats
Get file storage and processing statistics

**Response:**
```json
{
  "storage_stats": [
    {
      "file_category": "document",
      "total_files": 25,
      "total_size_mb": 150.5
    }
  ],
  "processing_stats": [
    {
      "status": "completed",
      "count": 20
    }
  ],
  "recent_files": [
    {
      "file_id": "uuid",
      "filename": "document.pdf",
      "created_at": "2025-07-09T10:00:00Z"
    }
  ]
}
```

### 🔍 Enhanced Search

#### POST /api/search/
Advanced multi-modal search with semantic, keyword, and hybrid modes

**Request Body:**
```json
{
  "query": "machine learning",
  "search_type": "hybrid",
  "limit": 20,
  "threshold": 0.3,
  "include_duplicates": false,
  "filters": {
    "type": "article",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "string",
      "url": "string",
      "snippet": "string",
      "tags": ["string"],
      "created_at": "2025-07-06T10:00:00Z",
      "similarity": 0.89,
      "search_metadata": {
        "has_embedding": true,
        "search_timestamp": "2025-07-06T10:00:00Z"
      },
      "search_type": "hybrid",
      "component_scores": {
        "semantic": 0.85,
        "keyword": 0.92
      }
    }
  ],
  "total": 15,
  "query": "machine learning",
  "search_type": "hybrid",
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  },
  "timestamp": "2025-07-06T10:00:00Z",
  "deduplication": {
    "original_count": 18,
    "deduplicated_count": 15,
    "removed_duplicates": 3
  }
}
```

### 🏷️ Tags

#### GET /api/tags
Get all tags with usage count

**Response:**
```json
[
  {
    "name": "string",
    "count": 10
  }
]
```

### 📄 Items

#### GET /api/items/{id}
Get a single item by ID

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "url": "string",
  "content": "string",
  "summary": "string",
  "platform": "string",
  "item_type": "string",
  "thumbnail_url": "string",
  "duration": 120,
  "file_path": "string",
  "createdAt": "2025-07-06T10:00:00Z",
  "updatedAt": "2025-07-06T10:00:00Z",
  "tags": ["string"],
  "attachments": []
}
```

#### PATCH /api/items/{id}
Update an item

**Request Body:**
```json
{
  "title": "New title",
  "summary": "Updated summary",
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "message": "Item updated successfully",
  "id": "uuid"
}
```

#### DELETE /api/items/{id}
Delete an item

**Response:**
```json
{
  "message": "Item deleted successfully",
  "id": "uuid"
}
```

### 🎥 Videos

#### GET /api/videos/{item_id}/stream
Stream a video file

**Response:** Video file stream

#### GET /api/videos/{item_id}/metadata
Get video metadata

**Response:**
```json
{
  "id": "uuid",
  "url": "string",
  "title": "string",
  "description": "string",
  "author": "string",
  "duration": 120,
  "video_path": "string",
  "thumbnail_path": "string",
  "platform": "instagram",
  "metadata": {},
  "downloaded_at": "2025-07-06T10:00:00Z",
  "status": "completed"
}
```

#### POST /api/videos/{item_id}/transcode
Request video transcoding

**Request Body:**
```json
{
  "quality": "high|standard"
}
```

#### DELETE /api/videos/{item_id}
Delete a video and associated files

### 💬 Telegram

#### POST /api/telegram/webhook
Webhook endpoint for Telegram bot updates

#### POST /api/telegram/setup-webhook
Manually setup Telegram webhook

### 💻 Development Content

#### GET /api/development/stats
Get development content statistics and analytics

**Response:**
```json
{
  "total_items": 4,
  "by_language": {
    "python": 2,
    "javascript": 1,
    "dockerfile": 1
  },
  "by_category": {
    "Backend": 1,
    "Frontend": 1,
    "DevOps": 1
  },
  "by_difficulty": {
    "2": 2,
    "3": 1,
    "4": 1
  },
  "career_related_count": 1,
  "recent_activity": [
    {
      "id": "uuid",
      "title": "GitHub - fastapi/fastapi: FastAPI framework",
      "programming_language": "python",
      "project_category": "Backend",
      "created_at": "2025-07-11T04:22:42Z"
    }
  ]
}
```

#### GET /api/development/docs
Get development documents with filtering

**Query Parameters:**
- `limit` (integer, default: 20) - Items per page
- `offset` (integer, default: 0) - Pagination offset
- `category` (string) - Filter by project category
- `language` (string) - Filter by programming language
- `difficulty` (integer, 1-5) - Filter by difficulty level
- `career_related` (boolean) - Filter career-related content
- `search` (string) - Full-text search query

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "GitHub - fastapi/fastapi: FastAPI framework",
    "url": "https://github.com/fastapi/fastapi",
    "summary": "High performance web framework for Python",
    "type": "development",
    "programming_language": "python",
    "project_category": "Backend",
    "difficulty_level": 2,
    "is_career_related": false,
    "learning_path": null,
    "code_snippets": [],
    "created_at": "2025-07-11T04:22:42Z",
    "updated_at": "2025-07-11T04:22:43Z",
    "tags": ["python", "api", "framework"]
  }
]
```

#### GET /api/development/categories
Get all development categories with item counts

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Frontend",
    "description": "Frontend development resources",
    "icon": "🎨",
    "color": "#3b82f6",
    "created_at": "2025-07-11T00:00:00Z",
    "item_count": 2
  }
]
```

#### GET /api/development/languages
Get all programming languages found in development content

**Response:**
```json
{
  "languages": [
    {
      "name": "python",
      "count": 2
    },
    {
      "name": "javascript", 
      "count": 1
    }
  ]
}
```

**Example Usage:**
```bash
# Get development statistics
curl "http://localhost:8000/api/development/stats"

# Search Python backend content
curl "http://localhost:8000/api/development/docs?language=python&category=Backend"

# Get all development categories
curl "http://localhost:8000/api/development/categories"
```

### 📊 Admin

#### GET /api/storage/metrics
Get storage usage metrics

**Response:**
```json
{
  "total_size_bytes": 1000000,
  "video_count": 10,
  "thumbnail_count": 30,
  "temp_files_count": 5
}
```

### 🏥 Health

#### GET /health
Check system health

**Response:**
```json
{
  "database": {
    "status": "UP",
    "details": ""
  },
  "ollama": {
    "status": "UP",
    "details": ""
  },
  "disk_space": {
    "status": "UP",
    "details": {
      "total": "100.00 GB",
      "used": "50.00 GB",
      "free": "50.00 GB",
      "percentage_free": "50.00%"
    }
  },
  "overall_status": "UP"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message",
  "status": 400
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## Data Formats

### Timestamps
All timestamps are in ISO 8601 format with UTC timezone:
`2025-07-06T10:00:00Z`

### IDs
All IDs are UUIDs in standard format:
`123e4567-e89b-12d3-a456-426614174000`

## Frontend Integration Notes

### Field Name Conventions
The backend now returns camelCase fields directly for frontend compatibility:
- `createdAt` (instead of `created_at`)
- `updatedAt` (instead of `updated_at`)

Note: Some fields still use snake_case:
- `item_type`
- `thumbnail_url`
- `file_path`

### CORS Configuration
Allowed origins:
- `http://localhost:3000`
- `http://localhost:3003`
- `http://localhost:5173`

## Rate Limiting
Currently no rate limiting in development mode

## Future Enhancements
- [ ] Authentication & Authorization
- [ ] WebSocket support for real-time updates
- [ ] Batch operations
- [ ] GraphQL endpoint
- [ ] API versioning
- [ ] Rate limiting
- [ ] Pagination cursors