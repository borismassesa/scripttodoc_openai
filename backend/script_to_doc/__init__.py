"""
ScriptToDoc - AI-Powered Training Document Generator
Core processing package for transcript analysis and document generation.
"""

__version__ = "0.1.0"
__author__ = "Boris"

from .pipeline import process_transcript, PipelineConfig

__all__ = ["process_transcript", "PipelineConfig"]

