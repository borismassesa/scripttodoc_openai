# Phase 1 Implementation Plan: Intelligent Parser & Topic Segmentation

**Date:** December 2, 2025
**Status:** 📋 Planning
**Timeline:** Weeks 1-2 (estimated 10-15 days)
**Dependencies:** Week 0 ✅ Complete

---

## Executive Summary

Phase 1 transforms ScriptToDoc from **arbitrary text chunking** to **intelligent conversation analysis**. By parsing transcript structure and identifying natural topic boundaries, we'll generate more coherent, contextually-aware training steps.

**Key Changes:**
1. **Parse transcripts** to extract metadata (speakers, timestamps, questions)
2. **Segment by topics** using semantic and conversational signals (not word count)
3. **Generate steps** from coherent topics (not arbitrary chunks)

**Expected Impact:**
- ⬆️ **Step coherence**: +40-60% (topics stay together)
- ⬇️ **Token usage**: -20-30% (fewer, better-quality chunks)
- ⬆️ **Confidence scores**: +15-25% (better grounding)
- ⬆️ **User satisfaction**: Natural conversation flow preserved

---

## Current State Analysis

### How It Works Now

**Pipeline Flow:**
```
Transcript (raw)
  ↓
TranscriptCleaner.normalize()  [removes ALL metadata: timestamps, speakers]
  ↓
TranscriptChunker.chunk_smart()  [splits by sentence count or paragraph boundaries]
  ↓
Steps generated from arbitrary chunks  [may mix unrelated topics]
```

**Example Problem:**
```
Chunk 3 (arbitrary 150-word split):
"...and that's how you create a resource group. [Speaker 2]: Great question!
The pricing depends on... [Speaker 1]: Now let's move on to deploying web apps.
First, navigate to App Service..."

Result: Step 3 mixes THREE topics (resource groups, pricing, web apps) ❌
```

### What Phase 1 Will Change

**New Pipeline Flow:**
```
Transcript (raw)
  ↓
TranscriptParser.parse()  [preserves metadata, identifies sentence types]
  ↓
TranscriptCleaner (enhanced)  [cleans but preserves structure]
  ↓
TopicSegmenter.segment()  [groups by semantic coherence + conversation signals]
  ↓
Steps generated from coherent topics  [natural conversation flow]
```

**After Phase 1:**
```
Topic 1: "Creating Resource Groups" (sentences 5-15, Speaker 1, 2min)
Topic 2: "Pricing Discussion" (sentences 16-20, Speaker 2 Q&A, 30sec) → FILTERED
Topic 3: "Deploying Web Apps" (sentences 21-35, Speaker 1, 3min)

Result: Step 1 = Resource Groups, Step 2 = Web Apps ✅
```

---

## Architecture Design

### Option A: Parse-First Architecture (RECOMMENDED)

**Rationale:**
- Aligns with v2.0 spec
- Clean separation of concerns
- Enables future enhancements (Q&A filtering, ranking)
- More testable and maintainable

**New Components:**

#### 1. TranscriptParser (`transcript_parser.py`)

**Purpose:** Parse raw transcript into structured sentences with metadata

**Data Structures:**
```python
@dataclass
class ParsedSentence:
    """A single parsed sentence with metadata."""
    text: str                           # Cleaned sentence text
    raw_text: str                       # Original text (with timestamps, etc.)
    sentence_index: int                 # 0-based index in transcript
    timestamp: Optional[float]          # Seconds from start (e.g., 65.0 for [00:01:05])
    speaker: Optional[str]              # e.g., "Speaker 1", "John"
    speaker_role: Optional[str]         # "instructor" or "participant" (heuristic)

    # Sentence characteristics
    is_question: bool                   # Ends with "?" or has question words
    is_transition: bool                 # Contains transition phrases
    has_emphasis: bool                  # Contains emphasis markers

    # Relationships
    follows_long_pause: bool            # >90 seconds since last sentence
    speaker_changed: bool               # Different speaker than previous


@dataclass
class TranscriptMetadata:
    """Overall transcript metadata."""
    total_sentences: int
    total_speakers: int
    duration_seconds: Optional[float]
    primary_speaker: Optional[str]      # Most frequent speaker (likely instructor)
    has_qa_sections: bool               # Contains Q&A patterns
```

