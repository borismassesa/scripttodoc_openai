# Step Generation Progress: Visual Guide

**Date:** December 4, 2025
**Purpose:** Visual demonstration of how step generation progress appears in the UI

---

## What You See During Step Generation

### The Complete UI Display

```
┌──────────────────────────────────────────────────────────┐
│  📄 Active Jobs (1)                                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Generating Steps                          44%  2m 30s  │
│                                                          │
│  ▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱ 44%                              │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ● ● ●  Generating Step 4 of 9                     │ │ ← THIS IS THE KEY!
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [▼ Show Progress Details]                   11 stages  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### What Changes Over Time

#### At 0:00 - Step 1 Starts
```
┌────────────────────────────────────────────────────┐
│ ● ● ●  Generating Step 1 of 9                     │ ← Shows "1 of 9"
└────────────────────────────────────────────────────┘
```

#### At 0:20 - Step 2 Starts
```
┌────────────────────────────────────────────────────┐
│ ● ● ●  Generating Step 2 of 9                     │ ← Changes to "2 of 9"
└────────────────────────────────────────────────────┘
```

#### At 0:40 - Step 3 Starts
```
┌────────────────────────────────────────────────────┐
│ ● ● ●  Generating Step 3 of 9                     │ ← Changes to "3 of 9"
└────────────────────────────────────────────────────┘
```

#### At 1:00 - Step 4 Starts
```
┌────────────────────────────────────────────────────┐
│ ● ● ●  Generating Step 4 of 9                     │ ← Changes to "4 of 9"
└────────────────────────────────────────────────────┘
```

#### ... and so on through Step 9

---

## Timeline Animation

### Full Progression (9 Steps Example)

```
TIME     DISPLAY                              WHAT'S HAPPENING
─────────────────────────────────────────────────────────────
00:00    Generating Step 1 of 9               ✓ Backend generates step 1
00:20    Generating Step 2 of 9               ✓ Backend generates step 2
00:40    Generating Step 3 of 9               ✓ Backend generates step 3
01:00    Generating Step 4 of 9               ✓ Backend generates step 4
01:20    Generating Step 5 of 9               ✓ Backend generates step 5
01:40    Generating Step 6 of 9               ✓ Backend generates step 6
02:00    Generating Step 7 of 9               ✓ Backend generates step 7
02:20    Generating Step 8 of 9               ✓ Backend generates step 8
02:40    Generating Step 9 of 9               ✓ Backend generates step 9
03:00    Building Citations                   ✓ Moves to next stage
```

**Key Points:**
- ✅ The number changes every ~20 seconds
- ✅ You see ALL steps: 1, 2, 3, 4, 5, 6, 7, 8, 9
- ✅ The blue box updates automatically via polling
- ✅ No user interaction needed - just watch!

---

## Common Scenarios

### Scenario 1: Watching a Live Job

**What you do:** Upload a transcript, stay on the page

**What you see:**
```
00:00  "Generating Step 1 of 9"  ← First step
       ... wait 20 seconds ...
00:20  "Generating Step 2 of 9"  ← Updates automatically
       ... wait 20 seconds ...
00:40  "Generating Step 3 of 9"  ← Updates automatically
       ... continues ...
```

**Result:** ✅ You see ALL steps progressing

---

### Scenario 2: Viewing a Completed Job

**What you do:** Click on a job in the History tab

**What you see:**
```
Status: Complete ✓
Progress: 100%
Current Step: 9 of 9  ← Shows FINAL state only
```

**Result:** ✅ This is correct - completed jobs show final state, not progression history

---

### Scenario 3: Refreshing During Processing

**What you do:** Upload transcript, wait 1 minute, refresh the page

**What you see after refresh:**
```
"Generating Step 3 of 9"  ← Shows current step at time of refresh
```

**Result:** ✅ You see the step that's currently being processed, not step 1

---

## The Blue Box Component

### Component Code Reference

**File:** [ProgressTracker.tsx:187-197](frontend/components/ProgressTracker.tsx#L187-L197)

```tsx
{job.stage === 'generate_steps' && job.current_step && job.total_steps && (
  <div className="flex items-center justify-center space-x-3 px-4 py-3 bg-blue-50 rounded-lg border border-blue-200">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
    </div>
    <span className="text-sm font-medium text-blue-900">
      Generating Step {job.current_step} of {job.total_steps}  ← THIS LINE!
    </span>
  </div>
)}
```

**What it does:**
1. Checks if stage is `generate_steps` ✅
2. Checks if `current_step` and `total_steps` are available ✅
3. Displays: `Generating Step {current_step} of {total_steps}` ✅
4. Updates automatically every 2 seconds via polling ✅

---

## Backend Update Mechanism

### How Backend Sends Updates

**File:** [pipeline.py:405-414](backend/script_to_doc/pipeline.py#L405-L414)

```python
for i, chunk in enumerate(chunks, 1):  # i = 1, 2, 3, 4, 5, 6, 7, 8, 9
    # ... generate step ...

    # Update progress with current step
    self._update_progress(
        progress_callback,
        progress,
        "generate_steps",
        current_step=i,                                    # ← 1, 2, 3, 4, ...
        total_steps=len(chunks),                           # ← Always 9
        stage_detail=f"Generating step {i} of {len(chunks)}"  # ← "step 1 of 9", "step 2 of 9", ...
    )
