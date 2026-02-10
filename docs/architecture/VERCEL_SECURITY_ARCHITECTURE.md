# Vercel + Azure Deployment: Security Architecture for Information Governance

**Version**: 2.0 - MVP FOCUSED
**Date**: December 9, 2025
**Status**: For IG Review and Approval

---

## Executive Summary

This document outlines the **MVP-focused security architecture** for deploying ScriptToDoc with a **Vercel-hosted frontend** and **Azure-hosted backend**. This version focuses on **practical, implementable security controls** while maintaining compliance with information governance requirements.

### 🎯 MVP vs. Production Features

This document clearly separates:
- ✅ **MVP MUST-HAVE** - Required for security approval (implement first)
- 🔄 **POST-MVP** - Enhanced security for production (implement later)
- 💡 **OPTIONAL** - Nice-to-have features (implement if needed)

### Key Security Highlights (MVP)

- **100% Microsoft Azure backend** - All data processing and storage in Azure ✅
- **Azure AD authentication** - User authentication with MFA support ✅
- **Data residency** - All sensitive data stays within Azure (Microsoft ecosystem) ✅
- **Encryption at rest and in transit** - TLS 1.2+, AES-256 encryption ✅
- **Basic audit logging** - Track critical operations (via Application Insights) ✅
- **Compliance foundation** - GDPR-ready, HIPAA-compatible architecture ✅
- **User data isolation** - Cosmos DB partition keys (users can't access each other's data) ✅
- **No data on Vercel** - Frontend is static assets only, no PII or documents ✅

---

## 🎯 MVP Implementation Roadmap

### Phase 1: MVP (Required for IG Approval) - 2-3 weeks

**Security Controls - MUST IMPLEMENT:**

| Feature | Status | Complexity | Priority |
|---------|--------|------------|----------|
| Azure AD B2C authentication (OAuth 2.0) | ✅ MVP | Medium | **P0** |
| JWT token validation on API | ✅ MVP | Low | **P0** |
| RBAC - User can only access own data | ✅ MVP | Low | **P0** |
| HTTPS/TLS 1.2+ enforced | ✅ MVP | Low | **P0** |
| Azure Blob Storage (private containers) | ✅ MVP | Low | **P0** |
| Azure Cosmos DB (partition by userId) | ✅ MVP | Low | **P0** |
| Encryption at rest (default Azure encryption) | ✅ MVP | None (automatic) | **P0** |
| Basic audit logging (Application Insights) | ✅ MVP | Low | **P0** |
| File type validation (whitelist) | ✅ MVP | Low | **P0** |
| File size limits (10 MB max) | ✅ MVP | Low | **P0** |
| Secrets in Azure Key Vault | ✅ MVP | Low | **P0** |
| Managed Identity (Container Apps → Azure services) | ✅ MVP | Medium | **P0** |
| Data retention policy (90 days auto-delete) | ✅ MVP | Low | **P0** |
| CORS configuration (Vercel origin only) | ✅ MVP | Low | **P0** |
| Vercel security headers (CSP, HSTS, etc.) | ✅ MVP | Low | **P0** |

**Total MVP effort**: ~1-2 weeks for security implementation

### Phase 2: Post-MVP (Production Hardening) - 4-6 weeks

**Enhanced Security - IMPLEMENT LATER:**

| Feature | Status | Complexity | Priority |
|---------|--------|------------|----------|
| Azure Front Door + WAF | 🔄 POST-MVP | High | **P1** |
| DDoS Protection Standard | 🔄 POST-MVP | Medium | **P1** |
| Rate limiting (per user) | 🔄 POST-MVP | Medium | **P1** |
| Azure Defender threat detection | 🔄 POST-MVP | Low | **P1** |
| Advanced alerting rules (10+ alerts) | 🔄 POST-MVP | Medium | **P1** |
| Private Link / Private Endpoints | 💡 OPTIONAL | High | **P2** |
| VNet injection (Container Apps) | 💡 OPTIONAL | High | **P2** |
| Customer-managed keys (CMK) | 💡 OPTIONAL | Medium | **P2** |
| Geo-redundancy (multi-region) | 💡 OPTIONAL | High | **P2** |
| SOC 2 Type II audit | 💡 OPTIONAL | Very High | **P3** |

### Phase 3: Enterprise Features (Optional) - 8-12 weeks

**Nice-to-Have - IMPLEMENT IF NEEDED:**

| Feature | Status | Complexity | Priority |
|---------|--------|------------|----------|
| Network isolation (Private Link) | 💡 OPTIONAL | Very High | **P3** |
| Advanced threat protection | 💡 OPTIONAL | High | **P3** |
| Penetration testing (annual) | 💡 OPTIONAL | High | **P3** |
| HIPAA BAA (if handling PHI) | 💡 OPTIONAL | Medium | **P3** |
| PII detection and redaction | 💡 OPTIONAL | High | **P3** |
| Compliance certifications | 💡 OPTIONAL | Very High | **P3** |

### MVP Timeline & Costs

**MVP Development Time**: 2-3 weeks
**MVP Security Implementation**: 1-2 weeks (parallel with development)
**Total MVP Time**: 3-4 weeks

**MVP Monthly Cost** (for 100 jobs/month):
- Compute (Container Apps): $20-40
- Storage (Cosmos DB + Blob): $15-30
- AI Services (OpenAI + Doc Intelligence): $50-100
- Networking (Basic): $5-10
- Monitoring (App Insights): $5-10
- **Total MVP Cost**: **$95-190/month** (scales with usage)

**Post-MVP Additional Costs** (production):
- Azure Front Door Premium: +$50-80/month
- DDoS Protection: +$30/month
- Azure Defender: +$15/month
- **Total Production Cost**: **$190-315/month**

---

## Architecture Overview

### 🎯 MVP Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT LAYER                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  User's Browser                                                    │ │
│  │  ✅ TLS 1.2+ encrypted communication (automatic)                  │ │
│  │  ✅ Azure AD B2C authentication (OAuth 2.0)                       │ │
│  │  ✅ JWT tokens in httpOnly, secure cookies                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTPS (automatic)
                            │ Authorization: Bearer {JWT}
┌───────────────────────────┴─────────────────────────────────────────────┐
│                    VERCEL EDGE NETWORK (CDN)                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Next.js Frontend (Static Site)                         ✅ MVP    │ │
│  │  ✅ Static HTML/CSS/JS only (no backend on Vercel)              │ │
│  │  ✅ NO sensitive data stored                                     │ │
│  │  ✅ NO database connections                                      │ │
│  │  ✅ NO API keys or secrets                                       │ │
│  │                                                                     │ │
│  │  Security (Built-in):                                              │ │
│  │  ✅ DDoS protection (Vercel automatic)                           │ │
│  │  ✅ Security headers (CSP, HSTS, X-Frame-Options)                │ │
│  │  ✅ Automatic HTTPS/TLS                                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTPS to Azure Container Apps
                            │ Authorization: Bearer {JWT}
                            │ CORS: Only from scripttodoc.vercel.app
                            │
                            │ 🔄 POST-MVP: Add Azure Front Door + WAF here
┌───────────────────────────┴─────────────────────────────────────────────┐
│              AZURE CONTAINER APPS (Backend API)               ✅ MVP     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application                                              │ │
│  │  ✅ HTTPS endpoint (TLS 1.2+ enforced)                           │ │
│  │  ✅ JWT token validation (every request)                         │ │
│  │  ✅ RBAC - Users can only access own data                        │ │
│  │  ✅ CORS validation (Vercel origin only)                         │ │
│  │  ✅ Input validation (Pydantic)                                  │ │
│  │  ✅ File validation (type whitelist, size limits)                │ │
│  │  ✅ Managed Identity (no hardcoded keys)                         │ │
│  │  ✅ Audit logging (Application Insights)                         │ │
│  │                                                                     │ │
│  │  🔄 POST-MVP: Add rate limiting, advanced monitoring             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ Managed Identity (no keys!)
        ┌───────────────────┼───────────────────┬───────────────────┐
┌───────────────────────────┴─────────────────────────────────────────────┐
│              AZURE CONTAINER APPS (Backend API)                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application (Ingress: Private)                           │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │  Security Middleware Stack (Order of Execution)              │ │ │
│  │  │  1. CORS validation (only from approved origins)             │ │ │
│  │  │  2. JWT token validation (Azure AD B2C)                      │ │ │
│  │  │  3. User authorization (RBAC - check permissions)            │ │ │
│  │  │  4. Input validation (Pydantic models)                       │ │ │
│  │  │  5. Request ID injection (for audit trail)                   │ │ │
│  │  │  6. Rate limiting (per user)                                 │ │ │
│  │  │  7. Business logic execution                                 │ │ │
│  │  │  8. Response sanitization (remove internal details)          │ │ │
│  │  │  9. Audit logging (to Application Insights)                  │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  Environment Configuration:                                        │ │
│  │  - Secrets from Azure Key Vault ONLY                              │ │
│  │  - Managed Identity for all Azure service access                  │ │
│  │  - No hardcoded credentials                                        │ │
│  │  - Network isolation (VNet injection available)                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬───────────────────┐
        │                   │                   │                   │
        │ Managed Identity  │ Managed Identity  │ Managed Identity  │
        │ (No keys!)        │ (No keys!)        │ (No keys!)        │
