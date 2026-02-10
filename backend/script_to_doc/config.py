"""
Configuration management for ScriptToDoc.
Loads settings from environment variables with validation.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Local Mode Settings (NEW)
    use_local_mode: bool = Field(
        default=False,
        description="Use local mode (SQLite, filesystem, OpenAI) instead of Azure services"
    )
    local_data_path: str = Field(
        default="./data",
        description="Base path for local data storage (database, files)"
    )

    # Azure Document Intelligence (CHANGED: Optional for local mode)
    azure_document_intelligence_endpoint: Optional[str] = Field(
        None,
        description="Azure Document Intelligence endpoint URL"
    )
    azure_document_intelligence_key: Optional[str] = Field(
        None,
        description="API key (optional if using Managed Identity)"
    )

    # Azure OpenAI (CHANGED: Optional for local mode)
    azure_openai_endpoint: Optional[str] = Field(
        None,
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_key: Optional[str] = Field(
        None,
        description="API key (optional if using Managed Identity)"
    )
    azure_openai_deployment: str = Field(
        default="gpt-4o-mini",
        description="OpenAI deployment name"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description="API version"
    )

    # OpenAI (CHANGED: Required for local mode, fallback for Azure mode)
    openai_api_key: Optional[str] = Field(
        None,
        description="OpenAI API key (required for local mode, fallback for Azure mode)"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )

    # Azure Storage (CHANGED: Optional for local mode)
    azure_storage_account_name: Optional[str] = Field(
        None,
        description="Storage account name"
    )
    azure_storage_connection_string: Optional[str] = Field(
        None,
        description="Storage connection string"
    )
    azure_storage_container_uploads: str = Field(
        default="uploads",
        description="Upload container name"
    )
    azure_storage_container_documents: str = Field(
        default="documents",
        description="Documents container name"
    )
    azure_storage_container_temp: str = Field(
        default="temp",
        description="Temporary files container name"
    )

    # Azure Cosmos DB (CHANGED: Optional for local mode)
    azure_cosmos_endpoint: Optional[str] = Field(
        None,
        description="Cosmos DB endpoint URL"
    )
    azure_cosmos_key: Optional[str] = Field(
        None,
        description="Cosmos DB key (optional if using Managed Identity)"
    )
    azure_cosmos_database: str = Field(
        default="scripttodoc",
        description="Database name"
    )
    azure_cosmos_container_jobs: str = Field(
        default="jobs",
        description="Jobs container name"
    )

    # Azure Service Bus (CHANGED: Optional for local mode)
    azure_service_bus_connection_string: Optional[str] = Field(
        None,
        description="Service Bus connection string"
    )
    azure_service_bus_queue_name: str = Field(
        default="scripttodoc-jobs",
        description="Queue name for job processing"
    )

    # Application Settings
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    max_file_size_mb: int = Field(
        default=5,
        description="Maximum upload file size in MB"
    )
    use_direct_processing: bool = Field(
        default=True,
        description="Process jobs directly without Service Bus (for development/testing)"
    )
    
    # Application Insights (Optional)
    applicationinsights_connection_string: Optional[str] = Field(
        None,
        description="Application Insights connection string"
    )

    # Azure AI Foundry (Optional - for advanced scenarios)
    azure_ai_foundry_endpoint: Optional[str] = Field(
        None,
        description="Azure AI Foundry endpoint URL (optional)"
    )

    # Bing Search (Optional - for knowledge grounding)
    bing_connection_name: Optional[str] = Field(
        None,
        description="Bing Search connection name (optional)"
    )


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global settings
    if settings is None:
        # Check for ENV_FILE environment variable
        env_file = os.environ.get('ENV_FILE', '.env')
        settings = Settings(_env_file=env_file)
    return settings


def init_settings(env_file: str = ".env") -> Settings:
    """Initialize settings from specific env file."""
    global settings
    settings = Settings(_env_file=env_file)
    return settings

