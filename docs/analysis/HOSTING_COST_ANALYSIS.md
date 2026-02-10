# Hosting Cost Analysis: Script to Doc Application

**Date:** January 2025  
**Current Monthly Cost:** CA$266.30 (US$197.50)  
**Primary Cost Driver:** Azure Container Apps (57% of total)

---

## Executive Summary

Your current Azure Container Apps deployment is costing **CA$136.01/month** (CA$152.33 with tax) for compute resources. This represents **57% of your total monthly bill**. The main issue is that both API and Worker containers are configured with `minReplicas: 1`, meaning they run 24/7 even when idle.

### Key Findings

- **Current Container Apps Cost:** CA$136.01/month (US$101/month)
- **Optimized Container Apps Cost:** CA$20-40/month (US$15-30/month) - **70-85% savings**
- **Azure App Service Alternative:** CA$100-120/month (US$73-90/month)
- **Azure Functions Alternative:** CA$170-200/month (US$125-150/month) - *Not recommended due to high cost*
- **Azure VM Alternative:** CA$45-55/month (US$34-41/month)

**Recommendation:** Optimize current Container Apps setup first (scale to zero), then consider App Service or VM for further cost reduction if needed.

---

## Current Cost Breakdown (December 2025 Invoice)

| Service | Charges | With Tax | % of Total | Notes |
|---------|---------|----------|------------|-------|
| **Azure Container Apps** | CA$136.01 | CA$152.33 | **57%** | Main cost driver |
| Container Registry (Basic) | CA$4.73 | CA$5.30 | 2% | Minimal cost |
| Azure OpenAI | CA$2.05 | CA$2.30 | 1% | Usage-based |
| Cosmos DB (Serverless) | CA$0.01 | CA$0.01 | <1% | Very efficient |
| **Other Services** | ~CA$95.00 | ~CA$108.26 | 40% | Storage, Service Bus, etc. |
| **TOTAL** | **CA$237.77** | **CA$266.30** | **100%** | |

### Current Container Apps Configuration

**API Container App:**
- CPU: 0.5 cores
- Memory: 1 GB
- Min Replicas: **1** (always running)
- Max Replicas: 10
- Estimated cost: **CA$68/month** (US$50/month)

**Worker Container App:**
- CPU: 1.0 core
- Memory: 2 GB
- Min Replicas: **1** (always running)
- Max Replicas: 5
- Estimated cost: **CA$68/month** (US$50/month)

**Problem:** Both containers run 24/7 (730 hours/month) even when idle, consuming:
- API: 0.5 vCPU × 730 hours = 365 vCPU-hours/month
- Worker: 1.0 vCPU × 730 hours = 730 vCPU-hours/month
- Total: 1,095 vCPU-hours/month

---

## Cost Comparison: Hosting Alternatives

### Option 1: Optimized Container Apps (Recommended First Step)

**Changes:**
- Set `minReplicas: 0` for both API and Worker
- Enable scale-to-zero during idle periods
- Keep current architecture and features

**Cost Calculation:**

**API Container App (Scale to Zero):**
- Assumed usage: 8 hours/day active (240 hours/month)
- vCPU-seconds: 0.5 × 240 × 3600 = 432,000 vCPU-seconds
- After free tier (180,000): 252,000 billable
- Cost: 252,000 × $0.000024 = **US$6.05/month** (CA$8.15)

**Worker Container App (Scale to Zero):**
- Assumed usage: 4 hours/day active (120 hours/month)
- vCPU-seconds: 1.0 × 120 × 3600 = 432,000 vCPU-seconds
- After free tier (180,000): 252,000 billable
- Cost: 252,000 × $0.000024 = **US$6.05/month** (CA$8.15)

**Memory Costs:**
- API: 1 GB × 240 hours × 3600 = 864,000 GiB-seconds
- After free tier (360,000): 504,000 billable
- Cost: 504,000 × $0.000003 = **US$1.51/month** (CA$2.04)

- Worker: 2 GB × 120 hours × 3600 = 864,000 GiB-seconds
- After free tier (360,000): 504,000 billable
- Cost: 504,000 × $0.000003 = **US$1.51/month** (CA$2.04)

**HTTP Requests:**
- Assumed: 100,000 requests/month (well within free tier)
- Cost: **US$0/month**

