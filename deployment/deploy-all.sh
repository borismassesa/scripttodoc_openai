#!/bin/bash

# Master Deployment Script for ScriptToDoc
# This script orchestrates the complete deployment of both frontend and backend
# Run this script to deploy everything in the correct order

set -e

echo "🚀 ScriptToDoc Complete Deployment"
echo "=================================="
echo ""
echo "This script will deploy:"
echo "  1. Azure Infrastructure"
echo "  2. Secrets to Key Vault"
echo "  3. Backend (API + Worker)"
echo "  4. Frontend"
echo "  5. CORS Configuration"
echo ""
echo "Estimated time: 40-55 minutes"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Check prerequisites
echo ""
echo "=========================================="
echo "Step 1: Checking Prerequisites"
echo "=========================================="
if ! ./check-prerequisites.sh; then
    echo "❌ Prerequisites check failed. Please fix the issues above."
    exit 1
fi
echo ""

# Step 2: Check deployment state
echo ""
echo "=========================================="
echo "Step 2: Checking Current Deployment State"
echo "=========================================="
./check-deployment-state.sh
echo ""

# Step 3: Deploy infrastructure
echo ""
echo "=========================================="
echo "Step 3: Deploying Azure Infrastructure"
echo "=========================================="
read -p "Deploy infrastructure? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./deploy-infrastructure.sh
else
    echo "⏭️  Skipping infrastructure deployment"
fi
echo ""

# Step 4: Store secrets
echo ""
echo "=========================================="
echo "Step 4: Storing Secrets in Key Vault"
echo "=========================================="
read -p "Store secrets in Key Vault? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./store-secrets.sh
else
    echo "⏭️  Skipping secrets storage"
fi
echo ""

# Step 5: Deploy backend
echo ""
echo "=========================================="
echo "Step 5: Deploying Backend (API + Worker)"
echo "=========================================="
read -p "Deploy backend? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./deploy-backend-local.sh
    
    # Get API URL for frontend deployment
    RESOURCE_GROUP="rg-scripttodoc-prod"
    API_URL=$(az containerapp show \
        -n ca-scripttodoc-prod-api \
        -g $RESOURCE_GROUP \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv 2>/dev/null || echo "")
    
    if [ -n "$API_URL" ]; then
        echo ""
        echo "✅ API deployed at: https://$API_URL"
        export API_URL="https://$API_URL"
    else
        echo "⚠️  Could not retrieve API URL. You may need to set it manually."
    fi
else
    echo "⏭️  Skipping backend deployment"
fi
echo ""

# Step 6: Deploy frontend
echo ""
echo "=========================================="
echo "Step 6: Deploying Frontend"
echo "=========================================="
read -p "Deploy frontend? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -z "$API_URL" ]; then
        echo "⚠️  API URL not set. Getting from Azure..."
        RESOURCE_GROUP="rg-scripttodoc-prod"
        API_URL=$(az containerapp show \
            -n ca-scripttodoc-prod-api \
            -g $RESOURCE_GROUP \
            --query "properties.configuration.ingress.fqdn" \
            -o tsv 2>/dev/null || echo "")
        
        if [ -z "$API_URL" ]; then
            echo "❌ Could not get API URL. Please deploy backend first or set API_URL environment variable."
            exit 1
        fi
        API_URL="https://$API_URL"
    fi
    
    # Update deploy script with API URL
    sed -i.bak "s|API_URL=.*|API_URL=\"$API_URL\"|" deploy-frontend-containerapp.sh
    ./deploy-frontend-containerapp.sh
    rm -f deploy-frontend-containerapp.sh.bak
else
    echo "⏭️  Skipping frontend deployment"
fi
echo ""

# Step 7: Update CORS
echo ""
echo "=========================================="
echo "Step 7: Updating API CORS Settings"
echo "=========================================="
read -p "Update CORS settings? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./update-cors.sh
else
    echo "⏭️  Skipping CORS update"
fi
echo ""

# Final summary
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""

RESOURCE_GROUP="rg-scripttodoc-prod"

# Get URLs
API_URL=$(az containerapp show \
    -n ca-scripttodoc-prod-api \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv 2>/dev/null || echo "")

FRONTEND_URL=$(az containerapp show \
    -n ca-scripttodoc-prod-frontend \
    -g $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv 2>/dev/null || echo "")

echo "📋 Deployment Summary:"
if [ -n "$API_URL" ]; then
    echo "  🔌 API URL: https://$API_URL"
fi
if [ -n "$FRONTEND_URL" ]; then
    echo "  🌐 Frontend URL: https://$FRONTEND_URL"
fi
echo ""

echo "📝 Next Steps:"
echo "  1. Test the deployment:"
if [ -n "$FRONTEND_URL" ]; then
    echo "     Visit: https://$FRONTEND_URL"
fi
echo "  2. Check logs if needed:"
echo "     ./check-logs.sh"
echo "  3. Monitor Application Insights in Azure Portal"
echo ""
