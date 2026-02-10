# Azure Services Setup Guide
## End-to-End Testing Configuration

**Purpose**: Configure all Azure services required for the ScriptToDoc platform to enable complete end-to-end testing of the file conversion feature.

**Status**: 🔧 Configuration Required
**Date**: December 3, 2025

---

## 📋 Overview

Currently, your `.env` file has placeholder values for Azure services. This guide will help you set up each service and obtain the real configuration values.

### Current Status

```bash
# ✅ Already Configured
AZURE_OPENAI_ENDPOINT=https://openai-scripttodoc-dev.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-06
AZURE_OPENAI_KEY=your-azure-openai-key-here

# ⏳ Needs Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-di-endpoint-here
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-di-key-here
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_COSMOS_ENDPOINT=your-cosmos-endpoint
AZURE_COSMOS_KEY=your-cosmos-key
AZURE_SERVICE_BUS_CONNECTION_STRING=your-service-bus-connection-string
```

---

## 🎯 Required Services

| Service | Purpose | Priority | Estimated Cost/Month |
|---------|---------|----------|---------------------|
| **Azure Storage Account** | Store generated documents and converted files | 🔴 Critical | $1-5 |
| **Azure Cosmos DB** | Store job metadata and user data | 🔴 Critical | $24+ (can use free tier) |
| **Azure Document Intelligence** | OCR and document processing (if needed) | 🟡 Optional | $0-50 |
| **Azure Service Bus** | Background job queue | 🟡 Optional | $0.05+ (can use free tier) |

**Note**: Azure OpenAI is already configured and working! 🎉

---

## 🚀 Quick Start (Essential Services Only)

If you want to get started quickly with just the file conversion feature, you only need:

1. **Azure Storage Account** (for storing documents)
2. **Azure Cosmos DB** (for job tracking)

Document Intelligence and Service Bus are optional for basic testing.

---

## 📦 Service 1: Azure Storage Account

### What It's Used For
- Store generated DOCX documents
- Cache converted PDF and PPTX files
- Provide SAS URLs for secure downloads

### Setup Steps

#### Option A: Using Azure Portal (Recommended for Beginners)

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your Azure account

2. **Create Storage Account**
   - Click "Create a resource"
   - Search for "Storage Account"
   - Click "Create"

3. **Configure Basic Settings**
   ```
   Resource Group: scripttodoc-dev (create new if needed)
   Storage Account Name: scripttodocdev (must be globally unique, lowercase, no special chars)
   Region: East US (or your preferred region)
   Performance: Standard
   Redundancy: Locally-redundant storage (LRS) - cheapest option for dev
   ```

4. **Review and Create**
   - Click "Review + Create"
   - Click "Create"
   - Wait for deployment to complete (1-2 minutes)

5. **Get Connection String**
   - Go to your new storage account
   - In left menu, click "Access keys" under "Security + networking"
   - Copy **Connection string** from "key1"
   - This is your `AZURE_STORAGE_CONNECTION_STRING`

6. **Create Containers**
   - In left menu, click "Containers" under "Data storage"
   - Click "+ Container"
   - Create three containers:
     - Name: `transcripts` (Private access)
     - Name: `documents` (Private access)
     - Name: `temp` (Private access)

#### Option B: Using Azure CLI (Recommended for Advanced Users)

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="scripttodoc-dev"
STORAGE_ACCOUNT="scripttodocdev"  # Must be globally unique
LOCATION="eastus"

# Create resource group if it doesn't exist
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --output tsv

# Create containers
az storage container create --name transcripts --account-name $STORAGE_ACCOUNT
az storage container create --name documents --account-name $STORAGE_ACCOUNT
az storage container create --name temp --account-name $STORAGE_ACCOUNT
```

### Update .env File

```bash
AZURE_STORAGE_ACCOUNT_NAME=scripttodocdev
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=scripttodocdev;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net
```

### Verify Setup

```bash
# Test connection
python -c "
from azure.storage.blob import BlobServiceClient
import os

conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service = BlobServiceClient.from_connection_string(conn_str)

