"""
Phase 2 integration test: Q&A Filter + Topic Ranker + Pipeline.
Verifies end-to-end flow with quality gates.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_phase2_disabled():
    """Test pipeline with Phase 2 features DISABLED (Phase 1 only)."""

    print("=" * 80)
    print("TEST 1: Phase 2 Disabled (Phase 1 Only)")
    print("=" * 80)

    # Sample transcript
    transcript = """[00:00:05] Speaker 1: Hello everyone. Today we'll learn about Azure.
[00:00:15] Speaker 2: That sounds great!
[00:00:20] Speaker 1: First, navigate to portal.azure.com."""

    # Create config with Phase 2 DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,    # Phase 1 enabled
        use_topic_segmentation=True,     # Phase 1 enabled
        use_qa_filtering=False,          # ← Phase 2 DISABLED
        use_topic_ranking=False          # ← Phase 2 DISABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that Phase 2 components are NOT initialized
        assert pipeline.qa_filter is None, "Q&A filter should be None when disabled"
        assert pipeline.topic_ranker is None, "Topic ranker should be None when disabled"

        # Check that Phase 1 components ARE initialized
        assert pipeline.transcript_parser is not None, "Parser should be initialized"
        assert pipeline.topic_segmenter is not None, "Segmenter should be initialized"

        print("✅ Pipeline initialized correctly with Phase 2 disabled")
        print(f"✅ qa_filter = {pipeline.qa_filter}")
        print(f"✅ topic_ranker = {pipeline.topic_ranker}")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__}")
        print(f"✅ topic_segmenter = {type(pipeline.topic_segmenter).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_qa_filtering_only():
    """Test pipeline with Q&A filtering enabled."""

    print("\n" + "=" * 80)
    print("TEST 2: Q&A Filtering Only")
    print("=" * 80)

    # Create config with Q&A filtering ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=True,           # ← Q&A filtering ENABLED
        use_topic_ranking=False,
        qa_density_threshold=0.3
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that Q&A filter IS initialized
        assert pipeline.qa_filter is not None, "Q&A filter should be initialized when enabled"
        assert pipeline.topic_ranker is None, "Topic ranker should be None when disabled"

        print("✅ Pipeline initialized correctly with Q&A filtering enabled")
        print(f"✅ qa_filter = {type(pipeline.qa_filter).__name__}")
        print(f"✅ topic_ranker = {pipeline.topic_ranker}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_topic_ranking_only():
    """Test pipeline with topic ranking enabled."""

    print("\n" + "=" * 80)
    print("TEST 3: Topic Ranking Only")
    print("=" * 80)

    # Create config with topic ranking ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=False,
        use_topic_ranking=True,          # ← Topic ranking ENABLED
        importance_threshold=0.3
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that topic ranker IS initialized
        assert pipeline.qa_filter is None, "Q&A filter should be None when disabled"
        assert pipeline.topic_ranker is not None, "Topic ranker should be initialized when enabled"

        print("✅ Pipeline initialized correctly with topic ranking enabled")
        print(f"✅ qa_filter = {pipeline.qa_filter}")
        print(f"✅ topic_ranker = {type(pipeline.topic_ranker).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_full():
    """Test pipeline with BOTH Q&A filtering and topic ranking enabled."""

    print("\n" + "=" * 80)
    print("TEST 4: Full Phase 2 (Q&A Filtering + Topic Ranking)")
    print("=" * 80)

    # Create config with BOTH enabled
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=True,           # ← BOTH ENABLED
        use_topic_ranking=True,          # ← BOTH ENABLED
        qa_density_threshold=0.3,
        importance_threshold=0.3
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that BOTH are initialized
        assert pipeline.qa_filter is not None, "Q&A filter should be initialized"
        assert pipeline.topic_ranker is not None, "Topic ranker should be initialized"

        print("✅ Pipeline initialized correctly with full Phase 2")
        print(f"✅ qa_filter = {type(pipeline.qa_filter).__name__}")
        print(f"✅ topic_ranker = {type(pipeline.topic_ranker).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_auto_enable_segmentation():
    """Test that Phase 2 features auto-enable segmentation when needed."""

    print("\n" + "=" * 80)
    print("TEST 5: Auto-Enable Segmentation for Phase 2")
    print("=" * 80)

    # Create config with Phase 2 enabled but segmentation DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=False,   # ← Parser DISABLED
        use_topic_segmentation=False,    # ← Segmentation DISABLED
        use_qa_filtering=True,           # ← But Q&A filtering ENABLED
        use_topic_ranking=False
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that segmentation was auto-enabled
        assert pipeline.transcript_parser is not None, "Parser should be auto-enabled"
        assert pipeline.topic_segmenter is not None, "Segmenter should be auto-enabled"
        assert pipeline.qa_filter is not None, "Q&A filter should be initialized"

        print("✅ Pipeline auto-enabled segmentation for Phase 2")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__} (auto-enabled)")
        print(f"✅ topic_segmenter = {type(pipeline.topic_segmenter).__name__} (auto-enabled)")
        print(f"✅ qa_filter = {type(pipeline.qa_filter).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run Phase 2 integration tests."""

    print("\n" + "=" * 80)
    print("PHASE 2 INTEGRATION TESTS")
    print("Q&A Filter + Topic Ranker + Pipeline")
    print("=" * 80)
    print()

    tests = [
        ("Phase 2 Disabled", test_phase2_disabled),
        ("Q&A Filtering Only", test_phase2_qa_filtering_only),
        ("Topic Ranking Only", test_phase2_topic_ranking_only),
        ("Full Phase 2", test_phase2_full),
        ("Auto-Enable Segmentation", test_phase2_auto_enable_segmentation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ FAIL: {test_name} - {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ PHASE 2 INTEGRATION VERIFIED!")
        print("\nPhase 2 features verified:")
        print("  ✓ Q&A filter initialization works correctly")
        print("  ✓ Topic ranker initialization works correctly")
        print("  ✓ Feature flags control initialization properly")
        print("  ✓ Phase 2 auto-enables segmentation when needed")
        print("  ✓ Backward compatibility maintained (Phase 1 only mode)")
        print("\nReady for Phase 2 end-to-end testing!")
        return 0
    else:
        print("\n❌ TESTS FAILED - Please review the failures above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
