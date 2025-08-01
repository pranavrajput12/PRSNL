# Cipher Pattern Templates - Copy & Use

Quick templates for storing high-value patterns as you work.

## 🐛 Bug Solution Pattern Template
```bash
cipher "BUG PATTERN: [ERROR MESSAGE] → [SOLUTION]"

# Example:
cipher "BUG PATTERN: TypeError: Cannot read property 'map' of undefined → Add null check: items?.map() || []"
```

## 🧩 Component Reusability Template
```bash
cipher "COMPONENT PATTERN: [USE CASE] → Use existing [COMPONENT_NAME] at [PATH]"

# Example:
cipher "COMPONENT PATTERN: User avatar display → Use existing Avatar.svelte at lib/components/Avatar.svelte"
```

## ⚙️ Configuration Success Template
```bash
cipher "CONFIG SUCCESS: [SERVICE] → [WORKING CONFIGURATION]"

# Example:
cipher "CONFIG SUCCESS: Playwright testing → Set CI=true, use webkit for Safari testing"
```

## 🏃 Sprint Achievement Template
```bash
cipher "SPRINT ACHIEVEMENT: [DATE] → [WHAT WAS COMPLETED]"
cipher "SPRINT LEARNING: [DATE] → [KEY INSIGHT]"

# Example:
cipher "SPRINT ACHIEVEMENT: 2025-08-02 → Implemented pattern storage system, 10x debugging speed"
```

## 📡 API Pattern Template
```bash
cipher "API PATTERN: [ENDPOINT TYPE] → [IMPLEMENTATION PATTERN]"

# Example:
cipher "API PATTERN: List endpoints → Always include total_count, has_more, cursor for pagination"
```

## 📊 Quick Pattern Storage Commands

### After Fixing a Bug
```bash
# Store immediately after fix
cipher "BUG PATTERN: $ERROR_MSG → $FIX_APPLIED"
```

### When Finding Existing Component
```bash
# Prevent future duplication
cipher "COMPONENT PATTERN: Needed $FEATURE, found at $LOCATION"
```

### After Successful Config
```bash
# Save working configuration
cipher "CONFIG SUCCESS: Got $SERVICE working with $CONFIG"
```

## 🎯 Pattern Categories for PRSNL

### Database Patterns
```bash
cipher "DB PATTERN: [OPERATION] → [QUERY PATTERN]"
# Example: "DB PATTERN: Bulk insert → Use INSERT ... ON CONFLICT for upserts"
```

### Frontend State Patterns
```bash
cipher "STATE PATTERN: [SCENARIO] → [SOLUTION]"
# Example: "STATE PATTERN: Global user data → Use auth store with persistence"
```

### Testing Patterns
```bash
cipher "TEST PATTERN: [TEST TYPE] → [APPROACH]"
# Example: "TEST PATTERN: API mocking → Use MSW for consistent mock responses"
```

### Performance Patterns
```bash
cipher "PERF PATTERN: [ISSUE] → [OPTIMIZATION]"
# Example: "PERF PATTERN: Slow list render → Add virtual scrolling for 100+ items"
```

## 💡 Pro Tips

### 1. Be Specific
❌ "Fixed the bug"
✅ "BUG PATTERN: Vite HMR not working → Add server.hmr.port to vite.config"

### 2. Include Context
❌ "Use Modal component"
✅ "COMPONENT PATTERN: Confirmation dialogs → Use Modal.svelte with confirmAction prop"

### 3. Add Keywords
Include error messages, service names, and file paths for better recall.

### 4. Update Patterns
When you find a better solution:
```bash
cipher "PATTERN UPDATE: [OLD PATTERN] → NOW USE [NEW PATTERN]"
```

## 📈 ROI Tracking

Track your pattern usage:
```bash
# See most recalled patterns
cipher recall "PATTERN" | grep -c "BUG PATTERN"  # Count bug fixes
cipher recall "COMPONENT PATTERN" | wc -l        # Count reuse wins
```

## 🔄 Daily Habit

End of day pattern capture:
```bash
# What did I fix today?
cipher "BUG PATTERN: [Today's fix]"

# What component did I reuse?
cipher "COMPONENT PATTERN: [Reuse win]"

# What config worked?
cipher "CONFIG SUCCESS: [Working setup]"
```

Remember: Every pattern stored saves future debugging time!