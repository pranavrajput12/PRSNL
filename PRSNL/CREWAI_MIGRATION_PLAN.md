# Crew.ai Migration Plan for PRSNL

## Executive Summary
This document outlines the migration strategy from the current custom agent system to Crew.ai, an autonomous agent framework that enables dynamic agent creation and workflow management.

## 1. Why Crew.ai?

### Current Limitations:
- Static agent definitions
- Manual orchestration logic
- No autonomous agent creation
- Limited inter-agent collaboration
- No learning/adaptation capabilities

### Crew.ai Benefits:
- **Autonomous agent creation** - Agents can spawn sub-agents
- **Dynamic workflows** - Adapt based on task requirements
- **Built-in collaboration** - Agents work together naturally
- **Memory and learning** - Agents improve over time
- **Tool integration** - Easy to add new capabilities
- **Production-ready** - Battle-tested framework

## 2. Crew.ai Architecture Overview

### Core Components:
```python
# Crew.ai structure
from crewai import Agent, Task, Crew, Process

# 1. Agents - Autonomous entities with roles
agent = Agent(
    role='Researcher',
    goal='Find accurate information',
    backstory='Expert researcher with 10 years experience',
    tools=[search_tool, scrape_tool],
    llm=azure_openai_model
)

# 2. Tasks - What agents need to accomplish
task = Task(
    description='Research the latest AI trends',
    agent=agent,
    expected_output='Comprehensive report on AI trends'
)

# 3. Crews - Teams of agents working together
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential  # or Process.hierarchical
)

# 4. Execution
result = crew.kickoff()
```

## 3. Migration Strategy

### Phase 1: Setup and Infrastructure (Week 1)
1. **Install Crew.ai**
   ```bash
   pip install crewai crewai-tools
   ```

2. **Create Crew.ai configuration**
   - Set up Azure OpenAI integration
   - Configure memory backends
   - Set up tool definitions

3. **Create base agent factory**
   - Agent creation patterns
   - Role definitions
   - Tool assignments

### Phase 2: Agent Migration (Week 2-3)

#### 3.1 Map Current Agents to Crew.ai Agents

**Crawl.ai Agents → Crew.ai Agents:**

1. **KnowledgeCuratorAgent → Knowledge Curator Agent**
   ```python
   knowledge_curator = Agent(
       role="Knowledge Curator",
       goal="Curate and organize knowledge from diverse sources",
       backstory="Expert in knowledge management and information architecture",
       tools=[web_scraper, content_analyzer, knowledge_graph_tool],
       llm=azure_openai,
       memory=True
   )
   ```

2. **ResearchSynthesisAgent → Research Synthesizer Agent**
   ```python
   research_synthesizer = Agent(
       role="Research Synthesizer",
       goal="Synthesize research from multiple sources into coherent insights",
       backstory="PhD in research methodology with expertise in meta-analysis",
       tools=[document_analyzer, citation_tool, summary_generator],
       llm=azure_openai,
       memory=True
   )
   ```

3. **CodeMirror Agents → Code Intelligence Crew**
   ```python
   code_analyst = Agent(
       role="Code Analyst",
       goal="Analyze codebases for patterns, quality, and insights",
       backstory="Senior software architect with 15 years experience",
       tools=[ast_parser, pattern_detector, security_scanner],
       llm=azure_openai,
       memory=True
   )
   ```

#### 3.2 Create Crew.ai Tools

Convert existing functionality into Crew.ai tools:

```python
# Example: Web Scraping Tool
from crewai_tools import BaseTool

class WebScrapingTool(BaseTool):
    name: str = "Web Scraper"
    description: str = "Scrapes and extracts content from web pages"
    
    def _run(self, url: str) -> str:
        # Use existing CrawlAIService
        result = await crawl_service.crawl(url)
        return result.content

# Example: Code Analysis Tool
class CodeAnalysisTool(BaseTool):
    name: str = "Code Analyzer"
    description: str = "Analyzes code for patterns and quality"
    
    def _run(self, repo_id: str) -> dict:
        # Use existing CodeMirror service
        return await codemirror_service.analyze_repository(repo_id)
```

### Phase 3: Workflow Migration (Week 3-4)

#### Convert Orchestrator to Crews

1. **Knowledge Curation Crew**
   ```python
   class KnowledgeCurationCrew:
       def __init__(self):
           self.researcher = Agent(...)
           self.curator = Agent(...)
           self.organizer = Agent(...)
           
       def create_crew(self, topic: str):
           research_task = Task(
               description=f"Research {topic} from multiple sources",
               agent=self.researcher
           )
           
           curation_task = Task(
               description="Curate and filter the research findings",
               agent=self.curator
           )
           
           organization_task = Task(
               description="Organize knowledge into structured format",
               agent=self.organizer
           )
           
           return Crew(
               agents=[self.researcher, self.curator, self.organizer],
               tasks=[research_task, curation_task, organization_task],
               process=Process.sequential
           )
   ```

2. **Code Intelligence Crew**
   ```python
   class CodeIntelligenceCrew:
       def __init__(self):
           self.analyzer = Agent(...)
           self.pattern_detector = Agent(...)
           self.insight_generator = Agent(...)
           
       def create_crew(self, repo_id: str):
           # Dynamic crew creation based on repository
           return Crew(
               agents=self._select_agents_for_repo(repo_id),
               tasks=self._create_tasks_for_repo(repo_id),
               process=Process.hierarchical
           )
   ```

### Phase 4: API Integration (Week 4)

#### Update API Endpoints

