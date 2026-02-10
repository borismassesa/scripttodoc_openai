# Backend Deployment Guide

Complete guide for deploying the ScriptToDoc backend to Azure Container Apps.

## Prerequisites ✅

Before deploying the backend, ensure you have:

- [x] Azure infrastructure deployed (from Day 2)
- [x] Frontend deployed to Azure Static Web Apps (from Day 2)
- [x] Docker Desktop installed and running
- [x] Azure CLI logged in (`az login`)
- [x] Correct subscription selected

## Deployment Options

### Option 1: Automated Script (Recommended)

Run the automated deployment script:

```bash
cd deployment
./deploy-backend.sh
```

This script will:
1. ✅ Get infrastructure outputs (ACR, Key Vault, etc.)
2. ✅ Build Docker images for API and Worker
3. ✅ Push images to Azure Container Registry
4. ✅ Deploy API Container App with Managed Identity
5. ✅ Deploy Worker Container App with Managed Identity
6. ✅ Configure RBAC permissions for all Azure services
7. ✅ Provide next steps and testing commands

**Time:** ~10-15 minutes

---

### Option 2: Manual Step-by-Step

If you prefer manual control:

#### Step 1: Get Infrastructure Outputs

```bash
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

# Get resource names
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

SB_NAMESPACE=$(az servicebus namespace list \
  -g $RESOURCE_GROUP \
  --query "[0].name" \
  -o tsv)

echo "Container Registry: $CONTAINER_REGISTRY"
echo "Key Vault: $KEY_VAULT_NAME"
echo "Service Bus: $SB_NAMESPACE"
```

#### Step 2: Build and Push Docker Images

```bash
# Login to ACR
az acr login --name $CONTAINER_REGISTRY

# Build and push API image
cd backend
docker build -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-api:latest -f Dockerfile .
docker push $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-api:latest

# Build and push Worker image
docker build -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-worker:latest -f Dockerfile.worker .
docker push $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-worker:latest
```

#### Step 3: Deploy API Container App

```bash
cd ../deployment

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
```

Get the API URL:

```bash
API_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-api \
  --query 'properties.outputs.apiUrl.value' \
  -o tsv)

echo "API URL: $API_URL"
```

#### Step 4: Deploy Worker Container App

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file backend-worker.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    serviceBusNamespaceName=$SB_NAMESPACE \
    imageTag=latest
```

#### Step 5: Configure RBAC Permissions

```bash
# Get Managed Identity Principal IDs
API_PRINCIPAL_ID=$(az containerapp show \
  -n ca-$APP_NAME-$ENVIRONMENT-api \
  -g $RESOURCE_GROUP \
  --query "identity.principalId" \
  -o tsv)

WORKER_PRINCIPAL_ID=$(az containerapp show \
  -n ca-$APP_NAME-$ENVIRONMENT-wrk \
  -g $RESOURCE_GROUP \
  --query "identity.principalId" \
  -o tsv)

