# 🚨 URGENT FIXES NEEDED - Active Processing Issues

**Date**: 2025-11-25
**Priority**: CRITICAL

---

## Issue Summary

Based on the screenshot and logs, there are 3 critical issues preventing successful document generation:

1. ❌ **sentence-transformers NOT installed** → 0.00 confidence → All steps rejected
2. ❌ **Invalid ProcessingStage errors** → UI can't display progress correctly
3. ❌ **Poor UI/UX** → User can't see what's happening during processing

---

## 🔥 CRITICAL: Issue #1 - sentence-transformers Not Installed

### Problem
```
WARNING:root:sentence-transformers not available - falling back to word-overlap only
WARNING:script_to_doc.pipeline:Step 1 rejected (confidence: 0.00 < 0.25, sources: 0)
WARNING:script_to_doc.pipeline:Step 2 rejected (confidence: 0.00 < 0.25, sources: 0)
WARNING:script_to_doc.pipeline:Step 3 rejected (confidence: 0.00 < 0.25, sources: 0)
WARNING:script_to_doc.pipeline:No valid steps passed validation
```

**Root Cause**: sentence-transformers is in requirements.txt but NOT installed in the venv!

### Impact
- **All steps get 0.00 confidence** instead of 0.43
- All semantic similarity code is disabled
- Word-overlap matching alone fails completely
- **No steps pass validation** → Empty documents

### Fix (MUST DO IMMEDIATELY)

```bash
# 1. Stop the server (Ctrl+C)

# 2. Install sentence-transformers in the venv
cd "/Users/boris/AZURE AI Document Intelligence/backend"
source venv/bin/activate
pip install sentence-transformers==2.3.1

# 3. Verify installation
python3 -c "from sentence_transformers import SentenceTransformer; print('✅ Installed')"

# 4. Restart server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Result After Fix
```
INFO: Semantic similarity scoring enabled with weights: word=0.50, semantic=0.50
```

**Instead of:**
```
WARNING:root:sentence-transformers not available - falling back to word-overlap only
```

---

## Issue #2 - Invalid ProcessingStage Errors

### Problem
```
ERROR:api.routes.status:Failed to get job status: 'generate_step_2' is not a valid ProcessingStage
WARNING:api.routes.status:Failed to list jobs: 'generate_step_1' is not a valid ProcessingStage
```

**Root Cause**: The pipeline is trying to set granular stages like `generate_step_1`, `generate_step_2`, etc., but these aren't defined in the `ProcessingStage` enum.

### Current ProcessingStage Enum
```python
class ProcessingStage(str, Enum):
    PENDING = "pending"
    LOAD_TRANSCRIPT = "load_transcript"
    CLEAN_TRANSCRIPT = "clean_transcript"
    FETCH_KNOWLEDGE = "fetch_knowledge"
    AZURE_DI_ANALYSIS = "azure_di_analysis"
    DETERMINE_STEPS = "determine_steps"
    GENERATE_STEPS = "generate_steps"    # ← Only one generic stage
    BUILD_SOURCES = "build_sources"
    VALIDATE_STEPS = "validate_steps"
    CREATE_DOCUMENT = "create_document"
    UPLOAD_DOCUMENT = "upload_document"
    COMPLETE = "complete"
    ERROR = "error"
```

### Fix Options

**Option A: Remove granular stage updates** (Recommended - Simplest)
- Keep using `GENERATE_STEPS` for all step generation
- Don't try to set individual step stages
- Add progress percentage instead

**Option B: Add dynamic step stages to enum**
- Add `GENERATE_STEP_1`, `GENERATE_STEP_2`, etc. to enum
- More complex, harder to maintain

**Option C: Use progress metadata instead of stage**
- Store `current_step` in job metadata
- Keep stage as `GENERATE_STEPS`
- Update progress percentage (0.0 - 1.0)

### Recommended Fix (Option C)

**Update `JobStatusResponse` model:**
```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=1.0)
    stage: ProcessingStage
    current_step: Optional[int] = None      # NEW: Current step being processed
    total_steps: Optional[int] = None        # NEW: Total steps to process
    stage_detail: Optional[str] = None       # NEW: Human-readable detail
    created_at: datetime
    updated_at: datetime
    config: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
