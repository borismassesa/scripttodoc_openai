"""
Conversion service orchestrator.
Manages document format conversions.
"""

import logging
from pathlib import Path
from enum import Enum
from typing import Dict, Optional
from .base import DocumentConverter, ConversionError
from .pdf_converter import PDFConverter
from .ppt_converter import PPTConverter

logger = logging.getLogger(__name__)


class DocumentFormat(str, Enum):
    """Supported document formats."""
    DOCX = "docx"
    PDF = "pdf"
    PPTX = "pptx"


class ConversionService:
    """
    Main service for document format conversion.
    Orchestrates different converter implementations.
    """

    def __init__(self):
        """Initialize conversion service with available converters."""
        self._converters: Dict[DocumentFormat, DocumentConverter] = {
            DocumentFormat.PDF: PDFConverter(),
            DocumentFormat.PPTX: PPTConverter(),
        }

    def convert_document(
        self,
        input_path: Path,
        output_format: DocumentFormat,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Convert document to specified format.

        Args:
            input_path: Path to source DOCX file
            output_format: Desired output format
            output_path: Optional custom output path

        Returns:
            Path to converted document

        Raises:
            ConversionError: If conversion fails
            ValueError: If format not supported
        """
        # No conversion needed for DOCX
        if output_format == DocumentFormat.DOCX:
            logger.info("No conversion needed for DOCX format")
            return input_path

        # Get appropriate converter
        converter = self._converters.get(output_format)
        if not converter:
            raise ValueError(f"Unsupported format: {output_format}")

        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}.{output_format.value}"

        try:
            logger.info(f"Converting {input_path.name} to {output_format.value}")
            result_path = converter.convert(input_path, output_path)
            logger.info(f"Conversion successful: {result_path}")
            return result_path

        except ConversionError as e:
            logger.error(f"Conversion failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected conversion error: {e}", exc_info=True)
            raise ConversionError(f"Conversion failed: {str(e)}")

    def is_format_supported(self, format: DocumentFormat) -> bool:
        """
        Check if format is supported.

        Args:
            format: Document format to check

        Returns:
            True if format is supported, False otherwise
        """
        return format in [DocumentFormat.DOCX, DocumentFormat.PDF, DocumentFormat.PPTX]

    def get_supported_formats(self) -> list:
        """
        Get list of supported formats.

        Returns:
            List of supported DocumentFormat values
        """
        return [DocumentFormat.DOCX, DocumentFormat.PDF, DocumentFormat.PPTX]


# Singleton instance
_conversion_service: Optional[ConversionService] = None


def get_conversion_service() -> ConversionService:
    """
    Get or create conversion service instance.

    Returns:
        ConversionService singleton instance
    """
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = ConversionService()
    return _conversion_service
