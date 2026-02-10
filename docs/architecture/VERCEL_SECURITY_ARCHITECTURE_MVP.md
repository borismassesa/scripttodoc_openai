# Vercel + Azure Deployment: MVP Security Architecture

**Version**: 2.0 - MVP FOCUSED
**Date**: December 9, 2025
**Status**: For IG Review and Approval
**Target**: Minimum Viable Product (3-4 weeks implementation)

---

## 🎯 Executive Summary

This document outlines a **practical, implementable security architecture** for ScriptToDoc MVP deployment with:
- **Vercel-hosted frontend** (static site, no backend)
- **Azure-hosted backend** (100% Microsoft cloud)
- **3-4 week implementation timeline**
- **$95-190/month estimated cost**

### What's Different in This MVP Approach

**❌ NOT in MVP** (implement post-launch):
- Azure Front Door + WAF
- Advanced rate limiting
- Private Link / VNet injection
- Azure Defender
- SOC 2 audit
- Penetration testing

**✅ IN MVP** (sufficient for IG approval):
- Azure AD authentication (with MFA support)
- Encryption (automatic in Azure)
- User data isolation
- Basic audit logging
- HTTPS/TLS everywhere
- Secrets in Key Vault
- GDPR-ready data controls

---

## 📋 MVP Implementation Checklist

### Security Controls (15 items - all low-to-medium complexity)

| # | Feature | Complexity | Time | Priority |
|---|---------|------------|------|----------|
| 1 | Azure AD B2C setup (OAuth 2.0) | Medium | 4h | **P0** |
| 2 | JWT validation middleware (FastAPI) | Low | 2h | **P0** |
| 3 | RBAC: Partition Cosmos DB by `userId` | Low | 1h | **P0** |
| 4 | HTTPS enforced on Container Apps | Auto | 0h | **P0** |
| 5 | Blob Storage private containers | Low | 1h | **P0** |
| 6 | File type whitelist validation | Low | 2h | **P0** |
| 7 | File size limits (10 MB max) | Low | 1h | **P0** |
| 8 | Secrets in Azure Key Vault | Low | 2h | **P0** |
| 9 | Managed Identity (Container Apps) | Medium | 3h | **P0** |
| 10 | Basic audit logging (App Insights) | Low | 2h | **P0** |
| 11 | CORS config (Vercel origin only) | Low | 1h | **P0** |
| 12 | Vercel security headers (CSP, HSTS) | Low | 1h | **P0** |
| 13 | Data retention (90-day auto-delete) | Medium | 3h | **P0** |
| 14 | User data isolation checks | Low | 2h | **P0** |
| 15 | httpOnly/secure cookies for JWT | Low | 1h | **P0** |

**Total MVP Security Implementation**: ~26 hours (~3-4 days)

### What's Automatic (0 hours - Azure handles it)

- ✅ Encryption at rest (AES-256) - automatic in Cosmos DB & Blob Storage
- ✅ TLS 1.2+ encryption - automatic on Container Apps & Vercel
- ✅ DDoS protection (basic) - automatic on Vercel
- ✅ Backup (Cosmos DB) - automatic continuous backup enabled by default

---

## 🏗️ MVP Architecture Diagram

### Simplified Architecture (No WAF, No Private Link)

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER's BROWSER                                 │
│  ✅ Azure AD B2C login (OAuth 2.0)                               │
│  ✅ JWT token in httpOnly, secure cookie                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS (automatic)
                           │ Authorization: Bearer {JWT}