```

### What Gets Stored in Cosmos DB

```json
// After step 1
{
  "job_id": "abc-123",
  "stage": "generate_steps",
  "current_step": 1,
  "total_steps": 9,
  "stage_detail": "Generating step 1 of 9"
}

// After step 2 (OVERWRITES previous)
{
  "job_id": "abc-123",
  "stage": "generate_steps",
  "current_step": 2,
  "total_steps": 9,
  "stage_detail": "Generating step 2 of 9"
}

// After step 3 (OVERWRITES previous)
{
  "job_id": "abc-123",
  "stage": "generate_steps",
  "current_step": 3,
  "total_steps": 9,
  "stage_detail": "Generating step 3 of 9"
}
```

### What Frontend Polls

```typescript
// Every 2 seconds
const response = await fetch(`/api/status/${jobId}`);
const data = await response.json();

// Updates React state
setJob({
  ...data,
  current_step: data.current_step,  // 1 → 2 → 3 → 4 → ...
  total_steps: data.total_steps      // Always 9
});

// React re-renders automatically
// Display changes from "Step 1 of 9" to "Step 2 of 9" to "Step 3 of 9" etc.
```

---

## Testing Guide

### Test 1: Upload New Transcript

1. Open http://localhost:3000
2. Click "Upload Transcript"
3. Select `sample_meeting.txt` or any transcript
4. Immediately watch the "Active Jobs" section
5. Look for the blue box with bouncing dots

**Expected:**
```
00:00  "Generating Step 1 of X"  ← Appears first
       ↓ Wait ~20 seconds
00:20  "Generating Step 2 of X"  ← Number changes!
       ↓ Wait ~20 seconds
00:40  "Generating Step 3 of X"  ← Number changes again!
       ↓ Continues through all steps
```

### Test 2: Check Backend Logs

While job is running:

```bash
cd backend
tail -f backend_server.log | grep -E "(Generating step|current_step)"
```

**Expected output:**
```
Generating step 1/9 from chunk (450 chars)
Updated job abc-123: generate_steps (current_step=1/9)
Generating step 2/9 from chunk (480 chars)
Updated job abc-123: generate_steps (current_step=2/9)
Generating step 3/9 from chunk (520 chars)
Updated job abc-123: generate_steps (current_step=3/9)
...
```

### Test 3: Check Cosmos DB Directly

```bash
curl http://localhost:8000/api/status/{job_id}
```

**Expected response (during step 4):**
```json
{
  "job_id": "abc-123",
  "status": "processing",
  "stage": "generate_steps",
  "current_step": 4,
  "total_steps": 9,
  "stage_detail": "Generating step 4 of 9",
  "progress": 0.49
}
```

---

## Troubleshooting

### Issue: "I only see Step 1 of 9"

**Possible causes:**
1. Job just started - wait 20 seconds for step 2
2. Browser not polling - check console for errors
3. Backend not updating - check backend logs

**Solution:**
```bash
# Check backend logs
cd backend
tail -f backend_server.log | grep "Generating step"

# Should see:
# Generating step 1/9 from chunk
# Generating step 2/9 from chunk  ← If you see this, backend is working
# Generating step 3/9 from chunk
```

---

### Issue: "Numbers don't change"

**Possible causes:**
1. Job already completed
2. Frontend polling stopped
3. Browser tab backgrounded (polling may slow)

**Solution:**
```bash
# Check job status
curl http://localhost:8000/api/status/{job_id}

# Look at "status" field:
# - "processing" → Should be updating
# - "completed" → Will show final step only
# - "failed" → Check error field
```

---

### Issue: "Completed job shows Step 9 of 9"

**This is CORRECT behavior!**

Completed jobs show the **final state**, not the progression history.

To see the progression:
1. Upload a NEW transcript
2. Watch it in real-time
3. You'll see: Step 1 → 2 → 3 → ... → 9

---

## Summary

✅ **Backend sends updates for every step:** 1, 2, 3, 4, 5, 6, 7, 8, 9
✅ **Frontend displays current step:** Updates every 2 seconds via polling
✅ **Blue box shows progress:** "Generating Step X of Y" with bouncing dots
✅ **You see ALL steps:** Numbers increment over ~3 minutes

**To verify:** Upload a new transcript and watch the blue box. You'll see the step counter increment through all steps!

---

**Status:** ✅ System working correctly
**Last Updated:** December 4, 2025
**Purpose:** Visual guide to understand step generation progress display
