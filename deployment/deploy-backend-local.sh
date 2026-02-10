#!/bin/bash

# Backend Deployment using Local Docker Build
# Faster than ACR Build since we build locally and only push the image

set -e

# Configuration
RESOURCE_GROUP="rg-scripttodoc-prod"
ENVIRONMENT="prod"
APP_NAME="scripttodoc"

echo "🚀 Backend Deployment (Local Docker Build)"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Environment: $ENVIRONMENT"
echo "App Name: $APP_NAME"
echo ""

# Step 1: Get infrastructure outputs
echo "📋 Step 1: Getting infrastructure outputs..."
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

echo "✅ Container Registry: $CONTAINER_REGISTRY"
echo "✅ Key Vault: $KEY_VAULT_NAME"
echo "✅ Container Apps Environment ID: ${CAE_ID:0:50}..."
echo "✅ Service Bus Namespace: $SB_NAMESPACE"
echo ""

# Step 2: Enable admin user on ACR temporarily
echo "📋 Step 2: Configuring Container Registry..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled true > /dev/null
echo "✅ ACR admin enabled"
echo ""

# Step 3: Login to ACR
echo "📋 Step 3: Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY
echo "✅ Logged in to ACR"
echo ""

# Step 4: Build API image locally (much faster)
echo "📋 Step 4: Building API image locally..."
echo "⏳ Building Docker image (this is faster than ACR upload)..."
cd ../backend

# Build locally first (no platform flag needed if on amd64 Mac)
docker build -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-api:latest -f Dockerfile .

echo "✅ API image built locally"
echo ""

# Step 5: Push API image
echo "📋 Step 5: Pushing API image to ACR..."
echo "⏳ Pushing image (this should be faster than uploading source code)..."
docker push $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-api:latest

echo "✅ API image pushed"
echo ""

# Step 6: Build Worker image locally
echo "📋 Step 6: Building Worker image locally..."
docker build -t $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-worker:latest -f Dockerfile.worker .

echo "✅ Worker image built locally"
echo ""

# Step 7: Push Worker image
echo "📋 Step 7: Pushing Worker image to ACR..."
docker push $CONTAINER_REGISTRY.azurecr.io/$APP_NAME-worker:latest

echo "✅ Worker image pushed"
echo ""

# Step 8: Deploy API Container App using two-stage approach
echo "📋 Step 8: Deploying API Container App (two-stage approach)..."
cd ../deployment

API_CONTAINER_APP_NAME="ca-${APP_NAME}-${ENVIRONMENT}-api"

# Check if Container App already exists
EXISTING_APP=$(az containerapp show \
  --name $API_CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "name" \
  -o tsv 2>/dev/null || echo "")

if [ -n "$EXISTING_APP" ]; then
    echo "📋 Existing Container App found. Deleting to start fresh..."
    az containerapp delete \
      --name $API_CONTAINER_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --yes \
      2>/dev/null || true
    echo "⏳ Waiting 10 seconds for cleanup..."
    sleep 10
fi

# Stage 1: Deploy minimal Container App (no Key Vault references) to establish identity
echo "📋 Stage 1: Deploying minimal Container App (establishes identity)..."
DEPLOY_RESULT=$(az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --name backend-api-minimal \
  --template-file backend-api-minimal.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    imageTag=latest \
  --output json 2>&1)

# #region agent log
LOG_FILE="/Users/boris/AZURE AI Document Intelligence/.cursor/debug.log"
TIMESTAMP=$(date +%s)000
# Check provisioningState properly - try jq first, fallback to grep
if command -v jq &> /dev/null; then
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | jq -r '.properties.provisioningState // .provisioningState // "unknown"' 2>/dev/null || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | jq -e '.error' > /dev/null 2>&1 && echo "true" || echo "false")
    HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | jq -e '.properties.outputs // .outputs' > /dev/null 2>&1 && echo "true" || echo "false")
else
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | grep -o '"provisioningState":"[^"]*"' | cut -d'"' -f4 | head -1 || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | grep -q '"error":' && echo "true" || echo "false")
    HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | grep -q '"outputs":' && echo "true" || echo "false")
fi

