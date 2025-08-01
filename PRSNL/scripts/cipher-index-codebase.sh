#!/bin/bash

# Cipher Codebase Pattern Indexing Script for PRSNL
# Indexes code patterns, services, and implementations

echo "💻 Indexing PRSNL Codebase Patterns in Cipher..."
echo "=============================================="

# Navigate to script directory
cd "$(dirname "$0")"

# Function to index code patterns
index_patterns() {
    local path="$1"
    local pattern_type="$2"
    local description="$3"
    
    echo "🔍 Indexing $description in $path"
}

echo ""
echo "🐍 1. Backend Patterns (FastAPI)"
echo "--------------------------------"

# Index FastAPI route patterns
echo "📡 Indexing API routes..."
grep -r --include="*.py" "router\." ../backend/app/api/ 2>/dev/null | head -10 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    route=$(echo "$line" | grep -oE '@router\.[a-z]+\("[^"]+"\)' | head -1)
    if [ ! -z "$route" ]; then
        ./prsnl-cipher.sh store "FASTAPI ROUTE: $file → $route"
    fi
done

# Index service patterns
echo "🔧 Indexing service patterns..."
find ../backend/app/services -name "*.py" -type f 2>/dev/null | head -10 | while read -r file; do
    service_name=$(basename "$file" .py)
    # Look for class definitions
    grep -E "^class [A-Z]" "$file" 2>/dev/null | head -3 | while read -r class_def; do
        ./prsnl-cipher.sh store "SERVICE PATTERN: $service_name → $class_def"
    done
done

# Index database models
echo "📊 Indexing database models..."
grep -r --include="*.py" "class.*Base" ../backend/app/models/ 2>/dev/null | head -10 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    model=$(echo "$line" | grep -oE 'class [A-Za-z]+' | head -1)
    if [ ! -z "$model" ]; then
        ./prsnl-cipher.sh store "DATABASE MODEL: $file → $model"
    fi
done

# Index Pydantic schemas
echo "📋 Indexing Pydantic schemas..."
grep -r --include="*.py" "BaseModel" ../backend/app/models/schemas.py 2>/dev/null | head -10 | while read -r line; do
    schema=$(echo "$line" | grep -oE 'class [A-Za-z]+' | head -1)
    if [ ! -z "$schema" ]; then
        ./prsnl-cipher.sh store "PYDANTIC SCHEMA: $schema for API validation"
    fi
done

echo ""
echo "⚛️ 2. Frontend Patterns (SvelteKit)"
echo "-----------------------------------"

# Index Svelte stores
echo "🗃️ Indexing Svelte stores..."
find ../frontend/src/lib/stores -name "*.ts" -type f 2>/dev/null | while read -r file; do
    store_name=$(basename "$file" .ts)
    # Look for writable/readable stores
    grep -E "writable|readable|derived" "$file" 2>/dev/null | head -3 | while read -r store_def; do
        ./prsnl-cipher.sh store "SVELTE STORE: $store_name → $store_def"
    done
done

# Index API integration patterns
echo "🔌 Indexing API integrations..."
grep -r --include="*.ts" "fetch\(" ../frontend/src/lib/api/ 2>/dev/null | head -10 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    endpoint=$(echo "$line" | grep -oE '/api/[^"]+' | head -1)
    if [ ! -z "$endpoint" ]; then
        ./prsnl-cipher.sh store "API INTEGRATION: $file → $endpoint"
    fi
done

# Index route patterns
echo "🛣️ Indexing SvelteKit routes..."
find ../frontend/src/routes -name "+page.svelte" -type f 2>/dev/null | head -15 | while read -r file; do
    route_path=$(echo "$file" | sed 's|.*/routes||' | sed 's|/+page.svelte||')
    ./prsnl-cipher.sh store "SVELTEKIT ROUTE: $route_path → $(basename $(dirname $file))"
done

echo ""
echo "⚙️ 3. Configuration Patterns"
echo "---------------------------"

# Index environment variables
echo "🔐 Indexing environment variables..."
grep -E "^[A-Z_]+=" ../.env.example 2>/dev/null | head -10 | while read -r env_var; do
    var_name=$(echo "$env_var" | cut -d= -f1)
    ./prsnl-cipher.sh store "ENV VARIABLE: $var_name (see .env.example)"
