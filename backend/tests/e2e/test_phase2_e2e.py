"""
Phase 2 End-to-End Test: Full pipeline with all Phase 2 features.
Tests Q&A filtering + topic ranking + step validation + enhanced confidence.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_phase2_e2e():
    """
    Test full Phase 2 pipeline with Azure OpenAI.

    Process: sample_meeting.txt → Parse → Segment → Filter Q&A → Rank Topics →
             Generate Steps → Validate → Enhance Confidence → Document
    """

    print("=" * 80)
    print("PHASE 2 END-TO-END TEST")
    print("Full Pipeline: Q&A Filter + Topic Ranker + Step Validator + Enhanced Confidence")
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

    # Create config with ALL Phase 2 features ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",  # Not needed for this test
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_key=azure_openai_key,
        azure_openai_deployment=azure_openai_deployment,
        use_azure_di=False,              # Disable DI for faster testing
        use_openai=True,                 # Enable OpenAI for step generation

        # Phase 1 features
        use_intelligent_parsing=True,    # ← Phase 1: Parser ENABLED
        use_topic_segmentation=True,     # ← Phase 1: Segmentation ENABLED

        # Phase 2 features (NEW)
        use_qa_filtering=True,           # ← Phase 2: Q&A filtering ENABLED
        use_topic_ranking=True,          # ← Phase 2: Topic ranking ENABLED
        use_step_validation=True,        # ← Phase 2: Step validation ENABLED

        # Thresholds (lenient for testing to avoid filtering everything)
        qa_density_threshold=0.50,       # 50% questions = Q&A section (lenient)
        importance_threshold=0.15,       # Min importance to keep (lenient)
        min_confidence_threshold=0.1,    # Min confidence for validation (lenient)

        min_steps=3,
        target_steps=5,
        max_steps=10,
        document_title="Azure Web App Deployment - Phase 2 Test"
    )

    print("=" * 80)
    print("PIPELINE CONFIGURATION")
    print("=" * 80)
    print("Phase 1 Features:")
    print(f"  ✓ Intelligent Parsing: {config.use_intelligent_parsing}")
    print(f"  ✓ Topic Segmentation: {config.use_topic_segmentation}")
    print()
    print("Phase 2 Features (NEW - with lenient thresholds for testing):")
    print(f"  ✓ Q&A Filtering: {config.use_qa_filtering} (threshold: {config.qa_density_threshold} - 50% questions)")
    print(f"  ✓ Topic Ranking: {config.use_topic_ranking} (threshold: {config.importance_threshold} - min importance)")
    print(f"  ✓ Step Validation: {config.use_step_validation} (min confidence: {config.min_confidence_threshold})")
    print()
    print(f"Target steps: {config.target_steps}")
    print(f"Azure OpenAI: {config.azure_openai_deployment}")
    print()

    # Initialize pipeline
    try:
        print("Initializing pipeline...")
        pipeline = ScriptToDocPipeline(config)
        print(f"✓ Pipeline initialized")
        print()
        print("Phase 1 Components:")
        print(f"  - Parser: {type(pipeline.transcript_parser).__name__ if pipeline.transcript_parser else 'None'}")
        print(f"  - Segmenter: {type(pipeline.topic_segmenter).__name__ if pipeline.topic_segmenter else 'None'}")
        print()
        print("Phase 2 Components:")
        print(f"  - Q&A Filter: {type(pipeline.qa_filter).__name__ if pipeline.qa_filter else 'None'}")
        print(f"  - Topic Ranker: {type(pipeline.topic_ranker).__name__ if pipeline.topic_ranker else 'None'}")
        print(f"  - Step Validator: {type(pipeline.step_validator).__name__ if pipeline.step_validator else 'None'}")
        print()
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    # Process transcript
    output_path = Path(__file__).parent / "test_output" / "phase2_e2e_result.md"
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
            total_quality = 0.0
            quality_indicators = {"high": 0, "medium": 0, "low": 0}
            validation_scores = []

            for i, step in enumerate(result.steps, 1):
                title = step.get('title', 'Untitled')
                actions = step.get('actions', [])
                confidence = step.get('confidence_score', 0.0)
                quality_score = step.get('quality_score', 0.0)
                quality_indicator = step.get('quality_indicator', 'unknown')

                total_actions += len(actions)
                total_confidence += confidence
                total_quality += quality_score

                if quality_indicator in quality_indicators:
                    quality_indicators[quality_indicator] += 1

                validation_scores.append(quality_score)

                print(f"{i}. {title}")
                print(f"   Actions: {len(actions)}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Quality Score: {quality_score:.2f}")
                print(f"   Quality Indicator: {quality_indicator}")
                print()

            # Calculate averages
            avg_actions = total_actions / len(result.steps)
            avg_confidence = total_confidence / len(result.steps)
            avg_quality = total_quality / len(result.steps)

            print("=" * 80)
            print("METRICS SUMMARY")
            print("=" * 80)
            print()
            print(f"Total Steps: {len(result.steps)}")
            print(f"Total Actions: {total_actions} (avg {avg_actions:.1f}/step)")
            print()
            print("Confidence Scores:")
            print(f"  Average: {avg_confidence:.2f}")
            print(f"  High (>= 0.7): {sum(1 for s in result.steps if s.get('confidence_score', 0) >= 0.7)} steps")
            print(f"  Medium (0.4-0.7): {sum(1 for s in result.steps if 0.4 <= s.get('confidence_score', 0) < 0.7)} steps")
            print(f"  Low (< 0.4): {sum(1 for s in result.steps if s.get('confidence_score', 0) < 0.4)} steps")
            print()
            print("Quality Scores:")
            print(f"  Average: {avg_quality:.2f}")
            print(f"  High quality: {quality_indicators.get('high', 0)} steps")
            print(f"  Medium quality: {quality_indicators.get('medium', 0)} steps")
            print(f"  Low quality: {quality_indicators.get('low', 0)} steps")
            print()
            print(f"Processing time: {result.processing_time:.2f}s")
            if result.metrics:
                print(f"Token usage: {result.metrics.get('total_tokens', 'N/A')} tokens")
            print()

            # Phase 2 specific metrics
            print("=" * 80)
            print("PHASE 2 QUALITY GATES")
            print("=" * 80)
            print()

            # Q&A filtering
            qa_filtered = result.metrics.get('qa_sections_filtered', 0) if result.metrics else 0
            print(f"Q&A Filtering:")
            print(f"  Sections filtered: {qa_filtered}")
            print()

            # Topic ranking
            topics_filtered = result.metrics.get('low_importance_topics_filtered', 0) if result.metrics else 0
            print(f"Topic Ranking:")
            print(f"  Low-importance topics filtered: {topics_filtered}")
            print()

            # Step validation
            validation_passed = len(result.steps)
            validation_failed = result.metrics.get('steps_failed_validation', 0) if result.metrics else 0
            print(f"Step Validation:")
            print(f"  Passed: {validation_passed}")
            print(f"  Failed: {validation_failed}")
            print()

            # Enhanced confidence
            confidence_boosted = sum(1 for s in result.steps
                                    if s.get('quality_score', 0) >= 0.7 and s.get('confidence_score', 0) >= 0.6)
            print(f"Enhanced Confidence:")
            print(f"  High confidence + high quality: {confidence_boosted} steps")
            print()

            print("=" * 80)
            print("✅ PHASE 2 E2E TEST COMPLETE")
            print("=" * 80)
            print()
            print("Next: Compare with Phase 1 baseline to measure improvements")
            print()

            return 0

        else:
            print("❌ No steps generated")
            return 1

    except Exception as e:
        print(f"❌ Processing failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = test_phase2_e2e()
    sys.exit(exit_code)
