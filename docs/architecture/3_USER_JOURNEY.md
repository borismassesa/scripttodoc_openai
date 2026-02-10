# ScriptToDoc - User Journey Flows

## Overview

This document details the user experience for all three MVP scenarios, from user action to final deliverable. Each journey includes the frontend experience, backend processing, and error handling.

---

## Journey 1: Basic - Transcript to Document

### User Story
*"As a training coordinator, I have a meeting transcript where we discussed a new process. I want to convert this into a professional training document so I can share it with my team."*

### Prerequisites
- User has meeting transcript saved as `.txt` file
- User has access to ScriptToDoc application
- User is authenticated via Azure AD

---

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ACTIONS                             │
└─────────────────────────────────────────────────────────────────┘

Step 1: Access Application
   │
   ├─> Navigate to https://scripttodoc.azurewebsites.net
   ├─> Azure AD login prompt appears
   └─> Sign in with company credentials (SSO)
   
   ✓ Success: Redirected to main dashboard
   ✗ Error: Invalid credentials → Show error message

Step 2: Upload Transcript
   │
   ├─> Click "Upload Transcript" or drag file to upload area
   ├─> Select transcript.txt from file system
   └─> File preview shows (filename, size, first 200 chars)
   
   Frontend Validation:
   ├─> Check file extension (.txt only)
   ├─> Check file size (< 5 MB)
   └─> Show error if validation fails
   
   ✓ Success: File staged for upload
   ✗ Error: "Only .txt files under 5MB accepted"

Step 3: Configure Options
   │
   ├─> Tone: [Professional ▼] (dropdown)
   ├─> Audience: [Technical Users ▼] (dropdown)
   ├─> Min Steps: [3] (slider)
   └─> Target Steps: [8] (slider)
   
   Optional: Expand "Advanced Settings"
   ├─> Use Azure DI: [✓] (toggle, default ON)
   └─> Use OpenAI Enhancement: [✓] (toggle, default ON)

Step 4: Start Processing
   │
   ├─> Click "Generate Training Document"
   ├─> Upload progress bar (0-100%)
   └─> Transition to processing view

Step 5: Monitor Progress
   │
   └─> Real-time progress display:
   
   ┌─────────────────────────────────────────┐
   │  Processing Your Document               │
   │                                         │
   │  ████████████░░░░░░░░░ 60%             │
   │                                         │
   │  Current Stage: Azure DI Analysis      │
   │                                         │
   │  ✓ Upload Complete                      │
   │  ✓ Transcript Cleaned                   │
   │  ⏳ Analyzing Structure                 │
   │  ○ Generating Steps                     │
   │  ○ Creating Document                    │
   │                                         │
   │  Estimated time: 15 seconds             │
   └─────────────────────────────────────────┘
   
   Backend polls /status/{job_id} every 2 seconds

Step 6: View Results
   │
   └─> Processing Complete! → Show preview
   
   ┌─────────────────────────────────────────┐
   │  ✓ Document Ready!                      │
   │                                         │
   │  Generated 7 Steps                      │
   │  Average Confidence: 0.82 (High)        │
   │  Processing Time: 18 seconds            │
   │                                         │
   │  [Download Word Document]               │
   │  [Edit Plan] [Start New]                │
   └─────────────────────────────────────────┘
   
   Preview shows:
   ├─> Step cards with titles and summaries
   ├─> Confidence indicators per step
   └─> Source reference counts

Step 7: Download Document
   │
   ├─> Click "Download Word Document"
   ├─> Browser downloads: transcript_training.docx
   └─> Open in Microsoft Word

Step 8: Review Document (in Word)
   │
   └─> Document contains:
       ├─> Title: "Training Document: [Extracted Topic]"
       ├─> Step 1-7 with details
       ├─> Each step has:
       │   ├─> Title
       │   ├─> Overview paragraph
       │   ├─> Key Actions (bullets)
       │   └─> [Confidence: High | Sources: transcript (5 refs)]
       └─> Appendix: Source References
           └─> Full transcript excerpts for each step
