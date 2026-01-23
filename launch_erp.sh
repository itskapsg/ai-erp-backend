#!/bin/bash

# ERP System Parallel Launch Script (PM2 Architecture)
# Usage: ./launch_erp.sh <instance_name> <port_number>
# Example: ./launch_erp.sh dev 8000

if [ $# -ne 2 ]; then
    echo "Usage: $0 <instance_name> <port_number>"
    echo "Example: $0 dev 8000"
    exit 1
fi

INSTANCE_NAME=$1
PORT_NUMBER=$2

echo "Launching ERP instance: $INSTANCE_NAME on port: $PORT_NUMBER"

# Step A (Isolation): Check if venvs/$instance_name exists. If not, create it
if [ ! -d "venvs/$INSTANCE_NAME" ]; then
    echo "🔧 Creating virtual environment for $INSTANCE_NAME..."
    python3 -m venv venvs/$INSTANCE_NAME
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Step B (Dependencies): Install requirements using that specific venv
echo "📦 Installing dependencies for $INSTANCE_NAME..."
venvs/$INSTANCE_NAME/bin/pip install -r requirements.txt > /tmp/${INSTANCE_NAME}_install.log 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Check /tmp/${INSTANCE_NAME}_install.log"
    exit 1
fi

# Step C (Launch): Use PM2 to start the app
echo "🚀 Starting $INSTANCE_NAME with PM2..."
pm2 start app/main.py --name $INSTANCE_NAME --interpreter venvs/$INSTANCE_NAME/bin/python -- --host 0.0.0.0 --port $PORT_NUMBER

if [ $? -eq 0 ]; then
    # Step D: Save the process list
    pm2 save > /dev/null 2>&1
    
    echo "✅ ERP instance '$INSTANCE_NAME' launched successfully on port $PORT_NUMBER"
    echo "🔗 Access the application at: http://localhost:$PORT_NUMBER"
    echo "📊 Check status with: pm2 list"
    echo "📋 View logs with: pm2 logs $INSTANCE_NAME"
    echo "🛑 Stop instance with: pm2 stop $INSTANCE_NAME"
    echo "🗑️  Delete instance with: pm2 delete $INSTANCE_NAME"
else
    echo "❌ Failed to launch ERP instance '$INSTANCE_NAME'"
    exit 1
fi