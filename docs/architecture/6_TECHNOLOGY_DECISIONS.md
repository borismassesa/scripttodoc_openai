# ScriptToDoc - Technology Decisions & Trade-offs

## Overview

This document captures key technology decisions, alternatives considered, and the rationale behind choices. It serves as a reference for understanding why specific technologies were selected for the ScriptToDoc system.

---

## 1. Backend Framework: FastAPI

### Decision: FastAPI over Flask, Django, or Express.js

**Chosen:** FastAPI (Python)

**Alternatives Considered:**
- Flask (Python)
- Django REST Framework (Python)
- Express.js (Node.js)
- ASP.NET Core (C#)

### Rationale

| Factor | FastAPI | Flask | Django | Express.js | ASP.NET Core |
|--------|---------|-------|--------|------------|--------------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Type Safety** | ⭐⭐⭐⭐⭐ (Pydantic) | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Async Support** | ⭐⭐⭐⭐⭐ (Native) | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **API Docs** | ⭐⭐⭐⭐⭐ (Auto) | ⭐⭐ (Manual) | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Azure SDK** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **NLP Libraries** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

**Key Advantages:**
- ✅ **Automatic API documentation** (Swagger/OpenAPI) - saves development time
- ✅ **Built-in data validation** (Pydantic) - reduces bugs
- ✅ **Async/await support** - efficient for I/O-bound operations (Azure API calls)
- ✅ **Python ecosystem** - rich NLP libraries (NLTK, spaCy) and Azure SDK
- ✅ **Type hints** - better IDE support and fewer runtime errors
- ✅ **Performance** - comparable to Node.js, faster than Flask/Django

**Trade-offs:**
- ⚠️ Newer framework (2018) - smaller community than Flask/Django
- ⚠️ Fewer third-party plugins - but core features are excellent

**Code Example:**
```python
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

class ProcessRequest(BaseModel):
    tone: str = "Professional"
    min_steps: int = 3

@app.post("/process")
async def process_transcript(
    file: UploadFile = File(...),
    config: ProcessRequest = Depends()
):
    # Automatic validation, type checking, and docs
    return {"job_id": "..."}
```

---

## 2. Frontend Framework: Next.js

### Decision: Next.js over React (CRA), Vue.js, or Angular

**Chosen:** Next.js 13+ with App Router

**Alternatives Considered:**
- Create React App (CRA)
- Vite + React
- Vue.js 3
- Angular
- Svelte

### Rationale

| Factor | Next.js | CRA | Vue.js | Angular | Svelte |
|--------|---------|-----|--------|---------|--------|
| **Performance** | ⭐⭐⭐⭐⭐ (SSR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **SEO** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Developer Experience** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Azure Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Community** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Microsoft Ecosystem** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Key Advantages:**
- ✅ **Azure Static Web Apps** native support - seamless deployment
- ✅ **Server-side rendering (SSR)** - better initial load times
- ✅ **File-based routing** - intuitive project structure
- ✅ **Built-in optimization** - image optimization, code splitting
- ✅ **TypeScript support** - first-class type safety
- ✅ **API routes** - can host simple backend logic if needed

**Trade-offs:**
- ⚠️ More complex than plain React - learning curve for SSR concepts
- ⚠️ Opinionated structure - but this is good for consistency

**Code Example:**
```typescript
// app/page.tsx (Next.js 13+ App Router)
'use client'

export default function Home() {
  const [jobId, setJobId] = useState<string | null>(null);
  
  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/process', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    setJobId(data.job_id);
  };
  
  return <UploadArea onUpload={handleUpload} />;
}
```

---

## 3. Database: Azure Cosmos DB (NoSQL)

### Decision: Cosmos DB over Azure SQL Database or Table Storage

**Chosen:** Azure Cosmos DB (NoSQL API)

**Alternatives Considered:**
- Azure SQL Database (relational)
- Azure Table Storage (key-value)
- Azure PostgreSQL (relational)
- MongoDB Atlas

### Rationale

| Factor | Cosmos DB | SQL Database | Table Storage | PostgreSQL |
|--------|-----------|--------------|---------------|------------|
| **Scalability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost (Serverless)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **JSON Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Query Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Setup Complexity** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Global Distribution** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

**Key Advantages:**
- ✅ **Serverless pricing** - pay per request, perfect for variable workloads
- ✅ **JSON-native** - store job data without schema migrations
- ✅ **TTL support** - auto-delete expired cache entries
- ✅ **Horizontal scaling** - automatic partitioning
- ✅ **99.999% SLA** - enterprise-grade reliability

**Trade-offs:**
- ⚠️ More expensive at scale - but serverless mode is cheap for low volume
- ⚠️ NoSQL mindset - need to design around partition keys

**When to Use Each:**

```
Cosmos DB (Chosen):
  ✓ Variable workload (scale to zero)
  ✓ JSON documents
  ✓ Simple queries (get by ID, filter by status)
  ✓ TTL for cache management

SQL Database:
  ✓ Complex relational queries
  ✓ Transactions across tables
  ✓ Reporting and analytics
  ✗ Overkill for our use case

Table Storage:
  ✓ Very cheap
  ✓ Simple key-value lookups
  ✗ Limited query capabilities (no complex filters)
  ✗ No TTL support
```

**Data Model:**
```typescript
// Job record (Cosmos DB document)
{
  "id": "job_123",          // Partition key
  "status": "processing",
  "progress": 0.45,
  "config": {...},          // Nested JSON
  "result": {...},          // Nested JSON
  "ttl": 7776000           // Auto-delete after 90 days
}
```

---

## 4. Message Queue: Azure Service Bus

### Decision: Service Bus over Storage Queues or Event Grid

**Chosen:** Azure Service Bus (Standard Tier)

**Alternatives Considered:**
- Azure Storage Queues
- Azure Event Grid
- Azure Event Hubs
- Redis Queue

### Rationale

| Factor | Service Bus | Storage Queues | Event Grid | Redis Queue |
|--------|-------------|----------------|------------|-------------|
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Dead Letter Queue** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Duplicate Detection** | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Message Ordering** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | ⭐⭐⭐⭐ |
| **Cost** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Azure Native** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Key Advantages:**
- ✅ **Dead-letter queue** - automatic handling of failed messages
- ✅ **Duplicate detection** - prevents processing same job twice
- ✅ **Sessions** - FIFO ordering within session
- ✅ **Scheduled messages** - delay job processing if needed
- ✅ **Transactions** - atomic operations

**Trade-offs:**
- ⚠️ More expensive than Storage Queues - but advanced features justify cost
- ⚠️ More complex setup - but worth it for reliability

**Comparison:**

```
Service Bus (Chosen):
  ✓ Enterprise messaging patterns
  ✓ Dead-letter queue
  ✓ Duplicate detection
  ✓ Message sessions (FIFO)
  ✓ Perfect for job processing

Storage Queues:
  ✓ Extremely cheap
  ✓ Simple setup
  ✗ No dead-letter queue (manual implementation)
  ✗ No duplicate detection
  ✗ At-least-once delivery (not exactly-once)

Event Grid:
  ✓ Pub/sub pattern
  ✓ Event routing
  ✗ Not designed for job queues
  ✗ No message ordering

Redis Queue:
  ✓ Fast in-memory operations
  ✗ Not fully Azure-native
  ✗ Requires Redis instance management
```

**Usage Pattern:**
```python
# Send job to queue
message = ServiceBusMessage(
    body=json.dumps({"job_id": "..."}),
    message_id="job_123",  # For duplicate detection
    scheduled_enqueue_time_utc=datetime.utcnow() + timedelta(seconds=30)
)
sender.send_messages(message)

# Receive and process
with receiver:
    for message in receiver:
        try:
            process_job(json.loads(str(message)))
            receiver.complete_message(message)  # Success
        except RecoverableError:
            receiver.abandon_message(message)   # Retry
        except FatalError:
            receiver.dead_letter_message(message)  # Move to DLQ
```

---

## 5. Document Intelligence: Azure DI + OpenAI Hybrid

### Decision: Hybrid approach over single-provider

**Chosen:** Azure Document Intelligence + Azure OpenAI Service

**Alternatives Considered:**
- Azure OpenAI only (no DI)
- Azure Document Intelligence only (no LLM)
- OpenAI API + Claude (multi-vendor)
- On-premise LLM (Llama, Mistral)

### Rationale

**Hybrid Approach Benefits:**

```
┌─────────────────────────────────────────────────────────┐
│              HYBRID PROCESSING PIPELINE                  │
└─────────────────────────────────────────────────────────┘

Transcript
   │
   ├─→ Azure DI (Structure)
   │   ├─ Paragraph detection
   │   ├─ Role identification
   │   ├─ Layout understanding
   │   └─ Fast, deterministic
   │
   └─→ Azure OpenAI (Content)
       ├─ Summarization
       ├─ Step expansion
       ├─ Natural language generation
       └─ High quality, contextual

Result: Best of both worlds
  ✓ Structure from DI (accurate, cheap)
  ✓ Content from OpenAI (fluent, engaging)
```

**Why Not Single Provider:**

| Approach | Pros | Cons |
|----------|------|------|
| **Hybrid (Chosen)** | • Best accuracy<br>• Complementary strengths<br>• Fallback options | • More complexity<br>• Two API calls |
| **OpenAI Only** | • Simpler architecture<br>• Good quality | • More expensive<br>• Less structure awareness |
| **Azure DI Only** | • Deterministic<br>• Cheaper | • Limited NLG<br>• Basic summarization |
| **Multi-vendor** | • Avoid vendor lock-in | • Complex billing<br>• Data residency issues |
| **On-premise LLM** | • Data privacy<br>• No API costs | • Infrastructure overhead<br>• Lower quality |

**Cost Comparison (per 100 jobs):**
```
Hybrid (Azure DI + OpenAI):
  Azure DI:  $3.00   (100 pages @ $0.03/page)
  OpenAI:    $45.00  (900 API calls @ $0.05/call)
  Total:     $48.00

OpenAI Only:
  OpenAI:    $65.00  (1200 API calls, more tokens)
  Total:     $65.00  (+35% more expensive)

Azure DI Only:
  Azure DI:  $5.00   (more model usage)
  Total:     $5.00   (-90% cheaper, but lower quality)
```

**Why Azure OpenAI vs OpenAI API:**
- ✅ **Data residency** - stays in Azure (compliance requirement)
- ✅ **Enterprise SLA** - 99.9% uptime guarantee
- ✅ **Azure AD integration** - unified authentication
- ✅ **Private networking** - can use Private Link
- ✅ **Billing integration** - single Azure invoice
- ⚠️ **Newer models slower** - OpenAI API gets updates first

---

## 6. Container Hosting: Azure Container Apps

### Decision: Container Apps over App Service or Kubernetes

**Chosen:** Azure Container Apps

**Alternatives Considered:**
- Azure App Service (PaaS)
- Azure Kubernetes Service (AKS)
- Azure Container Instances (ACI)
- Azure Functions (Serverless)

### Rationale

| Factor | Container Apps | App Service | AKS | Functions |
|--------|----------------|-------------|-----|-----------|
| **Scale to Zero** | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Container Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Event-driven** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Complexity** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Microservices Ready** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Key Advantages:**
- ✅ **Scale to zero** - no cost when idle (perfect for dev/staging)
- ✅ **Native Service Bus integration** - KEDA built-in
- ✅ **Microservices-ready** - can split into multiple apps later
- ✅ **Managed infrastructure** - no cluster management like AKS
- ✅ **Container flexibility** - use any container image

**Trade-offs:**
- ⚠️ Newer service (2022) - less mature than App Service
- ⚠️ Regional limitations - not available in all Azure regions

**Why Not Alternatives:**

```
App Service:
  ✓ Very mature, stable
  ✓ Easy deployment
  ✗ Can't scale to zero (always paying)
  ✗ Less flexible for containers
  ✗ $30+/month minimum

AKS (Kubernetes):
  ✓ Maximum flexibility
  ✓ Industry standard
  ✗ High complexity (overkill for MVP)
  ✗ Expensive ($200+/month minimum)
  ✗ Requires DevOps expertise

Azure Functions:
  ✓ Scale to zero
  ✓ Event-driven
  ✗ Execution time limits (10 min max)
  ✗ Not ideal for long-running jobs
  ✗ Cold start issues

Container Apps (Chosen):
  ✓ Scale to zero
  ✓ No time limits
  ✓ Container flexibility
  ✓ $0 when idle, $20-50/month active
```

**Architecture:**
```yaml
API Container App:
  - Public ingress
  - Auto-scale: 0-10 replicas
  - HTTP trigger

Worker Container App:
  - Internal only
  - Auto-scale: 0-5 replicas
  - Service Bus trigger (KEDA)
```

---

## 7. Document Generation: python-docx

### Decision: python-docx over alternatives

**Chosen:** python-docx library

**Alternatives Considered:**
- docxtpl (template-based)
- OpenPyXL + python-docx (advanced formatting)
- Aspose.Words (commercial)
- Convert from HTML/Markdown
- Azure Document Generation API (if available)

### Rationale

**Why python-docx:**
- ✅ **Pure Python** - no external dependencies
- ✅ **Comprehensive API** - supports all needed features
- ✅ **Active maintenance** - regularly updated
- ✅ **Good documentation** - easy to learn
- ✅ **Free and open-source**

**Feature Support:**
```python
from docx import Document
from docx.shared import Pt, RGBColor

doc = Document()

# All features we need:
✓ Headings (multiple levels)
✓ Paragraphs with rich text
✓ Bullet and numbered lists
✓ Text styling (bold, italic, colors, sizes)
✓ Page breaks
✓ Styles (Normal, Heading, Quote)
✓ Tables (for future use)
✓ Metadata (title, author, etc.)
```

**Alternatives Considered:**

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **python-docx** | Simple, complete | Basic formatting | ✅ **Chosen** |
| **docxtpl** | Template-based | Less flexible | ❌ Overkill |
| **Aspose.Words** | Advanced features | $1000+/year | ❌ Too expensive |
| **HTML→DOCX** | Familiar HTML | Poor formatting | ❌ Quality issues |

---

## 8. Authentication: Azure AD B2C

### Decision: Azure AD B2C over custom auth

**Chosen:** Azure Active Directory B2C

**Alternatives Considered:**
- Custom JWT auth (Auth0, Firebase)
- Azure AD (enterprise only)
- OpenID Connect (generic)
- API keys

### Rationale

**Why Azure AD B2C:**
- ✅ **Microsoft ecosystem native** - perfect fit for our deployment target
- ✅ **SSO support** - users sign in with company accounts
- ✅ **MFA built-in** - enterprise security
- ✅ **Compliance** - SOC 2, ISO 27001, HIPAA
- ✅ **No additional cost** - included in Azure subscription (50k users free)

**Enterprise Benefits:**
```
Azure AD B2C Features:
├─ Single Sign-On (SSO)
│  └─ Use existing company credentials
├─ Multi-Factor Authentication (MFA)
│  └─ SMS, authenticator app, phone call
├─ Conditional Access
│  └─ Require MFA from untrusted networks
├─ Audit Logs
│  └─ Track all authentication events
└─ Integration with Microsoft 365
   └─ Unified identity across organization
```

**Microsoft Ecosystem Fit:**
```
┌─────────────────────────────────────────┐
│        MICROSOFT IDENTITY               │
│                                         │
│  Azure AD B2C                           │
│     │                                   │
│     ├─→ ScriptToDoc (our app)          │
│     ├─→ SharePoint                      │
│     ├─→ Teams                           │
│     ├─→ OneDrive                        │
│     └─→ Other enterprise apps           │
│                                         │
│  Single identity for all services       │
└─────────────────────────────────────────┘
```

---

## 9. Frontend Deployment: Azure Static Web Apps

### Decision: Static Web Apps over App Service or CDN

**Chosen:** Azure Static Web Apps

**Alternatives Considered:**
- Azure App Service (for frontend)
- Azure Blob Storage + CDN
- Vercel / Netlify
- Azure Front Door + Storage

### Rationale

**Why Static Web Apps:**
- ✅ **Built for Next.js** - first-class support
- ✅ **Integrated CI/CD** - GitHub Actions auto-configured
- ✅ **Global CDN included** - fast worldwide
- ✅ **Free tier generous** - 100 GB bandwidth/month
- ✅ **Custom domains** - free SSL certificates
- ✅ **API routing** - can proxy to backend
- ✅ **Authentication built-in** - Azure AD integration

**Cost Comparison:**
```
Static Web Apps (Free Tier):
  - Hosting: $0
  - Bandwidth: 100 GB free
  - Custom domain: $0
  - SSL: $0
  Total: $0/month 🎉

App Service (S1):
  - Hosting: $70/month
  - Bandwidth: 165 GB included
  Total: $70/month

Blob + CDN:
  - Storage: $0.02/GB ($2 for 100 GB)
  - CDN: $0.081/GB ($8.10 for 100 GB)
  Total: $10.10/month

Verdict: Static Web Apps wins on cost AND features
```

---

## 10. Monitoring: Application Insights

### Decision: Application Insights over third-party APM

**Chosen:** Azure Application Insights

**Alternatives Considered:**
- Datadog
- New Relic
- Sentry (errors only)
- ELK Stack (self-hosted)

### Rationale

**Why Application Insights:**
- ✅ **Azure native** - automatic integration
- ✅ **Comprehensive** - metrics, logs, traces, errors
- ✅ **Low latency** - 2-3 second ingestion
- ✅ **Cost-effective** - 5 GB free per month
- ✅ **Smart detection** - ML-powered anomaly detection

**Feature Coverage:**
```
Application Insights:
├─ Metrics
│  ├─ Request duration
│  ├─ Dependency calls (Azure DI, OpenAI)
│  ├─ CPU/memory usage
│  └─ Custom metrics
├─ Logs
│  ├─ Structured logging
│  ├─ Log query language (KQL)
│  └─ Real-time streaming
├─ Distributed Tracing
│  └─ End-to-end request flow
├─ Errors
│  ├─ Exception tracking
│  ├─ Stack traces
│  └─ User impact
└─ Alerts
   ├─ Metric-based
   ├─ Log-based
   └─ Smart detection
```

**Cost (typical usage):**
```
Monthly Ingestion:
  - Logs: 10 GB @ $2.30/GB = $23
  - First 5 GB free = $0
  - Net: $11.50/month

vs Datadog:
  - Logs: 10 GB @ $0.10/GB = $1/GB ingestion + $1.70/GB retention
  - Total: ~$27/month
  
vs New Relic:
  - $99/month minimum (1 user)

Verdict: Application Insights is cheaper AND better integrated
```

---

## Summary: Technology Stack

### Final Stack (All Azure-Native)

```
┌─────────────────────────────────────────────────────────────┐
│                    SCRIPTTODOC STACK                         │
└─────────────────────────────────────────────────────────────┘

Frontend:
  ✓ Next.js 13+ (React framework)
  ✓ TypeScript (type safety)
  ✓ Tailwind CSS (styling)
  ✓ Azure Static Web Apps (hosting)

Backend:
  ✓ FastAPI (Python web framework)
  ✓ Pydantic (data validation)
  ✓ Azure Container Apps (hosting)

Data & Storage:
  ✓ Azure Cosmos DB (job state, NoSQL)
  ✓ Azure Blob Storage (files, documents)
  ✓ Azure Service Bus (job queue)

AI Services:
  ✓ Azure Document Intelligence (structure extraction)
  ✓ Azure OpenAI Service (content generation)
  ✓ Azure Computer Vision (video frames - Phase 3)
  ✓ Azure Speech-to-Text (video transcription - Phase 3)

Security & Operations:
  ✓ Azure AD B2C (authentication)
  ✓ Azure Key Vault (secrets management)
  ✓ Application Insights (monitoring)
  ✓ Azure Front Door + WAF (security)

Development:
  ✓ GitHub Actions (CI/CD)
  ✓ Azure Container Registry (Docker images)
  ✓ Docker (containerization)
```

### Cost Estimate (100 jobs/day)

```
Service                          Monthly Cost
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Container Apps (API + Worker)    $75
Azure OpenAI Service             $150
Azure Document Intelligence      $30
Cosmos DB (Serverless)           $25
Blob Storage                     $15
Service Bus                      $5
Other (Key Vault, Insights)      $10
────────────────────────────────────────
TOTAL                            $310/month

Per-Job Cost: ~$0.10
```

### Decision Principles Used

1. **Azure-First:** Maximize Microsoft ecosystem integration
2. **Serverless Where Possible:** Scale to zero for cost savings
3. **Managed Services:** Minimize operational overhead
4. **Type Safety:** TypeScript + Pydantic for fewer bugs
5. **Observability:** Built-in monitoring from day one
6. **Security:** Enterprise-grade auth and secrets management
7. **Performance:** Async/await for I/O-bound operations
8. **Cost-Effective:** Optimize for variable workloads

---

**These decisions create a modern, scalable, and cost-effective architecture that fits perfectly within the Microsoft ecosystem.**