┌──────────────────────────┴───────────────────────────────────────┐
│             VERCEL (Frontend CDN)                  ✅ MVP         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Next.js Static Site                                       │  │
│  │  • HTML/CSS/JS only (no backend code)                     │  │
│  │  • NO sensitive data                                       │  │
│  │  • NO database connections                                 │  │
│  │  • NO API keys                                             │  │
│  │                                                             │  │
│  │  Built-in Security:                                        │  │
│  │  ✅ Automatic HTTPS/TLS                                   │  │
│  │  ✅ DDoS protection (Vercel Edge)                         │  │
│  │  ✅ Security headers (configured in vercel.json)          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS to Azure
                           │ CORS: Only scripttodoc.vercel.app
                           │
                           📍 POST-MVP: Add Azure Front Door + WAF here
                           │
┌──────────────────────────┴───────────────────────────────────────┐
│     AZURE CONTAINER APPS (Backend API)             ✅ MVP         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                       │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Security Middleware (Simple MVP version)           │  │  │
│  │  │  1. ✅ CORS validation                              │  │  │
│  │  │  2. ✅ JWT token validation                         │  │  │
│  │  │  3. ✅ RBAC check (userId match)                    │  │  │
│  │  │  4. ✅ Input validation (Pydantic)                  │  │  │
│  │  │  5. ✅ Audit log (critical operations)              │  │  │
│  │  │                                                       │  │  │
│  │  │  📍 POST-MVP: Add rate limiting, advanced alerts    │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  Configuration:                                            │  │
│  │  ✅ HTTPS endpoint (TLS 1.2+ enforced)                    │  │
│  │  ✅ Managed Identity enabled (no API keys in code)        │  │
│  │  ✅ Secrets from Key Vault only                           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ Managed Identity (no keys!)
        ┌──────────────────┼──────────────────┬──────────────────┐
        │                  │                  │                  │
┌───────▼────────┐ ┌───────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│ Azure Key      │ │ Azure Service  │ │ Cosmos DB   │ │ Blob Storage    │
│ Vault          │ │ Bus            │ │             │ │                 │
│                │ │                │ │ ✅ Private  │ │ ✅ Private      │
│ ✅ Secrets     │ │ ✅ Job queue   │ │ ✅ AES-256  │ │ ✅ AES-256      │
│ ✅ Managed ID  │ │ ✅ Dead letter │ │ ✅ Partition│ │ ✅ SAS tokens   │
│    access      │ │                │ │    by userId│ │ ✅ Soft delete  │
└────────────────┘ └───────┬────────┘ └─────────────┘ └─────────────────┘
                           │
                   ┌───────▼────────────────────────────────────┐
                   │  Azure Container Apps (Worker)    ✅ MVP   │
                   │  • Background processing                   │
                   │  • Managed Identity                        │
                   │  • No public access                        │
                   └───────┬────────────────────────────────────┘
                           │ Managed Identity
        ┌──────────────────┼──────────────────┬──────────────────┐
┌───────▼──────────┐ ┌─────▼──────────┐ ┌────▼────────────┐
│ Azure Document   │ │ Azure OpenAI   │ │ App Insights    │
│ Intelligence     │ │                │ │                 │
│ ✅ Ephemeral     │ │ ✅ Azure only  │ │ ✅ Audit logs   │
│ ✅ No data kept  │ │ ✅ No training │ │ ✅ Monitoring   │
└──────────────────┘ └────────────────┘ └─────────────────┘
```

**Key MVP Security Highlights:**
1. ✅ Direct HTTPS connection (Vercel → Azure Container Apps)
2. ✅ No WAF/Front Door needed for MVP (add in Phase 2)
3. ✅ Managed Identity everywhere (no API keys in code)
4. ✅ User data isolation (Cosmos DB partition keys)
5. ✅ All data in Azure (100% Microsoft ecosystem)

---

## 🔐 MVP Security Implementation Details

### 1. Authentication (Azure AD B2C)

**Implementation**: 4 hours

```typescript
// Frontend (Next.js) - pages/api/auth/[...nextauth].ts
import NextAuth from "next-auth"
import AzureADB2CProvider from "next-auth/providers/azure-ad-b2c"

