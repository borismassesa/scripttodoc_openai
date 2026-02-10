# Production Deployment Guide

This guide covers deploying the ScriptToDoc application to production on Azure.

## Pre-Deployment Checklist

### Security

- [ ] All `.env` files contain only template/example values
- [ ] No API keys or secrets committed to repository
- [ ] `.gitignore` properly excludes sensitive files
- [ ] Environment variables configured in Azure App Service / Container Apps
- [ ] Azure Key Vault configured for secrets management
- [ ] Managed Identity enabled for Azure services

### Code Quality

- [ ] All tests passing (`pytest` in backend, `npm test` in frontend)
- [ ] Code linted and formatted
- [ ] No debug logging in production code
- [ ] Error handling implemented for all API endpoints
- [ ] Input validation on all user inputs

### Infrastructure

- [ ] Azure resources provisioned (see [docs/setup/AZURE_SERVICES_SETUP_GUIDE.md](docs/setup/AZURE_SERVICES_SETUP_GUIDE.md))
- [ ] Resource naming follows conventions
- [ ] Tags applied to all Azure resources
- [ ] Cost alerts configured
- [ ] Backup strategy in place for Cosmos DB

### Monitoring

- [ ] Application Insights configured
- [ ] Log Analytics workspace connected
- [ ] Custom metrics and alerts set up
- [ ] Health check endpoints tested
- [ ] Performance baselines established

## Deployment Architecture

### Production Environment

```
Azure Front Door (CDN + WAF)
    |
    ├── Frontend (Azure Static Web Apps / App Service)
    |   └── Next.js Application (Port 3000)
    |
    └── Backend API (Azure Container Apps / App Service)
        ├── FastAPI (Port 8000)
        └── Background Worker
            |
            ├── Azure Service Bus (Job Queue)
            ├── Azure Cosmos DB (Job Status)
            ├── Azure Blob Storage (Files)
            ├── Azure Document Intelligence
            └── Azure OpenAI
```

## Deployment Options

### Option 1: Azure Container Apps (Recommended)

**Advantages:**
- Automatic scaling
- Managed Kubernetes
- Built-in load balancing
- Simplified networking

**Steps:**

1. **Build and Push Container Images**

```bash
# Backend
cd backend
az acr build --registry <your-registry> --image scripttodoc-backend:latest .

# Frontend
cd frontend
az acr build --registry <your-registry> --image scripttodoc-frontend:latest .
```

2. **Deploy Container Apps**

```bash
# Create Container Apps Environment
az containerapp env create \
  --name scripttodoc-env \
  --resource-group rg-scripttodoc-prod \
  --location eastus

# Deploy Backend API
az containerapp create \
  --name scripttodoc-api \
  --resource-group rg-scripttodoc-prod \
  --environment scripttodoc-env \
  --image <your-registry>.azurecr.io/scripttodoc-backend:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint \
    AZURE_OPENAI_KEY=secretref:openai-key

# Deploy Background Worker
az containerapp create \
  --name scripttodoc-worker \
  --resource-group rg-scripttodoc-prod \
  --environment scripttodoc-env \
  --image <your-registry>.azurecr.io/scripttodoc-backend:latest \
  --command "python" "workers/processor.py" \
  --env-vars \
    AZURE_SERVICE_BUS_CONNECTION_STRING=secretref:servicebus-conn
```

3. **Deploy Frontend**

```bash
az containerapp create \
  --name scripttodoc-frontend \
  --resource-group rg-scripttodoc-prod \
  --environment scripttodoc-env \
  --image <your-registry>.azurecr.io/scripttodoc-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --env-vars \
    NEXT_PUBLIC_API_URL=https://<api-url>.azurecontainerapps.io
```

### Option 2: Azure App Service

**Steps:**

1. **Create App Service Plans**

```bash
# Backend App Service Plan
az appservice plan create \
  --name plan-scripttodoc-backend \
  --resource-group rg-scripttodoc-prod \
  --sku P1V2 \
  --is-linux

# Frontend App Service Plan
az appservice plan create \
  --name plan-scripttodoc-frontend \
  --resource-group rg-scripttodoc-prod \
  --sku P1V2 \
  --is-linux
```

