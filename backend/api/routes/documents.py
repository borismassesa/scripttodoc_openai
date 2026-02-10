"""
Document download endpoints.
"""

import logging
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from script_to_doc.config import get_settings
from script_to_doc.converters import get_conversion_service, ConversionError
from script_to_doc.converters.conversion_service import DocumentFormat as ConverterDocumentFormat
from ..models import DocumentDownloadResponse, JobStatus, DocumentFormat
from ..dependencies import (
    get_cosmos_client,
    get_blob_service_client,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/documents/{job_id}")
async def get_document_download_url(
    job_id: str,
    format: DocumentFormat = Query(DocumentFormat.DOCX, description="Document format (docx, pdf, pptx)"),
    download: bool = Query(False, description="Return file directly instead of URL"),
    user_id: str = Depends(get_current_user)
):
    """
    Get download URL for generated document in specified format.

    **Process:**
    1. Verify job is completed
    2. Convert document to requested format (if not DOCX)
    3. Generate SAS token for blob access (1 hour expiry)
    4. Return temporary download URL

    **Supported Formats:**
    - docx: Microsoft Word (native format, no conversion)
    - pdf: PDF document (converted from DOCX)
    - pptx: PowerPoint presentation (converted from DOCX)

    **Returns:**
        Temporary download URL with expiration time
    """
    settings = get_settings()
    
    try:
        # Get job status from Cosmos DB
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)
        
        job = container.read_item(item=job_id, partition_key=user_id)
        
        # Check if job is completed
        if job["status"] != JobStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document not ready. Current status: {job['status']}"
            )
        
        # Get document path from result
        if not job.get("result") or not job["result"].get("document_blob_path"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document path not found in job result"
            )

        base_document_path = job["result"]["document_blob_path"]
        base_filename = job["result"].get("filename", "training_document.docx")

        # Get blob service
        blob_service = get_blob_service_client()

        # Handle format conversion
        if format != DocumentFormat.DOCX:
            try:
                logger.info(f"Converting document to {format.value} for job {job_id}")

                # Download base DOCX from blob
                blob_client_base = blob_service.get_blob_client(
                    container=settings.azure_storage_container_documents,
                    blob=base_document_path
                )

                # Use temporary directory for conversion
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_input = Path(temp_dir) / "input.docx"
                    temp_output = Path(temp_dir) / f"output.{format.value}"

                    # Download DOCX
                    logger.info(f"Downloading base DOCX from blob: {base_document_path}")
                    with open(temp_input, "wb") as f:
                        f.write(blob_client_base.download_blob().readall())

                    # Convert to desired format
                    conversion_service = get_conversion_service()
                    converter_format = ConverterDocumentFormat(format.value)
                    converted_path = conversion_service.convert_document(
                        input_path=temp_input,
                        output_format=converter_format,
                        output_path=temp_output
                    )

                    # Upload converted document
                    converted_blob_path = base_document_path.replace('.docx', f'.{format.value}')
                    blob_client_converted = blob_service.get_blob_client(
                        container=settings.azure_storage_container_documents,
                        blob=converted_blob_path
                    )

                    logger.info(f"Uploading converted document to blob: {converted_blob_path}")
                    with open(converted_path, "rb") as f:
                        blob_client_converted.upload_blob(f, overwrite=True)

                    # Use converted document for download
                    document_blob_path = converted_blob_path
                    filename = base_filename.replace('.docx', f'.{format.value}')
                    blob_client = blob_client_converted

                    logger.info(f"Successfully converted document to {format.value} for job {job_id}")

            except ConversionError as e:
                logger.error(f"Conversion failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document conversion failed: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Conversion error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to convert document format"
                )
        else:
            # No conversion needed for DOCX
            document_blob_path = base_document_path
            filename = base_filename
            blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_documents,
                blob=document_blob_path
            )
        
        # LOCAL MODE: Handle file serving
        if settings.use_local_mode:
            logger.info(f"Local mode: Handling document for job {job_id}")

            # Get the file path from blob_client.url (file:// URL)
            file_url = blob_client.url
            if file_url.startswith('file://'):
                file_path = file_url.replace('file://', '')
                file_path = Path(file_path)

                if not file_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Document file not found: {file_path}"
                    )

                # If download=true, serve file directly
                if download:
                    logger.info(f"Serving file directly: {file_path}")
                    return FileResponse(
                        path=str(file_path),
                        filename=filename,
                        media_type='application/octet-stream'
                    )

                # Otherwise, return API URL for download
                download_url = f"/api/documents/{job_id}?format={format.value}&download=true"
                logger.info(f"Returning local download URL: {download_url}")
                return DocumentDownloadResponse(
                    download_url=download_url,
                    expires_in=3600,
                    filename=filename,
                    format=format
                )

        # AZURE MODE: Generate SAS token (1 hour expiry)
        expiry_time = datetime.utcnow() + timedelta(hours=1)

        # Get account key for SAS generation
        # Note: This requires the connection string to extract the account key
        # In production with Managed Identity, consider using user delegation SAS

        if settings.azure_storage_connection_string:
            # Extract account name and key from connection string
            conn_parts = dict(
                item.split('=', 1) for item in settings.azure_storage_connection_string.split(';')
                if '=' in item
            )
            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=settings.azure_storage_container_documents,
                blob_name=document_blob_path,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time
            )

            download_url = f"{blob_client.url}?{sas_token}"
        else:
            # Fallback: return blob URL (won't work without SAS in production)
            logger.warning("No storage connection string, returning unsigned URL")
            download_url = blob_client.url

        logger.info(f"Generated download URL for job {job_id} (format: {format.value})")

        return DocumentDownloadResponse(
            download_url=download_url,
            expires_in=3600,  # 1 hour in seconds
            filename=filename,
            format=format
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )


@router.delete("/documents/{job_id}")
async def delete_document(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a job and its associated document.
    
    **Warning:** This action cannot be undone.
    
    **Returns:**
        Success message
    """
    settings = get_settings()
    
    try:
        # Get job from Cosmos DB
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)
        
        job = container.read_item(item=job_id, partition_key=user_id)
        
        # Delete document from Blob Storage if exists
        if job.get("result") and job["result"].get("document_blob_path"):
            blob_service = get_blob_service_client()
            blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_documents,
                blob=job["result"]["document_blob_path"]
            )
            
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {job['result']['document_blob_path']}")
        
        # Delete transcript from Blob Storage
        if job.get("input") and job["input"].get("transcript_url"):
            blob_service = get_blob_service_client()
            # Extract blob name from URL
            blob_path = f"{job_id}/transcript.txt"
            blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_uploads,
                blob=blob_path
            )
            
            blob_client.delete_blob()
            logger.info(f"Deleted transcript blob: {blob_path}")
        
        # Delete job from Cosmos DB
        container.delete_item(item=job_id, partition_key=user_id)
        logger.info(f"Deleted job: {job_id}")
        
        return {"message": f"Job {job_id} and associated files deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )

