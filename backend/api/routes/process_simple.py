"""
Simple file upload endpoint for testing without Azure dependencies.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from ..file_utils import process_uploaded_file

logger = logging.getLogger(__name__)

router = APIRouter()


class SimpleUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    file_type: str
    text_length: int
    preview: str


@router.post("/upload-test", response_model=SimpleUploadResponse)
async def test_upload(
    file: UploadFile = File(..., description="Transcript file (.txt or .pdf)"),
):
    """
    Simple upload test endpoint without Azure dependencies.
    Tests file upload, validation, and text extraction only.
    """
    try:
        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # Check file size (5MB limit)
        if file_size_mb > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large: {file_size_mb:.2f} MB (max: 5 MB)"
            )
        
        # Process file and extract text
        try:
            extracted_text, file_type = process_uploaded_file(file.filename, content)
            logger.info(f"Successfully extracted {len(extracted_text)} characters from {file_type} file")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Return success with preview
        preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        
        return SimpleUploadResponse(
            success=True,
            message="File uploaded and processed successfully",
            filename=file.filename,
            file_type=file_type,
            text_length=len(extracted_text),
            preview=preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload test failed: {str(e)}"
        )

