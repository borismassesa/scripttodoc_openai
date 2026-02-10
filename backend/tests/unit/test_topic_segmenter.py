"""
Unit tests for topic segmentation.
Tests boundary detection, segment creation, and quality metrics.
"""

import pytest
from script_to_doc.topic_segmenter import (
    TopicSegmenter,
    TopicSegment,
    SegmentationConfig
)
from script_to_doc.transcript_parser import ParsedSentence, TranscriptMetadata


class TestSegmentationConfig:
    """Test segmentation configuration validation."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = SegmentationConfig()
        assert config.weight_timestamp_gap == 0.35
        assert config.weight_speaker_transition == 0.25
        assert config.weight_transition_phrase == 0.30
        assert config.weight_semantic_similarity == 0.10
        assert config.boundary_score_threshold == 0.40

    def test_custom_config(self):
        """Test custom configuration."""
        config = SegmentationConfig(
            weight_timestamp_gap=0.4,
            weight_speaker_transition=0.3,
            weight_transition_phrase=0.2,
            weight_semantic_similarity=0.1,
            boundary_score_threshold=0.6
        )
        assert config.weight_timestamp_gap == 0.4
        assert config.boundary_score_threshold == 0.6

    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            SegmentationConfig(
                weight_timestamp_gap=0.5,
                weight_speaker_transition=0.5,
                weight_transition_phrase=0.5,
                weight_semantic_similarity=0.5
            )

    def test_invalid_threshold(self):
        """Test that boundary threshold must be 0.0-1.0."""
        with pytest.raises(ValueError, match="boundary_score_threshold must be 0.0-1.0"):
            SegmentationConfig(boundary_score_threshold=1.5)


class TestTopicSegment:
    """Test TopicSegment dataclass and metadata computation."""

    def test_empty_segment(self):
        """Test segment with no sentences."""
        segment = TopicSegment(segment_index=0, sentences=[])
        assert segment.start_timestamp is None
        assert segment.duration_seconds is None
        assert segment.primary_speaker is None

    def test_segment_with_timestamps(self):
        """Test segment metadata extraction with timestamps."""
        sentences = [
            ParsedSentence(
                text="First sentence",
                raw_text="[00:00:05] Speaker 1: First sentence",
                sentence_index=0,
                timestamp=5.0,
                speaker="Speaker 1",
                speaker_role="instructor"
            ),
            ParsedSentence(
                text="Second sentence",
                raw_text="[00:00:15] Speaker 1: Second sentence",
                sentence_index=1,
                timestamp=15.0,
                speaker="Speaker 1",
                speaker_role="instructor"
            ),
            ParsedSentence(
                text="Third sentence",
                raw_text="[00:00:25] Speaker 1: Third sentence",
                sentence_index=2,
                timestamp=25.0,
                speaker="Speaker 1",
                speaker_role="instructor"
            )
        ]

        segment = TopicSegment(segment_index=0, sentences=sentences)

        assert segment.start_timestamp == 5.0
        assert segment.end_timestamp == 25.0
        assert segment.duration_seconds == 20.0
        assert segment.primary_speaker == "Speaker 1"
        assert len(segment.sentences) == 3

    def test_segment_with_multiple_speakers(self):
        """Test primary speaker detection with multiple speakers."""
        sentences = [
            ParsedSentence(
                text="First", raw_text="First", sentence_index=0,
                speaker="Speaker 1", speaker_role="instructor"
            ),
            ParsedSentence(
                text="Second", raw_text="Second", sentence_index=1,
                speaker="Speaker 1", speaker_role="instructor"
            ),
            ParsedSentence(
                text="Question?", raw_text="Question?", sentence_index=2,
                speaker="Speaker 2", speaker_role="participant",
                is_question=True
            )
        ]

        segment = TopicSegment(segment_index=0, sentences=sentences)

        assert segment.primary_speaker == "Speaker 1"
        assert segment.speaker_counts["Speaker 1"] == 2
        assert segment.speaker_counts["Speaker 2"] == 1

    def test_segment_with_transition_start(self):
        """Test detection of transition at segment start."""
        sentences = [
            ParsedSentence(
                text="Now let's move on",
                raw_text="Now let's move on",
                sentence_index=0,
                is_transition=True
            ),
            ParsedSentence(
                text="Next sentence",
                raw_text="Next sentence",
                sentence_index=1
            )
        ]

        segment = TopicSegment(segment_index=0, sentences=sentences)
        assert segment.has_transition_start is True

    def test_segment_with_qa_section(self):
        """Test detection of Q&A section."""
        sentences = [
            ParsedSentence(
                text="Instructor speaking",
                raw_text="Instructor speaking",
                sentence_index=0,
                speaker="Speaker 1",
                speaker_role="instructor"
            ),
            ParsedSentence(
                text="Can you explain this?",
                raw_text="Can you explain this?",
                sentence_index=1,
                speaker="Speaker 2",
                speaker_role="participant",
                is_question=True
            )
        ]

        segment = TopicSegment(segment_index=0, sentences=sentences)
        assert segment.has_qa_section is True
        assert segment.question_count == 1

    def test_segment_get_text(self):
        """Test get_text() method."""
        sentences = [
            ParsedSentence(text="First sentence", raw_text="First", sentence_index=0),
            ParsedSentence(text="Second sentence", raw_text="Second", sentence_index=1),
            ParsedSentence(text="Third sentence", raw_text="Third", sentence_index=2)
        ]

        segment = TopicSegment(segment_index=0, sentences=sentences)
        text = segment.get_text()

        assert text == "First sentence Second sentence Third sentence"


class TestBoundaryDetection:
    """Test topic boundary detection logic."""

    def setup_method(self):
        self.segmenter = TopicSegmenter()

    def test_timestamp_gap_score(self):
        """Test timestamp gap scoring."""
        prev_sent = ParsedSentence(
            text="First", raw_text="First", sentence_index=0,
            timestamp=5.0
        )
        curr_sent = ParsedSentence(
            text="Second", raw_text="Second", sentence_index=1,
            timestamp=100.0,  # 95 second gap
            follows_long_pause=True
        )

        score = self.segmenter._compute_timestamp_gap_score(prev_sent, curr_sent)
        assert score == 1.0  # Long pause = max score

    def test_timestamp_gap_score_no_timestamps(self):
        """Test timestamp gap scoring without timestamps."""
        prev_sent = ParsedSentence(text="First", raw_text="First", sentence_index=0)
        curr_sent = ParsedSentence(text="Second", raw_text="Second", sentence_index=1)

        score = self.segmenter._compute_timestamp_gap_score(prev_sent, curr_sent)
        assert score == 0.0

    def test_speaker_transition_score_instructor_resume(self):
        """Test high score when instructor resumes after participant."""
        prev_sent = ParsedSentence(
            text="Question?", raw_text="Question?", sentence_index=0,
            speaker="Speaker 2", speaker_role="participant"
        )
        curr_sent = ParsedSentence(
            text="Good question", raw_text="Good question", sentence_index=1,
            speaker="Speaker 1", speaker_role="instructor",
            speaker_changed=True
        )

        score = self.segmenter._compute_speaker_transition_score(prev_sent, curr_sent)
        assert score == 1.0

    def test_speaker_transition_score_with_transition_phrase(self):
        """Test speaker change + transition phrase."""
        prev_sent = ParsedSentence(
            text="Previous", raw_text="Previous", sentence_index=0,
            speaker="Speaker 1"
        )
        curr_sent = ParsedSentence(
            text="Now let's move on", raw_text="Now let's move on", sentence_index=1,
            speaker="Speaker 2", speaker_changed=True, is_transition=True
        )

        score = self.segmenter._compute_speaker_transition_score(prev_sent, curr_sent)
        assert score == 0.8

    def test_speaker_transition_score_no_change(self):
        """Test no score when speaker doesn't change."""
        prev_sent = ParsedSentence(
            text="First", raw_text="First", sentence_index=0,
            speaker="Speaker 1"
        )
        curr_sent = ParsedSentence(
            text="Second", raw_text="Second", sentence_index=1,
            speaker="Speaker 1", speaker_changed=False
        )

        score = self.segmenter._compute_speaker_transition_score(prev_sent, curr_sent)
        assert score == 0.0

    def test_transition_phrase_score(self):
        """Test transition phrase detection."""
        sent_with_transition = ParsedSentence(
            text="Now let's move on", raw_text="Now let's move on",
            sentence_index=0, is_transition=True
        )
        sent_without_transition = ParsedSentence(
            text="Regular sentence", raw_text="Regular sentence",
            sentence_index=1, is_transition=False
        )

        score1 = self.segmenter._compute_transition_phrase_score(sent_with_transition)
        score2 = self.segmenter._compute_transition_phrase_score(sent_without_transition)

        assert score1 == 1.0
        assert score2 == 0.0

    def test_semantic_similarity_score(self):
        """Test semantic similarity scoring (keyword overlap)."""
        config = SegmentationConfig(use_semantic_similarity=True)
        segmenter = TopicSegmenter(config)

        # Similar sentences (shared keywords: azure, portal)
        prev_sent = ParsedSentence(
            text="Configure Azure portal settings",
            raw_text="Configure Azure portal settings",
            sentence_index=0
        )
        curr_sent = ParsedSentence(
            text="Azure portal configuration complete",
            raw_text="Azure portal configuration complete",
            sentence_index=1
        )

        score = segmenter._compute_semantic_similarity_score(prev_sent, curr_sent)
        # Moderate similarity (Jaccard ~0.33) = moderate boundary score (~0.67)
        assert 0.5 < score < 0.8

    def test_semantic_similarity_score_dissimilar(self):
        """Test semantic similarity with dissimilar sentences."""
        config = SegmentationConfig(use_semantic_similarity=True)
        segmenter = TopicSegmenter(config)

        # Dissimilar sentences (no shared keywords)
        prev_sent = ParsedSentence(
            text="Configure Azure portal settings",
            raw_text="Configure Azure portal settings",
            sentence_index=0
        )
        curr_sent = ParsedSentence(
            text="Deploy Python application code",
            raw_text="Deploy Python application code",
            sentence_index=1
        )

        score = segmenter._compute_semantic_similarity_score(prev_sent, curr_sent)
        assert score > 0.5  # Low similarity = high boundary score

    def test_is_topic_boundary_above_threshold(self):
        """Test boundary detection with score above threshold."""
        sent = ParsedSentence(text="Test", raw_text="Test", sentence_index=0)

        # Default threshold is 0.4 (score must be > 0.4)
        assert self.segmenter._is_topic_boundary(0.5, sent) is True
        assert self.segmenter._is_topic_boundary(0.3, sent) is False
        assert self.segmenter._is_topic_boundary(0.4, sent) is False  # Equal to threshold = False

    def test_is_topic_boundary_long_pause_override(self):
        """Test that long pause always creates boundary."""
        sent = ParsedSentence(
            text="Test", raw_text="Test", sentence_index=0,
            follows_long_pause=True, timestamp=100.0
        )

        # Even with low score, long pause creates boundary
        assert self.segmenter._is_topic_boundary(0.1, sent) is True


