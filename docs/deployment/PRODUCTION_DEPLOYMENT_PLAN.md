# Production Deployment Plan: ScriptToDoc on Vercel + Azure

**Version**: 1.0
**Date**: December 11, 2025
**Target Go-Live**: [To be determined]
**Deployment Model**: Vercel (Frontend) + Azure (Backend)

---

## 📋 Executive Summary

This document provides a **step-by-step deployment plan** for deploying ScriptToDoc to production with:
- **Vercel** hosting the Next.js frontend
- **Azure** hosting all backend services and data
- **Estimated timeline**: 2-3 weeks
- **Team required**: 2-3 people (1 frontend, 1-2 backend/DevOps)

### Deployment Phases

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 0: Preparation** | 2-3 days | Prerequisites, accounts, planning |
| **Phase 1: Azure Infrastructure** | 3-4 days | Setup all Azure resources |
| **Phase 2: CI/CD Pipeline** | 2-3 days | Automate deployments |
| **Phase 3: Application Deployment** | 2-3 days | Deploy backend and frontend |
| **Phase 4: Testing & Validation** | 2-3 days | End-to-end testing |
| **Phase 5: Go-Live** | 1 day | Production launch |
| **Phase 6: Post-Launch** | Ongoing | Monitoring and support |

**Total Timeline**: 12-17 days (~2-3 weeks)

---

## 🎯 Pre-Deployment Checklist

### Prerequisites (Complete Before Starting)

**Accounts & Access:**
- [ ] Azure subscription with Owner or Contributor role
- [ ] Vercel account (Team or Pro plan recommended)
- [ ] GitHub repository access (with admin permissions)
- [ ] Azure DevOps or GitHub Actions enabled
- [ ] Domain name purchased (optional, for custom domain)

**Technical Requirements:**
- [ ] Azure CLI installed (`az --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Git configured with SSH keys

**Documentation:**
- [ ] Security architecture approved by IG
- [ ] Cost estimates approved by finance
- [ ] Deployment plan reviewed by team
- [ ] Rollback procedures documented

**Team Roles:**
- [ ] **Deployment Lead**: [Name] - Overall coordination
- [ ] **Backend Engineer**: [Name] - Azure infrastructure, FastAPI
- [ ] **Frontend Engineer**: [Name] - Vercel deployment, Next.js
- [ ] **DevOps Engineer**: [Name] - CI/CD, monitoring (optional)

---

## 📍 Phase 0: Preparation (Days 1-2)

### Day 1: Environment Planning

**Morning: Define Environments**

We'll create 3 environments:

| Environment | Purpose | Azure RG | Vercel Project | Cost/Month |
|-------------|---------|----------|----------------|------------|
| **Development** | Local development | `rg-scripttodoc-dev` | `scripttodoc-dev` | $50-100 |
| **Staging** | Pre-production testing | `rg-scripttodoc-staging` | `scripttodoc-staging` | $100-150 |
| **Production** | Live application | `rg-scripttodoc-prod` | `scripttodoc-prod` | $100-200 |

**Afternoon: Create Resource Naming Convention**

```
Format: {resource-type}-{app-name}-{environment}

Examples:
- Container Apps API:     ca-scripttodoc-api-prod
- Container Apps Worker:  ca-scripttodoc-worker-prod
- Cosmos DB:             cosmos-scripttodoc-prod
- Storage Account:       stscripttodocprod (no hyphens, max 24 chars)
- Key Vault:             kv-scripttodoc-prod
- Container Registry:    crscripttodocprod
- OpenAI:                openai-scripttodoc-prod
- Document Intelligence: di-scripttodoc-prod
- Service Bus:           sb-scripttodoc-prod
- App Insights:          ai-scripttodoc-prod
- Resource Group:        rg-scripttodoc-prod
```

**Evening: Create Configuration Files**

Create deployment configuration for each environment:

```bash
# Create deployment config directory
mkdir -p deployment/environments

# Create config files
touch deployment/environments/dev.env
touch deployment/environments/staging.env
touch deployment/environments/prod.env
```

**deployment/environments/prod.env** (template - fill in actual values later):
```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=
AZURE_LOCATION=eastus2
AZURE_RESOURCE_GROUP=rg-scripttodoc-prod

# Azure OpenAI
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-01

# Application Configuration
APP_NAME=scripttodoc
ENVIRONMENT=production
MIN_STEPS=3
TARGET_STEPS=8
DATA_RETENTION_DAYS=90

# Vercel Configuration
VERCEL_PROJECT_NAME=scripttodoc-prod
VERCEL_TEAM_ID=

# Domain (if using custom domain)
CUSTOM_DOMAIN=scripttodoc.company.com
API_DOMAIN=api.scripttodoc.company.com
```

---

### Day 2: Azure Subscription Setup

**Morning: Create Azure AD App Registration (for authentication)**

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create Azure AD B2C tenant (one-time setup)
# Note: This must be done in Azure Portal (cannot be automated)
# 1. Go to portal.azure.com
# 2. Create new resource → Azure Active Directory B2C
# 3. Create new tenant: scripttodoc-b2c
# 4. Link to subscription

# After B2C tenant created, create app registration
az ad app create \
  --display-name "ScriptToDoc Production" \
  --sign-in-audience AzureADandPersonalMicrosoftAccount \
  --web-redirect-uris "https://scripttodoc.vercel.app/auth/callback"

# Save the Application (client) ID - you'll need this!
# OUTPUT: "appId": "abc-123-def-456" ← COPY THIS
```

**Afternoon: Setup GitHub Secrets**

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
Repository Secrets:
- AZURE_CREDENTIALS          (Service Principal JSON)
- AZURE_SUBSCRIPTION_ID      (Your subscription ID)
- AZURE_TENANT_ID           (Your tenant ID)
- VERCEL_TOKEN              (Vercel API token)
- VERCEL_ORG_ID             (Vercel organization ID)
- VERCEL_PROJECT_ID_PROD    (Vercel project ID for production)
- VERCEL_PROJECT_ID_STAGING (Vercel project ID for staging)
```

**Get AZURE_CREDENTIALS** (Service Principal):
```bash
# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "GitHub-Actions-ScriptToDoc" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth

# Output (copy entire JSON):
# {
#   "clientId": "...",
#   "clientSecret": "...",
#   "subscriptionId": "...",
#   "tenantId": "...",
#   "activeDirectoryEndpointUrl": "...",
#   "resourceManagerEndpointUrl": "..."
# }
```

**Get VERCEL_TOKEN**:
1. Go to https://vercel.com/account/tokens
2. Create new token: "GitHub Actions - ScriptToDoc"
3. Copy token (you'll only see it once!)

**Evening: Install Required Tools**

```bash
# Install Azure CLI extensions
az extension add --name containerapp
az extension add --name application-insights

# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link projects
cd frontend
vercel link  # Follow prompts to link to existing project

# Get Vercel project details
vercel project ls
# Copy Project ID and Org ID for GitHub secrets
```

---

## 🏗️ Phase 1: Azure Infrastructure Setup (Days 3-6)

### Day 3: Core Infrastructure

**Step 1: Create Infrastructure-as-Code (Bicep/Terraform)**

I'll provide a complete Bicep template for all Azure resources:

Create `deployment/azure-infrastructure.bicep`:

```bicep
@description('Environment name (e.g., dev, staging, prod)')
param environment string = 'prod'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Application name')
param appName string = 'scripttodoc'

// Variables
var resourcePrefix = '${appName}-${environment}'
var storageAccountName = replace('st${appName}${environment}', '-', '')  // Remove hyphens

// Resource Group is created separately via Azure CLI

// ==================== Storage Account ====================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: take(storageAccountName, 24)  // Max 24 characters
  location: location
  sku: {
    name: 'Standard_LRS'  // Locally redundant storage
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false  // No public access!
    encryption: {
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Blob containers
resource uploadsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/uploads'
  properties: {
    publicAccess: 'None'  // Private
  }
}

resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/documents'
  properties: {
    publicAccess: 'None'  // Private
  }
}

resource tempContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/temp'
  properties: {
    publicAccess: 'None'  // Private
  }
}

