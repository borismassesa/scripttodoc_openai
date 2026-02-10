"""
Topic Ranker: Ranks topic segments by procedural importance.

Phase 2 Component - Builds on Phase 1's topic segmentation.
Scores segments based on action density, coherence, and procedural indicators.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging
import re

# Import Phase 1 components
from .topic_segmenter import TopicSegment
from .transcript_parser import ParsedSentence

logger = logging.getLogger(__name__)


@dataclass
class TopicScore:
    """
    Importance score for a topic segment.

    Scores are 0.0-1.0, with higher = more important/procedural.
    """
    segment_index: int
    importance_score: float       # Combined score (0.0-1.0)
    procedural_score: float       # How procedural is this segment
    action_density: float         # Actions per sentence
    coherence_score: float        # Topic coherence (from segmenter)

    # Score breakdown (for debugging)
    weighted_procedural: float = 0.0
    weighted_action_density: float = 0.0
    weighted_coherence: float = 0.0


@dataclass
class RankingConfig:
    """Configuration for topic ranking."""

    # Scoring weights (must sum to 1.0)
    weight_procedural: float = 0.4      # Procedural indicators (action verbs, sequence)
    weight_action_density: float = 0.3  # Actions per sentence
    weight_coherence: float = 0.3       # Topic coherence

    # Filtering thresholds
    min_importance_threshold: float = 0.3  # Filter segments below this score
    keep_top_n: Optional[int] = None       # Keep only top N segments (None = keep all)

    # Procedural detection
    action_verbs: List[str] = None  # Initialized in __post_init__
    sequence_indicators: List[str] = None  # Initialized in __post_init__

    def __post_init__(self):
        """Initialize default action verbs and sequence indicators."""
        if self.action_verbs is None:
            self.action_verbs = [
                # Navigation
                "navigate", "go", "open", "access", "visit", "browse",
                # Interaction
                "click", "select", "choose", "press", "tap", "hit",
                # Input
                "type", "enter", "input", "fill", "write", "paste",
                # Configuration
                "configure", "set", "enable", "disable", "change", "modify",
                "adjust", "update", "edit",
                # Creation
                "create", "add", "insert", "make", "build", "generate",
                # Management
                "delete", "remove", "clear", "reset", "restore", "save",
                # Verification
                "verify", "check", "confirm", "validate", "review", "test"
            ]

        if self.sequence_indicators is None:
            self.sequence_indicators = [
                "first", "second", "third", "next", "then", "after", "finally",
                "step", "now", "let's", "we'll", "going to"
            ]

        # Validate weights
        total_weight = self.weight_procedural + self.weight_action_density + self.weight_coherence
        if not 0.99 <= total_weight <= 1.01:  # Allow small floating point error
            raise ValueError(
                f"Weights must sum to 1.0, got {total_weight} "
                f"(procedural={self.weight_procedural}, "
                f"action_density={self.weight_action_density}, "
                f"coherence={self.weight_coherence})"
            )


class TopicRanker:
    """
    Ranks topic segments by procedural importance.

    Uses multiple signals:
    - Action density (actions per sentence)
    - Procedural indicators (action verbs, sequence words)
    - Topic coherence (from Phase 1 segmenter)
    """

    def __init__(self, config: Optional[RankingConfig] = None):
        """
        Initialize topic ranker.

        Args:
            config: Ranking configuration (uses defaults if None)
        """
        self.config = config or RankingConfig()
        logger.info(
            f"Topic Ranker initialized: "
            f"weights=[procedural={self.config.weight_procedural}, "
            f"action_density={self.config.weight_action_density}, "
            f"coherence={self.config.weight_coherence}]"
        )

    def score_segments(self, segments: List[TopicSegment]) -> List[TopicScore]:
        """
        Score all segments by importance.

        Args:
            segments: Topic segments from Phase 1 segmenter

        Returns:
            List of topic scores (one per segment)
        """
        if not segments:
            return []

        scores = []

        for segment in segments:
            # Compute individual scores
            procedural_score = self._compute_procedural_score(segment)
            action_density = self._compute_action_density(segment)
            coherence_score = segment.coherence_score if hasattr(segment, 'coherence_score') else 0.0

            # Weighted combination
            weighted_procedural = procedural_score * self.config.weight_procedural
            weighted_action_density = action_density * self.config.weight_action_density
            weighted_coherence = coherence_score * self.config.weight_coherence

            importance_score = weighted_procedural + weighted_action_density + weighted_coherence

            topic_score = TopicScore(
                segment_index=segment.segment_index,
                importance_score=importance_score,
                procedural_score=procedural_score,
                action_density=action_density,
                coherence_score=coherence_score,
                weighted_procedural=weighted_procedural,
                weighted_action_density=weighted_action_density,
                weighted_coherence=weighted_coherence
            )

            scores.append(topic_score)

            logger.debug(
                f"Segment {segment.segment_index}: "
                f"importance={importance_score:.2f} "
                f"(procedural={procedural_score:.2f}, "
                f"action_density={action_density:.2f}, "
                f"coherence={coherence_score:.2f})"
            )

        return scores

    def rank_by_importance(
        self,
        segments: List[TopicSegment]
    ) -> List[TopicSegment]:
        """
        Rank segments by importance (descending).

        Args:
            segments: Topic segments from Phase 1 segmenter

        Returns:
            Segments sorted by importance (highest first)
        """
        if not segments:
            return []

        # Score all segments
        scores = self.score_segments(segments)

        # Create segment-score pairs
        segment_scores = list(zip(segments, scores))

        # Sort by importance (descending)
        segment_scores.sort(key=lambda x: x[1].importance_score, reverse=True)

        # Extract ranked segments
        ranked_segments = [seg for seg, score in segment_scores]

        logger.info(
            f"Ranked {len(segments)} segments: "
            f"top score={scores[0].importance_score:.2f}, "
            f"bottom score={scores[-1].importance_score:.2f}"
        )

        return ranked_segments

    def filter_low_importance(
        self,
        segments: List[TopicSegment],
        threshold: Optional[float] = None
    ) -> List[TopicSegment]:
        """
        Filter out low-importance segments.

        Args:
            segments: Topic segments from Phase 1 segmenter
            threshold: Importance threshold (uses config default if None)

        Returns:
            Filtered segments (high importance only)
        """
        if not segments:
            return []

        threshold = threshold or self.config.min_importance_threshold

        # Score all segments
        scores = self.score_segments(segments)

        # Filter by threshold
        filtered = []
        for segment, score in zip(segments, scores):
            if score.importance_score >= threshold:
                filtered.append(segment)
            else:
                logger.info(
                    f"Filtering low-importance segment {segment.segment_index}: "
                    f"score={score.importance_score:.2f} < {threshold:.2f}"
                )

        # Optionally keep only top N
        if self.config.keep_top_n is not None and len(filtered) > self.config.keep_top_n:
            # Re-rank filtered segments
            ranked = self.rank_by_importance(filtered)
            filtered = ranked[:self.config.keep_top_n]
            logger.info(f"Keeping top {self.config.keep_top_n} segments")

        logger.info(
            f"Filtered segments: {len(segments)} → {len(filtered)} "
            f"(threshold={threshold:.2f})"
        )

        return filtered

    def _compute_procedural_score(self, segment: TopicSegment) -> float:
        """
        Compute how procedural a segment is (0.0-1.0).

        Procedural segments have:
        - Action verbs (click, navigate, configure, etc.)
        - Sequence indicators (first, next, then, etc.)
        - Imperative mood (commands/instructions)

        Args:
            segment: Topic segment

        Returns:
            Procedural score (0.0-1.0)
        """
        if not segment.sentences:
            return 0.0

        # Get all text
        text = " ".join(s.text.lower() for s in segment.sentences)
        words = text.split()

        if not words:
            return 0.0

        # Count action verbs
        action_count = sum(1 for verb in self.config.action_verbs if verb in text)

        # Count sequence indicators
        sequence_count = sum(1 for indicator in self.config.sequence_indicators if indicator in text)

        # Count imperative sentences (start with action verb)
        imperative_count = 0
        for sentence in segment.sentences:
            first_words = sentence.text.lower().split()[:2]  # First 2 words
            if any(verb in first_words for verb in self.config.action_verbs):
                imperative_count += 1

        # Normalize scores
        action_score = min(1.0, action_count / (len(segment.sentences) * 2))  # Expect ~2 actions/sentence
        sequence_score = min(1.0, sequence_count / max(1, len(segment.sentences) / 3))  # Expect ~1 per 3 sentences
        imperative_score = imperative_count / len(segment.sentences)

        # Weighted combination
        procedural_score = (
            action_score * 0.5 +       # 50% weight: action verbs
            imperative_score * 0.3 +   # 30% weight: imperative mood
            sequence_score * 0.2       # 20% weight: sequence indicators
        )

        return min(1.0, procedural_score)

    def _compute_action_density(self, segment: TopicSegment) -> float:
        """
        Compute action density (actions per sentence).

        Normalized to 0.0-1.0 assuming ~3 actions per sentence is ideal.

        Args:
            segment: Topic segment

        Returns:
            Action density score (0.0-1.0)
        """
        if not segment.sentences:
            return 0.0

        # Count action verbs in segment
        text = " ".join(s.text.lower() for s in segment.sentences)
        action_count = sum(1 for verb in self.config.action_verbs if verb in text)

        # Compute density
        density = action_count / len(segment.sentences)

        # Normalize (assume 3 actions/sentence is ideal)
        normalized = min(1.0, density / 3.0)

        return normalized

    def get_ranking_report(
        self,
        segments: List[TopicSegment]
    ) -> dict:
        """
        Get detailed ranking report for analysis.

        Args:
            segments: Topic segments

        Returns:
            Report dictionary with scores and statistics
        """
        scores = self.score_segments(segments)

        if not scores:
            return {
                "total_segments": 0,
                "scores": [],
                "statistics": {}
            }

        importance_scores = [s.importance_score for s in scores]

        return {
            "total_segments": len(segments),
            "scores": [
                {
                    "segment_index": s.segment_index,
                    "importance": round(s.importance_score, 3),
                    "procedural": round(s.procedural_score, 3),
                    "action_density": round(s.action_density, 3),
                    "coherence": round(s.coherence_score, 3)
                }
                for s in scores
            ],
            "statistics": {
                "avg_importance": sum(importance_scores) / len(importance_scores),
                "max_importance": max(importance_scores),
                "min_importance": min(importance_scores),
                "std_importance": self._compute_std(importance_scores),
                "high_importance_count": sum(1 for s in importance_scores if s >= 0.7),
                "medium_importance_count": sum(1 for s in importance_scores if 0.3 <= s < 0.7),
                "low_importance_count": sum(1 for s in importance_scores if s < 0.3)
            }
        }

    def _compute_std(self, values: List[float]) -> float:
        """Compute standard deviation."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
