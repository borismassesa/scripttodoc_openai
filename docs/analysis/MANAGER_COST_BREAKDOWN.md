# Azure Cost Breakdown - Script to Doc Application

**Period:** December 2025  
**Total Cost:** CA$266.30 (including tax)

---

## Detailed Cost Breakdown

| Service | Charges | With Tax | % of Total | Notes |
|---------|---------|----------|------------|-------|
| **Azure Container Apps** | **CA$136.01** | **CA$152.33** | **57%** | **Main cost driver - Compute resources** |
| ├─ API Container (0.5 CPU, 1 GB) | ~CA$68.00 | ~CA$76.16 | 29% | Always running (24/7) |
| └─ Worker Container (1.0 CPU, 2 GB) | ~CA$68.00 | ~CA$76.16 | 29% | Always running (24/7) |
| | | | | |
| **Azure Blob Storage** | ~CA$25.00 | ~CA$28.00 | 11% | File storage (transcripts, documents) |
| **Azure Service Bus** | ~CA$15.00 | ~CA$16.80 | 6% | Job queue (Standard tier) |
| **Application Insights** | ~CA$20.00 | ~CA$22.40 | 8% | Monitoring & logging |
| **Log Analytics Workspace** | ~CA$10.00 | ~CA$11.20 | 4% | Log aggregation |
| **Container Registry (Basic)** | CA$4.73 | CA$5.30 | 2% | Docker image storage |
| **Key Vault** | ~CA$5.00 | ~CA$5.60 | 2% | Secrets management |
| **Azure OpenAI** | CA$2.05 | CA$2.30 | 1% | AI content generation (GPT-4o-mini) |
| **Document Intelligence** | ~CA$5.00 | ~CA$5.60 | 2% | Structure analysis |
| **Cosmos DB (Serverless)** | CA$0.01 | CA$0.01 | <1% | Job status storage (very efficient) |
| **Data Transfer / Networking** | ~CA$10.00 | ~CA$11.20 | 4% | Outbound data transfer |
| **Other Azure Services** | ~CA$5.00 | ~CA$5.60 | 2% | Miscellaneous services |
| | | | | |
| **TOTAL** | **CA$237.77** | **CA$266.30** | **100%** | |

---

## Key Insights

### 🔴 Primary Cost Driver: Azure Container Apps (57%)

**Issue:** Both API and Worker containers are configured to run 24/7, even when idle.

**Current Configuration:**
- **API Container:** 0.5 CPU, 1 GB RAM, always running
- **Worker Container:** 1.0 CPU, 2 GB RAM, always running
- **Cost:** CA$136.01/month (CA$152.33 with tax)

**Problem:** Containers consume resources 730 hours/month even when not processing requests.

---

## Cost Optimization Opportunity

### ✅ Recommended Action: Enable Scale-to-Zero

**Change:** Configure containers to scale to zero when idle

**Expected Savings:**
- **Current Cost:** CA$136.01/month
- **Optimized Cost:** CA$25-40/month
- **Savings:** **CA$96-111/month (70-85% reduction)**
- **New Total:** CA$126-141/month (down from CA$266.30)

**Trade-off:**
- Cold start latency: 5-30 seconds when scaling from zero
- Acceptable for most use cases (background processing)

**Implementation:**
- Simple configuration change (30 minutes)
- No architecture changes required
- Can be reverted if needed

---

## Cost Breakdown by Category

| Category | Monthly Cost | % of Total | Notes |
|----------|-------------|------------|-------|
| **Compute (Container Apps)** | CA$152.33 | 57% | Can be reduced to CA$25-40 |
| **Storage & Data** | CA$39.20 | 15% | Blob Storage, Cosmos DB |
| **Monitoring & Logging** | CA$33.60 | 13% | Application Insights, Log Analytics |
| **Messaging** | CA$16.80 | 6% | Service Bus |
| **AI Services** | CA$7.90 | 3% | OpenAI, Document Intelligence |
| **Infrastructure** | CA$16.47 | 6% | Container Registry, Key Vault, Networking |
| **TOTAL** | **CA$266.30** | **100%** | |

---

## Comparison: Current vs. Optimized

| Scenario | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| **Current (Always-On)** | CA$266.30 | CA$3,195.60 | Both containers run 24/7 |
| **Optimized (Scale-to-Zero)** | CA$126-141 | CA$1,512-1,692 | Containers scale to zero when idle |
| **Savings** | **CA$125-140/month** | **CA$1,500-1,680/year** | **47-53% total cost reduction** |

---

## Alternative Hosting Options

| Option | Monthly Cost | Savings vs Current | Best For |
|--------|-------------|-------------------|----------|
| **Optimized Container Apps** | CA$126-141 | **47-53%** | Variable workloads (recommended) |
| **Azure App Service** | CA$100-120 | 55-62% | Steady, predictable traffic |
| **Azure VM** | CA$45-55 | 79-83% | Small scale, manual management |
| **Azure Functions** | CA$170-200 | -36% to -25% | Not recommended (more expensive) |

---

## Recommendations

### Immediate (This Week)
1. ✅ **Enable scale-to-zero** for Container Apps
   - Expected savings: CA$96-111/month
   - Implementation time: 30 minutes
   - Risk: Low (can revert if needed)

### Short-Term (This Month)
2. ✅ **Monitor costs** after optimization
   - Verify actual savings
   - Check for any performance issues

### Medium-Term (Next Quarter)
3. ⚠️ **Consider App Service migration** if:
   - Cold starts are problematic
   - Traffic becomes steady and predictable
   - Further cost reduction needed

---

## Questions?

For detailed technical analysis, see:
- [Full Cost Analysis](HOSTING_COST_ANALYSIS.md)
- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md)
- [Quick Reference](../../HOSTING_COST_SUMMARY.md)

---

**Prepared by:** Development Team  
**Date:** January 2025  
**Next Review:** February 2025
