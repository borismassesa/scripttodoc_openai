# API and Worker Containers: Detailed Explanation

## Overview

Your application uses a **microservices architecture** with two separate containers:

1. **API Container** - Handles user requests (FastAPI REST API)
2. **Worker Container** - Processes jobs in the background (Document generation pipeline)

This separation allows:
- ✅ **Scalability:** Scale API and Worker independently
- ✅ **Reliability:** Worker failures don't affect API
- ✅ **Cost Optimization:** Scale Worker to zero when no jobs
- ✅ **Performance:** API stays responsive while Worker processes heavy tasks

---

## API Container: Detailed Breakdown

### Purpose

The API container is your **user-facing REST API** that handles all HTTP requests from the frontend.

### What It Does

#### 1. **File Upload Endpoint** (`POST /api/process`)

**User Action:** User uploads a transcript file (.txt or .pdf)

**API Process:**
```
1. Receive file upload from frontend
   ↓
2. Validate file:
   - Check file size (max 50 MB)
   - Check file type (.txt or .pdf)
   - Extract text from PDF if needed
   ↓
3. Upload to Blob Storage:
   - Store in "uploads/" container
   - Generate unique blob URL
   ↓
4. Create job record in Cosmos DB:
   - Generate unique job_id
   - Store job metadata (status, config, user_id)
   - Set status to "queued"
   ↓
5. Send message to Service Bus queue:
   - Queue name: "scripttodoc-jobs"
   - Message contains: job_id, transcript_url, config
   ↓
6. Return job_id to user
   - User can use this to check status
```

**Response Time:** < 1 second (fast, synchronous operation)

**Key Code:**
```python
@router.post("/api/process")
async def process_transcript(file: UploadFile, ...):
    # Validate file
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    # Extract text
    extracted_text, file_type = process_uploaded_file(file.filename, content)
    
    # Upload to Blob Storage
    blob_client.upload_blob(extracted_text.encode('utf-8'))
    
    # Create job in Cosmos DB
    job_record = {
        "id": job_id,
        "status": "queued",
        "config": {...}
    }
    container.create_item(body=job_record)
    
    # Send to Service Bus queue
    message = ServiceBusMessage(json.dumps({
        "job_id": job_id,
        "transcript_url": transcript_url,
        "config": config
    }))
    queue_client.send_messages(message)
    
    return {"job_id": job_id, "status": "queued"}
```

---

#### 2. **Job Status Endpoint** (`GET /api/status/{job_id}`)

**User Action:** User checks status of their job

**API Process:**
```
1. Receive job_id from frontend
   ↓
2. Query Cosmos DB:
   - Find job by job_id and user_id
   - Return current status, progress, stage
   ↓
3. Return status to user:
   - status: "queued", "processing", "completed", "failed"
   - progress: 0.0 to 1.0 (percentage complete)
   - stage: Current processing stage
   - result: Document URL (if completed)
```

**Response Time:** < 100ms (fast database query)

**Key Code:**
```python
@router.get("/api/status/{job_id}")
async def get_job_status(job_id: str, user_id: str):
    # Query Cosmos DB
    job = container.read_item(item=job_id, partition_key=user_id)
    
    return {
        "job_id": job["id"],
        "status": job["status"],  # "processing"
        "progress": job["progress"],  # 0.65 (65% complete)
        "stage": job["stage"],  # "generate_steps"
        "result": job.get("result")  # Document URL if completed
    }
```

---

#### 3. **Job List Endpoint** (`GET /api/jobs`)

**User Action:** User views their job history

**API Process:**
```
1. Receive user_id (from authentication)
   ↓
2. Query Cosmos DB:
   - Find all jobs for this user
   - Order by created_at (newest first)
   - Limit to 10-50 jobs
   ↓
3. Return list of jobs:
   - Each job: id, status, progress, created_at, result
```

**Response Time:** < 200ms (database query with partition key)

---

#### 4. **Document Download Endpoint** (`GET /api/documents/{job_id}`)

**User Action:** User downloads the generated Word document

**API Process:**
```
1. Receive job_id from frontend
   ↓
2. Query Cosmos DB:
   - Find job by job_id
   - Get document URL from job result
   ↓
3. Generate SAS token for Blob Storage:
   - Temporary access token (expires in 1 hour)
   - Allows secure download without public access
   ↓
4. Return download URL to user:
   - User's browser downloads document
```

**Response Time:** < 200ms (fast, generates temporary URL)

---

#### 5. **Health Check Endpoint** (`GET /health`)

**Purpose:** Used by Container Apps for monitoring

**API Process:**
```
1. Check connectivity to all services:
   - Cosmos DB: Connected
   - Blob Storage: Connected
   - Service Bus: Connected
   - Azure OpenAI: Configured
   - Document Intelligence: Configured
   ↓
2. Return health status:
   - "healthy" if all services available
   - "unhealthy" if any service unavailable
```

**Used By:**
- Container Apps liveness probe (restarts container if unhealthy)
- Container Apps readiness probe (routes traffic only when ready)
- Monitoring dashboards

---

