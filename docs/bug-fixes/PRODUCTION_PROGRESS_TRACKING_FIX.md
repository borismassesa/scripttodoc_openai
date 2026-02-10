# Production Progress Tracking Fix

**Date:** December 15, 2025
**Issue:** Progress tracking (step counter, stages) not working in production
**Status:** ✅ Fixed

---

## 🐛 Root Cause

The production frontend was built with the **wrong API URL hardcoded** in the Docker image. Next.js `NEXT_PUBLIC_*` environment variables are embedded at **build time**, not runtime.

### Issues Found:

1. **Hardcoded API URL in Dockerfile**: Used development API instead of production
2. **API URL Mismatch**: Three different URLs across different files
3. **No Build Arguments**: Dockerfile didn't accept dynamic API URL configuration

---

## ✅ Fix Applied

### 1. Updated Dockerfile ([frontend/Dockerfile](../../frontend/Dockerfile))

**Before:**
```dockerfile
ENV NEXT_PUBLIC_API_URL=https://ca-scripttodoc-development-api...
```

**After:**
```dockerfile
ARG NEXT_PUBLIC_API_URL=https://ca-scripttodoc-prod-api...
ARG NEXT_PUBLIC_ENVIRONMENT=production
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ENVIRONMENT=${NEXT_PUBLIC_ENVIRONMENT}
```

### 2. Updated Deployment Script ([deployment/deploy-frontend-containerapp.sh](../../deployment/deploy-frontend-containerapp.sh))

**Fixed API URL:**
```bash
API_URL="https://ca-scripttodoc-prod-api.delightfuldune-05b8c4e7.eastus.azurecontainerapps.io"
```

**Pass as Build Argument:**
```bash
docker buildx build \
  --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
  --build-arg NEXT_PUBLIC_ENVIRONMENT="production" \
  ...
```

### 3. Enhanced ProgressTracker UI ([frontend/components/ProgressTracker.tsx](../../frontend/components/ProgressTracker.tsx))

- Step counter now **always visible** at top (not buried in timeline)
- Timeline **expanded by default** (was hidden)
- Better logging for debugging
- Real-time status updates in each phase

---

## 🚀 How to Deploy the Fix

### Step 1: Rebuild and Deploy Frontend

```bash
cd deployment
./deploy-frontend-containerapp.sh
```

This will:
- ✅ Build Docker image with **correct production API URL**
- ✅ Push to Azure Container Registry
- ✅ Deploy to Azure Container Apps
- ⏱️ Takes ~5 minutes

### Step 2: Verify Deployment

1. Visit your production URL (output from deployment script)
2. Open browser DevTools (F12) → Console tab
3. Upload a transcript and click "Generate Training Document"
4. You should see:
   - ✅ Logs: `[ProgressTracker] 📊 Poll Response: { stage: "generate_steps", current_step: 2, total_steps: 8 }`
   - ✅ UI: "Processing Step 2 of 8" counter at the top
   - ✅ Expanded timeline with all 3 phases visible

### Step 3: Clear Browser Cache (If Needed)

If you still see old behavior:
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Or clear browser cache and reload

---

## 📊 What Users Will See (After Fix)

### Active Tab Progress Display:

```
┌─────────────────────────────────────────────────┐
│ 🔄 Generating Steps                      45%    │
├─────────────────────────────────────────────────┤
│ 🔵 Processing Step 3 of 8                       │
│ ━━━━━━━━━━━━━━━━━░░░░░░░░░░                     │
├─────────────────────────────────────────────────┤
│ ▼ Show Progress Details (13 stages)            │
│                                                 │
│ ✅ Phase 1: Setup & Analysis                    │
│    [Queued] [Loading] [Cleaning] ...           │
│                                                 │
│ 🔵 Phase 2: Content Generation                  │
│    ⏳ Generating step 3 of 8                    │
│    [Planning] [Generating●] [Building]         │
│                                                 │
│ ⚪ Phase 3: Quality & Finalization              │
│    [Validating] [Creating] [Finalizing]        │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Why This Happened

Next.js has **two types** of environment variables:

1. **Runtime Variables** (server-side only)
   - Example: `API_KEY`, `DATABASE_URL`
   - Can be changed after build

2. **Build-Time Variables** (`NEXT_PUBLIC_*`)
   - Example: `NEXT_PUBLIC_API_URL`
   - **Embedded into JavaScript bundles during build**
   - Cannot be changed after build without rebuilding

Our `NEXT_PUBLIC_API_URL` was hardcoded in the Dockerfile, so every production build used the wrong API URL.

---

## ✅ Verification Checklist

After deploying, verify:

- [ ] Frontend loads without errors
- [ ] Console shows `[ProgressTracker] 📊 Poll Response` logs every 2 seconds
- [ ] "Processing Step X of Y" counter appears when generating steps
- [ ] Timeline shows all 3 phases expanded by default
- [ ] Progress updates in real-time (every 2 seconds)
- [ ] API calls go to **prod-api** URL (check Network tab in DevTools)

---

## 📝 Related Files

- [frontend/Dockerfile](../../frontend/Dockerfile) - Build-time API URL configuration
- [frontend/components/ProgressTracker.tsx](../../frontend/components/ProgressTracker.tsx) - UI enhancements
- [deployment/deploy-frontend-containerapp.sh](../../deployment/deploy-frontend-containerapp.sh) - Deployment script
- [frontend/.env.production](../../frontend/.env.production) - Production environment variables

---

## 🎯 Success Criteria

✅ **Production now matches development behavior:**
- Real-time step counter updates
- Visible progress timeline
- Detailed console logging
- Correct API URL

---

**Fixed by:** Claude Code
**Tested:** ⏳ Pending deployment verification
