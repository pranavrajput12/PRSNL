# 📚 PRSNL Complete API Documentation - Production-Ready System

This comprehensive API reference combines detailed endpoint documentation with security contracts and authentication requirements for the complete PRSNL API ecosystem.

---

## 🌐 Base URLs & Client Applications

### API Endpoints
- **Development**: `http://localhost:8000/api`
- **Frontend Proxy**: `http://localhost:3004/api`
- **AI Services**: `http://localhost:8000/api/ai`
- **LibreChat API**: `http://localhost:8000/api/ai`

### Client Applications
- **SvelteKit Frontend**: Web application (port 3004 dev, 3003 container)
- **iOS App (PRSNL APP)**: Native iOS application - *separate codebase*
- **Chrome Extension**: Browser extension
- **LibreChat Integration**: OpenAI-compatible chat interface
- **AI Services**: Intelligent content analysis and suggestions

### Application Structure (Neural Nest Theme)
- **Neural Nest** (`/`) - Main dashboard and knowledge hub
- **Ingest** (`/capture`) - Content capture and ingestion
- **Thought Stream** (`/timeline`) - Chronological content timeline
- **Cognitive Map** (`/insights`) - AI-powered insights and analysis
- **Mind Palace** (`/chat`) - Conversational interface with knowledge base
- **Visual Cortex** (`/videos`) - Video content management
- **Code Cortex** (`/code-cortex`) - Development content management hub
- **Knowledge Sync** (`/import`) - External data import and synchronization

---

## 🔐 Authentication System - Production Ready

### JWT Authentication Flow
1. User registers with email and password
2. Email verification sent via Resend API
3. User verifies email or uses magic link
4. Access and refresh tokens issued
5. Tokens automatically refresh on expiry

### Token Configuration
- **Access Token**: 15 minutes expiration
- **Refresh Token**: 7 days expiration
- **Headers**: `Authorization: Bearer {access_token}`

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

**Response (201):**
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

**Response (200):**
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

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /api/auth/send-magic-link
Request passwordless magic link

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Magic link sent to your email"
}
```

#### POST /api/auth/verify-email
Verify email address with token

**Request Body:**
```json
{
  "token": "verification_token_from_email"
}
```

**Response (200):**
```json
{
  "message": "Email verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /api/auth/forgot-password
Request password reset email

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Notes:**
- Returns success regardless of email existence to prevent enumeration attacks
- Reset link expires in 1 hour
- Professional email template with security messaging
- Rate limited to prevent abuse

#### POST /api/auth/reset-password
Reset password using token from email

**Request Body:**
```json
{
  "token": "password_reset_token_from_email",
  "new_password": "NewSecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

**Response (400) - Invalid/Expired Token:**
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Notes:**
- Token can only be used once
- All user sessions are revoked after successful password reset
- Password must meet security requirements (8+ chars, mixed case, digit)

#### GET /api/auth/me
Get current user profile

**Headers:** `Authorization: Bearer {access_token}`

**Response (200):**
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

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "Jane Doe"
}
```

**Response (200):**
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

---

## 🎤 Voice Integration API - Advanced Features

### Voice Settings Management

#### GET /api/user/settings
Get user voice settings

**Headers:** `Authorization: Bearer {access_token}`

**Response (200):**
```json
{
  "voice_settings": {
    "tts_model": "chatterbox",
    "emotion": "friendly",
    "speed": 1.0,
    "pitch": 0,
    "language": "en"
  }
}
```

#### PUT /api/user/settings
Update voice settings

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "voice_settings": {
    "tts_model": "chatterbox",
    "emotion": "excited",
    "speed": 1.2,
    "pitch": 5
  }
}
```

### Text-to-Speech Services

#### POST /api/voice/tts
Convert text to speech with emotional control

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "text": "Hello! I'm excited to help you today.",
  "emotion": "excited",
  "speed": 1.0,
  "pitch": 0,
  "model": "chatterbox"
}
```

**Available Emotions:**
- `neutral` - Default, balanced tone
- `happy` - Upbeat and cheerful
- `sad` - Subdued and melancholic
- `angry` - Intense and forceful
- `excited` - Energetic and enthusiastic
- `calm` - Soothing and relaxed
- `friendly` - Warm and welcoming

**Response:** Binary audio content (MP3)

#### POST /api/voice/transcribe
Transcribe audio to text

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:** `multipart/form-data`
- `audio`: Audio file
- `language`: Language code (optional, default: "en")

