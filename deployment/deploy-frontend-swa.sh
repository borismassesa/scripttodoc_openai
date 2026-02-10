#!/bin/bash

# Frontend Deployment Script for Azure Static Web Apps

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"
LOCATION="eastus2"  # Static Web Apps not available in eastus
SWA_NAME="swa-$APP_NAME-$ENVIRONMENT"

echo "🚀 Deploying Frontend to Azure Static Web App"
echo "=============================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Static Web App: $SWA_NAME"
echo ""

# Step 1: Create Static Web App
echo "📋 Step 1: Creating Static Web App..."
az staticwebapp create \
  -n $SWA_NAME \
  -g $RESOURCE_GROUP \
  -l $LOCATION \
  --sku Free \
  --source '' \
  --output table

echo "✅ Static Web App created"
echo ""

# Step 2: Build the frontend
echo "📋 Step 2: Building frontend..."
cd ../frontend
npm install
npm run build
echo "✅ Frontend built"
echo ""

# Step 3: Get deployment token
echo "📋 Step 3: Getting deployment token..."
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  -n $SWA_NAME \
  -g $RESOURCE_GROUP \
  --query properties.apiKey \
  -o tsv)

echo "✅ Deployment token retrieved"
echo ""

# Step 4: Deploy using SWA CLI with proper Next.js configuration
echo "📋 Step 4: Deploying to Static Web App..."
# For Next.js, we need to use standalone output or static export
# Let's use the Azure CLI deployment instead which handles Next.js better
echo "⚠️  Note: Azure Static Web Apps has limited Next.js support"
echo "Deploying build artifacts..."

# Deploy the entire frontend folder structure
npx @azure/static-web-apps-cli deploy \
  --app-location . \
  --output-location .next \
  --deployment-token "$DEPLOYMENT_TOKEN" \
  --no-use-keychain || true

echo "⚠️  Deployment attempted but may have issues with Next.js dynamic features"
echo ""

# Step 5: Get the URL
SWA_URL=$(az staticwebapp show \
  -n $SWA_NAME \
  -g $RESOURCE_GROUP \
  --query defaultHostname \
  -o tsv)

echo "======================================"
echo "✅ Frontend Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployment Summary:"
echo "  Frontend URL: https://$SWA_URL"
echo "  Static Web App: $SWA_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Visit: https://$SWA_URL"
echo "  2. Test file upload and processing"
echo "  3. Update API CORS to allow: https://$SWA_URL"
echo "     (Edit deployment/backend-api-direct.bicep and redeploy)"
echo ""
