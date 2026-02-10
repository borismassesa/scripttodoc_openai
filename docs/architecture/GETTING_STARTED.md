# Getting Started with ScriptToDoc

## Overview

This guide walks you through setting up ScriptToDoc from scratch, from Azure account setup to running your first document generation. Follow these steps in order.

---

## Prerequisites Checklist

### Azure Account Setup

- [ ] **Azure Subscription**
  - Active Azure subscription with contributor access
  - Budget approved (~$300/month for production)
  - Subscription ID noted

- [ ] **Azure Services Access**
  - [ ] Azure OpenAI Service access (requires application)
    - Apply at: https://aka.ms/oai/access
    - Approval typically takes 1-2 business days
  - [ ] Azure Document Intelligence enabled
  - [ ] Ability to create resources in East US or West Europe region

- [ ] **Permissions**
  - [ ] Contributor role on resource group
  - [ ] Can create service principals
  - [ ] Can access Azure Key Vault

### Development Tools

- [ ] **Python 3.11+**
  ```bash
  python --version  # Should be 3.11 or higher
  pip --version
  ```

- [ ] **Node.js 18+**
  ```bash
  node --version    # Should be 18.x or higher
  npm --version
  ```

- [ ] **Docker Desktop**
  ```bash
  docker --version
  docker compose --version
  ```

- [ ] **Azure CLI**
  ```bash
  az --version      # Should be 2.50+
  az login
  az account show   # Verify correct subscription
  ```

- [ ] **Git**
  ```bash
  git --version
  ```

- [ ] **Code Editor**
  - VS Code (recommended) with extensions:
    - Azure Account
    - Azure Resources
    - Python
    - Pylance
    - Docker
    - ES7+ React/Redux/React-Native snippets

---

## Phase 0: Azure Infrastructure Setup

### Step 1: Create Resource Group

```bash
# Set variables
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="rg-scripttodoc-dev"
LOCATION="eastus"

# Set subscription
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Verify
az group show --name $RESOURCE_GROUP
```

**✅ Success Criteria:** Resource group visible in Azure Portal

---

### Step 2: Create Storage Account

```bash
STORAGE_ACCOUNT="stscripttodocdev"  # Must be globally unique, lowercase, no hyphens

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create containers
az storage container create \
  --name uploads \
  --account-name $STORAGE_ACCOUNT \
  --auth-mode login

az storage container create \
  --name documents \
  --account-name $STORAGE_ACCOUNT \
  --auth-mode login

az storage container create \
  --name temp \
  --account-name $STORAGE_ACCOUNT \
  --auth-mode login

# Set lifecycle policy for temp container
cat > lifecycle-policy.json << EOF
{
  "rules": [
    {
      "enabled": true,
      "name": "delete-temp-files",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 1
            }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["temp/"]
        }
      }
    }
  ]
}
EOF

az storage account management-policy create \
  --account-name $STORAGE_ACCOUNT \
  --policy @lifecycle-policy.json

# Get connection string (save for later)
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv
```

**✅ Success Criteria:** Three containers visible in Storage Account

---

### Step 3: Create Cosmos DB

```bash
COSMOS_ACCOUNT="cosmos-scripttodoc-dev"  # Must be globally unique

# Create Cosmos DB account (serverless)
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --locations regionName=$LOCATION \
  --capabilities EnableServerless \
  --default-consistency-level Session

# Create database
az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name scripttodoc

# Create jobs container
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --database-name scripttodoc \
  --name jobs \
  --partition-key-path "/id" \
  --throughput 400

# Create cache container with TTL
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --database-name scripttodoc \
  --name processing_cache \
  --partition-key-path "/id" \
  --default-ttl 86400 \
  --throughput 400

# Get connection string (save for later)
az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  --output tsv
```

**✅ Success Criteria:** Cosmos DB account with 2 containers visible in portal

---

### Step 4: Create Service Bus

