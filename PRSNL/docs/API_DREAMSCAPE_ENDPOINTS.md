# Dreamscape API Endpoints Documentation

> **PersonaAnalysisCrew API endpoints for the Dreamscape feature**

This document provides comprehensive documentation for the Dreamscape PersonaAnalysisCrew API endpoints, part of PRSNL's AI-powered personal intelligence system.

## Base URL

```
http://localhost:8000/api/persona
```

## Authentication

All endpoints require valid authentication tokens. In development, authentication is bypassed for testing purposes.

## Endpoints Overview

### 1. Health Check

**GET** `/health`

Check the status of the PersonaAnalysisCrew service.

#### Response
```json
{
  "status": "healthy",
  "service": "persona-analysis",
  "crew_agents": [
    "technical_agent",
    "lifestyle_agent", 
    "learning_agent",
    "cross_domain_agent",
    "orchestrator_agent"
  ]
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/api/persona/health"
```

---

### 2. Analyze User Persona

**POST** `/analyze`

Trigger comprehensive persona analysis for a user using the 5-agent CrewAI system.

#### Request Body
```json
{
  "user_id": "uuid",
  "analysis_depth": "standard",
  "focus_areas": [],
  "background": true
}
```

#### Parameters
- **user_id** (UUID, required): User ID to analyze
- **analysis_depth** (string, optional): Analysis depth level
  - `"light"`: 30-60 seconds, basic patterns
  - `"standard"`: 1-2 minutes, comprehensive analysis (default)
  - `"deep"`: 2-5 minutes, extensive analysis with predictions
- **focus_areas** (array, optional): Specific areas to focus on
  - `"technical"`: Coding skills and technical behavior
  - `"learning"`: Educational preferences and patterns
  - `"lifestyle"`: Interests and activity patterns
  - `"cross-domain"`: Connections between different areas
- **background** (boolean, optional): Run analysis in background (default: true)

#### Response (Background Mode)
```json
{
  "user_id": "uuid",
  "status": "started",
  "message": "Persona analysis started in background",
  "analysis_id": "uuid"
}
```

#### Response (Synchronous Mode)
```json
{
  "user_id": "uuid",
  "status": "completed",
  "message": "Persona analysis completed",
  "persona_data": {
    "technical_profile": {...},
    "lifestyle_profile": {...},
    "learning_style": {...},
    "cross_domain_insights": {...},
    "behavioral_metrics": {...}
  }
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/persona/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "analysis_depth": "standard",
    "focus_areas": ["technical", "learning"],
    "background": true
  }'
```

---

### 3. Get User Persona

**GET** `/user/{user_id}`

Retrieve complete persona data for a user.

#### Parameters
- **user_id** (UUID, required): User ID to retrieve

#### Response
```json
{
  "user_id": "uuid",
  "analysis_timestamp": "2025-07-28T10:30:00Z",
  "crew_insights": "Detailed AI-generated insights...",
  "technical_profile": {
    "primary_languages": ["Python", "JavaScript"],
    "skill_levels": {
      "Python": "intermediate",
      "JavaScript": "beginner"
    },
    "domains": ["Web Development", "Data Science"],
    "tools": ["VSCode", "Git"]
  },
  "lifestyle_profile": {
    "interests": ["technology", "learning"],
    "activity_patterns": {
      "morning": 0.3,
      "afternoon": 0.4,
      "evening": 0.3
    },
    "content_preferences": {
      "article": 0.6,
      "video": 0.4
    }
  },
  "learning_style": {
    "preferred_formats": ["hands-on", "visual"],
    "attention_span": "medium",
    "complexity_preference": "moderate",
    "learning_goals": ["skill_development", "career_advancement"]
  },
  "cross_domain_insights": {
    "connections": [],
    "project_potential": [],
    "innovation_opportunities": []
  },
  "life_phase": "mid_career",
  "interests_evolution": {...},
  "behavioral_metrics": {
    "learning_velocity": 0.75,
    "engagement_score": 0.82,
    "diversity_score": 0.6
  },
  "recommendations": [
    "Consider advanced features and power-user tools"
  ]
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000"
```

---

### 4. Get Persona Summary

**GET** `/user/{user_id}/summary`

Get a concise summary of user persona for quick access and dashboards.

#### Parameters
- **user_id** (UUID, required): User ID to summarize

#### Response
```json
{
  "user_id": "uuid",
  "life_phase": "mid_career",
  "last_analyzed": "2025-07-28T10:30:00Z",
  "technical_summary": {
    "primary_languages": ["Python", "JavaScript", "TypeScript"],
    "top_domains": ["Web Development", "Data Science"],
    "skill_level": "intermediate"
  },
  "lifestyle_summary": {
    "top_interests": ["technology", "learning", "productivity"],
    "activity_preference": "evening",
    "content_preference": "article"
  },
  "learning_summary": {
    "preferred_format": "hands-on",
    "attention_span": "medium",
    "complexity_preference": "moderate"
  },
  "key_recommendations": [
    "Consider advanced features and power-user tools",
    "Focus on evening learning sessions",
    "Leverage cross-domain project opportunities"
  ]
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000/summary"
```