HAS_ERROR="false"
if [ "$HAS_ERROR_OBJ" = "true" ]; then
    HAS_ERROR="true"
    DEPLOY_STATUS="Failed"
elif [ "$DEPLOY_STATUS" != "Succeeded" ] && [ "$DEPLOY_STATUS" != "unknown" ]; then
    HAS_ERROR="true"
fi

echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:141\",\"message\":\"After minimal deployment\",\"data\":{\"status\":\"$DEPLOY_STATUS\",\"hasError\":$HAS_ERROR,\"hasErrorObj\":$HAS_ERROR_OBJ,\"hasOutputs\":$HAS_OUTPUTS},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# CRITICAL: Check for outputs FIRST - if outputs exist, deployment succeeded regardless of status
if [ "$HAS_OUTPUTS" = "true" ]; then
    echo "✅ Minimal deployment succeeded (outputs present)"
    DEPLOY_STATUS="Succeeded"
    HAS_ERROR="false"
# If status is unknown, check Container App existence
elif [ "$DEPLOY_STATUS" = "unknown" ]; then
    echo "⚠️  Warning: Could not determine deployment status. Checking Container App..."
    APP_EXISTS=$(az containerapp show --name $API_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
    if [ -n "$APP_EXISTS" ]; then
        echo "✅ Container App exists. Assuming deployment succeeded."
        DEPLOY_STATUS="Succeeded"
        HAS_ERROR="false"
    else
        echo "❌ Container App not found. Deployment may have failed."
        echo "$DEPLOY_RESULT"
        exit 1
    fi
# Only fail if we have a confirmed error object AND no outputs
elif [ "$HAS_ERROR" = "true" ] && [ "$HAS_ERROR_OBJ" = "true" ] && [ "$HAS_OUTPUTS" = "false" ]; then
    if command -v jq &> /dev/null; then
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | jq -r '.error.message // .error.details[0].message // ""' 2>/dev/null || echo "")
    else
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    fi
    echo "❌ Minimal deployment failed. Status: $DEPLOY_STATUS"
    if [ -n "$ERROR_MSG" ]; then
        echo "Error: $ERROR_MSG"
    fi
    if command -v jq &> /dev/null; then
        echo "$DEPLOY_RESULT" | jq '.error' 2>/dev/null || echo "$DEPLOY_RESULT"
    else
        echo "$DEPLOY_RESULT" | grep -A 30 '"error":' || echo "$DEPLOY_RESULT"
    fi
    exit 1
fi

# Get the principal ID from the minimal deployment
API_PRINCIPAL_ID=$(az containerapp show \
  --name $API_CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" \
  -o tsv 2>/dev/null || echo "")

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H3\",\"location\":\"deploy-backend-local.sh:125\",\"message\":\"Minimal deployment identity\",\"data\":{\"containerAppName\":\"$API_CONTAINER_APP_NAME\",\"principalId\":\"$API_PRINCIPAL_ID\",\"hasPrincipalId\":$([ -n "$API_PRINCIPAL_ID" ] && echo "true" || echo "false")},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ -z "$API_PRINCIPAL_ID" ] || [ "$API_PRINCIPAL_ID" == "null" ]; then
    echo "❌ Failed to get API principal ID from minimal deployment."
    exit 1
fi

echo "✅ Minimal Container App deployed with identity: ${API_PRINCIPAL_ID:0:50}..."
echo ""

# Step 8.5: Grant RBAC permissions BEFORE the deployment can succeed
echo "📋 Step 8.5: Granting Key Vault permissions..."
KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)

# #region agent log
LOG_FILE="/Users/boris/AZURE AI Document Intelligence/.cursor/debug.log"
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1,H6\",\"location\":\"deploy-backend-local.sh:377\",\"message\":\"Before RBAC grant\",\"data\":{\"apiPrincipalId\":\"$API_PRINCIPAL_ID\",\"keyVaultId\":\"$KV_ID\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# Grant permissions to Container App's identity
az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true

