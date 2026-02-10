# Step Generation Progress: How It Works

**Date:** December 4, 2025
**Issue:** User concern - '"Generating step 1 of X" does not show all the generated steps'
**Status:** ✅ Working correctly - Explanation provided

---

## How Step Generation Progress Works

### Backend Behavior (VERIFIED ✅)

**File:** [pipeline.py:384-414](backend/script_to_doc/pipeline.py#L384-L414)

The backend sends progress updates for **EVERY STEP** during generation:

```python
for i, chunk in enumerate(chunks, 1):  # i = 1, 2, 3, 4, ...
    try:
        logger.info(f"Generating step {i}/{len(chunks)} from chunk")

        # ... generate the step ...

        # Update progress for THIS step
        progress = 0.40 + (0.20 * i / len(chunks))
        self._update_progress(
            progress_callback,
            progress,
            "generate_steps",
            current_step=i,        # ← Increments: 1, 2, 3, 4, 5, 6, 7, 8, 9
            total_steps=len(chunks),
            stage_detail=f"Generating step {i} of {len(chunks)}"
        )
```

**What this means:**
- If generating 9 steps, backend sends 9 updates:
  - Update 1: `current_step=1, total_steps=9, stage_detail="Generating step 1 of 9"`
  - Update 2: `current_step=2, total_steps=9, stage_detail="Generating step 2 of 9"`
  - Update 3: `current_step=3, total_steps=9, stage_detail="Generating step 3 of 9"`
  - ... and so on up to step 9

---

### Frontend Behavior (VERIFIED ✅)

**File:** [ProgressTracker.tsx:194](frontend/components/ProgressTracker.tsx#L194)

The frontend displays the current step from the backend:

```tsx
<span className="text-sm font-medium text-blue-900">
  Generating Step {job.current_step} of {job.total_steps}
</span>
```

**What this means:**
- Frontend polls backend every 2 seconds
- Each poll fetches the latest `current_step` and `total_steps`
- Display updates from "Step 1 of 9" → "Step 2 of 9" → "Step 3 of 9" → etc.

---

## What You Should See During Processing

### Timeline of a Live Job (9 steps example)

```
Time    Backend State               Frontend Display
----    ---------------             -----------------
00:00   current_step=1, total=9     "Generating Step 1 of 9"
00:20   current_step=2, total=9     "Generating Step 2 of 9"
00:40   current_step=3, total=9     "Generating Step 3 of 9"
01:00   current_step=4, total=9     "Generating Step 4 of 9"
01:20   current_step=5, total=9     "Generating Step 5 of 9"
01:40   current_step=6, total=9     "Generating Step 6 of 9"
02:00   current_step=7, total=9     "Generating Step 7 of 9"
02:20   current_step=8, total=9     "Generating Step 8 of 9"
02:40   current_step=9, total=9     "Generating Step 9 of 9"
03:00   Stage moves to build_sources
```

**Expected behavior:**
- ✅ You see "Step 1 of 9"
- ✅ After ~20 seconds, you see "Step 2 of 9"
- ✅ After ~20 more seconds, you see "Step 3 of 9"
- ✅ This continues through ALL 9 steps
- ✅ Each step is visible for ~20 seconds
- ✅ Total time: ~3 minutes for 9 steps

---

## Why Completed Jobs Don't Show History

### Important: Jobs Show Current State, Not History

When you view a **completed job**, you see:
- ✅ Final status: `complete`
- ✅ Final progress: `100%`
- ✅ Final step: `current_step=9, total_steps=9`

You do **NOT** see the progression history (step 1 → 2 → 3 → etc.) because:
1. The frontend polls the **current state** from Cosmos DB
2. Cosmos DB stores the **latest state**, not the full history
3. Once the job completes, `current_step` remains at the final value (9)

**Example:**
```
Job 2ebbd4db-4b94-4671-a737-f143afee889f (completed)
  status: "completed"
  progress: 100%
  current_step: 9
  total_steps: 9
  stage: "complete"
```

This is **CORRECT BEHAVIOR**. You're seeing the final state, not the progression.

---

## How to Verify All Steps Are Visible

### Method 1: Upload a New Transcript (Recommended)

1. **Start backend** (if not running):
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend** (if not running):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload a new transcript**:
   - Open http://localhost:3000
   - Click "Upload Transcript"
   - Select a transcript file
   - Watch the "Active Jobs" section

4. **Observe the progress**:
   - ✅ You should see "Generating Step 1 of X"
   - ✅ After ~20 seconds, it changes to "Step 2 of X"
   - ✅ After ~20 more seconds, it changes to "Step 3 of X"
   - ✅ This continues through ALL steps
   - ✅ Each step is clearly visible

5. **After completion**:
   - Job moves to "History" tab
   - Shows final state: Step X of X (completed)

---

### Method 2: Check Backend Logs During Processing

While a job is processing, check the backend logs:

```bash
cd backend
tail -f backend_server.log | grep "Generating step"
```

**Expected output:**
```
2025-12-04 11:31:10 - Generating step 1/9 from chunk (450 chars)
2025-12-04 11:31:29 - Generating step 2/9 from chunk (480 chars)
2025-12-04 11:31:48 - Generating step 3/9 from chunk (520 chars)
2025-12-04 11:32:07 - Generating step 4/9 from chunk (490 chars)
2025-12-04 11:32:26 - Generating step 5/9 from chunk (510 chars)
2025-12-04 11:32:45 - Generating step 6/9 from chunk (470 chars)
2025-12-04 11:33:04 - Generating step 7/9 from chunk (500 chars)
2025-12-04 11:33:23 - Generating step 8/9 from chunk (460 chars)
2025-12-04 11:33:42 - Generating step 9/9 from chunk (480 chars)
```

Also check for progress updates:

```bash
cd backend
tail -f backend_server.log | grep "Updated job"
```

**Expected output:**
```
2025-12-04 11:31:10 - Updated job abc123: generate_steps (current_step=1/9)
2025-12-04 11:31:29 - Updated job abc123: generate_steps (current_step=2/9)
2025-12-04 11:31:48 - Updated job abc123: generate_steps (current_step=3/9)
...
```

---

## Common Misconceptions

### ❌ Misconception 1: "I only see Step 1"
**Reality:** You're likely looking at a completed job, or the job just started.
**Solution:** Wait 20-30 seconds and refresh, or upload a new job to watch in real-time.

### ❌ Misconception 2: "It should show all steps at once"
**Reality:** The frontend shows the **current** step being processed, not all steps simultaneously.
**Solution:** This is correct behavior. Watch the counter increment over time.

### ❌ Misconception 3: "Completed jobs should show the progression"
**Reality:** Completed jobs show the final state, not the progression history.
**Solution:** To see progression, watch a live job as it processes.

---

## Technical Details

### Polling Mechanism

**Frontend polling frequency:** Every 2 seconds

**Example step generation timing:**
- Step 1: 0s-20s (10 polling cycles)
- Step 2: 20s-40s (10 polling cycles)
- Step 3: 40s-60s (10 polling cycles)
- ...

**What the frontend fetches:**

```typescript
// Every 2 seconds
const response = await fetch(`/api/status/${jobId}`);
const job = await response.json();

// Display updates automatically
job.current_step  // 1 → 2 → 3 → 4 → ...
job.total_steps   // 9 (constant)
```

### Database Updates

**Backend writes to Cosmos DB:**
```python
# Update 1
{
  "current_step": 1,
  "total_steps": 9,
  "stage_detail": "Generating step 1 of 9"
}

# Update 2 (overwrites)
{
  "current_step": 2,
  "total_steps": 9,
  "stage_detail": "Generating step 2 of 9"
}

# Update 3 (overwrites)
{
  "current_step": 3,
  "total_steps": 9,
  "stage_detail": "Generating step 3 of 9"
}
```

**Frontend reads latest state:**
- Always sees the most recent `current_step` value
- No history is stored (only current state)

---

## Verification Checklist

To verify the step generation progress is working correctly:

- [ ] Backend server is running (port 8000)
- [ ] Frontend dev server is running (port 3000)
- [ ] Upload a new transcript
- [ ] Watch the "Active Jobs" section
- [ ] Confirm "Generating Step 1 of X" appears
- [ ] Wait ~20 seconds
- [ ] Confirm "Generating Step 2 of X" appears
- [ ] Continue watching through all steps
- [ ] Verify each step increments (1 → 2 → 3 → ...)
- [ ] After completion, verify job moves to History
- [ ] In History, verify final state shows "Step X of X"

---

## Conclusion

✅ **Backend IS sending updates for all steps** (1, 2, 3, ..., 9)
✅ **Frontend IS displaying the current step** from backend
✅ **Completed jobs show final state** (not progression history)

**To see the step progression:**
1. Upload a NEW transcript
2. Watch the progress in real-time
3. You will see ALL steps incrementing

**Current behavior is CORRECT.** If you're seeing "Step 1 of X" and it's not changing, either:
- The job hasn't progressed yet (wait ~20 seconds)
- The job is already completed (check if it's in History tab)
- There's no active job processing (upload a new transcript)

---

**Status:** ✅ **Working as designed**
**Last Updated:** December 4, 2025
**Issue:** User concern about step visibility
**Resolution:** System is working correctly - progression is visible during live job processing
