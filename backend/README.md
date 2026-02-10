# ScriptToDoc Backend - Phase 1 MVP

## Overview

This is the backend implementation for ScriptToDoc Phase 1: Core MVP functionality.

**Features:**
- ✅ Transcript cleaning and processing
- ✅ Azure Document Intelligence integration
- ✅ Azure OpenAI integration for step generation
- ✅ Source reference system with confidence scoring
- ✅ Professional Word document generation
- ✅ REST API with async job processing
- ✅ Background worker with Service Bus queue

## Project Structure

```
backend/
├── script_to_doc/           # Core processing library
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── transcript_parser.py # Intelligent transcript parsing
│   ├── topic_segmenter.py   # Topic-based segmentation
│   ├── transcript_cleaner.py # Text cleaning
│   ├── azure_di.py          # Azure DI integration
│   ├── azure_openai_client.py # OpenAI integration
│   ├── source_reference.py  # Source tracking
│   ├── document_generator.py # Word document creation
│   └── pipeline.py          # Main orchestration
│
├── api/                     # FastAPI REST API
│   ├── main.py             # Main app
│   ├── models.py           # Pydantic models
│   ├── dependencies.py     # Auth, DB connections
│   └── routes/
│       ├── process.py      # Upload endpoints
│       ├── status.py       # Status endpoints
│       └── documents.py    # Download endpoints
│
├── workers/                 # Background processing
│   └── processor.py        # Service Bus worker
│
├── tests/                   # Organized test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/                # End-to-end tests
│   └── test_converters.py  # File conversion tests
│
├── scripts/                 # Utility scripts
│   ├── analyze_week0_quality.py
│   ├── cleanup_database.py
│   └── verify_cosmos_empty.py
│
├── docs/                    # Technical documentation
│   ├── SEMANTIC_SIMILARITY_FINAL_REPORT.md
│   ├── SEMANTIC_SIMILARITY_RESEARCH.md
│   └── TASK_11_SEMANTIC_SIMILARITY_SUMMARY.md
│
├── output/                  # Generated output files
├── test_output/            # Test results
├── requirements.txt         # Python dependencies
└── .env                    # Environment variables
```

## Prerequisites

### Azure Resources Required

Before running, you need these Azure resources:

1. **Azure Document Intelligence**
   - Endpoint URL
   - API Key

2. **Azure OpenAI Service**
   - Endpoint URL
   - API Key
   - Deployment: gpt-4o-mini

3. **Azure Cosmos DB** (NoSQL)
   - Endpoint URL
   - API Key
   - Database: `scripttodoc`
   - Container: `jobs` (partition key: `/userId`)

4. **Azure Blob Storage**
   - Storage account name
   - Connection string
   - Containers: `uploads`, `documents`, `temp`

5. **Azure Service Bus**
   - Connection string
   - Queue: `scripttodoc-jobs`

### Local Development

**Required:**
- Python 3.11+
- pip

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.template` to `.env` and fill in your Azure credentials:

```bash
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=stscripttodocdev
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_KEY=your-key

# Azure Service Bus
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://your-sb.servicebus.windows.net/...

# Bing Search API (Optional - for internet browsing feature)
BING_SEARCH_API_KEY=your-bing-search-api-key
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
```

**Note:** For detailed Bing Search API setup instructions, see [BING_SEARCH_SETUP.md](./BING_SEARCH_SETUP.md)

### 3. Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt')"
```

## Running the Application

### Option 1: Full Stack (API + Worker)

**Terminal 1 - API Server:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Background Worker:**
```bash
cd backend
source venv/bin/activate
python workers/processor.py
```

### Option 2: Standalone Processing (No Azure Services)

For testing the core pipeline without Azure infrastructure:

```python
from script_to_doc.pipeline import process_transcript_file, PipelineConfig

config = PipelineConfig(
    azure_di_endpoint="your-endpoint",
    azure_di_key="your-key",
    azure_openai_endpoint="your-endpoint",
    azure_openai_key="your-key",
    target_steps=8,
    tone="Professional"
)

result = process_transcript_file(
    transcript_path="../sample_data/transcripts/sample_meeting.txt",
    output_dir="./output",
    config=config
)

if result.success:
    print(f"Document created: {result.document_path}")
    print(f"Average confidence: {result.metrics['average_confidence']:.2f}")
else:
    print(f"Error: {result.error}")
```

## API Usage