┌───────▼─────────┐ ┌───────▼─────────┐ ┌──────▼──────────┐ ┌─────▼──────┐
│ Azure Key Vault │ │ Azure Service   │ │ Azure Cosmos DB │ │ Azure Blob │
│                 │ │ Bus Queue       │ │                 │ │ Storage    │
│ ✓ Secrets mgmt  │ │                 │ │ ✓ Encryption at │ │            │
│ ✓ Soft delete   │ │ ✓ Job queue     │ │   rest (AES-256)│ │ ✓ Customer │
│ ✓ Audit logs    │ │ ✓ Dead letter   │ │ ✓ TLS in flight │ │   managed  │
│ ✓ RBAC access   │ │ ✓ Duplicate     │ │ ✓ RBAC access   │ │   keys     │
│ ✓ Key rotation  │ │   detection     │ │ ✓ Audit logs    │ │ ✓ Immutable│
└─────────────────┘ └───────┬─────────┘ │ ✓ Backup/restore│ │   blobs    │
                            │           │ ✓ Point-in-time │ │ ✓ Lifecycle│
                            │           │   restore       │ │   policies │
                            │           └─────────────────┘ │ ✓ Versioning│
                            │                               │ ✓ Soft delete│
                            │ Trigger                       └────────────┘
                    ┌───────▼────────────────────────────────────────┐
                    │  Azure Container Apps (Worker Instances)       │
                    │  - Background job processing                   │
                    │  - Managed Identity for all service access     │
                    │  - Isolated from public internet               │
                    │  - Auto-scaling based on queue depth           │
                    └───────┬────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        │ Managed Identity  │ Managed Identity  │
        │ (No keys!)        │ (No keys!)        │
┌───────▼──────────┐ ┌─────▼──────────┐ ┌─────▼──────────┐
│ Azure Document   │ │ Azure OpenAI   │ │ Azure Monitor  │
│ Intelligence     │ │ Service        │ │ + App Insights │
│                  │ │                │ │                │
│ ✓ Private Link   │ │ ✓ Private Link │ │ ✓ Audit logs   │
│   (optional)     │ │   (optional)   │ │ ✓ Alerts       │
│ ✓ Content filter │ │ ✓ Data stays   │ │ ✓ Dashboards   │
│ ✓ No data stored │ │   in Azure     │ │ ✓ Compliance   │
│   (ephemeral)    │ │ ✓ Enterprise   │ │   reports      │
└──────────────────┘ │   SLA          │ └────────────────┘
                     │ ✓ Abuse monitor│
                     └────────────────┘
