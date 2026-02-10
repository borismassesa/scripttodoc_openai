#!/bin/bash

# Check Deployment State Script
# This script checks the current deployment state and identifies what needs to be deployed

set -e

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

echo "🔍 Checking Deployment State"
echo "============================"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Check if resource group exists
echo "📋 Step 1: Checking resource group..."
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Resource group exists"
    LOCATION=$(az group show --name $RESOURCE_GROUP --query location -o tsv)
    echo "   Location: $LOCATION"
else
    echo "⚠️  Resource group does not exist"
    echo "   Will be created during infrastructure deployment"
fi
echo ""

# Check infrastructure deployment
echo "📋 Step 2: Checking infrastructure deployment..."
if az deployment group show --resource-group $RESOURCE_GROUP --name azure-infrastructure &> /dev/null; then
    echo "✅ Infrastructure deployment found"
    
    # Get key resources
    CONTAINER_REGISTRY=$(az deployment group show \
        --resource-group $RESOURCE_GROUP \
        --name azure-infrastructure \
        --query 'properties.outputs.containerRegistryName.value' \
        -o tsv 2>/dev/null || echo "")
    
    KEY_VAULT_NAME=$(az deployment group show \
        --resource-group $RESOURCE_GROUP \
        --name azure-infrastructure \
        --query 'properties.outputs.keyVaultName.value' \
        -o tsv 2>/dev/null || echo "")
    
    if [ -n "$CONTAINER_REGISTRY" ]; then
        echo "   Container Registry: $CONTAINER_REGISTRY"
    fi
    if [ -n "$KEY_VAULT_NAME" ]; then
        echo "   Key Vault: $KEY_VAULT_NAME"
    fi
else
    echo "⚠️  Infrastructure not deployed"
    echo "   Run: ./deploy-infrastructure.sh"
fi
echo ""

# Check Key Vault secrets
echo "📋 Step 3: Checking Key Vault secrets..."
if [ -n "$KEY_VAULT_NAME" ] && az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    REQUIRED_SECRETS=(
        "azure-openai-key"
        "azure-openai-endpoint"
        "azure-di-key"
        "azure-di-endpoint"
        "azure-storage-connection-string"
        "azure-cosmos-connection-string"
        "azure-service-bus-connection-string"
    )
    
    MISSING_SECRETS=0
    for SECRET in "${REQUIRED_SECRETS[@]}"; do
        if az keyvault secret show --vault-name $KEY_VAULT_NAME --name $SECRET &> /dev/null; then
            echo "   ✅ $SECRET"
        else
            echo "   ❌ $SECRET (missing)"
            MISSING_SECRETS=$((MISSING_SECRETS + 1))
        fi
    done
    
    if [ $MISSING_SECRETS -eq 0 ]; then
        echo "✅ All required secrets present"
    else
        echo "⚠️  $MISSING_SECRETS secret(s) missing"
        echo "   Run: ./store-secrets.sh"
    fi
else
    echo "⚠️  Key Vault not found or not accessible"
fi
echo ""

# Check Container Apps
echo "📋 Step 4: Checking Container Apps..."
API_APP="ca-$APP_NAME-$ENVIRONMENT-api"
WORKER_APP="ca-$APP_NAME-$ENVIRONMENT-wrk"
FRONTEND_APP="ca-$APP_NAME-$ENVIRONMENT-frontend"

if az containerapp show --name $API_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    API_URL=$(az containerapp show --name $API_APP --resource-group $RESOURCE_GROUP \
        --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "")
    echo "✅ API Container App: $API_APP"
    if [ -n "$API_URL" ]; then
        echo "   URL: https://$API_URL"
    fi
else
    echo "⚠️  API Container App not deployed: $API_APP"
fi

if az containerapp show --name $WORKER_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Worker Container App: $WORKER_APP"
else
    echo "⚠️  Worker Container App not deployed: $WORKER_APP"
fi

if az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP \
        --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "")
    echo "✅ Frontend Container App: $FRONTEND_APP"
    if [ -n "$FRONTEND_URL" ]; then
        echo "   URL: https://$FRONTEND_URL"
    fi
else
    echo "⚠️  Frontend Container App not deployed: $FRONTEND_APP"
fi
echo ""

# Check Docker images in ACR
echo "📋 Step 5: Checking Docker images in Container Registry..."
if [ -n "$CONTAINER_REGISTRY" ] && az acr repository list --name $CONTAINER_REGISTRY &> /dev/null; then
    REPOS=$(az acr repository list --name $CONTAINER_REGISTRY -o tsv 2>/dev/null || echo "")
    
    if echo "$REPOS" | grep -q "$APP_NAME-api"; then
        echo "✅ API image exists: $APP_NAME-api"
    else
        echo "⚠️  API image missing: $APP_NAME-api"
    fi
    
    if echo "$REPOS" | grep -q "$APP_NAME-worker"; then
        echo "✅ Worker image exists: $APP_NAME-worker"
    else
        echo "⚠️  Worker image missing: $APP_NAME-worker"
    fi
    
    if echo "$REPOS" | grep -q "$APP_NAME-frontend"; then
        echo "✅ Frontend image exists: $APP_NAME-frontend"
    else
        echo "⚠️  Frontend image missing: $APP_NAME-frontend"
    fi
else
    echo "⚠️  Container Registry not accessible or not found"
fi
echo ""

# Summary
echo "=================================================="
echo "📊 Deployment State Summary"
echo ""
echo "Next steps based on current state:"
echo ""

if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "1. Deploy infrastructure: ./deploy-infrastructure.sh"
elif ! az deployment group show --resource-group $RESOURCE_GROUP --name azure-infrastructure &> /dev/null; then
    echo "1. Deploy infrastructure: ./deploy-infrastructure.sh"
elif [ $MISSING_SECRETS -gt 0 ] 2>/dev/null; then
    echo "1. Store secrets: ./store-secrets.sh"
elif ! az containerapp show --name $API_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "1. Deploy backend: ./deploy-backend.sh"
elif ! az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "1. Deploy frontend: ./deploy-frontend-containerapp.sh"
else
    echo "✅ All components appear to be deployed!"
    echo ""
    if [ -n "$FRONTEND_URL" ]; then
        echo "🌐 Frontend URL: https://$FRONTEND_URL"
    fi
    if [ -n "$API_URL" ]; then
        echo "🔌 API URL: https://$API_URL"
    fi
fi
echo ""
