#!/bin/bash

# Check Logs Script
# Quick script to view logs from all Container Apps

set -e

RESOURCE_GROUP="rg-scripttodoc-prod"
APP_NAME="scripttodoc"
ENVIRONMENT="prod"

echo "📋 Container App Logs"
echo "===================="
echo ""

# Function to show logs
show_logs() {
    local APP_NAME=$1
    local CONTAINER_NAME=$2
    
    echo "📝 $APP_NAME logs (last 50 lines):"
    echo "-----------------------------------"
    az containerapp logs show \
        -n $APP_NAME \
        -g $RESOURCE_GROUP \
        --tail 50 \
        --type console \
        2>/dev/null || echo "⚠️  Could not retrieve logs"
    echo ""
}

# API logs
if az containerapp show -n ca-$APP_NAME-$ENVIRONMENT-api -g $RESOURCE_GROUP &> /dev/null; then
    show_logs "ca-$APP_NAME-$ENVIRONMENT-api" "api"
fi

# Worker logs
if az containerapp show -n ca-$APP_NAME-$ENVIRONMENT-wrk -g $RESOURCE_GROUP &> /dev/null; then
    show_logs "ca-$APP_NAME-$ENVIRONMENT-wrk" "worker"
fi

# Frontend logs
if az containerapp show -n ca-$APP_NAME-$ENVIRONMENT-frontend -g $RESOURCE_GROUP &> /dev/null; then
    show_logs "ca-$APP_NAME-$ENVIRONMENT-frontend" "frontend"
fi

echo "💡 To follow logs in real-time, use:"
echo "   az containerapp logs show -n <app-name> -g $RESOURCE_GROUP --follow"
echo ""
