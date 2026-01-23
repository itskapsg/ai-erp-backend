#!/bin/bash

# ERP System Stop Script
# Usage: ./stop_erp.sh <instance_name>
# Example: ./stop_erp.sh v1

if [ $# -ne 1 ]; then
    echo "Usage: $0 <instance_name>"
    echo "Example: $0 v1"
    exit 1
fi

INSTANCE_NAME=$1

echo "Stopping ERP instance: $INSTANCE_NAME"

# Stop the docker-compose project
docker compose -p $INSTANCE_NAME down

if [ $? -eq 0 ]; then
    echo "✅ ERP instance '$INSTANCE_NAME' stopped successfully"
else
    echo "❌ Failed to stop ERP instance '$INSTANCE_NAME'"
    exit 1
fi