# Get Resource IDs
KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)
STORAGE_ID=$(az storage account list -g $RESOURCE_GROUP --query "[0].id" -o tsv)
COSMOS_ID=$(az cosmosdb show -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query id -o tsv)
SB_ID=$(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Assign permissions (API)
az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID
az role assignment create --assignee $API_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID
az role assignment create --assignee $API_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID
az role assignment create --assignee $API_PRINCIPAL_ID --role "Azure Service Bus Data Sender" --scope $SB_ID

# Assign permissions (Worker)
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Azure Service Bus Data Owner" --scope $SB_ID
```

---

## Post-Deployment Configuration

### 1. Update Frontend Environment Variables

Update `frontend/.env.production` with the API URL:

```bash
NEXT_PUBLIC_API_URL=https://ca-scripttodoc-prod-api.XXX.azurecontainerapps.io
```

Commit and push to trigger frontend redeployment:

```bash
git add frontend/.env.production
git commit -m "Update API URL for production"
git push
```

### 2. Update API CORS Settings

Edit [deployment/backend-api.bicep](deployment/backend-api.bicep:29) to allow your Static Web App:

```bicep
corsPolicy: {
  allowedOrigins: ['https://swa-scripttodoc-prod-XXX.azurestaticapps.net']
  allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  allowedHeaders: ['*']
  exposeHeaders: ['*']
  maxAge: 3600
  allowCredentials: true
}
```

Then redeploy the API:

```bash
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/backend-api.bicep \
  --parameters environment=prod appName=scripttodoc \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME
```

---

## Testing the Deployment

### 1. Check API Health

```bash
curl https://ca-scripttodoc-prod-api.XXX.azurecontainerapps.io/health
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

### 2. View Container Logs

**API Logs:**
```bash
az containerapp logs show \
  -n ca-scripttodoc-prod-api \
  -g rg-scripttodoc-prod \
  --follow
```

**Worker Logs:**
```bash
az containerapp logs show \
  -n ca-scripttodoc-prod-wrk \
  -g rg-scripttodoc-prod \
  --follow
```

### 3. Test End-to-End

1. Visit your Static Web App: `https://swa-scripttodoc-prod-XXX.azurestaticapps.net`
2. Upload a sample transcript file
3. Monitor the job progress in real-time
4. Download the generated document
5. Check the worker logs to see processing details

---

## CI/CD with GitHub Actions

The deployment includes a GitHub Actions workflow at [.github/workflows/backend-deploy.yml](.github/workflows/backend-deploy.yml).

### Setup GitHub Secrets

1. **Create Service Principal:**

```bash
az ad sp create-for-rbac \
  --name "github-scripttodoc-backend" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-scripttodoc-prod \
  --sdk-auth
```

2. **Add to GitHub Secrets:**

Copy the output and add to GitHub repository secrets as `AZURE_CREDENTIALS`.

3. **Trigger Deployment:**

Push changes to the `main` branch:

```bash
git add .
git commit -m "feat: backend deployment setup"
git push
```

The workflow will automatically:
- Build Docker images
- Push to ACR
- Deploy Container Apps
- Configure RBAC

---

## Monitoring and Scaling

### View Container App Metrics

```bash
az containerapp show \
  -n ca-scripttodoc-prod-api \
  -g rg-scripttodoc-prod \
  --query "properties.template.scale"
```

### Update Scaling Rules

Edit the Bicep templates to adjust scaling:

**API Scaling** (backend-api.bicep):
```bicep
scale: {
  minReplicas: 1
  maxReplicas: 10
  rules: [
    {
      name: 'http-rule'
      http: {
        metadata: {
          concurrentRequests: '50'
        }
      }
    }
  ]
}
```

**Worker Scaling** (backend-worker.bicep):
```bicep
scale: {
  minReplicas: 1
  maxReplicas: 5
  rules: [
    {
      name: 'queue-scaling'
      custom: {
        type: 'azure-servicebus'
        metadata: {
          queueName: 'scripttodoc-jobs'
          messageCount: '5'
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Issue: Container fails to start

**Check logs:**
```bash
az containerapp logs show -n ca-scripttodoc-prod-api -g rg-scripttodoc-prod --tail 50
```

**Common causes:**
- Missing environment variables
- RBAC permissions not configured
- Key Vault secrets not accessible

### Issue: Worker not processing jobs

**Check Service Bus queue:**
```bash
az servicebus queue show \
  -n scripttodoc-jobs \
  --namespace-name sb-scripttodoc-prod \
  -g rg-scripttodoc-prod \
  --query "{activeMessages: countDetails.activeMessageCount, deadLetters: countDetails.deadLetterMessageCount}"
```

**Check worker logs:**
```bash
az containerapp logs show -n ca-scripttodoc-prod-wrk -g rg-scripttodoc-prod --follow
```

### Issue: API returns 500 errors

**Check Application Insights:**
```bash
az monitor app-insights query \
  --app ai-scripttodoc-prod \
  -g rg-scripttodoc-prod \
  --analytics-query "exceptions | top 10 by timestamp desc"
```

---

## Rollback

If deployment fails, rollback to previous revision:

```bash
# List revisions
az containerapp revision list \
  -n ca-scripttodoc-prod-api \
  -g rg-scripttodoc-prod \
  -o table

# Activate previous revision
az containerapp revision activate \
  -n ca-scripttodoc-prod-api \
  -g rg-scripttodoc-prod \
  --revision <REVISION_NAME>
```

---

## Cost Optimization

Current configuration costs ~$96-191/month. To reduce costs:

1. **Reduce Container App replicas:**
   - Set `minReplicas: 0` (scale to zero when idle)

2. **Reduce Cosmos DB TTL:**
   - Currently 90 days (7776000 seconds)
   - Reduce to 30 days (2592000 seconds)

3. **Use Azure Reservations:**
   - Purchase 1-year or 3-year reserved instances

---

## Next Steps

✅ Backend deployed successfully!

Now you can:
- [ ] Set up custom domain for Static Web App
- [ ] Configure Azure AD B2C authentication
- [ ] Enable Application Insights alerts
- [ ] Set up backup and disaster recovery
- [ ] Configure Azure Front Door for global distribution

For production hardening, see [VERCEL_SECURITY_ARCHITECTURE_MVP.md](../docs/architecture/VERCEL_SECURITY_ARCHITECTURE_MVP.md).
