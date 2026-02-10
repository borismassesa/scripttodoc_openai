# ScriptToDoc - Implementation Phases & Roadmap

## Overview

This document breaks down the implementation into manageable phases, from foundation to production-ready MVP. Each phase builds on the previous one with clear deliverables and success criteria.

---

## Phase 0: Foundation & Azure Setup (Week 1)

### Goal
Set up Azure infrastructure and development environment.

### Tasks

#### 1. Azure Resource Provisioning
```
Resource Group: rg-scripttodoc-dev

Resources to create:
├── Azure Container Registry (for Docker images)
├── Azure Container Apps Environment
├── Azure Storage Account
│   ├── Container: uploads (private)
│   ├── Container: documents (private)
│   └── Container: temp (lifecycle: 24h)
├── Azure Cosmos DB (serverless, NoSQL)
│   ├── Database: scripttodoc
│   ├── Container: jobs (partition key: /userId)
│   └── Container: processing_cache (TTL: 24h)
├── Azure Service Bus Namespace
│   ├── Queue: scripttodoc-jobs
│   └── Queue: scripttodoc-jobs-deadletter
├── Azure Key Vault
├── Azure Document Intelligence resource
├── Azure OpenAI Service
│   ├── Deployment: gpt-4o-mini
│   └── Deployment: gpt-4o
└── Application Insights
```

**Infrastructure as Code (Bicep):**
```bicep
// main.bicep
param location string = 'eastus'
param environment string = 'dev'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stscripttodoc${environment}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// ... more resources
```

#### 2. Development Environment Setup

**Local Development:**
```bash
# Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Azure CLI
- VS Code with Azure extensions

# Clone repo
git clone https://github.com/yourorg/scripttodoc.git
cd scripttodoc

# Backend setup
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd transcript-trainer-ui
npm install

# Azure login
az login
az account set --subscription "Your Subscription"
```

**Environment Configuration:**
```bash
# .env.development
AZURE_SUBSCRIPTION_ID=xxx
AZURE_RESOURCE_GROUP=rg-scripttodoc-dev
AZURE_STORAGE_ACCOUNT=stscripttodocdev
AZURE_COSMOS_DB_ENDPOINT=https://cosmos-scripttodoc-dev.documents.azure.com
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://...
AZURE_OPENAI_ENDPOINT=https://scripttodoc-openai.openai.azure.com/
AZURE_SERVICE_BUS_NAMESPACE=scripttodoc-sb-dev

# Development mode (use Key Vault secrets locally)
AZURE_KEY_VAULT_NAME=kv-scripttodoc-dev
```

#### 3. Repository Structure

```
scripttodoc/
├── .github/
│   └── workflows/
│       ├── deploy-backend.yml
│       └── deploy-frontend.yml
│
├── backend/
│   ├── script_to_doc/          # Core Python package
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── azure_di.py
│   │   ├── azure_openai_client.py
│   │   ├── source_reference.py
│   │   ├── process_flow.py
│   │   └── jobs.py
│   │
│   ├── api/                    # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app
│   │   ├── routes/
│   │   │   ├── process.py
│   │   │   ├── status.py
│   │   │   └── documents.py
│   │   ├── dependencies.py     # Auth, DB connections
│   │   └── models.py          # Pydantic models
│   │
│   ├── workers/                # Background job processors
│   │   ├── __init__.py
│   │   └── processor.py
│   │
│   ├── tests/
│   │   ├── test_pipeline.py
│   │   ├── test_azure_di.py
│   │   └── test_api.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   └── transcript-trainer-ui/
│       ├── pages/
│       ├── components/
│       ├── lib/
│       ├── styles/
│       └── package.json
│
├── infrastructure/             # IaC
│   ├── bicep/
│   │   ├── main.bicep
│   │   ├── storage.bicep
│   │   ├── cosmos.bicep
│   │   └── container-apps.bicep
│   └── terraform/             # Alternative to Bicep
│
├── docs/
│   ├── 1_SYSTEM_ARCHITECTURE.md
│   ├── 2_IMPLEMENTATION_PHASES.md
│   ├── 3_USER_JOURNEY.md
│   ├── 4_DATA_FLOW.md
│   └── API.md
│
├── sample_data/
│   └── transcripts/
│       └── sample_meeting.txt
│
├── .gitignore
├── README.md
└── docker-compose.yml          # Local development
```

