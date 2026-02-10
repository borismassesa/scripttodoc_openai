"""
Background worker for processing transcript jobs.
Listens to Azure Service Bus queue and processes jobs asynchronously.
"""

import logging
import json
import sys
import time
import tempfile
from datetime import datetime
from pathlib import Path
from azure.servicebus import ServiceBusClient, ServiceBusReceiver
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient

from script_to_doc.config import get_settings, init_settings
from script_to_doc.pipeline import process_transcript, PipelineConfig
from api.models import JobStatus, ProcessingStage

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


class JobProcessor:
    """Process jobs from Service Bus queue."""
    
    def __init__(self):
        """Initialize processor with Azure clients."""
        self.settings = get_settings()
        
        # Initialize clients
        self.sb_client = ServiceBusClient.from_connection_string(
            self.settings.azure_service_bus_connection_string
        )
        
        if self.settings.azure_cosmos_key:
            self.cosmos_client = CosmosClient(
                url=self.settings.azure_cosmos_endpoint,
                credential=self.settings.azure_cosmos_key
            )
        else:
            from azure.identity import DefaultAzureCredential
            self.cosmos_client = CosmosClient(
                url=self.settings.azure_cosmos_endpoint,
                credential=DefaultAzureCredential()
            )
        
        if self.settings.azure_storage_connection_string:
            self.blob_service = BlobServiceClient.from_connection_string(
                self.settings.azure_storage_connection_string
            )
        else:
            from azure.identity import DefaultAzureCredential
            self.blob_service = BlobServiceClient(
                account_url=f"https://{self.settings.azure_storage_account_name}.blob.core.windows.net",
                credential=DefaultAzureCredential()
            )
        
        # Get Cosmos DB container
        database = self.cosmos_client.get_database_client(
            self.settings.azure_cosmos_database
        )
        self.jobs_container = database.get_container_client(
            self.settings.azure_cosmos_container_jobs
        )
        
        logger.info("Job processor initialized")
    
    def update_job_status(
        self,
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
            # Try to read current job
            try:
                job = self.jobs_container.read_item(item=job_id, partition_key=user_id)
            except Exception as read_error:
                # If job doesn't exist, log warning but continue
                # This can happen if the job was created but not yet replicated
                logger.warning(f"Job {job_id} not found in Cosmos DB, creating new record: {read_error}")
                job = {
                    "id": job_id,
                    "user_id": user_id,
                    "status": status,
                    "progress": progress,
                    "stage": stage,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "config": {},
                    "result": result,
                    "error": error
                }

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

            # Use upsert to handle both create and update
            self.jobs_container.upsert_item(body=job)

            # Enhanced logging with metadata
            log_msg = f"Job {job_id}: status={status}, progress={progress:.2f}, stage={stage}"
            if stage_detail:
                log_msg += f", detail={stage_detail}"
            logger.info(log_msg)

        except Exception as e:
            logger.error(f"Failed to update job status: {e}", exc_info=True)
    
    def download_blob(self, blob_url: str) -> bytes:
        """Download blob content from URL."""
        # Extract container and blob name from URL
        # URL format: https://<account>.blob.core.windows.net/<container>/<path>/<filename>
        # Example: https://scripttodocstorage.blob.core.windows.net/uploads/job-id/transcript.txt
        from urllib.parse import urlparse
        
        parsed = urlparse(blob_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid blob URL format: {blob_url}")
        
        container_name = path_parts[0]  # First part is container
        blob_name = '/'.join(path_parts[1:])  # Rest is the blob path
        
        # Ensure container exists
        try:
            container_client = self.blob_service.get_container_client(container_name)
            if not container_client.exists():
                logger.warning(f"Container {container_name} does not exist, creating it...")
                container_client.create_container()
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise
        
        blob_client = self.blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        return blob_client.download_blob().readall()
    
    def upload_document(self, job_id: str, document_path: str) -> str:
        """Upload generated document to Blob Storage."""
        # Ensure container exists
        container_name = self.settings.azure_storage_container_documents
        try:
            container_client = self.blob_service.get_container_client(container_name)
            if not container_client.exists():
                logger.warning(f"Container {container_name} does not exist, creating it...")
                container_client.create_container()
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise
        
        # Generate blob path
        blob_name = f"{job_id}/training_document.docx"
        
        blob_client = self.blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Upload document
        with open(document_path, 'rb') as f:
            blob_client.upload_blob(f, overwrite=True)
        
        logger.info(f"Uploaded document to: {blob_name}")
        
        return blob_name
    
    def process_job(self, message_body: dict):
        """Process a single job from Service Bus message."""
        job_id = message_body["job_id"]
        user_id = message_body["user_id"]
        transcript_url = message_body["transcript_url"]
        config = message_body["config"]
        
        logger.info(f"Processing job {job_id} for user {user_id}")
        
        try:
            # Update status to processing
            self.update_job_status(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.PROCESSING.value,
                progress=0.05,
                stage=ProcessingStage.LOAD_TRANSCRIPT.value
            )
            
            # Download transcript from blob
            logger.info(f"Downloading transcript from: {transcript_url}")
            try:
                transcript_bytes = self.download_blob(transcript_url)
                transcript_text = transcript_bytes.decode('utf-8')
            except Exception as blob_error:
                error_msg = f"Failed to download transcript from blob storage: {str(blob_error)}"
                logger.error(error_msg)
                self.update_job_status(
                    job_id=job_id,
                    user_id=user_id,
                    status=JobStatus.FAILED.value,
                    progress=0.0,
                    stage=ProcessingStage.ERROR.value,
                    error=error_msg
                )
                raise
            
            # Create progress callback
            def progress_callback(
                progress: float,
                stage: str,
                current_step: int = None,
                total_steps: int = None,
                stage_detail: str = None
            ):
                # Determine status based on stage
                # If stage is 'complete', mark job as completed
                if stage == ProcessingStage.COMPLETE.value:
                    job_status = JobStatus.COMPLETED.value
                elif stage == ProcessingStage.ERROR.value:
                    job_status = JobStatus.FAILED.value
                else:
                    job_status = JobStatus.PROCESSING.value

                self.update_job_status(
                    job_id=job_id,
                    user_id=user_id,
                    status=job_status,
                    progress=progress,
                    stage=stage,
                    current_step=current_step,
                    total_steps=total_steps,
                    stage_detail=stage_detail
                )

            # Create temporary output file
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = str(Path(temp_dir) / "training_document.docx")
                
                # Create pipeline config
                pipeline_config = PipelineConfig(
                    azure_di_endpoint=self.settings.azure_document_intelligence_endpoint,
                    azure_di_key=self.settings.azure_document_intelligence_key,
                    azure_openai_endpoint=self.settings.azure_openai_endpoint,
                    azure_openai_key=self.settings.azure_openai_key,
                    azure_openai_deployment=self.settings.azure_openai_deployment,
                    openai_api_key=self.settings.openai_api_key,
                    openai_model=self.settings.openai_model,
                    min_steps=config.get("min_steps", 3),
                    target_steps=config.get("target_steps", 8),
                    max_steps=config.get("max_steps", 15),
                    tone=config.get("tone", "Professional"),
                    audience=config.get("audience", "Technical Users"),
                    document_title=config.get("document_title", "Training Document"),
                    include_statistics=config.get("include_statistics", True),
                    knowledge_urls=config.get("knowledge_urls", [])
                )
                
                # Run pipeline with progress tracking
                logger.info("Starting processing pipeline")
                import time as time_module
                start_time = time_module.time()
                
                # Update progress at each stage
                self.update_job_status(job_id, user_id, JobStatus.PROCESSING.value, 0.2, ProcessingStage.CLEAN_TRANSCRIPT.value)
                
                # Call process_transcript with correct parameters: text content, output path, config
                result = process_transcript(
                    transcript_text=transcript_text,
                    output_path=output_path,
                    config=pipeline_config,
                    progress_callback=progress_callback
                )
                
                processing_time = time_module.time() - start_time
                
                # Upload document (only if pipeline succeeded and document exists)
                if not result.success or not result.document_path:
                    error_msg = result.error or "Pipeline failed without generating document"
                    logger.error(f"Job {job_id} pipeline failed: {error_msg}")
                    raise Exception(error_msg)
                
                self.update_job_status(
                    job_id=job_id,
                    user_id=user_id,
                    status=JobStatus.PROCESSING.value,
                    progress=0.95,
                    stage=ProcessingStage.UPLOAD_DOCUMENT.value
                )
                
                document_blob_path = self.upload_document(job_id, result.document_path)

                # Prepare metrics safely
                steps = result.steps or []
                metrics = result.metrics or {}

                # Add result data (status already set to 'completed' by progress callback)
                result_data = {
                    "document_blob_path": document_blob_path,
                    "filename": f"{config.get('document_title', 'training_document')}.docx",
                    "steps_count": len(steps),
                    "metrics": {
                        "total_steps": len(steps),
                        "average_confidence": metrics.get("average_confidence", 0.0),
                        "high_confidence_steps": metrics.get("high_confidence_steps", 0),
                        "processing_time": metrics.get("processing_time_seconds", processing_time),
                        "transcript_word_count": metrics.get("transcript_word_count", 0),
                        "transcript_sentence_count": metrics.get("transcript_sentence_count", 0),
                        "token_usage": metrics.get("token_usage", {})
                    }
                }

                # Final update with result data
                self.update_job_status(
                    job_id=job_id,
                    user_id=user_id,
                    status=JobStatus.COMPLETED.value,
                    progress=1.0,
                    stage=ProcessingStage.COMPLETE.value,
                    result=result_data
                )
                
                logger.info(
                    f"Job {job_id} completed successfully in {processing_time:.2f}s"
                )
                
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            
            self.update_job_status(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.FAILED.value,
                progress=0.0,
                stage=ProcessingStage.ERROR.value,
                error=str(e)
            )
            
            raise
    
    def run(self):
        """Main worker loop - listen to Service Bus queue."""
        logger.info(
            f"Starting worker - listening to queue: "
            f"{self.settings.azure_service_bus_queue_name}"
        )
        
        receiver: ServiceBusReceiver = self.sb_client.get_queue_receiver(
            queue_name=self.settings.azure_service_bus_queue_name,
            max_wait_time=30  # Wait up to 30 seconds for messages
        )
        
        with receiver:
            while True:
                try:
                    # Receive messages
                    received_msgs = receiver.receive_messages(
                        max_message_count=1,
                        max_wait_time=30
                    )
                    
                    for message in received_msgs:
                        try:
                            # Parse message body safely (Service Bus messages return iterable body segments)
                            body_segments = []
                            for segment in message.body:
                                if isinstance(segment, bytes):
                                    body_segments.append(segment)
                                elif isinstance(segment, memoryview):
                                    body_segments.append(segment.tobytes())
                                else:
                                    body_segments.append(str(segment).encode("utf-8"))

                            body_bytes = b"".join(body_segments)
                            message_body = json.loads(body_bytes.decode("utf-8"))
                            logger.info(f"Received message: {message.message_id}")
                            
                            # Process job
                            self.process_job(message_body)
                            
                            # Complete message (remove from queue)
                            receiver.complete_message(message)
                            logger.info(f"Message completed: {message.message_id}")
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse message: {e}")
                            # Dead-letter invalid messages
                            receiver.dead_letter_message(
                                message,
                                reason="Invalid JSON",
                                error_description=str(e)
                            )
                            
                        except Exception as e:
                            logger.error(f"Failed to process message: {e}", exc_info=True)
                            # Abandon message (will be retried)
                            receiver.abandon_message(message)
                    
                    # Short sleep if no messages
                    if not received_msgs:
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    logger.info("Received shutdown signal")
                    break
                    
                except Exception as e:
                    logger.error(f"Worker error: {e}", exc_info=True)
                    time.sleep(5)  # Wait before retrying
        
        logger.info("Worker stopped")


def main():
    """Main entry point for worker."""
    logger.info("Starting ScriptToDoc Background Worker")
    
    # Initialize settings
    try:
        init_settings()
    except Exception as e:
        logger.error(f"Failed to initialize settings: {e}")
        sys.exit(1)
    
    # Create and run processor
    try:
        processor = JobProcessor()
        processor.run()
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