```

---

### Backend Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND PROCESSING                          │
└─────────────────────────────────────────────────────────────────┘

[API POST /process]
   │
   ├─> Validate file (extension, size)
   ├─> Generate job_id: "550e8400-e29b-41d4-a716-446655440000"
   ├─> Upload file to Azure Blob Storage
   │   └─> uploads/550e8400.../transcript.txt
   │
   ├─> Create job record in Cosmos DB:
   │   {
   │     "id": "550e8400...",
   │     "status": "queued",
   │     "progress": 0.0,
   │     "stage": "pending",
   │     "config": {...}
   │   }
   │
   └─> Send message to Service Bus Queue
       └─> scripttodoc-jobs

[Background Worker receives message]
   │
   ├─> Update job: status="processing", progress=0.05, stage="load_transcript"
   ├─> Download transcript from Blob Storage
   │
   ├─> Stage 1: Clean Transcript (progress=0.15)
   │   ├─> Remove timestamps: [00:15:32] → ""
   │   ├─> Remove speaker labels: "Speaker 1:" → ""
   │   ├─> Remove filler words: "um, uh, like" → ""
   │   └─> Normalize whitespace
   │   
   │   Input:
   │   "[00:15:32] Speaker 1: Um, so like, first you need to, 
   │    you know, open the Azure portal..."
   │   
   │   Output:
   │   "First you need to open the Azure portal..."
   │
   ├─> Stage 2: Azure DI Analysis (progress=0.25)
   │   ├─> Upload cleaned text to temp blob
   │   ├─> Call Azure Document Intelligence (prebuilt-read)
   │   │   POST https://{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze
   │   ├─> Extract structure:
   │   │   {
   │   │     "content": "cleaned text",
   │   │     "paragraphs": [
   │   │       {"content": "First you need...", "role": "title"},
   │   │       {"content": "Then navigate...", "role": "content"}
   │   │     ]
   │   │   }
   │   └─> Identify process structure:
   │       {
   │         "steps": ["open portal", "navigate", "create resource"],
   │         "decisions": ["if no permissions → contact admin"],
   │         "sequence": [1, 2, 3, ...]
   │       }
   │
   ├─> Stage 3: Build Source Catalog (progress=0.35)
   │   ├─> Tokenize into sentences
   │   ├─> Create sentence catalog:
   │   │   [
   │   │     {"index": 0, "text": "First you need to open the Azure portal."},
   │   │     {"index": 1, "text": "Then navigate to the resource groups."},
   │   │     ...
   │   │   ]
   │   └─> Store in memory for source lookups
   │
   ├─> Stage 4: Summarize with OpenAI (progress=0.45)
   │   ├─> Call Azure OpenAI (gpt-4o-mini)
   │   │   POST https://{endpoint}/openai/deployments/gpt-4o-mini/chat/completions
   │   ├─> Prompt:
   │   │   "Summarize this transcript into 8 key actionable sentences.
   │   │    Focus on process steps.
   │   │    Tone: Professional
   │   │    Audience: Technical Users"
   │   │
   │   └─> Response:
   │       [
   │         "Access the Azure portal using your credentials.",
   │         "Navigate to the Resource Groups section.",
   │         ...
   │       ]
   │
   ├─> Stage 5: Generate Steps (progress=0.60)
   │   ├─> For each summary sentence:
   │   │   ├─> Expand into full step with OpenAI
   │   │   │   {
   │   │   │     "title": "Step 1: Access Azure Portal",
   │   │   │     "summary": "Navigate to portal.azure.com and sign in",
   │   │   │     "details": "Open your web browser and navigate to...",
   │   │   │     "actions": [
   │   │   │       "Open web browser",
   │   │   │       "Navigate to portal.azure.com",
   │   │   │       "Enter credentials"
   │   │   │     ]
   │   │   │   }
   │   │   │
   │   │   ├─> Find source references:
   │   │   │   └─> Search sentence catalog for matching content
   │   │   │       └─> Found: sentence 3, 5, 7
   │   │   │       └─> Create SourceReference objects:
   │   │   │           [
   │   │   │             {
   │   │   │               "type": "transcript",
   │   │   │               "excerpt": "First you need to open the Azure portal",
   │   │   │               "sentence_index": 3,
   │   │   │               "confidence": 0.9
   │   │   │             },
   │   │   │             ...
   │   │   │           ]
   │   │   │
   │   │   └─> Calculate confidence:
   │   │       ├─> Base: Average of source confidences = 0.9
   │   │       ├─> Source count bonus: 3 sources * 0.1 = +0.3 (capped at +0.3)
   │   │       └─> Final: min(0.9 + 0.3, 1.0) = 1.0 → clip to 0.95
   │   │
   │   └─> Result: 7 steps with sources
   │
   ├─> Stage 6: Validate Quality (progress=0.70)
   │   ├─> For each step:
   │   │   ├─> Check confidence >= 0.7 ✓
   │   │   ├─> Check has_transcript_support ✓
   │   │   └─> If low confidence: add warning flag
   │   │
   │   └─> All steps validated
   │
   ├─> Stage 7: Create Document (progress=0.80)
   │   ├─> Initialize python-docx Document
   │   ├─> Add title: "Training Document: Azure Resource Management"
   │   ├─> For each step:
   │   │   ├─> Add heading: "Step 1: Access Azure Portal"
   │   │   ├─> Add overview paragraph
   │   │   ├─> Add details paragraph
   │   │   ├─> Add "Key Actions:" with bullets
   │   │   └─> Add confidence indicator:
   │   │       "[Confidence: High | Sources: transcript (3 refs)]"
   │   │
   │   ├─> Add page break
   │   ├─> Add "Source References" section
   │   ├─> For each step's sources:
   │   │   └─> Add quoted excerpt with reference number
   │   │
   │   └─> Save to temp file
   │
   ├─> Stage 8: Upload Document (progress=0.90)
   │   ├─> Upload .docx to Blob Storage
   │   │   └─> documents/550e8400..._training.docx
   │   └─> Generate SAS URL (1-hour expiry)
   │
   └─> Stage 9: Complete (progress=1.0)
       ├─> Update job in Cosmos DB:
       │   {
       │     "status": "completed",
       │     "progress": 1.0,
       │     "stage": "done",
       │     "result": {
       │       "document_url": "https://...sas_token",
       │       "step_count": 7,
       │       "average_confidence": 0.82,
       │       "processing_time_seconds": 18,
       │       "metrics": {
       │         "azure_di_calls": 1,
       │         "openai_calls": 9,
       │         "total_tokens": 3500,
       │         "estimated_cost_usd": 0.45
       │       }
       │     }
       │   }
       │
       └─> Job complete! Frontend will fetch on next poll.
```

