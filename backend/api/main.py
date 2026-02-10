"""
Main FastAPI application for ScriptToDoc.
"""

import logging
import sys
from datetime import datetime
from fastapi import FastAPI, __version__ as fastapi_version
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from script_to_doc import __version__ as scripttodoc_version
from script_to_doc.config import get_settings
from .models import HealthCheckResponse, ErrorResponse
from .routes import process, status, documents, process_simple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Reduce verbosity for Azure SDK libraries
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("azure.servicebus").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ScriptToDoc API",
    description="AI-Powered Training Document Generator using Azure AI Services",
    version=scripttodoc_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(process.router, prefix="/api", tags=["Processing"])
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting ScriptToDoc API v{scripttodoc_version}")
    logger.info(f"FastAPI v{fastapi_version}")
    
    # Load and validate settings
    try:
        settings = get_settings()
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Azure OpenAI Endpoint: {settings.azure_openai_endpoint}")
        logger.info(f"Azure DI Endpoint: {settings.azure_document_intelligence_endpoint}")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ScriptToDoc API")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "ScriptToDoc API",
        "version": scripttodoc_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    settings = get_settings()
    
    # Check service connectivity (basic)
    services = {
        "cosmos_db": "unknown",
        "blob_storage": "unknown",
        "service_bus": "unknown",
        "azure_openai": "unknown",
        "azure_di": "unknown"
    }
    
    # TODO: Add actual health checks for each service
    # For now, just report configured
    if settings.azure_cosmos_endpoint:
        services["cosmos_db"] = "configured"
    if settings.azure_storage_account_name:
        services["blob_storage"] = "configured"
    if settings.azure_service_bus_connection_string:
        services["service_bus"] = "configured"
    if settings.azure_openai_endpoint:
        services["azure_openai"] = "configured"
    if settings.azure_document_intelligence_endpoint:
        services["azure_di"] = "configured"
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=scripttodoc_version,
        services=services
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            status_code=500
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

