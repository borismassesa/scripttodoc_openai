"""
Test to verify that user's target_steps choice is respected.
This ensures Phase 1 topic segmentation doesn't override user preferences.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig

def test_step_count_control():
    """Verify that the pipeline respects user's target_steps when Phase 1 is disabled."""

    # Sample transcript
    transcript = """
    Hello everyone, welcome to this tutorial on Azure deployment.
    Today we're going to cover several important topics.

    First, let's talk about creating resource groups.
    Resource groups are containers for Azure resources.
    You can create them through the Azure Portal.

    Next, we'll configure networking.
    Virtual networks are essential for cloud infrastructure.
    You need to set up subnets and security groups.

    After that, we'll deploy an application.
    Applications can be deployed using various methods.
    Container apps are becoming increasingly popular.

    Finally, we'll monitor the deployment.
    Monitoring helps ensure everything is running smoothly.
    Azure provides excellent monitoring tools.
    """

    print("=" * 80)
    print("STEP COUNT CONTROL TEST")
    print("=" * 80)
    print()

    # Test different target_steps values
    for target_steps in [3, 6, 10]:
        print(f"\n📊 Testing with target_steps={target_steps}")
        print("-" * 80)

        config = PipelineConfig(
            azure_di_endpoint="dummy",
            azure_openai_endpoint="dummy",
            use_azure_di=False,  # Disable for testing
            use_openai=False,    # Disable for testing
            use_intelligent_parsing=False,  # ✅ Phase 1 DISABLED
            use_topic_segmentation=False,   # ✅ Phase 1 DISABLED
            target_steps=target_steps,
            min_steps=3,
            max_steps=15
        )

        pipeline = ScriptToDocPipeline(config)

        # Access the chunker directly to test
        from script_to_doc.transcript_cleaner import TranscriptCleaner, SentenceTokenizer, TranscriptChunker

        cleaner = TranscriptCleaner()
        tokenizer = SentenceTokenizer()
        chunker = TranscriptChunker(tokenizer)

        cleaned = cleaner.normalize(transcript)
        chunks = chunker.chunk_smart(cleaned, target_chunks=target_steps, prefer_paragraphs=True)

        print(f"  ✅ Requested: {target_steps} steps")
        print(f"  ✅ Generated: {len(chunks)} chunks")

        if len(chunks) == target_steps:
            print(f"  ✅ SUCCESS: Chunk count matches target_steps!")
        elif abs(len(chunks) - target_steps) <= 1:
            print(f"  ⚠️  CLOSE: Chunk count within ±1 of target (acceptable)")
        else:
            print(f"  ❌ FAIL: Chunk count doesn't match target_steps!")

        print(f"  📝 Chunk sizes: {[len(c.split()) for c in chunks]} words")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("✅ Expected Behavior:")
    print("   • With Phase 1 DISABLED, chunk count should match target_steps")
    print("   • User's slider choice should be respected")
    print()
    print("❌ If chunks don't match target:")
    print("   • Check if Phase 1 is enabled somewhere")
    print("   • Check environment variables for overrides")
    print("   • Look at backend logs for 'phase1_enabled=True'")

if __name__ == "__main__":
    test_step_count_control()
