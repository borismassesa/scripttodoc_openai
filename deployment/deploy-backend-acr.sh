#!/bin/bash

# Backend Deployment Script using ACR Build (no local Docker needed)
# This script builds Docker images in Azure Container Registry

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"
LOCATION="eastus"

echo "🚀 Starting Backend Deployment (ACR Build)"
echo "=========================================="
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

# Step 2: Build and push API image using ACR Build
echo "📋 Step 2: Building and pushing API image (using ACR Build)..."
echo "⏳ This takes ~3-5 minutes (building in Azure, no local Docker needed)..."
cd ../backend
az acr build \
  --registry $CONTAINER_REGISTRY \
  --image $APP_NAME-api:latest \
  --file Dockerfile \
  .
echo "✅ API image built and pushed"
echo ""

# Step 3: Build and push Worker image using ACR Build
echo "📋 Step 3: Building and pushing Worker image (using ACR Build)..."
echo "⏳ This takes ~3-5 minutes..."
az acr build \
  --registry $CONTAINER_REGISTRY \
  --image $APP_NAME-worker:latest \
  --file Dockerfile.worker \
  .
echo "✅ Worker image built and pushed"
echo ""

cd ../deployment

# Step 4: Deploy API Container App
echo "📋 Step 4: Deploying API Container App..."
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

# Step 5: Deploy Worker Container App
echo "📋 Step 5: Deploying Worker Container App..."
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

# Step 6: Configure RBAC permissions
echo "📋 Step 6: Configuring RBAC permissions for Managed Identities..."

# Get resource IDs
KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)
STORAGE_ID=$(az storage account list -g $RESOURCE_GROUP --query "[0].id" -o tsv)
COSMOS_ID=$(az cosmosdb show -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query id -o tsv)
SB_ID=$(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

echo "Assigning permissions (this may take a minute)..."

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

# Step 7: Get Static Web App URL (if exists)
echo "📋 Step 7: Getting deployment URLs..."
SWA_NAME=$(az staticwebapp list -g $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -n "$SWA_NAME" ]; then
  SWA_URL=$(az staticwebapp show -n $SWA_NAME -g $RESOURCE_GROUP --query "defaultHostname" -o tsv 2>/dev/null || echo "")
  echo "✅ Static Web App: https://$SWA_URL"
else
  echo "⚠️  Static Web App not deployed (will deploy separately)"
fi
echo ""

echo "======================================"
echo "✅ Backend Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployment Summary:"
echo "  API URL: $API_URL"
if [ -n "$SWA_URL" ]; then
  echo "  Static Web App: https://$SWA_URL"
fi
echo "  Key Vault: $KEY_VAULT_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Test API health:"
echo "     curl $API_URL/health"
echo ""
echo "  2. View API logs:"
echo "     az containerapp logs show -n ca-$APP_NAME-$ENVIRONMENT-api -g $RESOURCE_GROUP --follow"
echo ""
echo "  3. View Worker logs:"
echo "     az containerapp logs show -n ca-$APP_NAME-$ENVIRONMENT-wrk -g $RESOURCE_GROUP --follow"
echo ""
echo "  4. Deploy frontend (if not done yet)"
echo ""
echo "🎉 Backend is live and ready!"
echo ""