class TestSegmentation:
    """Test full segmentation workflow."""

    def test_single_sentence(self):
        """Test segmentation with single sentence."""
        sentences = [
            ParsedSentence(text="Only sentence", raw_text="Only", sentence_index=0)
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        assert len(segments) == 1
        assert len(segments[0].sentences) == 1

    def test_no_boundaries(self):
        """Test segmentation with no strong boundaries."""
        sentences = [
            ParsedSentence(
                text=f"Sentence {i}", raw_text=f"Sentence {i}",
                sentence_index=i, timestamp=float(i * 5),
                speaker="Speaker 1"
            )
            for i in range(5)
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        # Should create single segment (no strong boundaries)
        assert len(segments) == 1
        assert len(segments[0].sentences) == 5

    def test_clear_timestamp_boundary(self):
        """Test segmentation with clear timestamp gap."""
        sentences = [
            ParsedSentence(
                text="First topic sentence 1", raw_text="First 1",
                sentence_index=0, timestamp=5.0, speaker="Speaker 1"
            ),
            ParsedSentence(
                text="First topic sentence 2", raw_text="First 2",
                sentence_index=1, timestamp=10.0, speaker="Speaker 1"
            ),
            ParsedSentence(
                text="First topic sentence 3", raw_text="First 3",
                sentence_index=2, timestamp=15.0, speaker="Speaker 1"
            ),
            # Large gap (100 seconds)
            ParsedSentence(
                text="Second topic sentence 1", raw_text="Second 1",
                sentence_index=3, timestamp=115.0, speaker="Speaker 1",
                follows_long_pause=True
            ),
            ParsedSentence(
                text="Second topic sentence 2", raw_text="Second 2",
                sentence_index=4, timestamp=120.0, speaker="Speaker 1"
            )
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        assert len(segments) == 2
        assert len(segments[0].sentences) == 3
        assert len(segments[1].sentences) == 2

    def test_transition_phrase_boundary(self):
        """Test segmentation with transition phrase."""
        sentences = [
            ParsedSentence(
                text="First topic here", raw_text="First",
                sentence_index=0, speaker="Speaker 1"
            ),
            ParsedSentence(
                text="More about first topic", raw_text="More",
                sentence_index=1, speaker="Speaker 1"
            ),
            ParsedSentence(
                text="Ending first topic", raw_text="Ending",
                sentence_index=2, speaker="Speaker 1"
            ),
            ParsedSentence(
                text="Now let's move on to the next topic",
                raw_text="Now let's move on",
                sentence_index=3, speaker="Speaker 1",
                is_transition=True
            ),
            ParsedSentence(
                text="Second topic content", raw_text="Second",
                sentence_index=4, speaker="Speaker 1"
            )
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        assert len(segments) == 2
        assert segments[1].has_transition_start is True

    def test_speaker_transition_boundary(self):
        """Test segmentation with instructor resuming after Q&A."""
        sentences = [
            ParsedSentence(
                text="Teaching first topic", raw_text="Teaching",
                sentence_index=0,
                speaker="Speaker 1", speaker_role="instructor"
            ),
            ParsedSentence(
                text="More about first topic", raw_text="More",
                sentence_index=1,
                speaker="Speaker 1", speaker_role="instructor"
            ),
            ParsedSentence(
                text="Still on first topic", raw_text="Still",
                sentence_index=2,
                speaker="Speaker 1", speaker_role="instructor"
            ),
            # Participant question
            ParsedSentence(
                text="Can you explain this?", raw_text="Question",
                sentence_index=3,
                speaker="Speaker 2", speaker_role="participant",
                speaker_changed=True, is_question=True
            ),
            # Instructor resumes = new topic
            ParsedSentence(
                text="Good question. Now let's move to deployment",
                raw_text="Good question",
                sentence_index=4,
                speaker="Speaker 1", speaker_role="instructor",
                speaker_changed=True, is_transition=True
            ),
            ParsedSentence(
                text="Second topic content", raw_text="Second",
                sentence_index=5,
                speaker="Speaker 1", speaker_role="instructor"
            )
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        # Should create boundary when instructor resumes with transition
        assert len(segments) >= 2

    def test_merge_small_segments(self):
        """Test merging of small segments."""
        config = SegmentationConfig(
            min_segment_sentences=3,  # Custom: require 3 sentences minimum
            merge_small_segments=True
        )
        segmenter = TopicSegmenter(config)

        sentences = [
            # First segment: 3 sentences (OK)
            ParsedSentence(text="A1", raw_text="A1", sentence_index=0),
            ParsedSentence(text="A2", raw_text="A2", sentence_index=1),
            ParsedSentence(text="A3", raw_text="A3", sentence_index=2),
            # Second segment: 2 sentences (too small with min=3)
            ParsedSentence(
                text="Now let's move on", raw_text="B1",
                sentence_index=3, is_transition=True
            ),
            ParsedSentence(text="B2", raw_text="B2", sentence_index=4),
            # Third segment: 3 sentences (OK)
            ParsedSentence(
                text="Next topic", raw_text="C1",
                sentence_index=5, is_transition=True
            ),
            ParsedSentence(text="C2", raw_text="C2", sentence_index=6),
            ParsedSentence(text="C3", raw_text="C3", sentence_index=7)
        ]

        segments = segmenter.segment(sentences)

        # Should merge second segment into first (2 < 3)
        assert len(segments) == 2  # Not 3
        assert len(segments[0].sentences) == 5  # 3 + 2
        assert len(segments[1].sentences) == 3

    def test_no_merge_when_disabled(self):
        """Test that merging can be disabled."""
        config = SegmentationConfig(
            min_segment_sentences=3,  # Would normally merge segments < 3
            merge_small_segments=False  # But merging is disabled
        )
        segmenter = TopicSegmenter(config)

        sentences = [
            ParsedSentence(text="A1", raw_text="A1", sentence_index=0),
            ParsedSentence(text="A2", raw_text="A2", sentence_index=1),
            ParsedSentence(text="A3", raw_text="A3", sentence_index=2),
            ParsedSentence(
                text="Now let's move on", raw_text="B1",
                sentence_index=3, is_transition=True
            ),
            ParsedSentence(text="B2", raw_text="B2", sentence_index=4)
        ]

        segments = segmenter.segment(sentences)

        # Should NOT merge (merging disabled)
        assert len(segments) == 2
        assert len(segments[0].sentences) == 3
        assert len(segments[1].sentences) == 2


class TestSegmentMetrics:
    """Test segment quality metrics computation."""

    def test_coherence_score_single_sentence(self):
        """Test coherence for single-sentence segment."""
        segmenter = TopicSegmenter()

        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(text="Only sentence", raw_text="Only", sentence_index=0)
            ]
        )

        score = segmenter._compute_segment_coherence(segment)
        assert score == 1.0  # Single sentence is perfectly coherent

    def test_coherence_score_similar_sentences(self):
        """Test coherence for similar sentences."""
        segmenter = TopicSegmenter()

        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Configure Azure portal settings",
                    raw_text="Configure", sentence_index=0
                ),
                ParsedSentence(
                    text="Azure portal configuration requires authentication",
                    raw_text="Azure", sentence_index=1
                ),
                ParsedSentence(
                    text="Complete portal setup with authentication",
                    raw_text="Complete", sentence_index=2
                )
            ]
        )

        score = segmenter._compute_segment_coherence(segment)
        assert score > 0.2  # Should have decent coherence (shared keywords: portal, authentication)

    def test_coherence_score_dissimilar_sentences(self):
        """Test coherence for dissimilar sentences."""
        segmenter = TopicSegmenter()

        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Configure Azure portal settings",
                    raw_text="Configure", sentence_index=0
                ),
                ParsedSentence(
                    text="Deploy Python application code",
                    raw_text="Deploy", sentence_index=1
                ),
                ParsedSentence(
                    text="Create storage container bucket",
                    raw_text="Create", sentence_index=2
                )
            ]
        )

        score = segmenter._compute_segment_coherence(segment)
        assert score < 0.5  # Should have low coherence (different topics)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_sentence_list(self):
        """Test segmentation with empty input."""
        segmenter = TopicSegmenter()
        segments = segmenter.segment([])

        assert len(segments) == 0

    def test_all_sentences_identical(self):
        """Test segmentation with identical sentences."""
        sentences = [
            ParsedSentence(
                text="Same sentence", raw_text="Same",
                sentence_index=i, speaker="Speaker 1"
            )
            for i in range(5)
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        # Should create single segment (no boundaries)
        assert len(segments) == 1

    def test_missing_all_metadata(self):
        """Test segmentation with sentences missing all metadata."""
        sentences = [
            ParsedSentence(text=f"Sentence {i}", raw_text=f"Sent {i}", sentence_index=i)
            for i in range(5)
        ]

        segmenter = TopicSegmenter()
        segments = segmenter.segment(sentences)

        # Should still work (fall back to transition phrases)
        assert len(segments) >= 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
