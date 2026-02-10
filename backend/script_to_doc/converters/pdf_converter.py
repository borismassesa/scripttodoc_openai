"""
PDF converter using LibreOffice.
Converts DOCX documents to PDF format.
"""

import logging
import subprocess
from pathlib import Path
from .base import DocumentConverter, ConversionError

logger = logging.getLogger(__name__)


class PDFConverter(DocumentConverter):
    """Convert DOCX to PDF using LibreOffice."""

    def convert(self, input_path: Path, output_path: Path) -> Path:
        """
        Convert DOCX to PDF using LibreOffice headless mode.

        Args:
            input_path: Path to source DOCX file
            output_path: Path where PDF should be saved

        Returns:
            Path to converted PDF file

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Ensure input exists
            if not input_path.exists():
                raise ConversionError(f"Input file not found: {input_path}")

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Run LibreOffice conversion
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_path.parent),
                str(input_path)
            ]

            logger.info(f"Running PDF conversion: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                raise ConversionError(
                    f"LibreOffice PDF conversion failed: {error_msg}"
                )

            # LibreOffice creates file with same name but .pdf extension
            generated_pdf = output_path.parent / f"{input_path.stem}.pdf"

            # Verify the file was created
            if not generated_pdf.exists():
                raise ConversionError(
                    f"PDF file was not created at expected location: {generated_pdf}"
                )

            # Rename if needed
            if generated_pdf != output_path:
                generated_pdf.rename(output_path)

            logger.info(f"Successfully converted {input_path.name} to PDF: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            raise ConversionError("PDF conversion timed out after 30 seconds")
        except ConversionError:
            # Re-raise ConversionError as-is
            raise
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}", exc_info=True)
            raise ConversionError(f"PDF conversion error: {str(e)}")

    def get_supported_output_format(self) -> str:
        """Return the output format this converter produces."""
        return "pdf"
