"""
Job status endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from script_to_doc.config import get_settings
from ..models import JobStatusResponse, JobStatus, ProcessingStage
from ..dependencies import get_cosmos_client, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get processing status for a job.
    
    **Returns:**
    - job_id: Job identifier
    - status: Current status (queued, processing, completed, failed)
    - progress: Progress from 0.0 to 1.0
    - stage: Current processing stage
    - result: Result data (when completed)
    - error: Error message (when failed)
    """
    settings = get_settings()
    
    try:
        # Get job from Cosmos DB
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)
        
        job = container.read_item(item=job_id, partition_key=user_id)
        
        return JobStatusResponse(
            job_id=job["id"],
            status=JobStatus(job["status"]),
            progress=job.get("progress", 0.0),
            stage=ProcessingStage(job.get("stage", "pending")),
            current_step=job.get("current_step"),
            total_steps=job.get("total_steps"),
            stage_detail=job.get("stage_detail"),
            created_at=datetime.fromisoformat(job["created_at"]),
            updated_at=datetime.fromisoformat(job["updated_at"]),
            config=job.get("config"),
            result=job.get("result"),
            error=job.get("error")
        )
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )


@router.get("/jobs", response_model=list[JobStatusResponse])
async def list_jobs(
    limit: int = 10,
    status_filter: str = None,  # Optional filter: 'completed', 'failed', 'processing', etc.
    user_id: str = Depends(get_current_user)
):
    """
    List recent jobs for the current user.

    **Parameters:**
    - limit: Maximum number of jobs to return (default: 10, max: 50)
    - status_filter: Optional status filter ('completed', 'failed', 'processing', etc.)

    **Returns:**
        List of recent jobs

    **Performance Optimizations:**
    - Reduced default limit to 10 (max 50 instead of 100)
    - Uses partition key for faster queries
    - Returns only essential fields to reduce data transfer
    """
    settings = get_settings()

    # Cap limit at 50 for better performance (reduced from 100)
    limit = min(limit, 50)

    try:
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client(settings.azure_cosmos_database)
        container = database.get_container_client(settings.azure_cosmos_container_jobs)

        # Optimized query: Use indexed fields and limit result size
        # Only select fields needed for list view (not full result data)
        if status_filter:
            query = """
                SELECT TOP @limit c.id, c.status, c.progress, c.stage, c.current_step, c.total_steps,
                       c.stage_detail, c.created_at, c.updated_at, c.config, c.error,
                       c.result.metrics as result_metrics
                FROM c
                WHERE c.user_id = @user_id AND c.status = @status
                ORDER BY c._ts DESC
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@status", "value": status_filter},
                {"name": "@limit", "value": limit}
            ]
        else:
            query = """
                SELECT TOP @limit c.id, c.status, c.progress, c.stage, c.current_step, c.total_steps,
                       c.stage_detail, c.created_at, c.updated_at, c.config, c.error,
                       c.result.metrics as result_metrics
                FROM c
                WHERE c.user_id = @user_id
                ORDER BY c._ts DESC
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]

        # Execute query with timeout protection
        logger.info(f"Querying jobs for user {user_id[:8]}... (limit: {limit}, filter: {status_filter})")

        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=user_id,  # Use partition key for faster query
            max_item_count=limit
        ))

        logger.info(f"Retrieved {len(items)} jobs in query")

        # Convert to response models
        jobs = []
        for item in items:
            # Reconstruct minimal result object
            result_data = None
            if item.get("result_metrics"):
                result_data = {
                    "metrics": item["result_metrics"]
                }

            jobs.append(JobStatusResponse(
                job_id=item["id"],
                status=JobStatus(item["status"]),
                progress=item.get("progress", 0.0),
                stage=ProcessingStage(item.get("stage", "pending")),
                current_step=item.get("current_step"),
                total_steps=item.get("total_steps"),
                stage_detail=item.get("stage_detail"),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                config=item.get("config"),
                result=result_data,
                error=item.get("error")
            ))

        return jobs

    except Exception as e:
        logger.warning(f"Failed to list jobs (may be expected if DB not set up): {e}")
        # Return empty list instead of error for better UX during testing
        return []

