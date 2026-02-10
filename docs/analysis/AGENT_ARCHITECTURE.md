# How the ScriptToDoc Agent Works: A 7-Stage Intelligent Pipeline

The ScriptToDoc agent transforms meeting transcripts into professional training documents through a sophisticated **7-stage pipeline** that combines AI-powered content generation with intelligent knowledge integration.

---

## Pipeline Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ScriptToDoc 7-Stage Pipeline                          │
└─────────────────────────────────────────────────────────────────────────┘

Stage 1: LOAD & VALIDATE
┌──────────────────────────────────────────────────────────────────────────┐
│  User Input → Validation → Configuration                                 │
│  • Upload transcript (.txt, .pdf)                                        │
│  • Provide knowledge URLs (optional)                                     │
│  • Configure: tone, audience, target_steps, document_title              │
│  • Validate file format and size                                         │
│  [STATUS: User Approval Required] ✋                                     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ User clicks "Generate"
                                     ↓
Stage 2: FETCH KNOWLEDGE
┌──────────────────────────────────────────────────────────────────────────┐
│  Knowledge Fetcher: Parallel URL Retrieval                               │
│  • Fetch content from provided URLs (web, PDF, docs)                    │
│  • Extract up to 100k chars per source                                   │
│  • Cache for 24 hours (fast re-runs)                                     │
│  • Handle errors gracefully (continue if some fail)                      │
│                                                                           │
│  Output: List of knowledge sources with content + metadata               │
│  Tags: [FETCHED], [ERROR], [CACHED]                                     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
Stage 3: CLEAN & TOKENIZE
┌──────────────────────────────────────────────────────────────────────────┐
│  Transcript Cleaner: Text Normalization                                  │
│  • Sentence tokenization (NLTK)                                          │
│  • Normalize whitespace, punctuation                                     │
│  • Remove artifacts, fix formatting                                      │
│  • Build sentence catalog for source matching                            │
│                                                                           │
│  Output: Clean sentence list (used for source grounding)                 │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
Stage 4: SEMANTIC CHUNKING
┌──────────────────────────────────────────────────────────────────────────┐
│  Transcript Chunker: Intelligent Splitting                               │
│  • Split into N chunks (where N = target_steps)                          │
│  • Ensure 6-12 sentences per chunk                                       │
│  • Maintain semantic continuity (no mid-topic splits)                    │
│  • Balance chunk sizes (no tiny/huge chunks)                             │
│                                                                           │
│  Output: N focused chunks (1 chunk → 1 training step)                    │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
                            ┌────────────────────┐
                            │  FOR EACH CHUNK:   │
                            │  (Parallel Loop)   │
                            └────┬───────────────┘
                                 ↓
