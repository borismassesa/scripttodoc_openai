# Script to Doc Application Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                                   │
│                    Azure Static Web Apps                                     │
│                  • Upload Interface                                          │
│                  • Job Status Dashboard                                      │
│                  • Document Download                                          │
└──────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                │ HTTPS / REST API
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    API CONTAINER APP (Azure Container Apps)                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                                 │   │
│  │  • CPU: 0.5 cores | Memory: 1 GB                                    │   │
│  │  • Min Replicas: 0 (scale to zero) | Max: 10                         │   │
│  │                                                                       │   │
│  │  Endpoints:                                                           │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ POST /api/process          - Upload transcript, create job    │  │   │
│  │  │ GET  /api/status/{job_id}  - Get job status & progress        │  │   │
│  │  │ GET  /api/jobs             - List user's jobs                  │  │   │
│  │  │ GET  /api/documents/{id}   - Download generated document      │  │   │
│  │  │ GET  /health                - Health check (liveness/readiness) │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────┬───────────────────────────┬───────────────────────────┬─────────────┘
        │                           │                           │
        │ Upload Files              │ Job Status                │ Queue Jobs
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Azure Blob   │          │ Cosmos DB    │          │ Service Bus   │
│ Storage      │          │ (Serverless) │          │ Queue         │
│              │          │              │          │              │
│ Containers:  │          │ Database:    │          │ Queue:       │
│ • uploads/   │          │   scripttodoc│          │   scripttodoc│
│ • documents/ │          │              │          │   -jobs      │
│ • temp/      │          │ Container:   │          │              │
│              │          │   jobs       │          │              │
│ Files:       │          │              │          │ Messages:    │
│ • Transcripts│          │ Documents:   │          │ • job_id     │
│ • Documents  │          │   • id       │          │ • user_id    │
│ • Temp files │          │   • status   │          │ • transcript │
│              │          │   • progress │          │   _url       │
│              │          │   • stage    │          │ • config     │
│              │          │   • result   │          │              │
└──────────────┘          └──────────────┘          └──────┬───────┘
                                                            │
                                                            │ Poll Queue
                                                            │ (Service Bus Trigger)
                                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  WORKER CONTAINER APP (Azure Container Apps)                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Background Job Processor                                            │   │
│  │  • CPU: 1.0 core | Memory: 2 GB                                    │   │
│  │  • Min Replicas: 0 (scale to zero) | Max: 5                         │   │
│  │  • Trigger: Service Bus queue messages                               │   │
│  │                                                                       │   │
│  │  Processing Pipeline:                                                │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ 1. Receive job message from Service Bus                        │  │   │
│  │  │ 2. Download transcript from Blob Storage                        │  │   │
│  │  │ 3. Clean transcript (remove timestamps, fillers)              │  │   │
│  │  │ 4. Azure Document Intelligence (structure analysis)            │  │   │
│  │  │ 5. Topic segmentation & determine step count                   │  │   │
│  │  │ 6. Generate training steps (Azure OpenAI GPT-4o-mini)        │  │   │
│  │  │ 7. Create source references & citations                        │  │   │
│  │  │ 8. Generate Word document (python-docx)                       │  │   │
│  │  │ 9. Upload document to Blob Storage                              │  │   │
│  │  │ 10. Update job status in Cosmos DB (completed)                  │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                       │   │
│  │  Progress Updates:                                                   │   │
│  │  • Updates Cosmos DB throughout processing                           │   │
│  │  • Reports progress: 0.0 → 1.0                                      │   │
│  │  • Current stage: load → clean → analyze → generate → complete      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────┬───────────────────────────┬───────────────────────────┬─────────────┘
        │                           │                           │
        │ Download/Upload          │ Status Updates            │ AI Services
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Azure Blob   │          │ Cosmos DB    │          │ Azure OpenAI │
│ Storage      │          │ (Serverless) │          │              │
│              │          │              │          │ • GPT-4o-mini │
│ • Read       │          │ • Update     │          │   (text      │
│   transcripts│          │   status     │          │   generation)│
│ • Write      │          │ • Update     │          │              │
│   documents  │          │   progress   │          │              │
└──────────────┘          └──────────────┘          └──────┬───────┘
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
                                                  │   Analysis   │
                                                  └──────────────┘