2. **Deploy Backend**

```bash
cd backend
az webapp create \
  --name scripttodoc-api \
  --resource-group rg-scripttodoc-prod \
  --plan plan-scripttodoc-backend \
  --runtime "PYTHON|3.11"

# Deploy code
az webapp up \
  --name scripttodoc-api \
  --resource-group rg-scripttodoc-prod
```

3. **Deploy Frontend**

```bash
cd frontend
npm run build

az webapp create \
  --name scripttodoc-web \
  --resource-group rg-scripttodoc-prod \
  --plan plan-scripttodoc-frontend \
  --runtime "NODE|18-lts"

# Deploy
az webapp deployment source config-zip \
  --name scripttodoc-web \
  --resource-group rg-scripttodoc-prod \
  --src ./out.zip
```

## Environment Configuration

### Backend Environment Variables

Configure these in Azure App Service Configuration or Container Apps Secrets:

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=<from-key-vault>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<from-key-vault>
AZURE_STORAGE_CONNECTION_STRING=<from-key-vault>
AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_KEY=<from-key-vault>
AZURE_SERVICE_BUS_CONNECTION_STRING=<from-key-vault>

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
APPLICATIONINSIGHTS_CONNECTION_STRING=<app-insights-conn-string>
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://scripttodoc-api.azurecontainerapps.io
NEXT_PUBLIC_ENVIRONMENT=production
```

## Database Setup

### Cosmos DB

1. **Create Database and Container**

```bash
az cosmosdb sql database create \
  --account-name scripttodoc-cosmos \
  --resource-group rg-scripttodoc-prod \
  --name scripttodoc

az cosmosdb sql container create \
  --account-name scripttodoc-cosmos \
  --database-name scripttodoc \
  --name jobs \
  --partition-key-path "/userId" \
  --throughput 400
```

2. **Configure Indexing**

Update indexing policy for optimal query performance.

### Blob Storage

**Create Containers:**

```bash
az storage container create --name uploads --account-name <storage-account>
az storage container create --name documents --account-name <storage-account>
az storage container create --name temp --account-name <storage-account>
```

**Set Access Policies:**
- `uploads`: Private
- `documents`: Private (SAS token access only)
- `temp`: Private (auto-delete after 24 hours)

## Monitoring and Logging

### Application Insights

1. **Create Application Insights**

```bash
az monitor app-insights component create \
  --app scripttodoc-insights \
  --location eastus \
  --resource-group rg-scripttodoc-prod \
  --workspace <log-analytics-workspace-id>
```

2. **Configure Custom Metrics**

- Job completion rate
- Average processing time
- Token usage per job
- Error rate by stage
- Confidence score distribution

### Log Analytics

**Custom Queries:**

```kusto
// Failed jobs in last 24 hours
traces
| where timestamp > ago(24h)
| where severityLevel >= 3
| summarize count() by bin(timestamp, 1h)

// Average job duration
customMetrics
| where name == "job_duration"
| summarize avg(value) by bin(timestamp, 1h)
```

### Health Checks

**Backend API Health Endpoint:**
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "cosmos_db": "connected",
    "blob_storage": "connected",
    "service_bus": "connected",
    "openai": "connected"
  }
}
```

## Scaling Configuration

### Auto-Scaling Rules

**Backend API:**
- Min instances: 2
- Max instances: 10
- Scale up: CPU > 70% for 5 minutes
- Scale down: CPU < 30% for 10 minutes

**Background Worker:**
- Min instances: 1
- Max instances: 5
- Scale based on Service Bus queue length

### Performance Optimization

1. **Enable CDN** for static assets
2. **Configure caching** for API responses
3. **Optimize images** in frontend
4. **Use connection pooling** for database
5. **Implement request throttling**

## Security Hardening

### Network Security

