# 🧹 Langfuse Integration: What to Remove from PRSNL

**Purpose:** Detailed guide on what integrations and code can be removed after adding Langfuse

---

## 📊 Summary: ~1,576 Lines of Code Can Be Removed!

After integrating Langfuse, you can remove significant custom monitoring code, simplifying maintenance and reducing complexity.

---

## 🗑️ Complete File Removals

### 1. **Agent Monitoring Service** (644 lines)
```bash
# Remove entirely
rm app/services/agent_monitoring_service.py
rm app/api/agent_monitoring_api.py
```
**Replaced by:** Langfuse's native CrewAI integration with automatic agent tracking

### 2. **Agent Monitoring Database** (332 lines)
```sql
-- Tables to DROP:
DROP TABLE IF EXISTS agent_performance_metrics CASCADE;
DROP TABLE IF EXISTS workflow_performance_metrics CASCADE;
DROP TABLE IF EXISTS performance_alerts CASCADE;
DROP TABLE IF EXISTS agent_synthesis_results CASCADE;

-- Remove all related views and functions
```
**Replaced by:** Langfuse's built-in trace storage and analytics

---

## ✂️ Code Sections to Remove

### 1. **AI Cost Tracking** (~200 lines)

**In `ai_router.py`:**
```python
# REMOVE these methods/attributes:
- self.usage_stats = defaultdict(lambda: {...})
- get_usage_report()
- Cost calculation logic in route_request()
```

**In `ai_router_production.py`:**
```python
# REMOVE:
- usage_stats tracking
- cost_per_1k_tokens calculations
- Token counting logic
```

### 2. **Custom AI Performance Monitoring** (~150 lines)

**In `performance_monitoring.py`:**
```python
# REMOVE:
@profile_ai_operation  # This decorator
def some_ai_function():
    pass

# Keep general performance monitoring for non-AI operations
```

**In `observability.py`:**
```python
# REMOVE:
- _track_ai_processing_time()
- AI-specific token metrics
- Custom AI spans

# KEEP:
- General OpenTelemetry setup
- Database performance tracking
- HTTP request tracking
```

### 3. **Manual Token Counting** (~50 lines)

**In various services:**
```python
# REMOVE all instances of:
token_count = len(encoding.encode(text))
total_tokens = prompt_tokens + completion_tokens
cost = (total_tokens / 1000) * cost_per_1k
```

---

## 🔄 Integration Replacements

### Before → After Examples

#### 1. **Agent Monitoring**
```python
# BEFORE (with custom monitoring)
from app.services.agent_monitoring_service import AgentMonitoringService

monitoring = AgentMonitoringService()
await monitoring.start_agent_task(agent_id, task_type)
# ... agent work ...
await monitoring.complete_agent_task(agent_id, success=True)

# AFTER (with Langfuse)
from langfuse.crewai import LangfuseCallbackHandler

crew = Crew(
    agents=[...],
    callbacks=[LangfuseCallbackHandler()]  # Automatic tracking!
)
```

#### 2. **Cost Tracking**
```python
# BEFORE
tokens = count_tokens(prompt) + count_tokens(response)
cost = calculate_cost(tokens, model)
self.usage_stats[provider]["total_tokens"] += tokens
self.usage_stats[provider]["total_cost"] += cost

# AFTER
# Langfuse tracks automatically - no code needed!
```

#### 3. **Performance Monitoring**
```python
# BEFORE
@profile_ai_operation("content_analysis")
async def analyze_content(content):
    start = time.time()
    result = await ai_service.analyze(content)
    metrics.record_ai_latency(time.time() - start)
    return result

# AFTER
from langfuse.decorators import observe

@observe()  # Automatic performance tracking!
async def analyze_content(content):
    return await ai_service.analyze(content)
```

---

## 📦 Dependencies to Review

While no Python packages can be completely removed (they're used for non-AI operations), you can:

1. **Simplify OpenTelemetry Configuration**
   - Remove AI-specific instrumentations
   - Keep general application monitoring

2. **Database Cleanup**
   - Drop unused monitoring tables
   - Remove monitoring-related indexes
   - Simplify database schema

---

## ⚡ Performance Benefits

After removing these integrations:

1. **Reduced Database Load**
   - No more agent_performance_metrics inserts
   - No more workflow tracking updates
   - Fewer database connections

2. **Simplified Codebase**
   - 1,576 fewer lines to maintain
   - Fewer moving parts
   - Clearer separation of concerns

3. **Better Performance**
   - Less overhead from custom monitoring
   - Langfuse's optimized SDK
   - Async, non-blocking operations

---

## 🎯 Migration Strategy

### Phase 1: Add Langfuse (Keep everything)
1. Install Langfuse SDK
2. Add decorators to AI operations
3. Verify data collection works
4. Run both systems in parallel for 1 week

### Phase 2: Gradual Removal
1. Stop writing to agent_performance_metrics
2. Remove cost tracking from ai_router
3. Remove custom monitoring decorators
4. Keep database tables for historical data

### Phase 3: Complete Cleanup
1. Drop monitoring database tables
2. Remove monitoring service files
3. Clean up imports and dependencies
4. Update documentation

### Phase 4: Optimization
1. Review remaining OpenTelemetry usage
2. Optimize for Langfuse-first approach
3. Set up Langfuse dashboards
4. Configure alerts in Langfuse

---

## ✅ What to Keep

- **OpenTelemetry** for general application monitoring (HTTP, database, etc.)
- **Sentry** for error tracking and general performance
- **Prometheus metrics** for infrastructure monitoring
- **WebSocket infrastructure** for real-time updates (non-agent)
- **Job persistence system** for general background tasks

---

## 🚀 End Result

**From:** Complex multi-layered monitoring with custom code
**To:** Streamlined Langfuse-powered AI observability

- **Fewer dependencies** to manage
- **Less code** to maintain
- **Better insights** into AI operations
- **Unified platform** for all LLM concerns
- **Professional tooling** instead of custom solutions