```

---

## Data Flow with Security Controls

### Detailed Security Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: USER AUTHENTICATION & FILE UPLOAD                               │
└──────────────────────────────────────────────────────────────────────────┘

[Step 1] User accesses https://scripttodoc.vercel.app
         │
         ├─> Vercel serves static HTML/JS
         ├─> CSP headers prevent XSS
         ├─> HSTS enforces HTTPS
         │
[Step 2] Frontend redirects to Azure AD B2C for authentication
         │
         ├─> User authenticates with corporate credentials
         ├─> Multi-factor authentication (MFA) enforced
         ├─> Conditional access policies applied
         │   (e.g., require MFA, check device compliance)
         │
[Step 3] Azure AD B2C issues JWT token
         │
         ├─> Token contains: user ID, roles, permissions, expiry
         ├─> Token signed with Azure AD private key
         ├─> Token stored in httpOnly, secure, SameSite cookie
         ├─> Token lifetime: 1 hour (configurable)
         │
[Step 4] User uploads transcript file (via Vercel frontend)
         │
         ├─> File validated in browser (size, type, content)
         ├─> POST request to Azure API with JWT token
         ├─> Request goes through Vercel → Azure Front Door
         │
         │   Security Checks:
         │   ✓ TLS 1.3 encryption (end-to-end)
         │   ✓ File size limit: 10 MB
         │   ✓ File type whitelist: .txt, .pdf, .docx, .mp4, .mp3
         │   ✓ Content-Type validation
         │   ✓ Malware scanning (Azure Defender for Storage)
         │
[Step 5] Request hits Azure Front Door (WAF)
         │
         WAF Security Rules:
         │
         ├─> Rule 1: Rate limiting (100 req/min per IP)
         ├─> Rule 2: SQL injection prevention
         ├─> Rule 3: XSS attack prevention
         ├─> Rule 4: Geo-filtering (optional)
         ├─> Rule 5: Known bad actors (IP blocklist)
         ├─> Rule 6: Bot detection
         │
         └─> If any rule fails: 403 Forbidden + audit log
         └─> If all pass: forward to Container Apps
         │
[Step 6] Container Apps API receives request
         │
         Authentication & Authorization:
         │
         ├─> Step 6.1: Validate JWT token
         │   │
         │   ├─> Verify signature with Azure AD public key
         │   ├─> Check expiration (not expired)
         │   ├─> Check issuer (trusted Azure AD)
         │   ├─> Check audience (this API)
         │   │
         │   └─> If invalid: 401 Unauthorized + audit log
         │
         ├─> Step 6.2: Check user authorization (RBAC)
         │   │
         │   ├─> Extract user ID and roles from token
         │   ├─> Check against permission matrix:
         │   │   • upload_documents: [user, admin]
         │   │   • view_documents: [user, admin]
         │   │   • delete_documents: [admin only]
         │   │
         │   └─> If unauthorized: 403 Forbidden + audit log
         │
         ├─> Step 6.3: Input validation (Pydantic)
         │   │
         │   ├─> Validate file content (not empty, valid encoding)
         │   ├─> Validate config parameters (within allowed ranges)
         │   ├─> Sanitize file name (prevent path traversal)
         │   │
         │   └─> If invalid: 400 Bad Request + audit log
         │
         └─> Step 6.4: Virus scan (optional)
             │
             └─> Azure Defender scans file for malware
                 └─> If malware: 400 Bad Request + security alert

┌──────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: SECURE FILE STORAGE                                             │
└──────────────────────────────────────────────────────────────────────────┘

[Step 7] Upload file to Azure Blob Storage
         │
         Storage Security Configuration:
         │
         ├─> Container: "uploads" (PRIVATE - no public access)
         ├─> Path: {userId}/{jobId}/{filename}
         │   (User isolation - users can only access their own files)
         │
         ├─> Encryption at rest:
         │   ├─> AES-256 encryption (Microsoft-managed keys)
         │   └─> Option: Customer-managed keys (CMK) via Key Vault
         │
         ├─> Encryption in transit:
         │   └─> TLS 1.2+ required (enforced)
         │
         ├─> Access control:
         │   ├─> NO anonymous access
         │   ├─> Managed Identity authentication ONLY
         │   ├─> SAS tokens with short expiry (1 hour)
         │   └─> RBAC: only Container Apps can write
         │
         ├─> Audit logging:
         │   ├─> All read/write operations logged
         │   ├─> Logs sent to Azure Monitor
         │   └─> Alerts on suspicious activity
         │
         ├─> Data protection:
         │   ├─> Soft delete enabled (7-day retention)
         │   ├─> Blob versioning enabled
         │   ├─> Immutable storage for compliance (optional)
         │
         └─> Lifecycle policies:
             ├─> Temp files deleted after 24 hours
             ├─> Uploads moved to cool storage after 30 days
             └─> All files deleted after 90 days (data retention policy)

[Step 8] Create job record in Cosmos DB
         │
         Database Security Configuration:
         │
         ├─> Database: "scripttodoc" (PRIVATE - no public access)
         ├─> Partition key: userId (data isolation per user)
         │
         ├─> Encryption at rest:
         │   └─> AES-256 encryption (automatic)
         │
         ├─> Encryption in transit:
         │   └─> TLS 1.2+ required
         │
         ├─> Access control:
         │   ├─> NO SQL endpoint exposed publicly
         │   ├─> Managed Identity authentication ONLY
         │   ├─> RBAC: Container Apps have read/write
         │   └─> Users can only query their own partition
         │
         ├─> Audit logging:
         │   ├─> All database operations logged
         │   ├─> Logs include: user, operation, timestamp, query
         │   └─> Logs retained for 90 days (compliance)
         │
         ├─> Data protection:
         │   ├─> Continuous backup enabled
         │   ├─> Point-in-time restore (up to 30 days)
         │   └─> Geo-redundant backup (optional)
         │
         ├─> Sensitive data handling:
         │   ├─> User ID stored (for authorization)
         │   ├─> No PII in job records (except user ID reference)
         │   ├─> File URLs are temporary (SAS tokens expire)
         │   └─> Processing logs sanitized (no sensitive content)
         │
         └─> Data stored:
             {
               "id": "job_123",
               "userId": "azure_ad_user_id",  // For authorization
               "status": "queued",
               "created": "2025-12-09T10:00:00Z",
               "documentUrl": null,  // Populated after processing
               "metadata": {
                 "fileName": "meeting_notes.txt",  // Sanitized
                 "fileSize": 256000,
                 "configTone": "Professional"
               }
               // NO raw transcript content stored here
               // NO sensitive file content stored here
             }

┌──────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: SECURE BACKGROUND PROCESSING                                    │
└──────────────────────────────────────────────────────────────────────────┘

[Step 9] Send message to Azure Service Bus
         │
         Queue Security Configuration:
         │
         ├─> Queue: "scripttodoc-jobs" (PRIVATE)
         ├─> Access control:
         │   ├─> Managed Identity authentication ONLY
         │   ├─> API (sender): write-only permission
         │   └─> Worker (receiver): read-only permission
         │
         ├─> Message encryption:
         │   └─> TLS 1.2+ in transit
         │
         ├─> Message content:
         │   {
         │     "jobId": "job_123",
         │     "userId": "azure_ad_user_id",
         │     "blobUrl": "{SAS_URL}",  // Short-lived SAS token
         │     "config": {...}
         │   }
         │   // NO sensitive content in message
         │   // Blob URL is SAS-protected and expires in 1 hour
         │
         ├─> Message security:
         │   ├─> Time-to-live: 30 minutes (stale jobs expire)
         │   ├─> Duplicate detection enabled
         │   ├─> Dead-letter queue for failed jobs
         │   └─> Audit logging of all queue operations
         │
         └─> Worker isolation:
             ├─> Workers run in private Container Apps
             ├─> No public internet access
             └─> Can only access Azure services via Managed Identity

[Step 10] Worker processes job (Background Container Apps)
          │
          Worker Security Configuration:
          │
          ├─> Network isolation:
          │   ├─> No public IP address
          │   ├─> VNet injection (optional - for extra isolation)
          │   └─> All outbound traffic to Azure services only
          │
          ├─> Authentication:
          │   ├─> Managed Identity for all Azure service access
          │   ├─> NO API keys in environment variables
          │   ├─> Secrets fetched from Key Vault at runtime
          │   └─> Automatic token refresh (no expired tokens)
          │
          ├─> Processing security:
          │   │
          │   ├─> Step 10.1: Download transcript from Blob Storage
          │   │   │
          │   │   ├─> Validate SAS token (not expired)
          │   │   ├─> Download over TLS 1.2+
          │   │   ├─> Validate file size (prevent DoS)
          │   │   └─> Audit log: user_id, job_id, file_name, timestamp
          │   │
          │   ├─> Step 10.2: Process with Azure Document Intelligence
          │   │   │
          │   │   ├─> Send transcript to Azure DI (Private Link option)
          │   │   ├─> Azure DI processes ephemeral (no data retention)
          │   │   ├─> Response received over TLS 1.2+
          │   │   └─> Cache results in Cosmos DB (encrypted, 24h TTL)
          │   │
          │   ├─> Step 10.3: Generate steps with Azure OpenAI
          │   │   │
          │   │   Security Controls:
          │   │   │
          │   │   ├─> Data stays in Azure (never leaves Microsoft cloud)
          │   │   ├─> Private Link option (no internet transit)
          │   │   ├─> Azure OpenAI does NOT train on customer data
          │   │   ├─> Content filtering (toxicity, PII detection)
          │   │   ├─> Abuse monitoring (rate limits, usage quotas)
          │   │   ├─> Audit logging (all API calls logged)
          │   │   │
          │   │   └─> PII Handling:
          │   │       ├─> If PII detected in transcript (names, emails):
          │   │       │   • Redact before sending to OpenAI (optional)
          │   │       │   • Use Azure Cognitive Services PII detection
          │   │       │   • Replace with placeholders: [NAME], [EMAIL]
          │   │       │
          │   │       └─> Output sanitization:
          │   │           • Validate generated content
          │   │           • Filter harmful content
          │   │           • Remove any leaked PII
          │   │
          │   ├─> Step 10.4: Create Word document
          │   │   │
          │   │   ├─> Document generated in-memory (ephemeral)
          │   │   ├─> No temporary files on disk
          │   │   └─> Document metadata includes job_id, timestamp
          │   │
          │   └─> Step 10.5: Upload document to Blob Storage
          │       │
          │       ├─> Container: "documents" (PRIVATE)
          │       ├─> Path: {userId}/{jobId}/document.docx
          │       ├─> Encryption at rest (AES-256)
          │       ├─> Generate SAS URL (1-hour expiry)
          │       └─> Audit log: document created, user_id, job_id
          │
          └─> Update job status in Cosmos DB
              {
                "id": "job_123",
                "status": "completed",
                "completed": "2025-12-09T10:05:00Z",
                "documentUrl": "{SAS_URL}",  // 1-hour expiry
                "metrics": {
                  "processingTime": 150,
                  "stepCount": 7,
                  "confidence": 0.85
                }
              }

┌──────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: SECURE DOCUMENT RETRIEVAL                                       │
└──────────────────────────────────────────────────────────────────────────┘

[Step 11] User requests document download
          │
          Request Flow:
          │
          ├─> Frontend polls GET /api/status/{jobId}
          │   │
          │   ├─> Include JWT token in Authorization header
          │   ├─> Request goes through Azure Front Door (WAF)
          │   │
          │   └─> API validates:
          │       ├─> JWT token valid?
          │       ├─> User owns this job? (jobId.userId === token.userId)
          │       └─> Job status is "completed"?
          │
          ├─> When job completed, GET /api/documents/{jobId}
          │   │
          │   Authorization Check:
          │   │
          │   ├─> Verify JWT token
          │   ├─> Query Cosmos DB for job record
          │   ├─> Verify job.userId === token.userId
          │   │   └─> If mismatch: 403 Forbidden + audit log
          │   │
          │   └─> Generate new SAS URL (1-hour expiry)
          │       └─> Return to user
          │
          └─> User downloads document from Blob Storage
              │
              ├─> SAS URL provides temporary access (1 hour)
              ├─> Download over HTTPS (TLS 1.3)
              ├─> Audit log: document downloaded, user_id, job_id
              │
              └─> Security note: SAS URL is user-specific
                  (cannot be shared or reused by others)

┌──────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: DATA RETENTION & DELETION                                       │
└──────────────────────────────────────────────────────────────────────────┘

[Step 12] Automated data lifecycle management
          │
          Retention Policies (Configurable):
          │
          ├─> Immediate (after processing):
          │   └─> Delete temp files from "temp" container
          │       (Lifecycle policy: auto-delete after 24 hours)
          │
          ├─> 7 days:
          │   └─> Delete uploaded files from "uploads" container
          │       (User no longer needs source file)
          │
          ├─> 30 days:
          │   └─> Move documents to cool storage tier
          │       (Cheaper storage for infrequently accessed files)
          │
          ├─> 90 days (default retention period):
          │   ├─> Delete documents from "documents" container
          │   ├─> Delete job records from Cosmos DB
          │   └─> Audit log: data deleted, user_id, job_id
          │
          └─> Compliance note:
              ├─> Retention period configurable per compliance requirements
              │   (GDPR, HIPAA, company policy, etc.)
              │
              └─> User can request early deletion (GDPR "right to be forgotten")
                  └─> DELETE /api/documents/{jobId}
                      └─> Immediately deletes all associated data

[Step 13] Audit trail preservation
          │
          Audit Logs (Compliance):
          │
          ├─> All logs sent to Azure Monitor + Application Insights
          │
          ├─> Logs include:
          │   ├─> Timestamp (ISO 8601 UTC)
          │   ├─> User ID (Azure AD user ID)
          │   ├─> Operation (upload, download, delete, etc.)
          │   ├─> Resource (job_id, file_name, etc.)
          │   ├─> Result (success, failure, error code)
          │   ├─> IP address (for security monitoring)
          │   └─> Request ID (for correlation)
          │
          ├─> Log retention:
          │   ├─> Application logs: 90 days
          │   ├─> Security logs: 1 year
          │   ├─> Compliance logs: 7 years (if required)
          │   └─> Exported to Log Analytics Workspace
          │
          ├─> Alerting:
          │   ├─> Failed authentication attempts (>5 in 5 minutes)
          │   ├─> Authorization failures (403 errors)
          │   ├─> Suspicious download patterns
          │   ├─> Mass deletion attempts
          │   └─> Azure Defender security alerts
          │
          └─> Compliance reporting:
              ├─> Monthly access reports (who accessed what)
              ├─> Quarterly security reviews
              └─> Annual compliance audit exports
```

---

## Authentication & Authorization

### Azure AD B2C Integration (Zero-Trust Model)