1. **Configure Virtual Network**
   - Place all services in VNet
   - Use private endpoints for Azure services
   - Configure NSG rules

2. **Enable Web Application Firewall (WAF)**
   - OWASP rule set
   - Custom rules for API protection

3. **SSL/TLS Configuration**
   - Enforce HTTPS only
   - TLS 1.2 minimum
   - Disable weak ciphers

### Authentication & Authorization

1. **Azure AD Integration**
   - Configure OAuth 2.0
   - Set up application registration
   - Define API permissions

2. **API Key Management**
   - Store in Azure Key Vault
   - Rotate keys every 90 days
   - Use managed identities where possible

### Data Protection

1. **Encryption at Rest**
   - Enable for Cosmos DB
   - Enable for Blob Storage
   - Use customer-managed keys

2. **Encryption in Transit**
   - HTTPS everywhere
   - Secure Service Bus connections

## Backup and Disaster Recovery

### Backup Strategy

1. **Cosmos DB**
   - Continuous backup enabled
   - Point-in-time restore capability
   - Retention: 30 days

2. **Blob Storage**
   - Geo-redundant storage (GRS)
   - Soft delete enabled (14 days)
   - Version control enabled

### Disaster Recovery

1. **Multi-region deployment** (optional)
2. **Failover procedures** documented
3. **Regular DR drills** scheduled
4. **RTO: 4 hours, RPO: 1 hour**

## Post-Deployment Validation

### Smoke Tests

```bash
# Test API health
curl https://scripttodoc-api.azurecontainerapps.io/health

# Test file upload
curl -X POST https://scripttodoc-api.azurecontainerapps.io/api/process \
  -F "file=@sample.txt" \
  -F "tone=Professional"

# Test frontend
curl https://scripttodoc-web.azurecontainerapps.io
```

### Performance Tests

Run load tests using Azure Load Testing:
- 100 concurrent users
- 1000 requests over 10 minutes
- Success rate > 99%
- Average response time < 2s

## Rollback Procedure

If deployment fails:

1. **Immediate Rollback**
   ```bash
   az webapp deployment slot swap \
     --name scripttodoc-api \
     --resource-group rg-scripttodoc-prod \
     --slot staging \
     --action rollback
   ```

2. **Verify rollback**
   - Check health endpoints
   - Verify error rates in App Insights
   - Test critical user flows

3. **Investigate issues**
   - Review deployment logs
   - Check Application Insights
   - Analyze error messages

## Maintenance

### Regular Tasks

- **Daily**: Monitor error rates and performance
- **Weekly**: Review costs and optimize resources
- **Monthly**: Update dependencies and security patches
- **Quarterly**: DR drill, security audit, performance review

### Updates

1. Deploy to staging environment first
2. Run automated tests
3. Perform manual smoke tests
4. Deploy to production during off-peak hours
5. Monitor for 24 hours post-deployment

## Cost Optimization

1. **Right-size resources** based on actual usage
2. **Use reserved instances** for predictable workloads
3. **Implement auto-shutdown** for non-production environments
4. **Monitor and alert** on cost anomalies
5. **Regular cost reviews** with team

## Support and Troubleshooting

### Common Issues

1. **High latency**
   - Check Application Insights performance tab
   - Review database queries
   - Verify network connectivity

2. **Failed jobs**
   - Check Service Bus dead letter queue
   - Review worker logs
   - Verify Azure service quotas

3. **Memory issues**
   - Scale up instances
   - Review memory leaks
   - Optimize data processing

### Support Contacts

- **Azure Support**: support.azure.com
- **On-call Engineer**: [Contact info]
- **DevOps Team**: [Contact info]

## References

- [Azure Services Setup Guide](docs/setup/AZURE_SERVICES_SETUP_GUIDE.md)
- [Deployment Checklist](docs/setup/DEPLOYMENT_CHECKLIST.md)
- [Architecture Documentation](docs/architecture/README.md)
- [API Documentation](http://localhost:8000/docs)

---

**Last Updated**: December 2025
**Version**: 1.0