**Core Methods:**
```python
class TranscriptParser:
    def parse(self, raw_transcript: str) -> Tuple[List[ParsedSentence], TranscriptMetadata]:
        """
        Parse raw transcript into structured sentences.

        Steps:
        1. Extract timestamps and speakers (BEFORE cleaning)
        2. Split into sentences
        3. Associate metadata with each sentence
        4. Identify sentence characteristics (question, transition, etc.)
        5. Compute relationships (pauses, speaker changes)

        Returns:
            (parsed_sentences, metadata)
        """

    def _extract_timestamp(self, line: str) -> Optional[float]:
        """Extract timestamp from formats: [HH:MM:SS], (HH:MM:SS), etc."""

    def _extract_speaker(self, line: str) -> Optional[str]:
        """Extract speaker from formats: Speaker 1:, JOHN:, [John]:, etc."""

    def _detect_speaker_role(self, speaker: str, sentence_count: int, total: int) -> str:
        """Heuristic: most frequent speaker = instructor, others = participants"""

    def _is_question(self, text: str) -> bool:
        """Check if sentence is a question (ends with ? or has question words)"""

    def _is_transition(self, text: str) -> bool:
        """Check for transition phrases: "Now let's...", "Next...", "Moving on..."
        """
```

**Key Features:**
- ✅ Extracts timestamps in multiple formats
- ✅ Identifies speakers and roles
- ✅ Detects questions, transitions, emphasis
- ✅ Computes pause durations between sentences
- ✅ Preserves metadata for later use

---

#### 2. TopicSegmenter (`topic_segmenter.py`)

**Purpose:** Group parsed sentences into coherent topics using multi-signal analysis

**Data Structures:**
```python
@dataclass
class TopicSegment:
    """A coherent topic segment (group of sentences)."""
    segment_index: int                  # 0-based segment number
    sentences: List[ParsedSentence]     # Sentences in this segment

    # Segment characteristics
    start_timestamp: Optional[float]
    end_timestamp: Optional[float]
    duration_seconds: Optional[float]
    primary_speaker: Optional[str]

    # Topic indicators
    has_transition_start: bool          # Starts with explicit transition
    has_qa_section: bool                # Contains Q&A exchanges
    action_density: float               # Proportion of action verbs (0.0-1.0)

    # Quality metrics
    coherence_score: float              # Internal semantic similarity (0.0-1.0)

    def get_text(self) -> str:
        """Get combined text of all sentences in segment."""
        return ' '.join(s.text for s in self.sentences)


@dataclass
class SegmentationConfig:
    """Configuration for topic segmentation."""

    # Boundary detection thresholds
    max_pause_seconds: float = 90.0     # Long pause = likely topic change
    min_semantic_similarity: float = 0.5  # Below this = topic boundary

    # Segment constraints
    min_sentences_per_segment: int = 3   # Minimum segment size
    max_sentences_per_segment: int = 20  # Maximum segment size

    # Segmentation signals (weighted)
    weight_timestamp_gap: float = 0.3
    weight_speaker_change: float = 0.2
    weight_transition_phrase: float = 0.3
    weight_semantic_similarity: float = 0.2
```

**Core Methods:**
```python
class TopicSegmenter:
    def __init__(self, config: SegmentationConfig = None):
        self.config = config or SegmentationConfig()
        self.sentence_tokenizer = SentenceTokenizer()  # For text processing

    def segment(
        self,
        parsed_sentences: List[ParsedSentence]
    ) -> List[TopicSegment]:
        """
        Segment parsed sentences into coherent topics.

        Uses multi-signal boundary detection:
        1. Timestamp gaps (>90s = likely new topic)
        2. Speaker transitions (instructor resuming after Q&A)
        3. Explicit transitions ("Now let's...", "Next...")
        4. Semantic similarity breaks (embedding-based, optional)

        Returns:
            List of topic segments
        """

    def _compute_boundary_score(
        self,
        sentence1: ParsedSentence,
        sentence2: ParsedSentence
    ) -> float:
        """
        Compute likelihood that a boundary exists between two sentences.

        Returns score 0.0-1.0 (higher = more likely boundary)

        Factors:
        - Timestamp gap (>90s = +0.3)
        - Speaker change from participant back to instructor (+0.2)
        - Transition phrase in sentence2 (+0.3)
        - Low semantic similarity (+0.2)
        """

    def _is_topic_boundary(self, boundary_score: float) -> bool:
        """Determine if boundary score indicates topic change (threshold: 0.5)"""

    def _merge_small_segments(
        self,
        segments: List[TopicSegment]
    ) -> List[TopicSegment]:
        """Merge segments with <3 sentences into adjacent segments"""

    def _compute_coherence(self, sentences: List[ParsedSentence]) -> float:
        """Compute internal coherence of a segment (optional: use embeddings)"""

    def _compute_action_density(self, sentences: List[ParsedSentence]) -> float:
        """Compute proportion of sentences with strong action verbs"""
```

