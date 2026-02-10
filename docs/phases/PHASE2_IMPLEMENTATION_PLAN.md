# Phase 2 Implementation Plan: Quality Gates & Intelligence

## Summary

Build on Phase 1's intelligent parsing and segmentation by adding **quality gates** to filter noise, rank topics, and validate output quality.

**Goal:** Ensure only high-quality, procedural steps make it into the final document

**Expected Impact:**
- Avg confidence: 0.36 → 0.50+ (+40%)
- Q&A noise: Present → Filtered out
- High confidence steps: Unknown → 50%+ with >0.7 score
- Step quality: Inconsistent → Validated and guaranteed

---

## Architecture Overview

### Phase 1 Flow (Current)
```
Raw Transcript
    ↓
Parse (metadata extraction)
    ↓
Segment (topic boundaries)
    ↓
Generate Steps (one per segment)
    ↓
Document
```

### Phase 2 Flow (Enhanced)
```
Raw Transcript
    ↓
Parse (metadata extraction)
    ↓
Segment (topic boundaries)
    ↓
**Filter Q&A Sections** ← NEW
    ↓
**Rank Topics by Importance** ← NEW
    ↓
Generate Steps (from top-ranked segments)
    ↓
**Validate Step Quality** ← NEW
    ↓
**Enhanced Confidence Scoring** ← NEW
    ↓
Document
```

---

## Components to Build

### 1. Q&A Filter (`backend/script_to_doc/qa_filter.py`)

**Purpose:** Identify and filter out Q&A sections from procedural content

**Why Phase 1 enables this:** Parser now tracks `is_question`, `speaker`, and `speaker_role`

**Data Structures:**
```python
@dataclass
class QASection:
    segment_index: int
    start_sentence_index: int
    end_sentence_index: int
    question_count: int
    is_qa_dense: bool  # >50% questions
    primary_speaker: str

@dataclass
class FilterConfig:
    min_qa_density: float = 0.3  # 30% questions = Q&A section
    filter_qa_sections: bool = True
    keep_instructor_only: bool = True  # Keep only instructor-led content
```

**Key Methods:**
```python
class QAFilter:
    def identify_qa_sections(self, segments: List[TopicSegment]) -> List[QASection]
    def filter_segments(self, segments: List[TopicSegment]) -> List[TopicSegment]
    def compute_qa_density(self, segment: TopicSegment) -> float
```

**Algorithm:**
1. For each segment, compute Q&A density (% of questions)
2. Identify sections with >30% questions as Q&A
3. Filter out Q&A-dense segments (configurable)
4. Optionally keep only instructor-led segments

---

### 2. Topic Ranker (`backend/script_to_doc/topic_ranker.py`)

**Purpose:** Rank segments by importance/procedural value

**Why Phase 1 enables this:** Segments now have coherence scores, speaker info, metadata

**Data Structures:**
```python
@dataclass
class TopicScore:
    segment_index: int
    importance_score: float  # 0.0-1.0
    procedural_score: float  # 0.0-1.0
    action_density: float    # actions per sentence
    combined_score: float    # weighted combination

@dataclass
class RankingConfig:
    weight_procedural: float = 0.4
    weight_coherence: float = 0.3
    weight_action_density: float = 0.3
    min_importance_threshold: float = 0.3
```

**Key Methods:**
```python
class TopicRanker:
    def score_segments(self, segments: List[TopicSegment]) -> List[TopicScore]
    def rank_by_importance(self, segments: List[TopicSegment]) -> List[TopicSegment]
    def filter_low_importance(self, segments: List[TopicSegment], threshold: float) -> List[TopicSegment]
```

**Scoring Algorithm:**
```python
importance_score = (
    procedural_score * 0.4 +      # Has action verbs, instructions
    coherence_score * 0.3 +        # Topic coherence
    action_density * 0.3           # Actions per sentence
)
```

---

### 3. Enhanced Step Validator (`backend/script_to_doc/step_validator.py`)

**Purpose:** Validate step quality with detailed checks

**Builds on:** Phase 1's action validation, adds more rules