```
┌────────────────────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW (Azure AD B2C)                     │
└────────────────────────────────────────────────────────────────────────┘

[1] User accesses Vercel frontend (https://scripttodoc.vercel.app)
    │
    ├─> Frontend checks for valid session token
    │
    └─> If no token or expired:
        │
        [2] Redirect to Azure AD B2C login page
            │
            URL: https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/
                 oauth2/v2.0/authorize?
                 client_id={client_id}&
                 redirect_uri=https://scripttodoc.vercel.app/auth/callback&
                 scope=openid profile email&
                 response_type=code
            │
            Security Features:
            ├─> OAuth 2.0 / OpenID Connect standard
            ├─> PKCE (Proof Key for Code Exchange) enabled
            ├─> State parameter (CSRF protection)
            └─> Nonce parameter (replay attack prevention)
            │
        [3] User authenticates with corporate credentials
            │
            Authentication Options:
            ├─> Option A: Corporate SSO (Azure AD)
            │   └─> Users sign in with company email/password
            │       └─> Federated with company Active Directory
            │
            ├─> Option B: Multi-factor authentication (MFA)
            │   ├─> Password + Microsoft Authenticator app
            │   ├─> Password + SMS code
            │   └─> Password + Email code
            │
            └─> Option C: Conditional Access Policies
                ├─> Require compliant device
                ├─> Require managed device
                ├─> Block legacy authentication
                ├─> Require MFA from untrusted locations
                └─> Risk-based authentication
            │
        [4] Azure AD B2C validates credentials
            │
            ├─> Check username/password against Azure AD
            ├─> Validate MFA code (if required)
            ├─> Check conditional access policies
            ├─> Check user is not locked/disabled
            │
            └─> If valid: Issue authorization code
                └─> Redirect to: https://scripttodoc.vercel.app/auth/callback?
                                 code={authorization_code}&
                                 state={state}
            │
        [5] Frontend receives authorization code
            │
            ├─> Validate state parameter (CSRF check)
            │
            └─> Exchange authorization code for tokens
                │
                POST https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/
                     oauth2/v2.0/token
                │
                Request Body:
                {
                  "grant_type": "authorization_code",
                  "client_id": "{client_id}",
                  "code": "{authorization_code}",
                  "redirect_uri": "https://scripttodoc.vercel.app/auth/callback",
                  "code_verifier": "{pkce_verifier}"
                }
                │
                Response:
                {
                  "access_token": "{jwt_access_token}",
                  "id_token": "{jwt_id_token}",
                  "refresh_token": "{refresh_token}",
                  "expires_in": 3600,
                  "token_type": "Bearer"
                }
            │
        [6] Frontend stores tokens securely
            │
            Token Storage (Security Best Practices):
            │
            ├─> Access Token:
            │   ├─> Stored in httpOnly cookie (XSS protection)
            │   ├─> Secure flag enabled (HTTPS only)
            │   ├─> SameSite=Strict (CSRF protection)
            │   └─> Max age: 1 hour
            │
            ├─> Refresh Token:
            │   ├─> Stored in httpOnly cookie
            │   ├─> Secure flag enabled
            │   ├─> SameSite=Strict
            │   └─> Max age: 7 days (configurable)
            │
            └─> ID Token:
                └─> Stored in memory only (for UI display)
                    (contains user profile: name, email, roles)
            │
        [7] All API requests include access token
            │
            Request Headers:
            {
              "Authorization": "Bearer {jwt_access_token}",
              "Content-Type": "application/json"
            }
            │
            JWT Token Structure (Decoded):
            {
              "header": {
                "alg": "RS256",  // RSA signature
                "kid": "key_id_123"  // Key identifier
              },
              "payload": {
                "iss": "https://{tenant}.b2clogin.com/{tenant_id}/v2.0/",
                "sub": "azure_ad_user_id_12345",  // Unique user ID
                "aud": "api://scripttodoc-api",  // Intended audience
                "iat": 1699012800,  // Issued at
                "exp": 1699016400,  // Expires at (1 hour)
                "roles": ["user"],  // User roles
                "email": "user@company.com",
                "name": "John Doe",
                "tid": "tenant_id"  // Tenant ID
              },
              "signature": "..."
            }

┌────────────────────────────────────────────────────────────────────────┐
│              AUTHORIZATION FLOW (Role-Based Access Control)             │
└────────────────────────────────────────────────────────────────────────┘

[8] API validates JWT token on every request
    │
    Token Validation Steps:
    │
    ├─> Step 1: Verify token signature
    │   │
    │   ├─> Fetch Azure AD public keys (JWKS endpoint)
    │   │   URL: https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/
    │   │        discovery/v2.0/keys
    │   │
    │   ├─> Find key matching token "kid" header
    │   ├─> Verify RSA signature using public key
    │   └─> If signature invalid: 401 Unauthorized + audit log
    │
    ├─> Step 2: Verify token claims
    │   │
    │   ├─> Check "exp" (expiration): not expired
    │   ├─> Check "iat" (issued at): not in future
    │   ├─> Check "iss" (issuer): trusted Azure AD tenant
    │   ├─> Check "aud" (audience): this API
    │   │
    │   └─> If any claim invalid: 401 Unauthorized + audit log
    │
    └─> Step 3: Check user authorization (RBAC)
        │
        Permission Matrix:
        │
        ├─> Endpoint: POST /api/process (upload document)
        │   └─> Required role: "user" or "admin"
        │       └─> Check: token.roles includes "user"
        │
        ├─> Endpoint: GET /api/status/{jobId}
        │   └─> Required: User owns the job
        │       └─> Check: job.userId === token.sub (user ID)
        │
        ├─> Endpoint: GET /api/documents/{jobId}
        │   └─> Required: User owns the job
        │       └─> Check: job.userId === token.sub
        │
        ├─> Endpoint: DELETE /api/documents/{jobId}
        │   └─> Required: User owns the job
        │       └─> Check: job.userId === token.sub
        │
        └─> Endpoint: GET /api/admin/jobs (admin endpoint)
            └─> Required role: "admin"
                └─> Check: token.roles includes "admin"
        │
        If authorized: Process request
        If unauthorized: 403 Forbidden + audit log
            {
              "error": "Forbidden",
              "message": "Insufficient permissions",
              "code": "INSUFFICIENT_PERMISSIONS"
            }

┌────────────────────────────────────────────────────────────────────────┐
│                    TOKEN REFRESH FLOW                                   │
└────────────────────────────────────────────────────────────────────────┘

[9] Access token expires after 1 hour
    │
    ├─> API returns 401 Unauthorized
    │
    └─> Frontend detects expired token
        │
        [10] Use refresh token to get new access token
             │
             POST https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/
                  oauth2/v2.0/token
             │
             Request Body:
             {
               "grant_type": "refresh_token",
               "client_id": "{client_id}",
               "refresh_token": "{refresh_token}"
             }
             │
             Response:
             {
               "access_token": "{new_jwt_access_token}",
               "refresh_token": "{new_refresh_token}",
               "expires_in": 3600
             }
             │
             ├─> Store new tokens in httpOnly cookies
             │
             └─> Retry original request with new token
             │
        [11] If refresh token expired (after 7 days):
             │
             └─> Redirect user to Azure AD B2C login
                 └─> Start authentication flow from [1]

┌────────────────────────────────────────────────────────────────────────┐
│                    LOGOUT FLOW                                          │
└────────────────────────────────────────────────────────────────────────┘

[12] User clicks logout
     │
     ├─> Frontend clears cookies (delete access + refresh tokens)
     │
     ├─> Redirect to Azure AD B2C logout endpoint
     │   URL: https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/
     │        oauth2/v2.0/logout?
     │        post_logout_redirect_uri=https://scripttodoc.vercel.app
     │
     └─> Azure AD B2C ends user session
         └─> Redirect back to frontend (logged out state)
```

---

## Network Security & Isolation

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      NETWORK SECURITY LAYERS                             │
└─────────────────────────────────────────────────────────────────────────┘

Layer 1: Edge Security (Vercel + Azure Front Door)
         ├─> DDoS Protection (Layer 3/4 + Layer 7)
         ├─> Web Application Firewall (WAF)
         ├─> TLS 1.3 encryption
         ├─> Rate limiting (per IP, per user)
         └─> Geo-filtering (optional)

Layer 2: Application Gateway (Azure Front Door)
         ├─> SSL/TLS termination and re-encryption
         ├─> Backend pool health monitoring
         ├─> URL-based routing
         ├─> Custom security rules (OWASP Top 10)
         └─> IP allow/deny lists

Layer 3: Container Apps (Private Network)
         ├─> Ingress: External (via Azure Front Door only)
         ├─> Egress: Restricted to Azure services only
         ├─> VNet injection (optional - for extra isolation)
         └─> Managed Identity authentication (no internet keys)

Layer 4: Data Services (Private Endpoints)
         ├─> Cosmos DB: Private Link (no public internet access)
         ├─> Blob Storage: Private Endpoint (VNet only)
         ├─> Key Vault: Private Link
         ├─> OpenAI: Private Link (no data leaves Azure)
         └─> Document Intelligence: Private Link

Layer 5: Monitoring & Audit
         ├─> Azure Monitor: Network flow logs
         ├─> Application Insights: Request telemetry
         ├─> Azure Defender: Threat detection
         └─> Security Center: Compliance monitoring
```

### Private Link Architecture (Optional - Maximum Security)

```
┌───────────────────────────────────────────────────────────────────────┐
│             PRIVATE LINK CONFIGURATION (No Public Internet)            │
└───────────────────────────────────────────────────────────────────────┘

Corporate Network                 Azure Virtual Network (VNet)
      │                                      │
      │  VPN / ExpressRoute                 │
      │  (Site-to-Site)                     │
      │                                      │
      └──────────────┬─────────────────────┘
                     │
                     │ Private connectivity (no internet)
                     │
     ┌───────────────▼───────────────┐
     │   Azure Front Door            │
     │   - Private Link enabled      │
     │   - Only accessible from VNet │
     └───────────────┬───────────────┘
                     │
     ┌───────────────▼───────────────┐
     │   Container Apps              │
     │   - VNet injection            │
     │   - Subnet: 10.0.1.0/24       │
     └───────────────┬───────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
┌────────▼──────┐ ┌──▼────────┐ ┌──▼──────────┐
│ Cosmos DB     │ │Blob Storage│ │Azure OpenAI │
│ Private Link  │ │Private Link│ │Private Link │
│ 10.0.2.10     │ │10.0.2.20   │ │10.0.2.30    │
└───────────────┘ └────────────┘ └─────────────┘