### API Container Characteristics

**Workload Type:** I/O-bound
- Most operations are database queries or file uploads
- Not CPU-intensive
- Fast response times (< 200ms)

**Resource Requirements:**
- **CPU: 0.5 cores** - Sufficient for HTTP handling and database queries
- **Memory: 1 GB** - FastAPI app, Azure SDK clients, request buffers

**Scaling:**
- **Min Replicas: 0** (scale to zero when idle)
- **Max Replicas: 10** (scale up with traffic)
- **Trigger:** HTTP request load (concurrent requests > 10)

**Traffic Pattern:**
- Variable/spiky traffic
- Most requests are quick (< 1 second)
- No long-running operations (jobs are queued)

---

## Worker Container: Detailed Breakdown

### Purpose

The Worker container is your **background job processor** that handles the actual document generation.

### What It Does

#### Main Processing Loop

**Worker Process:**
```
1. Listen to Service Bus queue ("scripttodoc-jobs")
   ↓
2. Receive message when job is queued
   ↓
3. Process job (8-stage pipeline)
   ↓
4. Update progress in Cosmos DB throughout
   ↓
5. Mark job complete when done
   ↓
6. Return to step 1 (listen for next job)
```

**Key Code:**
```python
def main():
    # Connect to Service Bus
    receiver = sb_client.get_queue_receiver("scripttodoc-jobs")
    
    # Listen for messages
    with receiver:
        for message in receiver:
            try:
                # Parse message
                body = json.loads(str(message))
                
                # Process job
                processor.process_job(body)
                
                # Mark message as complete
                receiver.complete_message(message)
            except Exception as e:
                # Handle errors
                logger.error(f"Failed to process: {e}")
                receiver.abandon_message(message)
```

---

### 8-Stage Document Generation Pipeline

#### Stage 1: Load Transcript (Progress: 0.05)

**What Happens:**
```
1. Download transcript from Blob Storage
   - URL from job message
   - Download as bytes
   - Decode to UTF-8 text
   ↓
2. Update job status:
   - status: "processing"
   - progress: 0.05
   - stage: "load_transcript"
```

**Time:** 1-5 seconds (depending on file size)

---

#### Stage 2: Clean Transcript (Progress: 0.15)

**What Happens:**
```
1. Remove timestamps:
   - Pattern: [00:15:32] or 00:15:32
   - Example: "[00:15:32] Speaker 1: Hello" → "Hello"
   ↓
2. Remove speaker labels:
   - Pattern: "Speaker 1:", "SPEAKER_1:", etc.
   - Example: "Speaker 1: Hello" → "Hello"
   ↓
3. Remove filler words:
   - Words: "um", "uh", "like", "you know"
   - Example: "Um, so like, you know" → "So"
   ↓
4. Remove tags:
   - Pattern: [laughs], (background noise), etc.
   - Example: "Hello [laughs] world" → "Hello world"
   ↓
5. Fix punctuation and capitalization
```

**Time:** 1-3 seconds

**Result:** Clean, readable transcript text

---

#### Stage 3: Azure Document Intelligence Analysis (Progress: 0.35)

**What Happens:**
```
1. Upload cleaned transcript to temp blob
   - Temporary storage for Azure DI
   ↓
2. Call Azure Document Intelligence:
   - Model: "prebuilt-read" or "prebuilt-layout"
   - Analyze document structure
   - Extract paragraphs, headings, lists
   ↓
3. Extract structure:
   - Identify actions (verbs, commands)
   - Find sequence indicators ("first", "then", "next")
   - Detect roles ("user", "admin", "system")
   - Identify decision points ("if", "when", "unless")
```

**Time:** 5-15 seconds (API call to Azure DI)

**Result:** Document structure with actions, sequences, roles

---

#### Stage 4: Topic Segmentation (Progress: 0.40)

**What Happens:**
```
1. Analyze transcript complexity:
   - Count actions, decisions, roles
   - Measure transcript length
   - Identify natural topic boundaries
   ↓
2. Determine optimal step count:
   - Use OpenAI to suggest step count
   - Respect min_steps and max_steps from config
   - Example: 8 steps for medium complexity
   ↓
3. Segment transcript into topics:
   - Each topic becomes a training step
   - Maintain logical flow
```

**Time:** 10-30 seconds (OpenAI API call)

**Result:** Transcript divided into N training steps

---

#### Stage 5: Generate Training Steps (Progress: 0.60)

**What Happens:**
```
For each topic segment:
  1. Create prompt for OpenAI:
     - Include topic text
     - Include tone and audience from config
     - Request step description, instructions, examples
     ↓
  2. Call Azure OpenAI (GPT-4o-mini):
     - Generate step content
     - Format as structured training step
     ↓
  3. Extract step information:
     - Step title
     - Step description
     - Instructions
     - Examples (if applicable)
```

**Time:** 30-120 seconds (multiple OpenAI API calls)

**Result:** Complete training steps with content

---

#### Stage 6: Create Source References (Progress: 0.75)