// Lifecycle management policy (auto-delete old files)
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = {
  name: '${storageAccount.name}/default'
  properties: {
    policy: {
      rules: [
        {
          name: 'delete-temp-files'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['temp/']
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: 1
                }
              }
            }
          }
        }
        {
          name: 'delete-old-documents'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['documents/', 'uploads/']
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: 90
                }
              }
            }
          }
        }
      ]
    }
  }
}

// ==================== Cosmos DB ====================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: 'cosmos-${resourcePrefix}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'  // Serverless billing
      }
    ]
    backupPolicy: {
      type: 'Continuous'  // Point-in-time restore
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    minimalTlsVersion: 'Tls12'
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: appName
  properties: {
    resource: {
      id: appName
    }
  }
}

resource jobsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
  name: 'jobs'
  properties: {
    resource: {
      id: 'jobs'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 7776000  // 90 days in seconds
    }
  }
}

// ==================== Service Bus ====================
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-${resourcePrefix}'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    minimumTlsVersion: '1.2'
  }
}

resource jobQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: '${appName}-jobs'
  properties: {
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'PT30M'  // 30 minutes
    deadLetteringOnMessageExpiration: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    requiresDuplicateDetection: true
  }
}

// ==================== Key Vault ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${resourcePrefix}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    enableRbacAuthorization: true  // Use RBAC instead of access policies
    networkAcls: {
      defaultAction: 'Allow'  // MVP: Allow all, POST-MVP: Restrict to VNet
      bypass: 'AzureServices'
    }
  }
}

// ==================== Container Registry ====================
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: replace('cr${resourcePrefix}', '-', '')  // Remove hyphens
  location: location
  sku: {
    name: 'Basic'  // Upgrade to Standard/Premium for production if needed
  }
  properties: {
    adminUserEnabled: false  // Use Managed Identity instead
  }
}