Stage 5: GENERATE STEPS (The Core Loop)
┌──────────────────────────────────────────────────────────────────────────┐
│  🔄 ITERATIVE PROCESS FOR EACH CHUNK (N iterations)                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 5.1 SEMANTIC SEARCH (Knowledge Matching)                         │   │
│  │                                                                   │   │
│  │  Knowledge Fetcher → find_relevant_excerpts()                    │   │
│  │  • Encode chunk using sentence-transformers (all-MiniLM-L6-v2)  │   │
│  │  • Split knowledge sources into 500-char overlapping excerpts   │   │
│  │  • Calculate cosine similarity: chunk ↔ each excerpt            │   │
│  │  • Filter: keep only excerpts with similarity > 0.1             │   │
│  │  • Rank by relevance score (0.0-1.0)                            │   │
│  │  • Select top 5 excerpts overall                                │   │
│  │                                                                   │   │
│  │  Output: Top 5 relevant excerpts with scores                    │   │
│  │  Tags: [SEMANTIC_MATCH], [HIGH_RELEVANCE], [FILTERED]          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 5.2 PROMPT CONSTRUCTION                                          │   │
│  │                                                                   │   │
│  │  Azure OpenAI Client → _build_chunk_prompt()                    │   │
│  │  • Inject transcript chunk (6-12 sentences)                      │   │
│  │  • Inject top 5 relevant knowledge excerpts with scores         │   │
│  │  • Add grounding instructions:                                   │   │
│  │    ✓ Quote transcript directly (exact terminology)              │   │
│  │    ✓ Enhance with knowledge context                             │   │
│  │    ✓ Add technical depth from sources                           │   │
│  │    ✗ Don't contradict transcript                                │   │
│  │    ✗ Don't replace transcript content                           │   │
│  │  • Set tone, audience, step index                               │   │
│  │                                                                   │   │
│  │  Prompt Structure:                                               │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │ CREATE ONE TRAINING STEP (Step N of M)                   │  │   │
│  │  │                                                           │  │   │
│  │  │ TRANSCRIPT CHUNK:                                         │  │   │
│  │  │ [6-12 focused sentences from transcript]                 │  │   │
│  │  │                                                           │  │   │
│  │  │ === RELEVANT KNOWLEDGE SOURCES ===                       │  │   │
│  │  │ 📚 MOST RELEVANT EXCERPTS (sorted by relevance):        │  │   │
│  │  │                                                           │  │   │
│  │  │ [Excerpt 1] Azure Deployment Guide (Relevance: 0.87)    │  │   │
│  │  │ URL: https://learn.microsoft.com/...                     │  │   │
│  │  │ Content: When configuring deployment capacity...        │  │   │
│  │  │                                                           │  │   │
│  │  │ [Excerpt 2] Best Practices (Relevance: 0.72)            │  │   │
│  │  │ URL: https://docs.azure.com/...                          │  │   │
│  │  │ Content: Token capacity affects throughput...            │  │   │
│  │  │                                                           │  │   │
│  │  │ 📝 INSTRUCTIONS FOR USING KNOWLEDGE:                     │  │   │
│  │  │ ✓ DO: Use knowledge for technical depth                 │  │   │
│  │  │ ✗ DON'T: Replace transcript content                     │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 5.3 LLM GENERATION                                               │   │
│  │                                                                   │   │
│  │  Azure OpenAI (gpt-4o) or OpenAI (gpt-4o-mini fallback)        │   │
│  │  • Temperature: 0.2 (focused, consistent)                       │   │
│  │  • Max tokens: 1000 (one step)                                  │   │
│  │  • Top-p: 0.85 (slightly lower for precision)                  │   │
│  │  • Timeout: 60s                                                 │   │
│  │                                                                   │   │
│  │  Output: ONE training step                                      │   │
│  │  {                                                               │   │
│  │    "title": "Configure Azure OpenAI Deployment Settings",       │   │
│  │    "summary": "Navigate to Deployments section...",             │   │
│  │    "details": "In the Azure Portal, access... Microsoft         │   │
│  │                recommends 10K TPM for production...",            │   │
│  │    "actions": [                                                  │   │
│  │      "Navigate to Deployments section in Azure Portal",         │   │
│  │      "Click Create to start new deployment",                    │   │
│  │      "Set capacity to 10K tokens per minute",                   │   │
│  │      "Select gpt-4o model from available models",               │   │
│  │      "Choose region closest to users for optimal latency"       │   │
│  │    ]                                                             │   │
│  │  }                                                               │   │
│  │                                                                   │   │
│  │  Token Usage: ~650 tokens (input + output)                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Total Steps Generated: N steps (one per chunk)                          │
│  Total Tokens: ~650 × N tokens                                           │
│  Processing Time: ~4-6 seconds per step                                  │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
Stage 6: VALIDATE & SCORE (Quality Gate)
┌──────────────────────────────────────────────────────────────────────────┐
│  🔍 CRITIQUE LOOP FOR EACH GENERATED STEP                                │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 6.1 SOURCE MATCHING                                              │   │
│  │                                                                   │   │
│  │  Source Reference Manager → build_step_sources()                │   │
│  │  • Search transcript for sentences matching the step            │   │
│  │  • Use hybrid scoring:                                           │   │
│  │    - 50% word overlap (Jaccard similarity)                      │   │
│  │    - 50% semantic similarity (sentence-transformers)            │   │
│  │  • Find top 5 matching transcript sentences                     │   │
│  │  • Match knowledge sources cited in step                         │   │
│  │  • Track source usage (which URLs were helpful)                 │   │
│  │                                                                   │   │
│  │  Output: Sources per step                                        │   │
│  │  • Transcript sources: [3 sentences, avg confidence: 0.64]      │   │
│  │  • Knowledge sources: [2 URLs cited]                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 6.2 CONFIDENCE CALCULATION                                       │   │
│  │                                                                   │   │
│  │  calculate_confidence() - Multi-factor scoring                  │   │
│  │                                                                   │   │
│  │  Base Score (weighted average of top 3 sources):                │   │
│  │  • Source 1: 0.68 × 50%                                         │   │
│  │  • Source 2: 0.64 × 30%                                         │   │
│  │  • Source 3: 0.59 × 20%                                         │   │
│  │  = 0.65 base score                                              │   │
│  │                                                                   │   │
│  │  Multiplicative Bonuses:                                         │   │
│  │  × 1.15  (3 sources bonus)                                      │   │
│  │  × 1.12  (diverse: transcript + knowledge)                      │   │
│  │  × 1.10  (has high confidence source > 0.5)                     │   │
│  │  = 0.92 final confidence                                        │   │
│  │                                                                   │   │
│  │  Confidence Level: "Very High" (0.75+)                          │   │
│  │  Tags: [HIGH_CONFIDENCE], [TRANSCRIPT_GROUNDED],               │   │
│  │        [KNOWLEDGE_ENHANCED]                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 6.3 VALIDATION GATE                                              │   │
│  │                                                                   │   │
│  │  validate_step() - Quality threshold                            │   │
│  │                                                                   │   │
│  │  Requirements:                                                    │   │
│  │  ✓ Confidence ≥ 0.4  (minimum quality bar)                      │   │
│  │  ✓ Has transcript support (≥1 transcript source)                │   │
│  │  ✓ Has ≥1 source overall                                        │   │
│  │                                                                   │   │
│  │  Decision:                                                        │   │
│  │  IF all requirements met:                                        │   │
│  │    → [VALIDATED] → Include in document                          │   │
│  │  ELSE:                                                            │   │
│  │    → [REJECTED] → Exclude from document                         │   │
│  │    → Log warning with reason                                     │   │
│  │                                                                   │   │
│  │  Result: X valid steps / N total steps                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Final Validation:                                                        │
│  • IF valid_steps < 1: FAIL job (no empty documents)                    │
│  • ELSE: Proceed to document generation                                  │
│                                                                           │
│  Quality Metrics:                                                         │
│  • Average confidence: 0.68 (High)                                       │
│  • High confidence steps: 7/10 (≥70%)                                    │
│  • Knowledge usage rate: 85% (2/2 sources cited)                         │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
Stage 7: ASSEMBLE DOCUMENT
┌──────────────────────────────────────────────────────────────────────────┐
│  Document Generator: Professional Word Document (.docx)                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.1 Title Page                                                   │   │
│  │  • Brand name, subtitle, metadata                                │   │
│  │  • Generation date, version, author                              │   │
│  │  • Document information table                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.2 Table of Contents                                            │   │
│  │  • Auto-generated from step titles                               │   │
│  │  • Can be replaced with Word TOC field for page numbers         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.3 Introduction                                                 │   │
│  │  • Document overview                                             │   │
│  │  • How to use this document                                      │   │
│  │  • Structure explanation                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.4 Training Steps (Main Content)                                │   │
│  │                                                                   │   │
│  │  For each validated step:                                        │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │ Step N: [Title using exact transcript terminology]         │ │   │
│  │  │                                                             │ │   │
│  │  │ 📋 Overview: [One sentence summary]                        │ │   │
│  │  │                                                             │ │   │
│  │  │ [2-3 sentences with knowledge-enhanced details]            │ │   │
│  │  │                                                             │ │   │
│  │  │ ✅ Key Actions:                                            │ │   │
│  │  │ 1. [Exact action from chunk]                               │ │   │
│  │  │ 2. [Exact action from chunk]                               │ │   │
│  │  │ 3. [Exact action from chunk]                               │ │   │
│  │  │                                                             │ │   │
│  │  │ Quality Indicator: High (68%) | Sources: transcript (3),   │ │   │
│  │  │                                          knowledge (2)      │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.5 Source References (Appendix)                                 │   │
│  │                                                                   │   │
│  │  For each step, list all sources:                               │   │
│  │  • Transcript excerpts (full sentences)                          │   │
│  │  • Knowledge source excerpts (with URLs)                         │   │
│  │  • Confidence score per source                                   │   │
│  │  • Source type icons: 📄 (transcript) 🌐 (knowledge)            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.6 Knowledge Sources Used                                       │   │
│  │                                                                   │   │
│  │  List all fetched knowledge sources:                            │   │
│  │  • URL, title, type (web/PDF)                                   │   │
│  │  • Content preview (500 chars)                                   │   │
│  │  • Which steps cited this source                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 7.7 Document Statistics                                          │   │
│  │                                                                   │   │
│  │  Processing metrics:                                             │   │
│  │  • Total steps: 10                                               │   │
│  │  • Average confidence: 68% (High)                                │   │
│  │  • High confidence steps: 7/10 (≥70%)                            │   │
│  │  • Total source references: 45                                   │   │
│  │  • Processing time: 58.1 seconds                                 │   │
│  │  • Input tokens: 4,500                                           │   │
│  │  • Output tokens: 2,459                                          │   │
│  │  • Total tokens: 6,959                                           │   │
│  │  • Estimated cost: $0.0015                                       │   │
│  │  • Knowledge sources fetched: 2                                  │   │
│  │  • Knowledge sources cited: 2                                    │   │
│  │  • Knowledge usage rate: 100%                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Output: Professional .docx document with:                               │
│  • ~15-20 pages (for 10 steps)                                           │
│  • Professional formatting (Calibri font, color-coded headings)          │
│  • Inline citations & quality indicators                                 │
│  • Complete source references                                            │
│  • Ready for distribution or editing in Word                             │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
                           ✅ JOB COMPLETE
                    Document uploaded to Azure Blob Storage
                    User can download via frontend
