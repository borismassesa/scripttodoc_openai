#!/bin/bash

# Simplified Backend Deployment
# Uses ACR Build with better error handling and progress monitoring

set -e

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

echo "🚀 Simplified Backend Deployment"
echo "================================="
echo ""

# Get infrastructure outputs
CONTAINER_REGISTRY=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.containerRegistryName.value' \
  -o tsv)

KEY_VAULT_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.keyVaultName.value' \
  -o tsv)

CAE_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.containerAppsEnvironmentId.value' \
  -o tsv)

SB_NAMESPACE=$(az servicebus namespace list \
  -g $RESOURCE_GROUP \
  --query "[0].name" \
  -o tsv)

echo "✅ Container Registry: $CONTAINER_REGISTRY"
echo ""

# Build API image
echo "📦 Building API image (this will take 10-15 minutes)..."
echo "   Uploading code and building in Azure..."
cd ../backend

# Note: Context (.) must be the last argument for az acr build
BUILD_OUTPUT=$(az acr build \
  --registry $CONTAINER_REGISTRY \
  --image $APP_NAME-api:latest \
  --platform linux/amd64 \
  --file Dockerfile \
  --timeout 3600 \
  . 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ API image built successfully"
else
    echo "❌ API build failed"
    echo "$BUILD_OUTPUT"
    exit 1
fi

echo ""

# Build Worker image
echo "📦 Building Worker image..."
cd ../backend

# Note: Context (.) must be the last argument for az acr build
BUILD_OUTPUT=$(az acr build \
  --registry $CONTAINER_REGISTRY \
  --image $APP_NAME-worker:latest \
  --platform linux/amd64 \
  --file Dockerfile.worker \
  --timeout 3600 \
  . 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Worker image built successfully"
else
    echo "❌ Worker build failed"
    echo "$BUILD_OUTPUT"
    exit 1
fi

echo ""

# Deploy Container Apps
echo "📋 Deploying Container Apps..."
cd ../deployment

# Deploy API
echo "Deploying API..."
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file backend-api.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    imageTag=latest \
  --output none

API_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-api \
  --query 'properties.outputs.apiUrl.value' \
  -o tsv)

API_PRINCIPAL_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-api \
  --query 'properties.outputs.apiPrincipalId.value' \
  -o tsv)

echo "✅ API deployed: $API_URL"

# Deploy Worker
echo "Deploying Worker..."
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file backend-worker.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    serviceBusNamespaceName=$SB_NAMESPACE \
    imageTag=latest \
  --output none

WORKER_PRINCIPAL_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-worker \
  --query 'properties.outputs.workerPrincipalId.value' \
  -o tsv)

echo "✅ Worker deployed"
echo ""

# Configure RBAC
echo "📋 Configuring RBAC permissions..."

KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)
STORAGE_ID=$(az storage account list -g $RESOURCE_GROUP --query "[0].id" -o tsv)
COSMOS_ID=$(az cosmosdb show -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query id -o tsv)
SB_ID=$(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Assign roles (ignore errors if already assigned)
az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true
az role assignment create --assignee $API_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true
az role assignment create --assignee $API_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Azure Service Bus Data Owner" --scope $SB_ID 2>/dev/null || true
az role assignment create --assignee $API_PRINCIPAL_ID --role "Azure Service Bus Data Sender" --scope $SB_ID 2>/dev/null || true

echo "✅ RBAC configured"
echo ""

echo "======================================"
echo "✅ Backend Deployment Complete!"
echo "======================================"
echo ""
echo "API URL: $API_URL"
echo ""
echo "Next: Deploy frontend with ./deploy-frontend-containerapp.sh"
echo ""
