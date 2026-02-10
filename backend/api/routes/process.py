"""
Process transcript endpoints.
"""

import logging
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from azure.servicebus import ServiceBusMessage

from script_to_doc.config import get_settings
from ..models import ProcessRequest, ProcessResponse, JobStatus, ProcessingStage
from ..dependencies import (
    get_cosmos_client,
    get_blob_service_client,
    get_service_bus_client,
    get_current_user
)
from ..file_utils import process_uploaded_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
async def process_transcript(
    file: UploadFile = File(..., description="Transcript file (.txt or .pdf)"),
    tone: str = Form("Professional"),
    audience: str = Form("Technical Users"),
    # ⚠️ Phase 1: Step count auto-detected via topic segmentation (parameters kept for backward compatibility)
    min_steps: int = Form(3),
    target_steps: int = Form(None),  # Optional - Phase 1 auto-detects optimal count
    max_steps: int = Form(15),
    document_title: str = Form(None),
    include_statistics: bool = Form(True),
    knowledge_urls: str = Form(None, description="JSON array of knowledge source URLs"),
    user_id: str = Depends(get_current_user)
):
    """
    Upload transcript and start processing.
    
    **Supported File Types:**
    - .txt: Plain text files
    - .pdf: PDF documents (text will be extracted)
    
    **Process:**
    1. Validate and extract text from file
    2. Upload to Blob Storage
    3. Create job record in Cosmos DB
    4. Send message to Service Bus queue
    5. Return job ID
    
    **Returns:**
        Job ID and status
    """
    settings = get_settings()
    
    # Read file content
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    # Check file size
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {file_size_mb:.2f} MB (max: {settings.max_file_size_mb} MB)"
        )
    
    # Process file and extract text
    try:
        extracted_text, file_type = process_uploaded_file(file.filename, content)
        logger.info(f"Extracted {len(extracted_text)} characters from {file_type} file")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    logger.info(f"Processing transcript upload for job {job_id}, user {user_id}, file_type: {file_type}")
    
    try:
        # Upload extracted text to Blob Storage (always as .txt for processing)
        blob_service = get_blob_service_client()
        
        # Ensure container exists
        container_client = blob_service.get_container_client(settings.azure_storage_container_uploads)
        try:
            if not container_client.exists():
                logger.info(f"Creating container: {settings.azure_storage_container_uploads}")
                container_client.create_container()
        except Exception as container_error:
            logger.warning(f"Container check/create failed (may already exist): {container_error}")
        
        blob_client = blob_service.get_blob_client(
            container=settings.azure_storage_container_uploads,
            blob=f"{job_id}/transcript.txt"
        )
        
        # Store extracted text as UTF-8
        blob_client.upload_blob(extracted_text.encode('utf-8'), overwrite=True)
        transcript_url = blob_client.url
        
        logger.info(f"Uploaded transcript to: {transcript_url}")
        
        # Create job record in Cosmos DB
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)
        
        # Parse knowledge URLs if provided
        knowledge_urls_list = []
        if knowledge_urls:
            try:
                knowledge_urls_list = json.loads(knowledge_urls)
                if not isinstance(knowledge_urls_list, list):
                    knowledge_urls_list = []
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid knowledge_urls JSON, ignoring: {knowledge_urls}")
                knowledge_urls_list = []

        job_record = {
            "id": job_id,
            "user_id": user_id,
            "status": JobStatus.QUEUED.value,
            "progress": 0.0,
            "stage": ProcessingStage.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "config": {
                "tone": tone,
                "audience": audience,
                "min_steps": min_steps,
                "target_steps": target_steps if target_steps is not None else 8,  # Fallback for legacy compatibility
                "max_steps": max_steps,
                "document_title": document_title or file.filename.rsplit('.', 1)[0],
                "include_statistics": include_statistics,
                "knowledge_urls": knowledge_urls_list
            },
            "input": {
                "filename": file.filename,
                "file_type": file_type,
                "transcript_url": transcript_url,
                "file_size_mb": file_size_mb,
                "original_file_size_mb": file_size_mb,
                "extracted_text_length": len(extracted_text)
            },
            "result": None,
            "error": None
            # ⚠️ DO NOT set "total_steps" here - it will be determined by Phase 1 topic segmentation
        }
        
        container.create_item(body=job_record)
        
        logger.info(f"Created job record in Cosmos DB: {job_id}")
        
        # Check if direct processing is enabled (for development/testing)
        if settings.use_direct_processing:
            logger.info(f"Direct processing enabled, processing job immediately: {job_id}")
            try:
                import threading
                from ..background_processor import process_job_direct
                
                # Process in background thread
                thread = threading.Thread(
                    target=process_job_direct,
                    args=(job_id, user_id, transcript_url, job_record["config"])
                )
                thread.daemon = True
                thread.start()
                
                logger.info(f"Started direct processing in background: {job_id}")
                
                return ProcessResponse(
                    job_id=job_id,
                    status=JobStatus.PROCESSING,
                    message="Processing directly (development mode)"
                )
                
            except Exception as process_error:
                logger.error(f"Failed to start direct processing: {process_error}", exc_info=True)
                # Fall back to Service Bus if direct processing fails
                pass
        
        # Try to send message to Service Bus
        try:
            sb_client = get_service_bus_client()
            sender = sb_client.get_queue_sender(queue_name=settings.azure_service_bus_queue_name)
            
            message = ServiceBusMessage(
                body=json.dumps({
                    "job_id": job_id,
                    "user_id": user_id,
                    "transcript_url": transcript_url,
                    "config": job_record["config"]
                }),
                content_type="application/json",
                message_id=job_id
            )
            
            with sender:
                sender.send_messages(message)
            
            logger.info(f"Sent job to Service Bus queue: {job_id}")
            
            return ProcessResponse(
                job_id=job_id,
                status=JobStatus.QUEUED,
                message="Job queued for processing"
            )
            
        except Exception as sb_error:
            logger.warning(f"Service Bus not available, processing directly: {sb_error}")
            
            # Fall back to direct processing for MVP testing
            try:
                import threading
                from ..background_processor import process_job_direct
                
                # Process in background thread
                thread = threading.Thread(
                    target=process_job_direct,
                    args=(job_id, user_id, transcript_url, job_record["config"])
                )
                thread.daemon = True
                thread.start()
                
                logger.info(f"Started direct processing in background: {job_id}")
                
                return ProcessResponse(
                    job_id=job_id,
                    status=JobStatus.PROCESSING,
                    message="Processing directly (Service Bus unavailable)"
                )
                
            except Exception as process_error:
                logger.error(f"Failed to start direct processing: {process_error}", exc_info=True)
                # Return queued status anyway - manual processing can be done
                return ProcessResponse(
                    job_id=job_id,
                    status=JobStatus.QUEUED,
                    message="Job created (processing requires Service Bus setup or worker process)"
                )
        
    except Exception as e:
        logger.error(f"Failed to process upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue job: {str(e)}"
        )