```

**Usage in pipeline:**
```python
# Instead of:
job["stage"] = f"generate_step_{i}"  # ❌ Causes error

# Do this:
job["stage"] = ProcessingStage.GENERATE_STEPS
job["current_step"] = i
job["total_steps"] = len(chunks)
job["stage_detail"] = f"Generating step {i} of {len(chunks)}"
job["progress"] = i / len(chunks)
```

---

## Issue #3 - Poor UI/UX During Processing

### Problem
User sees only "Active processing" but has no visibility into:
- Which stage is currently running
- How many steps generated vs total
- What's being processed right now
- Whether it's working or stuck
- Time remaining estimate

### Recommended UI Improvements

#### A. Real-Time Progress Display

**Current UI (BAD):**
```
🔄 Active processing...
```

**Improved UI (GOOD):**
```
🔄 Generating Training Steps (Step 3 of 6)

Current Stage: Generate Steps
Progress: ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░ 50%
Time Elapsed: 45s
Estimated Remaining: ~45s

Recent Activity:
✅ Transcript loaded and cleaned
✅ Knowledge sources fetched (3 URLs)
✅ Step 1 generated (confidence: 0.45)
✅ Step 2 generated (confidence: 0.52)
🔄 Generating step 3...

Steps Generated: 2 | Accepted: 2 | Rejected: 0
Average Confidence: 0.49
```

#### B. Enhanced ProgressTracker Component

**File**: `frontend/components/ProgressTracker.tsx`

**Add these features:**
1. **Stage-by-stage breakdown** with checkmarks
2. **Real-time step counter** (e.g., "3 / 6 steps generated")
3. **Progress percentage** with visual bar
4. **Time elapsed / estimated**
5. **Recent activity log** (last 5 actions)
6. **Current confidence scores** (if available)

**Example Implementation:**
```typescript
interface ProgressData {
  stage: string;
  progress: number;  // 0.0 - 1.0
  currentStep?: number;
  totalSteps?: number;
  stageDetail?: string;
  stepsGenerated?: number;
  stepsAccepted?: number;
  stepsRejected?: number;
  averageConfidence?: number;
  recentActivity?: string[];
  timeElapsed?: number;
}