// ==================== Container Apps Environment ====================
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${resourcePrefix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// ==================== Log Analytics Workspace ====================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${resourcePrefix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
  }
}

// ==================== Application Insights ====================
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-${resourcePrefix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    RetentionInDays: 90
  }
}

// ==================== Azure OpenAI ====================
resource openAIAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'openai-${resourcePrefix}'
  location: 'eastus'  // Check availability in your region
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'openai-${resourcePrefix}'
    publicNetworkAccess: 'Enabled'
  }
}

// OpenAI deployment (GPT-4o-mini)
resource openAIDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIAccount
  name: 'gpt-4o-mini'
  sku: {
    name: 'Standard'
    capacity: 10  // Tokens per minute (thousands)
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
  }
}

// ==================== Document Intelligence ====================
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'di-${resourcePrefix}'
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'di-${resourcePrefix}'
    publicNetworkAccess: 'Enabled'
  }
}

// ==================== Outputs ====================
output storageAccountName string = storageAccount.name
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosConnectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
output serviceBusConnectionString string = listKeys('${serviceBusNamespace.id}/AuthorizationRules/RootManageSharedAccessKey', serviceBusNamespace.apiVersion).primaryConnectionString
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output openAIEndpoint string = openAIAccount.properties.endpoint
output openAIKey string = openAIAccount.listKeys().key1
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output documentIntelligenceKey string = documentIntelligence.listKeys().key1
```

**Step 2: Deploy Infrastructure**

```bash
# Set variables
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="rg-scripttodoc-prod"
LOCATION="eastus2"
ENVIRONMENT="prod"

# Login and set subscription
az login
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Deploy infrastructure
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deployment/azure-infrastructure.bicep \
  --parameters environment=$ENVIRONMENT \
  --parameters location=$LOCATION \
  --parameters appName=scripttodoc

# Save outputs to file
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-infrastructure \
  --query properties.outputs \
  > deployment/outputs-prod.json

# This takes about 10-15 minutes to complete
```

**Expected Output:**
```
✅ Storage Account created: stscripttodocprod
✅ Cosmos DB created: cosmos-scripttodoc-prod
✅ Service Bus created: sb-scripttodoc-prod
✅ Key Vault created: kv-scripttodoc-prod
✅ Container Registry created: crscripttodocprod
✅ Container Apps Environment created: cae-scripttodoc-prod
✅ Application Insights created: ai-scripttodoc-prod
✅ Azure OpenAI created: openai-scripttodoc-prod
✅ Document Intelligence created: di-scripttodoc-prod
```

---

### Day 4: Store Secrets in Key Vault

**Step 1: Extract Connection Strings**

```bash
# Parse outputs
KEYVAULT_NAME=$(jq -r '.keyVaultName.value' deployment/outputs-prod.json)
STORAGE_CONNECTION_STRING=$(jq -r '.storageConnectionString.value' deployment/outputs-prod.json)
COSMOS_CONNECTION_STRING=$(jq -r '.cosmosConnectionString.value' deployment/outputs-prod.json)
SERVICEBUS_CONNECTION_STRING=$(jq -r '.serviceBusConnectionString.value' deployment/outputs-prod.json)
OPENAI_KEY=$(jq -r '.openAIKey.value' deployment/outputs-prod.json)
OPENAI_ENDPOINT=$(jq -r '.openAIEndpoint.value' deployment/outputs-prod.json)
DI_KEY=$(jq -r '.documentIntelligenceKey.value' deployment/outputs-prod.json)
DI_ENDPOINT=$(jq -r '.documentIntelligenceEndpoint.value' deployment/outputs-prod.json)
APPINSIGHTS_CONNECTION_STRING=$(jq -r '.applicationInsightsConnectionString.value' deployment/outputs-prod.json)

# Azure AD B2C settings (from earlier setup)
AZURE_AD_CLIENT_ID="your-azure-ad-client-id"
AZURE_AD_CLIENT_SECRET="your-azure-ad-client-secret"
AZURE_AD_TENANT_ID="your-tenant-id"
```

**Step 2: Store Secrets in Key Vault**

```bash
# Login to Azure (if not already)
az login

# Set Key Vault name
KEYVAULT_NAME="kv-scripttodoc-prod"

# Add all secrets
az keyvault secret set --vault-name $KEYVAULT_NAME --name "storage-connection-string" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "cosmos-connection-string" --value "$COSMOS_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "servicebus-connection-string" --value "$SERVICEBUS_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-openai-key" --value "$OPENAI_KEY"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-openai-endpoint" --value "$OPENAI_ENDPOINT"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-di-key" --value "$DI_KEY"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-di-endpoint" --value "$DI_ENDPOINT"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "appinsights-connection-string" --value "$APPINSIGHTS_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-ad-client-id" --value "$AZURE_AD_CLIENT_ID"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-ad-client-secret" --value "$AZURE_AD_CLIENT_SECRET"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "azure-ad-tenant-id" --value "$AZURE_AD_TENANT_ID"