```bash
SERVICE_BUS_NAMESPACE="scripttodoc-sb-dev"  # Must be globally unique

# Create Service Bus namespace
az servicebus namespace create \
  --name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard

# Create queue
az servicebus queue create \
  --name scripttodoc-jobs \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --max-delivery-count 5 \
  --default-message-time-to-live P0DT0H30M0S \
  --enable-dead-lettering-on-message-expiration true

# Get connection string (save for later)
az servicebus namespace authorization-rule keys list \
  --resource-group $RESOURCE_GROUP \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString \
  --output tsv
```

**✅ Success Criteria:** Service Bus namespace with queue visible in portal

---

### Step 5: Create Azure Document Intelligence

```bash
DOCUMENT_INTELLIGENCE="scripttodoc-di-dev"

# Create Document Intelligence resource
az cognitiveservices account create \
  --name $DOCUMENT_INTELLIGENCE \
  --resource-group $RESOURCE_GROUP \
  --kind FormRecognizer \
  --sku S0 \
  --location $LOCATION \
  --yes

# Get endpoint and key (save for later)
az cognitiveservices account show \
  --name $DOCUMENT_INTELLIGENCE \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint \
  --output tsv

az cognitiveservices account keys list \
  --name $DOCUMENT_INTELLIGENCE \
  --resource-group $RESOURCE_GROUP \
  --query key1 \
  --output tsv
```

**✅ Success Criteria:** Document Intelligence resource visible in portal

---

### Step 6: Create Azure OpenAI Service

> ⚠️ **Important:** You must have Azure OpenAI access approved before this step

```bash
OPENAI_SERVICE="scripttodoc-openai-dev"

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location $LOCATION \
  --yes

# Create deployment (gpt-4o-mini)
az cognitiveservices account deployment create \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Get endpoint and key (save for later)
az cognitiveservices account show \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint \
  --output tsv

az cognitiveservices account keys list \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --query key1 \
  --output tsv
```

**✅ Success Criteria:** OpenAI resource with deployment visible in Azure OpenAI Studio

---

### Step 7: Create Key Vault

```bash
KEY_VAULT="kv-scripttodoc-dev"  # Must be globally unique, 3-24 chars

# Create Key Vault
az keyvault create \
  --name $KEY_VAULT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization false

# Store secrets (use the connection strings/keys from previous steps)
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "AzureStorageConnectionString" \
  --value "YOUR_STORAGE_CONNECTION_STRING"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "CosmosDBConnectionString" \
  --value "YOUR_COSMOS_CONNECTION_STRING"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "ServiceBusConnectionString" \
  --value "YOUR_SERVICE_BUS_CONNECTION_STRING"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "DocumentIntelligenceEndpoint" \
  --value "YOUR_DI_ENDPOINT"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "DocumentIntelligenceKey" \
  --value "YOUR_DI_KEY"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "AzureOpenAIEndpoint" \
  --value "YOUR_OPENAI_ENDPOINT"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "AzureOpenAIKey" \
  --value "YOUR_OPENAI_KEY"

# Grant yourself access
USER_OBJECT_ID=$(az ad signed-in-user show --query id --output tsv)

az keyvault set-policy \
  --name $KEY_VAULT \
  --object-id $USER_OBJECT_ID \
  --secret-permissions get list set delete
```

**✅ Success Criteria:** All secrets visible in Key Vault in portal

---

### Step 8: Create Application Insights

```bash
APP_INSIGHTS="appi-scripttodoc-dev"

# Create Application Insights
az monitor app-insights component create \
  --app $APP_INSIGHTS \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Get instrumentation key (save for later)
az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv

# Get connection string (save for later)
az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv
```

**✅ Success Criteria:** Application Insights resource visible in portal

---

### Step 9: Create Container Registry

