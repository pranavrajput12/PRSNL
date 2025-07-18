#!/bin/bash

echo "🖥️  Mac Mini M4 PRSNL Setup Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

echo "1. Checking Prerequisites..."
echo "----------------------------"

# Check for Homebrew
if command_exists brew; then
    print_status 0 "Homebrew is installed"
    export PATH="/opt/homebrew/bin:$PATH"
else
    echo -e "${YELLOW}!${NC} Homebrew not found in PATH. Trying to add it..."
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        print_status 0 "Homebrew found and added to PATH"
    else
        print_status 1 "Homebrew not installed. Please install it first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
fi

echo ""
echo "2. PostgreSQL Setup..."
echo "----------------------"

# Check if PostgreSQL is installed
if brew list postgresql@16 &>/dev/null; then
    print_status 0 "PostgreSQL 16 is installed"
    
    # Check if PostgreSQL is running
    if brew services list | grep "postgresql@16" | grep "started" &>/dev/null; then
        print_status 0 "PostgreSQL is running"
    else
        echo "Starting PostgreSQL..."
        brew services start postgresql@16
        sleep 2
        print_status $? "PostgreSQL started"
    fi
else
    echo "Installing PostgreSQL 16..."
    brew install postgresql@16
    print_status $? "PostgreSQL 16 installed"
    
    echo "Starting PostgreSQL..."
    brew services start postgresql@16
    sleep 2
    print_status $? "PostgreSQL started"
fi

# Check database
echo ""
echo "3. Database Check..."
echo "-------------------"

if psql -U pronav -d prsnl -c "\dt" &>/dev/null; then
    print_status 0 "Database 'prsnl' exists and is accessible"
    
    # Check for tables
    TABLES=$(psql -U pronav -d prsnl -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "  Tables found: $TABLES"
    
    # Check for users table data
    if psql -U pronav -d prsnl -c "SELECT COUNT(*) FROM users;" &>/dev/null; then
        USER_COUNT=$(psql -U pronav -d prsnl -t -c "SELECT COUNT(*) FROM users;")
        echo "  Users in database: $USER_COUNT"
    fi
    
    # Check for items table data
    if psql -U pronav -d prsnl -c "SELECT COUNT(*) FROM items;" &>/dev/null; then
        ITEM_COUNT=$(psql -U pronav -d prsnl -t -c "SELECT COUNT(*) FROM items;")
        echo "  Items in database: $ITEM_COUNT"
    fi
    
    # Check pgvector
    if psql -U pronav -d prsnl -c "SELECT * FROM pg_extension WHERE extname = 'vector';" | grep vector &>/dev/null; then
        print_status 0 "pgvector extension is installed"
    else
        print_status 1 "pgvector extension not found"
    fi
else
    echo -e "${YELLOW}!${NC} Database 'prsnl' not found. Creating it..."
    createdb prsnl
    print_status $? "Database 'prsnl' created"
fi

echo ""
echo "4. Python Setup..."
echo "------------------"

# Check for Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_status 0 "Python installed: $PYTHON_VERSION"
else
    echo "Installing Python 3.11..."
    brew install python@3.11
    print_status $? "Python 3.11 installed"
fi

echo ""
echo "5. Quick Start Commands..."
echo "--------------------------"
echo ""
echo "To complete the setup, run these commands:"
echo ""
echo "# 1. Set up backend (in a new terminal):"
echo "cd \"$PWD/backend\""
echo "python3 -m venv venv"
echo "source venv/bin/activate"
echo "pip install -r requirements.txt"
echo "alembic upgrade head  # Run migrations"
echo "uvicorn app.main:app --reload --port 8000"
echo ""
echo "# 2. Set up frontend (in another terminal):"
echo "cd \"$PWD/frontend\""
echo "npm install"
echo "npm run dev -- --port 3004"
echo ""
echo "# 3. Start auth services (optional, in another terminal):"
echo "cd \"$PWD\""
echo "colima start  # If not already running"
echo "docker-compose -f docker-compose.auth.yml up -d"
echo ""
echo "# 4. Access the application:"
echo "Frontend: http://localhost:3004"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

# Save current status
echo ""
echo "6. Saving Setup Status..."
echo "------------------------"

cat > setup_status.json << EOF
{
  "timestamp": "$(date)",
  "postgresql": $(brew services list | grep "postgresql@16" | grep "started" &>/dev/null && echo "true" || echo "false"),
  "database_exists": $(psql -U pronav -d prsnl -c "\dt" &>/dev/null && echo "true" || echo "false"),
  "pgvector_installed": $(psql -U pronav -d prsnl -c "SELECT * FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | grep vector &>/dev/null && echo "true" || echo "false"),
  "python_installed": $(command_exists python3 && echo "true" || echo "false"),
  "homebrew_path": "$(which brew)"
}
EOF

print_status 0 "Setup status saved to setup_status.json"

echo ""
echo "✅ Initial setup check complete!"
echo ""
echo "⚠️  IMPORTANT: Your database data should be preserved if PostgreSQL was already set up."
echo "   The tables 'users' and 'items' were created manually during the initial setup."
echo ""