#!/bin/bash

# Infrastructure Deployment Script for ScriptToDoc
# This creates all Azure resources needed for the application

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
LOCATION="eastus"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

echo "🏗️  Starting Infrastructure Deployment"
echo "========================================"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Environment: $ENVIRONMENT"
echo ""

# Step 1: Check if logged in to Azure
echo "📋 Step 1: Checking Azure login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run: az login"
    exit 1
fi

SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✅ Logged in to Azure"
echo "   Subscription: $SUBSCRIPTION_NAME"
echo "   ID: $SUBSCRIPTION_ID"
echo ""

# Step 2: Create Resource Group
echo "📋 Step 2: Creating resource group..."
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "⚠️  Resource group already exists, skipping creation"
else
    az group create \
      --name $RESOURCE_GROUP \
      --location $LOCATION \
      --output none
    echo "✅ Resource group created"
fi
echo ""

# Step 3: Deploy Infrastructure
echo "📋 Step 3: Deploying Azure infrastructure..."
echo "⏳ This will take 5-10 minutes (creating ~15 Azure resources)..."
echo ""
echo "Resources being created:"
echo "  • Storage Account (with 3 containers + lifecycle policies)"
echo "  • Cosmos DB (serverless with continuous backup)"
echo "  • Service Bus (with job queue)"
echo "  • Key Vault (with RBAC, soft-delete, purge protection)"
echo "  • Container Registry (for Docker images)"
echo "  • Container Apps Environment (for API and Worker)"
echo "  • Application Insights + Log Analytics"
echo "  • Azure OpenAI (with gpt-4o-mini deployment)"
echo "  • Azure Document Intelligence"
echo "  • Azure Static Web App (for frontend)"
echo ""

az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --template-file azure-infrastructure.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    githubRepoUrl='' \
    githubBranch=main

echo "✅ Infrastructure deployment complete!"
echo ""

# Step 4: Get and display outputs
echo "📋 Step 4: Retrieving deployment outputs..."
echo ""

STORAGE_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.storageAccountName.value' \
  -o tsv)

COSMOS_ENDPOINT=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.cosmosEndpoint.value' \
  -o tsv)

KEY_VAULT_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.keyVaultName.value' \
  -o tsv)

CONTAINER_REGISTRY=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.containerRegistryName.value' \
  -o tsv)

OPENAI_ENDPOINT=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.openAIEndpoint.value' \
  -o tsv)

DI_ENDPOINT=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.documentIntelligenceEndpoint.value' \
  -o tsv)

SWA_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query 'properties.outputs.staticWebAppUrl.value' \
  -o tsv)

echo "======================================"
echo "✅ Infrastructure Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployed Resources:"
echo "  Storage Account:         $STORAGE_NAME"
echo "  Cosmos DB:              $COSMOS_ENDPOINT"
echo "  Key Vault:              $KEY_VAULT_NAME"
echo "  Container Registry:     $CONTAINER_REGISTRY"
echo "  Azure OpenAI:           $OPENAI_ENDPOINT"
echo "  Document Intelligence:  $DI_ENDPOINT"
echo "  Static Web App:         $SWA_URL"
echo ""

# Step 5: Store secrets in Key Vault
echo "📋 Step 5: Storing secrets in Key Vault..."
echo "⚠️  You need to manually add these secrets to Key Vault:"
echo ""
echo "  1. Get Azure OpenAI Key:"
echo "     OPENAI_KEY=\$(az cognitiveservices account keys list -n openai-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query key1 -o tsv)"
echo "     az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-openai-key --value \"\$OPENAI_KEY\""
echo ""
echo "  2. Get Document Intelligence Key:"
echo "     DI_KEY=\$(az cognitiveservices account keys list -n di-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query key1 -o tsv)"
echo "     az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-di-key --value \"\$DI_KEY\""
echo ""
echo "  3. Get Storage Connection String:"
echo "     STORAGE_CONN=\$(az storage account show-connection-string -n $STORAGE_NAME -g $RESOURCE_GROUP --query connectionString -o tsv)"
echo "     az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-storage-connection-string --value \"\$STORAGE_CONN\""
echo ""
echo "  4. Get Cosmos DB Connection String:"
echo "     COSMOS_CONN=\$(az cosmosdb keys list -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --type connection-strings --query 'connectionStrings[0].connectionString' -o tsv)"
echo "     az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-cosmos-connection-string --value \"\$COSMOS_CONN\""
echo ""
echo "  5. Get Service Bus Connection String:"
echo "     SB_CONN=\$(az servicebus namespace authorization-rule keys list --resource-group $RESOURCE_GROUP --namespace-name sb-$APP_NAME-$ENVIRONMENT --name RootManageSharedAccessKey --query primaryConnectionString -o tsv)"
echo "     az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-service-bus-connection-string --value \"\$SB_CONN\""
echo ""

echo "📝 Next Steps:"
echo ""
echo "  1. Store secrets in Key Vault (commands above)"
echo "  2. Deploy backend:"
echo "     ./deploy-backend.sh"
echo "  3. Configure frontend and test end-to-end"
echo ""
echo "💡 Tip: You can view all resources in the Azure Portal:"
echo "   https://portal.azure.com/#@/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/overview"
echo ""
