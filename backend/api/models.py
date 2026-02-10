"""
Pydantic models for API request/response validation.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentFormat(str, Enum):
    """Supported document export formats."""
    DOCX = "docx"
    PDF = "pdf"
    PPTX = "pptx"


class JobStatus(str, Enum):
    """Job processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStage(str, Enum):
    """Current processing stage."""
    PENDING = "pending"
    LOAD_TRANSCRIPT = "load_transcript"
    CLEAN_TRANSCRIPT = "clean_transcript"
    FETCH_KNOWLEDGE = "fetch_knowledge"  # NEW: Knowledge URL fetching stage
    AZURE_DI_ANALYSIS = "azure_di_analysis"
    DETERMINE_STEPS = "determine_steps"
    GENERATE_STEPS = "generate_steps"
    BUILD_SOURCES = "build_sources"
    VALIDATE_STEPS = "validate_steps"
    CREATE_DOCUMENT = "create_document"
    UPLOAD_DOCUMENT = "upload_document"
    COMPLETE = "complete"
    ERROR = "error"


class ProcessRequest(BaseModel):
    """Request to process a transcript."""
    tone: str = Field(default="Professional", description="Document tone")
    audience: str = Field(default="Technical Users", description="Target audience")
    min_steps: int = Field(default=3, ge=1, le=20, description="Minimum number of steps")
    target_steps: int = Field(default=8, ge=1, le=20, description="Target number of steps")
    max_steps: int = Field(default=15, ge=1, le=20, description="Maximum number of steps")
    document_title: Optional[str] = Field(None, description="Custom document title")
    include_statistics: bool = Field(default=True, description="Include statistics page")


class ProcessResponse(BaseModel):
    """Response after initiating processing."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current status")
    message: str = Field(default="Job queued for processing")


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    stage: ProcessingStage
    current_step: Optional[int] = Field(None, description="Current step being processed (e.g., 3 when generating step 3)")
    total_steps: Optional[int] = Field(None, description="Total number of steps to process")
    stage_detail: Optional[str] = Field(None, description="Human-readable detail about current stage (e.g., 'Generating step 3 of 6')")
    created_at: datetime
    updated_at: datetime
    config: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class DocumentDownloadResponse(BaseModel):
    """Response with document download information."""
    download_url: str = Field(..., description="SAS URL for document download")
    expires_in: int = Field(..., description="URL expiry time in seconds")
    filename: str = Field(..., description="Document filename")
    format: DocumentFormat = Field(..., description="Document format")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    timestamp: datetime
    version: str
    services: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int

