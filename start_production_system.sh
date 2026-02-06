#!/bin/bash

# Production ERP System Startup Script
# This script ensures both backend and frontend are running permanently
# Usage: ./start_production_system.sh

set -e

echo "🚀 Starting Production ERP System..."
echo "=================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 2 "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "python.*http.server.*56000" 2>/dev/null || true
pm2 delete all 2>/dev/null || true
sleep 2

# Ensure PostgreSQL is running
echo "🔧 Ensuring PostgreSQL is running..."
if ! pgrep -x postgres >/dev/null; then
    echo "⚠️  PostgreSQL not detected, but continuing..."
fi

# Set environment variables
export DATABASE_URL="postgresql://erp_admin:db_password_123@localhost/erp_dev_db"
export PYTHONPATH="/workspace"

# Start Backend with PM2
echo "🔥 Starting Backend API (Port 54279)..."
cd /workspace

# Ensure virtual environment exists and has dependencies
if [ ! -d "venvs/production" ]; then
    echo "📦 Creating production virtual environment..."
    python3 -m venv venvs/production
fi

echo "📦 Installing/updating dependencies..."
venvs/production/bin/pip install -q -r requirements.txt
venvs/production/bin/pip install -q python-jose[cryptography] python-multipart bcrypt

# Start backend with PM2
pm2 start app/main.py \
    --name "erp-backend" \
    --interpreter venvs/production/bin/python \
    --max-memory-restart 400M \
    --restart-delay 3000 \
    --exp-backoff-restart-delay 100 \
    -e DATABASE_URL="$DATABASE_URL" \
    -e PYTHONPATH="/workspace" \
    -- --host 0.0.0.0 --port 54279

# Start Frontend with PM2
echo "🎨 Starting Frontend (Port 56000)..."
mkdir -p /workspace/logs

cd /workspace/frontend/dist
pm2 start "python3 -m http.server 56000 --bind 0.0.0.0" \
    --name "erp-frontend" \
    --max-memory-restart 100M \
    --restart-delay 2000

# Save PM2 configuration
echo "💾 Saving PM2 configuration..."
pm2 save

# Wait for services to be ready
wait_for_service "http://localhost:54279/health" "Backend API"
wait_for_service "http://localhost:56000/" "Frontend"

# Display status
echo ""
echo "📊 System Status:"
echo "=================="
pm2 list

echo ""
echo "🌐 Access URLs:"
echo "==============="
echo "🔗 Frontend: http://localhost:56000"
echo "🔗 Backend API: http://localhost:54279"
echo "🔗 Health Check: http://localhost:54279/health"
echo "🔗 API Docs: http://localhost:54279/docs"

echo ""
echo "📋 Management Commands:"
echo "======================"
echo "📊 Status: pm2 list"
echo "📋 Logs: pm2 logs"
echo "🔄 Restart: pm2 restart all"
echo "🛑 Stop: pm2 stop all"

echo ""
echo "✅ Production ERP System is running!"

# Test the system
echo ""
echo "🧪 Running system tests..."
echo "=========================="

# Test backend health
if curl -s http://localhost:54279/health | grep -q "healthy"; then
    echo "✅ Backend health check: PASSED"
else
    echo "❌ Backend health check: FAILED"
fi

# Test frontend
if curl -s http://localhost:56000/ | grep -q "ERP"; then
    echo "✅ Frontend accessibility: PASSED"
else
    echo "❌ Frontend accessibility: FAILED"
fi

echo ""
echo "🎉 System startup complete!"