1. **Maintain existing API structure**
   ```python
   @router.post("/workflow")
   async def execute_workflow(request: WorkflowRequest):
       # Create appropriate crew
       crew = crew_factory.create_crew(
           workflow_type=request.workflow_type,
           params=request.params
       )
       
       # Execute crew
       result = await crew.kickoff_async()
       
       # Store in existing job persistence
       await job_service.create_job(...)
       
       return {"job_id": job_id, "status": "processing"}
   ```

2. **Add new autonomous endpoints**
   ```python
   @router.post("/autonomous/goal")
   async def achieve_goal(goal: str):
       # Let Crew.ai figure out what agents and tasks are needed
       autonomous_crew = AutonomousCrew(goal=goal)
       result = await autonomous_crew.execute()
       return result
   ```

### Phase 5: Testing and Validation (Week 5)

1. **Parallel running**
   - Run both systems side-by-side
   - Compare results
   - Validate output quality

2. **Performance testing**
   - Measure execution times
   - Monitor resource usage
   - Test concurrent crews

3. **Integration testing**
   - Test all API endpoints
   - Verify database compatibility
   - Test frontend components

### Phase 6: Deployment (Week 6)

1. **Gradual rollout**
   - Feature flag for Crew.ai
   - A/B testing
   - Monitor metrics

2. **Migration completion**
   - Deprecate old system
   - Update documentation
   - Training for team

## 4. Implementation Details

### 4.1 Directory Structure
```
backend/
├── app/
│   ├── agents/              # New Crew.ai agents
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Base agent class
│   │   ├── knowledge/       # Knowledge agents
│   │   ├── code/           # Code analysis agents
│   │   ├── media/          # Media processing agents
│   │   └── conversation/   # Conversation agents
│   ├── crews/              # Crew definitions
│   │   ├── __init__.py
│   │   ├── base_crew.py
│   │   ├── knowledge_crew.py
│   │   ├── code_crew.py
│   │   └── autonomous_crew.py
│   ├── tools/              # Crew.ai tools
│   │   ├── __init__.py
│   │   ├── web_tools.py
│   │   ├── code_tools.py
│   │   ├── media_tools.py
│   │   └── ai_tools.py
│   └── services/
│       ├── crew_service.py  # Main Crew.ai service
│       └── agent_factory.py # Agent creation factory
```

### 4.2 Database Updates

Add tables for Crew.ai specific data:

```sql
-- Crew executions
CREATE TABLE crew_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id VARCHAR(255) NOT NULL,
    crew_type VARCHAR(100) NOT NULL,
    goal TEXT,
    agents JSONB,  -- Dynamic agent list
    tasks JSONB,   -- Dynamic task list
    status VARCHAR(50),
    result JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- Agent memory (for persistent memory)
CREATE TABLE agent_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_role VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50),  -- short_term, long_term, episodic
    content JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 1
);

-- Create indexes
CREATE INDEX idx_crew_executions_status ON crew_executions(status);
CREATE INDEX idx_agent_memory_role ON agent_memory(agent_role);
CREATE INDEX idx_agent_memory_embedding ON agent_memory USING ivfflat (embedding vector_cosine_ops);
```

### 4.3 Configuration

Create Crew.ai configuration file:

```python
# backend/app/config/crewai_config.py
from crewai import Agent
from app.config import settings

class CrewAIConfig:
    # LLM Configuration
    LLM_CONFIG = {
        "model": settings.AZURE_OPENAI_DEPLOYMENT,
        "api_key": settings.AZURE_OPENAI_API_KEY,
        "api_base": settings.AZURE_OPENAI_ENDPOINT,
        "api_version": settings.AZURE_OPENAI_API_VERSION,
        "api_type": "azure"
    }
    
    # Memory Configuration
    MEMORY_CONFIG = {
        "backend": "postgresql",
        "connection": settings.DATABASE_URL,
        "embedding_model": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    }
    
    # Agent Defaults
    DEFAULT_AGENT_CONFIG = {
        "verbose": True,
        "memory": True,
        "max_iter": 5,
        "max_execution_time": 300  # 5 minutes
    }
    
    # Crew Defaults
    DEFAULT_CREW_CONFIG = {
        "verbose": True,
        "memory": True,
        "cache": True,
        "max_rpm": 10  # Rate limiting
    }
```

## 5. Risk Mitigation

### 5.1 Risks and Mitigations

1. **Performance degradation**
   - Mitigation: Extensive performance testing
   - Fallback: Feature flag to revert

2. **API compatibility**
   - Mitigation: Maintain existing API structure
   - Gradual migration of endpoints

3. **Learning curve**
   - Mitigation: Comprehensive documentation
   - Team training sessions

4. **Cost increase**
   - Mitigation: Monitor token usage
   - Implement caching strategies

### 5.2 Rollback Plan

1. Feature flags for easy rollback
2. Keep old system code for 3 months
3. Database migrations are additive only
4. API versioning for compatibility

## 6. Success Metrics

1. **Performance**
   - Response time ≤ current system
   - Token usage within 20% of current

2. **Quality**
   - Output quality scores ≥ current
   - User satisfaction maintained

3. **Reliability**
   - 99.9% uptime
   - Error rate < 1%

4. **Scalability**
   - Support 10x current load
   - Concurrent crew execution

## 7. Timeline

- **Week 1**: Setup and infrastructure
- **Week 2-3**: Agent migration
- **Week 3-4**: Workflow migration
- **Week 4**: API integration
- **Week 5**: Testing and validation
- **Week 6**: Deployment

Total: 6 weeks for complete migration

## 8. Next Steps

1. Review and approve plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews
5. Adjust timeline as needed