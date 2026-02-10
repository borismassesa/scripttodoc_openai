"""
Direct background processor for MVP testing (when Service Bus is not available).
"""

import logging
from datetime import datetime
from io import BytesIO

from script_to_doc.config import get_settings
from script_to_doc.pipeline import process_transcript, PipelineConfig
from .dependencies import get_cosmos_client, get_blob_service_client

logger = logging.getLogger(__name__)


def process_job_direct(job_id: str, user_id: str, transcript_url: str, config: dict):
    """
    Process a job directly without Service Bus.
    
    This function is designed to run in a background thread for MVP testing.
    """
    settings = get_settings()
    
    try:
        logger.info(f"Starting direct processing for job {job_id}")
        
        # Update job status to processing
        update_job_status(job_id, user_id, "processing", 0.1, "load_transcript")
        
        # Download transcript from blob storage or local filesystem
        logger.info(f"Loading transcript from: {transcript_url}")
        blob_service = get_blob_service_client()

        # CHANGED: Handle file:// URLs for local mode
        if transcript_url.startswith("file://"):
            # Local file mode
            file_path = transcript_url.replace("file://", "")
            logger.info(f"Reading local file: {file_path}")
            with open(file_path, 'rb') as f:
                transcript_content = f.read().decode('utf-8')
        else:
            # Blob storage mode
            # Extract blob path from URL
            blob_path = transcript_url.split(f"/{settings.azure_storage_container_uploads}/")[1]
            blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_uploads,
                blob=blob_path
            )
            transcript_content = blob_client.download_blob().readall().decode('utf-8')

        logger.info(f"Loaded {len(transcript_content)} characters")
        
        update_job_status(job_id, user_id, "processing", 0.2, "clean_transcript")
        
        # Configure pipeline
        # ⭐ Phase 1 ENABLED: Intelligent topic-based segmentation for higher quality
        # CHANGED: Support local mode with OpenAI-only processing
        pipeline_config = PipelineConfig(
            use_local_mode=settings.use_local_mode,
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            azure_di_endpoint=settings.azure_document_intelligence_endpoint,
            azure_di_key=settings.azure_document_intelligence_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_key=settings.azure_openai_key,
            azure_openai_deployment=settings.azure_openai_deployment,
            use_azure_di=not settings.use_local_mode,  # Disable Azure DI in local mode
            tone=config.get("tone", "Professional"),
            audience=config.get("audience", "Technical Users"),
            min_steps=config.get("min_steps", 5),  # CHANGED: Minimum 5 steps for better quality
            target_steps=config.get("target_steps", 10),  # CHANGED: Target 10 steps
            max_steps=config.get("max_steps", 20),  # CHANGED: Allow up to 20 steps
            document_title=config.get("document_title", "Training Document"),
            include_statistics=config.get("include_statistics", True),
            knowledge_urls=config.get("knowledge_urls", []),
            # ✅ Phase 1 ENABLED: Auto-detect optimal step count based on conversation flow
            use_intelligent_parsing=True,
            use_topic_segmentation=True
        )

        logger.info(f"Pipeline configured with Phase 1 enabled (intelligent topic segmentation), "
                   f"min_steps={pipeline_config.min_steps}, max_steps={pipeline_config.max_steps}")
        
        # Process transcript
        logger.info(f"Processing transcript with pipeline...")
        
        # Create temporary output directory
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "training_document.docx")
        
        try:
            # Process transcript directly (function takes text, not file path)
            # Define progress callback that accepts all metadata parameters
            def progress_update(progress, stage, current_step=None, total_steps=None, stage_detail=None):
                update_job_status(
                    job_id, user_id, "processing", progress, stage,
                    current_step=current_step,
                    total_steps=total_steps,
                    stage_detail=stage_detail
                )

            result = process_transcript(
                transcript_text=transcript_content,
                output_path=output_path,
                config=pipeline_config,
                progress_callback=progress_update
            )
            
            # Check if pipeline succeeded
            if not result.success:
                error_msg = result.error or "Pipeline processing failed"
                logger.error(f"Pipeline failed for job {job_id}: {error_msg}")
                raise Exception(error_msg)
            
            # Check if document was created
            if not result.document_path:
                error_msg = "Pipeline completed but no document was generated"
                logger.error(f"Job {job_id}: {error_msg}")
                raise Exception(error_msg)
            
            document_path = result.document_path
            
            if not os.path.exists(document_path):
                error_msg = f"Document file not found at {document_path}"
                logger.error(f"Job {job_id}: {error_msg}")
                raise FileNotFoundError(error_msg)
            
            update_job_status(job_id, user_id, "processing", 0.9, "upload_document")
            
            with open(document_path, 'rb') as doc_file:
                doc_content = doc_file.read()
            
            # Upload to documents container
            doc_blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_documents,
                blob=f"{job_id}/training_document.docx"
            )
            doc_blob_client.upload_blob(doc_content, overwrite=True)
            document_url = doc_blob_client.url
            
            logger.info(f"Uploaded document to: {document_url}")
            
            # Clean up temporary files
            if os.path.exists(document_path):
                os.unlink(document_path)
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass  # Directory may not be empty
            
            # Update job with results
            steps = result.steps or []
            metrics = result.metrics or {}

            # Extract token usage for frontend (flatten the nested structure)
            token_usage = metrics.get("token_usage", {})

            result_data = {
                "document_url": document_url,
                "document_blob_path": f"{job_id}/training_document.docx",
                "filename": f"{config.get('document_title', 'training_document')}.docx",
                "steps_count": len(steps),
                "metrics": {
                    "total_steps": len(steps),
                    "average_confidence": metrics.get("average_confidence", 0.0),
                    "high_confidence_steps": metrics.get("high_confidence_steps", 0),
                    "processing_time": metrics.get("processing_time_seconds", result.processing_time),
                    "transcript_word_count": metrics.get("transcript_word_count", 0),
                    "transcript_sentence_count": metrics.get("transcript_sentence_count", 0),
                    # Flatten token usage for frontend
                    "input_tokens": token_usage.get("input_tokens", 0),
                    "output_tokens": token_usage.get("output_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0),
                    "knowledge_sources_fetched": metrics.get("knowledge_sources_fetched", 0),
                    "knowledge_sources_cited": metrics.get("knowledge_sources_cited", 0),
                    "knowledge_usage_rate": metrics.get("knowledge_usage_rate", 0.0)
                },
                "knowledge_sources_used": result.knowledge_sources_used or []
            }
            
            update_job_status(
                job_id, user_id, "completed", 1.0, "complete",
                result=result_data
            )
            
            logger.info(f"Job {job_id} completed successfully")
            
        finally:
            # Clean up temp directory if it still exists
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    pass
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id, user_id, "failed", 0.0, "error",
            error=str(e)
        )


def update_job_status(
    job_id: str,
    user_id: str,
    status: str,
    progress: float,
    stage: str,
    result: dict = None,
    error: str = None,
    current_step: int = None,
    total_steps: int = None,
    stage_detail: str = None
):
    """Update job status in Cosmos DB."""
    try:
        settings = get_settings()
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)

        # Read current job
        job = container.read_item(item=job_id, partition_key=user_id)

        # Update fields
        job["status"] = status
        job["progress"] = progress
        job["stage"] = stage
        job["updated_at"] = datetime.utcnow().isoformat()

        # Update optional metadata fields
        if current_step is not None:
            job["current_step"] = current_step
        if total_steps is not None:
            job["total_steps"] = total_steps
        if stage_detail is not None:
            job["stage_detail"] = stage_detail

        if result is not None:
            job["result"] = result

        if error is not None:
            job["error"] = error

        # Upsert
        container.upsert_item(body=job)

        # Enhanced logging
        log_msg = f"Updated job {job_id} status: {status} ({progress:.0%}) - {stage}"
        if stage_detail:
            log_msg += f" | {stage_detail}"
        logger.info(log_msg)

    except Exception as e:
        logger.error(f"Failed to update job status: {e}")