Benefits:
✓ Zero internet exposure for data services
✓ All traffic stays within Azure backbone
✓ Reduced attack surface
✓ Compliance with strict network policies
✓ Lower latency (no internet routing)
```

---

## Secrets Management & Key Rotation

### Azure Key Vault Integration

```
┌───────────────────────────────────────────────────────────────────────┐
│                 SECRETS MANAGEMENT ARCHITECTURE                        │
└───────────────────────────────────────────────────────────────────────┘

[Secrets Stored in Key Vault]

Azure Key Vault: "kv-scripttodoc-prod"
│
├─> Secret: "azure-openai-key"
│   ├─> Value: "{REDACTED}"
│   ├─> Version: Current (v2)
│   ├─> Enabled: Yes
│   ├─> Expiry: 2026-01-01
│   ├─> Access Policy: Container Apps (read-only)
│   └─> Audit Log: All access logged
│
├─> Secret: "azure-document-intelligence-key"
│   ├─> Value: "{REDACTED}"
│   ├─> Version: Current (v1)
│   ├─> Enabled: Yes
│   ├─> Expiry: 2026-01-01
│   └─> Access Policy: Container Apps (read-only)
│
├─> Secret: "azure-cosmos-connection-string"
│   ├─> Value: "{REDACTED}"
│   ├─> Version: Current (v3)
│   ├─> Enabled: Yes
│   ├─> Expiry: Never (rotated manually)
│   └─> Access Policy: Container Apps (read-only)
│
├─> Secret: "azure-storage-connection-string"
│   ├─> Value: "{REDACTED}"
│   ├─> Version: Current (v2)
│   ├─> Enabled: Yes
│   ├─> Expiry: Never (rotated quarterly)
│   └─> Access Policy: Container Apps (read-only)
│
└─> Secret: "azure-service-bus-connection-string"
    ├─> Value: "{REDACTED}"
    ├─> Version: Current (v1)
    ├─> Enabled: Yes
    ├─> Expiry: Never (rotated quarterly)
    └─> Access Policy: Container Apps (read-only)

[Access Control (RBAC)]

Managed Identity: "mi-scripttodoc-api"
├─> Type: System-assigned (Container Apps API)
├─> Permissions on Key Vault:
│   └─> Role: "Key Vault Secrets User" (read-only)
│       └─> Can only GET secrets (no create/update/delete)
│
└─> Audit: All secret access logged to Azure Monitor
    └─> Alert on suspicious patterns (e.g., excessive reads)

Managed Identity: "mi-scripttodoc-worker"
├─> Type: System-assigned (Container Apps Worker)
├─> Permissions on Key Vault:
│   └─> Role: "Key Vault Secrets User" (read-only)
│
└─> Separate identity from API (principle of least privilege)

[Key Rotation Process]

Quarterly Rotation Schedule:
│
├─> Week 1: Generate new keys in Azure portal
│   ├─> Azure OpenAI: Create new key (key2)
│   ├─> Document Intelligence: Create new key (key2)
│   ├─> Storage Account: Rotate key2
│   └─> Service Bus: Rotate secondary connection string
│
├─> Week 2: Update Key Vault with new secrets
│   ├─> Create new secret version in Key Vault
│   ├─> Keep old version enabled (for rollback)
│   └─> Container Apps automatically fetch new version
│
├─> Week 3: Monitor for errors
│   ├─> Check Application Insights for auth failures
│   ├─> Verify all services using new keys
│   └─> If errors: rollback to previous version
│
└─> Week 4: Disable old keys
    ├─> Disable old secret versions in Key Vault
    ├─> Revoke old keys in Azure services
    └─> Document rotation in audit log

[Security Best Practices]

✓ NO secrets in environment variables
✓ NO secrets in code repository
✓ NO secrets in Container Apps configuration
✓ Secrets fetched at runtime from Key Vault
✓ Secrets cached in memory (expired after 4 hours)
✓ Automatic token refresh for Managed Identity
✓ Soft delete enabled (90-day retention)
✓ Purge protection enabled (cannot be permanently deleted)
✓ Access logs retained for 90 days
✓ Alerts on secret access anomalies
```

---

## Compliance & Data Governance

### Regulatory Compliance

```
┌───────────────────────────────────────────────────────────────────────┐
│                  COMPLIANCE MATRIX                                     │
└───────────────────────────────────────────────────────────────────────┘

Framework: GDPR (General Data Protection Regulation)
│
├─> Data Minimization ✓
│   ├─> Only collect necessary data (transcript, config)
│   ├─> No excessive PII collection
│   └─> User can provide anonymous transcripts
│
├─> Right to Access ✓
│   ├─> User can query: GET /api/my-jobs
│   └─> Returns all jobs and documents for user
│
├─> Right to be Forgotten ✓
│   ├─> User can request: DELETE /api/my-data
│   ├─> Deletes all jobs, documents, and blobs
│   ├─> Deleted within 30 days (compliance)
│   └─> Audit log preserved (anonymous job_id only)
│
├─> Data Portability ✓
│   ├─> User can export: GET /api/my-data/export
│   └─> Returns JSON with all user data
│
├─> Consent Management ✓
│   ├─> User must accept terms before upload
│   ├─> Consent recorded in database
│   └─> Consent can be withdrawn (triggers deletion)
│
├─> Data Breach Notification ✓
│   ├─> Azure Defender monitors for breaches
│   ├─> Alert sent to admin within 24 hours
│   └─> User notification within 72 hours (GDPR requirement)
│
└─> Data Processing Agreement (DPA) ✓
    ├─> Microsoft Azure DPA covers all services
    └─> Standard contractual clauses (SCCs) included

Framework: HIPAA (Health Insurance Portability and Accountability Act)
│
├─> Encryption at Rest ✓
│   ├─> AES-256 encryption (Azure Storage, Cosmos DB)
│   └─> Customer-managed keys (CMK) available
│
├─> Encryption in Transit ✓
│   └─> TLS 1.2+ enforced (all communications)
│
├─> Access Control ✓
│   ├─> Azure AD authentication (MFA enforced)
│   ├─> RBAC (role-based access control)
│   └─> Audit logs for all PHI access
│
├─> Audit Logging ✓
│   ├─> All PHI access logged (who, what, when)
│   ├─> Logs retained for 6 years (HIPAA requirement)
│   └─> Tamper-proof logs (immutable storage)
│
├─> Business Associate Agreement (BAA) ✓
│   ├─> Microsoft Azure BAA covers all services
│   └─> Available for Enterprise customers
│
└─> PHI Handling (if applicable)
    ├─> Transcripts may contain PHI (patient names, diagnoses)
    ├─> Option: Enable PII detection and redaction
    ├─> Azure Cognitive Services Text Analytics (PII detection)
    └─> Redact before processing with OpenAI

Framework: SOC 2 Type II (Service Organization Control)
│
├─> Security ✓
│   ├─> Multi-layered security (WAF, encryption, RBAC)
│   ├─> Regular security assessments
│   └─> Incident response plan
│
├─> Availability ✓
│   ├─> 99.9% uptime SLA (Azure Container Apps)
│   ├─> Multi-region failover (optional)
│   └─> Health monitoring and auto-healing
│
├─> Processing Integrity ✓
│   ├─> Input validation (all API requests)
│   ├─> Data integrity checks (checksums)
│   └─> Error handling and retry logic
│
├─> Confidentiality ✓
│   ├─> Data encrypted at rest and in transit
│   ├─> Access controls (RBAC)
│   └─> Secrets in Key Vault (no exposure)
│
└─> Privacy ✓
    ├─> User data isolation (partition keys)
    ├─> Data retention policies (auto-delete after 90 days)
    └─> Privacy policy and terms of service

Framework: ISO 27001 (Information Security Management)
│
├─> Risk Assessment ✓
│   ├─> Regular threat modeling
│   ├─> Vulnerability scanning (Azure Defender)
│   └─> Penetration testing (annual)
│
├─> Access Control (A.9) ✓
│   ├─> Azure AD authentication
│   ├─> MFA enforced
│   ├─> RBAC (least privilege)
│   └─> Regular access reviews
│
├─> Cryptography (A.10) ✓
│   ├─> Strong encryption (AES-256, TLS 1.3)
│   ├─> Key management (Azure Key Vault)
│   └─> Key rotation (quarterly)
│
├─> Operations Security (A.12) ✓
│   ├─> Automated patching (Container Apps)
│   ├─> Security monitoring (Azure Defender)
│   ├─> Incident response plan
│   └─> Regular backups (Cosmos DB)
│
└─> Compliance (A.18) ✓
    ├─> Privacy policy published
    ├─> Terms of service published
    ├─> Regular compliance audits
    └─> Documentation maintained
```

### Data Residency & Sovereignty

```
┌───────────────────────────────────────────────────────────────────────┐
│                  DATA RESIDENCY CONFIGURATION                          │
└───────────────────────────────────────────────────────────────────────┘

Primary Region: [To be configured based on company policy]
│
Recommended Regions:
├─> US: East US 2 (if US-based company)
├─> EU: West Europe (if GDPR strict compliance)
├─> UK: UK South (if UK-based company)
└─> Canada: Canada Central (if Canadian company)

