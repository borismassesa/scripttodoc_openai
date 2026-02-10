# File Conversion Service Implementation Plan
## User Story 117: Multi-Format Document Export

**Status**: Ready for Implementation
**Created**: 2025-12-03
**Estimated Complexity**: Medium-High

---

## 📋 Executive Summary

This plan implements a file conversion service that converts generated DOCX documents into multiple formats (PDF, PPT, DOCX) based on user selection. The service will integrate with the existing ScriptToDoc pipeline.

---

## 🎯 Requirements

### Functional Requirements
1. ✅ Convert generated DOCX content to PDF format
2. ✅ Convert generated DOCX content to PPT/PPTX format
3. ✅ Allow users to select desired export format
4. ✅ Maintain existing DOCX export functionality
5. ✅ Provide meaningful error messages for failed conversions
6. ✅ Log conversion errors for monitoring

### Non-Functional Requirements
- Conversion should complete within 30 seconds for typical documents
- Support documents up to 50 pages
- Maintain document formatting quality
- No additional Azure services required (use existing infrastructure)

---

## 🏗️ Architecture Overview

### Current Flow
```
Document Generator (python-docx)
    ↓
Save to Blob Storage (.docx)
    ↓
Return download URL
```

### Proposed Flow
```
Document Generator (python-docx)
    ↓
Save base DOCX to temp location
    ↓
Conversion Service
    ├─→ PDF Converter (docx → pdf)
    ├─→ PPT Converter (docx → pptx)
    └─→ DOCX (no conversion)
    ↓
Upload to Blob Storage (with format extension)
    ↓
Return download URL
```

---

## 📦 Technology Stack

### Backend Libraries

#### Option 1: LibreOffice (Recommended)
**Pros:**
- Best format fidelity
- Supports DOCX → PDF, DOCX → PPT
- Battle-tested, stable
- Free and open-source

**Cons:**
- Requires LibreOffice installation
- Larger docker image size
- Requires subprocess calls

**Installation:**
```bash
# For Ubuntu/Debian
apt-get install -y libreoffice-writer libreoffice-impress

# Python wrapper
pip install python-libreoffice-convert
```

#### Option 2: python-pptx + docx2pdf (Alternative)
**Pros:**
- Pure Python (easier deployment)
- No system dependencies for PPT
- Lightweight

**Cons:**
- docx2pdf requires MS Word on Windows or LibreOffice on Linux
- Less format fidelity
- PPT conversion requires content restructuring

**Installation:**
```bash
pip install python-pptx docx2pdf
```

#### Option 3: Aspose.Words (Commercial - Not Recommended)
**Pros:**
- Best conversion quality
- No external dependencies

**Cons:**
- Expensive licensing ($999/year)
- Overkill for this use case

### **Recommended Approach: LibreOffice**
Use LibreOffice for both PDF and PPT conversions due to superior format fidelity and reliability.

---

## 📁 File Structure

### New Files to Create
```
backend/
├── script_to_doc/
│   └── converters/
│       ├── __init__.py              # Converter module
│       ├── base.py                  # Base converter interface
│       ├── pdf_converter.py         # DOCX → PDF conversion
│       ├── ppt_converter.py         # DOCX → PPT conversion
│       └── conversion_service.py    # Main conversion orchestrator
├── requirements.txt                 # Add new dependencies
└── Dockerfile                       # Add LibreOffice installation

frontend/
└── components/
    └── FormatSelector.tsx           # Format selection dropdown
```

### Files to Modify
```
backend/
├── api/
│   ├── models.py                    # Add format enum
│   └── routes/
│       └── documents.py             # Add format parameter
└── workers/
    └── processor.py                 # Integrate conversion service

frontend/
├── components/
│   └── DocumentResults.tsx          # Add format selection UI
└── lib/
    └── api.ts                       # Update API types
```

---

## 🔧 Implementation Details

### Phase 1: Backend - Conversion Service

#### Step 1.1: Create Base Converter Interface
**File**: `backend/script_to_doc/converters/base.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

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
```

#### Step 1.2: Create PDF Converter
**File**: `backend/script_to_doc/converters/pdf_converter.py`