---

### Error Handling

#### Upload Errors
```
Error: File too large (6 MB > 5 MB limit)
└─> Display: "File exceeds 5 MB limit. Please use a smaller file."
    Action: Clear upload, allow retry

Error: Invalid file type (.pdf)
└─> Display: "Only .txt files are accepted."
    Action: Show supported formats, allow retry

Error: Network timeout during upload
└─> Display: "Upload failed. Check your connection and try again."
    Action: Retry button
```

#### Processing Errors
```
Error: Azure DI service unavailable
├─> Backend fallback: Use NLTK-only processing (no Azure DI)
├─> Update job: "processing" with warning flag
└─> Display: "Processing with limited features (Azure DI unavailable)"

Error: OpenAI rate limit exceeded
├─> Backend: Retry with exponential backoff (3 attempts)
├─> If still failing: Use NLTK summarization (fallback)
└─> Display: "Processing complete (basic mode)"

Error: Job timeout (> 5 minutes)
├─> Backend: Move message to dead-letter queue
├─> Update job: status="failed", error="Processing timeout"
└─> Display: "Processing failed. Please try again or contact support."
    Action: [Retry] [Contact Support]
```

---

## Journey 2: Enhanced - Transcript + Screenshots

### User Story
*"As a training coordinator, I have a meeting transcript and several screenshots of the software UI we discussed. I want to generate a training document that references specific UI elements visible in the screenshots."*

