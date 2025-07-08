# 🧠 GEMINI - Simple Backend Tasks

## 📚 REQUIRED READING BEFORE ANY TASK
Always review these files before starting work:

### Documentation to Read First:
1. `/PRSNL/PROJECT_STATUS.md` - Current project state and context
2. `/CURRENT_STATE.md` - Real-time project status
3. `/SESSION_CONTINUITY.md` - Last session context
4. `/PRSNL/MODEL_COORDINATION_RULES.md` - **CRITICAL: PORT 8000 ONLY!**
5. `/PRSNL/API_DOCUMENTATION.md` - API structure and patterns
6. `/PRSNL/DATABASE_SCHEMA.md` - Database field mappings

### Files to Update After Each Task:
1. `/PRSNL/CONSOLIDATED_TASK_TRACKER.md` - Mark task complete
2. `/PRSNL/MODEL_ACTIVITY_LOG.md` - Log your changes
3. `/PRSNL/PROJECT_STATUS.md` - Update progress section
4. `/CURRENT_STATE.md` - Update current status
5. `/SESSION_CONTINUITY.md` - Update session context

---

## ⚠️ TASK REASSIGNMENT (2025-01-08)
Complex backend tasks have been reassigned to Claude. Gemini should focus on simple, time-consuming backend tasks.

## 🎯 NEW SIMPLE TASKS

### Task GEMINI-SIMPLE-001: Create Test Data Scripts
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 2 hours

**Task**: Create comprehensive test data population scripts
- Create script to add 50+ diverse test items
- Include all item types: videos, articles, tweets, GitHub repos, PDFs
- Add realistic metadata, tags, and summaries
- Create test users and activity patterns

**Files to Create:**
```
/PRSNL/backend/scripts/populate_test_data.py
/PRSNL/backend/scripts/generate_activity_data.py
```

---

### Task GEMINI-SIMPLE-002: API Response Time Logging
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 1 hour

**Task**: Add response time logging to all API endpoints
- Log endpoint, method, response time, status code
- Write logs to structured format
- Create daily summary reports
- No complex logic, just logging

**Files to Update:**
```
/PRSNL/backend/app/middleware/logging.py
/PRSNL/backend/app/utils/logger.py
```

---

### Task GEMINI-SIMPLE-003: Database Backup Scripts
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 1.5 hours

**Task**: Create automated database backup scripts
- Daily backup script using pg_dump
- Compress and timestamp backups
- Keep last 7 days of backups
- Simple bash/Python scripts

**Files to Create:**
```
/PRSNL/backend/scripts/backup_database.sh
/PRSNL/backend/scripts/restore_database.sh
/PRSNL/backend/scripts/cleanup_old_backups.py
```

---

### Task GEMINI-SIMPLE-004: Write Unit Tests for Utilities
**Priority**: HIGH
**Status**: TODO
**Estimated Time**: 3 hours

**Task**: Write tests for utility functions
- Test date formatting functions
- Test URL validation utilities
- Test file size formatting
- Test string truncation helpers
- Aim for 100% coverage of utils

**Files to Create:**
```
/PRSNL/backend/tests/test_utils_date.py
/PRSNL/backend/tests/test_utils_url.py
/PRSNL/backend/tests/test_utils_format.py
```

---

### Task GEMINI-SIMPLE-005: Error Log Analysis Script
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 2 hours

**Task**: Create script to analyze error logs
- Parse application error logs
- Group errors by type and frequency
- Generate daily error report
- Send summary to Slack/Discord webhook

**Files to Create:**
```
/PRSNL/backend/scripts/analyze_errors.py
/PRSNL/backend/scripts/error_report_template.md
```

---

### Task GEMINI-SIMPLE-006: API Documentation Examples
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 2 hours

**Task**: Add example requests/responses to API docs
- Create example JSON for each endpoint
- Add curl command examples
- Include common error responses
- Update OpenAPI schema descriptions

**Files to Update:**
```
/PRSNL/backend/app/api/examples/
/PRSNL/API_DOCUMENTATION.md
```

---

### Task GEMINI-SIMPLE-007: Health Check Endpoints
**Priority**: HIGH
**Status**: TODO
**Estimated Time**: 1 hour

**Task**: Implement simple health check endpoints
- Database connectivity check
- Redis connectivity check
- Disk space check
- Memory usage check
- Return simple JSON status

**Files to Create:**
```
/PRSNL/backend/app/api/health.py
/PRSNL/backend/app/utils/system_checks.py
```

---

### Task GEMINI-SIMPLE-008: Metrics Collection Script
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 2 hours

**Task**: Create metrics collection scripts
- Count items by type and status
- Calculate storage usage
- Track API usage by endpoint
- Generate CSV reports

**Files to Create:**
```
/PRSNL/backend/scripts/collect_metrics.py
/PRSNL/backend/scripts/generate_reports.py
```

---

## 📋 Guidelines for Simple Tasks

1. **DO NOT** modify core business logic
2. **DO NOT** change API contracts or database schema
3. **DO NOT** implement complex algorithms
4. **DO** focus on scripts, tests, and utilities
5. **DO** write clear, well-documented code
6. **DO** test your scripts before marking complete

## 🚫 Tasks NOT for Gemini

These are handled by Claude:
- AI service implementations
- Complex API endpoints
- Database schema changes
- WebSocket implementations
- Authentication/authorization
- Performance optimization of core features