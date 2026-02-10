"""
Step Validator integration test: StepValidator + Pipeline.
Verifies step validation is properly integrated into the pipeline.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig


def test_step_validator_disabled():
    """Test pipeline with step validation DISABLED."""

    print("=" * 80)
    print("TEST 1: Step Validator Disabled")
    print("=" * 80)

    # Create config with step validation DISABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=False,
        use_topic_ranking=False,
        use_step_validation=False  # ← DISABLED
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that step validator is NOT initialized
        assert pipeline.step_validator is None, "Step validator should be None when disabled"

        print("✅ Pipeline initialized correctly with step validation disabled")
        print(f"✅ step_validator = {pipeline.step_validator}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_step_validator_enabled():
    """Test pipeline with step validation ENABLED."""

    print("\n" + "=" * 80)
    print("TEST 2: Step Validator Enabled")
    print("=" * 80)

    # Create config with step validation ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=False,
        use_topic_ranking=False,
        use_step_validation=True,  # ← ENABLED
        min_confidence_threshold=0.3
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that step validator IS initialized
        assert pipeline.step_validator is not None, "Step validator should be initialized when enabled"

        # Check configuration
        assert pipeline.step_validator.config.min_confidence_threshold == 0.3

        print("✅ Pipeline initialized correctly with step validation enabled")
        print(f"✅ step_validator = {type(pipeline.step_validator).__name__}")
        print(f"✅ min_confidence_threshold = {pipeline.step_validator.config.min_confidence_threshold}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_step_validator_with_phase2_full():
    """Test pipeline with ALL Phase 2 features enabled."""

    print("\n" + "=" * 80)
    print("TEST 3: Full Phase 2 (Q&A Filter + Topic Ranker + Step Validator)")
    print("=" * 80)

    # Create config with ALL Phase 2 features ENABLED
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_intelligent_parsing=True,
        use_topic_segmentation=True,
        use_qa_filtering=True,          # ← ENABLED
        use_topic_ranking=True,          # ← ENABLED
        use_step_validation=True,        # ← ENABLED
        qa_density_threshold=0.3,
        importance_threshold=0.3,
        min_confidence_threshold=0.2
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check that ALL Phase 2 components are initialized
        assert pipeline.qa_filter is not None, "Q&A filter should be initialized"
        assert pipeline.topic_ranker is not None, "Topic ranker should be initialized"
        assert pipeline.step_validator is not None, "Step validator should be initialized"

        print("✅ Pipeline initialized correctly with full Phase 2")
        print(f"✅ qa_filter = {type(pipeline.qa_filter).__name__}")
        print(f"✅ topic_ranker = {type(pipeline.topic_ranker).__name__}")
        print(f"✅ step_validator = {type(pipeline.step_validator).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_step_validator_custom_config():
    """Test pipeline with custom step validation config."""

    print("\n" + "=" * 80)
    print("TEST 4: Step Validator with Custom Config")
    print("=" * 80)

    # Create config with custom threshold
    config = PipelineConfig(
        azure_di_endpoint="https://fake.endpoint",
        azure_openai_endpoint="https://fake.endpoint",
        use_azure_di=False,
        use_openai=False,
        use_step_validation=True,
        min_confidence_threshold=0.5  # Custom threshold
    )

    try:
        pipeline = ScriptToDocPipeline(config)

        # Check custom configuration
        assert pipeline.step_validator is not None
        assert pipeline.step_validator.config.min_confidence_threshold == 0.5

        print("✅ Pipeline initialized with custom step validation config")
        print(f"✅ min_confidence_threshold = {pipeline.step_validator.config.min_confidence_threshold}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run Step Validator integration tests."""

    print("\n" + "=" * 80)
    print("STEP VALIDATOR INTEGRATION TESTS")
    print("Step Validator + Pipeline")
    print("=" * 80)
    print()

    tests = [
        ("Step Validator Disabled", test_step_validator_disabled),
        ("Step Validator Enabled", test_step_validator_enabled),
        ("Full Phase 2", test_step_validator_with_phase2_full),
        ("Custom Config", test_step_validator_custom_config),
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
        print("\n✅ STEP VALIDATOR INTEGRATION VERIFIED!")
        print("\nStep Validator integration verified:")
        print("  ✓ Step validator initialization works correctly")
        print("  ✓ Feature flag controls initialization properly")
        print("  ✓ Custom configuration works")
        print("  ✓ Compatible with full Phase 2 (Q&A filter + ranker + validator)")
        print("\nReady for Phase 2 Days 6-7 end-to-end testing!")
        return 0
    else:
        print("\n❌ TESTS FAILED - Please review the failures above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