```python
import logging
import subprocess
from pathlib import Path
from .base import DocumentConverter, ConversionError

logger = logging.getLogger(__name__)

class PDFConverter(DocumentConverter):
    """Convert DOCX to PDF using LibreOffice."""

    def convert(self, input_path: Path, output_path: Path) -> Path:
        """Convert DOCX to PDF using LibreOffice headless mode."""
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

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise ConversionError(
                    f"LibreOffice conversion failed: {result.stderr}"
                )

            # LibreOffice creates file with same name but .pdf extension
            generated_pdf = output_path.parent / f"{input_path.stem}.pdf"

            # Rename if needed
            if generated_pdf != output_path:
                generated_pdf.rename(output_path)

            logger.info(f"Successfully converted {input_path} to PDF")
            return output_path

        except subprocess.TimeoutExpired:
            raise ConversionError("PDF conversion timed out")
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            raise ConversionError(f"PDF conversion error: {str(e)}")

    def get_supported_output_format(self) -> str:
        return "pdf"
```

#### Step 1.3: Create PPT Converter
**File**: `backend/script_to_doc/converters/ppt_converter.py`

```python
import logging
import subprocess
from pathlib import Path
from .base import DocumentConverter, ConversionError

logger = logging.getLogger(__name__)

class PPTConverter(DocumentConverter):
    """Convert DOCX to PPTX using LibreOffice."""

    def convert(self, input_path: Path, output_path: Path) -> Path:
        """Convert DOCX to PPTX using LibreOffice headless mode."""
        try:
            if not input_path.exists():
                raise ConversionError(f"Input file not found: {input_path}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Run LibreOffice conversion
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pptx',
                '--outdir', str(output_path.parent),
                str(input_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise ConversionError(
                    f"LibreOffice conversion failed: {result.stderr}"
                )

            generated_pptx = output_path.parent / f"{input_path.stem}.pptx"

            if generated_pptx != output_path:
                generated_pptx.rename(output_path)

            logger.info(f"Successfully converted {input_path} to PPTX")
            return output_path

        except subprocess.TimeoutExpired:
            raise ConversionError("PPTX conversion timed out")
        except Exception as e:
            logger.error(f"PPTX conversion failed: {e}")
            raise ConversionError(f"PPTX conversion error: {str(e)}")

    def get_supported_output_format(self) -> str:
        return "pptx"
```

#### Step 1.4: Create Conversion Service Orchestrator
**File**: `backend/script_to_doc/converters/conversion_service.py`

```python
import logging
from pathlib import Path
from enum import Enum
from typing import Dict, Type
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
        self._converters: Dict[DocumentFormat, Type[DocumentConverter]] = {
            DocumentFormat.PDF: PDFConverter(),
            DocumentFormat.PPTX: PPTConverter(),
        }

    def convert_document(
        self,
        input_path: Path,
        output_format: DocumentFormat,
        output_path: Path = None
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
            logger.info(f"Converting {input_path} to {output_format.value}")
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
        """Check if format is supported."""
        return format in [DocumentFormat.DOCX, DocumentFormat.PDF, DocumentFormat.PPTX]

    def get_supported_formats(self) -> list[DocumentFormat]:
        """Get list of supported formats."""
        return [DocumentFormat.DOCX, DocumentFormat.PDF, DocumentFormat.PPTX]

# Singleton instance
_conversion_service = None

def get_conversion_service() -> ConversionService:
    """Get or create conversion service instance."""
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = ConversionService()
    return _conversion_service
```

---

### Phase 2: Backend - API Integration

#### Step 2.1: Update Data Models
**File**: `backend/api/models.py`

Add after line 8:
```python
class DocumentFormat(str, Enum):
    """Supported document export formats."""
    DOCX = "docx"
    PDF = "pdf"
    PPTX = "pptx"
```

Update `DocumentDownloadResponse` (around line 70):
```python
class DocumentDownloadResponse(BaseModel):
    """Response with document download information."""
    download_url: str = Field(..., description="SAS URL for document download")
    expires_in: int = Field(..., description="URL expiry time in seconds")
    filename: str = Field(..., description="Document filename")
    format: DocumentFormat = Field(..., description="Document format")
```

#### Step 2.2: Update Documents Route
**File**: `backend/api/routes/documents.py`

Add import at top:
```python
from ..models import DocumentFormat, ConversionError
from script_to_doc.converters.conversion_service import get_conversion_service
```