### Deliverables
- ✅ All Azure resources provisioned
- ✅ Development environment configured
- ✅ Repository structure created
- ✅ Can deploy "Hello World" to Container Apps
- ✅ Can authenticate with all Azure services

### Success Criteria
- [ ] Run `az deployment group create` successfully
- [ ] Access Key Vault secrets from local dev
- [ ] Upload test file to Blob Storage
- [ ] Write test document to Cosmos DB
- [ ] Send test message to Service Bus

---

## Phase 1: Core Pipeline - MVP Basic (Weeks 2-3)

### Goal
**Basic functionality:** Upload transcript → Get training document

### User Story
"As a trainer, I can upload a meeting transcript text file and receive a structured Word document with step-by-step instructions."

### Architecture Focus
```
User → API → Service Bus → Worker → Azure DI + OpenAI → Document → Blob Storage
```

### Tasks

#### 1.1 Transcript Processing Module

**File:** `backend/script_to_doc/pipeline.py`

```python
class TranscriptCleaner:
    """Clean and normalize transcript text."""
    
    def remove_timestamps(self, text: str) -> str:
        """Remove [00:00:00], (00:00), etc."""
        
    def remove_speaker_labels(self, text: str) -> str:
        """Remove 'Speaker 1:', 'JOHN:', etc."""
        
    def remove_filler_words(self, text: str, custom_words: list = None) -> str:
        """Remove um, uh, like, you know."""
        
    def remove_transcriber_tags(self, text: str) -> str:
        """Remove [inaudible], (laughs), etc."""
        
    def normalize(self, text: str) -> str:
        """Full cleaning pipeline."""

class SentenceTokenizer:
    """Break transcript into sentences."""
    
    def tokenize(self, text: str) -> list[str]:
        """Use NLTK sentence tokenizer."""
```

**Tests:**
```python
def test_remove_timestamps():
    input_text = "[00:15:32] Let's start the meeting"
    expected = "Let's start the meeting"
    assert cleaner.remove_timestamps(input_text) == expected

def test_remove_filler_words():
    input_text = "Um, so like, we need to, you know, deploy this"
    expected = "We need to deploy this"
    # ... assert
```

#### 1.2 Azure Document Intelligence Integration

**File:** `backend/script_to_doc/azure_di.py`

```python
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.identity import DefaultAzureCredential

class AzureDocumentIntelligence:
    def __init__(self, endpoint: str):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential()
        )
    
    def analyze_transcript_text(self, text: str) -> dict:
        """
        Use prebuilt-read model to extract structure.
        
        Returns:
            {
                "content": str,
                "paragraphs": [{content, role}],
                "pages": [{page_number, width, height}],
                "styles": [...]
            }
        """
        # Create temporary blob with text
        # Analyze with prebuilt-read
        # Return structured result
        
    def extract_process_structure(self, content: str) -> dict:
        """
        Identify process flow patterns from transcript.
        
        Returns:
            {
                "steps": [action items],
                "decisions": [if/then scenarios],
                "roles": [trainer, user, admin],
                "sequence": [numbered steps]
            }
        """
        # Use Azure DI structure + pattern matching
```

**Test Strategy:**
```python
# Test with sample transcript
sample = """
First, open the Azure portal. 
Then, navigate to the resource groups section.
Click on Create Resource Group.
If you don't have permissions, contact your administrator.
"""

result = azure_di.analyze_transcript_text(sample)
assert len(result["paragraphs"]) > 0

structure = azure_di.extract_process_structure(result["content"])
assert "steps" in structure
assert len(structure["steps"]) >= 3
```

#### 1.3 Azure OpenAI Integration

**File:** `backend/script_to_doc/azure_openai_client.py`

