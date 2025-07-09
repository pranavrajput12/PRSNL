#!/bin/bash
# Complete database initialization script for PRSNL
# This ensures the database is properly set up with all extensions

set -e

echo "🚀 Initializing PRSNL database..."

# Database configuration
DB_HOST="127.0.0.1"
DB_PORT="5433"
DB_NAME="prsnl"
DB_USER="prsnl"
DB_PASS="prsnl123"

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
    echo "❌ PostgreSQL is not running on port $DB_PORT"
    echo "   Start it with: brew services start postgresql@16"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Connect as the postgres user (owner of the database cluster)
echo "📝 Setting up database and user..."
/usr/local/opt/postgresql@16/bin/psql -h $DB_HOST -p $DB_PORT -d postgres <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
    END IF;
END\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Make user superuser temporarily for extension creation
ALTER USER $DB_USER WITH SUPERUSER;
EOF

echo "✅ Database and user created"

# Install extensions
echo "📦 Installing required extensions..."
PGPASSWORD=$DB_PASS /usr/local/opt/postgresql@16/bin/psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<EOF
-- Install extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Verify extensions
SELECT extname, extversion FROM pg_extension;

-- Remove superuser privileges after extensions are installed
ALTER USER $DB_USER WITH NOSUPERUSER;
EOF

echo "✅ Extensions installed"

# Apply schema
if [ -f "/Users/pronav/Personal Knowledge Base/PRSNL/backend/app/db/schema.sql" ]; then
    echo "📋 Applying database schema..."
    PGPASSWORD=$DB_PASS /usr/local/opt/postgresql@16/bin/psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend/app/db/schema.sql
    echo "✅ Schema applied"
else
    echo "⚠️  Schema file not found. You'll need to apply it manually."
fi

echo "✨ Database initialization complete!"
echo ""
echo "📊 Database connection info:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASS"
echo ""
echo "🔗 Connection string: postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"