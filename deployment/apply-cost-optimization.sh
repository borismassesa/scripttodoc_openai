#!/bin/bash

# Apply Cost Optimization: Scale Container Apps to Zero
# This script updates Container Apps to scale to zero when idle
# Expected savings: 70-85% reduction in compute costs (CA$136 → CA$25-40/month)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Container Apps Cost Optimization${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if required variables are set
if [ -z "$RESOURCE_GROUP" ]; then
    echo -e "${YELLOW}RESOURCE_GROUP not set. Using default: rg-scripttodoc-prod${NC}"
    RESOURCE_GROUP="rg-scripttodoc-prod"
fi

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}ENVIRONMENT not set. Using default: prod${NC}"
    ENVIRONMENT="prod"
fi

if [ -z "$APP_NAME" ]; then
    echo -e "${YELLOW}APP_NAME not set. Using default: scripttodoc${NC}"
    APP_NAME="scripttodoc"
fi

# Get Container Registry name
CONTAINER_REGISTRY=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -z "$CONTAINER_REGISTRY" ]; then
    echo -e "${RED}Error: Could not find Container Registry in resource group ${RESOURCE_GROUP}${NC}"
    exit 1
fi

# Get Container Apps Environment ID
CONTAINER_APPS_ENV=$(az containerapp env list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv 2>/dev/null || echo "")
if [ -z "$CONTAINER_APPS_ENV" ]; then
    echo -e "${RED}Error: Could not find Container Apps Environment in resource group ${RESOURCE_GROUP}${NC}"
    exit 1
fi

# Get Key Vault name
KEY_VAULT=$(az keyvault list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -z "$KEY_VAULT" ]; then
    echo -e "${RED}Error: Could not find Key Vault in resource group ${RESOURCE_GROUP}${NC}"
    exit 1
fi

# Get Service Bus namespace name
SERVICE_BUS_NS=$(az servicebus namespace list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -z "$SERVICE_BUS_NS" ]; then
    echo -e "${RED}Error: Could not find Service Bus namespace in resource group ${RESOURCE_GROUP}${NC}"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Environment: $ENVIRONMENT"
echo "  App Name: $APP_NAME"
echo "  Container Registry: $CONTAINER_REGISTRY"
echo "  Key Vault: $KEY_VAULT"
echo "  Service Bus: $SERVICE_BUS_NS"
echo ""

# Confirm before proceeding
echo -e "${YELLOW}This will update Container Apps to scale to zero when idle.${NC}"
echo -e "${YELLOW}Expected savings: 70-85% reduction in compute costs${NC}"
echo -e "${YELLOW}Note: There will be a 5-30 second cold start when scaling from zero.${NC}"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}Deploying optimized API Container App...${NC}"
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deployment/backend-api.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CONTAINER_APPS_ENV" \
    keyVaultName=$KEY_VAULT \
  --query "properties.outputs" -o json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API Container App updated successfully${NC}"
else
    echo -e "${RED}✗ Failed to update API Container App${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Deploying optimized Worker Container App...${NC}"
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deployment/backend-worker.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CONTAINER_APPS_ENV" \
    keyVaultName=$KEY_VAULT \
    serviceBusNamespaceName=$SERVICE_BUS_NS \
  --query "properties.outputs" -o json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Worker Container App updated successfully${NC}"
else
    echo -e "${RED}✗ Failed to update Worker Container App${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cost Optimization Applied Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Monitor costs in Azure Cost Management (should see reduction in 24-48 hours)"
echo "2. Test application to ensure cold starts are acceptable (5-30 seconds)"
echo "3. Monitor Container Apps metrics to verify scale-to-zero behavior"
echo ""
echo -e "${YELLOW}To revert (if needed):${NC}"
echo "  Change minReplicas back to 1 in backend-api.bicep and backend-worker.bicep"
echo "  Then run this script again"
echo ""
echo -e "${GREEN}Expected Cost Reduction:${NC}"
echo "  Before: CA\$136/month (Container Apps compute)"
echo "  After:  CA\$25-40/month (70-85% savings)"
echo ""
