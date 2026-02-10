#!/usr/bin/env python3
"""
Simple test script for the ScriptToDoc pipeline.
Tests the core functionality without requiring full Azure infrastructure.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from script_to_doc.pipeline import process_transcript_file, PipelineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_pipeline():
    """Test the pipeline with sample data."""
    
    print("=" * 60)
    print("ScriptToDoc Phase 1 - Pipeline Test")
    print("=" * 60)
    print()
    
    # Check for required environment variables
    import os
    required_vars = [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please set these in your .env file or environment")
        return False
    
    print("✅ Environment variables configured")
    print()
    
    # Sample transcript path
    sample_path = Path(__file__).parent.parent / "sample_data" / "transcripts" / "sample_meeting.txt"
    
    if not sample_path.exists():
        print(f"❌ Sample file not found: {sample_path}")
        return False
    
    print(f"📄 Sample transcript: {sample_path.name}")
    print()
    
    # Output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Create pipeline config
    print("⚙️  Configuring pipeline...")
    config = PipelineConfig(
        azure_di_endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        azure_di_key=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        target_steps=8,
        tone="Professional",
        audience="Technical Users",
        document_title="Azure Deployment Training"
    )
    
    print("   ✓ Azure Document Intelligence configured")
    print("   ✓ Azure OpenAI configured")
    print()
    
    # Progress callback
    def progress_callback(progress: float, stage: str):
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r   [{bar}] {progress*100:.0f}% - {stage.replace('_', ' ').title()}", end="", flush=True)
    
    print("🚀 Starting processing...")
    print()
    
    try:
        # Process transcript
        result = process_transcript_file(
            transcript_path=str(sample_path),
            output_dir=str(output_dir),
            config=config,
            progress_callback=progress_callback
        )
        
        print("\n")
        
        if result.success:
            print("✅ Processing completed successfully!")
            print()
            print("📊 Results:")
            print(f"   • Document: {result.document_path}")
            print(f"   • Steps generated: {result.metrics['total_steps']}")
            print(f"   • Average confidence: {result.metrics['average_confidence']:.2f}")
            print(f"   • High confidence steps: {result.metrics['high_confidence_steps']}")
            print(f"   • Processing time: {result.processing_time:.2f}s")
            print()
            print(f"📄 Open the document to view results:")
            print(f"   {result.document_path}")
            print()
            return True
        else:
            print(f"❌ Processing failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Pipeline test failed")
        return False


if __name__ == "__main__":
    # Load environment variables from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env")
        print()
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment variables")
        print()
    
    # Run test
    success = test_pipeline()
    
    print()
    print("=" * 60)
    
    sys.exit(0 if success else 1)

