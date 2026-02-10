# ScriptToDoc - Data Flow & State Management

## Overview

This document details how data flows through the ScriptToDoc system, from user upload through processing to final document delivery. It includes data schemas, state transitions, storage patterns, and integration points.

---

## End-to-End Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DATA LIFECYCLE                                │
└──────────────────────────────────────────────────────────────────────┘

[1] USER INPUT
    │
    ├─> File Upload (Frontend)
    │   ├─> transcript.txt (text/plain, < 5 MB)
    │   ├─> screenshots/*.png (image/png, < 2 MB each)
    │   └─> video.mp4 (video/mp4, < 500 MB)
    │
    ├─> Configuration (Form Data)
    │   {
    │     "tone": "Professional" | "Casual" | "Neutral" | "Technical",
    │     "audience": "General" | "Technical" | "Non-Technical" | "Expert",
    │     "min_steps": 3-10,
    │     "target_steps": 5-20,
    │     "use_azure_di": true | false,
    │     "use_openai": true | false
    │   }
    │
    └─> HTTP POST to /process
        └─> multipart/form-data
            ├─> file: File
            ├─> screenshots: File[]
            └─> config: JSON

[2] API INGESTION (FastAPI)
    │
    ├─> Request Validation (Pydantic)
    │   {
    │     "file": {
    │       "filename": "transcript.txt",
    │       "size": 256000,  # 256 KB
    │       "content_type": "text/plain"
    │     },
    │     "screenshots": [
    │       {"filename": "screen1.png", "size": 1024000},
    │       {"filename": "screen2.png", "size": 892000}
    │     ]
    │   }
    │
    ├─> Generate Job ID
    │   └─> job_id = uuid.uuid4() → "550e8400-e29b-41d4-a716-446655440000"
    │
    ├─> Upload to Azure Blob Storage
    │   └─> Container: uploads
    │       └─> {job_id}/
    │           ├─> transcript.txt
    │           └─> screenshots/
    │               ├─> screen_01.png
    │               └─> screen_02.png
    │
    ├─> Create Job Record (Cosmos DB)
    │   └─> Database: scripttodoc
    │       └─> Container: jobs
    │           └─> Document:
    │               {
    │                 "id": "550e8400-...",
    │                 "partitionKey": "user_12345",
    │                 "status": "queued",
    │                 "created_at": "2025-11-03T10:00:00Z",
    │                 "input": {
    │                   "transcript_url": "https://stscripttodoc.blob.core.windows.net/uploads/550e8400.../transcript.txt",
    │                   "screenshot_urls": [...]
    │                 },
    │                 "config": {...},
    │                 "_ts": 1699012800  # Cosmos timestamp
    │               }
    │
    └─> Send to Service Bus Queue
        └─> Queue: scripttodoc-jobs
            └─> Message:
                {
                  "MessageId": "msg_abc123",
                  "Body": {
                    "job_id": "550e8400-...",
                    "transcript_url": "...",
                    "config": {...}
                  },
                  "EnqueuedTime": "2025-11-03T10:00:01Z",
                  "TimeToLive": "PT30M"  # 30 minutes
                }

[3] BACKGROUND PROCESSING (Worker)
    │
    ├─> Poll Service Bus Queue
    │   └─> Receive message (peek-lock mode)
    │
    ├─> Update Job Status
    │   └─> Cosmos DB PATCH:
    │       {
    │         "status": "processing",
    │         "progress": 0.05,
    │         "stage": "load_transcript"
    │       }
    │
    ├─> Download from Blob Storage
    │   └─> GET {transcript_url}
    │       └─> Response: raw transcript text (UTF-8)
    │
    ├─> STAGE 1: Clean Transcript
    │   │
    │   Input:
    │   "[00:15:32] Speaker 1: Um, so like, first you need to, you know, open the Azure portal. [laughs]"
    │   
    │   Transformations:
    │   ├─> Remove timestamps: regex r'\[?\d{2}:\d{2}(?::\d{2})?\]?'
    │   ├─> Remove speaker labels: regex r'^(Speaker \d+|[A-Z]+):\s*'
    │   ├─> Remove filler words: ['um', 'uh', 'like', 'you know']
    │   └─> Remove tags: regex r'\[[^\]]+\]|\([^)]+\)'
    │   
    │   Output:
    │   "First you need to open the Azure portal."
    │   
    │   └─> Update: progress=0.15, stage="clean_transcript"
    │
    ├─> STAGE 2: Azure DI Analysis
    │   │
    │   ├─> Upload cleaned text to temp blob
    │   │   └─> temp/{job_id}/cleaned_transcript.txt
    │   │
    │   ├─> Call Azure Document Intelligence
    │   │   │
    │   │   Request:
    │   │   POST https://{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2024-02-29-preview
    │   │   {
    │   │     "urlSource": "https://.../cleaned_transcript.txt"
    │   │   }
    │   │   
    │   │   Response (async):
    │   │   {
    │   │     "status": "running",
    │   │     "createdDateTime": "...",
    │   │     "lastUpdatedDateTime": "...",
    │   │     "analyzeResult": null
    │   │   }
    │   │   
    │   │   Poll until complete:
    │   │   GET {operation-location}
    │   │   
    │   │   Final Response:
    │   │   {
    │   │     "status": "succeeded",
    │   │     "analyzeResult": {
    │   │       "content": "First you need to open...",
    │   │       "pages": [{
    │   │         "pageNumber": 1,
    │   │         "spans": [{"offset": 0, "length": 1500}],
    │   │         "words": [...],
    │   │         "lines": [...]
    │   │       }],
    │   │       "paragraphs": [
    │   │         {
    │   │           "role": "title",
    │   │           "content": "Azure Portal Navigation",
    │   │           "spans": [{"offset": 0, "length": 27}]
    │   │         },
    │   │         {
    │   │           "role": "content",
    │   │           "content": "First you need to open the Azure portal...",
    │   │           "spans": [{"offset": 28, "length": 150}]
    │   │         }
    │   │       ],
    │   │       "styles": [...]
    │   │     }
    │   │   }
    │   │
    │   ├─> Process Structure Extraction
    │   │   │
    │   │   Pattern Recognition:
    │   │   ├─> Action verbs: "open", "click", "navigate", "create"
    │   │   ├─> Sequential markers: "first", "then", "next", "finally"
    │   │   ├─> Decision points: "if", "when", "choose"
    │   │   └─> Role mentions: "admin", "user", "trainer"
    │   │   
    │   │   Output:
    │   │   {
    │   │     "steps": [
    │   │       "open the Azure portal",
    │   │       "navigate to resource groups",
    │   │       "create new resource group"
    │   │     ],
    │   │     "decisions": [
    │   │       "if no permissions → contact admin"
    │   │     ],
    │   │     "sequence": [1, 2, 3],
    │   │     "roles": ["user", "admin"]
    │   │   }
    │   │
    │   └─> Cache result in Cosmos DB
    │       └─> Container: processing_cache
    │           └─> Document (TTL: 24 hours):
    │               {
    │                 "id": "azure_di_{job_id}",
    │                 "result": {...},
    │                 "ttl": 86400
    │               }
    │
    ├─> STAGE 3: Screenshot Analysis (if provided)
    │   │
    │   For each screenshot:
    │   │
    │   ├─> Call Azure DI (prebuilt-layout)
    │   │   │
    │   │   Request:
    │   │   POST .../documentModels/prebuilt-layout:analyze
    │   │   {
    │   │     "urlSource": "https://.../screen_01.png"
    │   │   }
    │   │   
    │   │   Response:
    │   │   {
    │   │     "analyzeResult": {
    │   │       "content": "Create Resource Group Name Description",
    │   │       "pages": [{
    │   │         "width": 1920,
    │   │         "height": 1080,
    │   │         "words": [
    │   │           {"content": "Create", "polygon": [...]},
    │   │           {"content": "Resource", "polygon": [...]},
    │   │           ...
    │   │         ]
    │   │       }],
    │   │       "tables": [
    │   │         {
    │   │           "rowCount": 3,
    │   │           "columnCount": 2,
    │   │           "cells": [...]
    │   │         }
    │   │       ]
    │   │     }
    │   │   }
    │   │
    │   ├─> Extract UI Elements
    │   │   │
    │   │   Heuristics:
    │   │   ├─> Buttons: short text (1-3 words), rectangular bounds
    │   │   ├─> Menus: text in header area, horizontal arrangement
    │   │   ├─> Forms: label-value pairs, vertical stacking
    │   │   └─> Tables: detected by Azure DI table model
    │   │   
    │   │   Output:
    │   │   {
    │   │     "screenshot": "screen_01.png",
    │   │     "ui_elements": [
    │   │       {"type": "button", "text": "Create", "location": [120, 45]},
    │   │       {"type": "menu", "text": "File", "location": [10, 10]},
    │   │       {"type": "textbox", "text": "Resource name", "location": [200, 150]}
    │   │     ],
    │   │     "tables": [...],
    │   │     "full_content": "Create Resource Group Name..."
    │   │   }
    │   │
    │   └─> Store screenshot analysis
    │       └─> In-memory cache for current job
    │
    ├─> STAGE 4: Build Source Catalog
    │   │
    │   ├─> Sentence Tokenization (NLTK)
    │   │   │
    │   │   Input: "First you need to open the Azure portal. Then navigate to resource groups. Create a new group."
    │   │   
    │   │   Output:
    │   │   [
    │   │     {"index": 0, "text": "First you need to open the Azure portal."},
    │   │     {"index": 1, "text": "Then navigate to resource groups."},
    │   │     {"index": 2, "text": "Create a new group."}
    │   │   ]
    │   │
    │   └─> Store sentence catalog
    │       └─> In-memory for quick lookup
    │
    ├─> STAGE 5: Generate Summary (OpenAI)
    │   │
    │   ├─> Call Azure OpenAI
    │   │   │
    │   │   Request:
    │   │   POST https://{endpoint}/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01
    │   │   {
    │   │     "messages": [
    │   │       {
    │   │         "role": "system",
    │   │         "content": "You are a technical documentation expert..."
    │   │       },
    │   │       {
    │   │         "role": "user",
    │   │         "content": "Summarize this transcript into 8 key actionable sentences. Tone: Professional..."
    │   │       }
    │   │     ],
    │   │     "temperature": 0.2,
    │   │     "max_tokens": 1000
    │   │   }
    │   │   
    │   │   Response:
    │   │   {
    │   │     "choices": [{
    │   │       "message": {
    │   │         "role": "assistant",
    │   │         "content": "1. Access the Azure portal...\n2. Navigate to resource groups...\n3. Create a new resource group..."
    │   │       }
    │   │     }],
    │   │     "usage": {
    │   │       "prompt_tokens": 450,
    │   │       "completion_tokens": 180,
    │   │       "total_tokens": 630
    │   │     }
    │   │   }
    │   │
    │   ├─> Parse summary into sentences
    │   │   └─> ["Access the Azure portal", "Navigate to resource groups", ...]
    │   │
    │   └─> Track token usage
    │       └─> Store in job metrics
    │
    ├─> STAGE 6: Generate Detailed Steps (OpenAI)
    │   │
    │   For each summary sentence:
    │   │
    │   ├─> Call Azure OpenAI (expansion)
    │   │   │
    │   │   Prompt:
    │   │   "Expand this action into a detailed training step:
    │   │    Action: 'Access the Azure portal'
    │   │    
    │   │    Provide:
    │   │    - Title (concise)
    │   │    - Summary (1 sentence overview)
    │   │    - Details (2-3 sentence explanation)
    │   │    - Actions (3-5 bullet points)
    │   │    
    │   │    Format as JSON."
    │   │   
    │   │   Response:
    │   │   {
    │   │     "title": "Access Azure Portal",
    │   │     "summary": "Navigate to portal.azure.com and authenticate with your credentials",
    │   │     "details": "Open your web browser and navigate to the Azure portal URL. Enter your organizational credentials to sign in. Once authenticated, you'll see the Azure dashboard.",
    │   │     "actions": [
    │   │       "Open web browser",
    │   │       "Navigate to portal.azure.com",
    │   │       "Enter your credentials",
    │   │       "Click Sign In",
    │   │       "Wait for dashboard to load"
    │   │     ]
    │   │   }
    │   │
    │   ├─> Find Source References
    │   │   │
    │   │   ├─> Search transcript sentences
    │   │   │   └─> TF-IDF similarity matching
    │   │   │       └─> Step content: "Open your web browser and navigate to the Azure portal"
    │   │   │           vs
    │   │   │           Sentence 0: "First you need to open the Azure portal"
    │   │   │           → Similarity: 0.87 ✓
    │   │   │
    │   │   ├─> Create transcript source
    │   │   │   {
    │   │   │     "type": "transcript",
    │   │   │     "excerpt": "First you need to open the Azure portal",
    │   │   │     "sentence_index": 0,
    │   │   │     "confidence": 0.87
    │   │   │   }
    │   │   │
    │   │   ├─> Search screenshot UI elements (if available)
    │   │   │   └─> Extract actions from step: "navigate to portal.azure.com"
    │   │   │       └─> Search screenshots for "portal" or "azure"
    │   │   │           └─> Found in screen_01.png: "portal.azure.com" in browser bar
    │   │   │               → Match confidence: 0.92 ✓
    │   │   │
    │   │   └─> Create visual source
    │   │       {
    │   │         "type": "visual",
    │   │         "excerpt": "Screenshot showing Azure portal URL in browser",
    │   │         "screenshot_ref": "screen_01.png",
    │   │         "ui_elements": ["portal.azure.com"],
    │   │         "confidence": 0.92
    │   │       }
    │   │
    │   ├─> Calculate Confidence Score
    │   │   │
    │   │   Factors:
    │   │   ├─> Average source confidence: (0.87 + 0.92) / 2 = 0.895
    │   │   ├─> Source count bonus: 2 sources × 0.1 = +0.2
    │   │   ├─> Cross-reference bonus: has transcript + visual = +0.2
    │   │   └─> Temporal alignment: N/A (no timestamps) = +0.0
    │   │   
    │   │   Calculation:
    │   │   confidence = base × 0.5 + bonuses
    │   │   confidence = 0.895 × 0.5 + 0.2 + 0.2
    │   │   confidence = 0.4475 + 0.4 = 0.8475
    │   │   → Rounded: 0.85
    │   │
    │   └─> Create StepSourceData
    │       {
    │         "step_index": 1,
    │         "step_content": {...},
    │         "sources": [transcript_source, visual_source],
    │         "overall_confidence": 0.85,
    │         "has_transcript_support": true,
    │         "has_visual_support": true,
    │         "validation_flags": []
    │       }
    │
    ├─> STAGE 7: Validate Steps
    │   │
    │   For each step:
    │   ├─> Check confidence >= 0.7 ✓
    │   ├─> Check has_transcript_support ✓
    │   ├─> If confidence < 0.8: add warning "medium_confidence"
    │   └─> If no visual support: add info "no_visual_reference"
    │   
    │   Result: All 7 steps validated
    │
    ├─> STAGE 8: Generate Word Document
    │   │
    │   ├─> Initialize python-docx
    │   │   └─> doc = Document()
    │   │
    │   ├─> Add document metadata
    │   │   doc.core_properties.title = "Azure Portal Navigation Training"
    │   │   doc.core_properties.author = "ScriptToDoc AI"
    │   │   doc.core_properties.created = datetime.now()
    │   │
    │   ├─> Add title
    │   │   └─> doc.add_heading("Training Document: Azure Portal Navigation", level=0)
    │   │
    │   ├─> Add generation info
    │   │   └─> doc.add_paragraph(
    │   │         "Generated: 2025-11-03 | Confidence: 0.85 | Steps: 7",
    │   │         style='Subtitle'
    │   │       )
    │   │
    │   ├─> For each step:
    │   │   │
    │   │   ├─> Add step heading
    │   │   │   └─> doc.add_heading("Step 1: Access Azure Portal", level=1)
    │   │   │
    │   │   ├─> Add overview
    │   │   │   └─> p = doc.add_paragraph()
    │   │   │       p.add_run("Overview: ").bold = True
    │   │   │       p.add_run("Navigate to portal.azure.com...")
    │   │   │
    │   │   ├─> Add details
    │   │   │   └─> doc.add_paragraph("Open your web browser...")
    │   │   │
    │   │   ├─> Add actions (bulleted list)
    │   │   │   └─> for action in step["actions"]:
    │   │   │         doc.add_paragraph(action, style='List Bullet')
    │   │   │
    │   │   └─> Add confidence indicator
    │   │       └─> p = doc.add_paragraph()
    │   │           p.add_run("[Confidence: High | Sources: transcript (1), visual (screen_01.png)]")
    │   │           p.runs[0].font.size = Pt(9)
    │   │           p.runs[0].font.color.rgb = RGBColor(100, 100, 100)
    │   │
    │   ├─> Add page break
    │   │   └─> doc.add_page_break()
    │   │
    │   ├─> Add source references section
    │   │   │
    │   │   └─> doc.add_heading("Source References", level=1)
    │   │       
    │   │       For each step's sources:
    │   │       ├─> p = doc.add_paragraph()
    │   │       │   p.add_run(f"Step 1 - transcript (Sentence 0)").bold = True
    │   │       │
    │   │       └─> quote = doc.add_paragraph(
    │   │             '"First you need to open the Azure portal"',
    │   │             style='Intense Quote'
    │   │           )
    │   │
    │   └─> Save document
    │       └─> output_path = f"/tmp/{job_id}_training.docx"
    │           doc.save(output_path)
    │
    ├─> STAGE 9: Upload Document
    │   │
    │   └─> Upload to Blob Storage
    │       ├─> Container: documents
    │       ├─> Blob: {job_id}_training.docx
    │       ├─> Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
    │       │
    │       └─> Generate SAS URL (1-hour expiry)
    │           {
    │             "url": "https://stscripttodoc.blob.core.windows.net/documents/550e8400..._training.docx?sv=2021-06-08&se=2025-11-03T11:00:00Z&sp=r&sig=...",
    │             "expires_at": "2025-11-03T11:00:00Z"
    │           }
    │
    └─> STAGE 10: Complete Job
        │
        ├─> Update Cosmos DB
        │   └─> PATCH /jobs/550e8400...
        │       {
        │         "status": "completed",
        │         "progress": 1.0,
        │         "stage": "done",
        │         "completed_at": "2025-11-03T10:00:18Z",
        │         "result": {
        │           "document_url": "https://.../550e8400..._training.docx?sv=...",
        │           "document_expires_at": "2025-11-03T11:00:00Z",
        │           "step_count": 7,
        │           "average_confidence": 0.85,
        │           "processing_time_seconds": 18.3,
        │           "metrics": {
        │             "azure_di": {
        │               "calls": 3,  # 1 transcript + 2 screenshots
        │               "pages_analyzed": 3,
        │               "cost_usd": 0.03
        │             },
        │             "azure_openai": {
        │               "calls": 8,  # 1 summary + 7 step expansions
        │               "total_tokens": 3542,
        │               "input_tokens": 2100,
        │               "output_tokens": 1442,
        │               "cost_usd": 0.42
        │             },
        │             "total_cost_usd": 0.45
        │           }
        │         }
        │       }
        │
        ├─> Complete Service Bus message
        │   └─> receiver.complete_message(message)
        │
        └─> Delete temp files
            └─> Blob: temp/{job_id}/*

[4] CLIENT RETRIEVAL (Frontend)
    │
    ├─> Poll /status/{job_id} every 2 seconds
    │   │
    │   └─> When status === "completed":
    │       ├─> Display success UI
    │       ├─> Show metrics
    │       └─> Enable download button
    │
    ├─> User clicks "Download"
    │   │
    │   └─> GET /documents/{job_id}
    │       │
    │       Response:
    │       {
    │         "download_url": "https://...?sv=...",
    │         "expires_in": 3600,
    │         "filename": "training_document.docx",
    │         "size_bytes": 45600
    │       }
    │
    └─> Browser downloads file
        └─> User opens in Microsoft Word

[5] DATA RETENTION & CLEANUP
    │
    ├─> Immediate (after processing):
    │   └─> Delete temp blobs (temp/{job_id}/*)
    │
    ├─> 24 hours:
    │   └─> Cosmos DB: processing_cache expires (TTL)
    │
    ├─> 7 days:
    │   └─> Delete upload blobs (uploads/{job_id}/*)
    │
    ├─> 30 days:
    │   └─> Move documents to cool storage
    │
    └─> 90 days:
        ├─> Delete job records from Cosmos DB
        └─> Delete document blobs
```

---

## Data Schemas

### 1. Job Record (Cosmos DB)

```typescript
interface JobRecord {
  // Core fields
  id: string;                    // Partition key
  partitionKey: string;          // User ID for tenant isolation
  status: JobStatus;
  created_at: string;            // ISO 8601
  updated_at: string;            // ISO 8601
  completed_at?: string;
  
  // Input data
  input: {
    transcript_url: string;
    screenshot_urls?: string[];
    video_url?: string;
  };
  
  // Configuration
  config: {
    tone: "Professional" | "Casual" | "Neutral" | "Technical";
    audience: "General" | "Technical" | "Non-Technical" | "Expert";
    min_steps: number;
    target_steps: number;
    use_azure_di: boolean;
    use_openai: boolean;
  };
  
  // Processing state
  progress: number;              // 0.0 - 1.0
  stage: string;
  
  // Result
  result?: {
    document_url: string;
    document_expires_at: string;
    step_count: number;
    average_confidence: number;
    processing_time_seconds: number;
    metrics: JobMetrics;
  };
  
  // Error handling
  error?: {
    message: string;
    code: string;
    timestamp: string;
  };
}

enum JobStatus {
  QUEUED = "queued",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

interface JobMetrics {
  azure_di: {
    calls: number;
    pages_analyzed: number;
    cost_usd: number;
  };
  azure_openai: {
    calls: number;
    total_tokens: number;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
  };
  total_cost_usd: number;
}
```

### 2. Step Data Structure

```typescript
interface TrainingStep {
  step_index: number;
  title: string;
  summary: string;
  details: string;
  actions: string[];
  prerequisites?: string[];
  expected_result?: string;
}

interface SourceReference {
  type: "transcript" | "visual" | "timestamp";
  excerpt: string;
  timestamp?: string;          // "00:15:32"
  sentence_index?: number;
  screenshot_ref?: string;     // "screen_01.png"
  ui_elements?: string[];
  confidence: number;          // 0.0 - 1.0
}

interface StepSourceData {
  step_index: number;
  step_content: TrainingStep;
  sources: SourceReference[];
  overall_confidence: number;
  has_transcript_support: boolean;
  has_visual_support: boolean;
  validation_flags: string[];
}
```

### 3. Azure DI Response (Prebuilt-Read)

```typescript
interface AzureDocumentIntelligenceResult {
  status: "succeeded" | "running" | "failed";
  createdDateTime: string;
  lastUpdatedDateTime: string;
  analyzeResult: {
    apiVersion: string;
    modelId: "prebuilt-read" | "prebuilt-layout";
    contentFormat: "text" | "markdown";
    content: string;
    pages: Page[];
    paragraphs?: Paragraph[];
    tables?: Table[];
    styles?: Style[];
  };
}

interface Page {
  pageNumber: number;
  angle: number;
  width: number;
  height: number;
  unit: "pixel" | "inch";
  words: Word[];
  lines: Line[];
  spans: Span[];
}

interface Paragraph {
  role?: "title" | "sectionHeading" | "footnote" | "pageHeader" | "content";
  content: string;
  boundingRegions: BoundingRegion[];
  spans: Span[];
}

interface Span {
  offset: number;
  length: number;
}
```

### 4. Service Bus Message

```typescript
interface ServiceBusJobMessage {
  job_id: string;
  transcript_url: string;
  screenshot_urls?: string[];
  video_url?: string;
  config: JobConfig;
  user_id: string;
  priority?: number;           // 0-10, higher = more urgent
}

// Message properties
{
  MessageId: string;
  ContentType: "application/json";
  EnqueuedTime: Date;
  TimeToLive: Duration;        // 30 minutes
  ScheduledEnqueueTime?: Date; // For delayed processing
}
```

---

## State Transitions

```
┌─────────┐
│ QUEUED  │
└────┬────┘
     │ Worker picks up message
     ▼
┌────────────┐     ┌─────────┐
│ PROCESSING ├────>│ FAILED  │
└─────┬──────┘     └─────────┘
      │ All stages complete
      ▼
┌───────────┐
│ COMPLETED │
└───────────┘

State Rules:
- QUEUED → PROCESSING: When worker starts processing
- PROCESSING → COMPLETED: When document uploaded successfully
- PROCESSING → FAILED: On unrecoverable error
- FAILED → QUEUED: Manual retry (admin action)
- No transition from COMPLETED
```

---

## Storage Patterns

### Blob Storage Layout

```
stscripttodoc (Storage Account)
├── uploads/ (Container - Private)
│   └── {job_id}/
│       ├── transcript.txt
│       ├── screenshots/
│       │   ├── screen_01.png
│       │   └── screen_02.png
│       └── video.mp4
│
├── documents/ (Container - Private with SAS)
│   └── {job_id}_training.docx
│
└── temp/ (Container - Lifecycle: 24h auto-delete)
    └── {job_id}/
        ├── cleaned_transcript.txt
        ├── frames/
        │   ├── frame_001.png
        │   └── frame_002.png
        └── audio.wav
```

**Lifecycle Policies:**
```json
{
  "rules": [
    {
      "name": "delete-temp-files",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["temp/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 1
            }
          }
        }
      }
    },
    {
      "name": "move-documents-to-cool",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["documents/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            }
          }
        }
      }
    }
  ]
}
```

### Cosmos DB Indexing

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/status/?",
      "indexes": [
        {"kind": "Range", "dataType": "String"}
      ]
    },
    {
      "path": "/created_at/?",
      "indexes": [
        {"kind": "Range", "dataType": "String"}
      ]
    },
    {
      "path": "/partitionKey/?",
      "indexes": [
        {"kind": "Hash", "dataType": "String"}
      ]
    }
  ],
  "excludedPaths": [
    {
      "path": "/result/metrics/*"
    }
  ]
}
```

**Query Performance:**
```sql
-- Get user's jobs (uses partition key)
SELECT * FROM c WHERE c.partitionKey = 'user_12345'

-- Get active jobs (uses status index)
SELECT * FROM c WHERE c.status = 'processing'

-- Get recent jobs (uses created_at index)
SELECT * FROM c WHERE c.created_at > '2025-11-01T00:00:00Z'
ORDER BY c.created_at DESC
```

---

## Integration Data Flow

### Azure Document Intelligence

```
Backend → Azure DI

1. Upload document to blob (if not already)
2. POST /documentModels/{modelId}:analyze
   Headers:
     Content-Type: application/json
     Ocp-Apim-Subscription-Key: {key}
   Body:
     { "urlSource": "https://.../document.txt" }

3. Response: 202 Accepted
   Headers:
     Operation-Location: https://.../analyzeResults/{resultId}

4. Poll Operation-Location (every 1 second)
   GET /analyzeResults/{resultId}
   
5. Response: 200 OK (when complete)
   Body: { analyzeResult: {...} }

6. Cache result in Cosmos DB (24h TTL)
```

### Azure OpenAI Service

```
Backend → Azure OpenAI

1. POST /openai/deployments/{deployment}/chat/completions
   Headers:
     Content-Type: application/json
     api-key: {key}
   Body:
     {
       "messages": [...],
       "temperature": 0.2,
       "max_tokens": 1000,
       "response_format": { "type": "json_object" }  # For structured output
     }

2. Response: 200 OK (streaming or complete)
   Body:
     {
       "choices": [{
         "message": {
           "role": "assistant",
           "content": "..."
         }
       }],
       "usage": {
         "prompt_tokens": 450,
         "completion_tokens": 180,
         "total_tokens": 630
       }
     }

3. Track token usage in job metrics
```

---

## Error Handling & Retries

### Retry Strategies

```typescript
// Exponential backoff
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      const delay = baseDelay * Math.pow(2, i);
      await sleep(delay);
    }
  }
}

// Usage
const result = await retryWithBackoff(
  () => azureOpenAI.summarize(transcript),
  3,
  2000
);
```

### Service Bus Dead Letter Queue

```
Normal Queue: scripttodoc-jobs
├─> Max delivery count: 5
└─> On 5th failure → Move to Dead Letter Queue

Dead Letter Queue: scripttodoc-jobs/$DeadLetterQueue
├─> Manual inspection
├─> Identify pattern (e.g., all jobs with video > 100MB)
└─> Fix issue and requeue
```

### Graceful Degradation

```typescript
async function processWithFallback(job: JobRecord) {
  let azureDiResult;
  
  // Try Azure DI
  try {
    azureDiResult = await azureDocumentIntelligence.analyze(job.transcript_url);
  } catch (error) {
    logger.warn("Azure DI unavailable, using fallback", { job_id: job.id });
    azureDiResult = null;
  }
  
  // Generate steps
  if (azureDiResult && job.config.use_openai) {
    // Best quality: Azure DI + OpenAI
    return generateStepsWithAzureDIAndOpenAI(azureDiResult, job);
  } else if (job.config.use_openai) {
    // Good quality: OpenAI only
    return generateStepsWithOpenAI(job);
  } else {
    // Basic quality: NLTK fallback
    return generateStepsWithNLTK(job);
  }
}
```

---

## Performance Optimization

### Caching Strategy

```typescript
// 1. Cosmos DB cache (for Azure DI results)
async function getOrAnalyzeDocument(url: string): Promise<AnalyzeResult> {
  const cacheKey = `azure_di_${hash(url)}`;
  
  // Try cache first
  const cached = await cosmosDB.readItem("processing_cache", cacheKey);
  if (cached) return cached.result;
  
  // Analyze and cache
  const result = await azureDocumentIntelligence.analyze(url);
  await cosmosDB.createItem("processing_cache", {
    id: cacheKey,
    result,
    ttl: 86400  // 24 hours
  });
  
  return result;
}

// 2. In-memory cache (for sentence catalog within job)
const sentenceCatalogCache = new Map<string, string[]>();

function getSentenceCatalog(transcript: string): string[] {
  if (sentenceCatalogCache.has(transcript)) {
    return sentenceCatalogCache.get(transcript)!;
  }
  
  const sentences = tokenizer.tokenize(transcript);
  sentenceCatalogCache.set(transcript, sentences);
  return sentences;
}
```

### Parallel Processing

```typescript
// Process screenshots in parallel
const screenshotResults = await Promise.all(
  job.input.screenshot_urls.map(url => 
    azureDocumentIntelligence.analyzeLayout(url)
  )
);

// Generate steps in parallel (if independent)
const steps = await Promise.all(
  summaries.map((summary, index) =>
    generateStep(summary, index, transcript, screenshotResults)
  )
);
```

---

**Next:** Review data flow and provide feedback on architecture decisions.

