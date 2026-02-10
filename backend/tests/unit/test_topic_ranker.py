"""
Unit tests for Topic Ranker (Phase 2).

Tests importance scoring and ranking logic.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.topic_ranker import TopicRanker, RankingConfig, TopicScore
from script_to_doc.transcript_parser import ParsedSentence
from script_to_doc.topic_segmenter import TopicSegment


class TestRankingConfig:
    """Test RankingConfig validation and defaults."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = RankingConfig()
        assert config.weight_procedural == 0.4
        assert config.weight_action_density == 0.3
        assert config.weight_coherence == 0.3
        assert config.min_importance_threshold == 0.3
        assert len(config.action_verbs) > 0

    def test_custom_config(self):
        """Test custom configuration."""
        config = RankingConfig(
            weight_procedural=0.5,
            weight_action_density=0.3,
            weight_coherence=0.2,
            min_importance_threshold=0.5
        )
        assert config.weight_procedural == 0.5
        assert config.min_importance_threshold == 0.5

    def test_invalid_weights(self):
        """Test that weights not summing to 1.0 raise error."""
        try:
            RankingConfig(
                weight_procedural=0.5,
                weight_action_density=0.3,
                weight_coherence=0.3  # Sum = 1.1
            )
            assert False, "Should raise ValueError for weights not summing to 1.0"
        except ValueError as e:
            assert "must sum to 1.0" in str(e)


class TestTopicRanker:
    """Test TopicRanker initialization."""

    def test_initialization(self):
        """Test ranker initialization with default config."""
        ranker = TopicRanker()
        assert ranker.config.weight_procedural == 0.4
        assert ranker.config.weight_action_density == 0.3

    def test_initialization_with_custom_config(self):
        """Test ranker initialization with custom config."""
        config = RankingConfig(min_importance_threshold=0.5)
        ranker = TopicRanker(config)
        assert ranker.config.min_importance_threshold == 0.5


class TestProceduralScore:
    """Test procedural score computation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = TopicRanker()

    def test_procedural_score_high(self):
        """Test procedural score for highly procedural segment."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Navigate to the Azure portal.",
                    raw_text="Navigate to the Azure portal.",
                    sentence_index=0
                ),
                ParsedSentence(
                    text="Click on Resource Groups.",
                    raw_text="Click on Resource Groups.",
                    sentence_index=1
                ),
                ParsedSentence(
                    text="Select Create New.",
                    raw_text="Select Create New.",
                    sentence_index=2
                )
            ]
        )

        score = self.ranker._compute_procedural_score(segment)
        assert score > 0.6  # High procedural content

    def test_procedural_score_low(self):
        """Test procedural score for non-procedural segment."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="This is interesting.",
                    raw_text="This is interesting.",
                    sentence_index=0
                ),
                ParsedSentence(
                    text="I think we should discuss this.",
                    raw_text="I think we should discuss this.",
                    sentence_index=1
                )
            ]
        )

        score = self.ranker._compute_procedural_score(segment)
        assert score < 0.3  # Low procedural content

    def test_procedural_score_with_sequence_indicators(self):
        """Test that sequence indicators increase procedural score."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="First, navigate to the portal.",
                    raw_text="First, navigate to the portal.",
                    sentence_index=0
                ),
                ParsedSentence(
                    text="Next, click on the menu.",
                    raw_text="Next, click on the menu.",
                    sentence_index=1
                ),
                ParsedSentence(
                    text="Finally, select your option.",
                    raw_text="Finally, select your option.",
                    sentence_index=2
                )
            ]
        )

        score = self.ranker._compute_procedural_score(segment)
        assert score > 0.7  # Very high with sequence indicators

    def test_procedural_score_empty_segment(self):
        """Test procedural score with empty segment."""
        segment = TopicSegment(segment_index=0, sentences=[])
        score = self.ranker._compute_procedural_score(segment)
        assert score == 0.0