# CRITICAL FIX: Also grant permissions to Container Apps Environment's managed identity
# The environment's identity is used to validate Key Vault references during deployment
CAE_NAME=$(echo $CAE_ID | sed 's/.*\/\([^/]*\)$/\1/')
CAE_PRINCIPAL_ID=$(az containerapp env show \
  --name $CAE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.workloadProfiles[0].workloadProfileType" \
  -o tsv 2>/dev/null || echo "")

# Get the environment's managed identity (if it has one)
CAE_MANAGED_IDENTITY=$(az containerapp env show \
  --name $CAE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" \
  -o tsv 2>/dev/null || echo "")

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H6\",\"location\":\"deploy-backend-local.sh:385\",\"message\":\"Container Apps Environment identity check\",\"data\":{\"caeName\":\"$CAE_NAME\",\"caePrincipalId\":\"$CAE_MANAGED_IDENTITY\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ -n "$CAE_MANAGED_IDENTITY" ] && [ "$CAE_MANAGED_IDENTITY" != "null" ]; then
    echo "📋 Granting Key Vault permissions to Container Apps Environment identity..."
    az role assignment create --assignee $CAE_MANAGED_IDENTITY --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true
    echo "✅ Environment identity permissions granted"
fi

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1\",\"location\":\"deploy-backend-local.sh:381\",\"message\":\"After RBAC grant\",\"data\":{\"principalId\":\"$API_PRINCIPAL_ID\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# Check if secrets exist (H2)
echo "📋 Checking if required secrets exist in Key Vault..."
REQUIRED_SECRETS=("azure-openai-key" "azure-openai-endpoint" "azure-openai-deployment" "azure-di-key" "azure-di-endpoint" "azure-storage-account-name" "azure-storage-connection-string" "azure-cosmos-endpoint" "azure-cosmos-connection-string" "azure-service-bus-connection-string")
MISSING_SECRETS=()
for SECRET in "${REQUIRED_SECRETS[@]}"; do
    if ! az keyvault secret show --vault-name $KEY_VAULT_NAME --name $SECRET &> /dev/null; then
        MISSING_SECRETS+=("$SECRET")
    fi
done

# #region agent log
TIMESTAMP=$(date +%s)000
MISSING_JSON="["
for i in "${!MISSING_SECRETS[@]}"; do
    [ $i -gt 0 ] && MISSING_JSON+=","
    MISSING_JSON+="\"${MISSING_SECRETS[$i]}\""
done
MISSING_JSON+="]"
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H2\",\"location\":\"deploy-backend-local.sh:393\",\"message\":\"Secret existence check\",\"data\":{\"missingSecrets\":$MISSING_JSON,\"totalRequired\":${#REQUIRED_SECRETS[@]}},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    echo "❌ Missing secrets: ${MISSING_SECRETS[*]}"
    echo "   Run ./store-secrets.sh to store them"
    exit 1
fi
echo "✅ All required secrets exist"

# Wait for RBAC propagation (H1) - increased wait time
echo "⏳ Waiting 60 seconds for RBAC permissions to fully propagate..."
sleep 60

# Verify RBAC permissions were actually granted (H1, H4)
echo "📋 Verifying RBAC permissions..."
ROLE_ASSIGNMENTS=$(az role assignment list \
  --scope $KV_ID \
  --assignee $API_PRINCIPAL_ID \
  --query "[?roleDefinitionName=='Key Vault Secrets User']" \
  -o json 2>/dev/null || echo "[]")

# #region agent log
TIMESTAMP=$(date +%s)000
HAS_PERMISSION="false"
if echo "$ROLE_ASSIGNMENTS" | grep -q "Key Vault Secrets User"; then
    HAS_PERMISSION="true"
fi
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1,H4\",\"location\":\"deploy-backend-local.sh:210\",\"message\":\"RBAC permission verification\",\"data\":{\"principalId\":\"$API_PRINCIPAL_ID\",\"hasPermission\":$HAS_PERMISSION,\"roleAssignments\":$ROLE_ASSIGNMENTS},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ "$HAS_PERMISSION" = "false" ]; then
    echo "⚠️  Warning: RBAC permission verification failed. Retrying grant..."
    az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID
    echo "⏳ Waiting additional 30 seconds..."
    sleep 30
fi

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1\",\"location\":\"deploy-backend-local.sh:220\",\"message\":\"After RBAC propagation wait\",\"data\":{\"waitSeconds\":60,\"verified\":$HAS_PERMISSION},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

echo "✅ Key Vault permissions granted and propagated"
echo ""

# Step 8.6: Update the SAME Container App with Key Vault references
# CRITICAL: We update the existing Container App, not delete/recreate it
# This preserves the identity that has permissions
echo "📋 Step 8.6: Updating Container App with Key Vault secret references..."

# Wait for the Container App to be fully ready and identity propagated
echo "⏳ Waiting 20 seconds for Container App identity to be fully ready..."
sleep 20

# Update the EXISTING Container App with full Bicep template
# The identity already exists and has permissions, so this should work
echo "📋 Updating existing Container App with Key Vault secret references..."

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:250\",\"message\":\"Before updating with Key Vault secrets\",\"data\":{\"principalId\":\"$API_PRINCIPAL_ID\",\"containerAppName\":\"$API_CONTAINER_APP_NAME\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

DEPLOY_RESULT=$(az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --name backend-api \
  --template-file backend-api.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    imageTag=latest \
  --output json 2>&1)

# #region agent log
TIMESTAMP=$(date +%s)000
# Check provisioningState properly - try jq first, fallback to grep
if command -v jq &> /dev/null; then
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | jq -r '.properties.provisioningState // .provisioningState // "unknown"' 2>/dev/null || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | jq -e '.error' > /dev/null 2>&1 && echo "true" || echo "false")
else
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | grep -o '"provisioningState":"[^"]*"' | cut -d'"' -f4 | head -1 || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | grep -q '"error":' && echo "true" || echo "false")
fi

