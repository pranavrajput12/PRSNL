# Current Agent System Analysis - PRSNL Project

## Overview
This document provides a comprehensive analysis of the current agent system implementation in PRSNL, which will be migrated to Crew.ai.

## 1. Agent Systems Inventory

### 1.1 Crawl.ai Multi-Agent System
**Location**: `/backend/app/services/crawl_ai_agents.py`
**Purpose**: Primary orchestration system for web crawling and content analysis

#### Agents:
1. **KnowledgeCuratorAgent**
   - Purpose: Curates knowledge from web content
   - Methods: `curate_knowledge(content, context)`
   - Output: Structured knowledge with summaries and themes

2. **ResearchSynthesisAgent**
   - Purpose: Synthesizes research from multiple sources
   - Methods: `synthesize_research(sources, topic)`
   - Output: Comprehensive research synthesis

3. **ContentExplorerAgent**
   - Purpose: Explores and analyzes content structure
   - Methods: `explore_content(url, depth)`
   - Output: Content map and recommendations

4. **LearningPathAgent**
   - Purpose: Creates learning paths from content
   - Methods: `create_learning_path(topic, level)`
   - Output: Structured learning journey

#### Orchestrator:
- **CrawlAIOrchestrator**: Coordinates agent workflows
- Methods:
  - `execute_workflow(workflow_type, params)`
  - `execute_multi_agent_workflow(agents, params)`

### 1.2 CodeMirror Intelligence Agents
**Location**: `/backend/app/services/codemirror_agents.py`
**Purpose**: Repository analysis and code intelligence

#### Agents:
1. **CodeRepositoryAnalysisAgent**
   - Purpose: Analyzes repository structure and architecture
   - Methods: `analyze_repository(repo_data)`
   - Output: Architecture patterns, frameworks detected

2. **CodePatternDetectionAgent**
   - Purpose: Detects code patterns and anti-patterns
   - Methods: `detect_patterns(code_base)`
   - Output: Pattern signatures with confidence scores

3. **CodeInsightGeneratorAgent**
   - Purpose: Generates actionable insights from code
   - Methods: `generate_insights(analysis_results)`
   - Output: Prioritized insights with recommendations

### 1.3 Conversation Intelligence Agents
**Location**: `/backend/app/services/conversation_agents.py`
**Purpose**: Extract intelligence from conversations

#### Agents:
1. **TechnicalContentExtractor**
   - Purpose: Extract technical details from conversations
   - Methods: `extract_technical_content(conversation)`

2. **LearningJourneyAnalyzer**
   - Purpose: Analyze learning progression
   - Methods: `analyze_learning_journey(conversations)`

3. **ActionableInsightsExtractor**
   - Purpose: Extract actionable insights
   - Methods: `extract_actionable_insights(content)`

4. **KnowledgeGapIdentifier**
   - Purpose: Identify knowledge gaps
   - Methods: `identify_knowledge_gaps(knowledge_base)`

### 1.4 Media Processing Agents
**Location**: `/backend/app/services/media_agents.py`
**Purpose**: Process various media types

#### Agents:
1. **OCRImageAnalysisAgent**
   - Purpose: Extract text and analyze images
   - Methods: `analyze_image(image_data)`

2. **VideoTranscriptionAgent**
   - Purpose: Transcribe and analyze videos
   - Methods: `process_video(video_data)`

3. **AudioJournalAgent**
   - Purpose: Process audio journals
   - Methods: `process_audio(audio_data)`

## 2. API Endpoints

### 2.1 Crawl.ai Integration API
**Location**: `/backend/app/api/crawl_ai_integration.py`
**Base Path**: `/api/crawl-ai`

#### Endpoints:
1. `POST /crawl/{url:path}` - Intelligent web crawling
2. `POST /workflow` - Execute agent workflow
3. `GET /status/{job_id}` - Check job status

### 2.2 CodeMirror API
**Location**: `/backend/app/api/codemirror.py`
**Base Path**: `/api/codemirror`

