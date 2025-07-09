#!/bin/bash
# Setup script for pgvector on PostgreSQL 16
# This ensures pgvector is properly installed and won't break in the future

set -e  # Exit on any error

echo "🔧 Setting up pgvector for PostgreSQL 16..."

# Check if PostgreSQL 16 is installed
if ! command -v /usr/local/opt/postgresql@16/bin/psql &> /dev/null; then
    echo "❌ PostgreSQL 16 is not installed. Please install it first with: brew install postgresql@16"
    exit 1
fi

# Get PostgreSQL 16 paths
PG_CONFIG="/usr/local/opt/postgresql@16/bin/pg_config"
PG_VERSION=$($PG_CONFIG --version | awk '{print $2}' | sed 's/\..*//')
PG_SHAREDIR=$($PG_CONFIG --sharedir)
PG_PKGLIBDIR=$($PG_CONFIG --pkglibdir)

echo "📍 PostgreSQL 16 paths:"
echo "   Share dir: $PG_SHAREDIR"
echo "   Lib dir: $PG_PKGLIBDIR"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$PG_SHAREDIR/extension"
mkdir -p "$PG_PKGLIBDIR"

# Check if pgvector files exist for other PostgreSQL versions
if [ -f "/usr/local/share/postgresql@14/extension/vector.control" ]; then
    echo "📋 Copying pgvector extension files..."
    cp -f /usr/local/share/postgresql@14/extension/vector* "$PG_SHAREDIR/extension/" 2>/dev/null || true
    
    # Copy library file
    if [ -f "/usr/local/Cellar/pgvector/0.8.0/lib/postgresql@14/vector.so" ]; then
        echo "📚 Copying pgvector library..."
        cp -f /usr/local/Cellar/pgvector/0.8.0/lib/postgresql@14/vector.so "$PG_PKGLIBDIR/" 2>/dev/null || true
    fi
else
    echo "⚠️  pgvector files not found for PostgreSQL 14. Trying alternative approach..."
    
    # Clone and build pgvector
    echo "🔨 Building pgvector from source..."
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
    cd pgvector
    
    export PG_CONFIG="/usr/local/opt/postgresql@16/bin/pg_config"
    make
    make install
    
    cd ..
    rm -rf "$TEMP_DIR"
fi

echo "✅ pgvector files installed"

# Now install the extension in the database
echo "🗄️  Installing pgvector extension in database..."

# Check if database is running
if ! pg_isready -h 127.0.0.1 -p 5433 &> /dev/null; then
    echo "⚠️  PostgreSQL is not running on port 5433. Starting it..."
    brew services start postgresql@16
    sleep 3
fi

# Create the extension using the postgres system user
echo "📝 Creating pgvector extension in database..."
/usr/local/opt/postgresql@16/bin/psql -h 127.0.0.1 -p 5433 -d prsnl <<EOF
-- First, grant superuser to prsnl temporarily
ALTER USER prsnl WITH SUPERUSER;

-- Create the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Revoke superuser after extension is created
ALTER USER prsnl WITH NOSUPERUSER;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
EOF

echo "✅ pgvector setup complete!"
echo ""
echo "🔍 To verify pgvector is working:"
echo "   psql -h 127.0.0.1 -p 5433 -U prsnl -d prsnl -c 'SELECT * FROM pg_extension WHERE extname = '\''vector'\'';'"