```

---

## Stage-by-Stage Deep Dive

### Stage 1: LOAD & VALIDATE

**Purpose:** Accept user inputs and validate before processing

**Inputs:**
- Transcript file (.txt or .pdf, max 10MB)
- Configuration (tone, audience, target_steps, document_title)
- Knowledge URLs (optional, up to 10 URLs)

**Processing:**
1. Validate file format and size
2. Extract text from PDF if needed
3. Validate configuration parameters
4. Create job record in Cosmos DB
5. Upload transcript to Blob Storage

**Outputs:**
- Job ID (unique identifier)
- Initial job status: "queued"
- Validated configuration object

**Tags:** `[INIT]`, `[LOAD_TRANSCRIPT]`

**Error Handling:**
- Invalid file format → Reject with clear error
- File too large → Reject with size limit
- Missing config → Use defaults (Professional, Technical Users, 8 steps)

---

### Stage 2: FETCH KNOWLEDGE

**Purpose:** Retrieve and extract content from external knowledge sources

**Inputs:**
- List of knowledge URLs from Stage 1

**Processing:**
1. **For each URL** (parallel processing):
   - Send HTTP request (30s timeout)
   - Detect content type (HTML, PDF, text)
   - Extract content:
     - HTML: BeautifulSoup (main content, remove nav/footer)
     - PDF: pypdf (extract text from all pages)
     - Text: Direct content
   - Clean whitespace, normalize
   - Truncate to 100,000 characters
   - Cache for 24 hours
2. Store metadata (URL, title, type, length)
3. Log success/failure per URL

**Outputs:**
- List of knowledge source dictionaries:
  ```python
  {
    "url": "https://learn.microsoft.com/...",
    "title": "Azure OpenAI Deployment Guide",
    "type": "web",
    "content": "When configuring...",  # up to 100k chars
    "error": None  # or error message if failed
  }
  ```

**Tags:** `[FETCH_KNOWLEDGE]`, `[FETCHED]`, `[ERROR]`, `[CACHED]`

**Performance:**
- Average fetch time: 2-5 seconds per URL
- Parallel fetching: All URLs fetched simultaneously
- Cache hit rate: ~70% (24-hour TTL)

**Error Handling:**
- URL timeout → Log error, continue with other URLs
- Invalid URL → Log error, continue
- Fetch failures don't block processing (graceful degradation)

---

### Stage 3: CLEAN & TOKENIZE

**Purpose:** Normalize transcript text and prepare for chunking

**Inputs:**
- Raw transcript text from Stage 1

**Processing:**
1. **Sentence tokenization** (NLTK)
   - Split on period, exclamation, question marks
   - Handle abbreviations (Dr., Mr., etc.)
   - Preserve sentence boundaries
2. **Text normalization**
   - Remove extra whitespace
   - Normalize punctuation
   - Fix common OCR artifacts (if from PDF)
3. **Build sentence catalog**
   - Index all sentences for source matching
   - Pre-calculate technical scores (for ranking)

**Outputs:**
- List of clean sentences
- Sentence catalog with indices
- Technical scores per sentence

**Tags:** `[CLEAN_TRANSCRIPT]`

**Performance:**
- Processing time: < 1 second (for 5-page transcript)
- Sentence count: Typically 50-200 sentences

---

### Stage 4: SEMANTIC CHUNKING

**Purpose:** Split transcript into N focused chunks (1 chunk → 1 step)

**Inputs:**
- Clean sentence list from Stage 3
- target_steps (N) from configuration

**Processing:**
1. **Calculate chunk boundaries**
   - Total sentences ÷ target_steps = sentences per chunk
   - Ensure 6-12 sentences per chunk (adjust if needed)
2. **Split maintaining semantic continuity**
   - Don't split mid-topic
   - Look for natural boundaries (paragraph breaks, topic shifts)
3. **Balance chunk sizes**
   - No tiny chunks (< 6 sentences)
   - No huge chunks (> 12 sentences)
   - Redistribute if unbalanced

**Outputs:**
- List of N chunks (text strings)
- Average chunk size: 8-9 sentences
- Word count per chunk: 150-250 words

**Tags:** `[CHUNK_TRANSCRIPT]`

**Example:**
```
Input: 80 sentences, target_steps=10
→ 80 ÷ 10 = 8 sentences/chunk
→ Create 10 chunks with 8 sentences each
→ Adjust boundaries for semantic continuity
```

---

### Stage 5: GENERATE STEPS (The Core Loop)

**Purpose:** Generate ONE training step per chunk using LLM + knowledge

**Inputs (per chunk):**
- Transcript chunk (6-12 sentences)
- Knowledge sources (from Stage 2)
- Configuration (tone, audience, step index)

**Sub-Stages:**

#### 5.1 Semantic Search
- **Model:** sentence-transformers (all-MiniLM-L6-v2)
- **Process:**
  1. Encode chunk → embedding vector (384 dims)
  2. Split each knowledge source into 500-char overlapping excerpts
  3. Encode each excerpt → embedding vector
  4. Calculate cosine similarity: chunk ↔ excerpt
  5. Filter excerpts with similarity < 0.1
  6. Sort by similarity (descending)
  7. Select top 5 excerpts overall

- **Output:** Top 5 relevant excerpts with scores
  ```python
  [
    {
      "source_title": "Azure Deployment Guide",
      "source_url": "https://...",
      "excerpt": "When configuring deployment capacity...",
      "relevance_score": 0.87
    },
    ...
  ]
  ```

#### 5.2 Prompt Construction
- **Template:** Chunk-focused prompt
- **Components:**
  - System instructions (grounding rules)
  - Transcript chunk (quoted)
  - Top 5 knowledge excerpts (with scores)
  - DO/DON'T instructions
  - Output format specification

#### 5.3 LLM Generation
- **Model:** Azure OpenAI (gpt-4o) or OpenAI (gpt-4o-mini fallback)
- **Parameters:**
  - Temperature: 0.2 (focused, consistent)
  - Max tokens: 1000
  - Top-p: 0.85
  - Timeout: 60s

- **Output:** Single training step (JSON)
  ```python
  {
    "title": "Configure Deployment Settings",
    "summary": "Navigate to Deployments section...",
    "details": "In the Azure Portal, access...",
    "actions": ["Navigate to...", "Click Create..."]
  }
  ```

**Performance (per chunk):**
- Semantic search: ~1 second
- Prompt construction: < 0.1 second
- LLM call: ~3-5 seconds
- Total: ~4-6 seconds per step

**Total for 10 steps:** 40-60 seconds

**Tags:** `[GENERATE_STEPS]`, `[SEMANTIC_MATCH]`, `[HIGH_RELEVANCE]`

**Error Handling:**
- LLM timeout → Retry once, then skip chunk
- Invalid response → Skip chunk, log error
- Continue with remaining chunks (graceful degradation)

---

### Stage 6: VALIDATE & SCORE (Quality Gate)

**Purpose:** Calculate confidence and validate each step meets quality threshold

**Inputs (per step):**
- Generated step from Stage 5
- Transcript sentences (from Stage 3)
- Knowledge sources (from Stage 2)

**Sub-Stages:**

#### 6.1 Source Matching
- **Process:**
  1. Search transcript for sentences matching step content
  2. Calculate hybrid similarity:
     - 50% word overlap (Jaccard: |A∩B| / |A∪B|)
     - 50% semantic similarity (sentence-transformers)
  3. Require minimum 3 matching words
  4. Require similarity ≥ 0.15
  5. Select top 5 transcript sources
  6. Match knowledge sources (if cited in step)

- **Output:** List of sources per step
  ```python
  [
    SourceReference(
      type="transcript",
      excerpt="Navigate to Deployments section...",
      sentence_index=42,
      confidence=0.68
    ),
    SourceReference(
      type="knowledge",
      excerpt="Microsoft recommends 10K TPM...",
      confidence=0.87
    )
  ]
  ```

#### 6.2 Confidence Calculation
- **Formula:** Multi-factor multiplicative scoring
  1. **Base score:** Weighted average of top 3 sources
     - Source 1: weight 50%
     - Source 2: weight 30%
     - Source 3: weight 20%
  2. **Multiplicative bonuses:**
     - ×1.25 for 4+ sources
     - ×1.15 for 3 sources
     - ×1.08 for 2 sources
     - ×1.12 for diverse sources (transcript + knowledge)
     - ×1.10 for high confidence source (>0.5)
  3. **Clamp:** [0.0, 1.0]

- **Confidence levels:**
  - Very High: 0.75+ (Excellent grounding)
  - High: 0.55-0.74 (Strong grounding)
  - Medium: 0.35-0.54 (Acceptable)
  - Low: 0.20-0.34 (Weak)
  - Very Low: <0.20 (Rejected)

#### 6.3 Validation Gate
- **Requirements:**
  1. Confidence ≥ 0.4
  2. Has ≥1 transcript source
  3. Has ≥1 source overall

- **Decision:**
  - **PASS:** All requirements met → `[VALIDATED]`
  - **FAIL:** Any requirement not met → `[REJECTED]`

- **Final gate:**
  - IF valid_steps < 1 → FAIL entire job
  - ELSE → Proceed to Stage 7

**Performance:**
- Source matching: ~0.5 seconds per step
- Confidence calculation: < 0.1 second
- Total: ~0.6 seconds per step × 10 = 6 seconds

**Tags:** `[BUILD_SOURCES]`, `[VALIDATE_STEPS]`, `[VALIDATED]`, `[REJECTED]`

**Quality Metrics:**
- Average confidence: 55-65% (typical)
- High confidence rate: 50-70% of steps
- Rejection rate: 0-10% of steps
- Knowledge usage: 70-90% of sources cited

---

### Stage 7: ASSEMBLE DOCUMENT

**Purpose:** Create professional Word document with all validated steps

**Inputs:**
- Valid steps (from Stage 6)
- Step sources (from Stage 6)
- Knowledge sources (from Stage 2)
- Configuration (title, metadata)
- Statistics (tokens, time, confidence)

**Processing:**
1. **Initialize Document** (python-docx)
   - Set fonts (Calibri 11pt)
   - Configure heading styles
   - Set page margins

2. **Add Sections** (in order):
   - Title page (brand, metadata)
   - Table of contents (manual, can be replaced)
   - Introduction (overview, how-to-use)
   - Training steps (main content)
   - Source references (appendix)
   - Knowledge sources (appendix)
   - Document statistics (metrics)

3. **Format Each Step:**
   ```
   Step N: [Title]

   📋 Overview: [Summary]

   [Details with knowledge enhancements]

   ✅ Key Actions:
   1. [Action]
   2. [Action]

   Quality Indicator: High (68%) | Sources: transcript (3), knowledge (2)
   ```

4. **Add Source References:**
   - Full transcript excerpts (quoted)
   - Knowledge source excerpts (with URLs)
   - Confidence scores per source
   - Icons: 📄 (transcript) 🌐 (knowledge)

5. **Add Statistics Table:**
   - Total steps, confidence, tokens, cost
   - Knowledge usage metrics
   - Processing time

**Outputs:**
- Professional .docx file (~15-20 pages for 10 steps)
- Upload to Azure Blob Storage
- Return download URL to user

**Performance:**
- Document generation: ~5-10 seconds
- File size: ~50-150 KB

**Tags:** `[CREATE_DOCUMENT]`, `[COMPLETE]`

---

## Processing Tags Reference

### Status Tags
| Tag | Meaning |
|-----|---------|
| `[INIT]` | Pipeline initialized |
| `[LOAD_TRANSCRIPT]` | Loading transcript file |
| `[FETCH_KNOWLEDGE]` | Fetching knowledge URLs |
| `[CLEAN_TRANSCRIPT]` | Cleaning and normalizing text |
| `[CHUNK_TRANSCRIPT]` | Splitting into chunks |
| `[GENERATE_STEPS]` | Generating steps from chunks |
| `[BUILD_SOURCES]` | Finding source references |
| `[VALIDATE_STEPS]` | Validating step quality |
| `[CREATE_DOCUMENT]` | Assembling Word document |
| `[COMPLETE]` | Processing finished successfully |
| `[ERROR]` | Fatal error occurred |

### Knowledge Tags
| Tag | Meaning |
|-----|---------|
| `[FETCHED]` | Successfully fetched from URL |
| `[CACHED]` | Using cached content (< 24 hours old) |
| `[SEMANTIC_MATCH]` | Using semantic similarity |
| `[KEYWORD_MATCH]` | Using keyword matching (fallback) |
| `[HIGH_RELEVANCE]` | Excerpt score ≥ 0.5 |
| `[MEDIUM_RELEVANCE]` | Excerpt score 0.2-0.49 |
| `[LOW_RELEVANCE]` | Excerpt score 0.1-0.19 |
| `[FILTERED]` | Excerpt below threshold (< 0.1) |

### Quality Tags
| Tag | Meaning |
|-----|---------|
| `[HIGH_CONFIDENCE]` | Step confidence ≥ 0.7 |
| `[MEDIUM_CONFIDENCE]` | Step confidence 0.4-0.69 |
| `[LOW_CONFIDENCE]` | Step confidence < 0.4 (rejected) |
| `[TRANSCRIPT_GROUNDED]` | Has transcript sources |
| `[KNOWLEDGE_ENHANCED]` | Has knowledge sources |
| `[VALIDATED]` | Passed all quality gates |
| `[REJECTED]` | Failed validation |

---

## Performance Metrics (10-Step Document)

| Metric | Value |
|--------|-------|
| **Total Processing Time** | 45-65 seconds |
| Stage 1 (Load) | < 1 second |
| Stage 2 (Fetch Knowledge) | 2-5 seconds |
| Stage 3 (Clean) | < 1 second |
| Stage 4 (Chunk) | < 1 second |
| Stage 5 (Generate) | 40-60 seconds |
| Stage 6 (Validate) | 5-8 seconds |
| Stage 7 (Assemble) | 5-10 seconds |
| **Total Tokens** | 6,000-8,000 |
| Input tokens/step | ~450 |
| Output tokens/step | ~200 |
| **Estimated Cost** | $0.0015-0.0025 |
| GPT-4o ($0.15/1M in, $0.60/1M out) | - |
| **Average Confidence** | 55-65% (High) |
| **Knowledge Usage** | 70-90% |

---

## Key Innovations

### 1. Chunk-Level Knowledge Matching
**Traditional RAG:**
- Sends entire knowledge base to every query
- Same context for all steps
- High token usage

**ScriptToDoc Pipeline:**
- Semantic search finds top 5 excerpts per chunk
- Different context per step
- 60% token savings

### 2. Iterative Quality Loop
**Per-Chunk Process:**
```
Chunk → Semantic Search → LLM Generate → Source Match → Confidence Score → Validate
  ↓                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
  IF confidence ≥ 0.4: PASS → Include in document
  IF confidence < 0.4: FAIL → Reject (log warning)
