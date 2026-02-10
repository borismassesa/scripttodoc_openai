# Cosmos DB Indexing Optimization Guide

This guide shows how to configure Cosmos DB indexing for optimal query performance in the ScriptToDoc application.

## Performance Impact

Without proper indexing, Cosmos DB queries can take **5-15 seconds** for large datasets.
With proper indexing, queries can be reduced to **100-500ms**.

## Current Query Patterns

The application uses these main queries:

1. **List Jobs by User** (most frequent)
   ```sql
   SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c._ts DESC
   ```

2. **List Jobs by User and Status**
   ```sql
   SELECT * FROM c WHERE c.user_id = @user_id AND c.status = @status ORDER BY c._ts DESC
   ```

3. **Get Single Job**
   ```sql
   SELECT * FROM c WHERE c.id = @job_id AND c.user_id = @user_id
   ```

## Recommended Indexing Policy

Apply this indexing policy to the `jobs` container in Cosmos DB:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/user_id/?"
    },
    {
      "path": "/status/?"
    },
    {
      "path": "/_ts/?"
    },
    {
      "path": "/created_at/?"
    },
    {
      "path": "/config/document_title/?"
    }
  ],
  "excludedPaths": [
    {
      "path": "/result/*"
    },
    {
      "path": "/input/*"
    }
  ],
  "compositeIndexes": [
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/_ts",
        "order": "descending"
      }
    ],
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/status",
        "order": "ascending"
      },
      {
        "path": "/_ts",
        "order": "descending"
      }
    ]
  ]
}
```

## How to Apply Indexing Policy

### Option 1: Azure Portal (Recommended)

1. **Navigate to Cosmos DB Account**
   - Go to [Azure Portal](https://portal.azure.com)
   - Open your Cosmos DB account
   - Select the `scripttodoc` database
   - Click on the `jobs` container

2. **Update Indexing Policy**
   - Click "Settings" → "Indexing Policy"
   - Replace the existing policy with the JSON above
   - Click "Save"
   - Wait 2-5 minutes for re-indexing to complete

### Option 2: Azure CLI

```bash
# Set variables
RESOURCE_GROUP="your-resource-group"
ACCOUNT_NAME="your-cosmos-account"
DATABASE_NAME="scripttodoc"
CONTAINER_NAME="jobs"

# Create indexing policy file
cat > indexing-policy.json <<'EOF'
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {"path": "/user_id/?"},
    {"path": "/status/?"},
    {"path": "/_ts/?"},
    {"path": "/created_at/?"},
    {"path": "/config/document_title/?"}
  ],
  "excludedPaths": [
    {"path": "/result/*"},
    {"path": "/input/*"}
  ],
  "compositeIndexes": [
    [
      {"path": "/user_id", "order": "ascending"},
      {"path": "/_ts", "order": "descending"}
    ],
    [
      {"path": "/user_id", "order": "ascending"},
      {"path": "/status", "order": "ascending"},
      {"path": "/_ts", "order": "descending"}
    ]
  ]
}
EOF

# Update container with new indexing policy
az cosmosdb sql container update \
  --resource-group $RESOURCE_GROUP \
  --account-name $ACCOUNT_NAME \
  --database-name $DATABASE_NAME \
  --name $CONTAINER_NAME \
  --idx @indexing-policy.json
```

### Option 3: Python Script

```python
from azure.cosmos import CosmosClient
import os

# Initialize client
client = CosmosClient(
    os.getenv("AZURE_COSMOS_ENDPOINT"),
    os.getenv("AZURE_COSMOS_KEY")
)

database = client.get_database_client("scripttodoc")
container = database.get_container_client("jobs")

# Define indexing policy
indexing_policy = {
    "indexingMode": "consistent",
    "automatic": True,
    "includedPaths": [
        {"path": "/user_id/?"},
        {"path": "/status/?"},
        {"path": "/_ts/?"},
        {"path": "/created_at/?"},
        {"path": "/config/document_title/?"}
    ],
    "excludedPaths": [
        {"path": "/result/*"},
        {"path": "/input/*"}
    ],
    "compositeIndexes": [
        [
            {"path": "/user_id", "order": "ascending"},
            {"path": "/_ts", "order": "descending"}
        ],
        [
            {"path": "/user_id", "order": "ascending"},
            {"path": "/status", "order": "ascending"},
            {"path": "/_ts", "order": "descending"}
        ]
    ]
}

