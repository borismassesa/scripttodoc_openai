"""
Unit tests for Q&A Filter (Phase 2).

Tests Q&A section detection and filtering logic.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.qa_filter import QAFilter, FilterConfig, QASection
from script_to_doc.transcript_parser import ParsedSentence
from script_to_doc.topic_segmenter import TopicSegment


class TestFilterConfig:
    """Test FilterConfig validation and defaults."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = FilterConfig()
        assert config.min_qa_density == 0.30
        assert config.min_questions == 2
        assert config.filter_qa_sections is True
        assert config.keep_instructor_only is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = FilterConfig(
            min_qa_density=0.5,
            min_questions=3,
            filter_qa_sections=False
        )
        assert config.min_qa_density == 0.5
        assert config.min_questions == 3
        assert config.filter_qa_sections is False

    def test_invalid_qa_density(self):
        """Test that invalid Q&A density raises error."""
        try:
            FilterConfig(min_qa_density=1.5)
            assert False, "Should raise ValueError for density > 1.0"
        except ValueError as e:
            assert "min_qa_density" in str(e)

    def test_invalid_min_questions(self):
        """Test that negative min_questions raises error."""
        try:
            FilterConfig(min_questions=-1)
            assert False, "Should raise ValueError for negative min_questions"
        except ValueError as e:
            assert "min_questions" in str(e)


