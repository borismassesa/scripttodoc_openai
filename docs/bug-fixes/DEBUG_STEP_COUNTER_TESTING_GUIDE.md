# Debug Step Counter - Testing Guide

**Date:** December 4, 2025
**Issue:** Frontend step counter stops updating after step 4
**Status:** 🔍 Debug logging added - Ready for testing

---

## What I've Done

### 1. Added Enhanced Debug Logging to Frontend ✅

**File:** [ProgressTracker.tsx](frontend/components/ProgressTracker.tsx)

**Changes:**
- Added logging when API responses are received
- Added logging when React state changes
- Added logging when the component re-renders with new step values

**What you'll see in browser console:**
```
[ProgressTracker] 📊 Poll Response: { jobId: "abc123...", stage: "generate_steps", current_step: 1, total_steps: 9, ... }
[ProgressTracker] ✅ Step Changed: { from: undefined, to: 1, total: 9 }
[ProgressTracker] 🎨 Rendering Step Counter: { current_step: 1, total_steps: 9, display: "Generating Step 1 of 9" }

... 2 seconds later ...

[ProgressTracker] 📊 Poll Response: { jobId: "abc123...", stage: "generate_steps", current_step: 2, total_steps: 9, ... }
[ProgressTracker] ✅ Step Changed: { from: 1, to: 2, total: 9 }
[ProgressTracker] 🎨 Rendering Step Counter: { current_step: 2, total_steps: 9, display: "Generating Step 2 of 9" }
```

---

### 2. Added Cache-Busting Headers ✅