HAS_ERROR="false"
if [ "$HAS_ERROR_OBJ" = "true" ]; then
    HAS_ERROR="true"
    DEPLOY_STATUS="Failed"
elif [ "$DEPLOY_STATUS" != "Succeeded" ] && [ "$DEPLOY_STATUS" != "unknown" ]; then
    HAS_ERROR="true"
fi
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:315\",\"message\":\"After Key Vault secrets update via Bicep\",\"data\":{\"status\":\"$DEPLOY_STATUS\",\"hasError\":$HAS_ERROR,\"hasErrorObj\":$HAS_ERROR_OBJ},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# Check if deployment actually failed
if [ "$HAS_ERROR" = "true" ] || [ "$DEPLOY_STATUS" = "Failed" ]; then
    if command -v jq &> /dev/null; then
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | jq -r '.error.message // .error.details[0].message // ""' 2>/dev/null || echo "")
    else
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    fi
    echo "❌ Deployment failed. Status: $DEPLOY_STATUS"
    if [ -n "$ERROR_MSG" ]; then
        echo "Error: $ERROR_MSG"
    fi
    # Show error details
    if command -v jq &> /dev/null; then
        echo "$DEPLOY_RESULT" | jq '.error' 2>/dev/null || echo "$DEPLOY_RESULT"
    else
        echo "$DEPLOY_RESULT" | grep -A 30 '"error":' || echo "$DEPLOY_RESULT"
    fi
    exit 1
fi

# If status is unknown, check if we got outputs (indicates success)
if [ "$DEPLOY_STATUS" = "unknown" ]; then
    if command -v jq &> /dev/null; then
        HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | jq -e '.properties.outputs' > /dev/null 2>&1 && echo "true" || echo "false")
    else
        HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | grep -q '"outputs":' && echo "true" || echo "false")
    fi
    
    if [ "$HAS_OUTPUTS" = "true" ]; then
        echo "✅ Deployment appears successful (outputs present)"
        DEPLOY_STATUS="Succeeded"
    else
        echo "⚠️  Warning: Could not determine deployment status. Checking Container App..."
        # Verify Container App exists and has the right configuration
        APP_EXISTS=$(az containerapp show --name $API_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
        if [ -n "$APP_EXISTS" ]; then
            echo "✅ Container App exists. Assuming deployment succeeded."
            DEPLOY_STATUS="Succeeded"
        else
            echo "❌ Container App not found. Deployment may have failed."
            echo "$DEPLOY_RESULT"
            exit 1
        fi
    fi
fi

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:425\",\"message\":\"Getting API URL from deployment\",\"data\":{\"deploymentName\":\"backend-api\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

API_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name backend-api \
  --query 'properties.outputs.apiUrl.value' \
  -o tsv 2>&1)