# List containers
containers = blob_service.list_containers()
print('✅ Connected to Azure Storage!')
print('Containers:', [c.name for c in containers])
"
```

**Expected Output:**
```
✅ Connected to Azure Storage!
Containers: ['transcripts', 'documents', 'temp']
```

---

## 🗄️ Service 2: Azure Cosmos DB

### What It's Used For
- Store job metadata (job_id, status, timestamps)
- Store user data
- Track document generation progress

### Setup Steps

#### Option A: Using Azure Portal

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com

2. **Create Cosmos DB Account**
   - Click "Create a resource"
   - Search for "Azure Cosmos DB"
   - Click "Create"
   - Choose **"Azure Cosmos DB for NoSQL"**

3. **Configure Basic Settings**
   ```
   Resource Group: scripttodoc-dev
   Account Name: scripttodoc-cosmos-dev (must be globally unique)
   Location: East US (same as storage account)
   Capacity mode: Serverless (cheapest for dev/test)
   ```

4. **Review and Create**
   - Click "Review + Create"
   - Click "Create"
   - Wait for deployment (3-5 minutes)

5. **Create Database and Container**
   - Go to your new Cosmos DB account
   - Click "Data Explorer" in left menu
   - Click "New Database"
   - Database ID: `scripttodoc`
   - Click "OK"
   - Click "New Container"
   - Database ID: Use existing `scripttodoc`
   - Container ID: `jobs`
   - Partition key: `/user_id`
   - Click "OK"

6. **Get Connection Details**
   - Click "Keys" in left menu
   - Copy **URI** - this is your `AZURE_COSMOS_ENDPOINT`
   - Copy **PRIMARY KEY** - this is your `AZURE_COSMOS_KEY`

#### Option B: Using Azure CLI

```bash
# Set variables
COSMOS_ACCOUNT="scripttodoc-cosmos-dev"  # Must be globally unique
DATABASE_NAME="scripttodoc"
CONTAINER_NAME="jobs"

# Create Cosmos DB account (serverless for cost efficiency)
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --locations regionName=$LOCATION \
  --capabilities EnableServerless

# Create database
az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name $DATABASE_NAME

# Create container
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --database-name $DATABASE_NAME \
  --name $CONTAINER_NAME \
  --partition-key-path "/user_id"

# Get endpoint
az cosmosdb show \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query documentEndpoint \
  --output tsv

# Get key
az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query primaryMasterKey \
  --output tsv
```

### Update .env File

```bash
AZURE_COSMOS_ENDPOINT=https://scripttodoc-cosmos-dev.documents.azure.com:443/
AZURE_COSMOS_KEY=YOUR_PRIMARY_KEY_HERE
```

### Verify Setup

```bash
# Test connection
python -c "
from azure.cosmos import CosmosClient
import os

endpoint = os.getenv('AZURE_COSMOS_ENDPOINT')
key = os.getenv('AZURE_COSMOS_KEY')

client = CosmosClient(endpoint, key)
database = client.get_database_client('scripttodoc')
container = database.get_container_client('jobs')

print('✅ Connected to Azure Cosmos DB!')
print('Database:', database.id)
print('Container:', container.id)
"
```

**Expected Output:**
```
✅ Connected to Azure Cosmos DB!
Database: scripttodoc
Container: jobs
```

---

## 🔍 Service 3: Azure Document Intelligence (Optional)

### What It's Used For
- OCR for scanned documents
- Extract structured data from PDFs
- **Note**: Currently not required for file conversion feature

### Do You Need This?
- ❌ **NO** if you're only uploading text transcripts
- ✅ **YES** if you want to support scanned documents or PDFs

### Setup Steps (If Needed)

#### Option A: Using Azure Portal

1. **Create Document Intelligence Resource**
   - Go to https://portal.azure.com
   - Click "Create a resource"
   - Search for "Document Intelligence"
   - Click "Create"

2. **Configure Settings**
   ```
   Resource Group: scripttodoc-dev
   Region: East US
   Name: scripttodoc-di-dev
   Pricing Tier: Free F0 (20 calls/min, 500 calls/month) or S0 (15 calls/sec)
   ```

3. **Get Keys**
   - Go to your resource
   - Click "Keys and Endpoint"
   - Copy **Endpoint** and **Key 1**

#### Option B: Using Azure CLI

```bash
# Create Document Intelligence resource
az cognitiveservices account create \
  --name scripttodoc-di-dev \
  --resource-group $RESOURCE_GROUP \
  --kind FormRecognizer \
  --sku F0 \
  --location $LOCATION \
  --yes

# Get endpoint
az cognitiveservices account show \
  --name scripttodoc-di-dev \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint \
  --output tsv

# Get key
az cognitiveservices account keys list \
  --name scripttodoc-di-dev \
  --resource-group $RESOURCE_GROUP \
  --query key1 \
  --output tsv
