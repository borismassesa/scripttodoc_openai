#!/bin/bash

# Test Deployment Script
# This script tests the deployed application end-to-end

set -e

RESOURCE_GROUP="rg-scripttodoc-prod"
APP_NAME="scripttodoc"
ENVIRONMENT="prod"

echo "🧪 Testing ScriptToDoc Deployment"
echo "================================"
echo ""

ERRORS=0

# Get URLs
echo "📋 Getting deployment URLs..."
API_APP="ca-$APP_NAME-$ENVIRONMENT-api"
FRONTEND_APP="ca-$APP_NAME-$ENVIRONMENT-frontend"

API_URL=$(az containerapp show \
    -n $API_APP \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv 2>/dev/null || echo "")

FRONTEND_URL=$(az containerapp show \
    -n $FRONTEND_APP \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv 2>/dev/null || echo "")

if [ -z "$API_URL" ]; then
    echo "❌ API Container App not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ API URL: https://$API_URL"
fi

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ Frontend Container App not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Frontend URL: https://$FRONTEND_URL"
fi
echo ""

# Test API Health
if [ -n "$API_URL" ]; then
    echo "📋 Testing API health endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$API_URL/health" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ API health check passed (HTTP $HTTP_CODE)"
        
        # Get health response
        HEALTH_RESPONSE=$(curl -s "https://$API_URL/health")
        echo "   Response: $HEALTH_RESPONSE"
    else
        echo "❌ API health check failed (HTTP $HTTP_CODE)"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
fi

# Test Frontend
if [ -n "$FRONTEND_URL" ]; then
    echo "📋 Testing frontend..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_URL" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Frontend is accessible (HTTP $HTTP_CODE)"
    else
        echo "❌ Frontend check failed (HTTP $HTTP_CODE)"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
fi

# Test CORS
if [ -n "$API_URL" ] && [ -n "$FRONTEND_URL" ]; then
    echo "📋 Testing CORS configuration..."
    CORS_RESPONSE=$(curl -s -X OPTIONS \
        -H "Origin: https://$FRONTEND_URL" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -o /dev/null -w "%{http_code}" \
        "https://$API_URL/health" || echo "000")
    
    if [ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ]; then
        echo "✅ CORS preflight check passed"
    else
        echo "⚠️  CORS preflight check returned HTTP $CORS_RESPONSE"
        echo "   This may be normal if CORS is configured differently"
    fi
    echo ""
fi

# Check Container App status
echo "📋 Checking Container App status..."
for APP in "$API_APP" "ca-$APP_NAME-$ENVIRONMENT-wrk" "$FRONTEND_APP"; do
    if az containerapp show -n $APP -g $RESOURCE_GROUP &> /dev/null; then
        STATUS=$(az containerapp show -n $APP -g $RESOURCE_GROUP \
            --query "properties.runningStatus" -o tsv 2>/dev/null || echo "unknown")
        REPLICAS=$(az containerapp show -n $APP -g $RESOURCE_GROUP \
            --query "properties.runningStatusDetails.activeReplicasCount" -o tsv 2>/dev/null || echo "0")
        
        if [ "$STATUS" = "Running" ] || [ "$STATUS" = "Healthy" ]; then
            echo "✅ $APP: $STATUS ($REPLICAS replicas)"
        else
            echo "⚠️  $APP: $STATUS ($REPLICAS replicas)"
        fi
    else
        echo "❌ $APP: Not found"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check Key Vault secrets
echo "📋 Checking Key Vault secrets..."
KEY_VAULT_NAME=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name azure-infrastructure \
    --query 'properties.outputs.keyVaultName.value' \
    -o tsv 2>/dev/null || echo "")

if [ -n "$KEY_VAULT_NAME" ]; then
    REQUIRED_SECRETS=(
        "azure-openai-key"
        "azure-openai-endpoint"
        "azure-di-key"
        "azure-storage-connection-string"
        "azure-cosmos-connection-string"
        "azure-service-bus-connection-string"
    )
    
    MISSING=0
    for SECRET in "${REQUIRED_SECRETS[@]}"; do
        if az keyvault secret show --vault-name $KEY_VAULT_NAME --name $SECRET &> /dev/null; then
            echo "   ✅ $SECRET"
        else
            echo "   ❌ $SECRET (missing)"
            MISSING=$((MISSING + 1))
        fi
    done
    
    if [ $MISSING -eq 0 ]; then
        echo "✅ All required secrets present"
    else
        echo "❌ $MISSING secret(s) missing"
        ERRORS=$((ERRORS + MISSING))
    fi
else
    echo "⚠️  Key Vault not found"
fi
echo ""

# Summary
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "🌐 Access your application:"
    if [ -n "$FRONTEND_URL" ]; then
        echo "   Frontend: https://$FRONTEND_URL"
    fi
    if [ -n "$API_URL" ]; then
        echo "   API: https://$API_URL"
        echo "   API Docs: https://$API_URL/docs"
    fi
    exit 0
else
    echo "❌ Found $ERRORS issue(s). Please review the errors above."
    exit 1
fi