class TestActionDensity:
    """Test action density computation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = TopicRanker()

    def test_action_density_high(self):
        """Test action density for action-dense segment."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Click the button, then select the option, and configure the setting.",
                    raw_text="Click the button, then select the option, and configure the setting.",
                    sentence_index=0
                )
            ]
        )

        density = self.ranker._compute_action_density(segment)
        assert density > 0.5  # 3 actions in 1 sentence

    def test_action_density_low(self):
        """Test action density for segment with few actions."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="This is a discussion about the topic.",
                    raw_text="This is a discussion about the topic.",
                    sentence_index=0
                ),
                ParsedSentence(
                    text="We think it's important to consider.",
                    raw_text="We think it's important to consider.",
                    sentence_index=1
                )
            ]
        )

        density = self.ranker._compute_action_density(segment)
        assert density < 0.2  # Few/no actions

    def test_action_density_empty_segment(self):
        """Test action density with empty segment."""
        segment = TopicSegment(segment_index=0, sentences=[])
        density = self.ranker._compute_action_density(segment)
        assert density == 0.0


class TestScoreSegments:
    """Test segment scoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = TopicRanker()

    def test_score_single_segment(self):
        """Test scoring a single segment."""
        segment = TopicSegment(
            segment_index=0,
            sentences=[
                ParsedSentence(
                    text="Navigate to portal.", raw_text="Navigate to portal.",
                    sentence_index=0
                ),
                ParsedSentence(
                    text="Click Resource Groups.", raw_text="Click Resource Groups.",
                    sentence_index=1
                )
            ],
            coherence_score=0.5
        )

        scores = self.ranker.score_segments([segment])

        assert len(scores) == 1
        assert scores[0].segment_index == 0
        assert 0.0 <= scores[0].importance_score <= 1.0
        assert 0.0 <= scores[0].procedural_score <= 1.0
        assert 0.0 <= scores[0].action_density <= 1.0

    def test_score_multiple_segments(self):
        """Test scoring multiple segments."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Navigate to portal.", raw_text="Navigate", sentence_index=0)
                ],
                coherence_score=0.5
            ),
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="This is a discussion.", raw_text="Discussion", sentence_index=1)
                ],
                coherence_score=0.3
            )
        ]

        scores = self.ranker.score_segments(segments)

        assert len(scores) == 2
        assert scores[0].segment_index == 0
        assert scores[1].segment_index == 1
        # First segment (procedural) should score higher
        assert scores[0].importance_score > scores[1].importance_score

    def test_score_empty_list(self):
        """Test scoring empty segment list."""
        scores = self.ranker.score_segments([])
        assert len(scores) == 0


class TestRankByImportance:
    """Test ranking segments by importance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = TopicRanker()

    def test_rank_descending_order(self):
        """Test that segments are ranked in descending importance."""
        segments = [
            # Low importance (discussion)
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Let's discuss this.", raw_text="Discussion", sentence_index=0)
                ],
                coherence_score=0.3
            ),
            # High importance (procedural)
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Navigate to portal and click setup.", raw_text="Navigate", sentence_index=1)
                ],
                coherence_score=0.8
            ),
            # Medium importance
            TopicSegment(
                segment_index=2,
                sentences=[
                    ParsedSentence(text="Select the option.", raw_text="Select", sentence_index=2)
                ],
                coherence_score=0.5
            )
        ]

        ranked = self.ranker.rank_by_importance(segments)

        # Should be ordered: 1 (high), 2 (medium), 0 (low)
        assert ranked[0].segment_index == 1
        assert ranked[2].segment_index == 0

    def test_rank_empty_list(self):
        """Test ranking empty segment list."""
        ranked = self.ranker.rank_by_importance([])
        assert len(ranked) == 0


class TestFilterLowImportance:
    """Test filtering low-importance segments."""

    def setup_method(self):
        """Set up test fixtures."""
        config = RankingConfig(min_importance_threshold=0.4)
        self.ranker = TopicRanker(config)

    def test_filter_below_threshold(self):
        """Test that segments below threshold are filtered."""
        segments = [
            # High importance (should keep)
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Navigate to portal, click menu, select option.", raw_text="Nav", sentence_index=0)
                ],
                coherence_score=0.8
            ),
            # Low importance (should filter)
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Maybe we should think about this.", raw_text="Think", sentence_index=1)
                ],
                coherence_score=0.2
            )
        ]

        filtered = self.ranker.filter_low_importance(segments)

        # Should keep only high-importance segment
        assert len(filtered) == 1
        assert filtered[0].segment_index == 0

    def test_filter_custom_threshold(self):
        """Test filtering with custom threshold."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Navigate to portal.", raw_text="Navigate", sentence_index=0)
                ],
                coherence_score=0.5
            )
        ]

        # Use very high threshold
        filtered = self.ranker.filter_low_importance(segments, threshold=0.8)

        # Should filter out segment
        assert len(filtered) == 0

    def test_filter_keep_top_n(self):
        """Test keeping only top N segments."""
        config = RankingConfig(keep_top_n=2)
        ranker = TopicRanker(config)

        segments = [
            TopicSegment(segment_index=0, sentences=[ParsedSentence(text="A", raw_text="A", sentence_index=0)], coherence_score=0.3),
            TopicSegment(segment_index=1, sentences=[ParsedSentence(text="Navigate and click.", raw_text="B", sentence_index=1)], coherence_score=0.8),
            TopicSegment(segment_index=2, sentences=[ParsedSentence(text="Select option.", raw_text="C", sentence_index=2)], coherence_score=0.6),
            TopicSegment(segment_index=3, sentences=[ParsedSentence(text="D", raw_text="D", sentence_index=3)], coherence_score=0.2)
        ]

        filtered = ranker.filter_low_importance(segments)

        # Should keep only top 2
        assert len(filtered) <= 2


class TestRankingReport:
    """Test ranking report generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = TopicRanker()

    def test_get_ranking_report(self):
        """Test ranking report generation."""
        segments = [
            TopicSegment(
                segment_index=0,
                sentences=[
                    ParsedSentence(text="Navigate to portal.", raw_text="Navigate", sentence_index=0)
                ],
                coherence_score=0.8
            ),
            TopicSegment(
                segment_index=1,
                sentences=[
                    ParsedSentence(text="Discuss the topic.", raw_text="Discuss", sentence_index=1)
                ],
                coherence_score=0.3
            )
        ]

        report = self.ranker.get_ranking_report(segments)

        assert report["total_segments"] == 2
        assert len(report["scores"]) == 2
        assert "statistics" in report
        assert "avg_importance" in report["statistics"]
        assert "max_importance" in report["statistics"]
        assert "min_importance" in report["statistics"]

    def test_get_ranking_report_empty(self):
        """Test ranking report with empty segment list."""
        report = self.ranker.get_ranking_report([])

        assert report["total_segments"] == 0
        assert len(report["scores"]) == 0


def main():
    """Run Topic Ranker tests."""
    import pytest

    print("\n" + "=" * 80)
    print("TOPIC RANKER UNIT TESTS (Phase 2)")
    print("=" * 80)
    print()

    # Run tests
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL TOPIC RANKER TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