Update endpoint signature (line 23):
```python
@router.get("/documents/{job_id}", response_model=DocumentDownloadResponse)
async def get_document_download_url(
    job_id: str,
    format: DocumentFormat = DocumentFormat.DOCX,  # NEW PARAMETER
    user_id: str = Depends(get_current_user)
):
```

Add conversion logic before SAS generation (after line 63):
```python
        # Get base document path
        base_document_path = job["result"]["document_blob_path"]
        base_filename = job["result"].get("filename", "training_document.docx")

        # Handle format conversion
        if format != DocumentFormat.DOCX:
            try:
                # Download base DOCX from blob
                blob_client_base = blob_service.get_blob_client(
                    container=settings.azure_storage_container_documents,
                    blob=base_document_path
                )

                # Download to temp file
                import tempfile
                from pathlib import Path

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_input = Path(temp_dir) / "input.docx"
                    temp_output = Path(temp_dir) / f"output.{format.value}"

                    # Download DOCX
                    with open(temp_input, "wb") as f:
                        f.write(blob_client_base.download_blob().readall())

                    # Convert to desired format
                    conversion_service = get_conversion_service()
                    converted_path = conversion_service.convert_document(
                        input_path=temp_input,
                        output_format=format,
                        output_path=temp_output
                    )

                    # Upload converted document
                    converted_blob_path = base_document_path.replace('.docx', f'.{format.value}')
                    blob_client_converted = blob_service.get_blob_client(
                        container=settings.azure_storage_container_documents,
                        blob=converted_blob_path
                    )

                    with open(converted_path, "rb") as f:
                        blob_client_converted.upload_blob(f, overwrite=True)

                    # Use converted document for download
                    document_blob_path = converted_blob_path
                    filename = base_filename.replace('.docx', f'.{format.value}')
                    blob_client = blob_client_converted

                    logger.info(f"Converted document to {format.value} for job {job_id}")

            except ConversionError as e:
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
            document_blob_path = base_document_path
            filename = base_filename
            blob_client = blob_service.get_blob_client(
                container=settings.azure_storage_container_documents,
                blob=document_blob_path
            )
```

Update return statement (line 106):
```python
        return DocumentDownloadResponse(
            download_url=download_url,
            expires_in=3600,
            filename=filename,
            format=format  # NEW FIELD
        )
```

---

### Phase 3: Frontend - UI Integration

#### Step 3.1: Create Format Selector Component
**File**: `frontend/components/FormatSelector.tsx`

```typescript
'use client';

import { Download } from 'lucide-react';
import { useState } from 'react';

export type DocumentFormat = 'docx' | 'pdf' | 'pptx';

interface FormatSelectorProps {
  onDownload: (format: DocumentFormat) => void;
  loading?: boolean;
}

const FORMAT_OPTIONS = [
  { value: 'docx', label: 'Word Document (.docx)', icon: '📄' },
  { value: 'pdf', label: 'PDF Document (.pdf)', icon: '📕' },
  { value: 'pptx', label: 'PowerPoint (.pptx)', icon: '📊' },
] as const;

export default function FormatSelector({ onDownload, loading = false }: FormatSelectorProps) {
  const [selectedFormat, setSelectedFormat] = useState<DocumentFormat>('docx');

  const handleDownload = () => {
    onDownload(selectedFormat);
  };

  return (
    <div className="flex items-center space-x-4">
      {/* Format Selection */}
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Export Format
        </label>
        <select
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value as DocumentFormat)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={loading}
        >
          {FORMAT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.icon} {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Download Button */}
      <div className="flex-shrink-0 pt-6">
        <button
          onClick={handleDownload}
          disabled={loading}
          className={`
            flex items-center space-x-2 px-6 py-2 rounded-lg font-semibold
            transition-colors shadow-md hover:shadow-lg
            ${loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
            }
          `}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Converting...</span>
            </>
          ) : (
            <>
              <Download className="h-5 w-5" />
              <span>Download</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
```

#### Step 3.2: Update DocumentResults Component
**File**: `frontend/components/DocumentResults.tsx`

Add import at top:
```typescript
import FormatSelector, { type DocumentFormat } from './FormatSelector';
```

Add state for download loading (after line 18):
```typescript
  const [downloadLoading, setDownloadLoading] = useState(false);
```

