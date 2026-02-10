"""
FastAPI dependencies for authentication, database connections, etc.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient

from script_to_doc.config import get_settings, Settings

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


def get_cosmos_client():
    """Get database client (SQLite in local mode, Cosmos DB otherwise)."""
    settings = get_settings()

    if settings.use_local_mode:
        # Local mode: Use SQLite database
        from script_to_doc.local_db import LocalDatabaseClient
        db_path = f"{settings.local_data_path}/scripttodoc.db"
        logger.info(f"Using local SQLite database: {db_path}")
        return LocalDatabaseClient(db_path)
    else:
        # Azure mode: Use Cosmos DB
        if settings.azure_cosmos_key:
            return CosmosClient(
                url=settings.azure_cosmos_endpoint,
                credential=settings.azure_cosmos_key
            )
        else:
            # Use Managed Identity
            from azure.identity import DefaultAzureCredential
            return CosmosClient(
                url=settings.azure_cosmos_endpoint,
                credential=DefaultAzureCredential()
            )


def get_blob_service_client():
    """Get storage client (filesystem in local mode, Blob Storage otherwise)."""
    settings = get_settings()

    if settings.use_local_mode:
        # Local mode: Use filesystem storage
        from script_to_doc.local_storage import LocalBlobServiceClient
        logger.info(f"Using local filesystem storage: {settings.local_data_path}")
        return LocalBlobServiceClient(settings.local_data_path)
    else:
        # Azure mode: Use Blob Storage
        if settings.azure_storage_connection_string:
            return BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        else:
            # Use Managed Identity
            from azure.identity import DefaultAzureCredential
            return BlobServiceClient(
                account_url=f"https://{settings.azure_storage_account_name}.blob.core.windows.net",
                credential=DefaultAzureCredential()
            )


def get_service_bus_client():
    """Get Service Bus client (None in local mode)."""
    settings = get_settings()

    if settings.use_local_mode:
        # Local mode: No message queue needed (use direct processing)
        logger.info("Local mode: Service Bus not needed (using direct processing)")
        return None
    else:
        # Azure mode: Use Service Bus
        return ServiceBusClient.from_connection_string(
            settings.azure_service_bus_connection_string
        )


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Verify authentication token (Azure AD).
    
    Returns:
        User ID if authenticated, None if no auth required (dev mode)
    """
    settings = get_settings()
    
    # In development, skip auth
    if settings.environment == "development":
        logger.warning("Development mode: Authentication bypassed")
        return "dev-user"
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # TODO: Implement proper Azure AD token validation
        # For now, accept any non-empty token in non-dev environments
        if token:
            return "authenticated-user"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


def get_current_user(user_id: str = Depends(verify_token)) -> str:
    """Get current authenticated user ID."""
    return user_id

