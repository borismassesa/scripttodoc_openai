# Production Deployment Plan: ScriptToDoc on Azure (100% Microsoft)

**Version**: 2.0 - Azure Static Web Apps Edition
**Date**: December 11, 2025
**Target Go-Live**: [To be determined]
**Deployment Model**: Azure Static Web Apps (Frontend) + Azure Container Apps (Backend)

---

## 📋 Executive Summary

This deployment plan uses **100% Azure infrastructure** for both frontend and backend:
- **Azure Static Web Apps** hosting the Next.js frontend
- **Azure Container Apps** hosting the FastAPI backend
- **Estimated timeline**: 2-3 weeks
- **Team required**: 2-3 people (1 frontend, 1-2 backend/DevOps)

### Key Differences from Vercel Version

| Aspect | Vercel Version | Azure Version |
|--------|----------------|---------------|
| Frontend Hosting | Vercel Edge Network | Azure Static Web Apps |
| CDN | Vercel CDN | Azure Front Door (built-in) |
| SSL Certificates | Vercel automatic | Azure automatic |
| Custom Domains | Vercel DNS | Azure DNS or external |
| CI/CD | Vercel CLI + GitHub Actions | Azure Static Web Apps (native) |
| Cost | $0-20/month | $0-9/month (free tier available) |
| **Ecosystem** | **Mixed** | **100% Microsoft** ✅ |

### Benefits of All-Azure Approach

✅ **Single Vendor**: Everything in Microsoft ecosystem (easier IG approval)
✅ **Unified Billing**: One Azure invoice (easier finance approval)
✅ **Integrated Security**: Azure AD, Key Vault, Defender across entire stack
✅ **Better Compliance**: Data never leaves Azure (even frontend assets)
✅ **Cost Efficiency**: Azure Static Web Apps free tier (vs Vercel $20/month)
✅ **Simpler RBAC**: All access controlled via Azure AD

---

## 🏗️ Updated Architecture: 100% Azure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT LAYER                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  User's Browser                                                    │ │
│  │  ✅ Azure AD B2C authentication (OAuth 2.0)                       │ │
│  │  ✅ JWT tokens in httpOnly, secure cookies                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTPS (automatic)
                            │ Authorization: Bearer {JWT}
┌───────────────────────────┴─────────────────────────────────────────────┐
│            AZURE STATIC WEB APPS (Frontend)              ✅ AZURE        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Next.js Static Export                                            │ │
│  │  ✅ HTML/CSS/JS served via Azure CDN (Front Door)                │ │
│  │  ✅ NO sensitive data stored                                      │ │
│  │  ✅ NO database connections                                       │ │
│  │  ✅ NO API keys or secrets                                        │ │
│  │                                                                     │ │
│  │  Built-in Features:                                                │ │
│  │  ✅ Azure Front Door CDN (global)                                 │ │
│  │  ✅ DDoS protection (automatic)                                   │ │
│  │  ✅ Custom domains + SSL (free)                                   │ │
│  │  ✅ Staging environments (per PR)                                 │ │
│  │  ✅ GitHub Actions CI/CD (native)                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTPS to Azure Container Apps
                            │ Authorization: Bearer {JWT}
                            │ CORS: Only from *.azurestaticapps.net
                            │
┌───────────────────────────┴─────────────────────────────────────────────┐
│         AZURE CONTAINER APPS (Backend API)               ✅ AZURE        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application                                              │ │
│  │  ✅ HTTPS endpoint (TLS 1.2+ enforced)                           │ │
│  │  ✅ JWT token validation (every request)                         │ │
│  │  ✅ RBAC - Users can only access own data                        │ │
│  │  ✅ CORS validation (Static Web Apps origin only)                │ │
│  │  ✅ Managed Identity (no hardcoded keys)                         │ │
│  │  ✅ Audit logging (Application Insights)                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ Managed Identity
        ┌───────────────────┼───────────────────┬───────────────────┐
┌───────▼────────┐ ┌────────▼───────┐ ┌─────────▼──────┐ ┌─────▼──────┐
│ Azure Key      │ │ Azure Service  │ │ Cosmos DB      │ │ Blob       │
│ Vault          │ │ Bus            │ │                │ │ Storage    │
│ ✅ Secrets     │ │ ✅ Job queue   │ │ ✅ Jobs data   │ │ ✅ Files   │
└────────────────┘ └────────┬───────┘ └────────────────┘ └────────────┘
                            │
                   ┌────────▼──────────────────────────────────┐
                   │  Container Apps (Worker)    ✅ AZURE      │
                   │  ✅ Background processing                 │
                   └────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