```

## Component Details

### API Container App

**Technology:** FastAPI (Python), Uvicorn ASGI server

**Responsibilities:**
- Handle HTTP requests from frontend
- Validate and store uploaded files
- Create job records
- Queue jobs for processing
- Return job status and progress
- Serve generated documents

**Resource Allocation:**
- **CPU:** 0.5 cores (sufficient for I/O-bound operations)
- **Memory:** 1 GB (lightweight API operations)
- **Scaling:** 0-10 replicas based on HTTP request load

**Key Operations:**
- File upload validation (< 1 second)
- Database queries (< 100ms)
- Queue message sending (< 50ms)
- Document download (< 2 seconds)

---

### Worker Container App

**Technology:** Python, Azure SDK, python-docx

**Responsibilities:**
- Process jobs from Service Bus queue
- Execute document generation pipeline
- Update job progress in real-time
- Handle errors and retries

**Resource Allocation:**
- **CPU:** 1.0 core (needed for AI processing and document generation)
- **Memory:** 2 GB (stores transcript, AI responses, document content)
- **Scaling:** 0-5 replicas based on queue depth

**Key Operations:**
- Transcript processing (30-60 seconds)
- AI content generation (1-5 minutes)
- Document generation (30-120 seconds)
- **Total processing time:** 2-10 minutes per job

---

## Data Flow Sequence

### 1. Upload & Job Creation
```
User → Frontend → API Container
  → Validate file
  → Upload to Blob Storage (uploads/)
  → Create job in Cosmos DB
  → Send message to Service Bus queue
  → Return job_id to user
```

### 2. Background Processing
```
Service Bus Queue → Worker Container
  → Receive job message
  → Download transcript from Blob Storage
  → Process pipeline (8 stages)
  → Update progress in Cosmos DB (multiple times)
  → Generate Word document
  → Upload document to Blob Storage (documents/)
  → Mark job complete in Cosmos DB
```

### 3. Status Polling
```
User → Frontend → API Container
  → Query Cosmos DB for job status
  → Return current progress, stage, status
  → User sees real-time updates
```

### 4. Document Download
```
User → Frontend → API Container
  → Get document URL from Cosmos DB
  → Generate SAS token for Blob Storage
  → Return download link to user
  → User downloads Word document
```

---

## Supporting Services

### Azure Blob Storage
- **Purpose:** File storage (transcripts, documents, temp files)
- **Containers:**
  - `uploads/` - User-uploaded transcripts
  - `documents/` - Generated Word documents
  - `temp/` - Temporary processing files (auto-deleted after 1 day)

### Cosmos DB (Serverless)
- **Purpose:** Job status and metadata storage
- **Database:** `scripttodoc`
- **Container:** `jobs`
- **Partition Key:** `user_id`
- **Documents:** Job records with status, progress, results

### Service Bus (Standard)
- **Purpose:** Reliable job queue
- **Queue:** `scripttodoc-jobs`
- **Features:** Dead-letter queue, duplicate detection, TTL

### Azure OpenAI
- **Purpose:** AI content generation
- **Model:** GPT-4o-mini
- **Usage:** Generate training steps, improve content quality

### Azure Document Intelligence
- **Purpose:** Structure analysis
- **Models:** Prebuilt Read, Layout
- **Usage:** Extract paragraphs, identify actions, find sequences

### Azure Key Vault
- **Purpose:** Secrets management
- **Stores:** API keys, connection strings, credentials

### Application Insights
- **Purpose:** Monitoring and logging
- **Tracks:** Performance, errors, usage metrics

---

## Scaling Behavior

### API Container
- **Scale Up:** When concurrent requests > 10
- **Scale Down:** When idle for 5+ minutes (scale to zero)
- **Cold Start:** 5-30 seconds when scaling from zero

### Worker Container
- **Scale Up:** When queue messages > 5
- **Scale Down:** When queue is empty for 5+ minutes (scale to zero)
- **Cold Start:** 10-30 seconds when scaling from zero

---

## Cost Optimization Features

1. **Scale to Zero:** Both containers scale to zero when idle
2. **Right-Sized Resources:** Minimal CPU/memory for each workload
3. **Serverless Services:** Cosmos DB, Blob Storage use pay-per-use
4. **Lifecycle Policies:** Auto-delete temp files after 1 day
5. **Efficient Queries:** Cosmos DB queries optimized with partition keys

---

**Last Updated:** January 2025