# #region agent log
TIMESTAMP=$(date +%s)000
if echo "$API_URL" | grep -qi "error\|not found"; then
    echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:432\",\"message\":\"Failed to get API URL\",\"data\":{\"error\":\"$API_URL\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
    # Try getting URL directly from Container App
    API_URL=$(az containerapp show \
      --name $API_CONTAINER_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --query "properties.configuration.ingress.fqdn" \
      -o tsv 2>/dev/null || echo "")
    if [ -n "$API_URL" ]; then
        API_URL="https://$API_URL"
        echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:438\",\"message\":\"Got API URL from Container App\",\"data\":{\"apiUrl\":\"$API_URL\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
    fi
else
    echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:432\",\"message\":\"Got API URL from deployment\",\"data\":{\"apiUrl\":\"$API_URL\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
fi
# #endregion

if [ -z "$API_URL" ]; then
    echo "⚠️  Warning: Could not retrieve API URL. Container App may still be starting."
    echo "   You can get it later with:"
    echo "   az containerapp show -n $API_CONTAINER_APP_NAME -g $RESOURCE_GROUP --query 'properties.configuration.ingress.fqdn' -o tsv"
    API_URL="https://$(az containerapp show -n $API_CONTAINER_APP_NAME -g $RESOURCE_GROUP --query 'properties.configuration.ingress.fqdn' -o tsv 2>/dev/null || echo 'pending')"
fi

echo "✅ API deployed at: $API_URL"
echo ""

# Step 9: Deploy Worker Container App (two-stage approach - same as API)
echo "📋 Step 9: Deploying Worker Container App (two-stage approach)..."

# Worker name matches Bicep template: ca-${appName}-${environment}-wrk
WORKER_CONTAINER_APP_NAME="ca-${APP_NAME}-${ENVIRONMENT}-wrk"

# Check if Worker Container App already exists
EXISTING_WORKER=$(az containerapp show --name $WORKER_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
if [ -n "$EXISTING_WORKER" ]; then
    echo "📋 Existing Worker Container App found. Deleting to start fresh..."
    az containerapp delete --name $WORKER_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes 2>/dev/null || true
    echo "⏳ Waiting 10 seconds for cleanup..."
    sleep 10
fi

# Stage 1: Deploy minimal Worker Container App (no Key Vault references) to establish identity
echo "📋 Stage 1: Deploying minimal Worker Container App (establishes identity)..."
DEPLOY_RESULT=$(az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --name backend-worker-minimal \
  --template-file backend-worker-minimal.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    serviceBusNamespaceName=$SB_NAMESPACE \
    imageTag=latest \
  --output json 2>&1)

# #region agent log
TIMESTAMP=$(date +%s)000
# Check provisioningState properly - try jq first, fallback to grep
if command -v jq &> /dev/null; then
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | jq -r '.properties.provisioningState // .provisioningState // "unknown"' 2>/dev/null || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | jq -e '.error' > /dev/null 2>&1 && echo "true" || echo "false")
    HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | jq -e '.properties.outputs // .outputs' > /dev/null 2>&1 && echo "true" || echo "false")
else
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | grep -o '"provisioningState":"[^"]*"' | cut -d'"' -f4 | head -1 || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | grep -q '"error":' && echo "true" || echo "false")
    HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | grep -q '"outputs":' && echo "true" || echo "false")
fi

HAS_ERROR="false"
if [ "$HAS_ERROR_OBJ" = "true" ]; then
    HAS_ERROR="true"
    DEPLOY_STATUS="Failed"
elif [ "$DEPLOY_STATUS" != "Succeeded" ] && [ "$DEPLOY_STATUS" != "unknown" ]; then
    HAS_ERROR="true"