### Flow Differences from Journey 1

```
Step 2: Upload Files (ENHANCED)
   │
   ├─> Upload transcript.txt (same as Journey 1)
   │
   ├─> Click "Add Screenshots" (optional)
   │   ├─> Multi-select screenshots:
   │   │   ├─> screenshot_01.png
   │   │   ├─> screenshot_02.png
   │   │   └─> screenshot_03.png
   │   │
   │   └─> Preview thumbnails show:
   │       ├─> Filename
   │       ├─> Resolution
   │       └─> [X] Remove button
   │
   └─> Validation:
       ├─> Max 10 screenshots
       ├─> Max 2 MB per image
       └─> Formats: PNG, JPEG, JPG

Backend Processing: NEW STAGES

├─> Stage 2.5: Analyze Screenshots (progress=0.30)
│   │
│   ├─> For each screenshot:
│   │   ├─> Call Azure DI (prebuilt-layout model)
│   │   │   POST .../documentModels/prebuilt-layout:analyze
│   │   │
│   │   ├─> Extract:
│   │   │   {
│   │   │     "content": "All OCR text from image",
│   │   │     "pages": [{
│   │   │       "lines": [{"content": "Create", "polygon": [...]}],
│   │   │       "words": [...],
│   │   │       "spans": [...]
│   │   │     }]
│   │   │   }
│   │   │
│   │   └─> Identify UI elements:
│   │       [
│   │         {"type": "button", "text": "Create", "location": [x, y]},
│   │         {"type": "menu", "text": "File", "location": [x, y]},
│   │         {"type": "textbox", "text": "Resource name", "location": [x, y]}
│   │       ]
│   │
│   └─> Store screenshot analysis results
│
├─> Stage 5: Generate Steps (ENHANCED - progress=0.60)
│   │
│   └─> For each step:
│       ├─> Generate step content (same as Journey 1)
│       │
│       ├─> Find transcript sources (same as Journey 1)
│       │
│       ├─> NEW: Find visual sources
│       │   ├─> Extract action phrases from step:
│       │   │   "Click the Create button"
│       │   │   → verb: "click", target: "create button"
│       │   │
│       │   ├─> Search screenshot UI elements:
│       │   │   └─> Match "create button" with:
│       │   │       screenshot_02.png: button "Create" ✓ (similarity: 0.85)
│       │   │
│       │   └─> Create SourceReference:
│       │       {
│       │         "type": "visual",
│       │         "excerpt": "Screenshot showing Create button in resource menu",
│       │         "screenshot_ref": "screenshot_02.png",
│       │         "ui_elements": ["Create"],
│       │         "confidence": 0.85
│       │       }
│       │
│       └─> Calculate enhanced confidence:
│           ├─> Transcript sources: 3 refs, avg confidence 0.9
│           ├─> Visual sources: 1 ref, confidence 0.85
│           ├─> Source count bonus: 4 * 0.1 = +0.4 (capped at +0.3)
│           ├─> Cross-reference bonus: +0.2 (has both transcript + visual)
│           └─> Final: (0.9 + 0.85) / 2 + 0.3 + 0.2 = 0.875 + 0.5 = 1.0 → 0.95
│
└─> Stage 7: Create Document (ENHANCED)
    │
    └─> For each step:
        ├─> Add confidence indicator:
        │   "[Confidence: High | Sources: transcript (3), visual (screenshot_02.png)]"
        │
        └─> In appendix, add visual sources:
            "Step 2 - visual (screenshot_02.png)
             Screenshot showing Create button in the resource group menu"
```

