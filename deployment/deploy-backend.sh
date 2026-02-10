#!/bin/bash

# Backend Deployment Script for ScriptToDoc
# This script builds Docker images, pushes to ACR, and deploys Container Apps

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"
LOCATION="eastus"

echo "🚀 Starting Backend Deployment"
echo "================================"
echo "Resource Group: $RESOURCE_GROUP"
echo "Environment: $ENVIRONMENT"
echo "App Name: $APP_NAME"
echo ""

# Step 1: Get infrastructure outputs
echo "📋 Step 1: Getting infrastructure outputs..."
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
echo "✅ Key Vault: $KEY_VAULT_NAME"
echo "✅ Container Apps Environment ID: ${CAE_ID:0:50}..."
echo "✅ Service Bus Namespace: $SB_NAMESPACE"
echo ""

# Step 2: Enable admin user on ACR temporarily (for Docker login)
echo "📋 Step 2: Configuring Container Registry..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled true
echo "✅ ACR admin enabled"
echo ""

# Step 3: Login to ACR
echo "📋 Step 3: Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY
echo "✅ Logged in to ACR"
echo ""

# Step 4: Build and push API image (for AMD64 platform)
echo "📋 Step 4: Building and pushing API image (for linux/amd64)..."
cd ../backend
docker buildx build --platform linux/amd64 -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-api:latest -f Dockerfile . --push
echo "✅ API image built and pushed"
echo ""

# Step 5: Build and push Worker image (for AMD64 platform)
echo "📋 Step 5: Building and pushing Worker image (for linux/amd64)..."
docker buildx build --platform linux/amd64 -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-worker:latest -f Dockerfile.worker . --push
echo "✅ Worker image built and pushed"
echo ""

# Step 6: Deploy API Container App
echo "📋 Step 6: Deploying API Container App..."
cd ../deployment
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file backend-api.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    imageTag=latest

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

echo "✅ API deployed at: $API_URL"
echo ""

# Step 7: Deploy Worker Container App
echo "📋 Step 7: Deploying Worker Container App..."
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
    imageTag=latest

WORKER_PRINCIPAL_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-worker \
  --query 'properties.outputs.workerPrincipalId.value' \
  -o tsv)

echo "✅ Worker deployed"
echo ""

# Step 8: Configure RBAC permissions
echo "📋 Step 8: Configuring RBAC permissions for Managed Identities..."

# Get resource IDs
KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)
STORAGE_ID=$(az storage account list -g $RESOURCE_GROUP --query "[0].id" -o tsv)
COSMOS_ID=$(az cosmosdb show -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query id -o tsv)
SB_ID=$(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Assign Key Vault Secrets User to both API and Worker
az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true

# Assign Storage Blob Data Contributor to both
az role assignment create --assignee $API_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true

# Assign Cosmos DB Data Contributor to both
az role assignment create --assignee $API_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true

# Assign Service Bus Data Owner to Worker (for receiving messages)
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Azure Service Bus Data Owner" --scope $SB_ID 2>/dev/null || true

# Assign Service Bus Data Sender to API (for sending messages)
az role assignment create --assignee $API_PRINCIPAL_ID --role "Azure Service Bus Data Sender" --scope $SB_ID 2>/dev/null || true

echo "✅ RBAC permissions configured"
echo ""

# Step 9: Update Static Web App with API URL
echo "📋 Step 9: Getting Static Web App URL..."
SWA_NAME=$(az staticwebapp list -g $RESOURCE_GROUP --query "[0].name" -o tsv)
SWA_URL=$(az staticwebapp show -n $SWA_NAME -g $RESOURCE_GROUP --query "defaultHostname" -o tsv)

echo "✅ Static Web App: https://$SWA_URL"
echo ""

# Step 10: Update API CORS to allow Static Web App
echo "📋 Step 10: Updating API CORS settings..."
# Note: CORS is configured in the Bicep template, but you may need to update it manually
echo "⚠️  Remember to update frontend .env with: NEXT_PUBLIC_API_URL=$API_URL"
echo ""

# Disable ACR admin (best practice - use Managed Identity instead)
echo "📋 Step 11: Disabling ACR admin user (security best practice)..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled false
echo "✅ ACR admin disabled"
echo ""

echo "======================================"
echo "✅ Backend Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployment Summary:"
echo "  API URL: $API_URL"
echo "  Static Web App: https://$SWA_URL"
echo "  Key Vault: $KEY_VAULT_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Update frontend/.env.production with:"
echo "     NEXT_PUBLIC_API_URL=$API_URL"
echo "  2. Update API CORS in backend-api.bicep to allow: https://$SWA_URL"
echo "  3. Test the deployment:"
echo "     - Visit https://$SWA_URL"
echo "     - Upload a transcript file"
echo "     - Monitor job progress"
echo "  4. Check logs:"
echo "     az containerapp logs show -n ca-$APP_NAME-$ENVIRONMENT-api -g $RESOURCE_GROUP --follow"
echo "     az containerapp logs show -n ca-$APP_NAME-$ENVIRONMENT-wrk -g $RESOURCE_GROUP --follow"
echo ""
