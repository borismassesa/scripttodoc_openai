"""
Base interface for document converters.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentConverter(ABC):
    """Base interface for document converters."""

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path) -> Path:
        """
        Convert document from one format to another.

        Args:
            input_path: Source document path
            output_path: Destination document path

        Returns:
            Path to converted document

        Raises:
            ConversionError: If conversion fails
        """
        pass

    @abstractmethod
    def get_supported_output_format(self) -> str:
        """Return the output format this converter produces."""
        pass


class ConversionError(Exception):
    """Raised when document conversion fails."""
    pass