function ProgressTracker({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState<ProgressData | null>(null);

  // Poll status every 2 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      const status = await fetchJobStatus(jobId);
      setProgress({
        stage: status.stage,
        progress: status.progress,
        currentStep: status.current_step,
        totalSteps: status.total_steps,
        stageDetail: status.stage_detail,
        // ... other fields
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="progress-tracker">
      <h3>{progress?.stageDetail || progress?.stage}</h3>

      {/* Progress Bar */}
      <ProgressBar value={progress?.progress * 100} />

      {/* Step Counter */}
      {progress?.currentStep && progress?.totalSteps && (
        <div>
          Step {progress.currentStep} of {progress.totalSteps}
        </div>
      )}

      {/* Stage Checklist */}
      <StageChecklist currentStage={progress?.stage} />

      {/* Recent Activity */}
      {progress?.recentActivity && (
        <ActivityLog items={progress.recentActivity} />
      )}

      {/* Statistics */}
      {progress?.stepsGenerated !== undefined && (
        <div>
          Steps: {progress.stepsAccepted} accepted, {progress.stepsRejected} rejected
          Avg Confidence: {progress.averageConfidence?.toFixed(2)}
        </div>
      )}
    </div>
  );
}
```

#### C. Backend API Updates

**Update status endpoint** to return detailed progress:

```python
@router.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    job = get_job_from_db(job_id)

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job["stage"],
        progress=job.get("progress", 0.0),
        current_step=job.get("current_step"),
        total_steps=job.get("total_steps"),
        stage_detail=job.get("stage_detail"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        result={
            "steps_generated": job.get("steps_generated", 0),
            "steps_accepted": job.get("steps_accepted", 0),
            "steps_rejected": job.get("steps_rejected", 0),
            "average_confidence": job.get("average_confidence", 0.0),
            "recent_activity": job.get("recent_activity", []),
        } if job.get("status") == "processing" else job.get("result"),
        error=job.get("error")
    )
```

---

## Implementation Priority

### 🔥 IMMEDIATE (Do Now):
1. ✅ **Install sentence-transformers** (Fixes 0.00 confidence)
   ```bash
   pip install sentence-transformers==2.3.1
   ```

### 🟡 HIGH PRIORITY (Today):
2. **Fix ProcessingStage errors**
   - Add `current_step`, `total_steps`, `stage_detail` to JobStatusResponse
   - Update pipeline to use these fields instead of invalid stages

3. **Add basic progress visibility**
   - Show current_step / total_steps in UI
   - Show stage_detail message
   - Show progress percentage

### 🟢 MEDIUM PRIORITY (This Week):
4. **Enhanced UI/UX**
   - Real-time activity log
   - Stage checklist with checkmarks
   - Confidence score display
   - Time remaining estimate

---

## Verification Steps

After implementing fixes:

### 1. Verify sentence-transformers
```bash
# Should see this in logs:
INFO: Semantic similarity scoring enabled with weights: word=0.50, semantic=0.50
```

### 2. Verify confidence scores
```bash
# Should see steps with good confidence:
INFO: Step 1: Confidence 0.43, 3 sources, valid: True
INFO: Step 2: Confidence 0.51, 4 sources, valid: True
```

### 3. Verify UI updates
- Progress bar shows percentage
- Step counter shows "Step 3 of 6"
- Stage detail shows human-readable message
- No more ProcessingStage errors in logs

---

## Expected Results After All Fixes

### Backend Logs (Good):
```
INFO: Semantic similarity scoring enabled with weights: word=0.50, semantic=0.50
INFO: Started processing job: abc-123
INFO: Stage: load_transcript (progress: 0.10)
INFO: Stage: clean_transcript (progress: 0.20)
INFO: Stage: generate_steps (progress: 0.40, step 1/6)
INFO: Step 1: Confidence 0.45, 3 sources, valid: True
INFO: Stage: generate_steps (progress: 0.50, step 2/6)
INFO: Step 2: Confidence 0.52, 4 sources, valid: True
...
INFO: Generated 6 steps, accepted: 6, rejected: 0
INFO: Average confidence: 0.48
INFO: Stage: create_document (progress: 0.90)
INFO: Stage: complete (progress: 1.0)
```

### UI Display (Good):
```
🔄 Generating Training Steps

Step 3 of 6 | Progress: 50%

▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░

Recent Activity:
✅ Step 1 generated (confidence: 0.45)
✅ Step 2 generated (confidence: 0.52)
🔄 Generating step 3...

Time Elapsed: 45s
Estimated Remaining: ~45s
```

---

## Files to Modify

1. **Backend**:
   - [api/models.py](backend/api/models.py) - Add fields to JobStatusResponse
   - [script_to_doc/pipeline.py](backend/script_to_doc/pipeline.py) - Update stage tracking
   - [api/routes/status.py](backend/api/routes/status.py) - Return detailed progress

2. **Frontend**:
   - [components/ProgressTracker.tsx](frontend/components/ProgressTracker.tsx) - Enhanced UI
   - [lib/api.ts](frontend/lib/api.ts) - Update status response types

---

**PRIORITY**: Fix #1 (sentence-transformers) IMMEDIATELY to restore functionality!