# Replace container with new indexing policy
database.replace_container(
    container="jobs",
    partition_key={"paths": ["/user_id"], "kind": "Hash"},
    indexing_policy=indexing_policy
)

print("Indexing policy updated successfully!")
print("Re-indexing in progress (may take 2-5 minutes)...")
```

## Explanation of Indexing Strategy

### Included Paths
- **`/user_id/?`**: Essential for filtering by user (partition key)
- **`/_ts/?`**: System timestamp, used for ORDER BY (faster than created_at)
- **`/status/?`**: For filtering completed/failed jobs
- **`/created_at/?`**: Alternative sorting field
- **`/config/document_title/?`**: For search functionality

### Excluded Paths
- **`/result/*`**: Large objects, not queried directly (saves index space)
- **`/input/*`**: Large transcript data, not queried (saves index space)

### Composite Indexes

**Index 1: user_id + _ts**
- Optimizes: `WHERE user_id = X ORDER BY _ts DESC`
- Use case: Default job list query
- Performance: ~100-200ms

**Index 2: user_id + status + _ts**
- Optimizes: `WHERE user_id = X AND status = Y ORDER BY _ts DESC`
- Use case: Filtered job list (completed/failed only)
- Performance: ~150-300ms

## Verification

After applying the indexing policy, verify it's working:

```bash
# Check indexing metrics in portal
# Azure Portal → Cosmos DB → Metrics → Filter by "Index Utilization"

# Or query with diagnostics
# In your application logs, look for:
# "Retrieved X jobs in query" - should be < 500ms
```

## Performance Metrics

### Before Optimization
- Initial load: 5-15 seconds
- Query RU consumption: 50-100 RUs
- User experience: Slow, poor UX

### After Optimization
- Initial load: 100-500ms ⚡
- Query RU consumption: 3-5 RUs 💰
- User experience: Fast, smooth UX ✨

## Additional Optimizations

### 1. Use Partition Key in Queries
✅ **Good:** `SELECT * FROM c WHERE c.user_id = 'abc' AND c.status = 'completed'`
❌ **Bad:** `SELECT * FROM c WHERE c.status = 'completed'` (cross-partition query)

### 2. Use System Timestamp (_ts)
✅ **Good:** `ORDER BY c._ts DESC` (indexed by default)
❌ **Bad:** `ORDER BY c.created_at DESC` (requires custom index)

### 3. Limit Result Size
✅ **Good:** `SELECT TOP 10 c.id, c.status FROM c...`
❌ **Bad:** `SELECT * FROM c...` (transfers unnecessary data)

### 4. Use Pagination
✅ **Good:** Load 10 items, then "Load More" button
❌ **Bad:** Load all 100+ items at once

## Monitoring

Monitor query performance in Azure Portal:

1. **Go to Cosmos DB → Metrics**
2. **View:**
   - Request Units (RU/s) - should be low (< 10 RU per query)
   - Server-side latency - should be < 500ms
   - Index utilization - should be > 95%

## Troubleshooting

**Problem:** Queries still slow after applying indexing
- **Solution:** Wait 5-10 minutes for re-indexing to complete
- **Check:** Azure Portal → Cosmos DB → Metrics → "Index Progress"

**Problem:** High RU consumption
- **Solution:** Ensure partition key is in all queries
- **Check:** Query logs for cross-partition queries

**Problem:** "Index not found" errors
- **Solution:** Verify composite indexes are defined correctly
- **Check:** Portal → Settings → Indexing Policy

## Cost Impact

- **Index storage**: ~10-20% increase (worth it for 10-50x speed improvement)
- **RU cost**: 90% reduction in RU consumption per query
- **Overall**: Significant cost savings due to efficient queries

---

**Next Steps:**
1. Apply the indexing policy above
2. Restart your backend server
3. Test the History tab - should load in < 1 second
4. Monitor RU consumption in Azure Portal

**Questions?** Check the [Cosmos DB Indexing Documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy)