#### Endpoints:
1. `POST /analyze/{repo_id}` - Start repository analysis
2. `GET /analysis/{analysis_id}` - Get analysis results
3. `GET /insights/{repo_id}` - Get repository insights

### 2.3 Agent Monitoring API
**Location**: `/backend/app/api/agent_monitoring_api.py`
**Base Path**: `/api/agent-monitoring`

#### Endpoints:
1. `GET /agents` - List all agents
2. `GET /performance/{agent_id}` - Get agent performance
3. `GET /executions` - Get execution history

## 3. Database Schema

### 3.1 Agent Performance Tables
```sql
-- agent_registry
CREATE TABLE agent_registry (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capabilities JSONB,
    configuration JSONB,
    status VARCHAR(50),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- agent_executions
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) REFERENCES agent_registry(agent_id),
    workflow_id VARCHAR(255),
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT,
    metadata JSONB
);

-- agent_performance_metrics
CREATE TABLE agent_performance_metrics (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255) REFERENCES agent_registry(agent_id),
    metric_type VARCHAR(100),
    metric_value FLOAT,
    timestamp TIMESTAMPTZ,
    metadata JSONB
);
```

## 4. Worker Tasks

### 4.1 Agent Coordination Tasks
**Location**: `/backend/app/workers/agent_coordination_tasks.py`

#### Tasks:
- `execute_agent_workflow` - Orchestrates agent workflows
- `monitor_agent_execution` - Monitors execution progress
- `aggregate_agent_results` - Combines results from multiple agents

### 4.2 Media Processing Tasks
**Location**: `/backend/app/workers/media_processing_tasks.py`

#### Tasks:
- `process_media_with_agents` - Routes media to appropriate agents
- `aggregate_media_insights` - Combines insights from media agents

## 5. Service Dependencies

### 5.1 Core Services Used by Agents
1. **UnifiedAIService** - LLM integration (Azure OpenAI)
2. **CrawlAIService** - Web crawling functionality
3. **MediaPersistenceService** - Media storage
4. **JobPersistenceService** - Job tracking
5. **CacheService** - Result caching

### 5.2 Import Patterns
```python
# Common imports in agent files
from app.services.unified_ai_service import unified_ai_service
from app.services.crawl_ai_service import CrawlAIService
from app.services.job_persistence_service import JobPersistenceService
from app.services.cache import cache_service
```

## 6. Frontend Integration

### 6.1 Components Using Agents
1. **RealtimeAnalysisProgress.svelte** - Shows agent execution progress
2. **AnalysisOverview.svelte** - Displays agent results
3. **InsightsList.svelte** - Shows insights from agents

### 6.2 WebSocket Integration
- Real-time updates via WebSocket at `/ws`
- Agent status updates published to channels

## 7. Current Architecture Flow

```
User Request
    ↓
API Endpoint
    ↓
Agent Orchestrator
    ↓
Individual Agents → Azure OpenAI
    ↓
Results Aggregation
    ↓
Response to User
```

## 8. Key Observations

### Strengths:
1. Modular agent design
2. Comprehensive monitoring
3. Async execution support
4. Result caching
5. Error handling

### Areas for Improvement:
1. No autonomous agent creation
2. Static workflow definitions
3. Limited agent collaboration
4. No learning/adaptation
5. Manual orchestration logic

## 9. Migration Considerations

### What Needs to Change:
1. Replace custom orchestration with Crew.ai
2. Convert agents to Crew.ai agent format
3. Implement Crew.ai tools and tasks
4. Update API endpoints to use Crew.ai
5. Migrate monitoring to Crew.ai patterns

### What Can Stay:
1. Database schema (with additions)
2. API endpoint structure
3. Frontend components
4. Azure OpenAI integration
5. Caching and persistence layers

## Next Steps
1. Install and configure Crew.ai
2. Create Crew.ai agent definitions
3. Implement Crew.ai tools for existing functionality
4. Update orchestration logic
5. Test and validate migration