---

### 5. Update Persona Insights

**PUT** `/user/{user_id}/insights`

Update specific persona insights without triggering full reanalysis.

#### Parameters
- **user_id** (UUID, required): User ID to update

#### Request Body
```json
{
  "insights": {
    "connections": [
      {
        "domain1": "programming",
        "domain2": "music",
        "connection_type": "pattern_recognition",
        "strength": 0.8
      }
    ],
    "project_potential": [
      "AI-powered music composition tool"
    ]
  }
}
```

#### Response
```json
{
  "user_id": "uuid",
  "status": "updated",
  "message": "Persona insights updated successfully"
}
```

#### Example
```bash
curl -X PUT "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "insights": {
      "project_potential": ["AI music tool", "Code visualization app"]
    }
  }'
```

---

### 6. Batch Analyze Personas

**POST** `/batch-analyze`

Trigger persona analysis for multiple users simultaneously.

#### Request Body
```json
{
  "user_ids": [
    "uuid1",
    "uuid2", 
    "uuid3"
  ],
  "analysis_depth": "light"
}
```

#### Parameters
- **user_ids** (array, required): List of user UUIDs to analyze
- **analysis_depth** (string, optional): Analysis depth for all users (default: "light")

#### Response
```json
{
  "status": "started",
  "message": "Batch analysis started for 3 users",
  "user_count": 3
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/persona/batch-analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "456e7890-e89b-12d3-a456-426614174001"
    ],
    "analysis_depth": "light"
  }'
```

---

## Analysis Depth Comparison

| Depth | Duration | Features |
|-------|----------|----------|
| **Light** | 30-60s | Basic behavioral patterns, surface-level preferences, quick personality insights |
| **Standard** | 1-2min | Comprehensive multi-agent analysis, detailed persona construction, cross-domain discovery |
| **Deep** | 2-5min | Extensive behavioral analysis, advanced pattern recognition, predictive insights |

## Focus Areas Detail

### Technical
- Programming language proficiency detection
- Development tool preferences
- Technical skill level assessment
- Project complexity preferences
- Learning velocity in technical domains

### Lifestyle
- Activity timing preferences
- Interest area identification
- Content consumption habits
- Social interaction patterns
- Work-life balance indicators

### Learning
- Learning format preferences (video, text, hands-on)
- Attention span and session patterns
- Complexity tolerance assessment
- Practice vs theory preferences
- Feedback and validation needs

### Cross-Domain
- Skill transfer opportunity identification
- Innovation potential from domain intersections
- Project ideas from combined interests
- Unique pattern recognition
- Cross-pollination insights

## Error Handling

All endpoints return standard HTTP status codes:

- **200**: Success
- **404**: Persona not found
- **422**: Validation error (invalid request format)
- **500**: Internal server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

- Analysis endpoints: 10 requests per minute per user
- Retrieval endpoints: 60 requests per minute per user
- Batch operations: 5 requests per minute per user

## Usage Examples

### Complete Analysis Workflow

```bash
# 1. Start analysis
curl -X POST "http://localhost:8000/api/persona/analyze" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123e4567-e89b-12d3-a456-426614174000"}'

# 2. Check if analysis completed (wait 1-2 minutes)
curl -X GET "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000/summary"

# 3. Get full persona data
curl -X GET "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000"

# 4. Update insights based on new information
curl -X PUT "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000/insights" \
  -H "Content-Type: application/json" \
  -d '{"insights": {"new_skill": "machine_learning"}}'
```

### Dashboard Integration

```bash
# Get summary for dashboard display
curl -X GET "http://localhost:8000/api/persona/user/123e4567-e89b-12d3-a456-426614174000/summary"

# Health check for service status
curl -X GET "http://localhost:8000/api/persona/health"
```

## Integration Notes

### Frontend Integration
- Use background analysis for better UX
- Show progress indicators during analysis
- Cache summary data for dashboard performance
- Handle 404 responses for new users gracefully

### Database Schema
The persona analysis data is stored in the `user_personas` table:
- `user_id`: UUID primary key
- `technical_profile`: JSONB column
- `lifestyle_profile`: JSONB column
- `learning_style`: JSONB column
- `life_phase`: TEXT column
- `cross_domain_insights`: JSONB column
- `last_analyzed_at`: TIMESTAMP
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

### Performance Considerations
- Analysis operations are CPU intensive (1-5 minutes)
- Use background processing for better responsiveness
- Consider caching persona summaries
- Monitor Azure OpenAI API usage and costs

---

**Dreamscape PersonaAnalysisCrew** - Multi-agent AI system for intelligent user understanding 🧠✨