#!/bin/bash

# Troubleshoot Docker Push Issues
# This script helps diagnose and fix Docker push problems

set -e

echo "🔍 Troubleshooting Docker Push Issues"
echo "======================================"
echo ""

# Check Docker buildx status
echo "📋 Step 1: Checking Docker buildx status..."
docker buildx ls
echo ""

# Check network connectivity to ACR
echo "📋 Step 2: Testing ACR connectivity..."
RESOURCE_GROUP="rg-scripttodoc-prod"
CONTAINER_REGISTRY=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name azure-infrastructure \
    --query 'properties.outputs.containerRegistryName.value' \
    -o tsv 2>/dev/null || echo "crscripttodocprod")

ACR_URL="$CONTAINER_REGISTRY.azurecr.io"
echo "Testing connection to $ACR_URL..."
if ping -c 1 $(echo $ACR_URL | cut -d'/' -f1) &> /dev/null; then
    echo "✅ Network connectivity OK"
else
    echo "⚠️  Network connectivity issue detected"
fi
echo ""

# Check if ACR login is still valid
echo "📋 Step 3: Testing ACR authentication..."
if az acr login --name $CONTAINER_REGISTRY &> /dev/null; then
    echo "✅ ACR authentication OK"
else
    echo "❌ ACR authentication failed. Re-authenticating..."
    az acr login --name $CONTAINER_REGISTRY
fi
echo ""

# Check Docker disk space
echo "📋 Step 4: Checking Docker disk space..."
docker system df
echo ""

# Recommendations
echo "======================================"
echo "💡 Recommendations:"
echo ""
echo "If the push is stuck, try:"
echo ""
echo "1. Cancel the current build (Ctrl+C) and retry:"
echo "   cd backend"
echo "   docker buildx build --platform linux/amd64 \\"
echo "     -t $CONTAINER_REGISTRY.azurecr.io/scripttodoc-api:latest \\"
echo "     -f Dockerfile . \\"
echo "     --push"
echo ""
echo "2. Use ACR build instead (faster, builds in Azure):"
echo "   az acr build --registry $CONTAINER_REGISTRY \\"
echo "     --image scripttodoc-api:latest \\"
echo "     --platform linux/amd64 \\"
echo "     --file Dockerfile ."
echo ""
echo "3. Check Docker Desktop resources:"
echo "   - Increase allocated memory/CPU"
echo "   - Restart Docker Desktop"
echo ""
echo "4. Try building without buildx (if on amd64 machine):"
echo "   docker build -t $CONTAINER_REGISTRY.azurecr.io/scripttodoc-api:latest -f Dockerfile ."
echo "   docker push $CONTAINER_REGISTRY.azurecr.io/scripttodoc-api:latest"
echo ""
