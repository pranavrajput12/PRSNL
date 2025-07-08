#!/bin/bash

echo "🗄️  PRSNL Data Migration to Railway"
echo "=================================="

# Check if local backend is running
if ! docker ps | grep -q prsnl_db; then
    echo "❌ Local database container not running"
    echo "Please start it with: cd PRSNL && docker-compose up -d db"
    exit 1
fi

echo "✅ Local database found"

# Export local data
echo ""
echo "📤 Exporting local database..."
docker-compose exec -T db pg_dump -U postgres prsnl > prsnl_backup.sql

if [ -f prsnl_backup.sql ]; then
    echo "✅ Database exported to prsnl_backup.sql"
    echo "   Size: $(du -h prsnl_backup.sql | cut -f1)"
else
    echo "❌ Export failed"
    exit 1
fi

echo ""
echo "📥 To import to Railway:"
echo ""
echo "1. Get your Railway PostgreSQL URL:"
echo "   cd backend && railway variables | grep DATABASE_URL"
echo ""
echo "2. Import the data:"
echo "   psql \$DATABASE_URL < ../prsnl_backup.sql"
echo ""
echo "Or use Railway's database dashboard to import the SQL file"