```python
from openai import AzureOpenAI

class AzureOpenAIClient:
    def __init__(self, endpoint: str, deployment: str = "gpt-4o-mini"):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-02-01",
            azure_ad_token_provider=get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
        )
        self.deployment = deployment
    
    def summarize_transcript(
        self, 
        text: str, 
        max_sentences: int = 10,
        tone: str = "Professional"
    ) -> tuple[list[str], dict]:
        """
        Summarize transcript into key points.
        
        Returns:
            (summary_sentences, token_usage)
        """
        prompt = f"""
        Summarize this meeting transcript into {max_sentences} key sentences.
        Tone: {tone}
        Focus on actionable steps and decisions.
        
        Transcript:
        {text}
        """
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a technical documentation expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        sentences = content.split('\n')
        
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return sentences, usage
    
    def generate_training_steps(
        self,
        transcript: str,
        azure_di_structure: dict,
        target_steps: int = 8,
        tone: str = "Professional"
    ) -> tuple[list[dict], dict]:
        """
        Generate step-by-step instructions.
        
        Returns:
            ([{title, summary, details, actions}], token_usage)
        """
        # Detailed prompt with examples
        # Parse response into structured steps
```

#### 1.4 Source Reference System

**File:** `backend/script_to_doc/source_reference.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SourceReference:
    type: str  # "transcript", "visual", "timestamp"
    excerpt: str
    timestamp: Optional[str] = None
    sentence_index: Optional[int] = None
    screenshot_ref: Optional[str] = None
    ui_elements: list[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.ui_elements is None:
            self.ui_elements = []

@dataclass
class StepSourceData:
    step_index: int
    step_content: str
    sources: list[SourceReference]
    overall_confidence: float
    has_transcript_support: bool
    has_visual_support: bool
    validation_flags: list[str]

class SourceReferenceManager:
    def __init__(self):
        self.sentence_catalog: list[str] = []
        self.step_sources: dict[int, StepSourceData] = {}
    
    def build_sentence_catalog(self, transcript: str) -> list[str]:
        """Create searchable catalog of all sentences."""
        
    def find_sources_for_step(
        self, 
        step_content: str,
        transcript_sentences: list[str],
        screenshots_data: list[dict] = None
    ) -> list[SourceReference]:
        """Find all source references for a generated step."""
        
    def calculate_confidence(self, step_data: StepSourceData) -> float:
        """
        Multi-factor confidence score.
        
        Factors:
        - Number of sources (0.1 per source, max +0.3)
        - Average source confidence
        - Cross-reference bonus (transcript + visual = +0.2)
        - Temporal alignment (timestamps match = +0.1)
        """
        
    def validate_step(self, step_data: StepSourceData) -> tuple[bool, list[str]]:
        """
        Check if step meets quality thresholds.
        
        Returns:
            (is_valid, [warning_messages])
        """
        warnings = []
        
        if step_data.overall_confidence < 0.6:
            warnings.append("Low confidence - may be hallucinated")
            
        if not step_data.has_transcript_support:
            warnings.append("No transcript support found")
            
        is_valid = step_data.overall_confidence >= 0.7
        return is_valid, warnings
```

#### 1.5 Document Generator

