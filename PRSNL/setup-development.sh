#!/bin/bash

# PRSNL Development Environment Setup Script
# Sets up pre-commit hooks and prepares monitoring

set -e

echo "🚀 Setting up PRSNL development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the PRSNL root directory"
    exit 1
fi

print_status "Found PRSNL project structure"

# Install pre-commit hooks
echo ""
echo "📋 Setting up pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    print_warning "pre-commit not found globally, using pip install"
    cd backend
    pip3 install pre-commit
    cd ..
fi

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    print_status "Pre-commit hooks installed"
    
    # Run initial check
    print_status "Running initial pre-commit check..."
    pre-commit run --all-files || print_warning "Some pre-commit checks failed - this is normal for first run"
else
    print_error ".pre-commit-config.yaml not found"
fi

# Note: whisper.cpp models are automatically downloaded on first use
echo ""
echo "🎙️ Offline transcription uses whisper.cpp (models auto-download on first use)"
print_status "whisper.cpp models will be downloaded automatically when needed"

# Create logs directory for monitoring
echo ""
echo "📊 Setting up monitoring directories..."

mkdir -p backend/logs
mkdir -p monitoring/grafana/provisioning
mkdir -p monitoring/grafana/dashboards

# Create basic log files
touch backend/logs/prsnl.log
touch backend/logs/error.log

print_status "Monitoring directories created"

# Set up environment variables template
echo ""
echo "🔧 Setting up environment configuration..."

ENV_FILE="backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# PRSNL Environment Configuration

# Database
DATABASE_URL=postgresql://pronav:Jaimatadi108!@localhost:5432/prsnl

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Azure OpenAI (for Whisper)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# GitHub (for enhanced API limits)
GITHUB_TOKEN=your_github_token

# Observability
OTLP_TRACES_ENDPOINT=http://localhost:4317
OTLP_METRICS_ENDPOINT=http://localhost:4317
PROMETHEUS_PORT=8001
ENVIRONMENT=development
ENABLE_METRICS=true

# Development
DEBUG=true
LOG_LEVEL=INFO
EOF
    print_status "Environment template created at $ENV_FILE"
    print_warning "Please update $ENV_FILE with your actual API keys"
else
    print_status "Environment file already exists"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."

cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found in backend directory"
fi
cd ..

# Check if Rancher Desktop is running
echo ""
echo "🐳 Checking container runtime..."

if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_status "Docker/Rancher Desktop is running"
    else
        print_warning "Docker/Rancher Desktop not accessible - please start Rancher Desktop"
    fi
else
    print_error "Docker not found - please install Rancher Desktop"
fi

# Create development scripts
echo ""
echo "📝 Creating development scripts..."

# Start monitoring script
cat > start-monitoring.sh << 'EOF'
#!/bin/bash
echo "🔍 Starting PRSNL monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Monitoring services:"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo "  • Prometheus: http://localhost:9090"
echo "  • Loki: http://localhost:3100"

echo "✅ Monitoring stack started!"
EOF
chmod +x start-monitoring.sh

# Stop monitoring script
cat > stop-monitoring.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping PRSNL monitoring stack..."
docker-compose -f docker-compose.monitoring.yml down
echo "✅ Monitoring stack stopped!"
EOF
chmod +x stop-monitoring.sh

print_status "Development scripts created"

# Final summary
echo ""
echo "🎉 PRSNL development environment setup complete!"
echo ""
echo "📋 Summary of what was set up:"
echo "  ✅ Pre-commit hooks for code quality"
echo "  ✅ whisper.cpp for offline transcription (auto-downloads models)"
echo "  ✅ Monitoring directory structure"
echo "  ✅ Environment configuration template"
echo "  ✅ Python dependencies"
echo "  ✅ Development scripts"
echo ""
echo "🚀 Next steps:"
echo "  1. Update backend/.env with your API keys"
echo "  2. Start the main PRSNL services: docker-compose up -d"
echo "  3. Start monitoring: ./start-monitoring.sh"
echo "  4. Access the application: http://localhost:3003"
echo "  5. Monitor performance: http://localhost:3000"
echo ""
echo "💡 Development commands:"
echo "  • Run pre-commit: pre-commit run --all-files"
echo "  • Start monitoring: ./start-monitoring.sh"
echo "  • Stop monitoring: ./stop-monitoring.sh"
echo "  • View logs: tail -f backend/logs/prsnl.log"
echo "  • Check metrics: curl http://localhost:8000/metrics"
echo ""
print_status "Happy coding! 🚀"