**Segmentation Algorithm:**
```
1. Initialize: boundary_scores = []
2. For each consecutive sentence pair:
   a. Compute boundary score (0.0-1.0)
   b. If score > 0.5: mark as boundary
3. Split into segments at boundaries
4. Merge segments with <3 sentences
5. Compute segment metadata (duration, coherence, etc.)
6. Return TopicSegment[]
```

**Key Features:**
- ✅ Multi-signal boundary detection (timestamps, speakers, phrases, semantics)
- ✅ Configurable thresholds and weights
- ✅ Handles edge cases (no timestamps, single speaker, etc.)
- ✅ Merges small segments for quality
- ✅ Computes segment quality metrics

---

#### 3. Pipeline Integration

**Modified `pipeline.py` Flow:**

```python
# Step 1: Parse transcript (NEW)
logger.info("Step 1: Parsing transcript")
parsed_sentences, transcript_metadata = self.transcript_parser.parse(transcript_text)
logger.info(f"Parsed {len(parsed_sentences)} sentences, "
            f"{transcript_metadata.total_speakers} speakers, "
            f"{transcript_metadata.duration_seconds}s duration")

# Step 2: Clean transcript (MODIFIED - preserve structure)
logger.info("Step 2: Cleaning transcript")
cleaned_sentences = []
for sentence in parsed_sentences:
    # Clean the text but keep the ParsedSentence structure
    cleaned_text = self.transcript_cleaner.normalize(sentence.text)
    sentence.text = cleaned_text
    cleaned_sentences.append(sentence)

# Step 3: Segment into topics (NEW)
logger.info("Step 3: Segmenting into topics")
topic_segments = self.topic_segmenter.segment(cleaned_sentences)
logger.info(f"Identified {len(topic_segments)} topic segments")

# Log segment details
for i, segment in enumerate(topic_segments, 1):
    logger.info(
        f"  Segment {i}: {len(segment.sentences)} sentences, "
        f"{segment.duration_seconds:.1f}s, "
        f"coherence={segment.coherence_score:.2f}"
    )

# Step 4: Generate steps from topic segments (MODIFIED)
logger.info("Step 4: Generating training steps from topic segments")
target_steps = min(len(topic_segments), self.config.target_steps)

steps = []
for i, segment in enumerate(topic_segments[:target_steps], 1):
    chunk_text = segment.get_text()

    step, usage = self.azure_openai.generate_step_from_chunk(
        chunk=chunk_text,
        chunk_index=i,
        total_chunks=target_steps,
        tone=self.config.tone,
        audience=self.config.audience,
        knowledge_sources=knowledge_sources
    )

    steps.append(step)
    # ... token tracking ...

# Steps 5-7: Unchanged (source references, validation, document generation)
```

**Key Changes:**
1. **Step 1 (NEW):** Parse transcript → `ParsedSentence[]`
2. **Step 2 (MODIFIED):** Clean preserving structure
3. **Step 3 (NEW):** Segment into topics → `TopicSegment[]`
4. **Step 4 (MODIFIED):** Generate from topics (not arbitrary chunks)

---

### Option B: Lightweight Enhancement (Alternative)

**Rationale:**
- Faster to implement (~5 days)
- Less refactoring
- Incrementally improves current architecture

**Approach:**
1. Keep existing `TranscriptCleaner` as-is
2. Add metadata extraction step BEFORE cleaning
3. Store metadata separately in a parallel structure
4. Enhance `TranscriptChunker` with topic-aware logic
5. Use metadata hints for better chunking

**Pros:**
- ✅ Minimal disruption to existing code
- ✅ Can deploy incrementally
- ✅ Lower risk

**Cons:**
- ❌ Less elegant architecture
- ❌ Harder to extend for Phase 2 (Q&A filtering, ranking)
- ❌ Metadata management is scattered
- ❌ Doesn't fully align with v2.0 spec

---

## Recommended Approach: Option A (Parse-First)

**Why:**
1. **Aligns with spec:** v2.0 architecture requires parsed structure
2. **Enables Phase 2:** Q&A filtering and ranking need metadata
3. **Cleaner design:** Separation of concerns, testable components
4. **Future-proof:** Easier to add features (speaker roles, emphasis, etc.)
5. **Better quality:** Full metadata enables smarter segmentation

**Trade-offs:**
- ⏱️ Takes 2 weeks instead of 1 week
- 🔧 More refactoring required
- 🧪 More comprehensive testing needed