### User Experience Differences

**Preview Display (Enhanced):**
```
┌─────────────────────────────────────────┐
│  Step 2: Create Resource Group          │
│                                         │
│  Overview: Access the resource creation │
│  menu and initiate a new group.         │
│                                         │
│  Key Actions:                           │
│  • Click "Create" button                │
│  • Select "Resource Group"              │
│                                         │
│  📷 Visual Reference: screenshot_02.png │
│                                         │
│  [Confidence: Very High (0.95)]         │
│  Sources: 3 transcript, 1 visual        │
└─────────────────────────────────────────┘
```

**Downloaded Document:**
- Steps now reference screenshots by filename
- Visual sources shown in confidence line
- Appendix includes visual source excerpts
- Higher overall confidence scores

---

## Journey 3: Advanced - Video Processing

### User Story
*"As a training coordinator, I recorded a 10-minute training session showing our software. I want to upload this video and automatically generate a training document with extracted frames as visual references."*

### Flow Diagram

```
Step 2: Upload Video (NEW)
   │
   ├─> Click "Upload Video" tab
   ├─> Select training_session.mp4 from file system
   │
   ├─> File preview shows:
   │   ├─> Filename: training_session.mp4
   │   ├─> Duration: 10:32
   │   ├─> Size: 45 MB
   │   └─> Resolution: 1920x1080
   │
   └─> Validation:
       ├─> Max 500 MB
       ├─> Max 30 minutes duration
       └─> Formats: MP4, MOV, AVI

Step 3: Configure Video Options (NEW)
   │
   ├─> Frame extraction interval: [30 seconds ▼]
   │   Options: 15s, 30s, 60s, Auto (scene detection)
   │
   ├─> Generate transcript: [✓] (toggle, default ON)
   │   └─> Transcription language: [English (US) ▼]
   │
   └─> Standard options (tone, audience, steps)

Step 4: Start Processing
   │
   └─> Extended progress tracking:
   
   ┌─────────────────────────────────────────┐
   │  Processing Video                       │
   │                                         │
   │  ████████░░░░░░░░░░ 40%                │
   │                                         │
   │  Current Stage: Extracting Audio       │
   │                                         │
   │  ✓ Upload Complete                      │
   │  ✓ Video Analyzed                       │
   │  ⏳ Extracting Audio                    │
   │  ○ Generating Transcript                │
   │  ○ Extracting Key Frames                │
   │  ○ Analyzing Frames                     │
   │  ○ Generating Steps                     │
   │  ○ Creating Document                    │
   │                                         │
   │  Estimated time: 2 minutes              │
   └─────────────────────────────────────────┘
```

### Backend Processing (Video-Specific Stages)