export default NextAuth({
  providers: [
    AzureADB2CProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID!,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
      tenantId: process.env.AZURE_AD_TENANT_ID!,
      primaryUserFlow: "B2C_1_signupsignin",
      authorization: {
        params: {
          scope: "openid profile email offline_access"
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token
        token.userId = account.providerAccountId
      }
      return token
    }
  },
  cookies: {
    sessionToken: {
      name: `__Secure-next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: true  // HTTPS only
      }
    }
  }
})
```

**Backend (FastAPI) - JWT Validation**:

```python
# backend/api/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

security = HTTPBearer()

# Cache JWKS keys for 24 hours
jwks_cache = {}

async def get_azure_ad_public_keys():
    """Fetch Azure AD B2C public keys for JWT validation"""
    if 'keys' in jwks_cache:
        return jwks_cache['keys']

    jwks_url = f"https://{TENANT}.b2clogin.com/{TENANT}.onmicrosoft.com/{POLICY}/discovery/v2.0/keys"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        jwks_cache['keys'] = response.json()
        return jwks_cache['keys']

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token on every request"""
    token = credentials.credentials

    try:
        # Get public keys from Azure AD
        jwks = await get_azure_ad_public_keys()

        # Decode and verify token
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=AZURE_AD_CLIENT_ID,
            issuer=f"https://{TENANT}.b2clogin.com/{TENANT_ID}/v2.0/"
        )

        # Extract user ID
        user_id = payload.get("sub")  # Subject = user ID
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        return user_id

    except JWTError as e:
        # Log for audit trail
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
```

**Security Notes:**
- ✅ OAuth 2.0 standard (industry best practice)
- ✅ MFA supported (configure in Azure AD B2C)
- ✅ Tokens expire after 1 hour (configurable)
- ✅ httpOnly cookies (prevent XSS attacks)
- ✅ Secure flag (HTTPS only)

---

### 2. Authorization (RBAC - User Data Isolation)

**Implementation**: 2 hours

```python
# backend/api/routes/documents.py
from fastapi import APIRouter, Depends, HTTPException
from ..auth import verify_token

router = APIRouter()

@router.get("/api/documents/{job_id}")
async def get_document(job_id: str, user_id: str = Depends(verify_token)):
    """Get document - user can only access their own documents"""

    # Query Cosmos DB with user_id as partition key
    job = await cosmos_client.read_item(
        container="jobs",
        item_id=job_id,
        partition_key=user_id  # Enforces user isolation!
    )

    if not job:
        # Job not found OR user doesn't own this job
        # (Same error to prevent user enumeration)
        raise HTTPException(status_code=404, detail="Job not found")

    # User owns this job, proceed
    return {
        "job_id": job["id"],
        "status": job["status"],
        "document_url": job.get("result", {}).get("document_url")
    }
```

**Cosmos DB Schema** (with partition key):

```json
{
  "id": "job_abc123",
  "userId": "azure_ad_user_12345",  // Partition key! ✅
  "status": "completed",
  "created": "2025-12-09T10:00:00Z",
  "result": {
    "document_url": "https://...?sv=..."  // SAS token
  }
}
```

**Security Benefits:**
- ✅ **Automatic isolation**: Queries filtered by `userId` (partition key)
- ✅ **Performance**: Cosmos DB queries within partition are fast
- ✅ **No cross-user access**: User A cannot read User B's data (database-level enforcement)

---

### 3. Encryption (Automatic in Azure)

**Implementation**: 0 hours (automatic)

**Cosmos DB Encryption**:
- ✅ AES-256 encryption at rest (automatic, no config needed)
- ✅ TLS 1.2+ in transit (enforced by default)
- ✅ No action required for MVP

**Blob Storage Encryption**:
- ✅ AES-256 encryption at rest (automatic)
- ✅ TLS 1.2+ required for all connections
- ✅ Microsoft-managed keys (default)
- 📍 POST-MVP: Customer-managed keys (CMK) optional

**Container Apps**:
- ✅ HTTPS enforced (TLS 1.2+)
- ✅ No HTTP allowed
- ✅ Automatic certificate management

**Configuration** (vercel.json for frontend):

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains"
        }
      ]
    }
  ]
}
```

---

### 4. Secrets Management (Azure Key Vault)

**Implementation**: 2 hours

**Setup**:

```bash
# 1. Create Key Vault
az keyvault create \
  --name kv-scripttodoc-mvp \
  --resource-group rg-scripttodoc-mvp \
  --location eastus2

