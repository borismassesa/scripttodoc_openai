# Stage Labels & Navigation Redesign

**Date:** December 4, 2025
**Issues:** Poor stage label design, step count mismatch, stuck in Active tab
**Status:** 🔄 Implementing fixes

---

## Issue 1: Poor Stage Label Design

### Current Problems:
```
[●][●][●][●][●][●][●][○][○][○][○]
 ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓
Queued
Loading Transcript
Cleaning Text        ← Tiny, hard to read
Fetching Knowledge   ← Cramped
Analyzing Document   ← Multiple rows
Planning Steps       ← Confusing layout
Generating Steps     ← Current (but also header!)
Building Citations
Validating Quality
Creating Document
Finalizing
```

**Problems:**
- Text too small (10px)
- Labels cramped under circles
- Multiple rows create visual mess
- Redundant: "Generating Steps" appears twice
- Hard to scan quickly
- Doesn't scale on mobile

---

## Solution 1: Grouped Phase Design

### NEW: 3 Logical Phases

Instead of 11 individual stages, group into 3 phases:

```
┌─────────────────────────────────────────────────────┐
│ ✓ Phase 1: Setup & Analysis                        │
│   5 stages complete                                 │
│                                                     │
│ ● Phase 2: Content Generation (current)            │
│   Generating step 3 of 15                          │
│   2 of 3 stages complete                           │
│                                                     │
│ ○ Phase 3: Quality & Finalization                  │
│   0 of 3 stages complete                           │
└─────────────────────────────────────────────────────┘
```

**Benefits:**
- Clearer progress flow
- Easier to scan
- Better use of space
- Mobile-friendly
- No tiny text

---

## Phase Groupings

### Phase 1: Setup & Analysis (5 stages)
- ✓ Queued
- ✓ Loading Transcript
- ✓ Cleaning Text
- ✓ Fetching Knowledge
- ✓ Analyzing Document

### Phase 2: Content Generation (3 stages)
- ✓ Planning Steps
- ● Generating Steps ← Current
- ○ Building Citations

### Phase 3: Quality & Finalization (3 stages)
- ○ Validating Quality
- ○ Creating Document
- ○ Finalizing

---

## Issue 2: Step Count Mismatch

### Problem:
Frontend shows: **"Generating step 3 of 15"**
Backend might be generating different number

### Investigation Needed:
1. Check backend: How many steps does it actually generate?
2. Check frontend: Where does "15" come from?
3. Fix the mismatch

### Likely Cause:
```tsx
// Frontend might be showing total chunks instead of total steps
job.current_step // ← Step being generated
job.total_steps  // ← Total steps to generate
```

Backend might be:
- Generating 8 steps (from topic segmentation)
- But frontend showing 15 (from chunk count?)

---

## Issue 3: Stuck in Active Tab

### Problem:
User can't navigate away from Active tab

### Possible Causes:
1. No tab navigation UI visible
2. Tabs not clickable
3. Jobs not moving to History after completion

### Solution:
Add clear tab navigation with:
- Active tab indicator
- Clickable tabs
- Auto-switch to History when all jobs complete (optional)

---

## Implementation Plan

### Fix 1: Redesign Stage Display

**Option A: Phase Cards (Recommended)**
```tsx
<div className="space-y-3">
  <PhaseCard
    name="Setup & Analysis"
    status="completed"
    stagesComplete={5}
    stagesTotal={5}
  />
  <PhaseCard
    name="Content Generation"
    status="in_progress"
    stagesComplete={2}
    stagesTotal={3}
    detail="Generating step 3 of 15"
  />
  <PhaseCard
    name="Quality & Finalization"
    status="pending"
    stagesComplete={0}
    stagesTotal={3}
  />
</div>
```

**Option B: Simplified Labels**
```tsx
<div className="flex items-center justify-between text-sm">
  <span className="text-green-700 font-semibold">
    ✓ Setup (5/5)
  </span>
  <span className="text-blue-700 font-bold">
    ● Generation (2/3) ← Generating step 3 of 15
  </span>
  <span className="text-gray-500">
    ○ Finalization (0/3)
  </span>
</div>
```

**Option C: Progress Bar with Labels**
```tsx
<div className="relative">
  {/* Progress bar */}
  <div className="h-2 bg-gray-200 rounded-full">
    <div className="h-full bg-blue-500" style={{ width: '44%' }} />
  </div>

  {/* Phase markers */}
  <div className="flex justify-between mt-2 text-xs">
    <span className="text-green-700 font-semibold">Setup ✓</span>
    <span className="text-blue-700 font-bold">Generation ●</span>
    <span className="text-gray-500">Finalization</span>
  </div>
</div>
```

