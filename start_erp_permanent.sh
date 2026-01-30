#!/bin/bash

# Permanent ERP System Startup Script
# This script ensures PostgreSQL, Backend, and Frontend are all running
# Usage: ./start_erp_permanent.sh

set -e

echo "🚀 Starting PERMANENT ERP System..."
echo "===================================="

# Function to check if a service is running
check_service() {
    local service_name=$1
    local check_command=$2
    
    if eval "$check_command" >/dev/null 2>&1; then
        echo "✅ $service_name is running"
        return 0
    else
        echo "❌ $service_name is not running"
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=15
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 3 "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# 1. Start PostgreSQL
echo "🐘 Starting PostgreSQL..."
if ! check_service "PostgreSQL" "pgrep -x postgres"; then
    service postgresql start
    sleep 3
    if check_service "PostgreSQL" "pgrep -x postgres"; then
        echo "✅ PostgreSQL started successfully"
    else
        echo "❌ Failed to start PostgreSQL"
        exit 1
    fi
fi

# 2. Clean up any existing PM2 processes
echo "🧹 Cleaning up existing PM2 processes..."
pm2 delete all 2>/dev/null || true
sleep 2

# 3. Set environment variables
export DATABASE_URL="postgresql://erp_admin:db_password_123@localhost/erp_dev_db"
export PYTHONPATH="$PWD"

# 4. Ensure virtual environment and dependencies
echo "📦 Setting up Python environment..."
cd $PWD

if [ ! -d "venvs/production" ]; then
    echo "📦 Creating production virtual environment..."
    python3 -m venv venvs/production
fi

echo "📦 Installing/updating dependencies..."
venvs/production/bin/pip install -q -r requirements.txt
venvs/production/bin/pip install -q python-jose[cryptography] python-multipart bcrypt

# 5. Start Backend with PM2
echo "🔥 Starting Backend API (Port 54279)..."
pm2 start venvs/production/bin/python \
    --name "erp-backend" \
    --max-memory-restart 400M \
    --restart-delay 3000 \
    --exp-backoff-restart-delay 100 \
    -e DATABASE_URL="$DATABASE_URL" \
    -e PYTHONPATH="$PWD" \
    -- -m uvicorn app.main:app --host 0.0.0.0 --port 54279

# 6. Start Frontend with PM2
echo "🎨 Starting Frontend (Port 56000)..."
cd $PWD/frontend/dist
pm2 start "python3 -m http.server 56000 --bind 0.0.0.0" \
    --name "erp-frontend" \
    --max-memory-restart 100M \
    --restart-delay 2000

# 7. Save PM2 configuration
echo "💾 Saving PM2 configuration..."
pm2 save

# 8. Wait for services to be ready
wait_for_service "http://localhost:54279/health" "Backend API"
wait_for_service "http://localhost:56000/" "Frontend"

# 9. Display status
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

# 10. Test the system
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
echo "🎉 PERMANENT ERP System is running!"
echo "🌍 External access: http://95.111.253.134:54279 (Backend) & http://95.111.253.134:56000 (Frontend)"

# 11. Create auto-startup service
echo ""
echo "🔧 Creating auto-startup service..."
cat > /etc/systemd/system/erp-system.service << 'EOF'
[Unit]
Description=ERP System Auto-Startup
After=network.target postgresql.service

[Service]
Type=forking
User=root
WorkingDirectory=$PWD
ExecStart=$PWD/start_erp_permanent.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable erp-system.service

echo "✅ Auto-startup service created and enabled"
echo "🔄 System will automatically start on boot"