echo "✅ All secrets stored in Key Vault"
```

**Step 3: Verify Secrets**

```bash
# List all secrets
az keyvault secret list --vault-name $KEYVAULT_NAME --query "[].name" -o table

# Expected output:
# Name
# ---------------------------------
# storage-connection-string
# cosmos-connection-string
# servicebus-connection-string
# azure-openai-key
# azure-openai-endpoint
# azure-di-key
# azure-di-endpoint
# appinsights-connection-string
# azure-ad-client-id
# azure-ad-client-secret
# azure-ad-tenant-id
```

---

### Day 5: Build and Push Docker Images

**Step 1: Create Dockerfiles**

Create `backend/Dockerfile`:

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `backend/Dockerfile.worker`:

```dockerfile
# Worker Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Copy application code
COPY . .

# Run worker
CMD ["python", "workers/processor.py"]
```

**Step 2: Build and Push Images**

```bash
# Get container registry name
ACR_NAME=$(jq -r '.containerRegistryName.value' deployment/outputs-prod.json)
ACR_LOGIN_SERVER=$(jq -r '.containerRegistryLoginServer.value' deployment/outputs-prod.json)

# Login to Azure Container Registry
az acr login --name $ACR_NAME

# Build and push API image
cd backend
docker build -t $ACR_LOGIN_SERVER/scripttodoc-api:latest -f Dockerfile .
docker push $ACR_LOGIN_SERVER/scripttodoc-api:latest

# Build and push worker image
docker build -t $ACR_LOGIN_SERVER/scripttodoc-worker:latest -f Dockerfile.worker .
docker push $ACR_LOGIN_SERVER/scripttodoc-worker:latest

echo "✅ Docker images pushed to ACR"
```

---

### Day 6: Deploy Container Apps

**Step 1: Create Container Apps Deployment Script**

Create `deployment/deploy-container-apps.sh`:

```bash
#!/bin/bash
set -e

# Variables
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="scripttodoc-prod"
LOCATION="eastus2"
ACR_NAME="crscripttodocprod"
KEYVAULT_NAME="kv-scripttodoc-prod"