Replace download button section (lines 150-176) with:
```typescript
      {/* Format Selection and Download */}
      <div className="mb-6">
        <FormatSelector
          onDownload={handleFormatDownload}
          loading={downloadLoading}
        />
      </div>

      {/* Preview Button */}
      {downloadUrl && officeOnlineUrl && (
        <a
          href={officeOnlineUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center space-x-3 py-4 px-6 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors shadow-md hover:shadow-lg"
        >
          <ExternalLink className="h-5 w-5" />
          <span>Preview Online (Word)</span>
        </a>
      )}
```

Add download handler (before return statement):
```typescript
  const handleFormatDownload = async (format: DocumentFormat) => {
    try {
      setDownloadLoading(true);
      const download = await getDocumentDownload(jobId, format);

      // Trigger download
      const link = document.createElement('a');
      link.href = download.download_url;
      link.download = download.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err: any) {
      console.error('Download failed:', err);
      setError(err?.message || 'Failed to download document');
    } finally {
      setDownloadLoading(false);
    }
  };
```

#### Step 3.3: Update API Client
**File**: `frontend/lib/api.ts`

Update `DocumentDownload` interface (line 124):
```typescript
export interface DocumentDownload {
  download_url: string;
  expires_in: number;
  filename: string;
  format: 'docx' | 'pdf' | 'pptx';
}
```

Update `getDocumentDownload` function (line 188):
```typescript
export async function getDocumentDownload(
  jobId: string,
  format: 'docx' | 'pdf' | 'pptx' = 'docx'
): Promise<DocumentDownload> {
  const response = await apiClient.get<DocumentDownload>(
    `/api/documents/${jobId}`,
    {
      params: { format },
      timeout: 60000,
    }
  );
  return response.data;
}
```

---

### Phase 4: Infrastructure

#### Step 4.1: Update Requirements
**File**: `backend/requirements.txt`

Add at the end:
```
# Document conversion (User Story 117)
python-libreoffice-convert==1.0.0
```

#### Step 4.2: Update Dockerfile (if exists)
**File**: `backend/Dockerfile`

Add LibreOffice installation:
```dockerfile
# Install LibreOffice for document conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

#### Step 4.3: Update Environment Config
**File**: `backend/script_to_doc/config.py`

Add optional config (if needed):
```python
    # Document Conversion Settings (User Story 117)
    conversion_timeout_seconds: int = Field(
        default=30,
        description="Maximum time for document conversion"
    )
    conversion_enabled: bool = Field(
        default=True,
        description="Enable/disable document conversion features"
    )
```

---

## 🧪 Testing Strategy

### Unit Tests

#### Test Converters
**File**: `backend/tests/test_converters.py`

```python
import pytest
from pathlib import Path
from script_to_doc.converters.conversion_service import (
    ConversionService,
    DocumentFormat,
    ConversionError
)

@pytest.fixture
def sample_docx(tmp_path):
    """Create a sample DOCX file for testing."""
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test document")
    docx_path = tmp_path / "test.docx"
    doc.save(docx_path)
    return docx_path

def test_pdf_conversion(sample_docx, tmp_path):
    """Test DOCX to PDF conversion."""
    service = ConversionService()
    output_path = tmp_path / "output.pdf"

    result = service.convert_document(
        input_path=sample_docx,
        output_format=DocumentFormat.PDF,
        output_path=output_path
    )

    assert result.exists()
    assert result.suffix == '.pdf'
    assert result.stat().st_size > 0

def test_pptx_conversion(sample_docx, tmp_path):
    """Test DOCX to PPTX conversion."""
    service = ConversionService()
    output_path = tmp_path / "output.pptx"

    result = service.convert_document(
        input_path=sample_docx,
        output_format=DocumentFormat.PPTX,
        output_path=output_path
    )

    assert result.exists()
    assert result.suffix == '.pptx'

def test_docx_no_conversion(sample_docx):
    """Test that DOCX format returns original file."""
    service = ConversionService()

    result = service.convert_document(
        input_path=sample_docx,
        output_format=DocumentFormat.DOCX
    )

    assert result == sample_docx

def test_invalid_format(sample_docx):
    """Test error handling for invalid format."""
    service = ConversionService()

    with pytest.raises(ValueError):
        service.convert_document(
            input_path=sample_docx,
            output_format="invalid_format"
        )