@router.post("/generate-title")
async def generate_document_title(
    text: str = Form(..., description="Transcript text to analyze"),
    user_id: str = Depends(get_current_user)
):
    """
    Generate a document title from transcript text using AI.

    Analyzes the transcript content and suggests an appropriate title.

    **Args:**
        text: The transcript text to analyze

    **Returns:**
        JSON with suggested title
    """
    from script_to_doc.azure_openai_client import AzureOpenAIClient

    settings = get_settings()

    # Validate input
    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is too short (minimum 50 characters)"
        )

    try:
        logger.info(f"Generating title for text length: {len(text)} chars")

        # Initialize Azure OpenAI client with better error handling
        try:
            client = AzureOpenAIClient(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                deployment=settings.azure_openai_deployment,
                api_version=settings.azure_openai_api_version,
                openai_api_key=settings.openai_api_key,
                openai_model=settings.openai_model
            )
        except ValueError as ve:
            logger.error(f"Failed to initialize OpenAI client: {ve}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service configuration error: {str(ve)}"
            )

        # Build prompt for title generation
        prompt = f"""Analyze the following transcript and generate a concise, professional document title.

The title should:
- Be 3-7 words long
- Describe the main topic or process being taught
- Be professional and clear
- Use title case (capitalize main words)
- NOT include phrases like "Guide to", "How to", "Training on" - just state the topic

Examples:
- Good: "Azure Resource Group Deployment"
- Good: "GitHub Encrypted Secrets Configuration"
- Good: "Database Query Optimization Techniques"
- Bad: "How to Deploy Azure Resources" (too long, includes "How to")
- Bad: "Training Session Notes" (too generic)

Transcript (first 2000 chars):
{text[:2000]}

Generate ONLY the title, nothing else. No quotes, no explanation, just the title."""

        # Use deployment/model name
        model_name = client.openai_model if client.use_fallback else client.deployment
        logger.info(f"Using model: {model_name} (fallback: {client.use_fallback})")

        # Generate title with error handling
        try:
            response = client.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional technical writer specializing in creating clear, concise document titles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50,
                timeout=15.0
            )

            title = response.choices[0].message.content.strip()

            # Remove any quotes that might have been added
            title = title.strip('"').strip("'")

            logger.info(f"Generated title: {title}")

            return {"title": title}

        except Exception as api_error:
            error_str = str(api_error).lower()

            # Handle rate limits
            if 'rate limit' in error_str or '429' in error_str:
                logger.warning(f"Rate limit exceeded: {api_error}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="AI service rate limit exceeded. Please try again in a moment."
                )

            # Handle deployment not found
            if 'deploymentnotfound' in error_str or '404' in error_str:
                logger.error(f"Deployment not found: {api_error}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"AI deployment '{settings.azure_openai_deployment}' not found. Please contact administrator."
                )

            # Handle authentication errors
            if 'unauthorized' in error_str or '401' in error_str:
                logger.error(f"Authentication failed: {api_error}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service authentication failed. Please contact administrator."
                )

            # Generic API error
            logger.error(f"OpenAI API error: {api_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service error: {str(api_error)}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating title: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate title: {str(e)}"
        )


@router.post("/process-with-screenshots", response_model=ProcessResponse)
async def process_transcript_with_screenshots(
    transcript: UploadFile = File(..., description="Transcript file (.txt)"),
    screenshots: list[UploadFile] = File(..., description="Screenshot files"),
    tone: str = Form("Professional"),
    audience: str = Form("Technical Users"),
    target_steps: int = Form(8),
    user_id: str = Depends(get_current_user)
):
    """
    Upload transcript with screenshots and start processing.

    This endpoint is for Phase 2 with screenshot support.

    **Note:** Currently not fully implemented (Phase 2 feature).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Screenshot support coming in Phase 2"
    )