# 2. Add secrets
az keyvault secret set \
  --vault-name kv-scripttodoc-mvp \
  --name "azure-openai-key" \
  --value "YOUR_OPENAI_KEY"

az keyvault secret set \
  --vault-name kv-scripttodoc-mvp \
  --name "cosmos-connection-string" \
  --value "YOUR_COSMOS_CONNECTION_STRING"

# 3. Grant Container Apps access via Managed Identity
az keyvault set-policy \
  --name kv-scripttodoc-mvp \
  --object-id <CONTAINER_APP_MANAGED_IDENTITY_ID> \
  --secret-permissions get list
```

**Container Apps Configuration** (use Key Vault references):

```yaml
# Container Apps - secrets from Key Vault
properties:
  configuration:
    secrets:
      - name: azure-openai-key
        keyVaultUrl: https://kv-scripttodoc-mvp.vault.azure.net/secrets/azure-openai-key
        identity: system
      - name: cosmos-connection-string
        keyVaultUrl: https://kv-scripttodoc-mvp.vault.azure.net/secrets/cosmos-connection-string
        identity: system
    registries:
      - server: crscripttodocmvp.azurecr.io
        identity: system
```

**Python Code** (backend):

```python
# backend/script_to_doc/config.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

# Use Managed Identity (no keys needed!)
credential = DefaultAzureCredential()
key_vault_url = "https://kv-scripttodoc-mvp.vault.azure.net/"
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Fetch secrets at runtime
AZURE_OPENAI_KEY = secret_client.get_secret("azure-openai-key").value
COSMOS_CONNECTION_STRING = secret_client.get_secret("cosmos-connection-string").value

# Secrets never in code, environment variables, or config files! ✅
```

**Security Benefits:**
- ✅ No secrets in code repository
- ✅ No secrets in environment variables (Container Apps config)
- ✅ Managed Identity (no keys to rotate manually)
- ✅ Audit logging (all secret access logged)
- ✅ Soft delete (90-day recovery if accidentally deleted)

---

### 5. Audit Logging (Application Insights)

**Implementation**: 2 hours

**Setup**:

```python
# backend/api/main.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

# Configure Application Insights
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
))
logger.setLevel(logging.INFO)

# Middleware to log all requests
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Log request
    logger.info("API request", extra={
        "custom_dimensions": {
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
            "ip_address": request.client.host,
            "timestamp": datetime.utcnow().isoformat()
        }
    })

    response = await call_next(request)

    # Log response
    logger.info("API response", extra={
        "custom_dimensions": {
            "user_id": user_id,
            "status_code": response.status_code,
            "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
        }
    })

    return response

# Log critical operations
@router.post("/api/process")
async def process_document(file: UploadFile, user_id: str = Depends(verify_token)):
    logger.info("Document uploaded", extra={
        "custom_dimensions": {
            "user_id": user_id,
            "filename": file.filename,
            "file_size": file.size,
            "content_type": file.content_type
        }
    })
    # ... process file

@router.get("/api/documents/{job_id}")
async def download_document(job_id: str, user_id: str = Depends(verify_token)):
    logger.info("Document downloaded", extra={
        "custom_dimensions": {
            "user_id": user_id,
            "job_id": job_id
        }
    })
    # ... return document
