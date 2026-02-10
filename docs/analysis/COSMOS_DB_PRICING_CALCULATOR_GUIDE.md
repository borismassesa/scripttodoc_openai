# Cosmos DB Pricing Calculator - Correct Configuration Guide

## ⚠️ Important: Your Application Uses Serverless Mode

Your Script to Doc application uses **Cosmos DB Serverless**, which costs **CA$0.01/month** (not $175.66/month).

The pricing calculator defaults to **Provisioned Capacity** mode, which is much more expensive. Follow these steps to configure it correctly.

---

## Step-by-Step: Configuring Cosmos DB Serverless in Pricing Calculator

### Step 1: Add Cosmos DB to Calculator

1. Go to [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
2. Search for "Cosmos DB"
3. Click "Add to estimate"

### Step 2: Select the Correct API

**⚠️ CRITICAL:** In the "API" dropdown, select:
- ✅ **"Azure Cosmos DB for NoSQL (formerly Core)"**

**❌ DO NOT select:**
- ❌ Azure Cosmos DB for Apache Cassandra (what you currently have selected)
- ❌ Azure Cosmos DB for PostgreSQL
- ❌ Azure Cosmos DB for MongoDB
- ❌ Azure Cosmos DB for Apache Gremlin
- ❌ Azure Cosmos DB for Table

### Step 3: Select Serverless Mode

After selecting "NoSQL", you should see capacity mode options:

**✅ Select: "Serverless" or "Pay-per-request"**

**❌ DO NOT select:**
- ❌ "Provisioned throughput"
- ❌ "Autoscale"
- ❌ "Single Node" (this is for PostgreSQL API)
- ❌ Any option showing "vCore" or "GiB RAM"

### Step 4: Configure Serverless Settings

Once in Serverless mode, you'll see:

- **Region:** East US (or your region)
- **Request Units (RU):** Enter your estimated monthly consumption
  - **Your actual usage:** ~50 RU/month = CA$0.01/month
  - **Typical estimate:** 10,000 RU/month = ~CA$0.28/month
  - **Heavy usage:** 100,000 RU/month = ~CA$2.80/month

- **Storage:** ~1 GB (estimated)
  - Cost: ~CA$0.25/GB/month

### Step 5: Verify Configuration

**✅ Correct Configuration Shows:**
- Pricing: "$0.28 per 1M RU" or similar
- Monthly cost: < $10 for typical usage
- No mention of "vCore", "GiB RAM", or "per hour"

**❌ Wrong Configuration Shows:**
- Pricing: "$0.110 per hour" or similar
- Monthly cost: $100+ 
- Shows "2 vCore, 8 GiB RAM"
- Shows "Single Node" or "Tier" dropdown

---

## Cost Comparison

| Mode | Configuration | Monthly Cost | Your Usage |
|------|--------------|-------------|-----------|
| **Serverless** ✅ | Pay-per-request | CA$0.01 | **What you're using** |
| Provisioned Capacity ❌ | 2 vCore, 8 GiB | $175.66 | What calculator defaulted to |

---

## Why Serverless is Perfect for Your Use Case

**Your Application:**
- Low to moderate traffic
- Variable request patterns
- Cost optimization priority
- Job status storage (not high-throughput)

**Serverless Benefits:**
- ✅ Pay only for requests you make
- ✅ No minimum charges (unlike provisioned)
- ✅ Automatic scaling
- ✅ Perfect for variable workloads

**Provisioned Capacity:**
- ❌ Pay for capacity even when idle
- ❌ Minimum $175+/month
- ❌ Overkill for your use case
- ❌ Better for high-throughput, steady workloads

---

## Your Actual Cosmos DB Configuration

From your infrastructure code (`azure-infrastructure.bicep`):

```bicep
capabilities: [
  {
    name: 'EnableServerless'  // ← This enables Serverless mode
  }
]
```

**Current Usage:**
- **API:** NoSQL (Core)
- **Mode:** Serverless
- **Region:** East US
- **Monthly Cost:** CA$0.01
- **Monthly RU Consumption:** ~50 RU

---

## Troubleshooting

### Problem: Calculator shows $175.66/month

**Solution:** You're in Provisioned Capacity mode. Look for:
1. API dropdown - change to "NoSQL"
2. Capacity mode - change to "Serverless"
3. Remove any "vCore" or "Tier" selections

### Problem: Can't find Serverless option

**Solution:** 
1. Make sure you selected "Azure Cosmos DB for NoSQL"
2. Some APIs (PostgreSQL, MongoDB vCore) don't support Serverless
3. Only NoSQL, MongoDB (RU), and Table APIs support Serverless

### Problem: Still showing high costs

**Solution:**
- Check the "Request Units" field - it might be set too high
- For your usage, enter 50-100 RU/month
- Serverless pricing: $0.28 per 1M RU
- 50 RU = $0.000014 = essentially free

---

## Quick Reference: Correct Settings

```
API: Azure Cosmos DB for NoSQL (formerly Core)
Capacity Mode: Serverless
Region: East US
Request Units: 50-10,000 RU/month (depending on usage)
Storage: 1 GB
Monthly Cost: CA$0.01 - CA$3.00
```

---

## Next Steps

1. ✅ Update your pricing calculator with Serverless mode
2. ✅ Verify monthly cost shows < $10
3. ✅ Export estimate for your manager
4. ✅ Reference this guide if you need to recalculate

---

**Last Updated:** January 2025