```

### 3. Multiplicative Confidence Scoring
- Prevents low-quality steps from passing with bonuses
- Rewards truly high-quality steps
- Text-only (visual support excluded)

### 4. Graceful Error Recovery
- Knowledge fetch failures don't block processing
- LLM failures skip chunk, continue others
- Validates ≥1 step generated (no empty documents)

---

## Error Handling Strategy

| Error Type | Stage | Recovery |
|------------|-------|----------|
| Invalid file | Stage 1 | Reject with clear message |
| Knowledge URL timeout | Stage 2 | Log error, continue with other URLs |
| LLM timeout | Stage 5 | Retry once, then skip chunk |
| All chunks failed | Stage 5 | FAIL job with root cause |
| All steps rejected | Stage 6 | FAIL job with detailed reason |
| Document generation error | Stage 7 | FAIL job, preserve intermediate data |

**Philosophy:** Fail fast with clear errors, but continue when possible (graceful degradation)

---

## Monitoring & Debugging

### Backend Logs (by Stage)

**Stage 2 (Fetch):**
```
INFO - Fetching knowledge from 2 URLs
INFO - Fetched https://learn.microsoft.com/... (15234 chars)
INFO - Fetched https://docs.azure.com/... (22156 chars)
INFO - Successfully fetched 2/2 knowledge sources
```

**Stage 4 (Chunk):**
```
INFO - Created 10 chunks (avg 8.3 sentences/chunk)
```

**Stage 5 (Generate):**
```
INFO - Generating step 1/10 from chunk (542 chars)
INFO - [SEMANTIC_MATCH] Found 5 relevant excerpts (max relevance: 0.87)
INFO - Generated step 1: "Configure Azure OpenAI Deployment"
```

**Stage 6 (Validate):**
```
INFO - Step 1: Confidence 0.68 (High), 5 sources, valid: True
INFO - Step 2: Confidence 0.72 (High), 4 sources, valid: True
...
INFO - Validated: 10/10 steps passed
```

**Stage 7 (Assemble):**
```
INFO - Creating Word document with 10 steps
INFO - Document saved to: output/training_document.docx
```

### Frontend Progress

```
⏳ Loading transcript... (5%)
⏳ Fetching knowledge sources... (20%)
⏳ Cleaning transcript... (30%)
⏳ Chunking transcript... (40%)
⏳ Generating steps... (60%)
   └─ Generating step 3 of 10
⏳ Validating steps... (85%)
⏳ Creating document... (95%)
✅ Document generated successfully! (100%)
```

---

## Summary: 7-Stage Pipeline

The ScriptToDoc agent is **not just a two-phase system** - it's a sophisticated **7-stage pipeline** where each stage builds on the previous:

1. **LOAD & VALIDATE** - Accept and verify inputs ✋ (User control)
2. **FETCH KNOWLEDGE** - Retrieve external sources (Parallel, cached)
3. **CLEAN & TOKENIZE** - Normalize transcript (NLTK, indexing)
4. **SEMANTIC CHUNKING** - Split into focused chunks (N chunks → N steps)
5. **GENERATE STEPS** - **Core iterative loop** (Search → Generate → per chunk) 🔄
6. **VALIDATE & SCORE** - **Quality gate** (Match → Score → Validate) 🔍
7. **ASSEMBLE DOCUMENT** - Professional output (Word .docx, 15-20 pages)

**The result:** High-quality training documents that are grounded in transcripts, enhanced with expert knowledge, and validated for confidence—all automatically in 45-65 seconds.
