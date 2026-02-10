# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email the security team at: [security-contact@example.com]
3. Include detailed information about the vulnerability
4. Allow 48 hours for initial response

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :x:                |

## Security Best Practices

### Environment Variables

- **NEVER** commit `.env` files to version control
- Use `.env.template` or `.env.example` for documentation
- Store production secrets in Azure Key Vault
- Rotate API keys every 90 days
- Use managed identities when possible

### Authentication & Authorization

- All API endpoints require authentication in production
- Use Azure AD OAuth 2.0 for user authentication
- Implement proper RBAC (Role-Based Access Control)
- Validate all JWT tokens server-side
- Implement rate limiting on all endpoints

### Data Protection

#### Encryption at Rest
- Cosmos DB encryption enabled
- Blob Storage encryption enabled
- Use customer-managed keys for sensitive data

#### Encryption in Transit
- HTTPS/TLS 1.2+ for all connections
- Secure WebSocket connections (WSS)
- No mixed content (HTTP/HTTPS)

#### Data Handling
- Sanitize all user inputs
- Validate file uploads (type, size, content)
- Implement content security policy (CSP)
- Use parameterized queries (prevent SQL injection)
- Escape output to prevent XSS

### API Security

#### Input Validation
```python
# ✅ Good - Validate and sanitize
from pydantic import BaseModel, validator

class UploadRequest(BaseModel):
    file: UploadFile
    tone: str

    @validator('tone')
    def validate_tone(cls, v):
        allowed = ['Professional', 'Casual', 'Technical']
        if v not in allowed:
            raise ValueError(f'Invalid tone. Must be one of {allowed}')
        return v
```

#### Rate Limiting
```python
# ✅ Implement rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/process")
@limiter.limit("10/minute")
async def process_file():
    pass
```

#### CORS Configuration
```python
# ✅ Restrict CORS to known origins
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-production-domain.com",
        "https://your-staging-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### File Upload Security

- **Validate file types** - Check MIME type and extension
- **Limit file size** - Max 100MB per file
- **Scan for malware** - Integrate virus scanning
- **Use temporary storage** - Auto-delete after processing
- **Rename files** - Use UUIDs instead of user-provided names

```python
# ✅ Secure file upload
ALLOWED_EXTENSIONS = {'.txt', '.docx', '.pdf', '.mp3', '.mp4'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

async def validate_file(file: UploadFile):
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    # Reset file pointer
    await file.seek(0)
    return file
```

### Azure Service Security

#### Managed Identity
```python
# ✅ Use Managed Identity instead of keys
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
cosmos_client = CosmosClient(
    url=cosmos_endpoint,
    credential=credential
)
```

#### Key Vault Integration
```python
# ✅ Retrieve secrets from Key Vault
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-keyvault.vault.azure.net/",
    credential=credential
)

openai_key = client.get_secret("openai-api-key").value
```

#### Network Security
- Use Private Endpoints for Azure services
- Configure Virtual Network integration
- Enable Azure Firewall
- Implement NSG rules
- Use Azure Front Door with WAF

### Secrets Management

#### ❌ Never Do This
```python
# ❌ BAD - Hardcoded secrets
OPENAI_KEY = "sk-1234567890abcdef"
CONNECTION_STRING = "mongodb://admin:password@localhost"
```

#### ✅ Do This Instead
```python
# ✅ GOOD - Environment variables + Key Vault
import os
from azure.keyvault.secrets import SecretClient

openai_key = os.getenv("AZURE_OPENAI_KEY")  # From env
# Or retrieve from Key Vault
openai_key = key_vault_client.get_secret("openai-key").value
```

### Dependency Security

#### Regular Updates
```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt

# Frontend
npm audit
npm audit fix
```

#### Lock Files
- Commit `requirements.txt` and `package-lock.json`
- Use exact versions for critical dependencies
- Review dependency changes before updating

### Logging and Monitoring

#### Secure Logging
```python
# ✅ GOOD - Log without sensitive data
logger.info(f"Processing job {job_id}")

# ❌ BAD - Logging sensitive data
logger.info(f"API Key: {api_key}")  # Never log secrets!
```

#### Audit Logging
- Log all authentication attempts
- Log all data access
- Log all configuration changes
- Retain logs for 90 days minimum
- Monitor for suspicious patterns

### Security Headers

Configure security headers in production:

```python
# FastAPI middleware for security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.azurecontainerapps.io"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Security Checklist for Production

### Before Deployment

- [ ] All dependencies updated and audited
- [ ] No secrets in code or configuration files
- [ ] Environment variables configured in Azure
- [ ] Managed identities enabled
- [ ] Key Vault configured and tested
- [ ] HTTPS enforced on all endpoints
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] File upload restrictions in place
- [ ] Security headers configured
- [ ] WAF rules configured
- [ ] Network security groups configured
- [ ] Logging and monitoring enabled
- [ ] Backup and DR tested

### Regular Security Tasks

#### Monthly
- Review access logs for anomalies
- Update dependencies
- Review and rotate API keys
- Check for security advisories

#### Quarterly
- Security audit
- Penetration testing
- Disaster recovery drill
- Review and update security policies

#### Annually
- Comprehensive security assessment
- Third-party security audit
- Update security training
- Review and update this policy

## Known Security Considerations

### Azure OpenAI
- API keys grant full access to the service
- Implement rate limiting to prevent abuse
- Monitor token usage and costs
- Use separate keys for dev/staging/production

### File Processing
- Uploaded files may contain malicious content
- Implement virus scanning before processing
- Run processing in isolated environment
- Set resource limits to prevent DoS

### Cosmos DB
- Partition keys can impact performance and security
- Implement row-level security where needed
- Use read-only connection strings for reporting

## Incident Response

### If a Security Breach Occurs

1. **Immediate Actions**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable enhanced monitoring
   - Notify security team

2. **Investigation**
   - Review audit logs
   - Identify scope of breach
   - Document findings
   - Preserve evidence

3. **Remediation**
   - Patch vulnerabilities
   - Rotate all credentials
   - Update security policies
   - Deploy fixes

4. **Communication**
   - Notify affected users
   - Report to stakeholders
   - Document lessons learned
   - Update security procedures

## Contact

For security concerns or questions:
- Email: [security-contact@example.com]
- Security Team: [Contact information]

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/)
- [Python Security Guidelines](https://python.readthedocs.io/en/stable/library/security.html)
- [Next.js Security](https://nextjs.org/docs/advanced-features/security-headers)

---

**Last Updated**: December 2025
**Version**: 1.0