**Data Structures:**
```python
@dataclass
class ValidationResult:
    step_index: int
    passed: bool
    confidence: float
    issues: List[str]         # ["no_actions", "low_confidence", ...]
    suggestions: List[str]     # Auto-fix suggestions

@dataclass
class ValidationConfig:
    min_actions: int = 2
    min_confidence: float = 0.25
    require_title: bool = True
    require_details: bool = True
    max_title_length: int = 100
```

**Key Methods:**
```python
class StepValidator:
    def validate_step(self, step: Dict, source_data: StepSourceData) -> ValidationResult
    def validate_batch(self, steps: List[Dict], sources: List[StepSourceData]) -> List[ValidationResult]
    def suggest_fixes(self, step: Dict, issues: List[str]) -> List[str]
```

**Validation Rules:**
1. **Structure:** Has title, details, actions
2. **Content:** Title is descriptive, details are substantive
3. **Actions:** At least 2 actions, properly formatted
4. **Confidence:** Meets minimum threshold
5. **Grounding:** Has transcript sources
6. **Quality:** No generic/vague content

---

### 4. Embeddings Similarity (Optional Enhancement)

**Purpose:** Replace keyword matching with semantic embeddings

**Current:** Phase 1 uses simple keyword overlap (Jaccard similarity)
**Upgrade:** Use sentence embeddings for better semantic understanding

**Integration Point:** `topic_segmenter.py` → `_compute_semantic_similarity_score()`

**Implementation:**
```python
# Option 1: sentence-transformers (all-MiniLM-L6-v2)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([sent1.text, sent2.text])
similarity = cosine_similarity(embeddings[0], embeddings[1])

# Option 2: OpenAI embeddings (more expensive, more accurate)
response = openai.Embedding.create(
    input=[sent1.text, sent2.text],
    model="text-embedding-3-small"
)
```

**Trade-offs:**
- **Pros:** More accurate similarity, better boundary detection
- **Cons:** Slower (~50-100ms per comparison), requires additional dependencies
- **Recommendation:** Start with sentence-transformers, upgrade to OpenAI if needed

---

## Implementation Timeline

### Week 1: Q&A Filtering & Topic Ranking

**Day 1-2: Q&A Filter**
- Create `qa_filter.py` with QASection/FilterConfig
- Implement Q&A density computation
- Implement section identification
- Unit tests (15+ tests)

**Day 3-4: Topic Ranker**
- Create `topic_ranker.py` with TopicScore/RankingConfig
- Implement importance scoring algorithm
- Implement ranking and filtering
- Unit tests (15+ tests)

**Day 5: Integration**
- Add to pipeline after segmentation
- Add feature flags: `use_qa_filtering`, `use_topic_ranking`
- Integration tests

**Deliverable:** Pipeline filters Q&A and ranks topics

---

### Week 2: Step Validation & Enhanced Confidence

**Day 6-7: Step Validator**
- Create `step_validator.py` with ValidationResult/ValidationConfig
- Implement validation rules
- Implement auto-fix suggestions
- Unit tests (20+ tests)

**Day 8: Enhanced Confidence**
- Upgrade confidence calculation with validation scores
- Add quality indicators (high/medium/low)
- Update source_reference.py

**Day 9: Pipeline Integration**
- Integrate validator after step generation
- Update validation flow with Phase 2 checks
- Add feature flag: `use_enhanced_validation`

**Day 10: End-to-End Testing**
- Test full Phase 2 pipeline
- Compare metrics: Phase 1 vs Phase 2
- Document improvements
- Create Phase 2 completion report

**Deliverable:** Complete Phase 2 with quality gates

---

### Optional: Embeddings (Week 3)

**Day 11-12: Embeddings Integration**
- Add sentence-transformers to requirements.txt
- Implement embeddings-based similarity
- Cache embeddings for performance
- A/B test: keyword vs embeddings

**Day 13-14: Optimization**
- Benchmark performance
- Tune thresholds
- Optimize caching
- Production testing

---

## Testing Strategy

### Unit Tests (50+ tests total)

**QAFilter (15 tests):**
- Q&A density computation
- Section identification
- Filtering logic
- Edge cases (no Q&A, all Q&A)

**TopicRanker (15 tests):**
- Importance scoring
- Ranking algorithm
- Threshold filtering
- Procedural detection

