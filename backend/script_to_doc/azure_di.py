"""
Azure Document Intelligence integration for structure extraction.
Uses prebuilt-read for transcript analysis and prebuilt-layout for screenshots.
"""

import logging
from typing import Dict, List, Optional
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class AzureDocumentIntelligence:
    """Client for Azure Document Intelligence operations."""
    
    def __init__(
        self,
        endpoint: str,
        credential: Optional[str] = None,
        use_managed_identity: bool = False
    ):
        """
        Initialize Azure Document Intelligence client.
        
        Args:
            endpoint: Azure DI endpoint URL
            credential: API key (if not using managed identity)
            use_managed_identity: Use Azure Managed Identity for auth
        """
        self.endpoint = endpoint
        
        if use_managed_identity:
            self.client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
        elif credential:
            self.client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(credential)
            )
        else:
            raise ValueError("Either credential or use_managed_identity must be provided")
    
    def analyze_transcript_text(self, text: str, blob_url: Optional[str] = None) -> Dict:
        """
        Analyze transcript text using prebuilt-read model.
        
        The prebuilt-read model extracts text content and document structure
        including paragraphs, styles, and reading order.
        
        Note: Azure DI requires a file (PDF/image) or blob URL, not raw text.
        If blob_url is provided, it will be used. Otherwise, the text will be
        returned as-is with minimal structure extraction.
        
        Args:
            text: Cleaned transcript text
            blob_url: Optional blob storage URL to analyze (if text is already uploaded)
            
        Returns:
            Dictionary containing:
            - content: Full text content
            - paragraphs: List of paragraph objects
            - styles: List of style information
            - pages: Page information
        """
        try:
            logger.info("Starting Azure DI analysis for transcript")
            
            # Azure DI requires a file/blob URL, not raw text
            # If we have a blob URL, use it; otherwise create minimal structure from text
            if blob_url:
                # Analyze document from blob URL
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-read",
                    analyze_request={"urlSource": blob_url}
                )
                result: AnalyzeResult = poller.result()
                
                # Extract structured information
                parsed_result = {
                    "content": result.content,
                    "paragraphs": self._extract_paragraphs(result),
                    "styles": self._extract_styles(result),
                    "pages": self._extract_pages(result),
                    "languages": self._extract_languages(result)
                }
                
                logger.info(f"Azure DI analysis complete. Found {len(parsed_result['paragraphs'])} paragraphs")
            else:
                # Fallback: Create minimal structure from text directly
                # Split text into paragraphs and create basic structure
                paragraphs = []
                for para_text in text.split('\n\n'):
                    if para_text.strip():
                        paragraphs.append({
                            "content": para_text.strip(),
                            "role": None
                        })
                
                parsed_result = {
                    "content": text,
                    "paragraphs": paragraphs,
                    "styles": [],
                    "pages": [{"page_number": 1, "width": 0, "height": 0, "unit": None, "lines": []}],
                    "languages": []
                }
                
                logger.info(f"Created minimal structure from text: {len(parsed_result['paragraphs'])} paragraphs")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Azure DI analysis failed: {str(e)}")
            # Return fallback structure instead of raising
            logger.warning("Falling back to minimal structure extraction")
            paragraphs = []
            for para_text in text.split('\n\n'):
                if para_text.strip():
                    paragraphs.append({
                        "content": para_text.strip(),
                        "role": None
                    })
            
            return {
                "content": text,
                "paragraphs": paragraphs,
                "styles": [],
                "pages": [{"page_number": 1, "width": 0, "height": 0, "unit": None, "lines": []}],
                "languages": []
            }
    
    def analyze_screenshot(self, image_url: str) -> Dict:
        """
        Analyze screenshot using prebuilt-layout model.
        
        Extracts UI elements, tables, and text from screenshots.
        
        Args:
            image_url: Blob storage URL of screenshot
            
        Returns:
            Dictionary containing:
            - content: Extracted text
            - ui_elements: List of detected UI elements
            - tables: List of tables
            - layout: Layout structure
        """
        try:
            logger.info(f"Starting Azure DI analysis for screenshot: {image_url}")
            
            # Analyze document from URL
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request={"urlSource": image_url}
            )
            
            result: AnalyzeResult = poller.result()
            
            # Extract structured information
            parsed_result = {
                "content": result.content,
                "ui_elements": self._extract_ui_elements(result),
                "tables": self._extract_tables(result),
                "layout": self._extract_layout(result),
                "figures": self._extract_figures(result)
            }
            
            logger.info(f"Screenshot analysis complete. Found {len(parsed_result['ui_elements'])} UI elements")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {str(e)}")
            raise
    
    def _extract_paragraphs(self, result: AnalyzeResult) -> List[Dict]:
        """Extract paragraph information from analysis result."""
        paragraphs = []
        
        if result.paragraphs:
            for para in result.paragraphs:
                paragraphs.append({
                    "content": para.content,
                    "role": para.role if hasattr(para, 'role') else None,
                    "bounding_regions": self._extract_bounding_regions(para)
                })
        
        return paragraphs
    
    def _extract_styles(self, result: AnalyzeResult) -> List[Dict]:
        """Extract style information."""
        styles = []
        
        if hasattr(result, 'styles') and result.styles:
            for style in result.styles:
                styles.append({
                    "is_handwritten": getattr(style, 'is_handwritten', False),
                    "confidence": getattr(style, 'confidence', 1.0),
                    "spans": [{"offset": s.offset, "length": s.length} for s in style.spans]
                })
        
        return styles
    
    def _extract_pages(self, result: AnalyzeResult) -> List[Dict]:
        """Extract page information."""
        pages = []
        
        if result.pages:
            for page in result.pages:
                pages.append({
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit if hasattr(page, 'unit') else None,
                    "lines": self._extract_lines(page)
                })
        
        return pages
    
    def _extract_lines(self, page) -> List[Dict]:
        """Extract line information from a page."""
        lines = []
        
        if hasattr(page, 'lines') and page.lines:
            for line in page.lines:
                lines.append({
                    "content": line.content,
                    "polygon": line.polygon if hasattr(line, 'polygon') else None
                })
        
        return lines
    
    def _extract_languages(self, result: AnalyzeResult) -> List[Dict]:
        """Extract language information."""
        languages = []
        
        if hasattr(result, 'languages') and result.languages:
            for lang in result.languages:
                languages.append({
                    "locale": lang.locale,
                    "confidence": lang.confidence,
                    "spans": [{"offset": s.offset, "length": s.length} for s in lang.spans]
                })
        
        return languages
    
    def _extract_ui_elements(self, result: AnalyzeResult) -> List[Dict]:
        """
        Extract UI elements from screenshot layout analysis.
        
        Identifies buttons, text fields, labels, etc.
        """
        ui_elements = []
        
        # Extract from lines (text elements)
        if result.pages:
            for page in result.pages:
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        # Analyze line content to identify UI element types
                        element_type = self._classify_ui_element(line.content)
                        
                        ui_elements.append({
                            "type": element_type,
                            "text": line.content,
                            "polygon": line.polygon if hasattr(line, 'polygon') else None,
                            "page": page.page_number
                        })
        
        return ui_elements
    
    def _classify_ui_element(self, text: str) -> str:
        """
        Classify UI element based on text content.
        
        Simple heuristics:
        - "Button", "Click", "Submit" -> button
        - Short text (< 30 chars) -> label
        - Contains "..." -> menu item
        """
        text_lower = text.lower()
        text_len = len(text)
        
        # Button indicators
        button_keywords = ["button", "click", "submit", "save", "cancel", "ok", "apply"]
        if any(kw in text_lower for kw in button_keywords):
            return "button"
        
        # Menu indicators
        if "..." in text or "▶" in text or ">" in text:
            return "menu_item"
        
        # Short text likely a label
        if text_len < 30 and not text.endswith("."):
            return "label"
        
        # Long text likely content
        if text_len > 50:
            return "content"
        
        return "text"
    
    def _extract_tables(self, result: AnalyzeResult) -> List[Dict]:
        """Extract table information from layout analysis."""
        tables = []
        
        if hasattr(result, 'tables') and result.tables:
            for table in result.tables:
                tables.append({
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": self._extract_table_cells(table)
                })
        
        return tables
    
    def _extract_table_cells(self, table) -> List[Dict]:
        """Extract cell information from a table."""
        cells = []
        
        if hasattr(table, 'cells') and table.cells:
            for cell in table.cells:
                cells.append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "kind": getattr(cell, 'kind', 'content')
                })
        
        return cells
    
    def _extract_layout(self, result: AnalyzeResult) -> Dict:
        """Extract overall layout structure."""
        layout = {
            "page_count": len(result.pages) if result.pages else 0,
            "content_length": len(result.content) if result.content else 0
        }
        
        return layout
    
    def _extract_figures(self, result: AnalyzeResult) -> List[Dict]:
        """Extract figure/image information."""
        figures = []
        
        if hasattr(result, 'figures') and result.figures:
            for figure in result.figures:
                figures.append({
                    "caption": getattr(figure, 'caption', None),
                    "bounding_regions": self._extract_bounding_regions(figure)
                })
        
        return figures
    
    def _extract_bounding_regions(self, element) -> List[Dict]:
        """Extract bounding region information from an element."""
        regions = []
        
        if hasattr(element, 'bounding_regions') and element.bounding_regions:
            for region in element.bounding_regions:
                regions.append({
                    "page_number": region.page_number,
                    "polygon": region.polygon if hasattr(region, 'polygon') else None
                })
        
        return regions
    
    def extract_process_structure(self, content: str, paragraphs: List[Dict]) -> Dict:
        """
        Identify process flow patterns from transcript structure.
        
        Looks for:
        - Sequential steps (First, Then, Next, Finally)
        - Action items (Click, Open, Navigate, Create)
        - Decision points (If, When, Choose)
        - Roles (User, Admin, Trainer)
        
        Args:
            content: Full transcript content
            paragraphs: Parsed paragraph information
            
        Returns:
            Dictionary with process structure information
        """
        structure = {
            "steps": [],
            "decisions": [],
            "roles": set(),
            "actions": [],
            "sequence_indicators": []
        }
        
        # Sequence indicators
        sequence_patterns = [
            r'\b(first|firstly|1st)\b',
            r'\b(second|secondly|2nd|then|next)\b',
            r'\b(third|thirdly|3rd|after\s+that)\b',
            r'\b(finally|lastly|last|in\s+conclusion)\b'
        ]
        
        # Action verbs
        action_verbs = [
            "click", "open", "navigate", "create", "delete", "update",
            "select", "choose", "enter", "type", "save", "cancel",
            "configure", "set", "enable", "disable", "install", "run"
        ]
        
        # Decision keywords
        decision_keywords = ["if", "when", "choose", "select", "whether", "depending"]
        
        # Role keywords
        role_keywords = ["user", "admin", "administrator", "trainer", "manager", "operator"]
        
        # Analyze content
        content_lower = content.lower()
        
        # Find sequence indicators
        import re
        for pattern in sequence_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                structure["sequence_indicators"].append({
                    "indicator": match.group(0),
                    "position": match.start()
                })
        
        # Find actions
        for verb in action_verbs:
            if verb in content_lower:
                structure["actions"].append(verb)
        
        # Find roles
        for role in role_keywords:
            if role in content_lower:
                structure["roles"].add(role)
        
        # Identify decision points
        for keyword in decision_keywords:
            if keyword in content_lower:
                structure["decisions"].append(keyword)
        
        # Convert set to list for JSON serialization
        structure["roles"] = list(structure["roles"])
        
        logger.info(f"Extracted process structure: {len(structure['actions'])} actions, "
                   f"{len(structure['sequence_indicators'])} sequence indicators")
        
        return structure