**Response (200):**
```json
{
  "text": "Transcribed text from audio",
  "language": "en",
  "confidence": 0.95
}
```

#### GET /api/voice/models
List available voice models

**Response (200):**
```json
{
  "models": [
    {
      "id": "chatterbox",
      "name": "Chatterbox TTS",
      "type": "neural",
      "emotions": ["neutral", "happy", "sad", "angry", "excited", "calm", "friendly"]
    },
    {
      "id": "edge-tts",
      "name": "Edge TTS",
      "type": "neural",
      "emotions": ["neutral"]
    }
  ]
}
```

### Real-time Voice Streaming

#### WebSocket /api/voice/ws/streaming
Real-time speech transcription with RealtimeSTT

**Connection:** `ws://localhost:8000/api/voice/ws/streaming`

**Headers:** `Authorization: Bearer {access_token}`

**Message Types:**

**Client → Server (Audio Data):**
```json
{
  "type": "audio_data",
  "data": "base64_encoded_audio_chunk"
}
```

**Server → Client (Partial Transcription):**
```json
{
  "type": "partial_transcript",
  "text": "Hello, this is a partial...",
  "confidence": 0.85
}
```

**Server → Client (Final Transcription):**
```json
{
  "type": "final_transcript",
  "text": "Hello, this is a complete sentence.",
  "confidence": 0.95
}
```

**Server → Client (AI Response):**
```json
{
  "type": "ai_response",
  "text": "I understand your request. Let me help you with that.",
  "audio_url": "/api/voice/audio/response_123.mp3"
}
```

---

## 🤖 AI Services API - Phase 4 Advanced Orchestration

### AI Health & Status

#### GET /api/ai/health
Get comprehensive AI service status

**Response (200):**
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
  "langraph_workflows": "enabled",
  "enhanced_routing": "active",
  "timestamp": "2025-07-23T10:30:00Z"
}
```

### AI Content Processing

#### POST /api/ai-suggest
Advanced AI-powered content analysis and suggestions

**Headers:** `Authorization: Bearer {access_token}`

**Request Body (Content Analysis):**
```json
{
  "content": "Content to analyze and process",
  "title": "Optional title",
  "tags": ["tag1", "tag2"],
  "url": "https://example.com",
  "type": "article",
  "context": {
    "use_workflow": true,
    "analysis_depth": "standard"
  }
}
```

**Request Body (Learning Path):**
```json
{
  "goal": "Master FastAPI and async Python for building high-performance APIs",
  "current_knowledge": ["Python basics", "HTTP fundamentals", "REST APIs"],
  "time_commitment": "intensive"
}
```

**Request Body (Topic Exploration):**
```json
{
  "topic": "Machine Learning for Knowledge Management",
  "user_interests": ["python", "ai", "automation"],
  "depth": 3
}
```

**Response (Content Analysis):**
```json
{
  "request_id": "content-1752355349.848207",
  "status": "completed",
  "workflow_enabled": true,
  "results": {
    "agent_outputs": {
      "knowledge_curator": "Detailed categorization and enhancement suggestions...",
      "research_synthesizer": "Comprehensive synthesis and insights..."
    },
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
  },
  "agents_involved": ["knowledge_curator", "research_synthesizer"],
  "execution_time": 10.546185,
  "timestamp": "2025-07-23T10:30:00Z"
}
```

### AI Router - Enhanced Routing System

#### GET /api/ai-router/status
Get AI Router health and performance metrics

**Response (200):**
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
Test AI Router provider selection logic

**Headers:** `Authorization: Bearer {access_token}`

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

**Response (200):**
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

### LibreChat - OpenAI Compatible API

#### POST /api/ai/chat/completions
OpenAI-compatible chat completions with knowledge base integration

**Headers:** 
- `Authorization: Bearer {access_token}`
- `Content-Type: application/json`
- `X-PRSNL-Integration: client-name` (optional)

**Request Body:**
```json
{
  "model": "prsnl-gpt-4",
  "messages": [
    {"role": "user", "content": "How does PRSNL work as a second brain system?"}
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false
}
```

**Response (Non-streaming):**
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

**Streaming Response (when `"stream": true`):**
```
data: {"id": "chatcmpl-1752374627", "object": "chat.completion.chunk", "created": 1752374627, "model": "prsnl-gpt-4", "choices": [{"index": 0, "delta": {"content": " Enhanced Information"}, "finish_reason": null}]}

data: {"id": "chatcmpl-1752374627", "object": "chat.completion.chunk", "created": 1752374627, "model": "prsnl-gpt-4", "choices": [{"index": 0, "delta": {"content": " Retrieval: AI can"}, "finish_reason": null}]}

data: [DONE]
```

#### GET /api/ai/models
List available AI models

**Response (200):**
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

---

## 📊 Content Management API

### Content Capture

#### POST /api/capture
Capture content with enhanced options

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "url": "https://example.com",
  "content": "Direct text content",
  "title": "Optional title",
  "highlight": "Highlighted text",
  "tags": ["tag1", "tag2"],
  "content_type": "auto|article|video|document|note|link|development",
  "enable_summarization": true,
  "programming_language": "python",
  "project_category": "backend",
  "difficulty_level": 3
}
```

**Validation:** Either `url` or `content` required

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending|completed|failed",
  "message": "Content captured successfully",
  "item_type": "article",
  "processing_enabled": true,
  "duplicate_info": null
}
```

#### POST /api/capture/check-duplicate
Check for duplicate content

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response (200):**
```json
{
  "is_duplicate": false,
  "existing_item": null
}
```

### Content Retrieval

#### GET /api/items/{item_id}
Get detailed item information

**Headers:** `Authorization: Bearer {access_token}`

**Path Parameters:** `item_id` (UUID)

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "title": "Example Article",
  "summary": "AI-generated summary",
  "content": "Full content text",
  "tags": ["technology", "ai"],
  "created_at": "2025-07-23T10:30:00Z",
  "updated_at": "2025-07-23T10:30:00Z",
  "accessed_at": "2025-07-23T10:30:00Z",
  "access_count": 5,
  "status": "completed",
  "item_type": "article",
  "platform": "web",
  "duration": null,
  "file_path": null,
  "thumbnail_url": "https://example.com/thumb.jpg",
  "metadata": {
    "video_metadata": null,
    "ai_analysis": {
      "summary": "...",
      "tags": [...],
      "key_points": [...]
    }
  }
}
```

