#!/bin/bash

# ERP System Parallel Launch Script
# Usage: ./launch_erp.sh <instance_name> <port_number>
# Example: ./launch_erp.sh v1 8000

if [ $# -ne 2 ]; then
    echo "Usage: $0 <instance_name> <port_number>"
    echo "Example: $0 v1 8000"
    exit 1
fi

INSTANCE_NAME=$1
PORT_NUMBER=$2

echo "Launching ERP instance: $INSTANCE_NAME on port: $PORT_NUMBER"

# Set the APP_PORT environment variable and run docker-compose
APP_PORT=$PORT_NUMBER docker compose -p $INSTANCE_NAME up -d

if [ $? -eq 0 ]; then
    echo "✅ ERP instance '$INSTANCE_NAME' launched successfully on port $PORT_NUMBER"
    echo "🔗 Access the application at: http://localhost:$PORT_NUMBER"
    echo "📊 Check status with: docker compose -p $INSTANCE_NAME ps"
    echo "📋 View logs with: docker compose -p $INSTANCE_NAME logs -f"
    echo "🛑 Stop instance with: docker compose -p $INSTANCE_NAME down"
else
    echo "❌ Failed to launch ERP instance '$INSTANCE_NAME'"
    exit 1
fi