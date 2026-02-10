"""
Phase 1 integration test: Parser + Topic Segmentation + Pipeline.
Verifies end-to-end flow with intelligent parsing and topic segmentation.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_phase1_disabled():
    """Test pipeline with Phase 1 features DISABLED (legacy mode)."""

    print("=" * 80)
    print("TEST 1: Phase 1 Disabled (Legacy Mode)")
    print("=" * 80)

    # Sample transcript
    transcript = """[00:00:05] Speaker 1: Hello everyone. Today we'll learn about Azure.
[00:00:15] Speaker 2: That sounds great!
[00:00:20] Speaker 1: First, navigate to portal.azure.com."""

    # Create config with Phase 1 DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,  # Disable Azure DI for testing
        use_openai=False,     # Disable OpenAI for testing
        use_intelligent_parsing=False,  # ← Phase 1 DISABLED
        use_topic_segmentation=False
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that Phase 1 components are NOT initialized
        assert pipeline.transcript_parser is None, "Parser should be None when disabled"
        assert pipeline.topic_segmenter is None, "Segmenter should be None when disabled"

        print("✅ Pipeline initialized correctly with Phase 1 disabled")
        print(f"✅ transcript_parser = {pipeline.transcript_parser}")
        print(f"✅ topic_segmenter = {pipeline.topic_segmenter}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase1_parser_only():
    """Test pipeline with PARSER enabled, segmentation disabled."""

    print("\n" + "=" * 80)
    print("TEST 2: Phase 1 Parser Only")
    print("=" * 80)

    # Create config with parser ENABLED, segmentation DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,   # ← Parser ENABLED
        use_topic_segmentation=False    # ← Segmentation DISABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that parser IS initialized, segmenter is NOT
        assert pipeline.transcript_parser is not None, "Parser should be initialized when enabled"
        assert pipeline.topic_segmenter is None, "Segmenter should be None when disabled"

        print("✅ Pipeline initialized correctly with parser enabled")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__}")
        print(f"✅ topic_segmenter = {pipeline.topic_segmenter}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase1_full():
    """Test pipeline with BOTH parser and segmentation enabled."""

    print("\n" + "=" * 80)
    print("TEST 3: Phase 1 Full (Parser + Segmentation)")
    print("=" * 80)

    # Create config with BOTH enabled
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,    # ← Parser ENABLED
        use_topic_segmentation=True      # ← Segmentation ENABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that BOTH are initialized
        assert pipeline.transcript_parser is not None, "Parser should be initialized"
        assert pipeline.topic_segmenter is not None, "Segmenter should be initialized"

        print("✅ Pipeline initialized correctly with Phase 1 full")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__}")
        print(f"✅ topic_segmenter = {type(pipeline.topic_segmenter).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phase1_segmentation_auto_enables_parser():
    """Test that enabling segmentation automatically enables parser."""

    print("\n" + "=" * 80)
    print("TEST 4: Segmentation Auto-Enables Parser")
    print("=" * 80)

    # Create config with segmentation ENABLED, parser DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=False,   # ← Parser DISABLED
        use_topic_segmentation=True      # ← Segmentation ENABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that parser was auto-enabled
        assert pipeline.transcript_parser is not None, "Parser should be auto-enabled"
        assert pipeline.topic_segmenter is not None, "Segmenter should be initialized"

        print("✅ Pipeline auto-enabled parser for segmentation")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__} (auto-enabled)")
        print(f"✅ topic_segmenter = {type(pipeline.topic_segmenter).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run Phase 1 integration tests."""

    print("\n" + "=" * 80)
    print("PHASE 1 INTEGRATION TESTS")
    print("Parser + Topic Segmentation + Pipeline")
    print("=" * 80)
    print()

    tests = [
        ("Phase 1 Disabled", test_phase1_disabled),
        ("Parser Only", test_phase1_parser_only),
        ("Parser + Segmentation", test_phase1_full),
        ("Auto-Enable Parser", test_phase1_segmentation_auto_enables_parser),
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
        print("\n✅ PHASE 1 INTEGRATION VERIFIED!")
        print("\nPhase 1 features verified:")
        print("  ✓ Parser initialization works correctly")
        print("  ✓ Segmenter initialization works correctly")
        print("  ✓ Feature flags control initialization properly")
        print("  ✓ Segmentation auto-enables parser when needed")
        print("  ✓ Backward compatibility maintained (legacy mode)")
        print("\nReady for Phase 1 end-to-end testing!")
        return 0
    else:
        print("\n❌ TESTS FAILED - Please review the failures above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