**File:** `backend/script_to_doc/document_generator.py`

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class TrainingDocumentGenerator:
    def __init__(self, title: str):
        self.doc = Document()
        self.title = title
        
    def add_title(self):
        """Add main document title."""
        heading = self.doc.add_heading(self.title, level=0)
        heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
    def add_step(
        self, 
        step_number: int,
        step_data: dict,
        source_data: StepSourceData
    ):
        """
        Add a complete step with sources.
        
        Format:
        Step N: [Title]
        Overview: [Summary]
        [Details paragraph]
        Key Actions:
          • Action 1
          • Action 2
        [Confidence: High | Sources: transcript (5), visual (screen_01)]
        """
        # Step heading
        self.doc.add_heading(f"Step {step_number}: {step_data['title']}", level=1)
        
        # Overview
        if step_data.get('summary'):
            p = self.doc.add_paragraph()
            p.add_run("Overview: ").bold = True
            p.add_run(step_data['summary'])
        
        # Details
        if step_data.get('details'):
            self.doc.add_paragraph(step_data['details'])
        
        # Actions (bullets)
        if step_data.get('actions'):
            p = self.doc.add_paragraph()
            p.add_run("Key Actions:").bold = True
            for action in step_data['actions']:
                self.doc.add_paragraph(action, style='List Bullet')
        
        # Confidence indicator
        confidence_level = self._get_confidence_level(source_data.overall_confidence)
        sources_summary = self._format_sources_summary(source_data.sources)
        
        p = self.doc.add_paragraph()
        p.add_run(f"[Confidence: {confidence_level} | Sources: {sources_summary}]")
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(100, 100, 100)
        
        self.doc.add_paragraph()  # Spacing
    
    def add_reference_section(self, all_step_sources: list[StepSourceData]):
        """
        Add appendix with full source excerpts.
        
        Format:
        SOURCE REFERENCES
        
        Step 1 - transcript (Sentence 5)
        "Full transcript excerpt here..."
        
        Step 1 - visual (screenshot_01.png)
        Screenshot showing File menu with Create option...
        """
        self.doc.add_page_break()
        self.doc.add_heading("Source References", level=1)
        
        for step_sources in all_step_sources:
            for source in step_sources.sources:
                # Step reference
                p = self.doc.add_paragraph()
                p.add_run(
                    f"Step {step_sources.step_index} - {source.type} "
                    f"({self._source_location(source)})"
                ).bold = True
                
                # Excerpt (as quote)
                quote = self.doc.add_paragraph(f'"{source.excerpt}"')
                quote.style = 'Intense Quote'
                
                self.doc.add_paragraph()  # Spacing
    
    def save(self, output_path: str):
        """Save document to file."""
        self.doc.save(output_path)
        return output_path
```

#### 1.6 FastAPI Endpoints

**File:** `backend/api/main.py`

```python
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import uuid

app = FastAPI(title="ScriptToDoc API")