class TestQAFilter:
    """Test QAFilter initialization and basic methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = QAFilter()

    def test_initialization(self):
        """Test filter initialization with default config."""
        assert self.filter.config.min_qa_density == 0.30
        assert self.filter.config.filter_qa_sections is True

    def test_initialization_with_custom_config(self):
        """Test filter initialization with custom config."""
        config = FilterConfig(min_qa_density=0.5)
        qa_filter = QAFilter(config)
        assert qa_filter.config.min_qa_density == 0.5


class TestQADensityComputation:
    """Test Q&A density computation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = QAFilter()

    def test_compute_qa_density_all_questions(self):
        """Test Q&A density with all questions."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="What is Azure?", raw_text="What is Azure?",
                    sentence_index=0, is_question=True
                ),
                ParsedSentence(
                    text="How do I start?", raw_text="How do I start?",
                    sentence_index=1, is_question=True
                ),
                ParsedSentence(
                    text="Where is the portal?", raw_text="Where is the portal?",
                    sentence_index=2, is_question=True
                )
            ]
        )

        density = self.filter._compute_qa_density(segment)
        assert density == 1.0

    def test_compute_qa_density_no_questions(self):
        """Test Q&A density with no questions."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Navigate to Azure portal.", raw_text="Navigate to Azure portal.",
                    sentence_index=0, is_question=False
                ),
                ParsedSentence(
                    text="Click on Resource Groups.", raw_text="Click on Resource Groups.",
                    sentence_index=1, is_question=False
                )
            ]
        )

        density = self.filter._compute_qa_density(segment)
        assert density == 0.0

    def test_compute_qa_density_mixed(self):
        """Test Q&A density with mixed content."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="What is Azure?", raw_text="What is Azure?",
                    sentence_index=0, is_question=True
                ),
                ParsedSentence(
                    text="Azure is a cloud platform.", raw_text="Azure is a cloud platform.",
                    sentence_index=1, is_question=False
                ),
                ParsedSentence(
                    text="How do I start?", raw_text="How do I start?",
                    sentence_index=2, is_question=True
                ),
                ParsedSentence(
                    text="Navigate to the portal.", raw_text="Navigate to the portal.",
                    sentence_index=3, is_question=False
                )
            ]
        )

        density = self.filter._compute_qa_density(segment)
        assert density == 0.5

    def test_compute_qa_density_empty_segment(self):
        """Test Q&A density with empty segment."""
        segment = TopicSegment(segment_index=0, sentences=[])
        density = self.filter._compute_qa_density(segment)
        assert density == 0.0


class TestQASectionIdentification:
    """Test Q&A section identification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = QAFilter()

    def test_identify_qa_section_high_density(self):
        """Test identification of Q&A section with high density."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(
                        text="What is Azure?", raw_text="What is Azure?",
                        sentence_index=0, is_question=True, speaker="Student"
                    ),
                    ParsedSentence(
                        text="Azure is a cloud platform.", raw_text="Azure is a cloud platform.",
                        sentence_index=1, is_question=False, speaker="Instructor"
                    ),
                    ParsedSentence(
                        text="How do I start?", raw_text="How do I start?",
                        sentence_index=2, is_question=True, speaker="Student"
                    ),
                    ParsedSentence(
                        text="Go to portal.azure.com.", raw_text="Go to portal.azure.com.",
                        sentence_index=3, is_question=False, speaker="Instructor"
                    )
                ],
                primary_speaker="Instructor"
            )
        ]

        qa_sections = self.filter.identify_qa_sections(segments)

        assert len(qa_sections) == 1
        assert qa_sections[0].segment_index == 0
        assert qa_sections[0].question_count == 2
        assert qa_sections[0].qa_density == 0.5
        assert qa_sections[0].is_qa_dense is True

    def test_identify_qa_section_low_density(self):
        """Test that low density segments are not identified as Q&A."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(
                        text="What is Azure?", raw_text="What is Azure?",
                        sentence_index=0, is_question=True
                    ),
                    ParsedSentence(
                        text="Azure is a cloud platform.", raw_text="Azure is a cloud platform.",
                        sentence_index=1, is_question=False
                    ),
                    ParsedSentence(
                        text="Navigate to the portal.", raw_text="Navigate to the portal.",
                        sentence_index=2, is_question=False
                    ),
                    ParsedSentence(
                        text="Click on Resource Groups.", raw_text="Click on Resource Groups.",
                        sentence_index=3, is_question=False
                    ),
                    ParsedSentence(
                        text="Select your subscription.", raw_text="Select your subscription.",
                        sentence_index=4, is_question=False
                    )
                ]
            )
        ]

        qa_sections = self.filter.identify_qa_sections(segments)

        # 1/5 = 20% < 30% threshold
        assert len(qa_sections) == 0

    def test_identify_multiple_qa_sections(self):
        """Test identification of multiple Q&A sections."""
        segments = [
            # Procedural segment
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Step 1", raw_text="Step 1", sentence_index=0, is_question=False),
                    ParsedSentence(text="Step 2", raw_text="Step 2", sentence_index=1, is_question=False)
                ]
            ),
            # Q&A segment
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Question 1?", raw_text="Q1", sentence_index=2, is_question=True),
                    ParsedSentence(text="Answer 1", raw_text="A1", sentence_index=3, is_question=False),
                    ParsedSentence(text="Question 2?", raw_text="Q2", sentence_index=4, is_question=True)
                ]
            ),
            # Another procedural segment
            TopicSegment(
                segment_index=2,
                sentences=[
                    ParsedSentence(text="Step 3", raw_text="Step 3", sentence_index=5, is_question=False),
                    ParsedSentence(text="Step 4", raw_text="Step 4", sentence_index=6, is_question=False)
                ]
            ),
            # Another Q&A segment
            TopicSegment(
                segment_index=3,
                sentences=[
                    ParsedSentence(text="Question 3?", raw_text="Q3", sentence_index=7, is_question=True),
                    ParsedSentence(text="Question 4?", raw_text="Q4", sentence_index=8, is_question=True),
                    ParsedSentence(text="Answer", raw_text="Answer", sentence_index=9, is_question=False)
                ]
            )
        ]

        qa_sections = self.filter.identify_qa_sections(segments)

        assert len(qa_sections) == 2
        assert qa_sections[0].segment_index == 1
        assert qa_sections[1].segment_index == 3


