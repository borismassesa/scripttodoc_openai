# Azure OpenAI Deployment Setup Guide

## Current Issue

Your jobs are failing because the Azure OpenAI deployment `gpt-4o-mini` doesn't exist in your Azure OpenAI resource. The system is falling back to your personal OpenAI API, which has hit rate limits (3 RPM, 100k TPM exhausted).

## Solution 1: Create Azure OpenAI Deployment (Recommended)

### Step 1: Access Azure Portal
1. Go to https://portal.azure.com
2. Sign in with your Azure credentials

### Step 2: Navigate to Your OpenAI Resource
1. In the search bar, type "openai-scripttodoc-dev"
2. Click on your Azure OpenAI resource

### Step 3: Create Deployment
1. In the left sidebar, click **"Deployments"** (under "Resource Management")
2. Click **"+ Create"** or **"Create new deployment"**
3. Fill in the deployment details:
   - **Deployment name**: `gpt-4o-mini` (must match .env file)
   - **Model**: Select `gpt-4o-mini` from the dropdown
   - **Model version**: Use the latest available
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: Set based on your quota (recommend 30K+)
4. Click **"Create"**

### Step 4: Verify Deployment
1. Wait for deployment to finish (usually takes 1-2 minutes)
2. Verify the deployment appears in your deployments list
3. Note the deployment name matches: `gpt-4o-mini`

### Step 5: Restart Backend
```bash
cd backend
# Kill any running processes
pkill -f "uvicorn"

# Restart the API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Solution 2: Use Existing Deployment (Alternative)

If you already have a different deployment (e.g., `gpt-4o`, `gpt-35-turbo`), you can update your `.env` file:

1. Open `/Users/boris/AZURE AI Document Intelligence/backend/.env`
2. Find the line: `AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini`
3. Change it to match your existing deployment name
4. Restart the backend (see Step 5 above)

## Solution 3: Upgrade OpenAI Account (Temporary)

If you can't access Azure Portal right now:

1. Go to https://platform.openai.com/account/billing
2. Add a payment method
3. This will increase your rate limits from:
   - 3 requests/min → 500+ requests/min
   - 100k tokens/min → 200k+ tokens/min

**Note**: This is a temporary solution. Azure OpenAI is recommended for production use.

## Verifying the Fix

After implementing one of the solutions above:

1. Upload a new transcript in the frontend
2. Watch the backend logs for:
   - ✅ "Initialized Azure OpenAI client with deployment: gpt-4o-mini"
   - ✅ "Generated X steps using Azure OpenAI"
   - ❌ No more "DeploymentNotFound" errors
   - ❌ No more "Rate limit exceeded" errors

## Current Configuration

Your `.env` file currently has:
```
AZURE_OPENAI_ENDPOINT=https://openai-scripttodoc-dev.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

## What Was Fixed

I've improved the error handling to:

1. **Better Error Messages**: When rate limits or deployment errors occur, you now get clear, actionable instructions
2. **Improved Frontend Display**: Error messages are parsed and displayed with numbered steps in a user-friendly format
3. **Detailed Logging**: Backend logs now show exactly which error occurred and why

## Next Steps

1. Choose one of the solutions above (Solution 1 recommended)
2. Implement the fix
3. Restart the backend
4. Try uploading a transcript again
5. The jobs should now process successfully using Azure OpenAI

## Need Help?

If you encounter issues:
- Check backend logs: Look for errors in the terminal running uvicorn
- Verify Azure quota: Ensure your Azure subscription has OpenAI quota allocated
- Check deployments: In Azure Portal, verify the deployment exists and is "Succeeded"