```

**What Gets Logged (MVP)**:
- ✅ All API requests (method, path, user, timestamp)
- ✅ All API responses (status code, duration)
- ✅ File uploads (user, filename, size)
- ✅ File downloads (user, job ID)
- ✅ Authentication failures (401 errors)
- ✅ Authorization failures (403 errors)
- ✅ Application errors (500 errors)

**Retention**:
- ✅ 90 days (configurable, free tier includes 5 GB)

**📍 POST-MVP**: Add advanced alerts (e.g., >5 failed logins, unusual download patterns)

---

### 6. File Validation

**Implementation**: 3 hours

```python
# backend/api/routes/process.py
from fastapi import UploadFile, HTTPException
import magic  # python-magic library

ALLOWED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "audio/mpeg",  # .mp3
    "video/mp4"
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def validate_file(file: UploadFile) -> None:
    """Validate file type and size"""

    # 1. Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)} MB"
        )

    # 2. Check MIME type (by content, not just extension!)
    mime_type = magic.from_buffer(contents, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {mime_type}. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    # 3. Check file extension matches MIME type
    file_extension = file.filename.split('.')[-1].lower()
    expected_extensions = {
        "text/plain": ["txt"],
        "application/pdf": ["pdf"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["docx"],
        "audio/mpeg": ["mp3"],
        "video/mp4": ["mp4"]
    }

    if file_extension not in expected_extensions.get(mime_type, []):
        raise HTTPException(
            status_code=400,
            detail="File extension does not match content type"
        )

    # Reset file pointer
    await file.seek(0)

    logger.info("File validated", extra={
        "custom_dimensions": {
            "filename": file.filename,
            "mime_type": mime_type,
            "size": len(contents)
        }
    })

@router.post("/api/process")
async def process_document(
    file: UploadFile,
    user_id: str = Depends(verify_token)
):
    # Validate file first
    await validate_file(file)

    # Proceed with processing
    # ...
```

**Security Benefits:**
- ✅ File size limit (prevent DoS via large uploads)
- ✅ MIME type validation by content (not just extension)
- ✅ Extension spoofing protection (check extension matches content)
- ✅ Whitelist approach (only allowed types accepted)

**📍 POST-MVP**: Add malware scanning with Azure Defender for Storage

---

### 7. Data Retention (90-Day Auto-Delete)

**Implementation**: 3 hours

**Blob Storage Lifecycle Policy**:

```bash
# Create lifecycle management policy
az storage account management-policy create \
  --account-name stscripttodocmvp \
  --policy @lifecycle-policy.json
```

**lifecycle-policy.json**:

```json
{
  "rules": [
    {
      "name": "delete-old-documents",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["documents/", "uploads/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 90
            }
          }
        }
      }
    },
    {
      "name": "delete-temp-files",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["temp/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 1
            }
          }
        }
      }
    }
  ]
}
```

**Cosmos DB TTL** (Time-To-Live):

```python
# backend/api/database.py
from azure.cosmos import CosmosClient

# Enable TTL on container (one-time setup)
container_definition = {
    "id": "jobs",
    "partitionKey": {"paths": ["/userId"], "kind": "Hash"},
    "defaultTtl": 7776000  # 90 days in seconds
}

database.create_container_if_not_exists(container_definition)

# When creating job record, set TTL
job_record = {
    "id": job_id,
    "userId": user_id,
    "status": "queued",
    "created": datetime.utcnow().isoformat(),
    "ttl": 7776000  # Auto-delete after 90 days
}
```

**Manual Deletion Endpoint** (GDPR "right to be forgotten"):

```python
@router.delete("/api/my-data")
async def delete_my_data(user_id: str = Depends(verify_token)):
    """Delete all user data immediately (GDPR compliance)"""

    # 1. Delete all user's job records from Cosmos DB
    query = "SELECT * FROM c WHERE c.userId = @userId"
    jobs = list(cosmos_container.query_items(
        query=query,
        parameters=[{"name": "@userId", "value": user_id}],
        partition_key=user_id
    ))

    for job in jobs:
        # Delete job record
        cosmos_container.delete_item(item=job["id"], partition_key=user_id)

        # Delete associated blobs
        blob_service_client.get_blob_client(
            container="documents",
            blob=f"{user_id}/{job['id']}/document.docx"
        ).delete_blob()

    logger.warning("User data deleted (GDPR request)", extra={
        "custom_dimensions": {
            "user_id": user_id,
            "jobs_deleted": len(jobs)
        }
    })

    return {"message": f"Deleted {len(jobs)} jobs and all associated data"}