def test_missing_input_file(tmp_path):
    """Test error handling for missing input file."""
    service = ConversionService()
    fake_path = tmp_path / "nonexistent.docx"

    with pytest.raises(ConversionError):
        service.convert_document(
            input_path=fake_path,
            output_format=DocumentFormat.PDF
        )
```

#### Test API Endpoint
**File**: `backend/tests/test_documents_api.py`

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_download_with_format_parameter():
    """Test document download with format parameter."""
    # Mock job setup needed
    job_id = "test-job-123"

    # Test DOCX (default)
    response = client.get(f"/api/documents/{job_id}")
    assert response.status_code == 200
    assert response.json()["format"] == "docx"

    # Test PDF
    response = client.get(f"/api/documents/{job_id}?format=pdf")
    assert response.status_code == 200
    assert response.json()["format"] == "pdf"

    # Test PPTX
    response = client.get(f"/api/documents/{job_id}?format=pptx")
    assert response.status_code == 200
    assert response.json()["format"] == "pptx"

def test_invalid_format_parameter():
    """Test error handling for invalid format."""
    job_id = "test-job-123"

    response = client.get(f"/api/documents/{job_id}?format=invalid")
    assert response.status_code == 422  # Validation error
```

### Integration Tests

#### Manual Testing Checklist
- [ ] Upload transcript and generate document
- [ ] Download as DOCX - verify formatting
- [ ] Download as PDF - verify formatting
- [ ] Download as PPTX - verify conversion
- [ ] Test error handling - simulate conversion failure
- [ ] Test timeout scenarios
- [ ] Verify SAS URLs expire correctly
- [ ] Test with large documents (>20 pages)

---

## 🚀 Deployment Plan

### Pre-Deployment Checklist
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] LibreOffice installed in production environment
- [ ] Docker image rebuilt with LibreOffice
- [ ] Environment variables configured
- [ ] API documentation updated
- [ ] Frontend components tested

### Deployment Steps
1. **Backend Deployment**
   - Install dependencies: `pip install -r requirements.txt`
   - Install LibreOffice: `apt-get install libreoffice-writer libreoffice-impress`
   - Run database migrations (if any)
   - Deploy backend service
   - Verify health check: `GET /health`

2. **Frontend Deployment**
   - Build frontend: `npm run build`
   - Deploy frontend service
   - Verify API connectivity

3. **Verification**
   - Test DOCX download
   - Test PDF conversion
   - Test PPTX conversion
   - Monitor logs for errors

### Rollback Plan
If issues occur:
1. Revert frontend to previous version
2. Revert backend API changes
3. Keep LibreOffice installed for future use
4. Document issues for investigation

---

## 📊 Success Metrics

### Functional Metrics
- ✅ All three formats (DOCX, PDF, PPTX) downloadable
- ✅ Conversion success rate > 95%
- ✅ Format fidelity maintained (visual inspection)
- ✅ Error messages displayed to users

### Performance Metrics
- PDF conversion: < 10 seconds (typical)
- PPTX conversion: < 15 seconds (typical)
- No impact on existing DOCX generation time
- Memory usage increase < 200MB during conversion

### User Experience Metrics
- Format selection dropdown visible and functional
- Download button provides feedback during conversion
- Error messages are clear and actionable
- No breaking changes to existing functionality

---

## 🐛 Error Handling

### Error Scenarios

1. **LibreOffice Not Installed**
   - Detection: Check for `libreoffice` command in PATH
   - Error Message: "Document conversion unavailable. Please contact support."
   - Fallback: Disable PDF/PPTX options, only offer DOCX

2. **Conversion Timeout**
   - Detection: subprocess.TimeoutExpired
   - Error Message: "Document conversion timed out. Please try again or download as DOCX."
   - Action: Log error, return 500 with meaningful message

3. **Corrupted DOCX File**
   - Detection: LibreOffice exits with non-zero code
   - Error Message: "Unable to convert document format. Please download as DOCX."
   - Action: Log error details, offer DOCX download

4. **Blob Storage Error**
   - Detection: Azure SDK exceptions
   - Error Message: "Failed to store converted document. Please try again."
   - Action: Log error, retry once, then fail gracefully