Data Residency Guarantees:
│
├─> All data stored in selected region
│   ├─> Cosmos DB: Primary region (single-region deployment)
│   ├─> Blob Storage: Primary region (LRS or ZRS)
│   ├─> Azure OpenAI: Primary region deployment
│   ├─> Document Intelligence: Primary region
│   └─> Service Bus: Primary region
│
├─> Data does NOT leave Microsoft cloud
│   ├─> No data sent to OpenAI.com (using Azure OpenAI)
│   ├─> No data sent to third-party services
│   └─> All processing within Azure
│
├─> Backup & Disaster Recovery
│   ├─> Cosmos DB: Continuous backup (same region)
│   ├─> Blob Storage: GRS (geo-redundant) optional
│   │   └─> Replicated to paired region (e.g., East US → West US)
│   └─> User can choose: LRS (local) vs GRS (geo-redundant)
│
└─> Compliance Notes
    ├─> GDPR: Data stays in EU (if EU region selected)
    ├─> HIPAA: Data stays in US (if US region selected)
    └─> Schrems II: Microsoft Azure Standard Contractual Clauses
```

---

## Monitoring, Alerting & Incident Response

### Monitoring Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                  MONITORING & OBSERVABILITY STACK                      │
└───────────────────────────────────────────────────────────────────────┘

[Layer 1: Application Insights]
│
├─> Real-time application monitoring
│   ├─> Request telemetry (latency, status codes)
│   ├─> Dependency tracking (Azure OpenAI, Cosmos DB, Blob Storage)
│   ├─> Exception tracking (errors, stack traces)
│   └─> Custom events (job started, completed, failed)
│
├─> Performance monitoring
│   ├─> Response time percentiles (p50, p95, p99)
│   ├─> Throughput (requests per second)
│   ├─> Failed request rate
│   └─> Slow queries (Cosmos DB)
│
└─> User analytics (anonymized)
    ├─> Active users
    ├─> Job completion rate
    └─> Average processing time

[Layer 2: Azure Monitor]
│
├─> Infrastructure monitoring
│   ├─> Container Apps: CPU, memory, scale events
│   ├─> Cosmos DB: RU consumption, throttling
│   ├─> Blob Storage: IOPS, bandwidth, capacity
│   └─> Service Bus: Queue depth, dead letters
│
├─> Security monitoring
│   ├─> Failed authentication attempts
│   ├─> Authorization failures (403 errors)
│   ├─> Key Vault access (secret reads)
│   └─> Network security group (NSG) flows
│
└─> Cost monitoring
    ├─> Azure Cost Management integration
    ├─> Cost per job calculated
    └─> Budget alerts (if over threshold)

[Layer 3: Azure Defender (Security Alerts)]
│
├─> Threat detection
│   ├─> SQL injection attempts
│   ├─> Suspicious file uploads (malware)
│   ├─> Brute-force authentication
│   ├─> Data exfiltration patterns
│   └─> Cryptojacking detection
│
├─> Vulnerability scanning
│   ├─> Container image scanning
│   ├─> Dependency vulnerabilities (Dependabot)
│   └─> Security baseline deviations
│
└─> Compliance monitoring
    ├─> Azure Security Center recommendations
    ├─> Regulatory compliance dashboard
    └─> Secure score tracking

[Layer 4: Log Analytics Workspace]
│
├─> Centralized log aggregation
│   ├─> Application logs (Container Apps)
│   ├─> Security logs (Azure AD, Key Vault)
│   ├─> Audit logs (Cosmos DB, Blob Storage)
│   └─> Network logs (Front Door, WAF)
│
├─> Log retention
│   ├─> Application logs: 90 days
│   ├─> Security logs: 1 year
│   ├─> Audit logs: 7 years (if compliance required)
│   └─> Archived to cold storage (Azure Data Lake)
│
└─> Kusto Query Language (KQL) queries
    ├─> Custom dashboards
    ├─> Saved queries for common scenarios
    └─> Exported to Power BI for reporting
```

### Security Alerting Rules

```
┌───────────────────────────────────────────────────────────────────────┐
│                  SECURITY ALERT CONFIGURATION                          │
└───────────────────────────────────────────────────────────────────────┘

[Critical Alerts] (Immediate notification to SOC)
│
├─> Alert 1: Multiple failed authentication attempts
│   ├─> Condition: >5 failed logins from same IP in 5 minutes
│   ├─> Action: Block IP for 1 hour, notify security team
│   └─> Severity: High
│
├─> Alert 2: Unauthorized data access attempt
│   ├─> Condition: 403 Forbidden errors for sensitive endpoints
│   ├─> Action: Audit log entry, notify security team
│   └─> Severity: High
│
├─> Alert 3: Mass data download
│   ├─> Condition: User downloads >100 documents in 10 minutes
│   ├─> Action: Temporarily suspend account, notify security team
│   └─> Severity: Critical
│
├─> Alert 4: Azure Defender threat detected
│   ├─> Condition: Malware, SQL injection, etc. detected
│   ├─> Action: Block request, quarantine file, notify security team
│   └─> Severity: Critical
│
└─> Alert 5: Key Vault secret access anomaly
    ├─> Condition: Unusual secret access pattern (e.g., wrong identity)
    ├─> Action: Revoke Managed Identity, notify security team
    └─> Severity: Critical

[High Alerts] (Notify within 1 hour)
│
├─> Alert 6: High error rate
│   ├─> Condition: >10% of requests fail (5xx errors)
│   ├─> Action: Trigger auto-scaling, notify on-call engineer
│   └─> Severity: Medium
│
├─> Alert 7: Slow response time
│   ├─> Condition: p95 response time >5 seconds
│   ├─> Action: Check dependencies, notify on-call engineer
│   └─> Severity: Medium
│
└─> Alert 8: Queue depth increasing
    ├─> Condition: Service Bus queue >1000 messages for >10 minutes
    ├─> Action: Scale up workers, notify on-call engineer
    └─> Severity: Medium

[Medium Alerts] (Daily digest)
│
├─> Alert 9: Failed jobs
│   ├─> Condition: >5% of jobs fail
│   ├─> Action: Daily summary email to development team
│   └─> Severity: Low
│
└─> Alert 10: Cost threshold exceeded
    ├─> Condition: Daily cost >$100 (configurable)
    ├─> Action: Notify finance team
    └─> Severity: Low
```

### Incident Response Plan

```
┌───────────────────────────────────────────────────────────────────────┐
│                  INCIDENT RESPONSE RUNBOOK                             │
└───────────────────────────────────────────────────────────────────────┘

[Phase 1: Detection] (0-15 minutes)
│
├─> Alert triggered (Azure Monitor or Defender)
├─> On-call engineer notified (PagerDuty / Teams)
├─> Severity assessment (Critical, High, Medium, Low)
└─> Create incident ticket (ServiceNow / Jira)

[Phase 2: Triage] (15-30 minutes)
│
├─> Verify alert is not false positive
├─> Check scope of impact (how many users affected?)
├─> Check related alerts (is this part of larger incident?)
└─> Escalate if needed (Critical → involve security team)

[Phase 3: Containment] (30-60 minutes)
│
├─> For security incidents:
│   ├─> Isolate affected resources (block IP, disable account)
│   ├─> Preserve evidence (snapshot VM, export logs)
│   └─> Prevent further damage (rotate keys, revoke tokens)
│
├─> For availability incidents:
│   ├─> Failover to backup region (if available)
│   ├─> Scale up resources (if capacity issue)
│   └─> Apply hotfix (if bug identified)
│
└─> Communication:
    ├─> Notify affected users (via email or status page)
    └─> Update incident ticket with actions taken

[Phase 4: Eradication] (1-4 hours)
│
├─> Identify root cause
├─> Remove threat or fix bug
├─> Deploy patch or configuration change
└─> Verify fix in staging environment first

[Phase 5: Recovery] (4-8 hours)
│
├─> Deploy fix to production
├─> Monitor for recurrence
├─> Restore any data from backups (if needed)
└─> Verify system back to normal

[Phase 6: Post-Incident] (1-2 days after)
│
├─> Conduct post-mortem meeting
├─> Document lessons learned
├─> Create action items (prevent recurrence)
├─> Update runbooks and documentation
└─> Close incident ticket

[Common Scenarios & Runbooks]
│
├─> Scenario 1: Data breach (unauthorized access)
│   ├─> Contain: Revoke access, rotate all keys
│   ├─> Investigate: Audit logs, identify scope
│   ├─> Notify: Users (within 72 hours for GDPR)
│   └─> Report: Regulatory bodies (if required)
│
├─> Scenario 2: Service outage (Azure service down)
│   ├─> Check Azure status page
│   ├─> Failover to secondary region (if available)
│   ├─> Notify users of degraded service
│   └─> Monitor Azure service health for recovery
│
└─> Scenario 3: Malware upload
    ├─> Quarantine file immediately (move to isolation container)
    ├─> Scan with Azure Defender for detailed analysis
    ├─> Notify user (file rejected due to security policy)
    └─> Block user if repeated attempts
```

---

## Risk Assessment & Mitigation

### Security Risk Matrix