```bash
CONTAINER_REGISTRY="acrscripttodocdev"  # Must be globally unique, alphanumeric only

# Create Azure Container Registry
az acr create \
  --name $CONTAINER_REGISTRY \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --admin-enabled true

# Get admin credentials
az acr credential show \
  --name $CONTAINER_REGISTRY \
  --resource-group $RESOURCE_GROUP
```

**✅ Success Criteria:** Container Registry visible in portal

---

### Step 10: Create Container Apps Environment

```bash
CONTAINER_APP_ENV="scripttodoc-env-dev"

# Create Container Apps Environment
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Link to Application Insights (optional)
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)

az containerapp env dapr-component set \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --dapr-component-name appinsights \
  --yaml "
componentType: middleware.http.appsinsights
version: v1
metadata:
- name: instrumentationKey
  value: $INSTRUMENTATION_KEY
"
```

**✅ Success Criteria:** Container Apps Environment visible in portal

---

## Summary of Azure Resources

After completing Phase 0, you should have:

| Resource Type | Name | Purpose |
|---------------|------|---------|
| Resource Group | `rg-scripttodoc-dev` | Contains all resources |
| Storage Account | `stscripttodocdev` | File storage |
| Cosmos DB | `cosmos-scripttodoc-dev` | Job state database |
| Service Bus | `scripttodoc-sb-dev` | Message queue |
| Document Intelligence | `scripttodoc-di-dev` | Structure extraction |
| Azure OpenAI | `scripttodoc-openai-dev` | Content generation |
| Key Vault | `kv-scripttodoc-dev` | Secrets management |
| Application Insights | `appi-scripttodoc-dev` | Monitoring |
| Container Registry | `acrscripttodocdev` | Docker images |
| Container Apps Environment | `scripttodoc-env-dev` | App hosting |

**Total Setup Time:** ~30-45 minutes  
**Estimated Monthly Cost (idle):** ~$5-10

---

## Phase 1: Local Development Setup

### Step 1: Clone Repository (When Available)

```bash
# Clone repository
git clone https://github.com/yourorg/scripttodoc.git
cd scripttodoc

# Create environment file
cp .env.template .env
```

### Step 2: Configure Environment Variables

Edit `.env` file:

```bash
# Azure Resource Endpoints (from Phase 0)
AZURE_SUBSCRIPTION_ID="your-subscription-id"
AZURE_RESOURCE_GROUP="rg-scripttodoc-dev"
AZURE_LOCATION="eastus"

# Storage
AZURE_STORAGE_ACCOUNT="stscripttodocdev"
AZURE_STORAGE_CONNECTION_STRING="..."

# Cosmos DB
COSMOS_DB_ENDPOINT="https://cosmos-scripttodoc-dev.documents.azure.com:443/"
COSMOS_DB_CONNECTION_STRING="..."

# Service Bus
SERVICE_BUS_NAMESPACE="scripttodoc-sb-dev.servicebus.windows.net"
SERVICE_BUS_CONNECTION_STRING="..."

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://scripttodoc-di-dev.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="..."

# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://scripttodoc-openai-dev.openai.azure.com/"
AZURE_OPENAI_KEY="..."
AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING="..."

# Configuration
USE_AZURE_DI=true
USE_OPENAI=true
MIN_STEPS=3
TARGET_STEPS=8
TONE="Professional"
AUDIENCE="General"
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import azure.ai.documentintelligence; print('✓ All dependencies installed')"
```

### Step 4: Frontend Setup

```bash
cd ../frontend/transcript-trainer-ui

# Install dependencies
npm install

# Verify installation
npm run build
```

### Step 5: Run Tests (When Implemented)

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd ../frontend/transcript-trainer-ui
npm test
```

---

## Phase 2: First Run

### Step 1: Test Azure Connections

Create `test_azure_connections.py`:

```python
import os
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.servicebus import ServiceBusClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

def test_blob_storage():
    client = BlobServiceClient.from_connection_string(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    )
    containers = list(client.list_containers())
    print(f"✓ Blob Storage: {len(containers)} containers found")