**What Happens:**
```
1. For each step, find source sentences:
   - Match step content to original transcript
   - Identify which sentences support each step
   ↓
2. Create citations:
   - Link steps to source transcript sections
   - Add timestamps (if available)
   - Add context (surrounding sentences)
```

**Time:** 5-15 seconds

**Result:** Steps with source references and citations

---

#### Stage 7: Generate Word Document (Progress: 0.90)

**What Happens:**
```
1. Create Word document using python-docx:
   - Add title page
   - Add table of contents
   - Add introduction
   ↓
2. For each training step:
   - Add step heading
   - Add step description
   - Add instructions
   - Add examples
   - Add source references
   ↓
3. Add appendix:
   - Statistics (word count, step count)
   - Metadata (generated date, config)
   ↓
4. Apply formatting:
   - Styles, fonts, colors
   - Page breaks, headers, footers
```

**Time:** 10-30 seconds

**Result:** Complete Word document (.docx file)

---

#### Stage 8: Upload and Complete (Progress: 1.0)

**What Happens:**
```
1. Upload Word document to Blob Storage:
   - Container: "documents/"
   - Filename: "{job_id}_training.docx"
   - Generate blob URL
   ↓
2. Update job status in Cosmos DB:
   - status: "completed"
   - progress: 1.0
   - stage: "complete"
   - result: {
       "document_url": "...",
       "document_size_mb": 2.5,
       "steps_generated": 8
     }
   ↓
3. Log completion
```

**Time:** 2-5 seconds

**Result:** Job marked complete, document available for download

---

### Worker Container Characteristics

**Workload Type:** CPU and I/O intensive
- AI processing (OpenAI API calls)
- Document generation (XML processing)
- File I/O (download/upload)

**Resource Requirements:**
- **CPU: 1.0 core** - Needed for AI processing and document generation
- **Memory: 2 GB** - Stores transcript, AI responses, document content

**Scaling:**
- **Min Replicas: 0** (scale to zero when queue is empty)
- **Max Replicas: 5** (scale up with queue depth)
- **Trigger:** Service Bus queue messages (scale up when 5+ messages)

**Processing Time:**
- **Per Job:** 2-10 minutes (depending on transcript length)
- **Typical:** 3-5 minutes for average transcript

**Concurrency:**
- Typically processes 1 job at a time per instance
- Can scale horizontally (multiple instances process multiple jobs)

---

## How They Work Together

### Complete User Journey

```
1. User uploads transcript
   ↓
2. API Container:
   - Validates file
   - Stores in Blob Storage
   - Creates job in Cosmos DB
   - Queues job in Service Bus
   - Returns job_id (< 1 second)
   ↓
3. Worker Container:
   - Receives job from queue
   - Processes 8-stage pipeline (3-5 minutes)
   - Updates progress in Cosmos DB
   - Uploads document to Blob Storage
   - Marks job complete
   ↓
4. User polls API:
   - API queries Cosmos DB
   - Returns current progress
   - User sees: "Processing... 65% complete"
   ↓
5. User downloads document:
   - API generates download URL
   - User downloads Word document
```

### Key Interactions

**API → Cosmos DB:**
- Create job records
- Query job status
- Update job metadata

**API → Blob Storage:**
- Upload transcripts
- Generate download URLs
- Store files

**API → Service Bus:**
- Queue jobs for processing
- Send job messages

**Worker → Service Bus:**
- Listen for job messages
- Receive jobs to process

**Worker → Cosmos DB:**
- Update job progress
- Mark jobs complete/failed

**Worker → Blob Storage:**
- Download transcripts
- Upload generated documents

**Worker → Azure OpenAI:**
- Generate training step content
- Analyze transcript structure

**Worker → Document Intelligence:**
- Analyze document structure
- Extract actions and sequences

---

## Why Two Containers?

### Separation of Concerns

**API Container:**
- Fast, responsive user interface
- Handles HTTP requests
- Lightweight operations

**Worker Container:**
- Heavy processing
- Long-running tasks
- Background operations

### Benefits

1. **Independent Scaling:**
   - API scales with user traffic
   - Worker scales with job queue depth
   - Optimize costs independently

2. **Reliability:**
   - Worker failures don't affect API
   - API failures don't affect job processing
   - Isolated error handling

3. **Performance:**
   - API stays responsive (no blocking operations)
   - Worker can process jobs without affecting API
   - Better resource utilization

4. **Cost Optimization:**
   - API can scale to zero when idle
   - Worker can scale to zero when queue is empty
   - Pay only for what you use

---

## Summary

**API Container:**
- **Purpose:** User-facing REST API
- **Does:** File uploads, status checks, job management
- **Resources:** 0.5 CPU, 1 GB RAM
- **Response Time:** < 200ms
- **Scaling:** Based on HTTP traffic

**Worker Container:**
- **Purpose:** Background job processor
- **Does:** 8-stage document generation pipeline
- **Resources:** 1.0 CPU, 2 GB RAM
- **Processing Time:** 2-10 minutes per job
- **Scaling:** Based on queue depth

**Together:** They create a scalable, reliable, cost-effective document generation system.

---

**Last Updated:** January 2025
