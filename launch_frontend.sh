#!/bin/bash

# Frontend Launch Script
# Starts the React PWA development server

echo "🚀 Starting AI ERP System Frontend..."
echo "======================================"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🌐 Starting development server..."
echo "Frontend will be available at:"
echo "  - Local:   http://localhost:5173"
echo "  - Network: http://0.0.0.0:5173"
echo ""
echo "📱 PWA Features:"
echo "  - Responsive design (mobile & desktop)"
echo "  - Installable on mobile devices"
echo "  - Offline capabilities"
echo ""
echo "🔧 Connected to API: http://localhost:54279"
echo ""

# Start the development server
npm run dev -- --host 0.0.0.0 --port 5173