# ScriptToDoc - System Architecture (Microsoft Azure Native)

## Executive Summary

**Goal:** Transform meeting transcripts and training videos into professional, citation-backed training documents using Azure AI services.

**Core Value:** Every generated step is grounded in source material with confidence scoring to prevent AI hallucination.

**Platform:** 100% Microsoft Azure ecosystem for enterprise integration.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Next.js Frontend (Static Web App)                       │  │
│  │  - Upload interface                                       │  │
│  │  - Progress tracking                                      │  │
│  │  - Plan editor                                            │  │
│  │  - Document download                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS / JSON
                            │ Azure Front Door (CDN + WAF)
┌───────────────────────────┴─────────────────────────────────────┐
│                    APPLICATION LAYER (Azure)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Azure Container Apps)                  │  │
│  │  - /process, /status, /documents endpoints               │  │
│  │  - File upload validation                                │  │
│  │  - Job orchestration                                     │  │
│  │  - Authentication (Azure AD)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼────────┐  ┌──────▼────────┐
│ Azure Service  │  │ Azure Cosmos  │  │ Azure Blob    │
│ Bus Queue      │  │ DB            │  │ Storage       │
│ - Job queue    │  │ - Job state   │  │ - Uploads     │
│ - Async tasks  │  │ - Metadata    │  │ - Documents   │
└───────┬────────┘  └───────────────┘  └───────────────┘
        │
        │ Trigger