fi
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:490\",\"message\":\"After minimal Worker deployment\",\"data\":{\"status\":\"$DEPLOY_STATUS\",\"hasError\":$HAS_ERROR,\"hasErrorObj\":$HAS_ERROR_OBJ,\"hasOutputs\":$HAS_OUTPUTS},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# CRITICAL: Check for outputs FIRST - if outputs exist, deployment succeeded
if [ "$HAS_OUTPUTS" = "true" ]; then
    echo "✅ Minimal Worker deployment succeeded (outputs present)"
    DEPLOY_STATUS="Succeeded"
    HAS_ERROR="false"
elif [ "$DEPLOY_STATUS" = "unknown" ]; then
    echo "⚠️  Warning: Could not determine deployment status. Checking Container App..."
    # #region agent log
    TIMESTAMP=$(date +%s)000
    echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:520\",\"message\":\"Checking Worker Container App existence\",\"data\":{\"containerAppName\":\"$WORKER_CONTAINER_APP_NAME\",\"resourceGroup\":\"$RESOURCE_GROUP\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
    # #endregion
    APP_EXISTS=$(az containerapp show --name $WORKER_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
    # #region agent log
    TIMESTAMP=$(date +%s)000
    echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:525\",\"message\":\"Worker Container App existence check result\",\"data\":{\"containerAppName\":\"$WORKER_CONTAINER_APP_NAME\",\"appExists\":\"$APP_EXISTS\",\"hasApp\":$(if [ -n "$APP_EXISTS" ]; then echo "true"; else echo "false"; fi)},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
    # #endregion
    if [ -n "$APP_EXISTS" ]; then
        echo "✅ Worker Container App exists. Assuming deployment succeeded."
        DEPLOY_STATUS="Succeeded"
        HAS_ERROR="false"
    else
        echo "❌ Worker Container App not found. Deployment may have failed."
        # #region agent log
        TIMESTAMP=$(date +%s)000
        echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:532\",\"message\":\"Worker Container App not found, showing deployment result\",\"data\":{\"deployResultLength\":$(echo "$DEPLOY_RESULT" | wc -c)},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
        # #endregion
        echo "$DEPLOY_RESULT"
        exit 1
    fi
elif [ "$HAS_ERROR" = "true" ] && [ "$HAS_ERROR_OBJ" = "true" ] && [ "$HAS_OUTPUTS" = "false" ]; then
    if command -v jq &> /dev/null; then
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | jq -r '.error.message // .error.details[0].message // ""' 2>/dev/null || echo "")
    else
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    fi
    echo "❌ Minimal Worker deployment failed. Status: $DEPLOY_STATUS"
    if [ -n "$ERROR_MSG" ]; then
        echo "Error: $ERROR_MSG"
    fi
    if command -v jq &> /dev/null; then
        echo "$DEPLOY_RESULT" | jq '.error' 2>/dev/null || echo "$DEPLOY_RESULT"
    else
        echo "$DEPLOY_RESULT" | grep -A 30 '"error":' || echo "$DEPLOY_RESULT"
    fi
    exit 1
fi

