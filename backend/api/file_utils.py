"""
Utility functions for file processing.
"""

import logging
from io import BytesIO
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text as string
        
    Raises:
        ValueError: If PDF cannot be read or contains no text
    """
    try:
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF file contains no pages")
        
        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text)
                    logger.debug(f"Extracted {len(text)} characters from page {page_num}")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue
        
        if not text_parts:
            raise ValueError("No text could be extracted from PDF")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Successfully extracted {len(full_text)} characters from {len(reader.pages)} pages")
        
        return full_text
        
    except Exception as e:
        logger.error(f"Failed to process PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def process_uploaded_file(filename: str, content: bytes) -> tuple[str, str]:
    """
    Process uploaded file and extract text content.
    
    Args:
        filename: Name of the uploaded file
        content: File content as bytes
        
    Returns:
        Tuple of (extracted_text, file_type)
        
    Raises:
        ValueError: If file type is not supported or processing fails
    """
    file_lower = filename.lower()
    
    if file_lower.endswith('.txt'):
        try:
            text = content.decode('utf-8')
            logger.info(f"Processed .txt file: {len(text)} characters")
            return text, 'txt'
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    text = content.decode(encoding)
                    logger.info(f"Processed .txt file with {encoding}: {len(text)} characters")
                    return text, 'txt'
                except UnicodeDecodeError:
                    continue
            raise ValueError("Unable to decode text file with supported encodings")
    
    elif file_lower.endswith('.pdf'):
        text = extract_text_from_pdf(content)
        return text, 'pdf'
    
    else:
        raise ValueError(f"Unsupported file type. Only .txt and .pdf files are accepted")