```
[Background Worker receives video job]
   │
   ├─> Stage 1: Upload & Validate (progress=0.05)
   │   ├─> Video uploaded to: uploads/{job_id}/training_session.mp4
   │   ├─> Check codec, duration, resolution
   │   └─> Extract metadata
   │
   ├─> Stage 2: Extract Audio (progress=0.15)
   │   ├─> Use FFmpeg to extract audio track:
   │   │   ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav
   │   │
   │   └─> Upload audio to: temp/{job_id}/audio.wav
   │
   ├─> Stage 3: Generate Transcript (progress=0.25)
   │   ├─> Call Azure Speech-to-Text:
   │   │   POST https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1
   │   │
   │   ├─> Configuration:
   │   │   {
   │   │     "language": "en-US",
   │   │     "format": "detailed",
   │   │     "profanityOption": "Masked",
   │   │     "enableWordTimeOffsets": true
   │   │   }
   │   │
   │   └─> Result (with timestamps):
   │       [00:00:05] Hello, today we'll learn about Azure resources.
   │       [00:00:15] First, let's open the Azure portal.
   │       [00:00:32] Navigate to the resource groups section.
   │       ...
   │
   ├─> Stage 4: Extract Key Frames (progress=0.40)
   │   ├─> Strategy: Scene change detection
   │   │   ├─> Use Azure Computer Vision Video Analysis
   │   │   │   OR
   │   │   ├─> Use OpenCV with histogram comparison
   │   │   │   └─> Compare consecutive frames
   │   │   │       └─> If difference > threshold: key frame
   │   │   │
   │   │   └─> Fallback: Extract frame every 30 seconds
   │   │
   │   ├─> Extract frames:
   │   │   [
   │   │     {"time": "00:00:15", "frame": frame_001.png},
   │   │     {"time": "00:00:45", "frame": frame_002.png},
   │   │     {"time": "00:01:30", "frame": frame_003.png},
   │   │     ...
   │   │   ]
   │   │   Total: 21 frames extracted
   │   │
   │   └─> Upload frames to: uploads/{job_id}/frames/
   │
   ├─> Stage 5: Analyze Frames (progress=0.55)
   │   ├─> For each frame:
   │   │   ├─> Call Azure DI (prebuilt-layout)
   │   │   │   └─> Extract UI elements, text, layout
   │   │   │
   │   │   └─> Link to transcript timestamp:
   │   │       frame_001.png (00:00:15) →
   │   │       transcript: "First, let's open the Azure portal." (00:00:15)
   │   │
   │   └─> Store frame analysis with temporal alignment
   │
   ├─> Continue with standard pipeline...
   │   ├─> Clean transcript (same as Journey 1)
   │   ├─> Generate steps (same as Journey 2, with video frames as screenshots)
   │   └─> Create document
   │
   └─> Stage 9: Complete (progress=1.0)
       └─> Result includes:
           ├─> Generated document
           ├─> Transcript file (downloadable separately)
           ├─> Extracted frames (zip file)
           └─> Metrics:
               {
                 "video_duration_seconds": 632,
                 "transcript_word_count": 1547,
                 "frames_extracted": 21,
                 "frames_analyzed": 21,
                 "steps_generated": 12,
                 "average_confidence": 0.87,
                 "processing_time_seconds": 125,
                 "costs": {
                   "speech_to_text": "$0.32",
                   "document_intelligence": "$0.21",
                   "openai": "$0.67",
                   "total": "$1.20"
                 }
               }
```

### Enhanced Document Output

**Video-Generated Document Features:**
```
TRAINING DOCUMENT: Azure Resource Management
(Generated from training_session.mp4)

Table of Contents
├─> Quick Reference
├─> Step-by-Step Instructions (12 steps)
└─> Appendix
    ├─> Full Transcript with Timestamps
    ├─> Visual References (21 frames)
    └─> Source Citations

Step 1: Access the Azure Portal [00:00:15]
Overview: Navigate to portal.azure.com and authenticate

[Video timestamp: 00:00:15]
[Visual reference: frame_001.png]
[Confidence: Very High | Sources: transcript (00:00:15), visual (frame_001.png)]

Key Actions:
  • Open web browser
  • Navigate to portal.azure.com
  • Enter credentials and authenticate

APPENDIX

Full Transcript:
[00:00:05] Hello, today we'll learn about Azure resources.
[00:00:15] First, let's open the Azure portal.
...

Visual References:
Frame 1 (00:00:15) - frame_001.png
Screenshot showing Azure portal login page with sign-in button

Frame 2 (00:00:45) - frame_002.png
Screenshot showing resource groups menu in Azure portal
```

---

## Cross-Journey Comparison