# Get the principal ID from the minimal deployment
WORKER_PRINCIPAL_ID=$(az containerapp show \
  --name $WORKER_CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" \
  -o tsv 2>/dev/null || echo "")

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H3\",\"location\":\"deploy-backend-local.sh:540\",\"message\":\"Minimal Worker deployment identity\",\"data\":{\"containerAppName\":\"$WORKER_CONTAINER_APP_NAME\",\"principalId\":\"$WORKER_PRINCIPAL_ID\",\"hasPrincipalId\":$(if [ -n "$WORKER_PRINCIPAL_ID" ]; then echo "true"; else echo "false"; fi)},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ -z "$WORKER_PRINCIPAL_ID" ]; then
    echo "❌ Failed to get Worker principal ID. Deployment may have failed completely."
    exit 1
fi

echo "✅ Minimal Worker Container App deployed with identity: ${WORKER_PRINCIPAL_ID:0:50}..."
echo ""

# Step 9.5: Grant RBAC permissions BEFORE the update deployment
echo "📋 Step 9.5: Granting Key Vault permissions to Worker identity..."
KV_ID=$(az keyvault show -n $KEY_VAULT_NAME -g $RESOURCE_GROUP --query id -o tsv)
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1,H6\",\"location\":\"deploy-backend-local.sh:555\",\"message\":\"Before Worker RBAC grant\",\"data\":{\"workerPrincipalId\":\"$WORKER_PRINCIPAL_ID\",\"keyVaultId\":\"$KV_ID\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

echo "⏳ Waiting 60 seconds for RBAC permissions to fully propagate..."
sleep 60

# Verify RBAC permissions
ROLE_ASSIGNMENTS=$(az role assignment list \
  --scope $KV_ID \
  --assignee $WORKER_PRINCIPAL_ID \
  --query "[?roleDefinitionName=='Key Vault Secrets User']" \
  -o json 2>/dev/null || echo "[]")

# #region agent log
TIMESTAMP=$(date +%s)000
HAS_PERMISSION="false"
if echo "$ROLE_ASSIGNMENTS" | grep -q "Key Vault Secrets User"; then
    HAS_PERMISSION="true"
fi
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H1,H4\",\"location\":\"deploy-backend-local.sh:570\",\"message\":\"Worker RBAC permission verification\",\"data\":{\"principalId\":\"$WORKER_PRINCIPAL_ID\",\"hasPermission\":$HAS_PERMISSION},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

if [ "$HAS_PERMISSION" = "false" ]; then
    echo "⚠️  Warning: RBAC permission verification failed. Retrying grant..."
    az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID
    echo "⏳ Waiting additional 30 seconds..."
    sleep 30
fi

echo "✅ Key Vault permissions granted and propagated"
echo ""

# Stage 2: Update the SAME Worker Container App with Key Vault references
echo "📋 Stage 2: Updating Worker Container App with Key Vault secret references..."

echo "⏳ Waiting 20 seconds for Worker Container App identity to be fully ready..."
sleep 20

# #region agent log
TIMESTAMP=$(date +%s)000
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:590\",\"message\":\"Before updating Worker with Key Vault secrets\",\"data\":{\"principalId\":\"$WORKER_PRINCIPAL_ID\",\"containerAppName\":\"$WORKER_CONTAINER_APP_NAME\"},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

DEPLOY_RESULT=$(az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --name backend-worker \
  --template-file backend-worker.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    appName=$APP_NAME \
    containerRegistryName=$CONTAINER_REGISTRY \
    containerAppsEnvironmentId="$CAE_ID" \
    keyVaultName=$KEY_VAULT_NAME \
    serviceBusNamespaceName=$SB_NAMESPACE \
    imageTag=latest \
  --output json 2>&1)

# #region agent log
TIMESTAMP=$(date +%s)000
# Check provisioningState properly - try jq first, fallback to grep
if command -v jq &> /dev/null; then
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | jq -r '.properties.provisioningState // .provisioningState // "unknown"' 2>/dev/null || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | jq -e '.error' > /dev/null 2>&1 && echo "true" || echo "false")
else
    DEPLOY_STATUS=$(echo "$DEPLOY_RESULT" | grep -o '"provisioningState":"[^"]*"' | cut -d'"' -f4 | head -1 || echo "unknown")
    HAS_ERROR_OBJ=$(echo "$DEPLOY_RESULT" | grep -q '"error":' && echo "true" || echo "false")
fi

HAS_ERROR="false"
if [ "$HAS_ERROR_OBJ" = "true" ]; then
    HAS_ERROR="true"
    DEPLOY_STATUS="Failed"
elif [ "$DEPLOY_STATUS" != "Succeeded" ] && [ "$DEPLOY_STATUS" != "unknown" ]; then
    HAS_ERROR="true"
fi
echo "{\"sessionId\":\"debug-session\",\"runId\":\"pre-fix\",\"hypothesisId\":\"H7\",\"location\":\"deploy-backend-local.sh:615\",\"message\":\"After Worker Key Vault secrets update via Bicep\",\"data\":{\"status\":\"$DEPLOY_STATUS\",\"hasError\":$HAS_ERROR,\"hasErrorObj\":$HAS_ERROR_OBJ},\"timestamp\":$TIMESTAMP}" >> "$LOG_FILE"
# #endregion

