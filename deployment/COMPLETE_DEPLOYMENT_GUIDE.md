# ScriptToDoc Complete Deployment Guide

This guide provides step-by-step instructions for deploying the ScriptToDoc application to Azure Container Apps.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Two-Stage Deployment Strategy](#two-stage-deployment-strategy)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Resource Naming Conventions](#resource-naming-conventions)
8. [Architecture Overview](#architecture-overview)

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

### Required Software

1. **Azure CLI** (v2.50.0 or later)
   ```bash
   az --version
   az login
   az account set --subscription <your-subscription-id>
   ```

2. **Docker Desktop** (running)
   ```bash
   docker --version
   docker info  # Should show Docker daemon is running
   ```

3. **Node.js** (v18 or later)
   ```bash
   node --version
   ```

4. **Python** (v3.11 or later)
   ```bash
   python3 --version
   ```
   > **Note**: For Docker builds, the Python version in the Dockerfile (3.11-slim) is used, so an older local Python version is acceptable if Docker is available.

5. **jq** (optional but recommended for better error parsing)
   ```bash
   jq --version
   # Install on macOS: brew install jq
   # Install on Ubuntu: sudo apt-get install jq
   ```

### Azure Requirements

- Azure subscription with **Contributor** or **Owner** role
- Sufficient quota for:
  - Container Apps (2-3 apps)
  - Container Registry (1 registry)
  - Cosmos DB (1 account)
  - Storage Account (1 account)
  - Service Bus (1 namespace)
  - Key Vault (1 vault)

### Verify Prerequisites

Run the prerequisites check script:

```bash
cd deployment
./check-prerequisites.sh
```

This will verify all requirements and provide guidance if anything is missing.

---

## Quick Start

For automated deployment, run:

```bash
cd deployment
./deploy-all.sh
```

This interactive script will guide you through:
1. Prerequisites check
2. Infrastructure deployment
3. Secrets storage
4. Backend deployment
5. Frontend deployment
6. CORS configuration

**Estimated Time**: 40-55 minutes

---

## Detailed Deployment Steps

### Step 1: Check Prerequisites

```bash
cd deployment
./check-prerequisites.sh
```

This verifies:
- Azure CLI installation and login status
- Docker installation and running status
- Node.js and Python versions
- Required Azure CLI extensions

### Step 2: Check Current Deployment State

```bash
./check-deployment-state.sh
```

This shows:
- Existing Azure resources
- What needs to be deployed
- Current deployment status

### Step 3: Deploy Infrastructure

Creates all Azure resources (Storage, Cosmos DB, Service Bus, Key Vault, Container Registry, Container Apps Environment, etc.):

```bash
./deploy-infrastructure.sh
```

**Time**: 10-15 minutes

**What it creates**:
- Resource Group: `rg-scripttodoc-prod`
- Storage Account: `stscripttodocprod`
- Cosmos DB: `cosmos-scripttodoc-prod`
- Service Bus Namespace: `sb-scripttodoc-prod`
- Key Vault: `kv-scripttodoc-prod`
- Container Registry: `crscripttodocprod`
- Container Apps Environment: `cae-scripttodoc-prod`
- Application Insights: `ai-scripttodoc-prod`

### Step 4: Store Secrets in Key Vault

Populates Key Vault with all required secrets:

```bash
./store-secrets.sh
```

**Time**: 2-3 minutes

**Required Secrets**:
- `azure-openai-endpoint`
- `azure-openai-api-key`
- `azure-openai-deployment-name`
- `azure-document-intelligence-endpoint`
- `azure-document-intelligence-api-key`
- `azure-storage-connection-string`
- `cosmos-db-connection-string`
- `cosmos-db-database-name`
- `service-bus-connection-string`
- `service-bus-queue-name`

The script will prompt you for each secret value.

### Step 5: Deploy Backend

Builds Docker images and deploys API + Worker Container Apps:

```bash
./deploy-backend-local.sh
```

**Time**: 15-20 minutes

**What it does**:
1. Gets infrastructure outputs (ACR, Key Vault, etc.)
2. Builds API Docker image locally
3. Pushes API image to Azure Container Registry
4. Builds Worker Docker image locally
5. Pushes Worker image to Azure Container Registry
6. Deploys API Container App using two-stage deployment
7. Deploys Worker Container App using two-stage deployment
8. Configures RBAC permissions for both Container Apps

**Two-Stage Deployment Process** (see [Two-Stage Deployment Strategy](#two-stage-deployment-strategy) for details):
- **Stage 1**: Deploy minimal Container App (creates managed identity)
- **Stage 2**: Grant RBAC permissions and wait for propagation
- **Stage 3**: Update Container App with full configuration (Key Vault references)

### Step 6: Deploy Frontend

Builds frontend image with API URL and deploys to Container Apps:

```bash
./deploy-frontend-containerapp.sh
```

**Time**: 10-15 minutes

**Note**: The API must be deployed first so we can get the API URL for the frontend build.

The script will:
1. Get the API URL from the deployed API Container App
2. Build the frontend Docker image with the API URL baked in
3. Push the image to Azure Container Registry
4. Deploy the frontend Container App

### Step 7: Update CORS Settings

Updates API CORS settings to allow the frontend:

```bash
./update-cors.sh
```

**Time**: 2-3 minutes

This ensures the frontend can make API requests without CORS errors.

---

## Two-Stage Deployment Strategy

The backend deployment uses a **two-stage deployment strategy** to handle Azure RBAC permission propagation delays. This is necessary because Azure's validation service checks Key Vault access permissions during deployment, but RBAC permissions can take time to propagate.

### Why Two-Stage Deployment?

When deploying a Container App with Key Vault secret references, Azure validates that the Container App's managed identity has permission to access those secrets. However:

1. The managed identity is created when the Container App is first deployed
2. RBAC permissions need to be granted to this identity
3. RBAC permission propagation can take 30-60 seconds
4. Azure's validation happens immediately during deployment

If we try to deploy with Key Vault references before permissions propagate, the deployment fails with errors like:
```
Unable to get value using Managed identity system for secret azure-storage-connection-string
```

### How It Works

#### Stage 1: Minimal Deployment
Deploy a minimal Bicep template (`backend-api-minimal.bicep` or `backend-worker-minimal.bicep`) that:
- Creates the Container App
- Creates the system-assigned managed identity
- Includes basic configuration (image, ingress, ACR password)
- **Excludes** Key Vault secret references

#### Stage 2: RBAC Configuration
1. Get the Container App's `principalId` from the managed identity
2. Grant "Key Vault Secrets User" role to the principal
3. Wait 60 seconds for RBAC propagation
4. Verify the role assignment exists

#### Stage 3: Full Configuration Update
Update the **same** Container App with the full Bicep template (`backend-api.bicep` or `backend-worker.bicep`) that:
- Includes all Key Vault secret references
- Includes all environment variables
- Includes all configuration

This works because:
- The identity already exists
- The identity already has permissions
- Azure's validation passes immediately

### Container App Names

**Important**: The Container App names must match between the script and Bicep templates:

- **API**: `ca-${APP_NAME}-${ENVIRONMENT}-api` → `ca-scripttodoc-prod-api`
- **Worker**: `ca-${APP_NAME}-${ENVIRONMENT}-wrk` → `ca-scripttodoc-prod-wrk`
  > Note: Worker uses `-wrk` (not `-worker`) to stay within Azure's 32-character limit

---

## Verification

### Check Deployment Status

```bash
./check-deployment-state.sh
```

### Check Container App Logs

```bash
./check-logs.sh
```

Or view logs for specific apps:

```bash
# API logs
az containerapp logs show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --follow

# Worker logs
az containerapp logs show \
    -n ca-scripttodoc-prod-wrk \
    -g rg-scripttodoc-prod \
    --follow
```

### Test Health Endpoints

```bash
# Get API URL
API_URL=$(az containerapp show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv)

# Test API health
curl https://$API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "cosmos_db": "configured",
    "blob_storage": "configured",
    "service_bus": "configured",
    "azure_openai": "configured",
    "azure_di": "configured"
  }
}
```

### Get Application URLs

```bash
# API URL
az containerapp show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv

# Frontend URL
az containerapp show \
    -n ca-scripttodoc-prod-frontend \
    -g rg-scripttodoc-prod \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv
```

### End-to-End Test

1. Visit the frontend URL in your browser
2. Upload a test transcript file
3. Monitor job progress
4. Download the generated document

---

## Troubleshooting

### Container App Fails to Start

**Symptoms**: Container App shows "Failed" or "Unhealthy" status

**Check logs**:
```bash
az containerapp logs show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --tail 50
```

**Common causes**:
1. **Missing Key Vault secrets**
   - Solution: Run `./store-secrets.sh` to populate all secrets

2. **RBAC permissions not configured**
   - Solution: Check that the Container App's managed identity has "Key Vault Secrets User" role
   ```bash
   # Get principal ID
   PRINCIPAL_ID=$(az containerapp show \
       -n ca-scripttodoc-prod-api \
       -g rg-scripttodoc-prod \
       --query "identity.principalId" \
       -o tsv)
   
   # Check role assignments
   az role assignment list \
       --assignee $PRINCIPAL_ID \
       --scope /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-scripttodoc-prod/providers/Microsoft.KeyVault/vaults/kv-scripttodoc-prod
   ```

3. **Image not found in ACR**
   - Solution: Rebuild and push images
   ```bash
   ./deploy-backend-local.sh
   ```

### Deployment Fails with "Unable to get value using Managed identity"

**Symptoms**: Deployment fails with Key Vault access errors

**Cause**: RBAC permissions haven't propagated yet, or the two-stage deployment wasn't used

**Solution**: 
1. Ensure you're using `deploy-backend-local.sh` (which implements two-stage deployment)
2. If manually deploying, follow the two-stage process:
   - Deploy minimal template first
   - Grant RBAC permissions
   - Wait 60 seconds
   - Update with full template

### Worker Not Processing Jobs

**Symptoms**: Jobs are queued but not processed

**Check Service Bus queue**:
```bash
az servicebus queue show \
    -n scripttodoc-jobs \
    --namespace-name sb-scripttodoc-prod \
    -g rg-scripttodoc-prod \
    --query "{activeMessages: countDetails.activeMessageCount, deadLetters: countDetails.deadLetterMessageCount}"
```

**Check worker logs**:
```bash
az containerapp logs show \
    -n ca-scripttodoc-prod-wrk \
    -g rg-scripttodoc-prod \
    --follow
```

**Verify RBAC permissions**: Worker needs "Service Bus Data Owner" role
```bash
WORKER_PRINCIPAL_ID=$(az containerapp show \
    -n ca-scripttodoc-prod-wrk \
    -g rg-scripttodoc-prod \
    --query "identity.principalId" \
    -o tsv)

SB_ID=$(az servicebus namespace show \
    -n sb-scripttodoc-prod \
    -g rg-scripttodoc-prod \
    --query id \
    -o tsv)

az role assignment create \
    --assignee $WORKER_PRINCIPAL_ID \
    --role "Azure Service Bus Data Owner" \
    --scope $SB_ID
```

### CORS Errors

**Symptoms**: Frontend can't make API requests, browser shows CORS errors

**Solution**: Update CORS settings
```bash
./update-cors.sh
```

Or manually update `backend-api.bicep` and redeploy:
```bicep
corsPolicy: {
  allowedOrigins: ['https://your-frontend-url.azurecontainerapps.io']
  allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  allowedHeaders: ['*']
  exposeHeaders: ['*']
  maxAge: 3600
  allowCredentials: true
}
```

### Docker Push Stuck or Slow

**Symptoms**: Docker push takes a very long time or gets stuck

**Solutions**:
1. **Use local Docker build** (recommended if Docker Desktop is running):
   ```bash
   ./deploy-backend-local.sh
   ```

2. **Use ACR Build** (builds directly in Azure):
   ```bash
   ./deploy-backend-acr-build.sh
   ```

3. **Check network connection**:
   ```bash
   az acr login --name crscripttodocprod
   docker pull mcr.microsoft.com/hello-world
   ```

### Container App Name Mismatch

**Symptoms**: Script can't find Container App after deployment

**Cause**: Name mismatch between script and Bicep template

**Solution**: Ensure names match:
- Script: `WORKER_CONTAINER_APP_NAME="ca-${APP_NAME}-${ENVIRONMENT}-wrk"`
- Bicep: `var workerName = 'ca-${resourcePrefix}-wrk'`

Both should resolve to: `ca-scripttodoc-prod-wrk`

### Deployment Status Shows "unknown"

**Symptoms**: Script reports deployment status as "unknown"

**Cause**: Azure deployment output format may vary

**Solution**: The script includes fallback logic:
1. Checks for `outputs` in deployment result (indicates success)
2. Checks if Container App exists (fallback verification)
3. If Container App exists, assumes deployment succeeded

If deployment truly failed, check Azure Portal or run:
```bash
az deployment group show \
    --resource-group rg-scripttodoc-prod \
    --name backend-api \
    --query "properties.provisioningState"
```

---

## Resource Naming Conventions

All resources follow this naming convention:

| Resource Type | Naming Pattern | Example |
|--------------|----------------|---------|
| Resource Group | `rg-{appName}-{environment}` | `rg-scripttodoc-prod` |
| Container App (API) | `ca-{appName}-{environment}-api` | `ca-scripttodoc-prod-api` |
| Container App (Worker) | `ca-{appName}-{environment}-wrk` | `ca-scripttodoc-prod-wrk` |
| Container App (Frontend) | `ca-{appName}-{environment}-frontend` | `ca-scripttodoc-prod-frontend` |
| Storage Account | `st{appName}{environment}` (no hyphens) | `stscripttodocprod` |
| Cosmos DB | `cosmos-{appName}-{environment}` | `cosmos-scripttodoc-prod` |
| Key Vault | `kv-{appName}-{environment}` | `kv-scripttodoc-prod` |
| Service Bus | `sb-{appName}-{environment}` | `sb-scripttodoc-prod` |
| Container Registry | `cr{appName}{environment}` (no hyphens) | `crscripttodocprod` |
| Container Apps Environment | `cae-{appName}-{environment}` | `cae-scripttodoc-prod` |
| Application Insights | `ai-{appName}-{environment}` | `ai-scripttodoc-prod` |

**Note**: Some Azure resources (Storage Account, Container Registry) don't allow hyphens in names, so they use concatenated format.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Container Apps                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Frontend      │  │      API        │  │   Worker     │ │
│  │  (Next.js)      │  │   (FastAPI)     │  │  (Processor) │ │
│  │  Port: 3000     │  │   Port: 8000    │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Managed Identity
                            │ (System-Assigned)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Key Vault    │  │ Blob Storage  │  │  Cosmos DB    │
│  (Secrets)    │  │   (Files)     │  │  (Job Status) │
└───────────────┘  └───────────────┘  └───────────────┘
                            │
                            ▼
                   ┌───────────────┐
                   │ Service Bus   │
                   │  (Job Queue)  │
                   └───────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Azure OpenAI  │  │   Document    │  │  Application  │
│  (GPT-4o-mini)│  │ Intelligence  │  │   Insights    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Managed Identity & RBAC

All Container Apps use **system-assigned managed identities** for secure access to Azure resources:

**API Container App** needs:
- "Key Vault Secrets User" → Access secrets
- "Storage Blob Data Contributor" → Upload/download files
- "Cosmos DB Built-in Data Contributor" → Read/write job status
- "Azure Service Bus Data Sender" → Send jobs to queue

**Worker Container App** needs:
- "Key Vault Secrets User" → Access secrets
- "Storage Blob Data Contributor" → Upload/download files
- "Cosmos DB Built-in Data Contributor" → Update job status
- "Azure Service Bus Data Owner" → Receive and process jobs from queue

### Data Flow

1. **User uploads transcript** → Frontend → API
2. **API validates and stores** → Blob Storage
3. **API creates job** → Cosmos DB (status: "pending")
4. **API sends message** → Service Bus queue
5. **Worker receives message** → Processes job
6. **Worker updates status** → Cosmos DB (status: "processing" → "completed")
7. **Frontend polls API** → Gets updated status
8. **User downloads document** → Frontend → API → Blob Storage

---

## Cost Estimation

Approximate monthly costs (varies by usage):

| Service | Estimated Cost |
|---------|---------------|
| Container Apps (3 apps) | $50-100 |
| Cosmos DB (serverless) | $20-50 |
| Blob Storage | $5-10 |
| Service Bus | $10-20 |
| Azure OpenAI (GPT-4o-mini) | $20-100 |
| Document Intelligence | $10-30 |
| Application Insights | $5-10 |
| Container Registry | $5-10 |

**Total**: ~$125-330/month

### Cost Optimization Tips

1. **Scale to zero**: Set `minReplicas: 0` for non-critical apps
2. **Reduce Cosmos DB TTL**: Lower from 90 days to 30 days
3. **Use Azure Reservations**: Purchase 1-year or 3-year reserved instances
4. **Monitor usage**: Use Azure Cost Management to track spending

---

## Next Steps

After successful deployment:

1. **Set up custom domain** (optional)
   - Configure DNS records
   - Add custom domain to Container Apps
   - Update CORS settings

2. **Configure Azure AD authentication** (if needed)
   - Set up Azure AD B2C
   - Configure authentication in frontend

3. **Set up monitoring and alerts**
   - Configure Application Insights alerts
   - Set up email notifications for errors

4. **Configure backup strategy**
   - Set up Cosmos DB backups
   - Configure Storage Account lifecycle policies

5. **Review and optimize costs**
   - Use Azure Cost Management
   - Set up budget alerts

6. **Set up CI/CD** (optional)
   - Configure GitHub Actions
   - Automate deployments on code changes

---

## Support

For issues or questions:

1. **Check logs**: `./check-logs.sh`
2. **Review Application Insights** in Azure Portal
3. **Check deployment state**: `./check-deployment-state.sh`
4. **Review troubleshooting section** above
5. **Check Azure Portal** for resource status

---

## Appendix: Manual Deployment Commands

If you need to deploy manually (without scripts):

### Deploy Infrastructure
```bash
az deployment group create \
    --resource-group rg-scripttodoc-prod \
    --template-file azure-infrastructure.bicep \
    --parameters environment=prod appName=scripttodoc
```

### Deploy API (Two-Stage)
```bash
# Stage 1: Minimal deployment
az deployment group create \
    --resource-group rg-scripttodoc-prod \
    --name backend-api-minimal \
    --template-file backend-api-minimal.bicep \
    --parameters \
        environment=prod \
        appName=scripttodoc \
        containerRegistryName=crscripttodocprod \
        containerAppsEnvironmentId="<CAE_ID>" \
        imageTag=latest

# Get principal ID
API_PRINCIPAL_ID=$(az containerapp show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --query "identity.principalId" \
    -o tsv)

# Grant RBAC
KV_ID=$(az keyvault show \
    -n kv-scripttodoc-prod \
    -g rg-scripttodoc-prod \
    --query id \
    -o tsv)

az role assignment create \
    --assignee $API_PRINCIPAL_ID \
    --role "Key Vault Secrets User" \
    --scope $KV_ID

# Wait 60 seconds
sleep 60

# Stage 2: Full deployment
az deployment group create \
    --resource-group rg-scripttodoc-prod \
    --name backend-api \
    --template-file backend-api.bicep \
    --parameters \
        environment=prod \
        appName=scripttodoc \
        containerRegistryName=crscripttodocprod \
        containerAppsEnvironmentId="<CAE_ID>" \
        keyVaultName=kv-scripttodoc-prod \
        imageTag=latest
```

---

**Last Updated**: January 2025
**Version**: 1.0