```

### Update .env File

```bash
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://scripttodoc-di-dev.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=YOUR_KEY_HERE
```

**Or leave as placeholders if not needed:**
```bash
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=not-configured
AZURE_DOCUMENT_INTELLIGENCE_KEY=not-configured
```

---

## 🚌 Service 4: Azure Service Bus (Optional)

### What It's Used For
- Queue background jobs
- Handle async document processing
- **Note**: Currently not required for basic functionality

### Do You Need This?
- ❌ **NO** for simple development/testing
- ✅ **YES** for production with high concurrency
- ✅ **YES** for distributed worker architecture

### Setup Steps (If Needed)

#### Option A: Using Azure Portal

1. **Create Service Bus Namespace**
   - Go to https://portal.azure.com
   - Click "Create a resource"
   - Search for "Service Bus"
   - Click "Create"

2. **Configure Settings**
   ```
   Resource Group: scripttodoc-dev
   Namespace name: scripttodoc-bus-dev (must be globally unique)
   Location: East US
   Pricing Tier: Basic (cheapest, sufficient for dev)
   ```

3. **Create Queue**
   - Go to your Service Bus namespace
   - Click "Queues" in left menu
   - Click "+ Queue"
   - Name: `document-jobs`
   - Click "Create"

4. **Get Connection String**
   - Click "Shared access policies" in left menu
   - Click "RootManageSharedAccessKey"
   - Copy **Primary Connection String**

#### Option B: Using Azure CLI

```bash
# Create Service Bus namespace
az servicebus namespace create \
  --name scripttodoc-bus-dev \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic

# Create queue
az servicebus queue create \
  --name document-jobs \
  --namespace-name scripttodoc-bus-dev \
  --resource-group $RESOURCE_GROUP

# Get connection string
az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name scripttodoc-bus-dev \
  --resource-group $RESOURCE_GROUP \
  --query primaryConnectionString \
  --output tsv
```

### Update .env File

```bash
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://scripttodoc-bus-dev.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY_HERE
```

**Or leave as placeholder if not needed:**
```bash
AZURE_SERVICE_BUS_CONNECTION_STRING=not-configured
```

---

## ✅ Complete .env File Example

After setting up all services, your `.env` file should look like this:

```bash
# Azure OpenAI Configuration (Already configured ✅)
AZURE_OPENAI_ENDPOINT=https://openai-scripttodoc-dev.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-06
AZURE_OPENAI_KEY=your-azure-openai-key-here

# Azure Storage Account (Critical 🔴)
AZURE_STORAGE_ACCOUNT_NAME=scripttodocdev
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=scripttodocdev;AccountKey=AbC123...==;EndpointSuffix=core.windows.net

# Azure Cosmos DB (Critical 🔴)
AZURE_COSMOS_ENDPOINT=https://scripttodoc-cosmos-dev.documents.azure.com:443/
AZURE_COSMOS_KEY=XyZ789...==

# Azure Document Intelligence (Optional 🟡)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://scripttodoc-di-dev.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=DeF456...

# Azure Service Bus (Optional 🟡)
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://scripttodoc-bus-dev.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=GhI012...
```

---

## 🧪 End-to-End Testing

### Test Script

Once all services are configured, run this comprehensive test:

```bash
cd backend

# Test all Azure connections
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

print('🧪 Testing Azure Services...\n')

# Test 1: Azure OpenAI (should already work)
print('1️⃣ Testing Azure OpenAI...')
try:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    print('   ✅ Azure OpenAI: Connected')
except Exception as e:
    print(f'   ❌ Azure OpenAI: {e}')

# Test 2: Storage Account
print('\n2️⃣ Testing Azure Storage...')
try:
    from azure.storage.blob import BlobServiceClient
    blob_service = BlobServiceClient.from_connection_string(
        os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    )
    containers = list(blob_service.list_containers())
    print(f'   ✅ Azure Storage: Connected ({len(containers)} containers)')
except Exception as e:
    print(f'   ❌ Azure Storage: {e}')

# Test 3: Cosmos DB
print('\n3️⃣ Testing Azure Cosmos DB...')
try:
    from azure.cosmos import CosmosClient
    cosmos_client = CosmosClient(
        os.getenv('AZURE_COSMOS_ENDPOINT'),
        os.getenv('AZURE_COSMOS_KEY')
    )
    databases = list(cosmos_client.list_databases())
    print(f'   ✅ Cosmos DB: Connected ({len(databases)} databases)')
except Exception as e:
    print(f'   ❌ Cosmos DB: {e}')

# Test 4: File Conversion Service
print('\n4️⃣ Testing File Conversion Service...')
try:
    from script_to_doc.converters import get_conversion_service, DocumentFormat
    service = get_conversion_service()
    formats = service.get_supported_formats()
    print(f'   ✅ Conversion Service: Loaded ({len(formats)} formats)')