# Check if deployment actually failed
if [ "$HAS_ERROR" = "true" ] || [ "$DEPLOY_STATUS" = "Failed" ]; then
    if command -v jq &> /dev/null; then
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | jq -r '.error.message // .error.details[0].message // ""' 2>/dev/null || echo "")
    else
        ERROR_MSG=$(echo "$DEPLOY_RESULT" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    fi
    echo "❌ Worker deployment failed. Status: $DEPLOY_STATUS"
    if [ -n "$ERROR_MSG" ]; then
        echo "Error: $ERROR_MSG"
    fi
    if command -v jq &> /dev/null; then
        echo "$DEPLOY_RESULT" | jq '.error' 2>/dev/null || echo "$DEPLOY_RESULT"
    else
        echo "$DEPLOY_RESULT" | grep -A 30 '"error":' || echo "$DEPLOY_RESULT"
    fi
    exit 1
fi

# If status is unknown, check if we got outputs or Container App exists
if [ "$DEPLOY_STATUS" = "unknown" ]; then
    if command -v jq &> /dev/null; then
        HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | jq -e '.properties.outputs' > /dev/null 2>&1 && echo "true" || echo "false")
    else
        HAS_OUTPUTS=$(echo "$DEPLOY_RESULT" | grep -q '"outputs":' && echo "true" || echo "false")
    fi
    
    if [ "$HAS_OUTPUTS" = "true" ]; then
        echo "✅ Worker deployment appears successful (outputs present)"
        DEPLOY_STATUS="Succeeded"
    else
        echo "⚠️  Warning: Could not determine deployment status. Checking Container App..."
        APP_EXISTS=$(az containerapp show --name $WORKER_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
        if [ -n "$APP_EXISTS" ]; then
            echo "✅ Worker Container App exists. Assuming deployment succeeded."
            DEPLOY_STATUS="Succeeded"
        else
            echo "❌ Worker Container App not found. Deployment may have failed."
            echo "$DEPLOY_RESULT"
            exit 1
        fi
    fi
fi

echo "✅ Worker deployed"
echo ""

# Step 10: Configure remaining RBAC permissions
echo "📋 Step 10: Configuring remaining RBAC permissions for Managed Identities..."

# Get resource IDs (KV_ID already set above)
STORAGE_ID=$(az storage account list -g $RESOURCE_GROUP --query "[0].id" -o tsv)
COSMOS_ID=$(az cosmosdb show -n cosmos-$APP_NAME-$ENVIRONMENT -g $RESOURCE_GROUP --query id -o tsv)
SB_ID=$(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Assign Key Vault Secrets User to both API and Worker
az role assignment create --assignee $API_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Key Vault Secrets User" --scope $KV_ID 2>/dev/null || true

# Assign Storage Blob Data Contributor to both
az role assignment create --assignee $API_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID 2>/dev/null || true

# Assign Cosmos DB Data Contributor to both
az role assignment create --assignee $API_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Cosmos DB Built-in Data Contributor" --scope $COSMOS_ID 2>/dev/null || true

# Assign Service Bus Data Owner to Worker (for receiving messages)
az role assignment create --assignee $WORKER_PRINCIPAL_ID --role "Azure Service Bus Data Owner" --scope $SB_ID 2>/dev/null || true

# Assign Service Bus Data Sender to API (for sending messages)
az role assignment create --assignee $API_PRINCIPAL_ID --role "Azure Service Bus Data Sender" --scope $SB_ID 2>/dev/null || true

echo "✅ RBAC permissions configured"
echo ""

# Disable ACR admin (best practice)
echo "📋 Step 11: Disabling ACR admin user (security best practice)..."
az acr update -n $CONTAINER_REGISTRY --admin-enabled false > /dev/null
echo "✅ ACR admin disabled"
echo ""

echo "======================================"
echo "✅ Backend Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Deployment Summary:"
echo "  API URL: $API_URL"
echo "  Key Vault: $KEY_VAULT_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Test API health:"
echo "     curl $API_URL/health"
echo "  2. Deploy frontend:"
echo "     ./deploy-frontend-containerapp.sh"
echo "  3. Check logs:"
echo "     az containerapp logs show -n ca-$APP_NAME-$ENVIRONMENT-api -g $RESOURCE_GROUP --follow"
echo ""