---

## Mockup: Before vs After

### BEFORE (Current - Poor Design)
```
┌────────────────────────────────────────────────────┐
│ Generating Steps                    44%   4m 16s   │
│ Generating step 3 of 15                            │← Mismatch?
│                                                    │
│ ▰▰▰▰▱▱▱▱▱▱                                         │
│                                                    │
│ [●●●] Generating Step 3 of 15                      │
│                                                    │
│ [▲ Hide Progress Details]              11 stages  │
│                                                    │
│ [✓][✓][✓][✓][✓][✓][●][○][○][○][○]                │← Circles
│  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓                 │
│ Queued                                             │← Tiny!
│ Loading Transcript                                 │
│ Cleaning Text                                      │
│ Fetching Knowledge                                 │
│ Analyzing Document                                 │
│ Planning Steps                                     │
│ Generating Steps  ← Current                        │
│ Building Citations                                 │
│ Validating Quality                                 │
│ Creating Document                                  │
│ Finalizing                                         │
└────────────────────────────────────────────────────┘
```

### AFTER (New - Clean Design)
```
┌────────────────────────────────────────────────────┐
│ Generating step 3 of 15                            │← CLEAR!
│                                                    │
│ ▰▰▰▰▱▱▱▱▱▱ 44%                        4m 16s      │
│                                                    │
│ [●●●] Generating Step 3 of 15                      │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ ✓ Phase 1: Setup & Analysis                  │  │← Clean!
│ │   All 5 stages complete                      │  │
│ │                                               │  │
│ │ ● Phase 2: Content Generation (current)      │  │
│ │   Generating step 3 of 15                    │  │
│ │   Progress: Planning ✓ · Generating ● ·      │  │
│ │            Building ○                         │  │
│ │                                               │  │
│ │ ○ Phase 3: Quality & Finalization            │  │
│ │   Pending (0 of 3 stages)                    │  │
│ └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

---

## Component Design: PhaseCard

```tsx
interface PhaseCardProps {
  name: string;
  status: 'completed' | 'in_progress' | 'pending';
  stagesComplete: number;
  stagesTotal: number;
  detail?: string;
  stages?: string[];
}

function PhaseCard({ name, status, stagesComplete, stagesTotal, detail, stages }: PhaseCardProps) {
  return (
    <div className={cn(
      'p-4 rounded-lg border-2 transition-all',
      status === 'completed' && 'bg-green-50 border-green-300',
      status === 'in_progress' && 'bg-blue-50 border-blue-400 shadow-md',
      status === 'pending' && 'bg-gray-50 border-gray-200'
    )}>
      {/* Phase header */}
      <div className="flex items-center space-x-2 mb-2">
        {status === 'completed' && <CheckCircle className="h-5 w-5 text-green-600" />}
        {status === 'in_progress' && <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />}
        {status === 'pending' && <Circle className="h-5 w-5 text-gray-400" />}

        <h4 className={cn(
          'font-semibold',
          status === 'completed' && 'text-green-900',
          status === 'in_progress' && 'text-blue-900',
          status === 'pending' && 'text-gray-500'
        )}>
          {name}
        </h4>
      </div>

      {/* Progress detail */}
      {detail && status === 'in_progress' && (
        <p className="text-sm text-blue-700 font-medium mb-2">{detail}</p>
      )}

      {/* Stage progress */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-600">
          {stagesComplete} of {stagesTotal} stages {status === 'completed' ? 'complete' : status === 'in_progress' ? 'in progress' : 'pending'}
        </span>

        {status !== 'pending' && (
          <div className="flex items-center space-x-1">
            {stages?.map((stage, idx) => (
              <span key={idx} className={cn(
                'text-xs',
                idx < stagesComplete ? 'text-green-600' : 'text-gray-400'
              )}>
                {idx < stagesComplete ? '✓' : '○'}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Optional: Stage names */}
      {stages && status === 'in_progress' && (
        <div className="mt-2 flex flex-wrap gap-1">
          {stages.map((stage, idx) => (
            <span key={idx} className={cn(
              'text-[10px] px-2 py-0.5 rounded-full',
              idx < stagesComplete && 'bg-green-100 text-green-700',
              idx === stagesComplete && 'bg-blue-100 text-blue-700 font-semibold',
              idx > stagesComplete && 'bg-gray-100 text-gray-500'
            )}>
              {stage}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Next Steps

1. ✅ Implement PhaseCard component
2. ✅ Replace timeline with phase cards
3. ✅ Fix step count mismatch
4. ✅ Add tab navigation (if missing)
5. ✅ Test on mobile

---

**Status:** Ready for implementation
**Priority:** High - Poor UX affecting user experience
