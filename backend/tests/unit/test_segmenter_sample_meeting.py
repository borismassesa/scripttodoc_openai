"""
Test topic segmenter with sample_meeting.txt
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.transcript_parser import TranscriptParser
from script_to_doc.topic_segmenter import TopicSegmenter, SegmentationConfig


def main():
    """Segment sample_meeting.txt and display results."""

    # Load sample transcript
    sample_path = Path(__file__).parent.parent / "sample_data" / "transcripts" / "sample_meeting.txt"

    if not sample_path.exists():
        print(f"❌ Sample transcript not found: {sample_path}")
        return 1

    with open(sample_path, 'r') as f:
        raw_transcript = f.read()

    print("=" * 80)
    print("TOPIC SEGMENTATION: SAMPLE MEETING")
    print("=" * 80)
    print(f"\nInput: {len(raw_transcript)} characters\n")

    # Step 1: Parse transcript
    print("Step 1: Parsing transcript...")
    parser = TranscriptParser()
    parsed_sentences, metadata = parser.parse(raw_transcript)
    print(f"✓ Parsed {metadata.total_sentences} sentences from {metadata.total_speakers} speakers")
    print(f"  Duration: {metadata.duration_seconds}s ({metadata.duration_seconds//60:.0f}m {metadata.duration_seconds%60:.0f}s)")
    print(f"  Primary speaker: {metadata.primary_speaker} ({metadata.primary_speaker_ratio:.1%})")
    print()

    # Step 2: Segment into topics
    print("Step 2: Segmenting into topics...")
    segmenter = TopicSegmenter()
    segments = segmenter.segment(parsed_sentences, metadata)
    print(f"✓ Created {len(segments)} topic segments")
    print()

    # Display segments
    print("=" * 80)
    print(f"TOPIC SEGMENTS ({len(segments)} total)")
    print("=" * 80)

    for seg in segments:
        print()
        print(f"Segment {seg.segment_index + 1}: {len(seg.sentences)} sentences")
        print("-" * 80)

        # Metadata
        if seg.start_timestamp is not None:
            mins = int(seg.start_timestamp // 60)
            secs = int(seg.start_timestamp % 60)
            print(f"  Timestamp: {mins:02d}:{secs:02d}")

        if seg.duration_seconds:
            print(f"  Duration: {seg.duration_seconds:.0f}s")

        if seg.primary_speaker:
            print(f"  Primary speaker: {seg.primary_speaker}")

        print(f"  Characteristics:")
        print(f"    - Transition start: {seg.has_transition_start}")
        print(f"    - Has Q&A: {seg.has_qa_section}")
        print(f"    - Questions: {seg.question_count}")
        print(f"    - Coherence: {seg.coherence_score:.2f}")

        # Preview first 3 sentences
        print()
        print(f"  Preview:")
        for i, sent in enumerate(seg.sentences[:3], 1):
            if sent.timestamp:
                mins = int(sent.timestamp // 60)
                secs = int(sent.timestamp % 60)
                timestamp_str = f"[{mins:02d}:{secs:02d}]"
            else:
                timestamp_str = ""

            speaker_str = f"[{sent.speaker}]" if sent.speaker else ""
            text_preview = sent.text[:70] + "..." if len(sent.text) > 70 else sent.text

            print(f"    {i}. {timestamp_str} {speaker_str} {text_preview}")

        if len(seg.sentences) > 3:
            print(f"    ... ({len(seg.sentences) - 3} more sentences)")

    # Summary statistics
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_sentences = sum(len(seg.sentences) for seg in segments)
    avg_sentences_per_segment = total_sentences / len(segments) if segments else 0
    avg_coherence = sum(seg.coherence_score for seg in segments) / len(segments) if segments else 0

    segments_with_qa = sum(1 for seg in segments if seg.has_qa_section)
    segments_with_transition = sum(1 for seg in segments if seg.has_transition_start)

    print(f"Total segments: {len(segments)}")
    print(f"Avg sentences per segment: {avg_sentences_per_segment:.1f}")
    print(f"Avg coherence score: {avg_coherence:.2f}")
    print(f"Segments with Q&A: {segments_with_qa}")
    print(f"Segments with transitions: {segments_with_transition}")

    print()
    print("✅ TOPIC SEGMENTATION COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