┌───────▼──────────┐ ┌─────▼──────────┐ ┌─────▼──────────┐
│ Azure Document   │ │ Azure OpenAI   │ │ App Insights   │
│ Intelligence     │ │                │ │                │
│ ✅ Doc analysis  │ │ ✅ GPT-4o-mini │ │ ✅ Monitoring  │
└──────────────────┘ └────────────────┘ └────────────────┘

                    100% MICROSOFT AZURE ECOSYSTEM ✅
```

---

## 🚀 Updated Deployment Steps

### CHANGED: Frontend Deployment (Azure Static Web Apps)

**Phase 1: Create Static Web App Resource (Day 3)**

Add to your Bicep template (`deployment/azure-infrastructure.bicep`):

```bicep
// ==================== Azure Static Web App ====================
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: 'swa-${resourcePrefix}'
  location: 'eastus2'  // Or Central US for Static Web Apps
  sku: {
    name: 'Free'  // or 'Standard' for $9/month
    tier: 'Free'
  }
  properties: {
    repositoryUrl: 'https://github.com/YOUR_ORG/YOUR_REPO'
    branch: 'main'
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: ''  // No Azure Functions API
      outputLocation: 'out'  // Next.js static export output
    }
  }
}

// Output the Static Web App URL
output staticWebAppUrl string = staticWebApp.properties.defaultHostname
output staticWebAppDeploymentToken string = staticWebApp.listSecrets().properties.apiKey
```

**Deploy Infrastructure:**

```bash
# Deploy (includes new Static Web App resource)
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/azure-infrastructure.bicep \
  --parameters environment=prod

# Get Static Web App details
STATIC_WEB_APP_NAME=$(jq -r '.staticWebAppName.value' deployment/outputs-prod.json)
STATIC_WEB_APP_URL=$(jq -r '.staticWebAppUrl.value' deployment/outputs-prod.json)
DEPLOYMENT_TOKEN=$(jq -r '.staticWebAppDeploymentToken.value' deployment/outputs-prod.json)

echo "Static Web App URL: https://$STATIC_WEB_APP_URL"
echo "Deployment Token: $DEPLOYMENT_TOKEN"

# Save deployment token as GitHub secret
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "$DEPLOYMENT_TOKEN"
```

---

### CHANGED: Frontend Configuration

**Update `frontend/next.config.js` for Static Export:**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Enable static export for Azure Static Web Apps

  // Disable features not supported in static export
  images: {
    unoptimized: true  // Azure Static Web Apps doesn't support Image Optimization
  },

  // Environment variables (will be replaced at build time)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_AZURE_AD_CLIENT_ID: process.env.NEXT_PUBLIC_AZURE_AD_CLIENT_ID,
    NEXT_PUBLIC_AZURE_AD_TENANT_ID: process.env.NEXT_PUBLIC_AZURE_AD_TENANT_ID,
  },

  // Trailing slashes for Azure Static Web Apps routing
  trailingSlash: true,
}

module.exports = nextConfig
```

**Create `frontend/staticwebapp.config.json`:**

```json
{
  "routes": [
    {
      "route": "/api/*",
      "rewrite": "https://ca-scripttodoc-api-prod.YOUR_REGION.azurecontainerapps.io/api/*"
    },
    {
      "route": "/*",
      "headers": {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.azurecontainerapps.io https://login.microsoftonline.com; frame-ancestors 'none'"
      }
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/api/*", "/*.{css,scss,sass,js,ts,tsx,jsx,json,png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}"]
  },
  "globalHeaders": {
    "Access-Control-Allow-Origin": "https://ca-scripttodoc-api-prod.YOUR_REGION.azurecontainerapps.io",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  },
  "mimeTypes": {
    ".json": "application/json",
    ".js": "text/javascript",
    ".css": "text/css"
  }
}
```

---

### CHANGED: CI/CD Pipeline (GitHub Actions)

**Replace Vercel workflow with Azure Static Web Apps workflow:**

Create `.github/workflows/frontend-deploy-azure.yml`:

