"""
Local filesystem storage (replaces Azure Blob Storage).

Provides Blob Storage-compatible API for local development without Azure subscription.
"""

import logging
from pathlib import Path
from typing import Optional, List
from io import BytesIO

logger = logging.getLogger(__name__)


class LocalBlobServiceClient:
    """
    Local filesystem client that emulates Blob Storage API.

    Provides the same interface as Azure Blob Storage but uses local directories.
    """

    def __init__(self, base_path: str = "./data"):
        """
        Initialize local storage client.

        Args:
            base_path: Base directory for all containers
        """
        self.base_path = Path(base_path)
        self._ensure_directories()
        logger.info(f"Initialized LocalBlobServiceClient at: {self.base_path.absolute()}")

    def _ensure_directories(self):
        """Create container directories if they don't exist."""
        for container in ["uploads", "documents", "temp"]:
            container_path = self.base_path / container
            container_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured container directory: {container_path}")

    def get_blob_client(self, container: str, blob: str) -> 'LocalBlobClient':
        """
        Get blob client for file operations.

        Args:
            container: Container name (e.g., "uploads", "documents")
            blob: Blob path within container (e.g., "job123/transcript.txt")

        Returns:
            LocalBlobClient instance
        """
        return LocalBlobClient(self.base_path / container, blob)

    def get_container_client(self, container: str) -> 'LocalContainerClient':
        """
        Get container client.

        Args:
            container: Container name

        Returns:
            LocalContainerClient instance
        """
        return LocalContainerClient(self.base_path / container)


class LocalBlobClient:
    """
    Blob client for individual file operations.

    Emulates Azure BlobClient API for local files.
    """

    def __init__(self, container_path: Path, blob_name: str):
        """
        Initialize blob client.

        Args:
            container_path: Path to container directory
            blob_name: Blob path within container
        """
        self.container_path = container_path
        self.blob_name = blob_name
        self.blob_path = container_path / blob_name
        self.url = f"file://{self.blob_path.absolute()}"

    def upload_blob(self, data, overwrite: bool = True):
        """
        Upload data to blob (write to file).

        Args:
            data: Data to upload (bytes, str, or file-like object)
            overwrite: Whether to overwrite existing file
        """
        # Ensure parent directory exists
        self.blob_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists and overwrite is False
        if self.blob_path.exists() and not overwrite:
            raise FileExistsError(f"Blob {self.blob_name} already exists")

        # Write data
        if isinstance(data, bytes):
            with open(self.blob_path, 'wb') as f:
                f.write(data)
        elif isinstance(data, str):
            with open(self.blob_path, 'w', encoding='utf-8') as f:
                f.write(data)
        elif hasattr(data, 'read'):
            # File-like object
            with open(self.blob_path, 'wb') as f:
                f.write(data.read())
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        logger.info(f"Uploaded blob: {self.blob_name} ({self.blob_path.stat().st_size} bytes)")

    def download_blob(self) -> 'LocalBlobDownloader':
        """
        Download blob (read from file).

        Returns:
            LocalBlobDownloader instance
        """
        if not self.blob_path.exists():
            raise FileNotFoundError(f"Blob {self.blob_name} not found")

        return LocalBlobDownloader(self.blob_path)

    def exists(self) -> bool:
        """
        Check if blob exists.

        Returns:
            True if file exists, False otherwise
        """
        return self.blob_path.exists()

    def delete_blob(self):
        """Delete blob (remove file)."""
        if self.blob_path.exists():
            self.blob_path.unlink()
            logger.info(f"Deleted blob: {self.blob_name}")
        else:
            logger.warning(f"Attempted to delete non-existent blob: {self.blob_name}")

    def get_blob_properties(self) -> dict:
        """
        Get blob properties.

        Returns:
            Dictionary with blob metadata
        """
        if not self.blob_path.exists():
            raise FileNotFoundError(f"Blob {self.blob_name} not found")

        stat = self.blob_path.stat()
        return {
            'name': self.blob_name,
            'size': stat.st_size,
            'last_modified': stat.st_mtime,
            'content_type': self._guess_content_type(),
        }

    def _guess_content_type(self) -> str:
        """Guess content type based on file extension."""
        extension = self.blob_path.suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
        }
        return content_types.get(extension, 'application/octet-stream')

    def generate_sas_url(self, expiry_hours: int = 1) -> str:
        """
        Generate SAS-like URL for blob access.

        For local storage, just returns file:// URL.

        Args:
            expiry_hours: Not used in local mode

        Returns:
            file:// URL
        """
        return self.url


class LocalBlobDownloader:
    """
    Blob downloader for reading file data.

    Emulates Azure BlobDownloadStreamDownloader API.
    """

    def __init__(self, blob_path: Path):
        """
        Initialize downloader.

        Args:
            blob_path: Path to local file
        """
        self.blob_path = blob_path

    def readall(self) -> bytes:
        """
        Read all data from blob.

        Returns:
            File contents as bytes
        """
        with open(self.blob_path, 'rb') as f:
            data = f.read()
        logger.debug(f"Downloaded {len(data)} bytes from {self.blob_path.name}")
        return data

    def readinto(self, stream):
        """
        Read blob data into stream.

        Args:
            stream: File-like object to write to
        """
        with open(self.blob_path, 'rb') as f:
            data = f.read()
            stream.write(data)

    def chunks(self):
        """
        Read blob data in chunks.

        Yields:
            Data chunks
        """
        with open(self.blob_path, 'rb') as f:
            while True:
                chunk = f.read(8192)  # 8KB chunks
                if not chunk:
                    break
                yield chunk


class LocalContainerClient:
    """
    Container client for container-level operations.

    Emulates Azure ContainerClient API.
    """

    def __init__(self, container_path: Path):
        """
        Initialize container client.

        Args:
            container_path: Path to container directory
        """
        self.container_path = container_path
        self.container_name = container_path.name

        # Ensure container directory exists
        self.container_path.mkdir(parents=True, exist_ok=True)

    def list_blobs(self, name_starts_with: Optional[str] = None) -> List[dict]:
        """
        List blobs in container.

        Args:
            name_starts_with: Optional prefix filter

        Returns:
            List of blob metadata dictionaries
        """
        if not self.container_path.exists():
            return []

        blobs = []
        for file_path in self.container_path.rglob('*'):
            if file_path.is_file():
                # Get relative path from container
                rel_path = file_path.relative_to(self.container_path)
                blob_name = str(rel_path).replace('\\', '/')

                # Apply prefix filter if specified
                if name_starts_with and not blob_name.startswith(name_starts_with):
                    continue

                blobs.append({
                    'name': blob_name,
                    'size': file_path.stat().st_size,
                    'last_modified': file_path.stat().st_mtime,
                })

        return blobs

    def delete_blob(self, blob_name: str):
        """
        Delete a blob from container.

        Args:
            blob_name: Blob path within container
        """
        blob_path = self.container_path / blob_name
        if blob_path.exists():
            blob_path.unlink()
            logger.info(f"Deleted blob: {blob_name}")

    def get_blob_client(self, blob: str) -> LocalBlobClient:
        """
        Get blob client.

        Args:
            blob: Blob path within container

        Returns:
            LocalBlobClient instance
        """
        return LocalBlobClient(self.container_path, blob)