done

# Index Docker configurations
echo "🐳 Indexing Docker configurations..."
grep -E "ports:|environment:" ../docker-compose.yml 2>/dev/null | head -10 | while read -r config; do
    ./prsnl-cipher.sh store "DOCKER CONFIG: $config"
done

echo ""
echo "🧪 4. Testing Patterns"
echo "---------------------"

# Index test patterns
echo "🔬 Indexing test patterns..."
find ../frontend -name "*.test.ts" -o -name "*.spec.ts" 2>/dev/null | head -10 | while read -r file; do
    test_name=$(basename "$file" | sed 's/\.[^.]*$//')
    ./prsnl-cipher.sh store "TEST PATTERN: $test_name → $(dirname $file)"
done

# Index Playwright tests
echo "🎭 Indexing Playwright tests..."
find ../tests -name "*.spec.ts" 2>/dev/null | head -10 | while read -r file; do
    test_name=$(basename "$file" .spec.ts)
    grep -E "test\(|describe\(" "$file" 2>/dev/null | head -3 | while read -r test_def; do
        ./prsnl-cipher.sh store "E2E TEST: $test_name → $test_def"
    done
done

echo ""
echo "🎨 5. Component Usage Patterns"
echo "-----------------------------"

# Index component imports
echo "📦 Indexing component imports..."
grep -r --include="*.svelte" "import.*from.*components" ../frontend/src/routes/ 2>/dev/null | head -15 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    component=$(echo "$line" | grep -oE 'import [^{]+ from' | sed 's/import //;s/ from//')
    if [ ! -z "$component" ]; then
        ./prsnl-cipher.sh store "COMPONENT USAGE: $file imports $component"
    fi
done

echo ""
echo "🔀 6. Integration Patterns"
echo "-------------------------"

# Index AI service integrations
echo "🤖 Indexing AI integrations..."
grep -r --include="*.py" "azure_openai\|openai" ../backend/app/services/ 2>/dev/null | head -10 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    ./prsnl-cipher.sh store "AI INTEGRATION: $file uses Azure OpenAI"
done

# Index WebSocket patterns
echo "🔌 Indexing WebSocket patterns..."
grep -r --include="*.py" "WebSocket\|websocket" ../backend/app/api/ 2>/dev/null | head -10 | while read -r line; do
    file=$(echo "$line" | cut -d: -f1 | xargs basename)
    ./prsnl-cipher.sh store "WEBSOCKET PATTERN: Found in $file"
done

echo ""
echo "📊 Codebase Statistics"
echo "---------------------"

# Count patterns
BACKEND_FILES=$(find ../backend -name "*.py" -type f 2>/dev/null | wc -l)
FRONTEND_FILES=$(find ../frontend/src -name "*.svelte" -o -name "*.ts" 2>/dev/null | wc -l)
TEST_FILES=$(find .. -name "*.test.ts" -o -name "*.spec.ts" 2>/dev/null | wc -l)

./prsnl-cipher.sh store "CODEBASE STATS: Backend=$BACKEND_FILES files, Frontend=$FRONTEND_FILES files, Tests=$TEST_FILES files"

echo "✅ Backend files: $BACKEND_FILES"
echo "✅ Frontend files: $FRONTEND_FILES"
echo "✅ Test files: $TEST_FILES"
echo ""

echo "💡 Quick Pattern Searches:"
echo "-------------------------"
echo "# Find FastAPI routes:"
echo "./prsnl-cipher.sh recall 'FASTAPI ROUTE'"
echo ""
echo "# Find service patterns:"
echo "./prsnl-cipher.sh recall 'SERVICE PATTERN'"
echo ""
echo "# Find component usage:"
echo "./prsnl-cipher.sh recall 'COMPONENT USAGE'"
echo ""
echo "# Find test patterns:"
echo "./prsnl-cipher.sh recall 'TEST PATTERN'"
echo ""

echo "✅ Codebase pattern indexing complete!"
echo ""
echo "🔄 Run after major code changes to update patterns."
echo "💡 Use recall commands to find implementation examples."