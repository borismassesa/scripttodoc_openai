# Hosting Cost Summary - Quick Reference

## Current Situation

**Monthly Cost:** CA$266.30 (US$197.50)  
**Container Apps Cost:** CA$136.01 (57% of total)  
**Problem:** Both API and Worker run 24/7 (minReplicas: 1)

## Quick Fix: Scale to Zero

**Change:** Set `minReplicas: 0` in both Container Apps  
**Savings:** CA$111-127/month (70-85% reduction)  
**New Cost:** CA$25-40/month  
**Time to Implement:** 30 minutes  
**Risk:** Low (cold starts 5-30 seconds)

## Cost Comparison

| Option | Monthly Cost (CAD) | Savings | Cold Starts |
|--------|-------------------|---------|-------------|
| Current | CA$136 | - | No |
| **Optimized (Recommended)** | **CA$25-40** | **70-85%** | Yes (5-30s) |
| App Service | CA$100-120 | 12-26% | No |
| Functions | CA$170-200 | -25% | Yes (5-10s) |
| VM | CA$45-55 | 60-67% | No |

## Implementation

### 1. Update `deployment/backend-api.bicep`:
```bicep
scale: {
  minReplicas: 0  // Change from 1
  maxReplicas: 10
}
```

### 2. Update `deployment/backend-worker.bicep`:
```bicep
scale: {
  minReplicas: 0  // Change from 1
  maxReplicas: 5
}
```

### 3. Deploy:
```bash
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/backend-api.bicep \
  --parameters environment=prod appName=scripttodoc

az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/backend-worker.bicep \
  --parameters environment=prod appName=scripttodoc
```

## Full Analysis

See [docs/analysis/HOSTING_COST_ANALYSIS.md](docs/analysis/HOSTING_COST_ANALYSIS.md) for detailed comparison of all hosting options.