class TestSegmentFiltering:
    """Test segment filtering logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = QAFilter()

    def test_filter_segments_removes_qa(self):
        """Test that Q&A segments are filtered out."""
        segments = [
            # Procedural
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Step 1", raw_text="Step 1", sentence_index=0, is_question=False),
                    ParsedSentence(text="Step 2", raw_text="Step 2", sentence_index=1, is_question=False)
                ]
            ),
            # Q&A (should be filtered)
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Question?", raw_text="Question?", sentence_index=2, is_question=True),
                    ParsedSentence(text="Answer", raw_text="Answer", sentence_index=3, is_question=False),
                    ParsedSentence(text="Question 2?", raw_text="Question 2?", sentence_index=4, is_question=True)
                ]
            ),
            # Procedural
            TopicSegment(
                segment_index=2,
                sentences=[
                    ParsedSentence(text="Step 3", raw_text="Step 3", sentence_index=5, is_question=False),
                    ParsedSentence(text="Step 4", raw_text="Step 4", sentence_index=6, is_question=False)
                ]
            )
        ]

        filtered = self.filter.filter_segments(segments)

        assert len(filtered) == 2
        assert filtered[0].segment_index == 0
        assert filtered[1].segment_index == 2

    def test_filter_segments_disabled(self):
        """Test that filtering can be disabled."""
        config = FilterConfig(filter_qa_sections=False)
        qa_filter = QAFilter(config)

        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Question?", raw_text="Question?", sentence_index=0, is_question=True),
                    ParsedSentence(text="Answer", raw_text="Answer", sentence_index=1, is_question=False),
                    ParsedSentence(text="Question 2?", raw_text="Question 2?", sentence_index=2, is_question=True)
                ]
            )
        ]

        filtered = qa_filter.filter_segments(segments)

        # Should not filter when disabled
        assert len(filtered) == 1

    def test_filter_segments_empty_input(self):
        """Test filtering with empty segment list."""
        filtered = self.filter.filter_segments([])
        assert len(filtered) == 0

    def test_filter_segments_no_qa(self):
        """Test filtering when no Q&A sections exist."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Step 1", raw_text="Step 1", sentence_index=0, is_question=False),
                    ParsedSentence(text="Step 2", raw_text="Step 2", sentence_index=1, is_question=False)
                ]
            ),
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Step 3", raw_text="Step 3", sentence_index=2, is_question=False),
                    ParsedSentence(text="Step 4", raw_text="Step 4", sentence_index=3, is_question=False)
                ]
            )
        ]

        filtered = self.filter.filter_segments(segments)

        # Should keep all segments
        assert len(filtered) == 2


class TestInstructorFiltering:
    """Test instructor-only filtering."""

    def setup_method(self):
        """Set up test fixtures."""
        config = FilterConfig(keep_instructor_only=True)
        self.filter = QAFilter(config)

    def test_keep_instructor_led_segment(self):
        """Test that instructor-led segments are kept."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(
                        text="Navigate to portal.", raw_text="Navigate to portal.",
                        sentence_index=0, is_question=False,
                        speaker="Instructor", speaker_role="instructor"
                    ),
                    ParsedSentence(
                        text="Click Resource Groups.", raw_text="Click Resource Groups.",
                        sentence_index=1, is_question=False,
                        speaker="Instructor", speaker_role="instructor"
                    )
                ],
                primary_speaker="Instructor"
            )
        ]

        filtered = self.filter.filter_segments(segments)
        assert len(filtered) == 1

    def test_filter_participant_led_segment(self):
        """Test that participant-led segments are filtered."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(
                        text="I think we should...", raw_text="I think we should...",
                        sentence_index=0, is_question=False,
                        speaker="Participant", speaker_role="participant"
                    ),
                    ParsedSentence(
                        text="Maybe try this?", raw_text="Maybe try this?",
                        sentence_index=1, is_question=True,
                        speaker="Participant", speaker_role="participant"
                    )
                ],
                primary_speaker="Participant"
            )
        ]

        filtered = self.filter.filter_segments(segments)
        assert len(filtered) == 0


class TestStatistics:
    """Test statistics computation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = QAFilter()

    def test_get_statistics(self):
        """Test statistics computation."""
        segments = [
            # Procedural
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Step 1", raw_text="Step 1", sentence_index=0, is_question=False),
                    ParsedSentence(text="Step 2", raw_text="Step 2", sentence_index=1, is_question=False)
                ]
            ),
            # Q&A
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Question?", raw_text="Question?", sentence_index=2, is_question=True),
                    ParsedSentence(text="Answer", raw_text="Answer", sentence_index=3, is_question=False),
                    ParsedSentence(text="Question 2?", raw_text="Question 2?", sentence_index=4, is_question=True)
                ]
            )
        ]

        stats = self.filter.get_statistics(segments)

        assert stats["total_segments"] == 2
        assert stats["qa_segments"] == 1
        assert stats["filtered_segments"] == 1
        assert stats["removed_segments"] == 1
        assert stats["total_questions"] == 2
        assert stats["total_sentences"] == 5
        assert stats["overall_qa_density"] == 0.4
        assert stats["filter_rate"] == 0.5


def main():
    """Run Q&A Filter tests."""
    import pytest

    print("\n" + "=" * 80)
    print("Q&A FILTER UNIT TESTS (Phase 2)")
    print("=" * 80)
    print()

    # Run tests
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL Q&A FILTER TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