except Exception as e:
    print(f'   ❌ Conversion Service: {e}')

print('\n🎉 Testing complete!')
"
```

### Expected Output

```
🧪 Testing Azure Services...

1️⃣ Testing Azure OpenAI...
   ✅ Azure OpenAI: Connected

2️⃣ Testing Azure Storage...
   ✅ Azure Storage: Connected (3 containers)

3️⃣ Testing Azure Cosmos DB...
   ✅ Cosmos DB: Connected (1 databases)

4️⃣ Testing File Conversion Service...
   ✅ Conversion Service: Loaded (3 formats)

🎉 Testing complete!
```

### Full End-to-End Test

```bash
# Start the backend
python -m uvicorn api.main:app --reload

# In another terminal, start the frontend
cd ../frontend
npm run dev

# Test the complete flow:
# 1. Navigate to http://localhost:3000
# 2. Upload a transcript
# 3. Wait for document generation
# 4. Select each format (DOCX, PDF, PPTX)
# 5. Download and verify each format opens correctly
```

---

## 💰 Cost Estimation

### Development/Testing Environment

| Service | Tier | Cost/Month | Notes |
|---------|------|-----------|-------|
| Azure OpenAI | Pay-as-you-go | $5-20 | Based on usage (already configured) |
| Storage Account | Standard LRS | $1-5 | ~100GB storage |
| Cosmos DB | Serverless | $0-10 | First 1M RUs free |
| Document Intelligence | Free F0 | $0 | 500 calls/month limit |
| Service Bus | Basic | $0.05 | First 1M operations free |
| **Total** | | **$6-35/month** | Depends on usage |

### Production Environment

| Service | Tier | Cost/Month | Notes |
|---------|------|-----------|-------|
| Azure OpenAI | Pay-as-you-go | $100-500 | Heavy usage |
| Storage Account | Standard LRS | $20-50 | ~1TB storage |
| Cosmos DB | Provisioned (400 RU/s) | $24 | Predictable costs |
| Document Intelligence | S0 | $1 per 1000 pages | Usage-based |
| Service Bus | Standard | $10 | Advanced features |
| **Total** | | **$155-585/month** | Depends on scale |

### Cost Optimization Tips

1. **Use Free Tiers for Dev**
   - Cosmos DB: Serverless or free tier (first account)
   - Document Intelligence: F0 tier
   - Service Bus: Basic tier

2. **Monitor Usage**
   - Set up Azure Cost Management alerts
   - Review monthly bills for unexpected charges
   - Use Azure Advisor for optimization recommendations

3. **Clean Up Resources**
   - Delete unused storage containers
   - Remove old documents after 30 days
   - Use lifecycle management for automatic cleanup

---

## 🔒 Security Best Practices

### 1. Secure Your Keys

**❌ Never commit .env file to git:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

**✅ Use Azure Key Vault (Production):**
```bash
# Store secrets in Key Vault
az keyvault secret set \
  --vault-name your-keyvault \
  --name storage-connection-string \
  --value "YOUR_CONNECTION_STRING"
```

### 2. Rotate Keys Regularly

```bash
# Regenerate storage account key
az storage account keys renew \
  --account-name scripttodocdev \
  --resource-group scripttodoc-dev \
  --key primary

# Regenerate Cosmos DB key
az cosmosdb keys regenerate \
  --name scripttodoc-cosmos-dev \
  --resource-group scripttodoc-dev \
  --key-kind primary
```

### 3. Use Managed Identities (Production)

Instead of connection strings, use Azure Managed Identities for production:

```python
# Example: Using Managed Identity for Storage
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