```yaml
name: Deploy Frontend to Azure Static Web Apps

on:
  push:
    branches:
      - main
      - staging
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-deploy-azure.yml'
  pull_request:
    types: [opened, synchronize, reopened, closed]
    branches:
      - main
  workflow_dispatch:

jobs:
  build_and_deploy:
    if: github.event_name == 'push' || (github.event_name == 'pull_request' && github.event.action != 'closed')
    runs-on: ubuntu-latest
    name: Build and Deploy

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Set environment variables
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "NEXT_PUBLIC_API_URL=${{ secrets.API_URL_PROD }}" >> $GITHUB_ENV
            echo "NEXT_PUBLIC_ENVIRONMENT=production" >> $GITHUB_ENV
          else
            echo "NEXT_PUBLIC_API_URL=${{ secrets.API_URL_STAGING }}" >> $GITHUB_ENV
            echo "NEXT_PUBLIC_ENVIRONMENT=staging" >> $GITHUB_ENV
          fi
          echo "NEXT_PUBLIC_AZURE_AD_CLIENT_ID=${{ secrets.AZURE_AD_CLIENT_ID }}" >> $GITHUB_ENV
          echo "NEXT_PUBLIC_AZURE_AD_TENANT_ID=${{ secrets.AZURE_AD_TENANT_ID }}" >> $GITHUB_ENV

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Build Next.js app
        run: |
          cd frontend
          npm run build

      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: 'upload'
          app_location: '/frontend'
          output_location: 'out'  # Next.js static export output
          skip_api_build: true  # No Azure Functions

      - name: Health check
        run: |
          echo "Waiting for deployment to complete..."
          sleep 30
          curl -f https://swa-scripttodoc-prod.azurestaticapps.net/ || exit 1

  close_pull_request:
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    name: Close Pull Request
    steps:
      - name: Close Pull Request
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          action: 'close'
```

---

### CHANGED: Environment Variables (GitHub Secrets)

**Update GitHub Secrets:**

Remove Vercel-specific secrets:
- ~~VERCEL_TOKEN~~
- ~~VERCEL_ORG_ID~~
- ~~VERCEL_PROJECT_ID_PROD~~

Add Azure Static Web Apps secrets:
```bash
# Get deployment token
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name swa-scripttodoc-prod \
  --resource-group rg-scripttodoc-prod \
  --query properties.apiKey -o tsv)

# Add to GitHub secrets
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "$DEPLOYMENT_TOKEN"

# Add API URLs
gh secret set API_URL_PROD --body "https://ca-scripttodoc-api-prod.YOUR_REGION.azurecontainerapps.io"
gh secret set API_URL_STAGING --body "https://ca-scripttodoc-api-staging.YOUR_REGION.azurecontainerapps.io"
```

---

### CHANGED: Backend CORS Configuration

**Update `backend/api/main.py` to allow Azure Static Web Apps origin:**

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration (allow Azure Static Web Apps)
allowed_origins = [
    "https://swa-scripttodoc-prod.azurestaticapps.net",  # Production
    "https://swa-scripttodoc-staging.azurestaticapps.net",  # Staging
    "http://localhost:3000"  # Local development
]

# Also allow PR preview environments
# Azure Static Web Apps creates URLs like: https://happy-ocean-12345.azurestaticapps.net
if os.environ.get("ENVIRONMENT") != "production":
    allowed_origins.append("https://*.azurestaticapps.net")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

---

## 💰 Updated Cost Comparison

### Monthly Costs (100 jobs/month)

| Service | Vercel Version | Azure Version | Difference |
|---------|----------------|---------------|------------|
| **Frontend Hosting** | Vercel Pro: $20 | Azure Static Web Apps Free: $0 | **-$20** ✅ |
| **Backend (Container Apps)** | $30-50 | $30-50 | Same |
| **Storage (Cosmos + Blob)** | $15-30 | $15-30 | Same |
| **AI Services** | $50-100 | $50-100 | Same |
| **Networking** | $5-10 | $5-10 | Same |
| **Monitoring** | $5-10 | $5-10 | Same |
| **TOTAL** | **$125-220/month** | **$105-200/month** | **-$20/month** ✅ |

**Annual Savings: $240** by using Azure Static Web Apps free tier!

---

## ✅ Benefits of All-Azure Architecture

### 1. **Unified Ecosystem** ✅
- Everything in Azure Portal (single pane of glass)
- Unified Azure AD authentication across all services
- Single Azure bill (easier procurement)

### 2. **Better Security Posture** ✅
- No data leaves Azure (frontend assets also in Azure)
- Azure Defender can monitor entire stack
- Azure Policy can enforce compliance across all resources
- All RBAC managed through Azure AD

### 3. **Easier IG Approval** ✅
- "100% Microsoft Azure" sounds better than "Azure + Vercel"
- No third-party vendor risk assessment needed
- Data residency guaranteed (Azure region)

### 4. **Cost Efficiency** ✅
- Azure Static Web Apps free tier (vs Vercel $20/month)
- Potential Azure consumption commitment discounts
- Bundled support (if you have Azure support plan)

### 5. **Better Integration** ✅
- Native GitHub integration (same as Vercel)
- Automatic staging environments per PR
- Built-in Azure Front Door CDN
- Easy custom domain setup with Azure DNS

### 6. **Simplified Operations** ✅
- One less vendor to manage
- One set of credentials
- Unified monitoring (Application Insights for everything)
- Consistent deployment model

---

