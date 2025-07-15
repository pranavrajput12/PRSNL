# Crew.ai Migration Quick Start Guide

## Installation

```bash
# Add to requirements.txt
crewai==0.30.11
crewai-tools==0.4.26
```

## Current → Crew.ai Mapping

### 1. Agent Conversion Example

**Current (Crawl.ai):**
```python
class KnowledgeCuratorAgent:
    async def curate_knowledge(self, content, context):
        prompt = "Curate this knowledge..."
        response = await unified_ai_service.complete(prompt)
        return response
```

**Crew.ai:**
```python
from crewai import Agent

knowledge_curator = Agent(
    role="Knowledge Curator",
    goal="Curate and organize knowledge from diverse sources",
    backstory="Expert in knowledge management with 10 years experience",
    tools=[web_scraper_tool, content_analyzer_tool],
    llm=azure_openai_model,
    memory=True,
    verbose=True
)
```

### 2. Orchestrator → Crew Conversion

**Current:**
```python
orchestrator = CrawlAIOrchestrator()
result = await orchestrator.execute_workflow("research", params)
```

**Crew.ai:**
```python
from crewai import Crew, Task, Process

# Create tasks
research_task = Task(
    description="Research the topic thoroughly",
    agent=researcher_agent,
    expected_output="Comprehensive research report"
)

# Create crew
crew = Crew(
    agents=[researcher_agent, analyst_agent],
    tasks=[research_task, analysis_task],
    process=Process.sequential
)

# Execute
result = crew.kickoff()
```

### 3. Tool Creation Pattern

```python
from crewai_tools import BaseTool

class PRSNLWebScraperTool(BaseTool):
    name: str = "PRSNL Web Scraper"
    description: str = "Scrapes web content using existing PRSNL crawler"
    
    def _run(self, url: str) -> str:
        # Reuse existing service
        crawl_service = CrawlAIService()
        result = crawl_service.crawl(url)
        return result.content
```

### 4. API Endpoint Pattern

```python
@router.post("/api/crew/execute")
async def execute_crew(request: CrewRequest):
    # 1. Create crew based on request
    crew = crew_factory.create_crew(request.crew_type, request.params)
    
    # 2. Execute asynchronously
    job_id = str(uuid4())
    background_tasks.add_task(run_crew_async, crew, job_id)
    
    # 3. Return job ID (same pattern as current)
    return {"job_id": job_id, "status": "processing"}
```

## Key Differences

### Memory
- **Current**: Manual state management
- **Crew.ai**: Built-in memory (short-term, long-term, episodic)

### Agent Creation
- **Current**: Static class definitions
- **Crew.ai**: Dynamic agent instantiation with roles

### Workflows
- **Current**: Hardcoded orchestration logic
- **Crew.ai**: Declarative task and crew definitions

### Collaboration
- **Current**: Explicit agent coordination
- **Crew.ai**: Automatic agent collaboration

## Migration Checklist

- [ ] Install Crew.ai packages
- [ ] Set up Azure OpenAI with Crew.ai
- [ ] Create base agent factory
- [ ] Convert first agent (KnowledgeCurator)
- [ ] Create first tool (WebScraper)
- [ ] Create first crew (Research)
- [ ] Test end-to-end flow
- [ ] Update API endpoint
- [ ] Test with frontend
- [ ] Monitor performance

## Common Patterns

### 1. Autonomous Goal Achievement
```python
# User provides high-level goal
goal = "Analyze my repository and suggest improvements"

# Crew.ai figures out what agents and tasks are needed
autonomous_crew = AutonomousCrew(goal=goal)
result = autonomous_crew.execute()
```

### 2. Hierarchical Crews
```python
crew = Crew(
    agents=[manager, researcher, analyst, writer],
    tasks=[...],
    process=Process.hierarchical,  # Manager delegates
    manager_llm=azure_openai_model
)
```

### 3. Custom Agent Behaviors
```python
agent = Agent(
    role="Code Reviewer",
    goal="Ensure code quality",
    backstory="...",
    tools=[...],
    llm=azure_openai_model,
    max_iter=3,  # Limit iterations
    max_execution_time=300,  # 5 min timeout
    callbacks={
        "on_start": lambda: logger.info("Starting review"),
        "on_complete": lambda: logger.info("Review complete")
    }
)
```

## Testing Strategy

1. **Unit Tests**: Test individual agents and tools
2. **Integration Tests**: Test crews end-to-end
3. **Comparison Tests**: Run old vs new system
4. **Load Tests**: Test concurrent crew execution

## Monitoring

```python
# Add to crew execution
crew = Crew(
    agents=[...],
    tasks=[...],
    callbacks={
        "on_task_complete": log_task_completion,
        "on_crew_complete": log_crew_metrics
    }
)
```

## Resources

- [Crew.ai Docs](https://docs.crewai.com)
- [Crew.ai Examples](https://github.com/joaomdmoura/crewAI-examples)
- [Azure OpenAI + Crew.ai](https://docs.crewai.com/how-to/LLM-Connections/)
- Internal: `AGENT_SYSTEM_ANALYSIS.md`
- Internal: `CREWAI_MIGRATION_PLAN.md`