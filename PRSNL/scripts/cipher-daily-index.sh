#!/bin/bash

# Cipher Daily Indexing Script for PRSNL
# Captures daily development patterns, fixes, and insights

echo "📅 Daily Cipher Indexing for PRSNL"
echo "=================================="
echo "Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# Navigate to script directory
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

# Function to store with timestamp
store_daily() {
    local pattern="$1"
    "$SCRIPT_DIR/prsnl-cipher.sh" store "[$(date '+%Y-%m-%d')] $pattern"
}

echo "📊 1. Git Activity"
echo "-----------------"

# Get today's commits
echo "🔍 Indexing today's commits..."
cd ../
git log --since="1 day ago" --pretty=format:"%h %s" 2>/dev/null | head -10 | while read -r commit; do
    store_daily "GIT COMMIT: $commit"
done

# Get changed files
echo "📝 Indexing changed files..."
git diff --name-only HEAD~1 2>/dev/null | head -10 | while read -r file; do
    store_daily "CHANGED FILE: $file"
done

cd scripts/

echo ""
echo "🐛 2. Error Patterns"
echo "-------------------"

# Check for recent errors in logs (if logs exist)
if [ -d "../logs" ]; then
    echo "🔍 Scanning error logs..."
    grep -i "error\|exception\|failed" ../logs/*.log 2>/dev/null | tail -10 | while read -r error; do
        store_daily "ERROR FOUND: $error"
    done
fi

# Check for TODO/FIXME comments added today
echo "📌 Indexing new TODOs..."
git diff --since="1 day ago" | grep -E "^\+.*TODO|^\+.*FIXME" 2>/dev/null | head -5 | while read -r todo; do
    cleaned_todo=$(echo "$todo" | sed 's/^+//')
    store_daily "NEW TODO: $cleaned_todo"
done

echo ""
echo "🧩 3. Component Activity"
echo "-----------------------"

# Find recently modified components
echo "🔍 Indexing modified components..."
find ../frontend/src/lib/components -name "*.svelte" -mtime -1 2>/dev/null | head -10 | while read -r component; do
    comp_name=$(basename "$component")
    store_daily "MODIFIED COMPONENT: $comp_name"
done

# Check for new component imports
echo "📦 Checking new component usage..."
git diff --since="1 day ago" ../frontend/src/routes/ 2>/dev/null | grep -E "^\+.*import.*components" | head -5 | while read -r import; do
    cleaned_import=$(echo "$import" | sed 's/^+//')
    store_daily "NEW IMPORT: $cleaned_import"
done

echo ""
echo "⚙️ 4. Configuration Changes"
echo "--------------------------"

# Check for environment variable changes
echo "🔐 Checking env changes..."
if git diff --since="1 day ago" ../.env.example 2>/dev/null | grep -E "^\+[A-Z_]+=" ; then
    git diff --since="1 day ago" ../.env.example | grep -E "^\+[A-Z_]+=" | while read -r env_change; do
        cleaned_env=$(echo "$env_change" | sed 's/^+//')
        store_daily "ENV CHANGE: $cleaned_env"
    done
fi

# Check for package.json changes
echo "📦 Checking dependency changes..."
if git diff --since="1 day ago" ../frontend/package.json ../backend/requirements.txt 2>/dev/null | grep -E "^\+" ; then
    store_daily "DEPENDENCIES: Updated today - check package.json or requirements.txt"
fi

echo ""
echo "🚀 5. Performance Insights"
echo "-------------------------"

# Store build time if available
if [ -f "../.next/build-manifest.json" ] || [ -f "../frontend/.svelte-kit/build/manifest.json" ]; then
    BUILD_TIME=$(date -r "../frontend/.svelte-kit/build/manifest.json" 2>/dev/null || echo "N/A")
    store_daily "BUILD TIME: Last build at $BUILD_TIME"
fi

# Check for performance-related commits
git log --since="1 day ago" --grep="perf\|performance\|optimize\|speed" --pretty=format:"%s" 2>/dev/null | head -5 | while read -r perf_commit; do
    store_daily "PERF IMPROVEMENT: $perf_commit"
done

echo ""
echo "🎯 6. Daily Summary"
echo "------------------"

# Count activities
COMMITS=$(git log --since="1 day ago" --oneline 2>/dev/null | wc -l)
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null | wc -l)
MODIFIED_COMPONENTS=$(find ../frontend/src/lib/components -name "*.svelte" -mtime -1 2>/dev/null | wc -l)

store_daily "DAILY STATS: $COMMITS commits, $CHANGED_FILES files changed, $MODIFIED_COMPONENTS components modified"

echo "📊 Daily Statistics:"
echo "  • Commits: $COMMITS"
echo "  • Changed files: $CHANGED_FILES"
echo "  • Modified components: $MODIFIED_COMPONENTS"
echo ""

# Prompt for manual insights
echo "💭 Manual Daily Insights"
echo "-----------------------"
echo "Consider adding these manually:"
echo ""
echo "# What major problem did you solve?"
echo "./prsnl-cipher.sh store \"[$(date '+%Y-%m-%d')] SOLVED: [problem] by [solution]\""
echo ""
echo "# What pattern did you discover?"
echo "./prsnl-cipher.sh store \"[$(date '+%Y-%m-%d')] DISCOVERED: [pattern] in [context]\""
echo ""
echo "# What should you remember for tomorrow?"
echo "./prsnl-cipher.sh store \"[$(date '+%Y-%m-%d')] REMEMBER: [important note]\""
echo ""

# Create daily session file
SESSION_FILE="../.cipher-memories/$(date '+%Y-%m-%d')-session.md"
if [ ! -f "$SESSION_FILE" ]; then
    cat > "$SESSION_FILE" << EOF
# Daily Session: $(date '+%Y-%m-%d')

## 🎯 Goals
- [ ] 

## 📝 Completed
- 

## 🐛 Issues Encountered
- 

## 💡 Insights
- 

## 🔮 Tomorrow
- 
EOF
    echo "📝 Created daily session file: $SESSION_FILE"
    echo "   Edit this file to capture detailed daily notes."
fi

echo ""
echo "✅ Daily indexing complete!"
echo ""
echo "🔄 Run this at the end of each development day."
echo "📊 Review weekly with: ./prsnl-cipher.sh recall \"[$(date '+%Y-%m-%d')]\""