@app.post("/process")
async def process_transcript(
    file: UploadFile = File(...),
    tone: str = Form("Professional"),
    audience: str = Form("General"),
    min_steps: int = Form(3),
    target_steps: int = Form(8),
    background_tasks: BackgroundTasks = None
):
    """
    Upload transcript and start processing.
    
    Returns:
        {"job_id": "abc123", "status": "queued"}
    """
    # 1. Validate file
    if not file.filename.endswith('.txt'):
        raise HTTPException(400, "Only .txt files accepted")
    
    if file.size > 5 * 1024 * 1024:  # 5 MB
        raise HTTPException(400, "File too large")
    
    # 2. Generate job ID
    job_id = str(uuid.uuid4())
    
    # 3. Upload to Blob Storage
    blob_service = BlobServiceClient.from_connection_string(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    )
    blob_client = blob_service.get_blob_client(
        container="uploads",
        blob=f"{job_id}/transcript.txt"
    )
    
    content = await file.read()
    blob_client.upload_blob(content)
    
    # 4. Create job record in Cosmos DB
    job_record = {
        "id": job_id,
        "status": "queued",
        "progress": 0.0,
        "stage": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "config": {
            "tone": tone,
            "audience": audience,
            "min_steps": min_steps,
            "target_steps": target_steps
        },
        "input": {
            "transcript_url": blob_client.url
        }
    }
    
    cosmos_client.create_item(job_record)
    
    # 5. Send message to Service Bus
    sb_client = ServiceBusClient.from_connection_string(
        os.environ["AZURE_SERVICE_BUS_CONNECTION_STRING"]
    )
    sender = sb_client.get_queue_sender("scripttodoc-jobs")
    
    message = ServiceBusMessage(
        body=json.dumps({
            "job_id": job_id,
            "transcript_url": blob_client.url,
            "config": job_record["config"]
        }),
        content_type="application/json"
    )
    
    sender.send_messages(message)
    
    return {
        "job_id": job_id,
        "status": "queued"
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get processing status.
    
    Returns:
        {
            "job_id": "abc123",
            "status": "processing",
            "progress": 0.45,
            "stage": "azure_di_analysis",
            "result": null  # or document data when complete
        }
    """
    job = cosmos_client.read_item(
        item=job_id,
        partition_key=job_id
    )
    
    return job

@app.get("/documents/{job_id}")
async def download_document(job_id: str):
    """
    Download generated document.
    
    Returns: DOCX file stream
    """
    # Get job to check status
    job = cosmos_client.read_item(item=job_id, partition_key=job_id)
    
    if job["status"] != "completed":
        raise HTTPException(400, "Document not ready")
    
    # Get document from Blob Storage
    blob_client = blob_service.get_blob_client(
        container="documents",
        blob=f"{job_id}_training.docx"
    )
    
    # Generate SAS URL with 1-hour expiry
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    from datetime import timedelta
    
    sas_token = generate_blob_sas(
        account_name=blob_client.account_name,
        container_name=blob_client.container_name,
        blob_name=blob_client.blob_name,
        account_key=os.environ["AZURE_STORAGE_KEY"],
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    
    return {
        "download_url": f"{blob_client.url}?{sas_token}",
        "expires_in": 3600
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

#### 1.7 Background Worker

**File:** `backend/workers/processor.py`

```python
from azure.servicebus import ServiceBusClient
from script_to_doc.pipeline import process_transcript
import json

def process_job_message(message_body: dict):
    """Process a single job from Service Bus."""
    job_id = message_body["job_id"]
    transcript_url = message_body["transcript_url"]
    config = message_body["config"]
    
    try:
        # Update status
        update_job_status(job_id, "processing", 0.05, "load_transcript")
        
        # Download transcript from blob
        transcript_text = download_blob(transcript_url)
        
        # Run processing pipeline
        result = process_transcript(
            transcript_text=transcript_text,
            job_id=job_id,
            config=config,
            progress_callback=lambda progress, stage: update_job_status(
                job_id, "processing", progress, stage
            )
        )
        
        # Mark complete
        update_job_status(job_id, "completed", 1.0, "done", result=result)
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        update_job_status(
            job_id, 
            "failed", 
            0.0, 
            "error",
            error=str(e)
        )
        raise

def main():
    """Main worker loop - listens to Service Bus."""
    sb_client = ServiceBusClient.from_connection_string(
        os.environ["AZURE_SERVICE_BUS_CONNECTION_STRING"]
    )
    
    receiver = sb_client.get_queue_receiver("scripttodoc-jobs")
    
    with receiver:
        for message in receiver:
            try:
                body = json.loads(str(message))
                process_job_message(body)
                receiver.complete_message(message)
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
                receiver.abandon_message(message)

if __name__ == "__main__":
    main()
```

### Deliverables
- ✅ Can clean transcripts (remove timestamps, fillers)
- ✅ Azure DI analyzes transcript structure
- ✅ Azure OpenAI generates training steps
- ✅ Source references linked to each step
- ✅ Word document generated with citations
- ✅ API accepts upload and returns job ID
- ✅ Worker processes jobs from Service Bus
- ✅ Can download completed document

### Success Criteria
**Test:** Upload `sample_meeting.txt` → Get `sample_meeting_training.docx`

Document should contain:
- [ ] 5-8 clear, actionable steps
- [ ] Each step has confidence score
- [ ] Source references in appendix
- [ ] Professional formatting
- [ ] Process completes in < 30 seconds

---

## Phase 2: Enhanced Features - Screenshots (Week 4)

### Goal
**Enhanced functionality:** Upload transcript + screenshots → Document with visual references

### User Story
"As a trainer, I can upload meeting transcripts with screenshots, and the generated document will reference specific UI elements visible in the images."

### New Components

#### 2.1 Screenshot Analysis

**File:** `backend/script_to_doc/azure_di.py` (extend)

```python
def analyze_screenshots(self, screenshot_blobs: list[str]) -> list[dict]:
    """
    Analyze screenshots with prebuilt-layout model.
    
    Returns:
        [{
            "filename": "screen_01.png",
            "content": "extracted text",
            "ui_elements": [{"type": "button", "text": "Create"}],
            "tables": [{row_count, column_count, content}],
            "layout": {...}
        }]
    """
    results = []
    
    for blob_url in screenshot_blobs:
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-layout",
            document_url=blob_url
        )
        result = poller.result()
        
        # Extract UI elements
        ui_elements = self._extract_ui_elements(result)
        
        results.append({
            "filename": extract_filename(blob_url),
            "content": result.content,
            "ui_elements": ui_elements,
            "tables": result.tables,
            "layout": result.pages[0] if result.pages else None
        })
    
    return results

def _extract_ui_elements(self, result) -> list[dict]:
    """Identify buttons, menus, forms from layout."""
    # Pattern matching on extracted text
    # Look for common UI patterns
```

#### 2.2 Cross-Reference Engine

**File:** `backend/script_to_doc/source_reference.py` (extend)

```python
def cross_reference_visuals(
    self,
    step_content: str,
    screenshot_data: dict
) -> list[SourceReference]:
    """
    Find visual evidence for a step.
    
    Match step actions (e.g., "Click Create button") with
    screenshot content (e.g., button labeled "Create").
    """
    visual_sources = []
    
    # Extract action verbs and targets from step
    actions = extract_action_phrases(step_content)
    # Example: "Click Create button" → ("click", "create button")
    
    for action_verb, action_target in actions:
        # Search screenshot UI elements
        for element in screenshot_data["ui_elements"]:
            similarity = fuzzy_match(action_target, element["text"])
            if similarity > 0.7:
                visual_sources.append(SourceReference(
                    type="visual",
                    excerpt=f"Screenshot showing {element['text']} {element['type']}",
                    screenshot_ref=screenshot_data["filename"],
                    ui_elements=[element["text"]],
                    confidence=similarity
                ))
    
    return visual_sources
```

#### 2.3 Enhanced Document Generator

**File:** `backend/script_to_doc/document_generator.py` (extend)

```python
def add_step(self, step_number: int, step_data: dict, source_data: StepSourceData):
    """Enhanced with screenshot references."""
    # ... existing code ...
    
    # Add screenshot indicators
    visual_sources = [s for s in source_data.sources if s.type == "visual"]
    if visual_sources:
        p = self.doc.add_paragraph()
        p.add_run("Visual References: ").bold = True
        for vs in visual_sources:
            p.add_run(f"\n  • {vs.screenshot_ref}: {vs.excerpt}")
            p.runs[-1].font.size = Pt(9)
```

#### 2.4 API Enhancement

**File:** `backend/api/main.py` (extend)

```python
@app.post("/process")
async def process_transcript(
    file: UploadFile = File(...),
    screenshots: list[UploadFile] = File(None),  # NEW: multiple screenshots
    tone: str = Form("Professional"),
    # ... other params
):
    """Enhanced to accept screenshots."""
    job_id = str(uuid.uuid4())
    
    # Upload transcript (same as before)
    # ...
    
    # Upload screenshots
    screenshot_urls = []
    if screenshots:
        for i, screenshot in enumerate(screenshots):
            blob_client = blob_service.get_blob_client(
                container="uploads",
                blob=f"{job_id}/screenshots/screen_{i:02d}{Path(screenshot.filename).suffix}"
            )
            content = await screenshot.read()
            blob_client.upload_blob(content)
            screenshot_urls.append(blob_client.url)
    
    # Update job record with screenshot URLs
    job_record["input"]["screenshot_urls"] = screenshot_urls
    
    # ... rest of processing
```

### Deliverables
- ✅ Can analyze screenshots with Azure DI
- ✅ Cross-reference steps with visual content
- ✅ Document includes screenshot citations
- ✅ API accepts multiple screenshot uploads
- ✅ Higher confidence scores with visual backing

### Success Criteria
**Test:** Upload transcript + 3 screenshots → Get enhanced document

Document should contain:
- [ ] Steps reference specific screenshots
- [ ] UI elements mentioned match screenshots
- [ ] Visual sources in reference section
- [ ] Confidence scores improved (+0.2 for cross-reference)

---

## Phase 3: Advanced - Video Processing (Week 5-6)

### Goal
**Full functionality:** Upload training video → Extract frames → Generate document

### User Story
"As a trainer, I can upload a training video (MP4), and the system will automatically extract key frames and generate a comprehensive training document."

### New Components

#### 3.1 Video Frame Extraction

**File:** `backend/script_to_doc/video_processor.py`

```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
import cv2

class VideoFrameExtractor:
    def __init__(self, computer_vision_endpoint: str):
        self.cv_client = ComputerVisionClient(
            endpoint=computer_vision_endpoint,
            credential=DefaultAzureCredential()
        )
    
    def extract_key_frames(
        self, 
        video_blob_url: str,
        interval_seconds: int = 30
    ) -> list[bytes]:
        """
        Extract frames from video at regular intervals.
        
        Strategy:
        1. Download video from blob
        2. Use OpenCV to extract frames
        3. Use Azure Computer Vision for scene change detection
        4. Return key frames as image bytes
        """
        # Download video
        video_path = download_blob_to_temp(video_blob_url)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_seconds)
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert frame to bytes
                _, buffer = cv2.imencode('.png', frame)
                frames.append(buffer.tobytes())
            
            frame_count += 1
        
        cap.release()
        
        # Filter for significant frames (scene changes)
        key_frames = self._detect_scene_changes(frames)
        
        return key_frames
    
    def _detect_scene_changes(self, frames: list[bytes]) -> list[bytes]:
        """Use Computer Vision to identify significant scenes."""
        # Analyze each frame for content
        # Keep frames with significant differences
        pass

def extract_transcript_from_video_audio(video_blob_url: str) -> str:
    """
    Extract audio and generate transcript.
    
    Options:
    1. Azure Speech-to-Text service
    2. Whisper API (OpenAI)
    3. AssemblyAI
    """
    # Extract audio from video
    # Send to speech-to-text service
    # Return transcript with timestamps
    pass
```

#### 3.2 Enhanced Pipeline

**File:** `backend/script_to_doc/pipeline.py` (extend)

```python
def process_video(
    video_blob_url: str,
    job_id: str,
    config: dict,
    progress_callback: callable
) -> dict:
    """
    Complete video processing pipeline.
    
    Steps:
    1. Extract audio → transcript (Azure Speech)
    2. Extract key frames (Computer Vision)
    3. Analyze frames (Azure DI)
    4. Process transcript (existing pipeline)
    5. Cross-reference with frames
    6. Generate document
    """
    progress_callback(0.05, "extracting_audio")
    transcript = extract_transcript_from_video_audio(video_blob_url)
    
    progress_callback(0.20, "extracting_frames")
    frames = video_processor.extract_key_frames(video_blob_url)
    
    progress_callback(0.35, "analyzing_frames")
    # Upload frames to blob storage
    frame_urls = upload_frames_to_blob(frames, job_id)
    
    # Continue with normal pipeline
    # ...
```

#### 3.3 Azure Speech Service Integration

**New File:** `backend/script_to_doc/azure_speech.py`

```python
import azure.cognitiveservices.speech as speechsdk

class AzureSpeechTranscriber:
    def __init__(self, speech_key: str, region: str):
        self.config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        self.config.speech_recognition_language = "en-US"
    
    def transcribe_audio_file(self, audio_blob_url: str) -> str:
        """
        Transcribe audio to text with timestamps.
        
        Returns formatted transcript:
        [00:00:05] Let's start the meeting...
        [00:00:32] First, open the Azure portal...
        """
        # Create audio config from blob
        # Run speech recognition
        # Format with timestamps
        pass
```

### Deliverables
- ✅ Extract audio from video
- ✅ Generate transcript with Azure Speech
- ✅ Extract key frames from video
- ✅ Analyze frames with Computer Vision
- ✅ Full pipeline works end-to-end

### Success Criteria
**Test:** Upload training video (5 min) → Get complete document

- [ ] Transcript generated from audio
- [ ] 10-15 key frames extracted
- [ ] Frames analyzed and referenced
- [ ] Document includes video timestamps
- [ ] Process completes in < 2 minutes

---

## Phase 4: Frontend UI (Week 7)

### Goal
Build Next.js frontend for ScriptToDoc

### Components to Build

#### 4.1 Upload Interface
```typescript
// components/UploadArea.tsx
export default function UploadArea() {
  const [files, setFiles] = useState<File[]>([]);
  
  const handleDrop = (e: DragEvent) => {
    // Handle file drop
  };
  
  return (
    <div 
      onDrop={handleDrop}
      className="border-2 border-dashed rounded-lg p-8"
    >
      {/* Drag-and-drop UI */}
    </div>
  );
}
```

#### 4.2 Progress Tracking
```typescript
// components/ProgressTracker.tsx
export default function ProgressTracker({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/status/${jobId}`);
      const data = await response.json();
      setStatus(data);
      
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  return (
    <div className="space-y-4">
      <ProgressBar value={status?.progress * 100} />
      <StepIndicator currentStage={status?.stage} />
    </div>
  );
}
```

#### 4.3 Document Preview
```typescript
// components/DocumentPreview.tsx
export default function DocumentPreview({ result }: { result: JobResult }) {
  return (
    <div className="space-y-6">
      {result.steps.map((step, i) => (
        <StepCard key={i} step={step} sources={result.sources[i]} />
      ))}
      
      <button onClick={() => downloadDocument(result.job_id)}>
        Download Word Document
      </button>
    </div>
  );
}
```

### Deliverables
- ✅ Upload interface (transcript + screenshots)
- ✅ Configuration controls (tone, audience, steps)
- ✅ Real-time progress tracking
- ✅ Document preview
- ✅ Download functionality
- ✅ Responsive design (mobile-friendly)

---

## Phase 5: Production Readiness (Week 8)

### Goal
Security, monitoring, and deployment

### Tasks

#### 5.1 Security
- [ ] Implement Azure AD authentication
- [ ] Add rate limiting
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set up WAF rules
- [ ] Audit logging enabled

#### 5.2 Monitoring
- [ ] Application Insights dashboards
- [ ] Cost tracking queries
- [ ] Error alerting (email/Teams)
- [ ] Performance baselines

#### 5.3 CI/CD
- [ ] GitHub Actions pipelines
- [ ] Automated testing
- [ ] Blue-green deployment
- [ ] Rollback procedures

#### 5.4 Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide
- [ ] Admin guide
- [ ] Architecture diagrams

### Deliverables
- ✅ Production environment deployed
- ✅ Monitoring dashboards active
- ✅ CI/CD pipeline running
- ✅ Security review passed
- ✅ Documentation complete

---

## Testing Strategy

### Unit Tests
```bash
# Backend
pytest backend/tests/ --cov=script_to_doc

# Frontend
npm test
```

### Integration Tests
```python
def test_end_to_end_basic():
    """Test complete pipeline."""
    # Upload transcript
    response = client.post("/process", files={"file": transcript_file})
    job_id = response.json()["job_id"]
    
    # Wait for completion
    for _ in range(30):
        status = client.get(f"/status/{job_id}").json()
        if status["status"] == "completed":
            break
        time.sleep(1)
    
    assert status["status"] == "completed"
    
    # Download document
    doc_response = client.get(f"/documents/{job_id}")
    assert doc_response.status_code == 200
    
    # Verify document content
    doc = Document(BytesIO(doc_response.content))
    assert len(doc.paragraphs) > 10
```

### Performance Tests
```python
def test_performance_baseline():
    """Ensure processing time is acceptable."""
    start = time.time()
    result = process_transcript(sample_transcript, config)
    duration = time.time() - start
    
    assert duration < 30, f"Processing took {duration}s, expected <30s"
```

---

## Success Metrics

### Phase 1 (Core)
- [ ] 95% of jobs complete successfully
- [ ] Average processing time < 20 seconds
- [ ] Generated steps have 0.7+ average confidence

### Phase 2 (Screenshots)
- [ ] 80% of steps cross-referenced with visuals
- [ ] Average confidence improves to 0.8+

### Phase 3 (Video)
- [ ] Video processing completes in < 2 minutes
- [ ] Transcript accuracy > 90%

### Phase 4 (Frontend)
- [ ] 100% of users can complete upload flow
- [ ] Mobile-friendly (responsive design)

### Phase 5 (Production)
- [ ] 99% uptime
- [ ] Zero security incidents
- [ ] All monitoring alerts configured

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 0 - Foundation | 1 week | Azure infrastructure ready |
| 1 - Core MVP | 2 weeks | Basic transcript → document |
| 2 - Screenshots | 1 week | Enhanced with visuals |
| 3 - Video | 2 weeks | Full video processing |
| 4 - Frontend | 1 week | Next.js UI complete |
| 5 - Production | 1 week | Deployed and monitored |
| **Total** | **8 weeks** | **Production-ready MVP** |

---

**Next:** Review this plan, adjust priorities, and start Phase 0!