## 🎯 Updated Pre-Launch Checklist

**Infrastructure (All Azure):**
- [ ] Azure Static Web App created
- [ ] Custom domain configured (optional)
- [ ] SSL certificate issued (automatic)
- [ ] Frontend deployed and accessible
- [ ] Backend API CORS updated for Static Web App origin
- [ ] GitHub Actions workflow working
- [ ] Staging environment configured (PR previews)

**Remove Vercel Dependencies:**
- [ ] Remove `vercel.json` (replaced with `staticwebapp.config.json`)
- [ ] Remove Vercel CLI from scripts
- [ ] Remove Vercel GitHub secrets
- [ ] Update documentation (remove Vercel references)

---

## 📊 Feature Comparison

| Feature | Vercel | Azure Static Web Apps | Winner |
|---------|--------|----------------------|--------|
| **Static Site Hosting** | ✅ | ✅ | Tie |
| **Next.js Support** | ✅ Full (SSR/ISR) | ⚠️ Static export only | Vercel |
| **Custom Domains** | ✅ Free | ✅ Free | Tie |
| **SSL Certificates** | ✅ Auto | ✅ Auto | Tie |
| **Global CDN** | ✅ Edge Network | ✅ Azure Front Door | Tie |
| **CI/CD** | ✅ Native | ✅ GitHub Actions | Tie |
| **Staging (PR Preview)** | ✅ | ✅ | Tie |
| **Free Tier** | ❌ ($20/month) | ✅ (100 GB/month) | **Azure** ✅ |
| **Microsoft Ecosystem** | ❌ Third-party | ✅ Native | **Azure** ✅ |
| **IG Approval** | ⚠️ Requires review | ✅ Easier | **Azure** ✅ |
| **Ease of Use** | ✅ Very easy | ✅ Easy | Tie |

**Recommendation**: Use **Azure Static Web Apps** unless you need SSR/ISR features.

---

## 🚀 Quick Start (Azure Version)

```bash
# 1. Deploy infrastructure (includes Static Web App)
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/azure-infrastructure.bicep \
  --parameters environment=prod

# 2. Update frontend for static export
cd frontend
# Edit next.config.js (add output: 'export')
# Create staticwebapp.config.json

# 3. Configure GitHub Actions
# Add AZURE_STATIC_WEB_APPS_API_TOKEN secret
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "$(az staticwebapp secrets list ...)"

# 4. Push to GitHub (triggers deployment)
git add .
git commit -m "feat: migrate frontend to Azure Static Web Apps"
git push origin main

# 5. Verify deployment
curl https://swa-scripttodoc-prod.azurestaticapps.net/
```

---

## 📝 Migration from Vercel (If Already Deployed)

### Step 1: Create Azure Static Web App
```bash
az staticwebapp create \
  --name swa-scripttodoc-prod \
  --resource-group rg-scripttodoc-prod \
  --location eastus2 \
  --sku Free \
  --source https://github.com/YOUR_ORG/YOUR_REPO \
  --branch main \
  --app-location frontend \
  --output-location out
```

### Step 2: Update Frontend Code
```bash
# Update next.config.js
# Create staticwebapp.config.json
# Update environment variables
```

### Step 3: Update Backend CORS
```python
# Change allowed_origins from vercel.app to azurestaticapps.net
```

### Step 4: Deploy
```bash
# Push to GitHub (triggers Azure Static Web Apps deployment)
git push origin main
```

### Step 5: Test
```bash
# Test new Azure URL
curl https://swa-scripttodoc-prod.azurestaticapps.net/

# If working, update DNS to point to Azure
```

### Step 6: Decommission Vercel
```bash
# Delete Vercel project
vercel rm scripttodoc-prod --yes

# Remove GitHub secrets
gh secret delete VERCEL_TOKEN
```

---

## 🎉 Result: 100% Microsoft Azure Stack

**Frontend**: Azure Static Web Apps ✅
**Backend API**: Azure Container Apps ✅
**Background Jobs**: Azure Container Apps ✅
**Database**: Azure Cosmos DB ✅
**File Storage**: Azure Blob Storage ✅
**Message Queue**: Azure Service Bus ✅
**AI Services**: Azure OpenAI + Document Intelligence ✅
**Authentication**: Azure AD B2C ✅
**Secrets**: Azure Key Vault ✅
**Monitoring**: Azure Application Insights ✅
**CDN**: Azure Front Door (built into Static Web Apps) ✅

**🎯 100% Microsoft Azure - Perfect for your Microsoft-centric organization!**

---

**Document Status**: Ready for Execution
**Next Action**: Choose Azure Static Web Apps or keep Vercel
**Recommendation**: Go with Azure Static Web Apps for 100% Microsoft stack