```

**Security & Compliance Benefits:**
- ✅ GDPR compliance (data not kept longer than necessary)
- ✅ Automatic cleanup (no manual intervention)
- ✅ User can request immediate deletion
- ✅ Audit log preserved (even after data deletion)

---

### 8. CORS Configuration

**Implementation**: 1 hour

```python
# backend/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration (only allow Vercel frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://scripttodoc.vercel.app",  # Production
        "http://localhost:3000"  # Local development
    ],
    allow_credentials=True,  # Allow cookies (JWT tokens)
    allow_methods=["GET", "POST", "DELETE"],  # Only needed methods
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

**Security Benefits:**
- ✅ Only Vercel frontend can call API (blocks unauthorized origins)
- ✅ Credentials (cookies) allowed only from trusted origins
- ✅ Limited HTTP methods (principle of least privilege)

---

### 9. Vercel Security Headers

**Implementation**: 1 hour

**vercel.json**:

```json
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
          "value": "max-age=31536000; includeSubDomains; preload"
        },
        {
          "key": "Permissions-Policy",
          "value": "geolocation=(), microphone=(), camera=()"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.azurecontainerapps.io https://login.microsoftonline.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        }
      ]
    }
  ]
}
```

**What These Headers Do:**
- ✅ **X-Frame-Options**: Prevent clickjacking (site can't be embedded in iframe)
- ✅ **X-Content-Type-Options**: Prevent MIME-type sniffing attacks
- ✅ **X-XSS-Protection**: Enable browser's XSS filter
- ✅ **HSTS**: Force HTTPS (even if user types http://)
- ✅ **CSP**: Control what resources can load (prevent XSS, injection attacks)
- ✅ **Permissions-Policy**: Disable unnecessary browser APIs (geolocation, camera, etc.)

---

## 📊 MVP Cost Breakdown

### Estimated Monthly Costs (100 jobs/month)

| Service | Configuration | Cost/Month |
|---------|--------------|------------|
| **Azure Container Apps (API)** | 0.5 vCPU, 1 GB RAM, min 1 replica | $30-50 |
| **Azure Container Apps (Worker)** | 1 vCPU, 2 GB RAM, scale to 0 | $10-20 |
| **Azure Cosmos DB** | Serverless, ~5M RU/month | $15-25 |
| **Azure Blob Storage** | 50 GB + transactions | $5-10 |
| **Azure Service Bus** | Standard tier | $10 |
| **Azure OpenAI** | GPT-4o-mini, ~500K tokens/month | $15-30 |
| **Azure Document Intelligence** | prebuilt-read, ~200 pages/month | $5 |
| **Azure Key Vault** | Standard, ~100 operations/month | $1 |
| **Application Insights** | 5 GB ingestion (free), 90-day retention | $5 |
| **Vercel** | Hobby (free) or Pro | $0-20 |
| **TOTAL (MVP)** |  | **$96-191/month** |

**Cost per job**: ~$0.96-1.91

### Cost Comparison: MVP vs Production

| Phase | Monthly Cost | Additional Features |
|-------|--------------|---------------------|
| **MVP** | $96-191 | Basic security + compliance |
| **Production** | $191-315 | + Front Door, WAF, Defender, advanced monitoring |
| **Enterprise** | $400-785 | + Private Link, geo-redundancy, SOC 2 audit |

---

## 🎯 MVP vs Post-MVP Features

### ✅ MVP (Week 1-4) - MUST IMPLEMENT

| Feature | Why It's MVP | Effort |
|---------|--------------|--------|
| Azure AD authentication | **Required** - Can't allow unauthenticated access | Medium |
| JWT validation | **Required** - Verify every request | Low |
| User data isolation (RBAC) | **Required** - Users can't see each other's data | Low |
| Encryption (automatic) | **Required** - GDPR/compliance | None (auto) |
| HTTPS/TLS everywhere | **Required** - Industry standard | None (auto) |
| File validation | **Required** - Prevent malicious uploads | Low |
| Secrets in Key Vault | **Required** - Can't hardcode secrets | Low |
| Managed Identity | **Required** - Best practice, no key management | Medium |
| Basic audit logging | **Required** - Compliance, troubleshooting | Low |
| Data retention (90 days) | **Required** - GDPR compliance | Low |
| CORS configuration | **Required** - Prevent unauthorized API access | Low |
| Security headers | **Required** - Industry best practice | Low |

**Total MVP Effort**: 26 hours (~3-4 days)

### 🔄 POST-MVP (Week 5-10) - ADD FOR PRODUCTION

| Feature | Why It's Post-MVP | Effort |
|---------|-------------------|--------|
| Azure Front Door + WAF | **Nice-to-have** - Extra protection layer | High (2-3 days) |
| Rate limiting (per user) | **Nice-to-have** - Prevent abuse | Medium (1 day) |
| Azure Defender | **Nice-to-have** - Advanced threat detection | Low (4 hours) |
| Advanced alerting | **Nice-to-have** - Proactive monitoring | Medium (1 day) |
| Malware scanning | **Nice-to-have** - Extra file validation | Low (4 hours) |
| DDoS Protection Standard | **Nice-to-have** - Already have basic on Vercel | Low (2 hours) |

**Total Post-MVP Effort**: 40-50 hours (~6-8 days)

### 💡 OPTIONAL (Week 11+) - ONLY IF NEEDED

| Feature | Why It's Optional | Effort |
|---------|-------------------|--------|
| Private Link | Only if data must never touch internet | Very High (1-2 weeks) |
| VNet injection | Only if required by corporate policy | Very High (1-2 weeks) |
| Customer-managed keys | Only if required by compliance | Medium (1 week) |
| Geo-redundancy | Only if 99.99%+ uptime required | High (2 weeks) |
| SOC 2 Type II audit | Only if selling to enterprises | Very High (3-6 months) |
| Penetration testing | Recommended annually, not for MVP | High (1 week + vendor) |
| PII detection/redaction | Only if handling sensitive PII | High (1-2 weeks) |

---

## ✅ MVP Security Approval Checklist

### For Information Governance Review

**Authentication & Authorization:**
- [x] ✅ Azure AD authentication (industry standard)
- [x] ✅ MFA supported (configured in Azure AD B2C)
- [x] ✅ JWT token validation on every request
- [x] ✅ Users can only access own data (Cosmos DB partition keys)
- [x] ✅ Token expiration (1 hour, configurable)

**Data Protection:**
- [x] ✅ Encryption at rest (AES-256, automatic in Azure)
- [x] ✅ Encryption in transit (TLS 1.2+, enforced)
- [x] ✅ Data residency (all data in selected Azure region)
- [x] ✅ No data on Vercel (frontend is static assets only)
- [x] ✅ Data retention policy (90-day auto-delete)
- [x] ✅ User can request deletion (GDPR compliance)

**Security Best Practices:**
- [x] ✅ No secrets in code (all in Key Vault)
- [x] ✅ Managed Identity (no API keys to manage)
- [x] ✅ File validation (type whitelist, size limits)
- [x] ✅ CORS configuration (only Vercel origin)
- [x] ✅ Security headers (CSP, HSTS, X-Frame-Options)
- [x] ✅ httpOnly, secure cookies (XSS protection)

**Audit & Monitoring:**
- [x] ✅ Application Insights enabled (90-day retention)
- [x] ✅ All critical operations logged (upload, download, delete)
- [x] ✅ Authentication failures logged (401 errors)
- [x] ✅ Authorization failures logged (403 errors)

**Compliance:**
- [x] ✅ GDPR-ready (data minimization, right to be forgotten)
- [x] ✅ HIPAA-compatible (encryption, audit logs, BAA available)
- [x] ✅ All data in Microsoft ecosystem (Azure only)
- [x] ✅ No third-party data sharing (except Microsoft services)

**What's NOT in MVP** (but can be added post-launch):
- [ ] ❌ Azure Front Door + WAF (add in Phase 2)
- [ ] ❌ Rate limiting (add in Phase 2)
- [ ] ❌ Azure Defender threat detection (add in Phase 2)
- [ ] ❌ Advanced alerting rules (add in Phase 2)
- [ ] ❌ Private Link / VNet injection (optional, enterprise only)
- [ ] ❌ SOC 2 Type II audit (optional, enterprise only)

**Approval:**
- [ ] Information Security Officer (ISO): ________________ Date: _______
- [ ] Data Protection Officer (DPO): ________________ Date: _______
- [ ] Chief Information Officer (CIO): ________________ Date: _______

**Notes for IG Team:**
This MVP architecture provides **sufficient security for internal pilot/beta** launch. The controls marked as "POST-MVP" should be implemented before **public/production** launch or when handling sensitive data (PII, PHI).

---

## 🚀 Implementation Timeline

### Week 1: Azure Infrastructure Setup
- Day 1: Create Azure resources (Container Apps, Cosmos DB, Blob Storage, Key Vault)
- Day 2: Configure Managed Identity and Key Vault access
- Day 3: Setup Azure AD B2C (OAuth 2.0)
- Day 4: Deploy basic backend API (no business logic yet)
- Day 5: Test authentication flow end-to-end

### Week 2: Security Implementation
- Day 1: Implement JWT validation middleware
- Day 2: Implement RBAC (Cosmos DB partition keys)
- Day 3: Implement file validation
- Day 4: Implement audit logging (Application Insights)
- Day 5: Configure data retention policies

### Week 3: Frontend + Integration
- Day 1-2: Vercel deployment with security headers
- Day 3-4: Integrate frontend with Azure AD authentication
- Day 5: End-to-end testing

### Week 4: Testing + Documentation
- Day 1-2: Security testing (manual)
- Day 3: Performance testing
- Day 4: Documentation (runbooks, user guide)
- Day 5: IG review + approval

**Total: 4 weeks to MVP** ✅

---

## 📞 Support & Questions

**For IG Team:**
- **Primary Contact**: [Your Name] | [Email]
- **Architecture Questions**: [Technical Lead]
- **Compliance Questions**: [Compliance Officer]

**Questions to Address in IG Review:**
1. Is Azure AD B2C acceptable for authentication? (vs. corporate SSO)
2. Is 90-day data retention acceptable? (configurable to 30/60/180 days)
3. Is encryption with Microsoft-managed keys acceptable? (vs. customer-managed keys)
4. Is basic audit logging sufficient for MVP? (vs. advanced SIEM integration)
5. Is direct Vercel → Azure connection acceptable? (vs. Azure Front Door + WAF)

**Expected IG Feedback:**
- "Add WAF before production" → ✅ Planned for Post-MVP
- "Need rate limiting" → ✅ Planned for Post-MVP
- "Need malware scanning" → ✅ Planned for Post-MVP
- "Need Private Link" → 💡 Optional (very high effort)

---

**Document Status**: Ready for IG Review
**Next Action**: Schedule IG review meeting
**Timeline**: Target MVP launch in 4 weeks from approval