```
┌───────────────────────────────────────────────────────────────────────┐
│                  SECURITY RISK ASSESSMENT                              │
└───────────────────────────────────────────────────────────────────────┘

Risk 1: Unauthorized Data Access
├─> Likelihood: Low
├─> Impact: High
├─> Current Controls:
│   ✓ Azure AD authentication (MFA enforced)
│   ✓ RBAC (user can only access own data)
│   ✓ JWT token validation on every request
│   ✓ Partition keys (data isolation)
│   ✓ Audit logging (all access logged)
└─> Residual Risk: Low

Risk 2: Data Breach (Exfiltration)
├─> Likelihood: Low
├─> Impact: Critical
├─> Current Controls:
│   ✓ Encryption at rest (AES-256)
│   ✓ Encryption in transit (TLS 1.3)
│   ✓ Private endpoints (no public access to data)
│   ✓ Azure Defender threat detection
│   ✓ Download rate limiting (prevent mass download)
│   ✓ Audit logging (detect anomalous patterns)
└─> Residual Risk: Low

Risk 3: Malware Upload
├─> Likelihood: Medium
├─> Impact: Medium
├─> Current Controls:
│   ✓ File type whitelist (.txt, .pdf, .docx only)
│   ✓ File size limit (10 MB)
│   ✓ Azure Defender malware scanning
│   ✓ Isolated processing (worker cannot access internet)
└─> Residual Risk: Low

Risk 4: Denial of Service (DoS)
├─> Likelihood: Medium
├─> Impact: Medium
├─> Current Controls:
│   ✓ Azure Front Door DDoS Protection
│   ✓ Rate limiting (per IP, per user)
│   ✓ Auto-scaling (Container Apps)
│   ✓ Queue-based processing (absorb spikes)
│   ✓ WAF rules (block malicious patterns)
└─> Residual Risk: Low

Risk 5: Credential Theft
├─> Likelihood: Low
├─> Impact: High
├─> Current Controls:
│   ✓ MFA enforced (Azure AD B2C)
│   ✓ Conditional access policies (trusted devices only)
│   ✓ httpOnly, secure cookies (prevent XSS token theft)
│   ✓ Short token lifetime (1 hour)
│   ✓ Failed login alerts (detect brute force)
└─> Residual Risk: Low

Risk 6: Insider Threat (Malicious Employee)
├─> Likelihood: Low
├─> Impact: High
├─> Current Controls:
│   ✓ RBAC (least privilege principle)
│   ✓ Managed Identity (no keys accessible to humans)
│   ✓ Audit logging (all actions logged)
│   ✓ Regular access reviews
│   ✓ Separation of duties (no single person has full access)
└─> Residual Risk: Low

Risk 7: Supply Chain Attack (Compromised Dependency)
├─> Likelihood: Low
├─> Impact: High
├─> Current Controls:
│   ✓ Dependabot security alerts
│   ✓ Regular dependency updates
│   ✓ Container image scanning (Azure Defender)
│   ✓ Pin dependency versions (requirements.txt)
│   ✓ Code review (all changes reviewed)
└─> Residual Risk: Medium

Risk 8: Azure Service Outage
├─> Likelihood: Low
├─> Impact: Medium
├─> Current Controls:
│   ✓ Multi-region deployment (optional)
│   ✓ Cosmos DB automatic failover
│   ✓ Blob Storage geo-redundancy
│   ✓ Service Bus redundancy
│   ✓ Health monitoring and alerts
└─> Residual Risk: Low

Risk 9: Data Loss (Accidental Deletion)
├─> Likelihood: Low
├─> Impact: Medium
├─> Current Controls:
│   ✓ Soft delete (Blob Storage, Key Vault)
│   ✓ Continuous backup (Cosmos DB)
│   ✓ Point-in-time restore (30 days)
│   ✓ Blob versioning
│   ✓ Immutable storage (optional)
└─> Residual Risk: Low

Risk 10: Compliance Violation (GDPR, HIPAA)
├─> Likelihood: Low
├─> Impact: Critical
├─> Current Controls:
│   ✓ Data retention policies (auto-delete after 90 days)
│   ✓ Right to be forgotten (user can request deletion)
│   ✓ Audit trail (all data access logged)
│   ✓ Encryption (at rest and in transit)
│   ✓ Azure compliance certifications (GDPR, HIPAA, SOC 2)
│   ✓ Regular compliance audits
└─> Residual Risk: Low
```

---

## Deployment Architecture (Vercel + Azure)

### Production Deployment Configuration

```
┌───────────────────────────────────────────────────────────────────────┐
│                  VERCEL DEPLOYMENT CONFIGURATION                       │
└───────────────────────────────────────────────────────────────────────┘

Vercel Project: "scripttodoc"
├─> Framework: Next.js 14
├─> Region: Auto (Edge Network - global CDN)
├─> Build Command: npm run build
├─> Output Directory: .next
├─> Install Command: npm install
└─> Node.js Version: 18.x

Environment Variables (Vercel):
├─> NEXT_PUBLIC_API_URL=https://api.scripttodoc.azure.com
├─> NEXT_PUBLIC_AZURE_AD_CLIENT_ID={client_id}
├─> NEXT_PUBLIC_AZURE_AD_TENANT={tenant_id}
├─> NEXT_PUBLIC_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/{tenant}
└─> NEXT_PUBLIC_AZURE_AD_REDIRECT_URI=https://scripttodoc.vercel.app/auth/callback

Security Headers (vercel.json):
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.scripttodoc.azure.com https://login.microsoftonline.com; frame-ancestors 'none';"
        }
      ]
    }
  ]
}

┌───────────────────────────────────────────────────────────────────────┐
│                  AZURE DEPLOYMENT CONFIGURATION                        │
└───────────────────────────────────────────────────────────────────────┘

Resource Group: "rg-scripttodoc-prod"
Location: East US 2 (or company-preferred region)
│
├─> [1] Azure Container Registry (ACR)
│   ├─> Name: crscripttodocprod
│   ├─> SKU: Standard
│   ├─> Admin user: Disabled (use Managed Identity)
│   └─> Geo-replication: Disabled (single region)
│
├─> [2] Azure Container Apps (API)
│   ├─> Name: ca-scripttodoc-api-prod
│   ├─> Image: crscripttodocprod.azurecr.io/api:latest
│   ├─> CPU: 0.5 cores, Memory: 1 GB
│   ├─> Scale: Min 1, Max 10 replicas
│   ├─> Ingress: External (HTTPS only)
│   ├─> Custom domain: api.scripttodoc.azure.com
│   ├─> Managed Identity: System-assigned (enabled)
│   └─> Secrets: From Key Vault (reference)
│
├─> [3] Azure Container Apps (Worker)
│   ├─> Name: ca-scripttodoc-worker-prod
│   ├─> Image: crscripttodocprod.azurecr.io/worker:latest
│   ├─> CPU: 1 core, Memory: 2 GB
│   ├─> Scale: Min 0, Max 5 replicas (scale to zero)
│   ├─> Ingress: None (internal only)
│   ├─> Managed Identity: System-assigned (enabled)
│   └─> Triggers: Azure Service Bus queue
│
├─> [4] Azure Cosmos DB
│   ├─> Name: cosmos-scripttodoc-prod
│   ├─> API: NoSQL
│   ├─> Consistency: Session
│   ├─> Geo-replication: Single region (LRS)
│   ├─> Backup: Continuous (point-in-time restore)
│   ├─> Network: Private endpoint (optional) or Firewall
│   └─> Database: scripttodoc, Container: jobs
│
├─> [5] Azure Blob Storage
│   ├─> Name: stscripttodocprod
│   ├─> Replication: LRS (or GRS for geo-redundancy)
│   ├─> Access tier: Hot
│   ├─> Encryption: Microsoft-managed keys (or CMK)
│   ├─> Soft delete: Enabled (7 days)
│   ├─> Versioning: Enabled
│   ├─> Containers: uploads, documents, temp
│   ├─> Network: Private endpoint (optional) or Firewall
│   └─> Lifecycle policies: Enabled
│
├─> [6] Azure Service Bus
│   ├─> Name: sb-scripttodoc-prod
│   ├─> Tier: Standard
│   ├─> Queue: scripttodoc-jobs
│   ├─> Max queue size: 5 GB
│   ├─> Message TTL: 30 minutes
│   └─> Dead-letter queue: Enabled
│
├─> [7] Azure Key Vault
│   ├─> Name: kv-scripttodoc-prod
│   ├─> SKU: Standard
│   ├─> Soft delete: Enabled (90 days)
│   ├─> Purge protection: Enabled
│   ├─> Network: Private endpoint (optional) or Firewall
│   └─> Access policies: Managed Identities only
│
├─> [8] Azure OpenAI
│   ├─> Name: openai-scripttodoc-prod
│   ├─> Region: East US 2 (same as other resources)
│   ├─> Deployment: gpt-4o-mini (model)
│   ├─> Network: Private endpoint (optional) or Firewall
│   └─> Data location: East US 2 (data does not leave Azure)
│
├─> [9] Azure Document Intelligence
│   ├─> Name: di-scripttodoc-prod
│   ├─> Tier: S0 (Standard)
│   ├─> Region: East US 2
│   └─> Network: Private endpoint (optional) or Firewall
│
├─> [10] Azure Front Door
│   ├─> Name: fd-scripttodoc-prod
│   ├─> Tier: Premium (includes WAF)
│   ├─> Backend pool: Container Apps API
│   ├─> Custom domain: api.scripttodoc.azure.com
│   ├─> SSL certificate: Managed (auto-renew)
│   ├─> WAF policy: Enabled (OWASP 3.2 rules)
│   └─> DDoS protection: Standard
│
├─> [11] Application Insights
│   ├─> Name: appinsights-scripttodoc-prod
│   ├─> Workspace: Log Analytics Workspace
│   ├─> Sampling: 10% (normal), 100% (errors)
│   └─> Retention: 90 days
│
└─> [12] Azure Monitor
    ├─> Alerts: Configured (see alert rules above)
    ├─> Dashboards: Application health, security, cost
    └─> Action Groups: Email, SMS, PagerDuty
```