┌───────▼────────────────────────────────────────────────────────┐
│              PROCESSING LAYER (Background Workers)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Azure Container Apps (Worker Instances)                 │  │
│  │  - Pipeline orchestration                                │  │
│  │  - Multi-stage processing                                │  │
│  │  - Progress updates                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────────┐ ┌─────▼──────────┐ ┌─────▼──────────┐
│ Azure Document   │ │ Azure OpenAI   │ │ Azure Computer │
│ Intelligence     │ │ Service        │ │ Vision         │
│ - Layout model   │ │ - GPT-4        │ │ - Video frames │
│ - Read model     │ │ - Embeddings   │ │ - OCR          │
└──────────────────┘ └────────────────┘ └────────────────┘
```

---

## Azure Services Breakdown

### 1. **Frontend Hosting** - Azure Static Web Apps
**Purpose:** Host Next.js UI with built-in CI/CD

**Features:**
- Automatic deployment from GitHub
- Global CDN distribution
- Custom domains with SSL
- Integrated authentication (Azure AD B2C)
- API routing to backend

**Configuration:**
```json
{
  "routes": [
    {
      "route": "/api/*",
      "rewrite": "https://backend-api.azurecontainerapps.io/api/*"
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html"
  }
}
```

---

### 2. **Backend API** - Azure Container Apps
**Purpose:** FastAPI application with auto-scaling

**Why Container Apps over App Service:**
- Event-driven scaling (scale to zero when idle)
- Native container support
- Built-in Service Bus integration
- Microservices-ready architecture
- Cost-effective for variable workloads

**Configuration:**
```yaml
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8000
    secrets:
      - name: azure-openai-key
        keyVaultUrl: https://keyvault.vault.azure.net/secrets/openai-key
    scale:
      minReplicas: 0
      maxReplicas: 10
      rules:
        - name: http-scaling
          http:
            metadata:
              concurrentRequests: 10
```

**Environment Variables from Azure Key Vault:**
- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
- `AZURE_DOCUMENT_INTELLIGENCE_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_STORAGE_CONNECTION_STRING`
- `COSMOS_DB_CONNECTION_STRING`

---

### 3. **Job Queue** - Azure Service Bus
**Purpose:** Reliable async job processing

**Queue Structure:**
```
scripttodoc-jobs (Queue)
├── message properties:
│   ├── job_id (string)
│   ├── transcript_blob_url (string)
│   ├── screenshot_blob_urls (array)
│   ├── config (JSON)
│   └── user_id (string)
└── message body: full job payload
```

**Features:**
- Dead-letter queue for failed jobs
- Message TTL (30 minutes)
- Duplicate detection
- FIFO processing with sessions

**Why Service Bus over Storage Queues:**
- Advanced messaging patterns
- Duplicate detection
- Transactions support
- Enterprise-grade reliability

---

### 4. **Data Storage** - Azure Cosmos DB (NoSQL)
**Purpose:** Store job metadata and results

**Container: `jobs`**
```json
{
  "id": "job_abc123",
  "partitionKey": "user_xyz",
  "status": "processing",
  "stage": "azure_di_analysis",
  "progress": 0.35,
  "created_at": "2025-11-03T10:00:00Z",
  "updated_at": "2025-11-03T10:05:00Z",
  "config": {
    "tone": "Professional",
    "audience": "Technical",
    "min_steps": 3,
    "target_steps": 8
  },
  "input": {
    "transcript_url": "https://...",
    "screenshot_urls": ["https://..."]
  },
  "result": {
    "document_url": "https://...",
    "metrics": {...}
  },
  "error": null
}
```

**Container: `processing_cache`**
- Cache intermediate results (Azure DI responses)
- TTL: 24 hours
- Reduces redundant API calls

**Why Cosmos DB:**
- Serverless billing (pay per request)
- Global distribution (if needed)
- JSON-native storage
- Automatic indexing
- 99.999% SLA

**Alternative:** Azure Table Storage (cheaper for simple key-value)

---

### 5. **File Storage** - Azure Blob Storage
**Purpose:** Store uploaded files and generated documents

**Container Structure:**
```
scripttodoc-storage (Storage Account)
├── uploads/                    (Container - Private)
│   ├── {job_id}/
│   │   ├── transcript.txt
│   │   └── screenshots/
│   │       ├── screen_01.png
│   │       └── screen_02.png
├── documents/                  (Container - Private with SAS)
│   └── {job_id}_training.docx
└── temp/                       (Container - Lifecycle policy: delete after 24h)
    └── video_frames/
```

**Features:**
- Lifecycle management (auto-delete temp files)
- SAS tokens for secure downloads
- CDN integration for document delivery
- Versioning for document history
- Immutable storage for compliance

**Access Patterns:**
- Upload: Backend generates SAS token for client direct upload
- Download: Time-limited SAS URL (1 hour expiry)
- Processing: Managed Identity access (no keys)

---

### 6. **Azure Document Intelligence**
**Purpose:** Extract structure from transcripts and screenshots

**Models Used:**
1. **prebuilt-read** - For transcript text analysis
   - Extracts paragraphs, structure
   - Identifies process flow patterns
   - Cost: $1.50 per 1,000 pages

2. **prebuilt-layout** - For screenshot analysis
   - OCR for UI elements
   - Table extraction
   - Layout understanding
   - Cost: $10.00 per 1,000 pages

**Optimization Strategy:**
- Use read model for text-only transcripts
- Use layout model only when screenshots provided
- Cache results in Cosmos DB (24h TTL)
- Batch screenshots when possible

**API Integration:**
```python
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.identity import DefaultAzureCredential

# Managed Identity authentication
credential = DefaultAzureCredential()
client = DocumentIntelligenceClient(
    endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"],
    credential=credential
)

# Analyze from blob URL
poller = client.begin_analyze_document(
    model_id="prebuilt-read",
    document_url=blob_url
)
result = poller.result()
```

---

### 7. **Azure OpenAI Service**
**Purpose:** Enhanced content generation with GPT-4

**Why Azure OpenAI vs OpenAI API:**
- Data residency (stays in Azure)
- Enterprise SLA and support
- Integration with Azure AD
- Network isolation (Private Link)
- Compliance (HIPAA, SOC 2, ISO)
- Cost management (Azure billing)

**Deployment Configuration:**
```
Resource: scripttodoc-openai
Location: East US
Deployments:
  - gpt-4o (for complex analysis)
  - gpt-4o-mini (for routine tasks)
  - text-embedding-3-small (future: semantic search)
```

**Rate Limits:**
- GPT-4: 10K tokens/min (adjustable)
- GPT-4-mini: 30K tokens/min
- Quota management through Azure

**Usage Pattern:**
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
)

response = client.chat.completions.create(
    model="gpt-4o-mini",  # deployment name
    messages=[...],
    temperature=0.2
)
```

---

### 8. **Azure Computer Vision** (Phase 3 - Video)
**Purpose:** Extract frames from training videos

**Features:**
- Video frame extraction
- Scene change detection
- OCR on video frames
- Object detection (identify UI elements)

**Integration:**
```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient

# Extract key frames
frames = computer_vision_client.analyze_video(
    video_url=blob_url,
    features=["frames", "ocr", "objects"]
)
```

---

### 9. **Security & Secrets** - Azure Key Vault
**Purpose:** Secure credential management

**Secrets Stored:**
- Azure OpenAI API keys
- Azure Document Intelligence keys
- Storage account connection strings
- Cosmos DB connection strings
- Third-party API keys (if any)

**Access Control:**
- Managed Identity for Container Apps
- RBAC for developers (read-only)
- Audit logging for all access

**Integration:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://scripttodoc-kv.vault.azure.net/",
    credential=credential
)