#### PATCH /api/items/{item_id}
Update item information

**Headers:** `Authorization: Bearer {access_token}`

**Path Parameters:** `item_id` (UUID)

**Request Body:**
```json
{
  "title": "Updated title",
  "summary": "Updated summary",
  "tags": ["updated", "tags"]
}
```

**Response (200):** Updated item object

#### DELETE /api/items/{item_id}
Delete an item

**Headers:** `Authorization: Bearer {access_token}`

**Path Parameters:** `item_id` (UUID)

**Response (200):**
```json
{
  "message": "Item deleted successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Timeline & Search

#### GET /api/timeline
Get chronological content timeline

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**
- `limit` (integer, default: 20, max: 100)
- `cursor` (string, optional, for pagination)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Example Article",
      "url": "https://example.com",
      "snippet": "Article preview text...",
      "tags": ["technology", "ai"],
      "created_at": "2025-07-23T10:30:00Z",
      "item_type": "article",
      "thumbnail_url": "https://example.com/thumb.jpg"
    }
  ],
  "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNS0wNy0yM1QxMDozMDowMFoifQ"
}
```

#### POST /api/search/
Enhanced multi-modal search

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "query": "search query",
  "search_type": "semantic|keyword|hybrid",
  "limit": 20,
  "threshold": 0.3,
  "include_duplicates": false
}
```

**Response (200):**
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Matching Article",
      "snippet": "Relevant excerpt...",
      "url": "https://example.com",
      "tags": ["relevant", "tags"],
      "created_at": "2025-07-23T10:30:00Z",
      "similarity": 0.89,
      "search_type": "hybrid",
      "component_scores": {
        "semantic": 0.85,
        "keyword": 0.92
      }
    }
  ],
  "total": 15,
  "query": "search query",
  "search_type": "hybrid",
  "deduplication": {
    "original_count": 18,
    "deduplicated_count": 15,
    "removed_duplicates": 3
  }
}
```

---

## 🔍 CodeMirror - AI Repository Intelligence

### Repository Analysis

#### POST /api/codemirror/analyze/{repo_id}
Start AI-powered repository analysis

**Headers:** `Authorization: Bearer {access_token}`

**Path Parameters:** `repo_id` (UUID)

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

**Response (202):**
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

**Headers:** `Authorization: Bearer {access_token}`

**Response (200):**
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
      "created_at": "2025-07-23T10:30:00Z",
      "completed_at": "2025-07-23T10:32:00Z"
    }
  ]
}
```

#### GET /api/codemirror/patterns/{analysis_id}
Get detected code patterns

**Headers:** `Authorization: Bearer {access_token}`

**Response (200):**
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
          "code_example": "class ServiceClass:\n    def __init__(self, dependency: Dependency):\n        self.dependency = dependency"
        }
      ],
      "confidence": 0.92
    }
  ]
}
```

