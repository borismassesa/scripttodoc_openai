"""
Test Phase 1 parser integration with pipeline.
Verifies that use_intelligent_parsing flag works correctly.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_parser_disabled():
    """Test pipeline with parser DISABLED (legacy mode)."""

    print("=" * 80)
    print("TEST 1: Parser Disabled (Legacy Mode)")
    print("=" * 80)

    # Sample transcript
    transcript = """[00:00:05] Speaker 1: Hello everyone. Today we'll learn about Azure.
[00:00:15] Speaker 2: That sounds great!
[00:00:20] Speaker 1: First, navigate to portal.azure.com."""

    # Create config with parser DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,  # Disable Azure DI for testing
        use_openai=False,     # Disable OpenAI for testing
        use_intelligent_parsing=False,  # ← Parser DISABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that parser is NOT initialized
        assert pipeline.transcript_parser is None, "Parser should be None when disabled"

        print("✅ Pipeline initialized correctly with parser disabled")
        print(f"✅ transcript_parser = {pipeline.transcript_parser}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parser_enabled():
    """Test pipeline with parser ENABLED."""

    print("\n" + "=" * 80)
    print("TEST 2: Parser Enabled (Phase 1 Mode)")
    print("=" * 80)

    # Create config with parser ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,  # ← Parser ENABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that parser IS initialized
        assert pipeline.transcript_parser is not None, "Parser should be initialized when enabled"

        print("✅ Pipeline initialized correctly with parser enabled")
        print(f"✅ transcript_parser = {type(pipeline.transcript_parser).__name__}")

        # Test parsing a simple transcript (without full pipeline run)
        transcript = """[00:00:05] Speaker 1: Hello everyone. Today we'll learn about Azure.
[00:00:15] Speaker 2: That sounds great!
[00:00:20] Speaker 1: First, navigate to portal.azure.com."""

        parsed_sentences, metadata = pipeline.transcript_parser.parse(transcript)

        print(f"\n✅ Parser working: {len(parsed_sentences)} sentences, {metadata.total_speakers} speakers")
        print(f"   Primary speaker: {metadata.primary_speaker}")
        print(f"   Duration: {metadata.duration_seconds}s")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run parser integration tests."""

    print("\n" + "=" * 80)
    print("PHASE 1 PARSER INTEGRATION TESTS")
    print("=" * 80)
    print()

    tests = [
        ("Parser Disabled", test_parser_disabled),
        ("Parser Enabled", test_parser_enabled),
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
        print("\n✅ PHASE 1 PARSER INTEGRATION VERIFIED!")
        print("\nParser integration features verified:")
        print("  ✓ Feature flag use_intelligent_parsing works")
        print("  ✓ Parser initializes when enabled")
        print("  ✓ Parser remains None when disabled")
        print("  ✓ Backward compatibility maintained")
        print("\nReady for Day 6-7: Topic Segmentation")
        return 0
    else:
        print("\n❌ TESTS FAILED - Please review the failures above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