# Get Container Apps Environment ID
CA_ENV_ID=$(az containerapp env show \
  --name cae-scripttodoc-prod \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Get Key Vault URI
KEYVAULT_URI="https://${KEYVAULT_NAME}.vault.azure.net/"

# Deploy API Container App
echo "Deploying API Container App..."
az containerapp create \
  --name ca-scripttodoc-api-prod \
  --resource-group $RESOURCE_GROUP \
  --environment $CA_ENV_ID \
  --image ${ACR_NAME}.azurecr.io/scripttodoc-api:latest \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 10 \
  --ingress external \
  --target-port 8000 \
  --transport http \
  --env-vars \
    ENVIRONMENT=production \
    AZURE_KEY_VAULT_URI=$KEYVAULT_URI \
  --system-assigned

# Get API Container App identity
API_IDENTITY=$(az containerapp show \
  --name ca-scripttodoc-api-prod \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId -o tsv)

# Grant API Container App access to Key Vault
az role assignment create \
  --assignee $API_IDENTITY \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME

# Grant API Container App access to ACR
az role assignment create \
  --assignee $API_IDENTITY \
  --role "AcrPull" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME

# Deploy Worker Container App
echo "Deploying Worker Container App..."
az containerapp create \
  --name ca-scripttodoc-worker-prod \
  --resource-group $RESOURCE_GROUP \
  --environment $CA_ENV_ID \
  --image ${ACR_NAME}.azurecr.io/scripttodoc-worker:latest \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-identity system \
  --cpu 1 \
  --memory 2Gi \
  --min-replicas 0 \
  --max-replicas 5 \
  --env-vars \
    ENVIRONMENT=production \
    AZURE_KEY_VAULT_URI=$KEYVAULT_URI \
  --system-assigned

# Get Worker Container App identity
WORKER_IDENTITY=$(az containerapp show \
  --name ca-scripttodoc-worker-prod \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId -o tsv)

# Grant Worker Container App access to Key Vault
az role assignment create \
  --assignee $WORKER_IDENTITY \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME

# Grant Worker Container App access to ACR
az role assignment create \
  --assignee $WORKER_IDENTITY \
  --role "AcrPull" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME

echo "✅ Container Apps deployed successfully"

# Get API URL
API_URL=$(az containerapp show \
  --name ca-scripttodoc-api-prod \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "API URL: https://$API_URL"
```

**Step 2: Run Deployment**

```bash
chmod +x deployment/deploy-container-apps.sh
./deployment/deploy-container-apps.sh
```

**Expected Output:**
```
✅ API Container App deployed: ca-scripttodoc-api-prod
✅ Worker Container App deployed: ca-scripttodoc-worker-prod
✅ API URL: https://ca-scripttodoc-api-prod.{region}.azurecontainerapps.io
```

---

## 🚀 Phase 2: CI/CD Pipeline Setup (Days 7-9)

### Day 7: GitHub Actions - Backend CI/CD

Create `.github/workflows/backend-deploy.yml`:

```yaml
name: Deploy Backend to Azure

on:
  push:
    branches:
      - main
      - staging
    paths:
      - 'backend/**'
      - '.github/workflows/backend-deploy.yml'
  workflow_dispatch:

env:
  AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  ACR_NAME: crscripttodocprod

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set environment based on branch
        id: set-env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "ENVIRONMENT=prod" >> $GITHUB_OUTPUT
            echo "RESOURCE_GROUP=rg-scripttodoc-prod" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
            echo "ENVIRONMENT=staging" >> $GITHUB_OUTPUT
            echo "RESOURCE_GROUP=rg-scripttodoc-staging" >> $GITHUB_OUTPUT
          fi

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to Azure Container Registry
        run: |
          az acr login --name ${{ env.ACR_NAME }}

      - name: Build and push API image
        run: |
          cd backend
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:${{ github.sha }} -f Dockerfile .
          docker tag ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:${{ github.sha }} ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:latest
          docker push ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:${{ github.sha }}
          docker push ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:latest

      - name: Build and push Worker image
        run: |
          cd backend
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:${{ github.sha }} -f Dockerfile.worker .
          docker tag ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:${{ github.sha }} ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:latest
          docker push ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:${{ github.sha }}
          docker push ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:latest

      - name: Deploy API to Container Apps
        run: |
          az containerapp update \
            --name ca-scripttodoc-api-${{ steps.set-env.outputs.ENVIRONMENT }} \
            --resource-group ${{ steps.set-env.outputs.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-api:${{ github.sha }}

      - name: Deploy Worker to Container Apps
        run: |
          az containerapp update \
            --name ca-scripttodoc-worker-${{ steps.set-env.outputs.ENVIRONMENT }} \
            --resource-group ${{ steps.set-env.outputs.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/scripttodoc-worker:${{ github.sha }}

      - name: Run health check
        run: |
          API_URL=$(az containerapp show \
            --name ca-scripttodoc-api-${{ steps.set-env.outputs.ENVIRONMENT }} \
            --resource-group ${{ steps.set-env.outputs.RESOURCE_GROUP }} \
            --query properties.configuration.ingress.fqdn -o tsv)

          echo "Checking API health at https://$API_URL/health"
          curl -f https://$API_URL/health || exit 1

      - name: Notify on success
        if: success()
        run: |
          echo "✅ Deployment successful to ${{ steps.set-env.outputs.ENVIRONMENT }}"

      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ Deployment failed to ${{ steps.set-env.outputs.ENVIRONMENT }}"
```

---

### Day 8: GitHub Actions - Frontend CI/CD

Create `.github/workflows/frontend-deploy.yml`:

```yaml
name: Deploy Frontend to Vercel

on:
  push:
    branches:
      - main
      - staging
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-deploy.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Pull Vercel Environment Information (Production)
        if: github.ref == 'refs/heads/main'
        run: |
          cd frontend
          vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Pull Vercel Environment Information (Staging)
        if: github.ref == 'refs/heads/staging'
        run: |
          cd frontend
          vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project Artifacts (Production)
        if: github.ref == 'refs/heads/main'
        run: |
          cd frontend
          vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project Artifacts (Staging)
        if: github.ref == 'refs/heads/staging'
        run: |
          cd frontend
          vercel build --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel (Production)
        if: github.ref == 'refs/heads/main'
        run: |
          cd frontend
          vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel (Staging)
        if: github.ref == 'refs/heads/staging'
        run: |
          cd frontend
          vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }}

      - name: Notify on success
        if: success()
        run: |
          echo "✅ Frontend deployed successfully"

      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ Frontend deployment failed"
```

---

### Day 9: Setup Vercel Projects

**Step 1: Create Vercel Projects**

```bash
# Login to Vercel
vercel login

# Create staging project
cd frontend
vercel --name scripttodoc-staging

# Create production project
vercel --name scripttodoc-prod

# Link projects
vercel link
```

**Step 2: Configure Vercel Environment Variables**

Go to Vercel Dashboard → Project Settings → Environment Variables

**Production Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://ca-scripttodoc-api-prod.{region}.azurecontainerapps.io
NEXT_PUBLIC_AZURE_AD_CLIENT_ID=your-azure-ad-client-id
NEXT_PUBLIC_AZURE_AD_TENANT_ID=your-tenant-id
NEXT_PUBLIC_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/{tenant-id}
NEXT_PUBLIC_AZURE_AD_REDIRECT_URI=https://scripttodoc-prod.vercel.app/auth/callback
NEXT_PUBLIC_ENVIRONMENT=production
```

**Staging Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://ca-scripttodoc-api-staging.{region}.azurecontainerapps.io
NEXT_PUBLIC_AZURE_AD_CLIENT_ID=your-azure-ad-client-id-staging
NEXT_PUBLIC_AZURE_AD_TENANT_ID=your-tenant-id
NEXT_PUBLIC_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/{tenant-id}
NEXT_PUBLIC_AZURE_AD_REDIRECT_URI=https://scripttodoc-staging.vercel.app/auth/callback
NEXT_PUBLIC_ENVIRONMENT=staging
```

**Step 3: Configure Vercel Security Headers**

Create `frontend/vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains; preload"
        },
        {
          "key": "Permissions-Policy",
          "value": "geolocation=(), microphone=(), camera=()"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.azurecontainerapps.io https://login.microsoftonline.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        }
      ]
    }
  ]
}
```

---

## ✅ Phase 3: Testing & Validation (Days 10-12)

### Day 10: Smoke Tests

**Step 1: Backend Health Check**

```bash
# Get API URL
API_URL=$(az containerapp show \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --query properties.configuration.ingress.fqdn -o tsv)