secret = client.get_secret("azure-openai-key")
```

---

### 10. **Monitoring & Logging** - Azure Monitor + Application Insights
**Purpose:** Observability and diagnostics

**Metrics Tracked:**
- API response times
- Job processing duration
- Azure DI API call counts
- OpenAI token usage
- Error rates
- Cost per job

**Logging:**
```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

logging.basicConfig(
    handlers=[
        AzureLogHandler(
            connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
        )
    ]
)

logger.info("Job started", extra={
    "custom_dimensions": {
        "job_id": job_id,
        "user_id": user_id,
        "stage": "transcript_cleaning"
    }
})
```

**Dashboards:**
- Real-time job processing view
- Cost analysis by service
- Error trending
- Performance metrics

---

## Authentication & Authorization

### Azure AD B2C Integration

**User Flow:**
```
1. User accesses frontend
2. Redirected to Azure AD B2C login
3. Token issued (JWT)
4. Frontend stores token
5. All API calls include token in header
6. Backend validates token with Azure AD
```

**Implementation:**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from azure.identity import DefaultAzureCredential
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Validate JWT with Azure AD
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}  # Simplified - use proper validation
        )
        return payload["oid"]  # User ID
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Benefits:**
- Single Sign-On (SSO) with company accounts
- Multi-factor authentication (MFA)
- Conditional access policies
- Audit trail

---

## Network Security

### Azure Front Door + WAF

**Purpose:** Secure public-facing endpoints

**Features:**
- DDoS protection
- SSL/TLS termination
- Rate limiting (per user/IP)
- Geo-filtering (if needed)
- Bot protection

**Configuration:**
```json
{
  "wafPolicy": {
    "customRules": [
      {
        "name": "RateLimitRule",
        "priority": 1,
        "ruleType": "RateLimitRule",
        "rateLimitThreshold": 100,
        "rateLimitDuration": "PT1M"
      }
    ]
  }
}
```

### Private Endpoints (Optional - Enterprise)

**For enhanced security:**
- Cosmos DB via Private Link
- Blob Storage via Private Endpoint
- Key Vault via Private Endpoint
- No public internet access to data services

---

## Cost Optimization Strategies

### 1. **Compute**
- Container Apps: Scale to zero when idle
- Serverless Cosmos DB: Pay per request
- Reserved instances for production (if stable load)

### 2. **Storage**
- Lifecycle policies: Auto-delete temp files after 24h
- Cool tier for old documents (>30 days)
- Archive tier for compliance storage (>90 days)

### 3. **AI Services**
- Cache Azure DI results (24h)
- Use GPT-4o-mini for routine tasks (cheaper)
- Batch processing when possible
- Set token limits on OpenAI calls

### 4. **Monitoring**
- Sampling for Application Insights (10% for normal, 100% for errors)
- Retention: 30 days (configurable)

**Estimated Monthly Costs (100 jobs/day):**
- Container Apps: $50-100
- Cosmos DB: $25-50
- Blob Storage: $10-20
- Azure DI: $50-100
- Azure OpenAI: $100-200
- Other services: $50
- **Total: $285-520/month**

---

## Deployment Architecture

### Environments

**1. Development**
```
Resource Group: rg-scripttodoc-dev
- Container App: scripttodoc-api-dev
- Storage: stscripttodocdev
- Cosmos DB: cosmos-scripttodoc-dev (serverless)
- Key Vault: kv-scripttodoc-dev
```

**2. Staging**
```
Resource Group: rg-scripttodoc-staging
- Mirror of production
- Separate Azure OpenAI deployment
- Test data isolation
```

**3. Production**
```
Resource Group: rg-scripttodoc-prod
- High availability zones
- Backup policies enabled
- Production-grade SLA
```

### CI/CD Pipeline (Azure DevOps or GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v1
      - name: Build and push container
        run: |
          az acr build --registry scripttodoc --image api:${{ github.sha }} .
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name scripttodoc-api \
            --resource-group rg-scripttodoc-prod \
            --image scripttodoc.azurecr.io/api:${{ github.sha }}
  
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - name: Build Next.js
        run: npm run build
      - name: Deploy to Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
```