credential = DefaultAzureCredential()
blob_service = BlobServiceClient(
    account_url="https://scripttodocdev.blob.core.windows.net",
    credential=credential
)
```

### 4. Network Security

- Enable Azure Storage firewall
- Restrict Cosmos DB access to specific IPs
- Use Private Endpoints for production

---

## 🐛 Troubleshooting

### Issue: "Authentication failed" for Storage

**Symptoms:**
```
azure.core.exceptions.ClientAuthenticationError: Authentication failed
```

**Solutions:**
1. Verify connection string is correct (no extra spaces)
2. Check if storage account key was regenerated
3. Ensure storage account exists and is accessible
4. Try using Azure Portal to browse containers manually

### Issue: "Resource not found" for Cosmos DB

**Symptoms:**
```
azure.cosmos.exceptions.CosmosResourceNotFoundError: Resource not found
```

**Solutions:**
1. Verify database name is `scripttodoc`
2. Verify container name is `jobs`
3. Check if Cosmos DB account is fully deployed
4. Ensure endpoint URL is correct (should end with `:443/`)

### Issue: Backend won't start

**Symptoms:**
```
pydantic.error_wrappers.ValidationError: 4 validation errors for Settings
```

**Solutions:**
1. Ensure `.env` file is in the `backend/` directory
2. Verify all required fields have values (no placeholders)
3. Check for typos in environment variable names
4. Restart terminal to reload environment variables

### Issue: LibreOffice conversion fails

**Symptoms:**
```
ConversionError: libreoffice: command not found
```

**Solutions:**
1. Verify LibreOffice is installed: `libreoffice --version`
2. On macOS, create symlink if needed (see [FILE_CONVERSION_SETUP_GUIDE.md](FILE_CONVERSION_SETUP_GUIDE.md))
3. Ensure sufficient disk space for temp files
4. Check permissions on temp directory

### Issue: "Too many requests" errors

**Symptoms:**
```
429 Too Many Requests
```

**Solutions:**
1. Upgrade to higher pricing tier
2. Implement rate limiting in application
3. Use exponential backoff for retries
4. Monitor usage in Azure Portal

---

## 📞 Getting Help

### Azure Documentation
- [Azure Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/)
- [Azure Cosmos DB Documentation](https://docs.microsoft.com/en-us/azure/cosmos-db/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)

### Internal Resources
- **Setup Guide**: [FILE_CONVERSION_SETUP_GUIDE.md](FILE_CONVERSION_SETUP_GUIDE.md)
- **Implementation Plan**: [FILE_CONVERSION_IMPLEMENTATION_PLAN.md](FILE_CONVERSION_IMPLEMENTATION_PLAN.md)
- **Completion Summary**: [TASK_117_COMPLETION_SUMMARY.md](TASK_117_COMPLETION_SUMMARY.md)

### Azure Support
- Azure Portal: "Help + Support" → "New support request"
- Azure Community: https://techcommunity.microsoft.com/
- Stack Overflow: Tag questions with `azure` or specific service

---

## ✅ Setup Checklist

Use this checklist to track your progress:

### Essential Services (Required for File Conversion)

- [ ] **Azure Storage Account**
  - [ ] Created storage account
  - [ ] Created containers: `transcripts`, `documents`, `temp`
  - [ ] Obtained connection string
  - [ ] Updated `.env` file
  - [ ] Verified connection with test script

- [ ] **Azure Cosmos DB**
  - [ ] Created Cosmos DB account (serverless)
  - [ ] Created database: `scripttodoc`
  - [ ] Created container: `jobs` (partition key: `/user_id`)
  - [ ] Obtained endpoint and key
  - [ ] Updated `.env` file
  - [ ] Verified connection with test script

### Optional Services (For Extended Functionality)

- [ ] **Azure Document Intelligence** (optional)
  - [ ] Created Document Intelligence resource
  - [ ] Obtained endpoint and key
  - [ ] Updated `.env` file
  - [ ] Verified connection with test script

- [ ] **Azure Service Bus** (optional)
  - [ ] Created Service Bus namespace
  - [ ] Created queue: `document-jobs`
  - [ ] Obtained connection string
  - [ ] Updated `.env` file
  - [ ] Verified connection with test script

### Testing & Validation

- [ ] **Run Connection Tests**
  - [ ] All services connect successfully
  - [ ] No authentication errors
  - [ ] Containers/databases accessible

- [ ] **End-to-End Test**
  - [ ] Backend starts without errors
  - [ ] Frontend connects to backend
  - [ ] Can upload transcript
  - [ ] Document generation works
  - [ ] DOCX download works
  - [ ] PDF conversion works
  - [ ] PPTX conversion works

### Security & Best Practices

- [ ] **.env file is secure**
  - [ ] Added to `.gitignore`
  - [ ] Not committed to version control
  - [ ] Keys stored securely

- [ ] **Access controls configured**
  - [ ] Storage containers are private
  - [ ] Cosmos DB access restricted
  - [ ] SAS tokens have expiration

---

## 🎉 Success!

Once you've completed all the essential services setup and verified the connections, you're ready for full end-to-end testing of the file conversion feature!

**Next Steps:**
1. Run the backend: `python -m uvicorn api.main:app --reload`
2. Run the frontend: `npm run dev`
3. Test the complete user flow
4. Verify all three formats download correctly
5. Celebrate! 🎊

---

**Document Version**: 1.0
**Last Updated**: December 3, 2025
**Status**: 🔧 Ready for Configuration