# Test health endpoint
curl https://$API_URL/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}

# Test docs endpoint
curl https://$API_URL/docs
# Should return HTML (OpenAPI docs)
```

**Step 2: Frontend Smoke Test**

```bash
# Get Vercel deployment URL
vercel ls --scope your-team

# Visit URL in browser
open https://scripttodoc-prod.vercel.app

# Check:
# ✅ Page loads
# ✅ No console errors
# ✅ Security headers present (check in DevTools → Network)
```

**Step 3: Authentication Test**

1. Visit frontend URL
2. Click "Sign In" → Should redirect to Azure AD B2C
3. Login with test account
4. Should redirect back to frontend with token
5. Check cookie in DevTools → Application → Cookies
   - Should see `__Secure-next-auth.session-token`
   - Should have `HttpOnly`, `Secure`, `SameSite=Lax` flags

---

### Day 11: End-to-End Tests

Create `tests/e2e/test_production.py`:

```python
#!/usr/bin/env python3
"""
Production E2E Test Suite
Run with: python tests/e2e/test_production.py
"""

import requests
import os
import time
from pathlib import Path

API_URL = os.environ.get("API_URL", "https://ca-scripttodoc-api-prod.{region}.azurecontainerapps.io")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")  # Get from authenticated session

def test_health():
    """Test 1: Health endpoint"""
    print("Test 1: Health check...")
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_auth_required():
    """Test 2: Authentication required"""
    print("Test 2: Auth required...")
    response = requests.post(f"{API_URL}/api/process")
    assert response.status_code == 401  # Unauthorized
    print("✅ Auth protection works")

