# ScriptToDoc Deployment Guide

Complete guide for deploying ScriptToDoc frontend and backend to Azure Container Apps.

> **📖 For the most comprehensive and up-to-date guide, see [COMPLETE_DEPLOYMENT_GUIDE.md](./COMPLETE_DEPLOYMENT_GUIDE.md)**

## Quick Start

For automated deployment, run:

```bash
cd deployment
./deploy-all.sh
```

This will guide you through the complete deployment process.

## Prerequisites

Before deploying, ensure you have:

1. **Azure CLI** installed and logged in
   ```bash
   az login
   az account set --subscription <your-subscription-id>
   ```

2. **Docker** installed and running
   ```bash
   docker --version
   docker info  # Should show Docker daemon is running
   ```

3. **Node.js 18+** installed
   ```bash
   node --version
   ```

4. **Python 3.11+** installed
   ```bash
   python3 --version
   ```

5. **Azure subscription** with Contributor or Owner role

Run the prerequisites check:

```bash
./check-prerequisites.sh
```

## Deployment Steps

### Step 1: Check Current State

Check what's already deployed:

```bash
./check-deployment-state.sh
```

### Step 2: Deploy Infrastructure

Creates all Azure resources (Storage, Cosmos DB, Service Bus, Key Vault, etc.):

```bash
./deploy-infrastructure.sh
```

**Time**: 10-15 minutes

### Step 3: Store Secrets

Populates Key Vault with all required secrets:

```bash
./store-secrets.sh
```

**Time**: 2-3 minutes

### Step 4: Deploy Backend

Builds Docker images and deploys API + Worker Container Apps:

```bash
./deploy-backend-local.sh
```

**Time**: 15-20 minutes

This script:
- Builds and pushes API image to ACR
- Builds and pushes Worker image to ACR
- Deploys API Container App
- Deploys Worker Container App
- Configures RBAC permissions

### Step 5: Deploy Frontend

Builds frontend image with API URL and deploys to Container Apps:

```bash
./deploy-frontend-containerapp.sh
```

**Time**: 10-15 minutes

**Note**: The API must be deployed first so we can get the API URL for the frontend build.

### Step 6: Update CORS

Updates API CORS settings to allow the frontend:

```bash
./update-cors.sh
```

**Time**: 2-3 minutes

## Verification

### Check Logs

View logs from all Container Apps:

```bash
./check-logs.sh
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

# Get Frontend URL
FRONTEND_URL=$(az containerapp show \
    -n ca-scripttodoc-prod-frontend \
    -g rg-scripttodoc-prod \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv)

# Test Frontend
curl https://$FRONTEND_URL
```

### End-to-End Test

1. Visit the frontend URL in your browser
2. Upload a test transcript file
3. Monitor job progress
4. Download the generated document

## Troubleshooting

### Container App fails to start

Check logs:

```bash
az containerapp logs show \
    -n ca-scripttodoc-prod-api \
    -g rg-scripttodoc-prod \
    --follow
```

Common issues:
- Missing Key Vault secrets → Run `./store-secrets.sh`
- RBAC permissions not configured → Check `deploy-backend.sh` Step 8
- Image not found in ACR → Rebuild and push images

### CORS errors

Update CORS settings:

```bash
./update-cors.sh
```

Or manually update `backend-api.bicep` and redeploy.

### Worker not processing jobs

1. Check Service Bus queue:
   ```bash
   az servicebus queue show \
       -n scripttodoc-jobs \
       --namespace-name sb-scripttodoc-prod \
       -g rg-scripttodoc-prod
   ```

2. Check worker logs:
   ```bash
   az containerapp logs show \
       -n ca-scripttodoc-prod-wrk \
       -g rg-scripttodoc-prod \
       --follow
   ```

3. Verify RBAC permissions (worker needs "Service Bus Data Owner" role)

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│      Azure Container Apps                │
├─────────────────────────────────────────┤
│  Frontend (Next.js on port 3000)        │
│  API (FastAPI on port 8000)              │
│  Worker (Background processor)          │
├─────────────────────────────────────────┤
│  Azure Services:                         │
│  • Key Vault (Secrets)                   │
│  • Cosmos DB (Job status)                │
│  • Blob Storage (Files)                  │
│  • Service Bus (Job queue)               │
│  • Azure OpenAI (GPT-4o-mini)           │
│  • Document Intelligence                 │
└─────────────────────────────────────────┘
```

## Resource Naming

All resources follow this naming convention:

- Resource Group: `rg-scripttodoc-prod`
- Container Apps: `ca-scripttodoc-prod-{api|wrk|frontend}`
- Storage Account: `stscripttodocprod`
- Cosmos DB: `cosmos-scripttodoc-prod`
- Key Vault: `kv-scripttodoc-prod`
- Service Bus: `sb-scripttodoc-prod`
- Container Registry: `crscripttodocprod`

## Cost Estimation

Approximate monthly costs (varies by usage):

- Container Apps: $50-100
- Cosmos DB (serverless): $20-50
- Storage: $5-10
- Service Bus: $10-20
- Azure OpenAI: $20-100 (depends on usage)
- Document Intelligence: $10-30
- Application Insights: $5-10

**Total**: ~$120-320/month

## Next Steps

After deployment:

1. Set up custom domain (optional)
2. Configure Azure AD authentication (if needed)
3. Set up Application Insights alerts
4. Configure backup strategy
5. Review and optimize costs

## Support

For issues or questions:

1. Check logs: `./check-logs.sh`
2. Review Application Insights in Azure Portal
3. Check deployment state: `./check-deployment-state.sh`