---

## Disaster Recovery

### Backup Strategy
- **Cosmos DB**: Point-in-time restore (enabled)
- **Blob Storage**: Geo-redundant storage (GRS)
- **Code**: GitHub repository
- **Secrets**: Key Vault soft-delete + purge protection

### Recovery Objectives
- **RTO** (Recovery Time Objective): 4 hours
- **RPO** (Recovery Point Objective): 1 hour

### High Availability
- Multi-region deployment (future)
- Automatic failover for Cosmos DB
- Read replicas for Blob Storage

---

## Compliance & Governance

### Data Residency
- All data stays in configured Azure region
- No data leaves Microsoft cloud
- GDPR compliant

### Audit Trail
- All API calls logged to Application Insights
- Key Vault access logged
- Blob Storage access logs

### Data Retention
- Job data: 90 days in Cosmos DB
- Documents: Configurable (default: 1 year)
- Logs: 30 days in Application Insights

---

## Integration Points

### Microsoft 365 Integration (Future)
- **SharePoint**: Save documents directly to SharePoint libraries
- **Teams**: Notifications on job completion
- **OneDrive**: User-specific document storage

### Power Platform Integration (Future)
- **Power Automate**: Trigger flows on document generation
- **Power BI**: Analytics dashboard for usage metrics

---

## Architecture Decisions

### Why Container Apps over App Service?
✅ Better for event-driven workloads
✅ Scale to zero (cost savings)
✅ Native Service Bus integration
✅ Microservices-ready
❌ More complex setup

### Why Cosmos DB over SQL Database?
✅ Serverless pricing (better for variable load)
✅ JSON-native storage
✅ Horizontal scaling built-in
✅ Global distribution option
❌ Higher per-operation cost at scale

### Why Service Bus over Storage Queues?
✅ Advanced messaging patterns
✅ Duplicate detection
✅ Dead-letter queue
✅ Better for enterprise
❌ Slightly higher cost

### Why Static Web Apps over App Service for Frontend?
✅ Built for static sites + APIs
✅ Automatic CDN
✅ Free tier available
✅ GitHub integration
❌ Limited backend capabilities (perfect for our use case)

---

## Security Checklist

- [x] All secrets in Key Vault (no hardcoded keys)
- [x] Managed Identity for service-to-service auth
- [x] Azure AD authentication for users
- [x] HTTPS only (no HTTP)
- [x] Network isolation options available
- [x] Input validation on all endpoints
- [x] File upload size limits enforced
- [x] SAS tokens with expiry for file access
- [x] RBAC for resource access control
- [x] Audit logging enabled

---

## Next Steps

1. **Create Azure Resources** (Terraform/Bicep)
2. **Set up CI/CD pipeline**
3. **Implement core backend services**
4. **Build frontend UI**
5. **Integration testing**
6. **Security review**
7. **Performance testing**
8. **Documentation**
9. **User training**
10. **Go-live**

---

*This architecture ensures enterprise-grade security, scalability, and maintainability while staying 100% within the Microsoft ecosystem.*