**Total Optimized Container Apps Cost:**
- Compute: US$15.12/month (CA$20.38)
- **Estimated Total: CA$25-40/month** (including overhead)

**Savings:** **CA$111-127/month** (70-85% reduction)

**Pros:**
- ✅ No architecture changes needed
- ✅ Keep all current features (auto-scaling, Service Bus integration)
- ✅ Scale to zero when idle
- ✅ Easy to implement (just change minReplicas)

**Cons:**
- ⚠️ Cold start latency (5-30 seconds) when scaling from zero
- ⚠️ Still more expensive than App Service for steady workloads

---

### Option 2: Azure App Service (Linux)

**Configuration:**
- **API:** App Service Plan (Basic B1 or Standard S1)
- **Worker:** Same plan or separate Basic B1
- Container-based deployment (Docker)

**Cost Calculation:**

**Basic B1 Plan (Shared):**
- 1 vCPU, 1.75 GB RAM
- Cost: **US$13/month** (CA$17.50)
- Suitable for: API only (low traffic)

**Standard S1 Plan (Dedicated):**
- 1 vCPU, 1.75 GB RAM
- Cost: **US$73/month** (CA$98.50)
- Suitable for: Production API + Worker

**Standard S1 (2 instances):**
- API + Worker on same plan
- Cost: **US$73/month** (CA$98.50)
- Can run both containers on same plan

**Recommended Setup:**
- **Standard S1 Plan:** US$73/month (CA$98.50)
- Run both API and Worker on same plan
- **Total: CA$100-120/month** (including overhead)

**Pros:**
- ✅ Predictable pricing (no per-second billing)
- ✅ No cold starts
- ✅ Built-in CI/CD
- ✅ Easy scaling (manual or auto-scale)
- ✅ Lower cost for steady workloads