**File:** [api.ts:170-179](frontend/lib/api.ts#L170-L179)

**Purpose:** Prevent browser from caching API responses

**Headers Added:**
```typescript
{
  'Cache-Control': 'no-cache, no-store, must-revalidate',
  'Pragma': 'no-cache',
  'Expires': '0'
}
```

This ensures every poll gets fresh data from the backend.

---

### 3. Created Investigation Document ✅

**File:** [BUG_INVESTIGATION_STEP_COUNTER.md](BUG_INVESTIGATION_STEP_COUNTER.md)

Contains:
- Detailed code review
- 5 possible root cause hypotheses
- Debugging plan
- Expected behavior vs. actual behavior

---

## How to Test

### Step 1: Open Frontend with DevTools

1. **Navigate to:** http://localhost:3000
2. **Open Browser DevTools:**
   - Chrome/Edge: `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Firefox: `F12` or `Cmd+Option+K` (Mac) / `Ctrl+Shift+K` (Windows)
3. **Go to Console tab**
4. **Clear console:** Click the "Clear" button or press `Cmd+K` (Mac) / `Ctrl+L` (Windows)

---

### Step 2: Upload a Test Transcript

1. Click **"Upload Transcript"** button
2. Select a transcript file (e.g., `sample_meeting.txt`)
3. Configure settings or use defaults
4. Click **"Generate Document"**

---

### Step 3: Monitor the Console Output

**Watch for these log patterns:**

#### A) Normal Behavior (All Steps Visible)
```
[ProgressTracker] 📊 Poll Response: { current_step: 1, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: undefined, to: 1 }
[ProgressTracker] 🎨 Rendering: { current_step: 1 }

[ProgressTracker] 📊 Poll Response: { current_step: 2, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 1, to: 2 }
[ProgressTracker] 🎨 Rendering: { current_step: 2 }

[ProgressTracker] 📊 Poll Response: { current_step: 3, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 2, to: 3 }
[ProgressTracker] 🎨 Rendering: { current_step: 3 }

[ProgressTracker] 📊 Poll Response: { current_step: 4, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 3, to: 4 }
[ProgressTracker] 🎨 Rendering: { current_step: 4 }

[ProgressTracker] 📊 Poll Response: { current_step: 5, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 4, to: 5 }
[ProgressTracker] 🎨 Rendering: { current_step: 5 }

... continues through step 9 ...
```

✅ **This is CORRECT** - You should see ALL steps 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

#### B) Bug Behavior (Stops at Step 4)
```
[ProgressTracker] 📊 Poll Response: { current_step: 1, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: undefined, to: 1 }
[ProgressTracker] 🎨 Rendering: { current_step: 1 }

[ProgressTracker] 📊 Poll Response: { current_step: 2, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 1, to: 2 }
[ProgressTracker] 🎨 Rendering: { current_step: 2 }

[ProgressTracker] 📊 Poll Response: { current_step: 3, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 2, to: 3 }
[ProgressTracker] 🎨 Rendering: { current_step: 3 }

[ProgressTracker] 📊 Poll Response: { current_step: 4, total_steps: 9 }
[ProgressTracker] ✅ Step Changed: { from: 3, to: 4 }
[ProgressTracker] 🎨 Rendering: { current_step: 4 }

[ProgressTracker] 📊 Poll Response: { current_step: 4, total_steps: 9 }  ← STUCK!
[ProgressTracker] 📊 Poll Response: { current_step: 4, total_steps: 9 }  ← STUCK!
[ProgressTracker] 📊 Poll Response: { current_step: 4, total_steps: 9 }  ← STUCK!

... many polls with same value ...

[ProgressTracker] 📊 Poll Response: { current_step: 9, total_steps: 9 }  ← Jumped to final!
[ProgressTracker] ✅ Step Changed: { from: 4, to: 9 }
```

❌ **This is the BUG** - API keeps returning `current_step: 4`, then jumps to 9

---

### Step 4: Check What the Logs Tell Us

The console logs will reveal which scenario is happening:

| Log Pattern | Root Cause | What's Wrong |
|-------------|------------|--------------|
| **Poll Response shows: 4, 4, 4, 4** | Backend not updating Cosmos DB | Backend pipeline issue |
| **Poll Response shows: 4, 5, 6, 7 BUT no "Step Changed"** | React state not updating | Frontend state management issue |
| **"Step Changed" logs BUT no "Rendering" logs** | React not re-rendering | Component rendering issue |
| **All logs show 1→2→3→4→9 (skipping 5-8)** | Timing issue - steps generate too fast | Polling frequency too slow |
| **All logs show all steps 1-9** | No bug! | Working correctly ✅ |

---

## Step 5: Also Check Backend Logs

While the job is processing, check backend logs:

```bash
cd backend
tail -f backend_server.log | grep -E "(Generating step|Updated job|current_step)"
```

**You should see:**
```
2025-12-04 11:30:00 - Generating step 1/9 from chunk (450 chars)
2025-12-04 11:30:00 - Updated job abc-123: processing (44%) - generate_steps | Generating step 1 of 9
2025-12-04 11:30:20 - Generating step 2/9 from chunk (480 chars)
2025-12-04 11:30:20 - Updated job abc-123: processing (48%) - generate_steps | Generating step 2 of 9
2025-12-04 11:30:40 - Generating step 3/9 from chunk (520 chars)
2025-12-04 11:30:40 - Updated job abc-123: processing (51%) - generate_steps | Generating step 3 of 9
2025-12-04 11:31:00 - Generating step 4/9 from chunk (490 chars)
2025-12-04 11:31:00 - Updated job abc-123: processing (55%) - generate_steps | Generating step 4 of 9
2025-12-04 11:31:20 - Generating step 5/9 from chunk (510 chars)
2025-12-04 11:31:20 - Updated job abc-123: processing (58%) - generate_steps | Generating step 5 of 9
...
```

**Check:**
- ✅ Are ALL steps being generated? (1, 2, 3, 4, 5, 6, 7, 8, 9)
- ✅ Is Cosmos DB being updated for EACH step?
- ⏱️ How long between each step? (affects whether frontend polling catches them)

---

## What to Report Back

Please provide the following information:

### 1. Visual Behavior
- [ ] Did the step counter update through ALL steps (1→2→3→4→5→6→7→8→9)?
- [ ] Or did it stop at step 4 and then jump to completion?
- [ ] Which step number did it stop at?

### 2. Frontend Console Logs
Copy and paste the console logs showing:
- The "Poll Response" logs
- The "Step Changed" logs
- The "Rendering" logs

**Example:**
```
[ProgressTracker] 📊 Poll Response: { current_step: 1, ... }
[ProgressTracker] ✅ Step Changed: { from: undefined, to: 1 }
[ProgressTracker] 🎨 Rendering: { current_step: 1 }
... paste all logs ...
```

### 3. Backend Logs
Copy and paste the backend logs showing step generation:
```bash
cd backend
tail -100 backend_server.log | grep -E "(Generating step|Updated job)"
```

### 4. Timing Information
From the backend logs, calculate:
- How many seconds between each step generation?
- Total time for all steps?
- Is it faster or slower than 2 seconds per step?

---

## Quick Diagnostic

**If frontend console shows all steps 1-9 but you didn't SEE them:**
→ Steps might be generating too fast (< 2 seconds each)
→ Solution: Reduce polling interval from 2s to 500ms

**If frontend console shows 1, 2, 3, 4, then jumps to 9:**
→ Backend is not updating Cosmos DB for steps 5-8
→ Solution: Check backend logs for errors during those steps

**If frontend console shows all steps BUT no "Step Changed" logs:**
→ React state is not updating properly
→ Solution: Investigate React state management

---

## Current Status

- ✅ Backend server running (port 8000)
- ✅ Frontend dev server running (port 3000)
- ✅ Debug logging added to frontend
- ✅ Cache-busting headers added
- ⏳ Waiting for test results

---

## Next Steps

Based on your test results, I will:

1. **If logs show API returning stale data (4, 4, 4, 4):**
   → Investigate backend Cosmos DB updates

2. **If logs show API returning new data BUT React not updating:**
   → Investigate React state management

3. **If logs show all steps but timing < 2s per step:**
   → Reduce polling interval or implement WebSockets

4. **If logs show all steps and everything works:**
   → Close the bug as "cannot reproduce" and document expected behavior

---

**Please run the test and report back with the console logs and visual behavior!**

---

**Last Updated:** December 4, 2025
**Status:** Ready for user testing
**Files Modified:**
- `frontend/components/ProgressTracker.tsx` (added debug logging)
- `frontend/lib/api.ts` (added cache-busting headers)
