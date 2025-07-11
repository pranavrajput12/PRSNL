#!/bin/bash

echo "🔍 PRSNL Setup Verification"
echo "=========================="

# Check local PostgreSQL
echo -e "\n📊 Local PostgreSQL Database:"
if psql -U pronav -d prsnl -c "SELECT 'Connected' as status;" >/dev/null 2>&1; then
    echo "✅ Connected to local PostgreSQL"
    psql -U pronav -d prsnl -t -c "SELECT COUNT(*) || ' total items (' || STRING_AGG(type || ': ' || count::text, ', ') || ')' FROM (SELECT type, COUNT(*) as count FROM items GROUP BY type) t;"
else
    echo "❌ Cannot connect to local PostgreSQL"
fi

# Check Docker services
echo -e "\n🐳 Docker Services:"
if docker ps | grep prsnl_redis >/dev/null; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
fi

# Check backend
echo -e "\n🚀 Backend API:"
if curl -s http://localhost:8000/health | grep -q "UP"; then
    echo "✅ Backend is running and healthy"
    echo "   Database connection: $(curl -s http://localhost:8000/health | jq -r .database.status)"
else
    echo "❌ Backend is not running or unhealthy"
fi

# Check frontend
echo -e "\n🎨 Frontend:"
if curl -s http://localhost:3004/ | grep -q "<!DOCTYPE html>" >/dev/null 2>&1; then
    echo "✅ Frontend is running on port 3004"
else
    echo "❌ Frontend is not running"
fi

# Check Code Cortex entries
echo -e "\n📚 Code Cortex Entries:"
CORTEX_COUNT=$(psql -U pronav -d prsnl -t -c "SELECT COUNT(*) FROM items WHERE type = 'development';" | xargs)
if [ "$CORTEX_COUNT" -gt 0 ]; then
    echo "✅ Found $CORTEX_COUNT development items"
    psql -U pronav -d prsnl -c "SELECT title FROM items WHERE type = 'development' LIMIT 3;" | grep -v "title" | grep -v "---" | grep -v "rows)" | while read line; do
        echo "   - $line"
    done
else
    echo "❌ No Code Cortex entries found"
fi

echo -e "\n✨ Summary:"
echo "Database: postgresql://pronav@localhost:5432/prsnl"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3004"
echo "Redis: localhost:6379 (Docker)"