**Cons:**
- ⚠️ Always-on (can't scale to zero)
- ⚠️ Less flexible than Container Apps
- ⚠️ Manual scaling configuration
- ⚠️ Less cost-effective for variable workloads

**Best For:** Steady, predictable workloads with consistent traffic

---

### Option 3: Azure Functions (Serverless)

**Configuration:**
- **API:** Azure Functions Premium Plan (for HTTP triggers)
- **Worker:** Azure Functions Consumption Plan (for queue triggers)

**Why Premium Plan for API?**

The Premium Plan is used for the API because:

1. **Always-Warm Instances:** Premium Plan keeps at least one instance always running, eliminating cold starts for HTTP endpoints. This is critical for API responsiveness.

2. **FastAPI Compatibility:** FastAPI applications benefit from always-on instances. Consumption Plan would cause 5-30 second cold starts on every request when scaled to zero, which is unacceptable for API endpoints.

3. **HTTP Trigger Performance:** Premium Plan provides better performance for HTTP triggers compared to Consumption Plan, which is optimized for event-driven scenarios.

**Alternative: Consumption Plan for API**
- **Cost:** Would be much cheaper (~US$5-20/month depending on usage)
- **Trade-off:** 5-30 second cold starts on first request after idle period
- **Verdict:** Not recommended for production APIs due to poor user experience

**Cost Calculation:**

**Functions Premium Plan (API):**
- Base cost: **US$0.173/hour** = **US$125/month** (CA$168.50)
- Includes: 1 vCPU, 3.5 GB RAM (always-warm)
- Additional instances: US$0.173/hour each
- **Why expensive:** You pay for always-on instances even when idle

**Functions Consumption Plan (Worker):**
- Pay per execution: **US$0.000016/GB-second**
- Assumed: 1,000 jobs/month × 2 minutes × 2 GB = 4,000 GB-seconds
- Cost: 4,000 × $0.000016 = **US$0.06/month** (CA$0.08)
- **Why cheap:** Only pays for actual execution time, scales to zero

**Total Functions Cost:**
- Premium Plan: US$125/month (CA$168.50)
- Consumption Plan: US$0.06/month (CA$0.08)
- **Total: CA$170-200/month** (including overhead)

**Pros:**
- ✅ True serverless (scale to zero for Worker)
- ✅ Pay only for execution time (Worker)
- ✅ Automatic scaling
- ✅ Built-in queue triggers

**Cons:**
- ❌ **Very expensive for API** (Premium Plan required)
- ❌ Cold starts if using Consumption Plan for API (unacceptable)
- ❌ Complex setup for FastAPI (requires Azure Functions Python worker)
- ❌ Less suitable for long-running processes (10-minute timeout on Consumption)
- ❌ **Not cost-effective compared to other options**

**Best For:** Event-driven workloads with infrequent API calls (not recommended for this use case)

---

### Option 4: Azure Virtual Machine

**Configuration:**
- **VM Size:** Standard_B2s (2 vCPU, 4 GB RAM)
- **OS:** Ubuntu Server 22.04 LTS
- **Deployment:** Docker Compose (API + Worker)

**Cost Calculation:**

**Standard_B2s VM:**
- Cost: **US$0.042/hour** = **US$30.66/month** (CA$41.30)
- Storage: 30 GB SSD = **US$3/month** (CA$4.05)
- **Total: CA$45-55/month** (including overhead)

**Pros:**
- ✅ Full control over environment
- ✅ Lowest cost for always-on workloads
- ✅ Can run multiple services on one VM
- ✅ Predictable pricing

**Cons:**
- ❌ Manual management (updates, security)
- ❌ No auto-scaling
- ❌ Single point of failure
- ❌ Requires DevOps expertise
- ❌ No built-in load balancing

**Best For:** Small-scale deployments with low traffic and technical expertise

---

### Option 5: Hybrid Approach

**Configuration:**
- **API:** Azure App Service (Standard S1) - US$73/month
- **Worker:** Azure Functions (Consumption) - US$0.06/month
- **Total: CA$100-120/month**

**Pros:**
- ✅ Best of both worlds
- ✅ API always available (no cold starts)
- ✅ Worker scales to zero (cost-effective)
- ✅ Optimized for each workload type

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Two different platforms to manage

---

## Detailed Cost Comparison Table

| Option | Monthly Cost (CAD) | Monthly Cost (USD) | Savings vs Current | Cold Starts | Complexity | Best For |
|--------|-------------------|-------------------|-------------------|-------------|------------|----------|
| **Current (Container Apps)** | **CA$136** | **US$101** | Baseline | No | Low | - |
| **Optimized Container Apps** | **CA$25-40** | **US$19-30** | **70-85%** | Yes (5-30s) | Low | Variable workloads |
| **App Service (Standard S1)** | **CA$100-120** | **US$73-90** | **12-26%** | No | Low | Steady workloads |
| **Functions (Premium)** | **CA$170-200** | **US$125-150** | -25% | Yes (5-10s) | Medium | Event-driven |
| **VM (Standard_B2s)** | **CA$45-55** | **US$34-41** | **60-67%** | No | High | Small scale |
| **Hybrid (App Service + Functions)** | **CA$100-120** | **US$73-90** | **12-26%** | Worker only | Medium | Mixed workloads |

---

## Recommendations

### Immediate Action (Week 1): Optimize Container Apps

**Priority: HIGH** - Can save **CA$111-127/month** immediately

1. **Change `minReplicas` to 0** in both Bicep templates:
   ```bicep
   scale: {
     minReplicas: 0  // Changed from 1
     maxReplicas: 10
   }
   ```

2. **Add HTTP scaling rule** for API:
   ```bicep
   rules: [
     {
       name: 'http-rule'
       http: {
         metadata: {
           concurrentRequests: '10'  // Scale up at 10 concurrent requests
         }
       }
     }
   ]
   ```

3. **Keep Service Bus scaling** for Worker (already configured)

4. **Expected Result:**
   - Cost reduction: **70-85%** (CA$136 → CA$25-40/month)
   - Cold start latency: 5-30 seconds (acceptable for most use cases)
   - No architecture changes needed

### Medium-Term (Month 2-3): Evaluate App Service

**Priority: MEDIUM** - If optimized Container Apps still too expensive

1. **Migrate to Azure App Service** if:
   - Traffic is steady and predictable
   - Cold starts are unacceptable
   - You need guaranteed availability

2. **Keep Container Apps** if:
   - Traffic is variable/spiky
   - Cost is acceptable after optimization
   - You value auto-scaling features

### Long-Term (Month 4+): Consider Hybrid

**Priority: LOW** - Only if specific requirements emerge

1. **Hybrid approach** (App Service + Functions) if:
   - API needs to be always-on
   - Worker has very infrequent jobs
   - You want to optimize each component separately

---

## Implementation Guide: Optimize Container Apps

### Step 1: Update Backend API Bicep

**File:** `deployment/backend-api.bicep`

```bicep
scale: {
  minReplicas: 0  // Change from 1
  maxReplicas: 10
  rules: [
    {
      name: 'http-rule'
      http: {
        metadata: {
          concurrentRequests: '10'  // Scale up when 10+ concurrent requests
        }
      }
    }
  ]
}
```

### Step 2: Update Worker Bicep

**File:** `deployment/backend-worker.bicep`

```bicep
scale: {
  minReplicas: 0  // Change from 1
  maxReplicas: 5
  rules: [
    {
      name: 'queue-scaling'
      custom: {
        type: 'azure-servicebus'
        metadata: {
          queueName: '${appName}-jobs'
          messageCount: '5'  // Scale up when 5+ messages in queue
          namespace: serviceBusNamespaceName
        }
        identity: 'system'
      }
    }
  ]
}
```

### Step 3: Deploy Changes

```bash
# Deploy updated API
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/backend-api.bicep \
  --parameters environment=prod appName=scripttodoc

# Deploy updated Worker
az deployment group create \
  --resource-group rg-scripttodoc-prod \
  --template-file deployment/backend-worker.bicep \
  --parameters environment=prod appName=scripttodoc
```

### Step 4: Monitor Costs

**Check costs after 1 week:**
```bash
az consumption usage list \
  --start-date $(date -u -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date -u +%Y-%m-%d) \
  --query "[?instanceName=='ca-scripttodoc-prod-api' || instanceName=='ca-scripttodoc-prod-wrk']"
```

---

## Cost Monitoring & Alerts

### Set Up Cost Alerts

1. **Azure Cost Management:**
   - Create budget: CA$50/month for Container Apps
   - Alert at 80% threshold (CA$40)

2. **Monitor Usage:**
   - Track vCPU-hours consumed
   - Monitor scale events (scale up/down)
   - Review cold start frequency

### Expected Metrics After Optimization

- **API Replicas:** 0-2 (average 0.5)
- **Worker Replicas:** 0-1 (average 0.2)
- **Monthly vCPU-hours:** 50-150 (down from 1,095)
- **Cost:** CA$25-40/month (down from CA$136)

---

## Additional Cost Optimizations

### 1. Container Registry

**Current:** Basic tier (CA$4.73/month)  
**Optimization:** Use Azure Container Registry (ACR) with lifecycle policies to delete old images

**Savings:** CA$1-2/month

### 2. Application Insights

**Current:** ~CA$5-10/month  
**Optimization:** 
- Reduce log retention from 90 to 30 days
- Disable verbose logging in production
- Use sampling (10-20% of requests)

**Savings:** CA$2-5/month

### 3. Storage Lifecycle Policies

**Already configured** in `azure-infrastructure.bicep`:
- Temp files: Delete after 1 day
- Documents: Delete after 90 days

**No additional savings needed**

---

## Migration Path: Container Apps → App Service

If you decide to migrate to App Service after optimization:

### Prerequisites

1. **Container Registry:** Keep ACR (already have Basic tier)
2. **Application Insights:** Already configured
3. **Key Vault:** Already configured
4. **Service Bus:** Already configured

### Migration Steps

1. **Create App Service Plan:**
   ```bash
   az appservice plan create \
     --name plan-scripttodoc-prod \
     --resource-group rg-scripttodoc-prod \
     --sku S1 \
     --is-linux
   ```

2. **Create API Web App:**
   ```bash
   az webapp create \
     --name api-scripttodoc-prod \
     --resource-group rg-scripttodoc-prod \
     --plan plan-scripttodoc-prod \
     --deployment-container-image-name crscripttodocprod.azurecr.io/scripttodoc-api:latest
   ```

3. **Configure Environment Variables:**
   - Copy from Container Apps
   - Use Key Vault references

4. **Create Worker Web App:**
   ```bash
   az webapp create \
     --name worker-scripttodoc-prod \
     --resource-group rg-scripttodoc-prod \
     --plan plan-scripttodoc-prod \
     --deployment-container-image-name crscripttodocprod.azurecr.io/scripttodoc-worker:latest
   ```

5. **Configure Auto-Scale:**
   ```bash
   az monitor autoscale create \
     --name autoscale-api \
     --resource-group rg-scripttodoc-prod \
     --resource /subscriptions/{sub-id}/resourceGroups/rg-scripttodoc-prod/providers/Microsoft.Web/serverfarms/plan-scripttodoc-prod \
     --min-count 1 \
     --max-count 3 \
     --count 1
   ```

6. **Test & Switch DNS:**
   - Test new endpoints
   - Update frontend CORS settings
   - Switch DNS when ready

**Estimated Migration Time:** 2-4 hours  
**Downtime:** < 5 minutes (with proper DNS switching)

---

## Summary & Next Steps

### Immediate Actions (This Week)

1. ✅ **Optimize Container Apps** (change minReplicas to 0)
   - Expected savings: **CA$111-127/month**
   - Time: 30 minutes
   - Risk: Low (can revert easily)

2. ✅ **Set up cost alerts** in Azure Cost Management
   - Budget: CA$50/month for Container Apps
   - Alert at 80% threshold

3. ✅ **Monitor costs** for 1 week after optimization

### Medium-Term (Next Month)

1. **Evaluate results:**
   - Are cold starts acceptable?
   - Is cost reduction sufficient?
   - Any performance issues?

2. **Consider App Service migration** if:
   - Cold starts are problematic
   - Cost is still too high
   - Traffic is steady

### Long-Term (3+ Months)

1. **Review architecture** based on actual usage patterns
2. **Consider hybrid approach** if specific needs emerge
3. **Optimize other services** (Storage, Cosmos DB, etc.)

---

## Application Architecture & Container Details

### API Container Overview

**Purpose:** FastAPI REST API that handles user requests and job management.

**Key Responsibilities:**
1. **File Upload & Validation** (`/api/process`)
   - Accepts transcript files (.txt, .pdf)
   - Validates file size (max 50 MB)
   - Extracts text from PDFs
   - Uploads to Azure Blob Storage

2. **Job Management** (`/api/status/{job_id}`, `/api/jobs`)
   - Creates job records in Cosmos DB
   - Sends jobs to Service Bus queue for processing
   - Returns job status and progress
   - Lists user's job history

3. **Document Retrieval** (`/api/documents/{job_id}`)
   - Downloads generated Word documents from Blob Storage
   - Provides download links

4. **Health Checks** (`/health`)
   - Monitors service connectivity
   - Used by Container Apps for liveness/readiness probes

**Technology Stack:**
- FastAPI (Python web framework)
- Azure SDK clients (Cosmos DB, Blob Storage, Service Bus)
- Uvicorn (ASGI server)

**Resource Requirements:**
- **CPU: 0.5 cores** - Handles HTTP requests, file validation, database queries. Lightweight operations.
- **Memory: 1 GB** - FastAPI app, Azure SDK clients, request/response buffers. Sufficient for typical API workloads.

**Traffic Pattern:**
- Variable/spiky traffic
- Most requests are quick (file upload, status checks)
- No long-running operations (jobs are queued)

---

### Worker Container Overview

**Purpose:** Background job processor that handles the actual document generation pipeline.

**Key Responsibilities:**
1. **Queue Processing**
   - Listens to Azure Service Bus queue (`scripttodoc-jobs`)
   - Receives job messages with transcript URLs and configuration
   - Processes jobs asynchronously

2. **Document Generation Pipeline**
   - **Stage 1:** Download transcript from Blob Storage
   - **Stage 2:** Clean transcript (remove timestamps, filler words)
   - **Stage 3:** Azure Document Intelligence analysis (structure extraction)
   - **Stage 4:** Topic segmentation and step count determination
   - **Stage 5:** Generate training steps using Azure OpenAI (GPT-4o-mini)
   - **Stage 6:** Create source references and citations
   - **Stage 7:** Generate Word document with formatting
   - **Stage 8:** Upload final document to Blob Storage

3. **Status Updates**
   - Updates job status in Cosmos DB throughout processing
   - Reports progress (0.0 to 1.0) and current stage
   - Handles errors and updates failure status

**Technology Stack:**
- Python with Azure SDK
- Azure OpenAI (GPT-4o-mini) for content generation
- Azure Document Intelligence for structure analysis
- python-docx for Word document generation

**Resource Requirements:**
- **CPU: 1.0 core** - Handles AI model calls (OpenAI), document processing, file I/O. More CPU-intensive than API.
- **Memory: 2 GB** - Stores transcript text, AI responses, document content in memory during processing. Larger memory needed for document generation.

**Workload Pattern:**
- Event-driven (triggered by queue messages)
- Long-running processes (2-10 minutes per job)
- CPU-intensive during AI processing
- Memory-intensive during document generation

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE (Frontend)                          │
│                    Azure Static Web Apps / Next.js                          │
└──────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                │ HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API CONTAINER APP                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application (0.5 CPU, 1 GB RAM)                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐ │   │
│  │  │  Endpoints:                                                   │ │   │
│  │  │  • POST /api/process      - Upload transcript, create job    │ │   │
│  │  │  • GET  /api/status/{id}  - Get job status                   │ │   │
│  │  │  • GET  /api/jobs          - List user jobs                   │ │   │
│  │  │  • GET  /api/documents/{id} - Download document              │ │   │
│  │  │  • GET  /health            - Health check                     │ │   │
│  │  └──────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────┬───────────────────────────┬───────────────────────────┬─────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Azure Blob   │          │ Cosmos DB    │          │ Service Bus  │
│ Storage      │          │ (Serverless)  │          │ Queue        │
│              │          │              │          │              │
│ • uploads/   │          │ • jobs       │          │ • scripttodoc│
│ • documents/ │          │   container  │          │   -jobs      │
│ • temp/      │          │              │          │              │
└──────────────┘          └──────────────┘          └──────┬───────┘
                                                            │
                                                            │ Queue Messages
                                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WORKER CONTAINER APP                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Background Processor (1.0 CPU, 2 GB RAM)                           │   │
│  │  ┌──────────────────────────────────────────────────────────────┐ │   │
│  │  │  Processing Pipeline:                                        │ │   │
│  │  │  1. Receive job from Service Bus                              │ │   │
│  │  │  2. Download transcript from Blob Storage                      │ │   │
│  │  │  3. Clean transcript (remove timestamps, fillers)            │ │   │
│  │  │  4. Azure Document Intelligence (structure analysis)          │ │   │
│  │  │  5. Topic segmentation & step count determination             │ │   │
│  │  │  6. Generate steps using Azure OpenAI (GPT-4o-mini)          │ │   │
│  │  │  7. Create source references & citations                      │ │   │
│  │  │  8. Generate Word document (python-docx)                      │ │   │
│  │  │  9. Upload document to Blob Storage                          │ │   │
│  │  │  10. Update job status in Cosmos DB                          │ │   │
│  │  └──────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────┬───────────────────────────┬───────────────────────────┬─────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Azure Blob   │          │ Cosmos DB    │          │ Azure OpenAI │
│ Storage      │          │ (Serverless)  │          │              │
│              │          │              │          │ • GPT-4o-mini │
│ • documents/ │          │ • jobs       │          │ • Embeddings │
│              │          │   (updates)  │          │              │
└──────────────┘          └──────────────┘          └──────────────┘
                                                           │
                                                           │
                                                           ▼
                                                  ┌──────────────┐
                                                  │ Azure Doc    │
                                                  │ Intelligence │
                                                  │              │
                                                  │ • Prebuilt   │
                                                  │   Read       │
                                                  │ • Layout     │
                                                  └──────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTING SERVICES                                 │
│  • Azure Key Vault (secrets management)                                     │
│  • Azure Container Registry (Docker images)                                 │
│  • Application Insights (monitoring & logging)                              │
│  • Log Analytics Workspace (log aggregation)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. User uploads transcript → API validates & stores in Blob Storage
2. API creates job in Cosmos DB → Sends message to Service Bus queue
3. Worker receives message → Downloads transcript → Processes pipeline
4. Worker updates progress in Cosmos DB throughout processing
5. Worker generates document → Uploads to Blob Storage → Marks job complete
6. User polls API for status → API returns progress from Cosmos DB
7. User downloads document → API retrieves from Blob Storage

---

## CPU & Memory Requirements Rationale

### API Container: 0.5 CPU, 1 GB RAM

**CPU: 0.5 cores**
- **Rationale:** API handles lightweight operations:
  - HTTP request/response handling
  - File validation (size checks, type detection)
  - Database queries (Cosmos DB - typically < 100ms)
  - Blob Storage operations (metadata only, not content processing)
  - JSON serialization/deserialization
- **Workload:** I/O-bound operations, not CPU-intensive
- **Scaling:** Can handle 50+ concurrent requests with 0.5 CPU
- **Cost optimization:** Lower CPU = lower cost in Container Apps

**Memory: 1 GB**
- **Rationale:** Sufficient for:
  - FastAPI application (~50-100 MB)
  - Azure SDK clients (~100-200 MB)
  - Request/response buffers (~50-100 MB)
  - Python runtime overhead (~200-300 MB)
  - Headroom for spikes (~300-400 MB)
- **Typical usage:** 400-600 MB under normal load
- **Peak usage:** ~800 MB during file uploads

**Why not more?**
- API doesn't process large files (just validates and stores)
- No in-memory document processing
- Cost optimization: Lower memory = lower cost

---

### Worker Container: 1.0 CPU, 2 GB RAM

**CPU: 1.0 core**
- **Rationale:** Worker performs CPU-intensive operations:
  - Azure OpenAI API calls (GPT-4o-mini) - network + processing
  - Document generation (python-docx) - XML processing
  - Text processing (cleaning, tokenization, segmentation)
  - Azure Document Intelligence API calls
  - File I/O operations (download/upload)
- **Workload:** CPU-bound during AI processing, I/O-bound during file operations
- **Processing time:** 2-10 minutes per job depending on transcript length
- **Concurrency:** Typically processes 1 job at a time per instance

**Memory: 2 GB**
- **Rationale:** Required for:
  - Full transcript text in memory (~1-50 MB depending on length)
  - AI model responses (GPT-4o-mini outputs) (~500 KB - 5 MB)
  - Document content during generation (~10-100 MB)
  - Python runtime (~200-300 MB)
  - Azure SDK clients (~100-200 MB)
  - Processing buffers (~100-200 MB)
- **Typical usage:** 800 MB - 1.2 GB during processing
- **Peak usage:** ~1.8 GB for large transcripts (50+ pages)

**Why not less?**
- Document generation requires keeping content in memory
- Large transcripts (50+ pages) need more memory
- Azure OpenAI responses can be substantial
- Insufficient memory causes OOM errors and job failures

**Why not more?**
- Most jobs don't exceed 2 GB
- Cost optimization: 2 GB is sufficient for 95% of use cases
- Can scale horizontally (more instances) if needed

---

## Azure Pricing Calculator Configuration

### Step-by-Step Guide

1. **Navigate to Azure Pricing Calculator:**
   - URL: https://azure.microsoft.com/pricing/calculator/
   - Or search: "Azure Pricing Calculator"

2. **Add Services:**

   **A. Container Apps (Current Setup)**
   - Search: "Container Apps"
   - Add "Container Apps"
   - Configure:
     - **Region:** East US (or your region)
     - **Consumption Plan**
     - **API Container:**
       - vCPU: 0.5
       - Memory: 1 GB
       - Replicas: 1 (or 0 for optimized)
       - Hours: 730 (or estimated active hours)
     - **Worker Container:**
       - vCPU: 1.0
       - Memory: 2 GB
       - Replicas: 1 (or 0 for optimized)
       - Hours: 730 (or estimated active hours)

   **B. Container Registry**
   - Search: "Container Registry"
   - Add "Azure Container Registry"
   - Configure:
     - **Tier:** Basic
     - **Storage:** 10 GB (estimated)

   **C. Cosmos DB (IMPORTANT: Use Serverless, not Provisioned)**
   - Search: "Cosmos DB"
   - Add "Azure Cosmos DB"
   - **⚠️ CRITICAL:** In the API dropdown, select **"Azure Cosmos DB for NoSQL (formerly Core)"**
   - Configure:
     - **API:** Azure Cosmos DB for NoSQL (NOT Cassandra, MongoDB, PostgreSQL, etc.)
     - **Capacity Mode:** Select **"Serverless"** (NOT "Provisioned throughput" or "Autoscale")
     - **Region:** East US
     - **Request Units (RU):** 
       - For Serverless: Enter estimated monthly RU consumption
       - Example: 10,000 RU/month = ~CA$0.28/month
       - Your actual usage: ~50 RU/month = CA$0.01/month
     - **Storage:** ~1 GB (estimated)
   
   **⚠️ Common Mistake:** 
   - If you see "2 vCore, 8 GiB RAM" or "Single Node" options, you're in the WRONG mode
   - Those are for Provisioned Capacity (expensive: $175+/month)
   - You need Serverless mode (pay-per-request, very cheap)
   
   **How to verify you're in Serverless mode:**
   - Look for "Serverless" or "Pay-per-request" option
   - Should show pricing like "$0.28 per 1M RU" (not "$0.110 per hour")
   - Monthly cost should be < $10 for typical usage

   **D. Blob Storage (IMPORTANT: Search for "Storage Accounts")**
   - Search: **"Storage Accounts"** (NOT "Blob Storage" or "Storage Discovery")
   - Add **"Storage Accounts"** to your estimate
   - Note: "Storage Accounts" includes Blob Storage pricing
   - Configure:
     - **Region:** East US
     - **Performance:** Standard (NOT Premium)
     - **Redundancy:** Locally Redundant Storage (LRS)
     - **Access Tier:** Hot
     - **Storage Capacity:** 100-500 GB (check Azure Portal for actual usage)
     - **Write Operations:** ~5,000/month
     - **Read Operations:** ~5,000/month
     - **List Operations:** ~1,000/month
     - **Data Transfer (Outbound):** ~10-20 GB/month
   
   **⚠️ Common Mistake:**
   - "Azure Storage Discovery" is NOT the pricing calculator
   - It's a service for analyzing storage accounts
   - You need "Azure Blob Storage" for cost estimation
   
   **Your Actual Configuration:**
   - SKU: Standard_LRS
   - Access Tier: Hot
   - Containers: uploads, documents, temp
   - Lifecycle policies: Auto-delete temp files after 1 day

   **E. Service Bus**
   - Search: "Service Bus"
   - Add "Azure Service Bus"
   - Configure:
     - **Tier:** Standard
     - **Messages:** 1,000,000/month (estimated)

   **F. Azure OpenAI**
   - Search: "Azure OpenAI"
   - Add "Azure OpenAI Service"
   - Configure:
     - **Model:** GPT-4o-mini
     - **Input tokens:** 5,000,000/month
     - **Output tokens:** 2,000,000/month

   **G. Document Intelligence**
   - Search: "Document Intelligence"
   - Add "Azure AI Document Intelligence"
   - Configure:
     - **Pages:** 2,000/month

   **H. Application Insights**
   - Search: "Application Insights"
   - Add "Application Insights"
   - Configure:
     - **Data Ingestion:** 5 GB/month

3. **Export Estimate:**
   - Click "Export" to save as PDF or Excel
   - Share with stakeholders

### Sample Calculator Configuration (Optimized)

**Container Apps (Optimized - Scale to Zero):**
- API: 0.5 vCPU, 1 GB, 0-2 replicas, 240 hours/month active
- Worker: 1.0 vCPU, 2 GB, 0-1 replicas, 120 hours/month active
- **Estimated Cost:** US$15-30/month (CA$20-40/month)

**Alternative: App Service**
- Standard S1 Plan: 1 vCPU, 1.75 GB
- **Estimated Cost:** US$73/month (CA$98.50/month)

### Quick Links

- **Azure Pricing Calculator:** https://azure.microsoft.com/pricing/calculator/
- **Container Apps Pricing:** https://azure.microsoft.com/pricing/details/container-apps/
- **App Service Pricing:** https://azure.microsoft.com/pricing/details/app-service/windows/
- **Functions Pricing:** https://azure.microsoft.com/pricing/details/functions/

---

## Questions & Support

**For cost optimization questions:**
- Review Azure Cost Management dashboard
- Check Container Apps metrics (replica counts, vCPU usage)
- Monitor Application Insights for performance impact

**For migration questions:**
- Refer to Azure App Service documentation
- Test in staging environment first
- Plan for minimal downtime

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** February 2025
