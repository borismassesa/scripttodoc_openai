#!/bin/bash

# Frontend Deployment Script for Azure Container Apps
# Deploys Next.js frontend as a containerized application

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"
LOCATION="eastus"
# ⭐ FIXED: Use production API URL (matching .env.production)
API_URL="https://ca-scripttodoc-prod-api.delightfuldune-05b8c4e7.eastus.azurecontainerapps.io"

echo "🚀 Deploying Frontend to Azure Container Apps"
echo "==============================================="
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

CAE_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.containerAppsEnvironmentId.value' \
  -o tsv)

echo "✅ Container Registry: $CONTAINER_REGISTRY"
echo "✅ Container Apps Environment ID: ${CAE_ID:0:50}..."
echo ""

# Step 2: Enable admin user on ACR
echo "📋 Step 2: Configuring Container Registry..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled true > /dev/null
echo "✅ ACR admin enabled"
echo ""

# Step 3: Login to ACR
echo "📋 Step 3: Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY
echo "✅ Logged in to ACR"
echo ""

# Step 4: Build and push Frontend image
echo "📋 Step 4: Building and pushing Frontend image (for linux/amd64)..."
echo "⏳ This may take 3-5 minutes (building Next.js app in Docker)..."
echo "   Using API URL: $API_URL"
cd ../frontend
# ⭐ FIXED: Pass API_URL as build argument to bake it into the Next.js bundle
docker buildx build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
  --build-arg NEXT_PUBLIC_ENVIRONMENT="production" \
  -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-frontend:latest \
  -f Dockerfile . \
  --push
echo "✅ Frontend image built and pushed with API URL: $API_URL"
echo ""

# Step 5: Deploy Frontend Container App
echo "📋 Step 5: Deploying Frontend Container App..."
cd ../deployment
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file frontend-containerapp.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    apiUrl="$API_URL" \
    imageTag=latest

FRONTEND_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name frontend-containerapp \
  --query 'properties.outputs.frontendUrl.value' \
  -o tsv)

echo "✅ Frontend deployed at: $FRONTEND_URL"
echo ""

# Step 6: Disable ACR admin (best practice)
echo "📋 Step 6: Disabling ACR admin user (security best practice)..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled false > /dev/null
echo "✅ ACR admin disabled"
echo ""

# Step 7: Update API CORS settings
echo "📋 Step 7: Updating API CORS settings..."
echo "⚠️  You need to update the API CORS to allow your frontend URL"
echo ""

echo "======================================"
echo "✅ Frontend Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployment Summary:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend API URL: $API_URL"
echo ""
echo "📝 Next Steps:"
echo "  1. Visit your application:"
echo "     $FRONTEND_URL"
echo ""
echo "  2. Update API CORS settings:"
echo "     • Edit deployment/backend-api-direct.bicep"
echo "     • Change allowedOrigins from ['*'] to ['$FRONTEND_URL']"
echo "     • Run: cd deployment && ./deploy-backend-with-secrets.sh"
echo ""
echo "  3. Test end-to-end:"
echo "     • Upload a transcript file"
echo "     • Monitor processing in logs"
echo "     • Download generated documentation"
echo ""
echo "🎉 Your full-stack application is now live on Azure!"
echo ""
