#!/bin/bash

# Monitor Docker Push Progress
# Run this in another terminal to see if push is still progressing

echo "🔍 Monitoring Docker Push Progress"
echo "=================================="
echo ""

CONTAINER_REGISTRY="crscripttodocprod"

echo "Checking for active pushes..."
echo ""

# Check if there are any Docker processes pushing
if pgrep -f "docker push" > /dev/null; then
    echo "✅ Docker push process is running"
    echo ""
    echo "To see detailed progress, check Docker Desktop or run:"
    echo "  docker images | grep $CONTAINER_REGISTRY"
else
    echo "⚠️  No active push process found"
    echo "The push may have completed or failed"
    echo ""
    echo "Check if images were pushed:"
    az acr repository show-tags \
        --registry $CONTAINER_REGISTRY \
        --name scripttodoc-api \
        --output table 2>/dev/null || echo "No API images found"
fi

echo ""
echo "💡 Tip: Large layers (340MB) can take 5-10 minutes to push"
echo "   This is normal for Python dependency layers"
echo ""