**Mitigation:**
- Implement incrementally (parser first, then segmenter)
- Add feature flag for easy rollback
- Keep `TranscriptChunker` as fallback

---

## Implementation Tasks

### Week 1: Transcript Parser (Days 1-5)

**Day 1-2: Core Parser Implementation**
- [ ] Create `transcript_parser.py`
- [ ] Implement `ParsedSentence` and `TranscriptMetadata` dataclasses
- [ ] Implement `TranscriptParser` class:
  - [ ] `_extract_timestamp()` - multiple format support
  - [ ] `_extract_speaker()` - multiple format support
  - [ ] `parse()` - main parsing logic
- [ ] Write unit tests for timestamp/speaker extraction
- [ ] Test with sample_meeting.txt

**Day 3: Sentence Analysis**
- [ ] Implement `_is_question()` detection
- [ ] Implement `_is_transition()` detection
- [ ] Implement `_detect_speaker_role()` heuristic
- [ ] Compute pause durations and speaker changes
- [ ] Write unit tests for detection logic
- [ ] Test with multiple transcript formats

**Day 4: Integration Prep**
- [ ] Modify `TranscriptCleaner` to accept structured input
- [ ] Add `clean_parsed_sentence()` method
- [ ] Update pipeline to call parser first
- [ ] Add feature flag: `use_intelligent_parsing` (default: False)
- [ ] Test end-to-end with parser enabled

**Day 5: Testing & Validation**
- [ ] Create comprehensive test suite
- [ ] Test edge cases (no timestamps, single speaker, etc.)
- [ ] Validate parser output quality
- [ ] Document parser API and usage
- [ ] Code review and refinement

**Deliverable:** Working transcript parser that extracts metadata

---

### Week 2: Topic Segmentation (Days 6-10)

**Day 6-7: Core Segmenter Implementation**
- [ ] Create `topic_segmenter.py`
- [ ] Implement `TopicSegment` and `SegmentationConfig` dataclasses
- [ ] Implement `TopicSegmenter` class:
  - [ ] `_compute_boundary_score()` - multi-signal analysis
  - [ ] `_is_topic_boundary()` - threshold check
  - [ ] `segment()` - main segmentation logic
- [ ] Write unit tests for boundary detection
- [ ] Test with sample_meeting.txt

**Day 8: Segment Quality**
- [ ] Implement `_merge_small_segments()`
- [ ] Implement `_compute_coherence()` (simple version)
- [ ] Implement `_compute_action_density()`
- [ ] Add segment metadata computation
- [ ] Write unit tests for quality metrics
- [ ] Test segment quality with various thresholds

**Day 9: Pipeline Integration**
- [ ] Update `pipeline.py` to use topic segmenter
- [ ] Replace `chunk_smart()` call with `segment()` call
- [ ] Update progress tracking for new steps
- [ ] Add logging for segment details
- [ ] Add feature flag: `use_topic_segmentation` (default: False)
- [ ] Test end-to-end with segmentation enabled

**Day 10: Testing & Validation**
- [ ] Create comprehensive test suite
- [ ] Compare topic-based vs sentence-based chunking
- [ ] Measure quality improvements:
  - Coherence scores
  - Token usage
  - Step confidence
  - User perception (manual review)
- [ ] Document segmenter API and configuration
- [ ] Code review and refinement

**Deliverable:** Working topic segmentation with quality improvements

---

## Testing Strategy

### Unit Tests

**Parser Tests:**
```python
def test_parse_timestamp_formats():
    """Test extraction of [HH:MM:SS], (HH:MM:SS), etc."""

def test_parse_speaker_formats():
    """Test extraction of 'Speaker 1:', '[John]:', etc."""

def test_detect_questions():
    """Test question detection (? or question words)"""

def test_detect_transitions():
    """Test transition phrase detection"""

def test_compute_pauses():
    """Test pause duration calculation"""
```

**Segmenter Tests:**
```python
def test_boundary_detection():
    """Test multi-signal boundary scoring"""

def test_topic_segmentation():
    """Test end-to-end segmentation"""

def test_merge_small_segments():
    """Test segment merging logic"""

def test_coherence_computation():
    """Test coherence scoring"""
```

### Integration Tests

**End-to-End Tests:**
```python
def test_parse_and_segment_sample_meeting():
    """Test full pipeline with sample_meeting.txt"""

def test_phase1_vs_baseline():
    """Compare Phase 1 output vs baseline (Week 0)"""
```

### Quality Metrics

