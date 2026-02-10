# Azure Blob Storage Pricing Calculator - Configuration Guide

## ⚠️ Important: You're on the Wrong Page

The "Azure Storage Discovery" page you're seeing is for **analyzing** storage accounts, not for pricing regular Blob Storage.

You need to find the **"Azure Blob Storage"** pricing calculator instead.

---

## Step-by-Step: Finding the Correct Blob Storage Calculator

### Step 1: Navigate to Pricing Calculator

1. Go to [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
2. In the search box, type: **"Storage Accounts"** (NOT "Storage Discovery" or "Blob Storage")
3. Select **"Storage Accounts"** from the results
   - This is the correct service name in the calculator
   - It includes Blob Storage pricing

### Step 2: Configure Storage Accounts

Once you've added "Storage Accounts" to your estimate, configure:

**A. Region:**
- Select: **East US** (or your region)

**B. Performance Tier:**
- Select: **Standard** (NOT Premium)

**C. Redundancy:**
- Select: **Locally Redundant Storage (LRS)**
- This matches your configuration: `Standard_LRS`

**D. Access Tier:**
- Select: **Hot** (for frequently accessed files)
- This matches your configuration: `accessTier: 'Hot'`

**E. Storage Capacity:**
- Enter estimated storage in GB
- **Typical estimate:** 100 GB
- **Your actual usage:** Check your Azure Portal for current usage
- **Breakdown:**
  - Uploads: ~20-50 GB (transcripts, screenshots)
  - Documents: ~30-50 GB (generated Word documents)
  - Temp: ~10 GB (auto-deleted after 24h)

**F. Data Operations:**
- **Write Operations:** ~5,000/month
  - File uploads
  - Document generation
- **Read Operations:** ~5,000/month
  - Document downloads
  - Status checks
- **List Operations:** ~1,000/month
  - Container listings
  - Job queries

**G. Data Transfer:**
- **Outbound Data:** ~10-20 GB/month
  - Document downloads
  - API responses

---

## Your Actual Configuration

From your infrastructure code (`azure-infrastructure.bicep`):

```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  sku: {
    name: 'Standard_LRS'  // ← Locally Redundant Storage
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'  // ← Hot tier for frequent access
  }
}
```

**Containers:**
- `uploads/` - User-uploaded transcripts and files
- `documents/` - Generated Word documents
- `temp/` - Temporary processing files (auto-deleted after 24h)

---

## Cost Breakdown Example

For **100 GB storage** with your usage pattern:

| Component | Quantity | Cost |
|-----------|----------|------|
| **Storage (Hot, LRS)** | 100 GB | ~CA$2.00/month |
| **Write Operations** | 5,000 | ~CA$0.10/month |
| **Read Operations** | 5,000 | ~CA$0.10/month |
| **List Operations** | 1,000 | ~CA$0.01/month |
| **Data Transfer (Outbound)** | 15 GB | ~CA$1.80/month |
| **TOTAL** | | **~CA$4.01/month** |

**Note:** Your actual cost from the invoice shows ~CA$25/month, which suggests:
- Higher storage usage (500+ GB)
- More transactions
- Or includes other storage services

---

## What NOT to Use

**❌ Azure Storage Discovery:**
- This is for analyzing storage accounts
- Shows "$0.00" because it's not a pricing calculator
- Used for finding unused storage, not cost estimation

**✅ Storage Accounts:**
- This is the correct pricing calculator
- Shows actual storage and transaction costs
- Use this for cost estimation
- In the calculator, search for "Storage Accounts"

---

## Quick Reference: Correct Settings

```
Service: Storage Accounts (search for this in calculator)
Region: East US
Performance: Standard
Redundancy: Locally Redundant Storage (LRS)
Access Tier: Hot
Storage: 100-500 GB (estimate based on usage)
Write Operations: 5,000/month
Read Operations: 5,000/month
List Operations: 1,000/month
Data Transfer: 10-20 GB/month
Monthly Cost: CA$4-25/month (depending on storage size)
```

---

## Troubleshooting

### Problem: Can't find "Blob Storage" in search

**Solution:**
1. Search for **"Storage Accounts"** (this is the correct name)
2. Do NOT search for "Blob Storage" - it's not listed that way
3. Do NOT use "Storage Discovery" - that's a different service
4. The service is called "Storage Accounts" in the pricing calculator

### Problem: Calculator shows $0.00

**Solution:**
- You might be on "Storage Discovery" page
- Go back and search for "Blob Storage" specifically
- Make sure you're configuring storage capacity and operations

### Problem: Don't know actual storage usage

**Solution:**
1. Go to Azure Portal
2. Navigate to your Storage Account
3. Check "Overview" → "Capacity" section
4. Use that number in the calculator

---

## Lifecycle Policies (Cost Optimization)

Your application has lifecycle policies configured:

**Temp Files:**
- Auto-deleted after 1 day
- Saves storage costs on temporary processing files

**Documents:**
- Could be moved to Cool tier after 30 days (optional)
- Would save ~50% on storage costs for old documents

**Current Configuration:**
```bicep
lifecyclePolicy: {
  rules: [
    {
      name: 'delete-temp-files'
      // Deletes temp/ files after 1 day
    },
    {
      name: 'delete-old-documents'
      // Deletes documents/uploads after 90 days
    }
  ]
}
```

---

## Next Steps

1. ✅ Search for **"Storage Accounts"** (this is the correct service name)
2. ✅ Configure with settings above
3. ✅ Enter your actual storage usage from Azure Portal
4. ✅ Add to estimate
5. ✅ Export for your manager

---

**Last Updated:** January 2025
