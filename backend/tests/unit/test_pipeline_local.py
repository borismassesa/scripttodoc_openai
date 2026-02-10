#!/usr/bin/env python3
"""
Local Pipeline Test Script
Run the ScriptToDoc pipeline directly without the API server.
"""

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig
from pathlib import Path
import os
from dotenv import load_dotenv
import sys

def main():
    # Load environment variables
    load_dotenv()

    print("="*80)
    print("SCRIPTTODOC LOCAL PIPELINE TEST")
    print("="*80)
    print()

    # Check for input file
    if len(sys.argv) > 1:
        transcript_path = Path(sys.argv[1])
    else:
        transcript_path = Path("../sample_data/transcripts/sample_meeting.txt")

    if not transcript_path.exists():
        print(f"❌ Error: Transcript file not found: {transcript_path}")
        print()
        print("Usage: python test_pipeline_local.py [transcript_file.txt]")
        print("Example: python test_pipeline_local.py my_transcript.txt")
        return

    # Load transcript
    with open(transcript_path, 'r') as f:
        transcript_text = f.read()

    print(f"✓ Loaded transcript: {transcript_path.name}")
    print(f"  Characters: {len(transcript_text)}")
    print()

    # Configure pipeline with ALL Phase 1 & Phase 2 features
    print("Configuring pipeline...")
    config = PipelineConfig(
        # Azure credentials
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),

        # Services
        use_openai=True,
        use_azure_di=False,  # Not needed for plain text

        # ===== PHASE 1 FEATURES =====
        use_intelligent_parsing=True,
        use_topic_segmentation=True,

        # ===== PHASE 2 FEATURES =====
        use_qa_filtering=True,
        use_topic_ranking=True,
        use_step_validation=True,

        # Thresholds
        qa_density_threshold=0.50,
        importance_threshold=0.15,
        min_confidence_threshold=0.1,

        # Document settings
        min_steps=3,
        target_steps=5,
        max_steps=10,
        document_title=f"Tutorial from {transcript_path.stem}"
    )

    print("✓ Configuration complete")
    print()
    print("  Phase 1:")
    print("    ✓ Intelligent Parsing")
    print("    ✓ Topic Segmentation")
    print()
    print("  Phase 2:")
    print("    ✓ Q&A Filtering")
    print("    ✓ Topic Ranking")
    print("    ✓ Step Validation")
    print("    ✓ Enhanced Confidence")
    print()

    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = ScriptToDocPipeline(config)
    print("✓ Pipeline initialized")
    print()

    # Process transcript
    output_path = f"test_output/{transcript_path.stem}_tutorial.md"
    print(f"Processing transcript... (this may take 20-30 seconds)")
    print()

    result = pipeline.process(
        transcript_text=transcript_text,
        output_path=output_path
    )

    # Display results
    print("="*80)
    print("RESULTS")
    print("="*80)
    print()

    if result.success:
        print("✅ SUCCESS!")
        print()
        print(f"📄 Document: {result.document_path}")
        print(f"⏱️  Processing time: {result.processing_time:.2f}s")
        print(f"📊 Steps generated: {len(result.steps)}")
        print()

        # Calculate averages
        avg_confidence = sum(s['confidence_score'] for s in result.steps) / len(result.steps)
        avg_quality = sum(s.get('quality_score', 0) for s in result.steps) / len(result.steps)

        quality_indicators = {}
        for step in result.steps:
            indicator = step.get('quality_indicator', 'unknown')
            quality_indicators[indicator] = quality_indicators.get(indicator, 0) + 1

        print("METRICS:")
        print(f"  Avg Confidence: {avg_confidence:.2f}")
        print(f"  Avg Quality: {avg_quality:.2f}")
        print()
        print("QUALITY DISTRIBUTION:")
        for indicator, count in sorted(quality_indicators.items()):
            print(f"  {indicator.capitalize()}: {count} steps")
        print()

        # Show steps
        print("STEPS:")
        print()
        for i, step in enumerate(result.steps, 1):
            print(f"{i}. {step['title']}")
            print(f"   • Actions: {len(step['actions'])}")
            print(f"   • Confidence: {step['confidence_score']:.2f} ({step.get('quality_indicator', 'N/A')})")
            print(f"   • Quality: {step.get('quality_score', 0):.2f}")
            print()

            # Show first 2 actions
            for j, action in enumerate(step['actions'][:2], 1):
                print(f"      {j}. {action['action']}")

            if len(step['actions']) > 2:
                print(f"      ... and {len(step['actions']) - 2} more actions")
            print()

        print("="*80)
        print(f"✅ Tutorial saved to: {result.document_path}")
        print("="*80)

    else:
        print("❌ FAILED")
        print()
        print(f"Error: {result.error}")
        print()

if __name__ == "__main__":
    main()
