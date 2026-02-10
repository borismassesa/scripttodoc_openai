# ScriptToDoc - Quick Start Guide (Phase 1)

## 🎯 What is Phase 1?

Phase 1 is the **Core MVP** that converts meeting transcripts into professional training documents:

**Input:** Meeting transcript (text file)
**Output:** Professional Word document with:
- Step-by-step instructions
- Source citations
- Confidence scores
- Professional formatting

## ⚡ Quick Test (5 minutes)

### 1. Prerequisites

- Python 3.11+
- Azure Document Intelligence resource
- Azure OpenAI Service resource

### 2. Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.template .env
# Edit .env and add your Azure credentials
```

### 3. Configure Azure Credentials

Edit `backend/.env`:

```env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://YOUR-DI.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here

AZURE_OPENAI_ENDPOINT=https://YOUR-OPENAI.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### 4. Run Simple Test

```bash
# From backend directory
python test_pipeline_simple.py
```

**Expected output:**
- ✅ Processing completes in ~20-30 seconds
- 📄 Generates `output/sample_meeting_training.docx`
- 📊 Shows confidence scores and metrics

### 5. Open the Document

```bash
# macOS
open output/sample_meeting_training.docx

# Windows
start output/sample_meeting_training.docx

# Linux
xdg-open output/sample_meeting_training.docx
```

## 🚀 Full System Test (with API and Worker)

### 1. Prerequisites (Additional)

- Azure Cosmos DB resource
- Azure Blob Storage account
- Azure Service Bus namespace

### 2. Configure Full Environment

Edit `backend/.env` with additional settings:

```env
# Storage
AZURE_STORAGE_ACCOUNT_NAME=stscripttodocdev
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Cosmos DB
AZURE_COSMOS_ENDPOINT=https://YOUR-COSMOS.documents.azure.com:443/
AZURE_COSMOS_KEY=your-key-here
AZURE_COSMOS_DATABASE=scripttodoc
AZURE_COSMOS_CONTAINER_JOBS=jobs

# Service Bus
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://YOUR-SB.servicebus.windows.net/...
AZURE_SERVICE_BUS_QUEUE_NAME=scripttodoc-jobs
```

### 3. Start Services

**Terminal 1 - API:**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Worker:**
```bash
cd backend
source venv/bin/activate
python workers/processor.py
```

### 4. Test API

**Upload transcript:**
```bash
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@../sample_data/transcripts/sample_meeting.txt" \
  -F "document_title=Azure Deployment Guide" \
  -F "tone=Professional"
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "queued"
}
```

**Check status:**
```bash
curl "http://localhost:8000/api/status/abc-123-def"
```

**Download document:**
```bash
# Get download URL
curl "http://localhost:8000/api/documents/abc-123-def"

# Use the download_url from response to download
```

## 📊 What to Expect

### Sample Output

For `sample_meeting.txt` (5-minute Azure tutorial):

**Generated Document Contains:**
- 7-9 training steps
- Each step with:
  - Clear title
  - Overview summary
  - Detailed instructions
  - Key actions (bullet points)
  - Confidence score (0.7-0.95)
  - Source citations

**Processing Time:** 20-30 seconds

**Quality Metrics:**
- Average confidence: 0.75-0.85
- High confidence steps: 6-8 out of 8
- Source references: 20-30 citations

### Example Step

```
Step 1: Access the Azure Portal

Overview: Navigate to portal.azure.com and authenticate with your credentials

To begin the process, you need to access the Azure Portal web interface. This is the 
central hub for managing all Azure resources. Open your preferred web browser and enter 
the URL. Once the page loads, you'll be prompted to sign in with your organizational 
credentials.

Key Actions:
  • Open web browser
  • Navigate to portal.azure.com
  • Enter credentials and sign in
  • Complete multi-factor authentication if enabled

[Confidence: High (0.92) | Sources: transcript (3), visual (0)]
```

## 🔧 Troubleshooting

### "Module not found" errors
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "NLTK punkt not found"
```bash
python -c "import nltk; nltk.download('punkt')"
```

### Azure connection errors
```bash
# Test endpoints
curl -I https://YOUR-ENDPOINT.cognitiveservices.azure.com/

# Verify .env file
cat .env | grep AZURE_
```

### Low confidence scores
- ✅ Normal range: 0.6-0.9
- ⚠️ Below 0.6: Transcript may be unclear
- 💡 Tip: Use cleaner transcripts for better results

## 📖 Next Steps

### Customize Processing

Edit `test_pipeline_simple.py`:

```python
config = PipelineConfig(
    # ... endpoints ...
    target_steps=10,              # More/fewer steps
    tone="Technical",              # or "Casual"
    audience="Beginners",          # or "Experts"
    min_confidence_threshold=0.8   # Stricter validation
)
```

### Try Your Own Transcripts

```bash
# Place your transcript in sample_data/transcripts/
cp your_meeting.txt sample_data/transcripts/

# Update test script to use your file
# Edit test_pipeline_simple.py, line 46:
sample_path = Path(...) / "your_meeting.txt"

# Run test
python test_pipeline_simple.py
```

### Explore the Code

**Core modules:**
- `script_to_doc/pipeline.py` - Main orchestration
- `script_to_doc/transcript_cleaner.py` - Text processing
- `script_to_doc/azure_openai_client.py` - Step generation
- `script_to_doc/document_generator.py` - Word document creation

### Phase 2 Preview

Coming soon:
- 📸 Screenshot analysis
- 🔗 Visual cross-referencing
- 🎯 Enhanced UI element detection
- ⬆️ Multi-file uploads

## 💡 Tips

### Better Results

1. **Clean transcripts work best:**
   - Remove excessive timestamps
   - Fix obvious typos
   - Remove long tangential discussions

2. **Adjust step count based on content:**
   - Short transcript (< 500 words): 3-5 steps
   - Medium (500-1500 words): 5-8 steps
   - Long (> 1500 words): 8-12 steps

3. **Use appropriate tone:**
   - `Professional`: Formal documentation
   - `Technical`: Developer-focused
   - `Casual`: Friendly training

### Performance

- First run: ~30-40s (cold start)
- Subsequent runs: ~15-25s
- Most time: OpenAI generation (60%)

## 📚 Documentation

- **Full README:** `backend/README.md`
- **API Docs:** http://localhost:8000/docs (when API running)
- **Architecture:** `architecture/1_SYSTEM_ARCHITECTURE.md`
- **Implementation Plan:** `architecture/2_IMPLEMENTATION_PHASES.md`

## 🎉 Success Criteria

Phase 1 is working if:
- ✅ Processes sample transcript in < 30s
- ✅ Generates readable Word document
- ✅ Average confidence > 0.7
- ✅ Steps are clear and actionable
- ✅ Source citations present

---

**Ready to build Phase 2?** Check `architecture/2_IMPLEMENTATION_PHASES.md` for Phase 2 (Screenshots) plan!