**StepValidator (20 tests):**
- Each validation rule
- Auto-fix suggestions
- Batch validation
- Edge cases

### Integration Tests (5 tests)

1. Phase 2 disabled (Phase 1 only)
2. Q&A filtering only
3. Topic ranking only
4. Full Phase 2 enabled
5. Embeddings enabled (optional)

### Quality Metrics

| Metric | Phase 1 | Phase 2 Target | How to Measure |
|--------|---------|----------------|----------------|
| **Avg Confidence** | 0.36 | 0.50+ | avg(step.confidence_score) |
| **High Confidence Steps** | Unknown | 50%+ | count(confidence > 0.7) / total |
| **Q&A Noise** | Present | 0% | Manual review: count Q&A in steps |
| **Low Quality Steps** | Unknown | <10% | count(validation_issues) / total |

---

## Feature Flags

```python
class PipelineConfig:
    # Phase 1 (existing)
    use_intelligent_parsing: bool = False
    use_topic_segmentation: bool = False

    # Phase 2 (new)
    use_qa_filtering: bool = False        # Filter Q&A sections
    use_topic_ranking: bool = False       # Rank by importance
    use_enhanced_validation: bool = False # Detailed validation
    use_embeddings: bool = False          # Semantic embeddings (optional)
```

**Deployment Strategy:**
1. Phase 1 only (current state)
2. Phase 1 + Q&A filtering
3. Phase 1 + Q&A + ranking
4. Full Phase 2 (all quality gates)
5. Phase 2 + embeddings (optional)

---

## Success Criteria

Phase 2 is successful if:

1. ✅ **Q&A sections filtered correctly** (0% Q&A in procedural steps)
2. ✅ **Topics ranked by importance** (top-ranked = most procedural)
3. ✅ **Steps validated with detailed checks** (validation rules enforced)
4. ✅ **Confidence scores improve** (0.36 → 0.50+, +40%)
5. ✅ **High confidence steps increase** (50%+ with >0.7 score)
6. ✅ **No breaking changes** (backward compatible)
7. ✅ **All tests pass** (50+ unit, 5+ integration)

---

## Risks & Mitigation

### Risk 1: Over-filtering (too aggressive)
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Conservative thresholds (30% Q&A density)
- Feature flags for gradual rollout
- Manual review of filtered content
- Configurable thresholds

### Risk 2: Ranking algorithm too simple
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Start with simple weighted score
- Iterate based on feedback
- Add machine learning later if needed

### Risk 3: Embeddings slow down pipeline
**Likelihood:** High
**Impact:** Medium
**Mitigation:**
- Make embeddings optional
- Cache embeddings aggressively
- Use fast model (all-MiniLM-L6-v2)
- Only compute when needed

---

## Open Questions

1. **Q&A density threshold:** 30% (conservative) or 50% (aggressive)?
   - **Recommendation:** Start with 30%, increase if over-filtering

2. **Topic ranking weights:** Equal weights or favor action density?
   - **Recommendation:** Favor action density (0.4) for procedural content

3. **Embeddings model:** sentence-transformers or OpenAI?
   - **Recommendation:** sentence-transformers (faster, cheaper, offline)

4. **Validation strictness:** Fail steps or just warn?
   - **Recommendation:** Warn initially, fail after threshold tuning

---

## Dependencies

**New Python Packages:**
```bash
# For embeddings (optional)
pip install sentence-transformers  # ~50MB model
pip install torch  # Required by sentence-transformers
```

**Phase 1 Prerequisites:**
- ✅ TranscriptParser (provides metadata)
- ✅ TopicSegmenter (provides segments)
- ✅ ParsedSentence (has is_question, speaker)

---

## Next Steps After Approval

1. Create feature branch: `feature/phase2-quality-gates`
2. Begin Day 1: Q&A Filter Implementation
3. Week 1 checkpoint (Day 5): Q&A + Ranking complete
4. Week 2 checkpoint (Day 10): Phase 2 complete

---

**Plan Status:** Ready for approval
**Total Timeline:** 10 days (2 weeks) + 4 days optional (embeddings)
**Risk Level:** Low (builds on Phase 1, feature flags, incremental)

**Prerequisites:** Phase 1 complete ✅