def test_cosmos_db():
    client = CosmosClient.from_connection_string(
        os.environ["COSMOS_DB_CONNECTION_STRING"]
    )
    database = client.get_database_client("scripttodoc")
    containers = list(database.list_containers())
    print(f"✓ Cosmos DB: {len(containers)} containers found")

def test_service_bus():
    client = ServiceBusClient.from_connection_string(
        os.environ["SERVICE_BUS_CONNECTION_STRING"]
    )
    print("✓ Service Bus: Connected")

def test_document_intelligence():
    client = DocumentIntelligenceClient(
        endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"])
    )
    print("✓ Azure Document Intelligence: Connected")

if __name__ == "__main__":
    test_blob_storage()
    test_cosmos_db()
    test_service_bus()
    test_document_intelligence()
    print("\n✅ All Azure services connected successfully!")
```

Run test:
```bash
python test_azure_connections.py
```

### Step 2: Process First Transcript

Create `sample_transcript.txt`:

```
Today we'll walk through creating a resource in Azure.

First, you need to open the Azure portal at portal.azure.com.
Sign in with your organizational credentials.

Once you're signed in, you'll see the dashboard.
Click on Create a resource in the top left corner.

In the search box, type Resource Group and select it from the results.
Click Create to start the creation process.

Enter a name for your resource group, such as my-first-rg.
Choose your subscription from the dropdown.
Select a region, like East US.

Click Review + Create at the bottom.
After validation passes, click Create.

Your resource group will be created in a few seconds.
```

Run processing:
```bash
# (Once pipeline is implemented)
python -m script_to_doc.pipeline \
  --input sample_transcript.txt \
  --output ./output \
  --tone Professional \
  --min-steps 5 \
  --target-steps 8
```

**✅ Success Criteria:** Document generated at `./output/sample_transcript_training.docx`

---

## Troubleshooting

### Common Issues

**Issue: Azure OpenAI access denied**
```
Solution: Verify you have approval for Azure OpenAI
- Check: https://aka.ms/oai/access
- Wait for approval email (1-2 business days)
```

**Issue: Container Apps deployment fails**
```
Solution: Check Docker Desktop is running
- docker ps  # Should show running containers
- Restart Docker Desktop if needed
```

**Issue: Cosmos DB connection timeout**
```
Solution: Check firewall settings
- Azure Portal → Cosmos DB → Networking
- Add your IP address to allowed list
```

**Issue: Document Intelligence "Invalid image"**
```
Solution: Check file format and size
- Supported: PDF, JPEG, PNG, BMP, TIFF
- Max size: 500 MB
- Resolution: 50-300 DPI recommended
```

**Issue: Python dependencies conflict**
```
Solution: Use fresh virtual environment
- deactivate
- rm -rf venv
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
```

---

## Next Steps

Once you've completed setup:

1. **Read Implementation Phases** - [2_IMPLEMENTATION_PHASES.md](./2_IMPLEMENTATION_PHASES.md)
2. **Review Architecture** - [1_SYSTEM_ARCHITECTURE.md](./1_SYSTEM_ARCHITECTURE.md)
3. **Start Phase 1 Development** - Core pipeline implementation
4. **Set up CI/CD** - GitHub Actions for automated deployment

---

## Verification Checklist

Before starting development, verify:

- [ ] All Azure resources created and accessible
- [ ] All secrets stored in Key Vault
- [ ] Environment variables configured locally
- [ ] Python environment set up with all dependencies
- [ ] Node.js environment set up with all dependencies
- [ ] Docker Desktop running
- [ ] Azure CLI authenticated
- [ ] Test connections script passes
- [ ] Can access Azure Portal and see all resources
- [ ] Cost alerts configured (optional but recommended)

---

**🎉 You're ready to start building ScriptToDoc!**

*Estimated setup time: 1-2 hours*  
*Next: Begin Phase 1 implementation*