def test_upload_document():
    """Test 3: Upload document"""
    print("Test 3: Upload document...")

    # Create test file
    test_file = Path("test_transcript.txt")
    test_file.write_text("This is a test meeting transcript about Azure deployment.")

    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    files = {"file": open(test_file, "rb")}
    data = {"tone": "Professional", "target_steps": 5}

    response = requests.post(
        f"{API_URL}/api/process",
        headers=headers,
        files=files,
        data=data
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    print(f"✅ Document uploaded, job_id: {job_id}")

    # Clean up
    test_file.unlink()

    return job_id

def test_check_status(job_id):
    """Test 4: Check job status"""
    print(f"Test 4: Check status for {job_id}...")

    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # Poll for completion (max 3 minutes)
    for i in range(36):  # 36 * 5s = 3 minutes
        response = requests.get(
            f"{API_URL}/api/status/{job_id}",
            headers=headers
        )

        assert response.status_code == 200
        status = response.json()["status"]

        if status == "completed":
            print(f"✅ Job completed in {i*5} seconds")
            return True
        elif status == "failed":
            print(f"❌ Job failed: {response.json()}")
            return False

        time.sleep(5)

    print("❌ Job timed out")
    return False

def test_download_document(job_id):
    """Test 5: Download document"""
    print(f"Test 5: Download document for {job_id}...")

    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    response = requests.get(
        f"{API_URL}/api/documents/{job_id}",
        headers=headers
    )

    assert response.status_code == 200
    document_url = response.json()["download_url"]

    # Download the document
    doc_response = requests.get(document_url)
    assert doc_response.status_code == 200
    assert len(doc_response.content) > 0

    print(f"✅ Document downloaded, size: {len(doc_response.content)} bytes")

if __name__ == "__main__":
    print("=" * 60)
    print("Running Production E2E Tests")
    print("=" * 60)

    # Check prerequisites
    if not AUTH_TOKEN:
        print("❌ Error: AUTH_TOKEN environment variable not set")
        print("Please authenticate and export AUTH_TOKEN")
        exit(1)

    try:
        # Run tests
        test_health()
        test_auth_required()
        job_id = test_upload_document()
        if test_check_status(job_id):
            test_download_document(job_id)

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
```

**Run E2E Tests:**

```bash
# Set environment variables
export API_URL="https://ca-scripttodoc-api-prod.{region}.azurecontainerapps.io"
export AUTH_TOKEN="your-jwt-token-here"

# Run tests
python tests/e2e/test_production.py
```

---

### Day 12: Security Validation

**Checklist:**

```bash
# 1. Check HTTPS enforcement
curl -I http://scripttodoc-prod.vercel.app
# Should redirect to https://

# 2. Check security headers
curl -I https://scripttodoc-prod.vercel.app
# Look for:
# ✅ Strict-Transport-Security
# ✅ X-Frame-Options: DENY
# ✅ X-Content-Type-Options: nosniff
# ✅ Content-Security-Policy

# 3. Check CORS
curl -X OPTIONS https://$API_URL/api/process \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST"
# Should be blocked (no CORS headers)

# 4. Check auth required
curl https://$API_URL/api/process
# Should return 401 Unauthorized

# 5. Check Key Vault access
az keyvault secret show \
  --vault-name kv-scripttodoc-prod \
  --name azure-openai-key
# Should succeed (you have access)

# 6. Check Managed Identity works
# Login to Container App console and test:
az containerapp exec \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --command /bin/bash

# Inside container:
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
# Should return access token ✅
```

---

## 🎉 Phase 4: Go-Live (Day 13)

### Pre-Launch Checklist

**Infrastructure:**
- [ ] All Azure resources deployed successfully
- [ ] Container Apps running and healthy
- [ ] Managed Identity configured for all services
- [ ] Key Vault secrets populated
- [ ] CORS configured correctly
- [ ] Application Insights receiving telemetry

**Application:**
- [ ] Backend API responding to health checks
- [ ] Worker processing jobs successfully
- [ ] Frontend deployed to Vercel
- [ ] Azure AD B2C authentication working
- [ ] End-to-end tests passing

**Security:**
- [ ] No secrets in code repository
- [ ] Security headers configured on Vercel
- [ ] HTTPS enforced everywhere
- [ ] Auth required for all API endpoints
- [ ] User data isolation verified

**Monitoring:**
- [ ] Application Insights dashboard created
- [ ] Basic alerts configured
- [ ] Error logging working
- [ ] Audit logging enabled

**Documentation:**
- [ ] Deployment runbook completed
- [ ] User guide published
- [ ] Support contact information shared
- [ ] Rollback procedures documented

---

### Go-Live Steps

**8:00 AM: Final Checks**

```bash
# 1. Check all services healthy
./scripts/check-health.sh

# 2. Run smoke tests
python tests/e2e/test_production.py

# 3. Verify monitoring
# Open Application Insights dashboard
# Confirm telemetry is flowing

# 4. Check error logs (should be empty or minimal)
az monitor log-analytics query \
  --workspace $(az monitor log-analytics workspace show \
    --resource-group rg-scripttodoc-prod \
    --workspace-name log-scripttodoc-prod \
    --query customerId -o tsv) \
  --analytics-query "traces | where severityLevel >= 3 | order by timestamp desc | take 10"
```

**9:00 AM: Announce Launch**

Send email to pilot users:

```
Subject: ScriptToDoc is now live!

Hi team,

ScriptToDoc is now available for use at: https://scripttodoc-prod.vercel.app

Features:
- Upload meeting transcripts
- AI-generated training documents
- Real-time progress tracking
- Secure Azure storage

Support:
- Email: support@yourcompany.com
- Slack: #scripttodoc-support

Please report any issues immediately.

Thanks,
The ScriptToDoc Team
```

**10:00 AM - 5:00 PM: Monitor Closely**

```bash
# Watch Container Apps logs in real-time
az containerapp logs show \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --follow

# Monitor Application Insights metrics
# Open Azure Portal → Application Insights → Live Metrics

# Check for errors every hour
watch -n 3600 '
  az monitor log-analytics query \
    --workspace $WORKSPACE_ID \
    --analytics-query "traces | where severityLevel >= 3 | summarize count() by bin(timestamp, 1h)"
'
```

**End of Day: Review Metrics**

```bash
# Generate launch day report
./scripts/generate-metrics-report.sh

# Metrics to review:
# - Total users
# - Total jobs processed
# - Average processing time
# - Error rate
# - API response times
```

---

## 📊 Phase 5: Post-Launch (Days 14+)

### Day 14: Monitoring Setup

**Create Application Insights Dashboard:**

1. Go to Azure Portal → Application Insights
2. Create new dashboard: "ScriptToDoc Production"
3. Add charts:
   - Request rate (requests/min)
   - Response time (avg, p95)
   - Failed requests (%)
   - Active users
   - Job processing time

**Setup Alerts:**

```bash
# Alert 1: High error rate
az monitor metrics alert create \
  --name "High Error Rate" \
  --resource-group rg-scripttodoc-prod \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-scripttodoc-prod/providers/Microsoft.Insights/components/ai-scripttodoc-prod \
  --condition "count requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-id /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-scripttodoc-prod/providers/microsoft.insights/actionGroups/ops-team

# Alert 2: Slow response time
az monitor metrics alert create \
  --name "Slow Response Time" \
  --resource-group rg-scripttodoc-prod \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-scripttodoc-prod/providers/Microsoft.Insights/components/ai-scripttodoc-prod \
  --condition "avg requests/duration > 5000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-id /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-scripttodoc-prod/providers/microsoft.insights/actionGroups/ops-team
```

---

### Ongoing: Maintenance Tasks

**Daily:**
- [ ] Check Application Insights for errors
- [ ] Review user feedback
- [ ] Monitor costs in Azure Cost Management

**Weekly:**
- [ ] Review performance metrics
- [ ] Update documentation based on user questions
- [ ] Review security logs for anomalies
- [ ] Deploy updates (if any)

**Monthly:**
- [ ] Review and optimize costs
- [ ] Update dependencies (npm, pip packages)
- [ ] Rotate API keys (if using keys instead of Managed Identity)
- [ ] Backup configuration files

**Quarterly:**
- [ ] Security audit
- [ ] Performance review
- [ ] User satisfaction survey
- [ ] Plan new features

---

## 🔄 Rollback Procedures

### Scenario 1: Bad Deployment

**If deployment fails or introduces bugs:**

```bash
# Option A: Rollback to previous image (fast)
az containerapp update \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --image crscripttodocprod.azurecr.io/scripttodoc-api:PREVIOUS_SHA

# Option B: Redeploy specific version
az containerapp update \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --image crscripttodocprod.azurecr.io/scripttodoc-api:v1.2.3

# Verify health after rollback
curl https://$API_URL/health
```

**For Vercel:**

```bash
# List deployments
vercel ls scripttodoc-prod

# Promote previous deployment to production
vercel promote <deployment-url> --scope your-team
```

---

### Scenario 2: Data Issue

**If Cosmos DB data is corrupted:**

```bash
# Restore from point-in-time (within last 7 days)
az cosmosdb sql database restore \
  --account-name cosmos-scripttodoc-prod \
  --resource-group rg-scripttodoc-prod \
  --name scripttodoc \
  --restore-timestamp "2025-12-10T10:00:00Z"
```

---

### Scenario 3: Total Failure

**If entire environment needs to be rebuilt:**

```bash
# 1. Deploy infrastructure from scratch
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/azure-infrastructure.bicep

# 2. Restore secrets to Key Vault
./scripts/restore-secrets.sh

# 3. Redeploy Container Apps
./deployment/deploy-container-apps.sh

# 4. Restore data from backup
az cosmosdb sql database restore ...

# 5. Verify and test
python tests/e2e/test_production.py
```

---

## 📞 Support & Contact

**Deployment Team:**
- **Lead**: [Name] - [Email] - [Phone]
- **Backend**: [Name] - [Email]
- **Frontend**: [Name] - [Email]
- **DevOps**: [Name] - [Email]

**Escalation:**
- **IG/Security**: [Name] - [Email]
- **Infrastructure**: [Name] - [Email]
- **Management**: [Name] - [Email]

**On-Call Schedule:**
- Week 1: [Name]
- Week 2: [Name]
- Rotation: Every 2 weeks

**Communication Channels:**
- Slack: #scripttodoc-ops
- Email: ops-scripttodoc@company.com
- Incident Management: [Tool]

---

## 📝 Appendix

### A. Useful Commands

```bash
# Check API logs
az containerapp logs show \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --follow

# Check worker logs
az containerapp logs show \
  --name ca-scripttodoc-worker-prod \
  --resource-group rg-scripttodoc-prod \
  --follow

# Scale up/down manually
az containerapp update \
  --name ca-scripttodoc-api-prod \
  --resource-group rg-scripttodoc-prod \
  --min-replicas 2 \
  --max-replicas 20

# Check Cosmos DB usage
az cosmosdb show \
  --name cosmos-scripttodoc-prod \
  --resource-group rg-scripttodoc-prod \
  --query "{usage: documentEndpoint}"

# Check costs
az consumption usage list \
  --start-date 2025-12-01 \
  --end-date 2025-12-11 \
  | jq '[.[] | select(.instanceName | contains("scripttodoc"))] | group_by(.meterName) | map({meter: .[0].meterName, cost: map(.cost) | add})'
```

---

### B. Troubleshooting Guide

**Problem: Container App not starting**

```bash
# Check logs
az containerapp logs show --name ca-scripttodoc-api-prod --resource-group rg-scripttodoc-prod

# Common issues:
# - Missing environment variables → Check Key Vault
# - Image pull failure → Check Managed Identity has AcrPull role
# - Port mismatch → Verify targetPort=8000
```

**Problem: Authentication failing**

```bash
# Verify Azure AD B2C configuration
# Check redirect URI matches exactly
# Verify client ID and tenant ID are correct
```

**Problem: High latency**

```bash
# Check if scaling is needed
az containerapp show --name ca-scripttodoc-api-prod --resource-group rg-scripttodoc-prod --query "properties.template.scale"

# Increase replicas if needed
az containerapp update --name ca-scripttodoc-api-prod --resource-group rg-scripttodoc-prod --min-replicas 3
```

---

**Document Status**: Ready for Execution
**Next Action**: Begin Phase 0 (Preparation)
**Timeline**: 2-3 weeks to production
**Estimated Effort**: 80-100 hours

**Sign-off:**
- [ ] Deployment Lead: ________________ Date: _______
- [ ] Backend Engineer: ________________ Date: _______
- [ ] Frontend Engineer: ________________ Date: _______
- [ ] DevOps Engineer: ________________ Date: _______
