# Bug Investigation: Step Counter Stops at Step 4

**Date:** December 4, 2025
**Issue:** Frontend step counter shows steps 1, 2, 3, 4 but then stops updating until completion
**Status:** 🔍 Under Investigation

---

## User Report

> "in the frontend when its on the generating steps once it gets to setep 4 it stops updating the steps to get to the final step and then move to the next phase"

**Symptoms:**
- Step counter shows: "Generating Step 1 of X" ✅
- Updates to: "Generating Step 2 of X" ✅
- Updates to: "Generating Step 3 of X" ✅
- Updates to: "Generating Step 4 of X" ✅
- **STOPS UPDATING** ❌
- Eventually completes and moves to next phase
- Steps 5, 6, 7, 8, 9 are never displayed

---

## Code Review Findings

### Backend Code (✅ Appears Correct)

**File:** [pipeline.py:384-414](backend/script_to_doc/pipeline.py#L384-L414)

```python
for i, chunk in enumerate(chunks, 1):  # i goes from 1 to len(chunks)
    try:
        # ... generate step ...

        # Update progress incrementally with step metadata
        progress = 0.40 + (0.20 * i / len(chunks))
        self._update_progress(
            progress_callback,
            progress,
            "generate_steps",
            current_step=i,        # ← Should be 1, 2, 3, 4, 5, 6, 7, 8, 9
            total_steps=len(chunks),
            stage_detail=f"Generating step {i} of {len(chunks)}"
        )
    except Exception as e:
        logger.error(f"Failed to generate step {i}/{len(chunks)}: {str(e)}")
        continue  # Continue with remaining chunks
```

**Analysis:**
- ✅ Loop iterates through ALL chunks (1 to len(chunks))
- ✅ Updates sent for every iteration
- ✅ Exception handling doesn't break the loop
- ✅ Progress callback called with correct `current_step` value

---

**File:** [background_processor.py:78-84](backend/api/background_processor.py#L78-L84)

```python
def progress_update(progress, stage, current_step=None, total_steps=None, stage_detail=None):
    update_job_status(
        job_id, user_id, "processing", progress, stage,
        current_step=current_step,
        total_steps=total_steps,
        stage_detail=stage_detail
    )
```

**Analysis:**
- ✅ Callback correctly passes all parameters to `update_job_status`

---

**File:** [background_processor.py:188-232](backend/api/background_processor.py#L188-L232)

```python
def update_job_status(
    job_id, user_id, status, progress, stage,
    result=None, error=None,
    current_step=None, total_steps=None, stage_detail=None
):
    # ... get job from Cosmos DB ...

    # Update fields
    job["status"] = status
    job["progress"] = progress
    job["stage"] = stage
    job["updated_at"] = datetime.utcnow().isoformat()

    # Update optional metadata fields
    if current_step is not None:
        job["current_step"] = current_step
    if total_steps is not None:
        job["total_steps"] = total_steps
    if stage_detail is not None:
        job["stage_detail"] = stage_detail

    # Upsert
    container.upsert_item(body=job)

    logger.info(f"Updated job {job_id}: {status} ({progress:.0%}) - {stage} | {stage_detail}")
```

**Analysis:**
- ✅ Updates Cosmos DB with new values
- ⚠️ **POTENTIAL ISSUE**: If `current_step` is None, it doesn't update the field (keeps old value)
  - But during generate_steps, `current_step` is always provided
- ✅ Logs the update for debugging

---

### Frontend Code (✅ Appears Correct)

**File:** [ProgressTracker.tsx:37-95](frontend/components/ProgressTracker.tsx#L37-L95)

```tsx
useEffect(() => {
  let interval: NodeJS.Timeout;

  const pollStatus = async () => {
    const status = await getJobStatus(jobId);
    if (!isMountedRef.current) return;

    setJob(status);  // ← Update React state
    setError(null);

    if (status.status === 'completed') {
      clearInterval(interval);
      // ...
    }
  };

  pollStatus();  // Initial poll
  interval = setInterval(pollStatus, 2000);  // Poll every 2 seconds

  return () => {
    clearInterval(interval);
  };
}, [jobId, onComplete]);
```

**Analysis:**
- ✅ Polls every 2 seconds
- ✅ Updates state with `setJob(status)`
- ✅ Should trigger re-render on every state change

---

**File:** [ProgressTracker.tsx:186-197](frontend/components/ProgressTracker.tsx#L186-L197)

```tsx
{job.stage === 'generate_steps' && job.current_step && job.total_steps && (
  <div className="...">
    <span>
      Generating Step {job.current_step} of {job.total_steps}
    </span>
  </div>
)}
```

**Analysis:**
- ✅ Displays `job.current_step` directly from state
- ✅ Should update when `job` state changes
- ⚠️ **POTENTIAL ISSUE**: Only shows when `job.stage === 'generate_steps'`
  - If stage changes prematurely, counter disappears

---

**File:** [api.ts:170-173](frontend/lib/api.ts#L170-L173)

```tsx
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await apiClient.get<JobStatus>(`/api/status/${jobId}`);
  return response.data;
}
```

**Analysis:**
- ✅ Simple GET request
- ⚠️ **POTENTIAL ISSUE**: axios default caching behavior?
- ⚠️ **POTENTIAL ISSUE**: Network request timing (2s interval might miss fast updates)

---

## Possible Root Causes

### Hypothesis 1: Axios Response Caching
**Likelihood:** Medium

**Issue:** Browser or axios might be caching GET requests, returning stale data

**Evidence:**
- axios doesn't cache by default, but browsers might
- No cache headers explicitly set

**Test:**
1. Add cache-busting headers to API requests
2. Check browser DevTools Network tab for 304 responses
3. Monitor if responses are identical when they should differ

**Fix:**
```typescript
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await apiClient.get<JobStatus>(`/api/status/${jobId}`, {
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    }
  });
  return response.data;
}
```

---

### Hypothesis 2: React State Update Batching
**Likelihood:** Low

**Issue:** React might be batching state updates and skipping intermediate values

**Evidence:**
- React 18 automatic batching could skip intermediate updates
- `setJob(status)` called every 2 seconds with potentially same values

**Test:**
1. Add console.log to track every state update
2. Check if `setJob` is called but component doesn't re-render

**Fix:**
```tsx
const pollStatus = async () => {
  const status = await getJobStatus(jobId);
  if (!isMountedRef.current) return;

  console.log('[ProgressTracker] Received status:', {
    current_step: status.current_step,
    total_steps: status.total_steps,
    stage: status.stage
  });

  setJob(prevJob => {
    if (prevJob?.current_step !== status.current_step) {
      console.log('[ProgressTracker] Step changed:', prevJob?.current_step, '→', status.current_step);
    }
    return status;
  });
};
```

---

### Hypothesis 3: Cosmos DB Update Race Condition
**Likelihood:** Medium

**Issue:** Multiple rapid updates to Cosmos DB might cause race conditions

**Evidence:**
- `update_job_status` reads, modifies, then writes
- If two updates happen simultaneously, one might overwrite the other
- Cosmos DB upsert_item might not be atomic for read-modify-write

**Test:**
1. Check backend logs for out-of-order updates
2. Monitor Cosmos DB directly during processing
3. Add timestamps to track update order

**Fix:**
```python
# Use optimistic concurrency control with etag
job = container.read_item(item=job_id, partition_key=user_id)
job_etag = job.get('_etag')

# ... update fields ...

try:
    container.upsert_item(body=job, etag=job_etag, match_condition=MatchConditions.IfNotModified)
except CosmosResourceExistsError:
    # Retry if etag mismatch
    logger.warning(f"Concurrent update detected for job {job_id}, retrying...")
```

---

### Hypothesis 4: Network Timing Issue
**Likelihood:** High ⭐

**Issue:** Step generation happens faster than 2-second polling interval

**Scenario:**
```
Time    Backend Updates Cosmos      Frontend Polls          Display
────────────────────────────────────────────────────────────────────
00:00   current_step=1              Polls → step=1          "Step 1"
00:15   current_step=2              -                       "Step 1"
00:30   current_step=3              -                       "Step 1"
00:45   current_step=4              -                       "Step 1"
02:00   current_step=5              Polls → step=5          "Step 5"  ← Skipped 2,3,4!
04:00   current_step=9              Polls → step=9          "Step 9"  ← Skipped 6,7,8!
```

**Evidence:**
- If steps generate faster than ~20 seconds each, polling might miss them
- User reports it "stops" at step 4, suggesting polling caught steps 1-4 then jumped to completion

**Test:**
1. Check backend logs for timestamp of each step generation
2. Calculate average time per step
3. If < 2 seconds per step, polling will miss updates

**Fix Option 1: Decrease polling interval**
```tsx
interval = setInterval(pollStatus, 500);  // Poll every 500ms instead of 2s
```

**Fix Option 2: WebSocket/Server-Sent Events for real-time updates**
```python
@router.websocket("/ws/status/{job_id}")
async def websocket_status(websocket: WebSocket, job_id: str):
    await websocket.accept()
    while True:
        status = get_job_status(job_id)
        await websocket.send_json(status)
        await asyncio.sleep(0.5)
```

---

### Hypothesis 5: Frontend Component Re-mount
**Likelihood:** Low

**Issue:** ProgressTracker component might be re-mounting, resetting state

**Evidence:**
- ActiveJobs maps over jobs without stable keys
- React might unmount/remount components during re-renders

**Test:**
1. Add console.log in useEffect mount/unmount
2. Check if component is being recreated

**Fix:**
```tsx
{activeJobs.map((job) => (
  <div key={job.job_id}>  {/* ← Ensure stable key */}
    <ProgressTracker jobId={job.job_id} />
  </div>
))}
```

---

## Debugging Plan

### Step 1: Add Comprehensive Logging

**Backend (pipeline.py):**
```python
logger.info(f"[STEP_PROGRESS] Sending update: current_step={i}, total_steps={len(chunks)}, timestamp={datetime.now().isoformat()}")
```

**Backend (background_processor.py):**
```python
logger.info(f"[COSMOS_UPDATE] Writing to DB: job_id={job_id}, current_step={current_step}, total_steps={total_steps}")
```

**Frontend (ProgressTracker.tsx):**
```tsx
console.log('[POLL] API Response:', {
  job_id: status.job_id,
  current_step: status.current_step,
  total_steps: status.total_steps,
  timestamp: new Date().toISOString()
});

console.log('[RENDER] Displaying:', {
  current_step: job?.current_step,
  total_steps: job?.total_steps
});
```

---

### Step 2: Test with Real Upload

1. Start backend with enhanced logging
2. Open frontend with DevTools Console
3. Upload test transcript (sample_meeting.txt)
4. Monitor:
   - Backend logs: Check every step update is sent
   - Frontend console: Check every poll response
   - Browser DevTools Network: Check response status codes
   - Visual: Watch the step counter

---

### Step 3: Analyze Timing

From backend logs, calculate:
- Time between step updates
- Total generation time
- Average time per step

From frontend logs, calculate:
- Polling frequency
- Response delays
- Missed updates (gaps in received current_step values)

---

## Expected Behavior

**If working correctly:**
```
Backend Log:
11:30:00 - Generating step 1/9
11:30:20 - Generating step 2/9
11:30:40 - Generating step 3/9
11:31:00 - Generating step 4/9
11:31:20 - Generating step 5/9
11:31:40 - Generating step 6/9
11:32:00 - Generating step 7/9
11:32:20 - Generating step 8/9
11:32:40 - Generating step 9/9

Frontend Console:
11:30:00 - [POLL] current_step: 1
11:30:02 - [POLL] current_step: 1
11:30:04 - [POLL] current_step: 1
...
11:30:20 - [POLL] current_step: 2
11:30:22 - [POLL] current_step: 2
...
11:32:40 - [POLL] current_step: 9
```

**User sees:**
- "Generating Step 1 of 9" (for ~20 seconds)
- "Generating Step 2 of 9" (for ~20 seconds)
- ... all the way to ...
- "Generating Step 9 of 9"

---

## Status

🔍 **Investigation Phase** - Waiting for test results with enhanced logging

**Next Steps:**
1. Add debug logging to backend and frontend
2. Run test with sample transcript
3. Analyze logs to identify root cause
4. Implement fix based on findings

---

**Last Updated:** December 4, 2025
**Backend Server:** Running (port 8000)
**Frontend Server:** Running (port 3000)
**Ready for Testing:** ✅ Yes