---

## Information Governance Checklist

### Pre-Deployment Approval Checklist

```
┌───────────────────────────────────────────────────────────────────────┐
│              INFORMATION GOVERNANCE APPROVAL CHECKLIST                 │
└───────────────────────────────────────────────────────────────────────┘

Security & Access Control:
├─> [✓] All user access requires Azure AD authentication
├─> [✓] Multi-factor authentication (MFA) enforced
├─> [✓] Role-based access control (RBAC) implemented
├─> [✓] Least privilege principle applied
├─> [✓] JWT token validation on every API request
├─> [✓] User can only access own data (partition keys)
└─> [✓] Audit logging for all data access

Data Encryption:
├─> [✓] Encryption at rest (AES-256) for all data stores
├─> [✓] Encryption in transit (TLS 1.3) for all communications
├─> [✓] Managed Identity for service-to-service auth (no keys in code)
├─> [✓] Secrets stored in Azure Key Vault only
└─> [✓] Optional: Customer-managed keys (CMK) via Key Vault

Data Residency & Compliance:
├─> [✓] All data stays within Microsoft Azure (no third-party)
├─> [✓] Data stored in specified region (e.g., East US 2)
├─> [✓] No data sent to OpenAI.com (using Azure OpenAI)
├─> [✓] Azure DI processes data ephemerally (no retention)
├─> [✓] Compliance: GDPR, HIPAA, SOC 2, ISO 27001 ready
└─> [✓] Data retention policy: 90 days (configurable)

Network Security:
├─> [✓] Web Application Firewall (WAF) enabled (Azure Front Door)
├─> [✓] DDoS Protection Standard
├─> [✓] Rate limiting (per IP, per user)
├─> [✓] Private endpoints for data services (optional)
├─> [✓] No public internet access to backend workers
└─> [✓] VNet injection available for extra isolation

Monitoring & Audit:
├─> [✓] Application Insights enabled (request telemetry)
├─> [✓] Azure Monitor alerts configured
├─> [✓] Azure Defender threat detection enabled
├─> [✓] Audit logs for all data operations
├─> [✓] Log retention: 90 days (application), 1 year (security)
├─> [✓] Incident response plan documented
└─> [✓] Security alerts to SOC team

Data Protection & Privacy:
├─> [✓] User can download all their data (GDPR right to access)
├─> [✓] User can request deletion (GDPR right to be forgotten)
├─> [✓] Consent recorded before processing
├─> [✓] PII detection and redaction available (optional)
├─> [✓] Soft delete enabled (7-day recovery window)
├─> [✓] Continuous backup (Cosmos DB point-in-time restore)
└─> [✓] Data breach notification plan (72 hours)

Secrets Management:
├─> [✓] NO secrets in code repository
├─> [✓] NO secrets in environment variables (Container Apps config)
├─> [✓] All secrets in Azure Key Vault
├─> [✓] Managed Identity for all Azure service access
├─> [✓] Quarterly key rotation schedule
└─> [✓] Soft delete + purge protection (Key Vault)

Vercel Frontend Security:
├─> [✓] Static assets only (no backend logic on Vercel)
├─> [✓] NO sensitive data stored on Vercel
├─> [✓] NO database connections from Vercel
├─> [✓] NO API keys in frontend environment variables
├─> [✓] All API calls go to Azure backend (CORS validated)
├─> [✓] Security headers configured (CSP, HSTS, X-Frame-Options)
└─> [✓] httpOnly, secure, SameSite cookies (JWT tokens)

Testing & Validation:
├─> [  ] Penetration testing completed (annual)
├─> [  ] Vulnerability scanning (Azure Defender)
├─> [  ] Security code review completed
├─> [  ] Load testing completed
├─> [  ] Disaster recovery tested
└─> [  ] Compliance audit completed

Documentation:
├─> [✓] Architecture diagram (this document)
├─> [✓] Data flow diagram (this document)
├─> [✓] Security controls documented
├─> [✓] Incident response plan documented
├─> [✓] Privacy policy published
├─> [✓] Terms of service published
└─> [  ] User training materials prepared

Approval Sign-off:
├─> [  ] Information Security Officer (ISO): ________________ Date: _______
├─> [  ] Data Protection Officer (DPO): ________________ Date: _______
├─> [  ] Chief Information Officer (CIO): ________________ Date: _______
└─> [  ] Legal / Compliance: ________________ Date: _______
```

---

## Cost Estimation

### Monthly Cost Breakdown (Estimated for 1,000 jobs/month)

```
┌───────────────────────────────────────────────────────────────────────┐
│                  AZURE COST ESTIMATION (Production)                    │
└───────────────────────────────────────────────────────────────────────┘

Compute:
├─> Azure Container Apps (API): $50-100/month
│   └─> Min 1 replica × 730 hours × $0.12/vCPU-hour
├─> Azure Container Apps (Worker): $20-50/month
│   └─> Scale to zero, avg 0.3 replicas × 730 hours × $0.24/vCPU-hour
└─> Subtotal: $70-150/month

Storage:
├─> Cosmos DB (Serverless): $30-60/month
│   └─> ~10M RU/month × $0.28 per 1M RU
├─> Blob Storage: $15-30/month
│   └─> 500 GB storage × $0.02/GB + transactions
└─> Subtotal: $45-90/month

AI Services:
├─> Azure OpenAI (GPT-4o-mini): $150-300/month
│   └─> ~5M tokens/month × $0.30 per 1M tokens (input) + $0.60 (output)
├─> Azure Document Intelligence: $30-60/month
│   └─> ~2,000 pages/month × $0.015/page (prebuilt-read)
└─> Subtotal: $180-360/month

Networking:
├─> Azure Front Door (Premium): $50-80/month
│   └─> Base fee + data transfer
├─> Data transfer (outbound): $10-20/month
│   └─> ~100 GB × $0.12/GB
└─> Subtotal: $60-100/month

Monitoring & Security:
├─> Application Insights: $20-40/month
│   └─> ~10 GB logs × $2.88/GB
├─> Azure Defender: $15/month
│   └─> Container registry + storage scanning
└─> Subtotal: $35-55/month

Messaging:
├─> Azure Service Bus (Standard): $10/month
│   └─> Base tier + operations
└─> Subtotal: $10/month

Total Estimated Cost: $400-765/month (for 1,000 jobs/month)

Cost per job: $0.40-0.77

Vercel Cost: $0-20/month (Hobby tier free, Pro $20/month)
└─> Frontend hosting only (static assets)

TOTAL (Azure + Vercel): $400-785/month

Cost Optimization Tips:
├─> Use gpt-4o-mini instead of gpt-4o (10x cheaper)
├─> Enable Cosmos DB autoscale (pay only for used RU)
├─> Scale to zero for worker instances (when idle)
├─> Lifecycle policies for blob storage (auto-delete old files)
└─> Cache Azure DI results (reduce duplicate API calls)
```

---

## Summary for Information Governance

### Security Highlights (TL;DR for IG Review)

1. **Zero-Trust Architecture**
   - Every request authenticated with Azure AD (MFA enforced)
   - JWT token validation on every API call
   - Users can only access their own data (partition keys)

2. **Data Stays in Microsoft Cloud**
   - 100% Azure backend (no third-party services)
   - Vercel frontend is static assets only (no sensitive data)
   - All processing within Azure (data residency guaranteed)

3. **Encryption Everywhere**
   - AES-256 encryption at rest (all data stores)
   - TLS 1.3 encryption in transit (all communications)
   - Customer-managed keys (CMK) available via Key Vault

4. **Comprehensive Audit Trail**
   - All data access logged (who, what, when)
   - Logs retained for 90 days (1 year for security logs)
   - Alerts on suspicious activity (failed auth, mass downloads)

5. **Compliance Ready**
   - GDPR: Right to access, right to be forgotten, data minimization
   - HIPAA: BAA available, encryption, audit logging
   - SOC 2: Security, availability, confidentiality, privacy
   - ISO 27001: Risk assessment, access control, cryptography

6. **Defense in Depth**
   - WAF + DDoS Protection (Layer 7)
   - Azure Defender threat detection (real-time)
   - Rate limiting (prevent brute force, DoS)
   - Managed Identity (no API keys in code)
   - Secrets in Key Vault only (quarterly rotation)

7. **Data Retention & Deletion**
   - Auto-delete after 90 days (configurable)
   - User can request early deletion (GDPR)
   - Soft delete enabled (7-day recovery window)
   - Continuous backup (point-in-time restore)

8. **Incident Response Plan**
   - 24/7 monitoring with Azure Defender
   - Automated alerts to SOC team
   - Documented runbooks for common scenarios
   - Post-incident reviews and lessons learned

---

**Document prepared by**: Development Team
**Date**: December 9, 2025
**Version**: 1.0
**Status**: Awaiting Information Governance Approval

**Next Steps**:
1. IG team reviews this document
2. Schedule security review meeting
3. Address any concerns or questions
4. Obtain sign-off from ISO, DPO, CIO
5. Proceed with production deployment

**Contact**: [Your Name/Team] | [Email] | [Phone]
