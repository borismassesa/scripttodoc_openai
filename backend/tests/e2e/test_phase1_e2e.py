"""
Phase 1 End-to-End Test: Full pipeline with Azure OpenAI.
Tests parser + segmenter + step generation to measure quality improvements.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_phase1_e2e():
    """
    Test full Phase 1 pipeline with Azure OpenAI.

    Process: sample_meeting.txt → Parse → Segment → Generate Steps → Document
    """

    print("=" * 80)
    print("PHASE 1 END-TO-END TEST")
    print("Parser + Segmenter + Step Generation")
    print("=" * 80)
    print()

    # Load sample transcript
    sample_path = Path(__file__).parent.parent / "sample_data" / "transcripts" / "sample_meeting.txt"

    if not sample_path.exists():
        print(f"❌ Sample transcript not found: {sample_path}")
        return 1

    with open(sample_path, 'r') as f:
        transcript_text = f.read()

    print(f"✓ Loaded transcript: {len(transcript_text)} characters")
    print()

    # Load Azure credentials from .env
    from dotenv import load_dotenv
    load_dotenv()

    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
    azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not azure_openai_endpoint or not azure_openai_key:
        print("❌ Azure OpenAI credentials not found in .env file")
        print("   Please ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY are set")
        return 1

    print(f"✓ Azure OpenAI configured: {azure_openai_deployment}")
    print()

    # Create config with Phase 1 ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",  # Not needed for this test
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_key=azure_openai_key,
        azure_openai_deployment=azure_openai_deployment,
        use_azure_di=False,              # Disable DI for faster testing
        use_openai=True,                 # Enable OpenAI for step generation
        use_intelligent_parsing=True,    # ← Phase 1: Parser ENABLED
        use_topic_segmentation=True,     # ← Phase 1: Segmentation ENABLED
        min_steps=3,
        target_steps=5,                  # Request 5 steps (but segmenter determines actual count)
        max_steps=10,
        document_title="Azure Web App Deployment - Phase 1 Test"
    )

    print("=" * 80)
    print("PIPELINE CONFIGURATION")
    print("=" * 80)
    print(f"  Phase 1 Parsing: {config.use_intelligent_parsing}")
    print(f"  Phase 1 Segmentation: {config.use_topic_segmentation}")
    print(f"  Target steps: {config.target_steps}")
    print(f"  Azure OpenAI: {config.azure_openai_deployment}")
    print()

    # Initialize pipeline
    try:
        print("Initializing pipeline...")
        pipeline = ScriptToDocPipeline(config)
        print(f"✓ Pipeline initialized")
        print(f"  - Parser: {type(pipeline.transcript_parser).__name__ if pipeline.transcript_parser else 'None'}")
        print(f"  - Segmenter: {type(pipeline.topic_segmenter).__name__ if pipeline.topic_segmenter else 'None'}")
        print()
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    # Process transcript
    output_path = Path(__file__).parent / "test_output" / "phase1_e2e_result.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PROCESSING TRANSCRIPT")
    print("=" * 80)
    print()

    try:
        result = pipeline.process(
            transcript_text=transcript_text,
            output_path=str(output_path)
        )

        if not result.success:
            print(f"❌ Processing failed: {result.error}")
            return 1

        print("✓ Processing complete!")
        print()

        # Display results
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()

        print(f"Success: {result.success}")
        print(f"Document: {result.document_path}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print()

        # Steps summary
        if result.steps:
            print(f"Generated {len(result.steps)} steps:")
            print()

            total_actions = 0
            total_confidence = 0.0

            for i, step in enumerate(result.steps, 1):
                title = step.get("title", "Untitled")
                actions = step.get("actions", [])
                confidence = step.get("confidence_score", 0.0)

                total_actions += len(actions)
                total_confidence += confidence

                print(f"Step {i}: {title}")
                print(f"  Actions: {len(actions)}")
                print(f"  Confidence: {confidence:.2f}")

                # Preview actions
                for j, action in enumerate(actions[:3], 1):
                    action_text = action if isinstance(action, str) else action.get("action", "")
                    preview = action_text[:60] + "..." if len(action_text) > 60 else action_text
                    print(f"    {j}. {preview}")

                if len(actions) > 3:
                    print(f"    ... ({len(actions) - 3} more actions)")
                print()

            # Metrics
            avg_actions = total_actions / len(result.steps)
            avg_confidence = total_confidence / len(result.steps)

            print("=" * 80)
            print("METRICS")
            print("=" * 80)
            print(f"Total steps: {len(result.steps)}")
            print(f"Total actions: {total_actions}")
            print(f"Avg actions per step: {avg_actions:.1f}")
            print(f"Avg confidence: {avg_confidence:.2f}")
            print()

            # Token usage
            if result.metrics:
                token_usage = result.metrics.get("token_usage", {})
                total_tokens = token_usage.get("total_tokens", 0)
                input_tokens = token_usage.get("total_input_tokens", 0)
                output_tokens = token_usage.get("total_output_tokens", 0)

                print("Token Usage:")
                print(f"  Input: {input_tokens:,}")
                print(f"  Output: {output_tokens:,}")
                print(f"  Total: {total_tokens:,}")
                print()

        # Read generated document
        if output_path.exists():
            print("=" * 80)
            print("GENERATED DOCUMENT PREVIEW")
            print("=" * 80)
            print()

            with open(output_path, 'r') as f:
                doc_lines = f.readlines()

            # Show first 30 lines
            for i, line in enumerate(doc_lines[:30], 1):
                print(line.rstrip())

            if len(doc_lines) > 30:
                print(f"\n... ({len(doc_lines) - 30} more lines)")
            print()

        print("=" * 80)
        print("✅ PHASE 1 END-TO-END TEST COMPLETE")
        print("=" * 80)
        print()
        print(f"Document saved to: {output_path}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Run Phase 1 end-to-end test."""
    exit_code = test_phase1_e2e()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
