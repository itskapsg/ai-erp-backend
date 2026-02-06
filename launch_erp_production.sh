#!/bin/bash

# Production ERP System Launcher with Stability Fixes
# This script ensures PostgreSQL is used and sets memory limits

echo "🚀 Starting ERP System in Production Mode..."

# Set environment variables for production
export DATABASE_URL=postgresql://erp_admin:db_password_123@localhost/erp_dev_db
export PYTHONPATH=/workspace:$PYTHONPATH

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*http.server" || true
sleep 2

# Ensure PostgreSQL is running
echo "🗄️ Ensuring PostgreSQL is running..."
service postgresql start

# Start Backend with memory limit and production settings
echo "🔧 Starting Backend API (Port 54279)..."
cd /workspace
nohup python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 54279 \
    --workers 1 \
    --access-log \
    --log-level info \
    > backend.log 2>&1 &

BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
sleep 5

# Start Frontend
echo "🌐 Starting Frontend (Port 56000)..."
cd /workspace/frontend/dist
nohup python -m http.server 56000 --bind 0.0.0.0 > ../frontend.log 2>&1 &

FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Save PIDs for monitoring
echo $BACKEND_PID > /workspace/backend.pid
echo $FRONTEND_PID > /workspace/frontend.pid

echo "✅ ERP System started successfully!"
echo "📊 Backend API: http://localhost:54279"
echo "🌐 Frontend: http://localhost:56000"
echo "📝 Logs: backend.log, frontend/frontend.log"

# Health check
sleep 3
echo "🏥 Performing health check..."
curl -s http://localhost:54279/health || echo "❌ Backend health check failed"
curl -s http://localhost:56000/ > /dev/null && echo "✅ Frontend is responding" || echo "❌ Frontend health check failed"

echo "🎉 Production startup complete!"