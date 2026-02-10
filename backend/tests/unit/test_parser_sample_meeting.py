"""
Test transcript parser with sample_meeting.txt
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.transcript_parser import TranscriptParser


def main():
    """Parse and display sample_meeting.txt."""

    # Load sample transcript
    sample_path = Path(__file__).parent.parent / "sample_data" / "transcripts" / "sample_meeting.txt"

    if not sample_path.exists():
        print(f"❌ Sample transcript not found: {sample_path}")
        return 1

    with open(sample_path, 'r') as f:
        raw_transcript = f.read()

    print("=" * 80)
    print("PARSING SAMPLE MEETING TRANSCRIPT")
    print("=" * 80)
    print(f"\nInput: {len(raw_transcript)} characters\n")

    # Parse transcript
    parser = TranscriptParser()
    parsed_sentences, metadata = parser.parse(raw_transcript)

    # Display metadata
    print("=" * 80)
    print("TRANSCRIPT METADATA")
    print("=" * 80)
    print(f"Total sentences: {metadata.total_sentences}")
    print(f"Total speakers: {metadata.total_speakers}")
    print(f"Speaker names: {', '.join(metadata.speaker_names)}")
    print(f"Duration: {metadata.duration_seconds}s ({metadata.duration_seconds//60:.0f}m {metadata.duration_seconds%60:.0f}s)")
    print(f"Has timestamps: {metadata.has_timestamps}")
    print(f"Primary speaker: {metadata.primary_speaker} ({metadata.primary_speaker_ratio:.1%})")
    print(f"Has Q&A sections: {metadata.has_qa_sections}")
    print(f"Question count: {metadata.question_count}")
    print(f"Transition count: {metadata.transition_count}")
    print()

    # Display parsed sentences
    print("=" * 80)
    print(f"PARSED SENTENCES ({len(parsed_sentences)} total)")
    print("=" * 80)

    for i, sent in enumerate(parsed_sentences[:10], 1):  # Show first 10
        print(f"\n{i}. {sent}")
        print(f"   Speaker: {sent.speaker} ({sent.speaker_role})")
        if sent.timestamp:
            mins = int(sent.timestamp // 60)
            secs = int(sent.timestamp % 60)
            print(f"   Timestamp: {mins:02d}:{secs:02d}")

        characteristics = []
        if sent.is_question:
            characteristics.append("Question")
        if sent.is_transition:
            characteristics.append("Transition")
        if sent.has_emphasis:
            characteristics.append("Emphasis")
        if sent.follows_long_pause:
            characteristics.append("After Long Pause")
        if sent.speaker_changed:
            characteristics.append("Speaker Changed")

        if characteristics:
            print(f"   Characteristics: {', '.join(characteristics)}")

    if len(parsed_sentences) > 10:
        print(f"\n... ({len(parsed_sentences) - 10} more sentences)")

    # Display questions
    print("\n" + "=" * 80)
    print("QUESTIONS")
    print("=" * 80)

    questions = [s for s in parsed_sentences if s.is_question]
    for q in questions:
        print(f"- [{q.speaker}] {q.text}")

    # Display transitions
    print("\n" + "=" * 80)
    print("TRANSITIONS")
    print("=" * 80)

    transitions = [s for s in parsed_sentences if s.is_transition]
    for t in transitions:
        mins = int(t.timestamp // 60) if t.timestamp else 0
        secs = int(t.timestamp % 60) if t.timestamp else 0
        print(f"- [{mins:02d}:{secs:02d}] [{t.speaker}] {t.text}")

    # Display speaker changes
    print("\n" + "=" * 80)
    print("SPEAKER CHANGES")
    print("=" * 80)

    changes = [s for s in parsed_sentences if s.speaker_changed]
    for c in changes[:5]:  # Show first 5
        prev_idx = c.sentence_index - 1
        if prev_idx >= 0:
            prev = parsed_sentences[prev_idx]
            print(f"- {prev.speaker} → {c.speaker}")
            print(f"  Before: {prev.text[:60]}...")
            print(f"  After:  {c.text[:60]}...")
            print()

    if len(changes) > 5:
        print(f"... ({len(changes) - 5} more speaker changes)")

    print("\n" + "=" * 80)
    print("✅ PARSER TEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