**Compare Phase 1 vs Baseline:**
| Metric | Baseline (Week 0) | Phase 1 Target |
|--------|-------------------|----------------|
| **Topic Coherence** | ~50% (subjective) | ~90% |
| **Steps Mix Topics** | ~40% of steps | <10% of steps |
| **Token Usage** | 8,430 tokens | ~6,000 tokens (-29%) |
| **Avg Confidence** | 0.34 | 0.45 (+32%) |
| **Processing Time** | 28.8s | ~25s (-13%) |

---

## Rollback Plan

**If Phase 1 has issues:**

### Quick Rollback (5 minutes)
1. Set feature flags to False:
   ```python
   use_intelligent_parsing = False
   use_topic_segmentation = False
   ```
2. Pipeline automatically falls back to Week 0 behavior
3. No code changes needed

### Keep Components
- Parser and segmenter remain in codebase
- Can be improved and re-enabled later
- Useful for analytics and debugging

---

## Migration Path

**Phase 0 → Phase 1 → Phase 2:**

```
Week 0 (Current):
├─ Arbitrary chunking (sentence count)
├─ No metadata preserved
└─ Week 0 prompt improvements ✅

Phase 1 (Weeks 1-2):
├─ Intelligent parsing (metadata extraction) ✅
├─ Topic segmentation (multi-signal) ✅
└─ Coherent chunks → better steps

Phase 2 (Weeks 3-4):
├─ Q&A filtering (uses parser metadata)
├─ Topic ranking (uses segment quality)
└─ Step validation (enhanced)
```

**Backward Compatibility:**
- ✅ All Phase 1 features are opt-in (feature flags)
- ✅ Existing API contracts unchanged
- ✅ Can deploy incrementally (parser first, then segmenter)
- ✅ Easy rollback if needed

---

## Success Criteria

**Phase 1 is successful if:**

1. ✅ **Parser extracts metadata correctly** (timestamps, speakers, questions)
2. ✅ **Topics align with conversation flow** (90%+ coherence)
3. ✅ **Steps don't mix unrelated topics** (<10% mixed)
4. ✅ **Token usage decreases** (20-30% reduction)
5. ✅ **Confidence scores improve** (+15-25%)
6. ✅ **No breaking changes** to existing functionality
7. ✅ **All tests pass** (unit, integration, end-to-end)

---

## Risks & Mitigation

### Risk 1: Transcripts without timestamps/speakers
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Parser handles missing metadata gracefully
- Falls back to sentence-based analysis
- Uses transition phrases as primary signal
- Keeps `TranscriptChunker` as fallback

### Risk 2: Semantic similarity computation is slow
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Make semantic similarity optional
- Use simple keyword/phrase matching as primary signal
- Only use embeddings if performance allows
- Cache embeddings for repeated use

### Risk 3: Over-segmentation (too many small topics)
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Tune boundary thresholds conservatively
- Implement segment merging logic
- Add minimum segment size constraint
- Configurable thresholds for adjustment

### Risk 4: Integration breaks existing functionality
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Feature flags for gradual rollout
- Comprehensive test coverage
- Keep baseline implementation as fallback
- Staged deployment (parser → segmenter)

---

## Next Steps

**Immediate (After Plan Approval):**
1. ✅ Review and approve this plan
2. ⏳ Create feature branch: `feature/phase1-parser-segmenter`
3. ⏳ Set up test environment with sample transcripts
4. ⏳ Begin Day 1: Core Parser Implementation

**Week 1 Checkpoints:**
- Day 2: Parser core complete, timestamp/speaker extraction working
- Day 4: Parser integrated, tests passing
- Day 5: Week 1 deliverable ready (working parser)

**Week 2 Checkpoints:**
- Day 7: Segmenter core complete, boundary detection working
- Day 9: Segmenter integrated, pipeline updated
- Day 10: Phase 1 complete, quality metrics validated

---

## Open Questions

**For User to Decide:**

1. **Semantic similarity:** Use embeddings (slower, more accurate) or keyword matching (faster, less accurate)?
   - Recommendation: Start with keyword matching, add embeddings in Phase 2 if needed

2. **Feature flag strategy:** Enable by default or opt-in?
   - Recommendation: Opt-in initially (default: False), enable by default after 1 week of testing

3. **Minimum segment size:** 3 sentences (current) or different threshold?
   - Recommendation: Start with 3, tune based on quality metrics

4. **Deploy incrementally or all at once?**
   - Recommendation: Incremental (parser in Week 1, segmenter in Week 2)

---

**Plan Status:** 📋 Ready for Review and Approval
**Prepared By:** Claude (AI Assistant)
**Review Required:** Product Owner / Engineering Lead
**Next Action:** Approve plan and begin implementation
