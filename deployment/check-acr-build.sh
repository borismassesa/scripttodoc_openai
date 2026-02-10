#!/bin/bash

# Check ACR Build Status
# This script checks the status of recent ACR builds

set -e

RESOURCE_GROUP="rg-scripttodoc-prod"
CONTAINER_REGISTRY=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name azure-infrastructure \
    --query 'properties.outputs.containerRegistryName.value' \
    -o tsv 2>/dev/null || echo "crscripttodocprod")

echo "🔍 Checking ACR Build Status"
echo "============================"
echo "Registry: $CONTAINER_REGISTRY"
echo ""

echo "📋 Checking for existing images..."
echo ""

# Check if images exist
echo "API images:"
az acr repository show-tags \
    --registry $CONTAINER_REGISTRY \
    --name scripttodoc-api \
    --orderby time_desc \
    --top 3 \
    --output table 2>/dev/null || echo "  No API images found"

echo ""
echo "Worker images:"
az acr repository show-tags \
    --registry $CONTAINER_REGISTRY \
    --name scripttodoc-worker \
    --orderby time_desc \
    --top 3 \
    --output table 2>/dev/null || echo "  No Worker images found"

echo ""
echo "📋 To check build status in Azure Portal:"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "   https://portal.azure.com/#@/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-scripttodoc-prod/providers/Microsoft.ContainerRegistry/registries/$CONTAINER_REGISTRY/overview"
echo ""
echo "   Navigate to: Services → Tasks → Runs (for ACR Tasks)"
echo "   Or: Services → Repositories → scripttodoc-api (to see images)"
echo ""
