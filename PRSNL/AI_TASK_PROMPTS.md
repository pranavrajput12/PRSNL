# AI Task Prompts with Required Reading

## CRITICAL: Before ANY Implementation

### 1. MANDATORY Files to Read First
Every AI model MUST read these files before starting ANY work:

```bash
# Port and coordination rules
/PRSNL/MODEL_COORDINATION_RULES.md

# Current architecture and patterns
/PRSNL/ARCHITECTURE.md

# API documentation
/PRSNL/API_DOCUMENTATION.md

# Task tracking
/PRSNL/CONSOLIDATED_TASK_TRACKER.md
/PRSNL/MODEL_ACTIVITY_LOG.md
```

### 2. Feature-Specific Required Reading

#### For Frontend Work:
```bash
# Design system
/PRSNL/DESIGN_LANGUAGE.md

# Existing components
/PRSNL/frontend/src/lib/components/
/PRSNL/frontend/src/lib/api.ts
/PRSNL/frontend/src/lib/stores/
```

#### For Backend Work:
```bash
# Service patterns
/PRSNL/backend/app/services/ai_router.py
/PRSNL/backend/app/services/llm_processor.py
/PRSNL/backend/app/config.py

# API patterns
/PRSNL/backend/app/api/
```

## Task Template

### Task: [Feature Name]

**STEP 1: Read Required Files**
```bash
# Read coordination rules
cat /PRSNL/MODEL_COORDINATION_RULES.md

# Read architecture
cat /PRSNL/ARCHITECTURE.md

# Read relevant service files
cat /PRSNL/backend/app/services/ai_router.py
cat /PRSNL/backend/app/config.py
```

**STEP 2: Check Port Availability**
```bash
# MUST use assigned port 3002 for frontend
lsof -i :3002

# If occupied, STOP and coordinate
```

**STEP 3: Implementation Requirements**
- Use existing patterns (AI router for AI tasks)
- Follow established architecture
- Maintain assigned ports
- Update MODEL_ACTIVITY_LOG.md

## Specific Task Prompts

### For Windsurf - AI Insights Dashboard

**CRITICAL SETUP:**
1. READ these files FIRST:
   - `/PRSNL/MODEL_COORDINATION_RULES.md` - Your port is 3002, NOT 3004
   - `/PRSNL/DESIGN_LANGUAGE.md` - Follow the design system
   - `/PRSNL/frontend/src/lib/api.ts` - Use existing API patterns
   - `/PRSNL/API_DOCUMENTATION.md` - Check available endpoints

2. Frontend MUST run on port 3002:
   ```bash
   npm run dev -- --port 3002
   ```

**Implementation Requirements:**
- Create route: `/PRSNL/frontend/src/routes/insights/+page.svelte`
- Use existing component patterns from `/lib/components/`
- Follow Manchester United red theme (#dc143c)
- Implement visualizations for:
  - Content trends over time
  - Top tags and topics
  - Knowledge graph connections
  - AI usage statistics

### For Gemini - Remaining Features

**CRITICAL SETUP:**
1. READ these files FIRST:
   - `/PRSNL/backend/app/config.py` - We use AZURE OpenAI, not standard OpenAI
   - `/PRSNL/backend/app/services/ai_router.py` - Use this for ALL AI tasks
   - `/PRSNL/backend/app/services/embedding_service.py` - Already fixed to use Azure
   - `/PRSNL/MODEL_COORDINATION_RULES.md` - Follow the rules

**Remaining Tasks:**
1. Create analytics endpoints for insights dashboard:
   ```python
   # /PRSNL/backend/app/api/analytics.py
   - GET /api/analytics/trends
   - GET /api/analytics/topics
   - GET /api/analytics/usage
   ```

2. Implement caching for embeddings:
   - Use Redis for embedding cache
   - Cache similarity calculations

## Enforcement Rules

1. **Port Violations**: Any model using wrong ports will have their work rejected
2. **Pattern Violations**: Not using established patterns (like AI router) requires rework
3. **Documentation**: All changes MUST be logged in MODEL_ACTIVITY_LOG.md

## Example of Proper Implementation Flow

```bash
# 1. Start by reading
cat /PRSNL/MODEL_COORDINATION_RULES.md
cat /PRSNL/ARCHITECTURE.md
grep -n "azure" /PRSNL/backend/app/config.py

# 2. Check what exists
ls /PRSNL/backend/app/services/
cat /PRSNL/backend/app/services/ai_router.py

# 3. Use existing patterns
# DON'T create new OpenAI client
# DO use ai_router.execute_task()

# 4. Maintain ports
# Frontend ALWAYS on 3002
# Backend ALWAYS on 8000

# 5. Update tracking
echo "Working on feature X" >> /PRSNL/MODEL_ACTIVITY_LOG.md
```