#### GET /api/codemirror/insights/{analysis_id}
Get AI-generated insights

**Headers:** `Authorization: Bearer {access_token}`

**Response (200):**
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

---

## 🔄 Job Persistence & Processing System

### Job Management

#### POST /api/persistence/save
Save job results (idempotent operation)

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "job_id": "media_image_20250723_abc123",
  "result_data": {
    "ocr_text": "Sample text extracted from image",
    "objects_detected": ["person", "computer", "desk"],
    "confidence": 0.95,
    "processing_time": 2.3
  },
  "status": "completed"
}
```

**Response (200):**
```json
{
  "message": "Results saved successfully for job media_image_20250723_abc123",
  "job_id": "media_image_20250723_abc123",
  "status": "completed",
  "completed_at": "2025-07-23T10:30:00Z",
  "result_size": 143
}
```

#### GET /api/persistence/status/{job_id}
Get comprehensive job status

**Headers:** `Authorization: Bearer {access_token}`

**Path Parameters:** `job_id` (string)

**Response (200):**
```json
{
  "job_id": "media_image_20250723_abc123",
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
  "created_at": "2025-07-23T10:28:00Z",
  "started_at": "2025-07-23T10:28:30Z",
  "completed_at": "2025-07-23T10:30:00Z",
  "last_updated": "2025-07-23T10:30:00Z",
  "retry_count": 0,
  "tags": ["media", "image_analysis"]
}
```

#### PUT /api/persistence/update
Update job status during processing

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**
- `job_id` (string, required)
- `status` (string, optional) - pending, processing, completed, failed, cancelled
- `progress` (integer, optional) - 0-100
- `stage` (string, optional)
- `message` (string, optional)
- `error` (string, optional)

**Response (200):**
```json
{
  "message": "Job media_image_20250723_abc123 updated successfully",
  "job_id": "media_image_20250723_abc123",
  "status": "processing",
  "progress_percentage": 75,
  "updated_at": "2025-07-23T10:29:00Z"
}
```

#### GET /api/persistence/jobs
List jobs with filtering

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**
- `job_type` (string, optional) - Filter by type
- `status` (string, optional) - Filter by status
- `limit` (integer, optional, default: 20)
- `offset` (integer, optional, default: 0)

**Response (200):**
```json
{
  "jobs": [
    {
      "job_id": "media_image_20250723_abc123",
      "job_type": "media_image",
      "status": "completed",
      "progress_percentage": 100,
      "created_at": "2025-07-23T10:28:00Z",
      "completed_at": "2025-07-23T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## 📊 Analytics & Insights API

### Analytics Endpoints

#### GET /api/analytics/trends
Content trends analysis

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:** `timeframe` (7d|30d|90d|1y, default: 7d)

**Response (200):**
```json
{
  "trends": [
    {
      "date": "2025-07-23",
      "count": 15
    },
    {
      "date": "2025-07-22",
      "count": 12
    }
  ],
  "timeframe": "7d",
  "total_items": 127
}
```

#### GET /api/analytics/topics
Top topics analysis

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:** `limit` (integer, default: 10)

**Response (200):**
```json
{
  "topics": [
    {
      "tag": "technology",
      "count": 45,
      "percentage": 35.4
    },
    {
      "tag": "ai",
      "count": 32,
      "percentage": 25.2
    }
  ]
}
```

---

## 🚨 Error Handling & Status Codes

### HTTP Status Codes
- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **202 Accepted** - Request accepted for processing
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required or failed
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity** - Validation errors
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-07-23T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Rate Limiting
- **Capture endpoints**: 10 requests per minute
- **Search endpoints**: 60 requests per minute
- **Voice endpoints**: 30 requests per minute
- **AI endpoints**: 20 requests per minute

### Security Requirements
- All endpoints require valid JWT authentication
- CORS configured for allowed origins
- Request size limits enforced
- Rate limiting per user/IP
- Input validation and sanitization

---

**Last Updated**: 2025-07-23  
**API Version**: v8.0 Production Ready  
**Authentication**: Full JWT implementation with email verification  
**Security Status**: Production-ready with comprehensive authentication

This complete API documentation serves as the definitive reference for all PRSNL API interactions, covering authentication, content management, AI services, voice integration, and system administration.