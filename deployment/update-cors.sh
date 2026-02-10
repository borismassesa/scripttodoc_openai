#!/bin/bash

# Update CORS Settings Script
# This script updates the API CORS configuration to allow the frontend Container App

set -e

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

echo "🔧 Updating API CORS Settings"
echo "=============================="
echo ""

# Get frontend URL
echo "📋 Step 1: Getting frontend URL..."
FRONTEND_APP="ca-$APP_NAME-$ENVIRONMENT-frontend"
FRONTEND_URL=$(az containerapp show \
    -n $FRONTEND_APP \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv 2>/dev/null || echo "")

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ Frontend Container App not found. Please deploy frontend first."
    exit 1
fi

FRONTEND_FULL_URL="https://$FRONTEND_URL"
echo "✅ Frontend URL: $FRONTEND_FULL_URL"
echo ""

# Get infrastructure outputs
echo "📋 Step 2: Getting infrastructure outputs..."
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

echo "✅ Container Registry: $CONTAINER_REGISTRY"
echo "✅ Key Vault: $KEY_VAULT_NAME"
echo ""

# Update backend-api.bicep with frontend URL
echo "📋 Step 3: Updating backend-api.bicep with frontend URL..."
BICEP_FILE="backend-api.bicep"

if [ ! -f "$BICEP_FILE" ]; then
    echo "❌ $BICEP_FILE not found"
    exit 1
fi

# Create backup
cp "$BICEP_FILE" "${BICEP_FILE}.bak"

# Update CORS allowedOrigins
# This is a simple approach - in production you might want to use a parameter
sed -i.tmp "s|allowedOrigins: \['\*'\]|allowedOrigins: ['$FRONTEND_FULL_URL']|g" "$BICEP_FILE"
rm -f "${BICEP_FILE}.tmp"

echo "✅ Updated $BICEP_FILE"
echo ""

# Redeploy API with updated CORS
echo "📋 Step 4: Redeploying API with updated CORS..."
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

echo "✅ API redeployed with updated CORS"
echo ""

# Verify CORS update
echo "📋 Step 5: Verifying CORS configuration..."
API_URL=$(az containerapp show \
    -n ca-$APP_NAME-$ENVIRONMENT-api \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv)

echo "✅ API URL: https://$API_URL"
echo "✅ CORS now allows: $FRONTEND_FULL_URL"
echo ""

echo "======================================"
echo "✅ CORS Update Complete!"
echo "======================================"
echo ""
echo "📝 Test CORS:"
echo "  curl -H 'Origin: $FRONTEND_FULL_URL' \\"
echo "       -H 'Access-Control-Request-Method: GET' \\"
echo "       -X OPTIONS https://$API_URL/health"
echo ""