### 1. Upload Transcript

```bash
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@sample_meeting.txt" \
  -F "tone=Professional" \
  -F "target_steps=8"
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "queued",
  "message": "Job queued for processing"
}
```

### 2. Check Status

```bash
curl "http://localhost:8000/api/status/abc-123-def"
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "processing",
  "progress": 0.45,
  "stage": "generate_steps",
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:01:00Z"
}
```

### 3. Download Document

```bash
curl "http://localhost:8000/api/documents/abc-123-def"
```

**Response:**
```json
{
  "download_url": "https://storage.blob.core.windows.net/...",
  "expires_in": 3600,
  "filename": "training_document.docx"
}
```

## Testing

### Sample Data

Test transcripts are in `sample_data/transcripts/`:
- `sample_meeting.txt` - Full meeting transcript (~5 min)
- `short_test.txt` - Quick test (30 seconds)

### Manual Test

```bash
# 1. Start API and Worker (see above)

# 2. Upload sample transcript
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@../sample_data/transcripts/sample_meeting.txt" \
  -F "document_title=Azure Deployment Guide"

# 3. Note the job_id from response

# 4. Poll status until completed
curl "http://localhost:8000/api/status/{job_id}"

# 5. Download document
curl "http://localhost:8000/api/documents/{job_id}" | jq -r .download_url
```

## Configuration Options

### Pipeline Config

```python
PipelineConfig(
    # Azure services
    azure_di_endpoint: str,
    azure_di_key: str,
    azure_openai_endpoint: str,
    azure_openai_key: str,
    
    # Processing options
    use_azure_di: bool = True,
    use_openai: bool = True,
    
    # Content options
    min_steps: int = 3,
    target_steps: int = 8,
    max_steps: int = 15,
    tone: str = "Professional",  # or "Casual", "Technical"
    audience: str = "Technical Users",
    
    # Quality options
    min_confidence_threshold: float = 0.7,
    enable_source_validation: bool = True,
    
    # Document options
    document_title: str = None,
    include_statistics: bool = True
)
```

## Architecture

### Processing Flow

```
1. User uploads transcript via API
2. API validates and uploads to Blob Storage
3. API creates job record in Cosmos DB
4. API sends message to Service Bus queue
5. Worker picks up message
6. Worker downloads transcript
7. Worker runs processing pipeline:
   a. Clean transcript
   b. Analyze with Azure DI
   c. Generate steps with OpenAI
   d. Build source references
   e. Validate confidence
   f. Create Word document
8. Worker uploads document to Blob Storage
9. Worker updates job status to "completed"
10. User downloads document via API
```

### Pipeline Stages

1. **load_transcript** (5%) - Download and load
2. **clean_transcript** (15%) - Remove noise
3. **azure_di_analysis** (35%) - Structure extraction
4. **generate_steps** (60%) - OpenAI step generation
5. **build_sources** (75%) - Source reference linking
6. **validate_steps** (85%) - Confidence validation
7. **create_document** (95%) - Word document generation
8. **upload_document** (100%) - Upload to storage

## Troubleshooting

### Common Issues

**1. Import errors**
```bash
# Make sure you're in the backend directory and venv is activated
cd backend
source venv/bin/activate
```

**2. Azure connection failures**
```bash
# Check your .env file has correct credentials
# Test connectivity:
python -c "from script_to_doc.config import get_settings; s = get_settings(); print(s.azure_openai_endpoint)"
```

**3. NLTK punkt not found**
```bash
python -c "import nltk; nltk.download('punkt')"
```

**4. Service Bus worker not processing**
```bash
# Check queue name matches
# Verify connection string is correct
# Check worker logs for errors
```

## Success Metrics

Phase 1 targets:
- ✅ Process transcript in < 30 seconds
- ✅ Average confidence score > 0.7
- ✅ 95%+ jobs complete successfully
- ✅ Generated steps are actionable and clear

## Next Steps (Phase 2)

Phase 2 will add:
- Screenshot analysis
- Visual cross-referencing
- Enhanced confidence scoring
- UI element detection

## Support

For issues or questions:
1. Check logs in console output
2. Verify Azure resource configuration
3. Test with sample data first
4. Check API documentation at http://localhost:8000/docs

---

**Built with:**
- FastAPI 0.109.0
- Azure SDK for Python
- OpenAI Python SDK
- python-docx 1.1.0
- NLTK 3.8.1

