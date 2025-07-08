# 🧠 GEMINI - Standard Operating Procedure

## 📋 Your Role
You handle **SIMPLE BACKEND TASKS ONLY**. No core logic changes, no API design, no complex features.

## ✅ Task Checklist

### 1. Start of Session
```bash
# Read these files in order:
1. /PRSNL/CENTRALIZED_TASK_MANAGEMENT.md
2. /PRSNL/PROJECT_STATUS.md
3. /PRSNL/GEMINI_TASKS.md (your task list)
```

### 2. Select a Task
- Pick a task marked **TODO** from GEMINI_TASKS.md
- Tasks are already simple and well-defined
- Focus on scripts, tests, and documentation

### 3. Before Working
```bash
# Check if anyone is working on related files
grep "LOCKED" /PRSNL/MODEL_ACTIVITY_LOG.md

# Ensure backend is accessible
curl http://localhost:8000/health
```

### 4. Update Task Status
```markdown
# In CONSOLIDATED_TASK_TRACKER.md, add:
### Task GEMINI-2025-01-08-001: Create Test Data Scripts
**Status**: IN PROGRESS
**Started**: 2025-01-08 15:00
**Assigned**: Gemini
```

### 5. Do the Work
- Follow the task specifications exactly
- Don't modify core application logic
- Add comments to scripts
- Test your scripts work

### 6. Complete the Task
```markdown
# In CONSOLIDATED_TASK_TRACKER.md:
**Status**: COMPLETED
**Completed**: 2025-01-08 16:00

# In GEMINI_TASKS.md:
Move task from TODO to COMPLETED section
```

## 🚫 What NOT to Do

### Never Touch
- Core API endpoints
- Database schema
- Business logic
- Authentication/authorization
- AI service implementations

### Never Add
- New API endpoints
- Database migrations
- Complex algorithms
- External dependencies
- Breaking changes

## ✅ What You CAN Do

### Scripts
- Test data population
- Database backup scripts
- Log analysis scripts
- Metrics collection
- Report generation

### Testing
- Unit tests for utilities
- Test data generators
- Performance benchmarks
- Load testing scripts
- Documentation tests

### Documentation
- API examples
- Code comments
- README updates
- Error documentation
- Configuration guides

## 📝 Example Tasks

### Good Task Example
```markdown
Task: Create script to populate test data
- Generate 50 diverse items
- Include all item types
- Add realistic metadata
- Save to database via API
```

### Task You Should Skip
```markdown
Task: Optimize search algorithm
- Requires algorithm knowledge (skip)
- Core logic change (skip)
- Complex implementation (skip)
```

## 🛠️ Common Patterns

### Script Structure
```python
#!/usr/bin/env python3
"""
Script: populate_test_data.py
Purpose: Add test data to PRSNL database
Author: Gemini
Date: 2025-01-08
"""

import sys
import json
import httpx
from datetime import datetime

API_URL = "http://localhost:8000/api"

def main():
    """Main script logic."""
    try:
        # Your code here
        print("✅ Script completed successfully")
    except Exception as e:
        print(f"❌ Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Test Structure
```python
import pytest
from app.utils.formatters import format_date

def test_format_date():
    """Test date formatting function."""
    # Test with datetime object
    date = datetime(2025, 1, 8, 15, 30)
    assert format_date(date) == "Jan 8, 2025"
    
    # Test with string
    assert format_date("2025-01-08") == "Jan 8, 2025"
    
    # Test with None
    assert format_date(None) == ""
```

## 🧪 Testing Your Work

### Script Testing
```bash
# Make script executable
chmod +x script_name.py

# Run with test flag
./script_name.py --test

# Check output
./script_name.py > output.log 2>&1
```

### Unit Test Running
```bash
# Run specific test
pytest tests/test_utils.py::test_format_date -v

# Run all new tests
pytest tests/test_new_file.py -v

# Check coverage
pytest --cov=app.utils tests/test_utils.py
```

## 📊 Output Standards

### Logging
```python
# Use structured logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting data population")
logger.error(f"Failed to create item: {error}")
```

### Reports
```python
# Generate readable reports
report = {
    "timestamp": datetime.now().isoformat(),
    "total_items": 50,
    "successful": 48,
    "failed": 2,
    "duration_seconds": 12.5
}

with open("report.json", "w") as f:
    json.dump(report, f, indent=2)
```

## 📞 When to Ask for Help

### Ask Claude if
- Task affects core functionality
- Requires architectural decisions
- Needs complex logic
- Might break existing features

### Ask User if
- Requirements unclear
- Need access credentials
- Priority questions

## 🏁 End of Session

### Final Steps
1. Ensure all scripts are documented
2. Verify tests pass
3. Update task tracker
4. Clean up test data

### Handoff Notes
```markdown
## Gemini Session Summary - [Date]
**Completed**:
- Test data script (GEMINI-001)
- Unit tests for utils (GEMINI-002)

**Notes**:
- Added 50 test items via API
- All utility functions now have tests
- Coverage increased to 85%
```

Remember: Keep it simple, make it reliable, document everything!