| Feature | Journey 1<br>(Basic) | Journey 2<br>(+Screenshots) | Journey 3<br>(Video) |
|---------|---------------------|---------------------------|---------------------|
| **Input** | Transcript .txt | Transcript + PNG/JPG | Video file (MP4) |
| **Processing Time** | 15-20 sec | 25-35 sec | 90-120 sec |
| **Azure Services** | DI (read), OpenAI | DI (read+layout), OpenAI | Speech, CV, DI, OpenAI |
| **Output Steps** | 5-8 steps | 5-8 steps | 8-15 steps |
| **Confidence** | 0.75-0.85 | 0.80-0.90 | 0.85-0.95 |
| **Source Types** | Transcript only | Transcript + Visual | Transcript + Visual + Temporal |
| **Cost per Job** | $0.30-0.50 | $0.50-0.80 | $1.00-1.50 |
| **Complexity** | Low | Medium | High |
| **Use Case** | Quick documentation | UI-heavy training | Full video tutorials |

---

## Common UX Patterns

### Loading States
```
Empty State (No file uploaded):
┌─────────────────────────────────────────┐
│           📄                            │
│                                         │
│    Drag and drop your transcript       │
│    or click to browse                   │
│                                         │
│    Supported: .txt files (max 5 MB)    │
└─────────────────────────────────────────┘

File Selected:
┌─────────────────────────────────────────┐
│  ✓ transcript.txt (245 KB)              │
│                                         │
│  "First, open the Azure portal. Then   │
│   navigate to the resource groups..."   │
│                                         │
│  [✕ Remove] [Process Document]          │
└─────────────────────────────────────────┘

Processing:
┌─────────────────────────────────────────┐
│  ⏳ Processing (45%)                     │
│  Current: Generating steps              │
│  Time remaining: ~10 seconds            │
└─────────────────────────────────────────┘

Complete:
┌─────────────────────────────────────────┐
│  ✓ Ready to Download                    │
│  7 steps generated                      │
│  Avg. confidence: 0.82                  │
│  [Download .docx]                       │
└─────────────────────────────────────────┘
```

### Error Recovery
```
Recoverable Error:
┌─────────────────────────────────────────┐
│  ⚠️ Processing Warning                   │
│                                         │
│  Azure DI temporarily unavailable.      │
│  Using fallback processing (NLTK).      │
│                                         │
│  Quality may be slightly reduced.       │
│                                         │
│  [Continue Anyway] [Cancel]             │
└─────────────────────────────────────────┘

Fatal Error:
┌─────────────────────────────────────────┐
│  ❌ Processing Failed                    │
│                                         │
│  Unable to process video file.          │
│  Error: Unsupported codec (VP9)         │
│                                         │
│  Please use H.264 encoded video.        │
│                                         │
│  [Try Again] [Contact Support]          │
└─────────────────────────────────────────┘
```

---

## Accessibility Considerations

### WCAG 2.1 AA Compliance

**Keyboard Navigation:**
- All interactions accessible via keyboard
- Tab order: Upload → Configure → Process → Download
- Enter/Space to activate buttons
- Escape to close modals

**Screen Reader Support:**
- `aria-label` on all interactive elements
- `role="status"` for progress updates
- `aria-live="polite"` for status changes
- Alt text for all visual indicators

**Visual:**
- Color contrast ratio ≥ 4.5:1
- Focus indicators on all interactive elements
- Text size adjustable (responsive typography)
- No reliance on color alone for status

---

## Mobile Experience

### Responsive Breakpoints
```
Desktop (≥1024px):
├─> Two-column layout
├─> Side-by-side upload and preview
└─> Full metrics panel

Tablet (768px - 1023px):
├─> Single column with collapsible sections
├─> Stacked upload and preview
└─> Condensed metrics

Mobile (≤767px):
├─> Full-width components
├─> Progressive disclosure (accordion)
├─> Simplified progress indicator
└─> Bottom sheet for actions
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to Interactive** | < 2 seconds | Lighthouse |
| **Upload Start** | < 500ms | Time to first byte |
| **Progress Poll** | Every 2 seconds | Network timing |
| **Document Download** | < 3 seconds | File transfer time |
| **Error Recovery** | < 1 second | Error → retry ready |

---

**Next:** Review user flows and provide feedback on UX decisions.