5. **Unsupported Format**
   - Detection: Format validation in API
   - Error Message: "Unsupported format requested."
   - Action: Return 422 Unprocessable Entity

---

## 🔐 Security Considerations

1. **File System Access**
   - Use temporary directories for conversion
   - Clean up temp files after conversion
   - Set restrictive file permissions

2. **Command Injection**
   - Use subprocess.run with list arguments (not shell=True)
   - Validate all file paths
   - No user input passed to LibreOffice command

3. **Resource Limits**
   - Set conversion timeout (30 seconds)
   - Limit concurrent conversions
   - Monitor disk space usage

4. **Access Control**
   - Maintain existing user authentication
   - Verify user owns job before conversion
   - Generate SAS tokens with minimal permissions

---

## 📝 Documentation Updates

### API Documentation
Update FastAPI Swagger docs with:
- New `format` query parameter
- Format enum values
- Example requests/responses
- Error codes

### User Documentation
Create user guide:
- How to select export format
- Supported formats and use cases
- Troubleshooting conversion issues
- Format-specific limitations

### Developer Documentation
Update technical docs:
- Conversion service architecture
- Adding new format converters
- Testing conversion features
- Debugging conversion issues

---

## 🎯 Future Enhancements (Out of Scope)

These features are not included in the current implementation but can be added later:

1. **Additional Formats**
   - HTML export
   - Markdown export
   - EPUB for e-readers

2. **Conversion Settings**
   - PDF quality settings
   - Custom page sizes
   - Watermark support

3. **Batch Conversion**
   - Convert multiple documents at once
   - Background conversion jobs

4. **Preview Without Download**
   - In-browser PDF preview
   - PPTX thumbnail preview

5. **Format-Specific Optimizations**
   - PDF/A compliance
   - PowerPoint slide layout optimization
   - Accessibility features

---

## 💡 Implementation Notes

### Estimated Timeline
- **Phase 1** (Backend Conversion): 4-6 hours
- **Phase 2** (API Integration): 2-3 hours
- **Phase 3** (Frontend UI): 2-3 hours
- **Phase 4** (Infrastructure): 1-2 hours
- **Testing & QA**: 3-4 hours
- **Total**: 12-18 hours

### Dependencies
- LibreOffice installation in production environment
- No additional Azure services required
- No breaking changes to existing API

### Risk Assessment
- **Low Risk**: Format conversion is isolated from document generation
- **Medium Risk**: LibreOffice installation in production
- **Mitigation**: Fallback to DOCX-only if LibreOffice unavailable

---

## ✅ Acceptance Criteria Verification

### User Story Requirements Met

| Requirement | Implementation | Status |
|------------|---------------|---------|
| Convert to PDF | PDFConverter + LibreOffice | ✅ |
| Convert to PPT | PPTConverter + LibreOffice | ✅ |
| Convert to DOCX | No conversion (native) | ✅ |
| Format parameter | API query parameter | ✅ |
| Frontend selection | FormatSelector component | ✅ |
| Error handling | ConversionError + logging | ✅ |
| Meaningful errors | User-friendly messages | ✅ |

### Acceptance Criteria

✅ **Given** the system generates raw document content,
✅ **When** a file type parameter is specified,
✅ **Then** the service should convert the content to the requested file format.

✅ **Given** an unsupported or failed conversion occurs,
✅ **When** the conversion fails,
✅ **Then** the system should log the error and return a meaningful message to the user.

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: "LibreOffice command not found"
- **Solution**: Install LibreOffice: `apt-get install libreoffice-writer libreoffice-impress`

**Issue**: "Permission denied" during conversion
- **Solution**: Ensure temp directory has write permissions

**Issue**: "Conversion timeout"
- **Solution**: Increase timeout in config, check server resources

**Issue**: "PDF formatting incorrect"
- **Solution**: Check DOCX source formatting, LibreOffice version

### Logging
All conversion operations logged with:
- Input/output paths
- Conversion duration
- Success/failure status
- Error details

---

## 🎓 References

- [LibreOffice Headless Documentation](https://wiki.documentfoundation.org/Documentation/HowTo/Use_LibreOffice_in_Headless_Mode)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [Azure Blob Storage SDK](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)

---

**Plan Status**: ✅ Ready for Implementation
**Next Step**: Review and approve plan, then begin Phase 1 implementation
