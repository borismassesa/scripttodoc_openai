"""
Topic segmentation module for intelligent conversation analysis.
Groups parsed sentences into coherent topics using multi-signal boundary detection.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter

from .transcript_parser import ParsedSentence, TranscriptMetadata

logger = logging.getLogger(__name__)


@dataclass
class SegmentationConfig:
    """Configuration for topic segmentation behavior and thresholds."""

    # Boundary detection weights (must sum to 1.0)
    weight_timestamp_gap: float = 0.35      # Long pauses indicate topic change
    weight_speaker_transition: float = 0.25  # Instructor resuming after Q&A
    weight_transition_phrase: float = 0.30   # Explicit "Now let's..." phrases
    weight_semantic_similarity: float = 0.10 # Keyword overlap (optional)

    # Boundary thresholds
    timestamp_gap_threshold: float = 90.0    # Seconds (>90s = likely boundary)
    boundary_score_threshold: float = 0.40   # 0.0-1.0 (>0.4 = boundary)

    # Quality constraints
    min_segment_sentences: int = 2           # Merge segments shorter than this
    max_segment_sentences: int = 30          # Split segments longer than this (optional)
    min_total_segments: int = 3              # ⭐ CRITICAL: Minimum segments for any transcript (prevents 1-step documents)

    # Feature toggles
    use_semantic_similarity: bool = False    # Enable keyword-based similarity
    merge_small_segments: bool = True        # Automatically merge small segments

    def __post_init__(self):
        """Validate configuration."""
        total_weight = (
            self.weight_timestamp_gap +
            self.weight_speaker_transition +
            self.weight_transition_phrase +
            self.weight_semantic_similarity
        )
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        if not 0.0 <= self.boundary_score_threshold <= 1.0:
            raise ValueError(f"boundary_score_threshold must be 0.0-1.0, got {self.boundary_score_threshold}")


@dataclass
class TopicSegment:
    """A coherent topic segment containing related sentences."""

    # Core content
    segment_index: int                      # 0-based segment index
    sentences: List[ParsedSentence]         # Sentences in this segment

    # Temporal metadata
    start_timestamp: Optional[float] = None # First sentence timestamp (seconds)
    end_timestamp: Optional[float] = None   # Last sentence timestamp (seconds)
    duration_seconds: Optional[float] = None

    # Speaker metadata
    primary_speaker: Optional[str] = None   # Most frequent speaker in segment
    speaker_counts: dict = field(default_factory=dict)

    # Segment characteristics
    has_transition_start: bool = False      # Starts with transition phrase
    has_qa_section: bool = False            # Contains Q&A interactions
    question_count: int = 0

    # Quality metrics
    action_density: float = 0.0             # Actions per sentence (computed later)
    coherence_score: float = 0.0            # Semantic coherence (0.0-1.0)
    fallback_split: bool = False            # ⭐ Created by minimum count fallback (not natural boundary)

    def __post_init__(self):
        """Compute derived metadata from sentences."""
        if not self.sentences:
            return

        # Extract timestamps
        timestamps = [s.timestamp for s in self.sentences if s.timestamp is not None]
        if timestamps:
            self.start_timestamp = min(timestamps)
            self.end_timestamp = max(timestamps)
            self.duration_seconds = self.end_timestamp - self.start_timestamp

        # Count speakers
        speaker_counter = Counter(s.speaker for s in self.sentences if s.speaker)
        self.speaker_counts = dict(speaker_counter)
        if speaker_counter:
            self.primary_speaker = speaker_counter.most_common(1)[0][0]

        # Detect characteristics
        self.has_transition_start = self.sentences[0].is_transition if self.sentences else False
        self.question_count = sum(1 for s in self.sentences if s.is_question)

        # Detect Q&A sections (questions from participants)
        self.has_qa_section = any(
            s.is_question and s.speaker_role == "participant"
            for s in self.sentences
        )

    def get_text(self) -> str:
        """Get concatenated text of all sentences in segment."""
        return ' '.join(s.text for s in self.sentences)

    def __str__(self) -> str:
        """String representation for debugging."""
        parts = [f"Segment {self.segment_index}"]
        parts.append(f"{len(self.sentences)} sentences")

        if self.start_timestamp is not None:
            mins = int(self.start_timestamp // 60)
            secs = int(self.start_timestamp % 60)
            parts.append(f"starts {mins:02d}:{secs:02d}")

        if self.duration_seconds:
            parts.append(f"duration {self.duration_seconds:.0f}s")

        if self.primary_speaker:
            parts.append(f"speaker: {self.primary_speaker}")

        return " | ".join(parts)


class TopicSegmenter:
    """
    Segment parsed transcript into coherent topics using multi-signal boundary detection.

    Boundary signals:
    1. Timestamp gaps (>90s pause = likely topic change)
    2. Speaker transitions (instructor resuming after Q&A)
    3. Transition phrases ("Now let's...", "Next...")
    4. Semantic similarity (keyword overlap - optional)

    Each signal contributes a weighted score. If total score exceeds threshold,
    a topic boundary is created.
    """

    def __init__(self, config: Optional[SegmentationConfig] = None):
        """
        Initialize segmenter with configuration.

        Args:
            config: Segmentation configuration (uses defaults if None)
        """
        self.config = config or SegmentationConfig()
        logger.info(f"TopicSegmenter initialized: {self.config}")

    def segment(
        self,
        parsed_sentences: List[ParsedSentence],
        metadata: Optional[TranscriptMetadata] = None
    ) -> List[TopicSegment]:
        """
        Segment parsed sentences into coherent topics.

        Process:
        1. Compute boundary scores between consecutive sentences
        2. Create segments at boundaries
        3. Merge small segments (if enabled)
        4. Compute segment metadata

        Args:
            parsed_sentences: List of parsed sentences with metadata
            metadata: Optional transcript metadata (for context)

        Returns:
            List of TopicSegment objects
        """
        if not parsed_sentences:
            logger.warning("No sentences to segment")
            return []

        logger.info(f"Segmenting {len(parsed_sentences)} sentences into topics...")

        # Step 1: Identify topic boundaries
        boundary_indices = self._identify_boundaries(parsed_sentences)
        logger.info(f"Identified {len(boundary_indices)} topic boundaries")

        # Step 2: Create segments from boundaries
        segments = self._create_segments(parsed_sentences, boundary_indices)
        logger.info(f"Created {len(segments)} initial segments")

        # Step 3: Merge small segments (if enabled)
        if self.config.merge_small_segments:
            segments = self._merge_small_segments(segments)
            logger.info(f"After merging: {len(segments)} segments")

        # ⭐ Step 3.5: Enforce minimum segment count (CRITICAL for quality)
        if len(segments) < self.config.min_total_segments:
            logger.warning(
                f"Only {len(segments)} segments detected (min: {self.config.min_total_segments}). "
                f"Applying fallback: split largest segment(s) to reach minimum."
            )
            segments = self._ensure_minimum_segments(segments, parsed_sentences)
            logger.info(f"After minimum enforcement: {len(segments)} segments")

        # Step 4: Compute segment quality metrics
        segments = self._compute_segment_metrics(segments)

        logger.info(f"Segmentation complete: {len(segments)} topics")
        for seg in segments:
            logger.debug(f"  {seg}")

        return segments

    def _identify_boundaries(self, sentences: List[ParsedSentence]) -> List[int]:
        """
        Identify topic boundary indices using multi-signal analysis.

        Args:
            sentences: List of parsed sentences

        Returns:
            List of sentence indices that start new topics
        """
        boundaries = [0]  # First sentence always starts a topic

        for i in range(1, len(sentences)):
            prev_sent = sentences[i - 1]
            curr_sent = sentences[i]

            # Compute boundary score
            boundary_score = self._compute_boundary_score(prev_sent, curr_sent)

            # Check if boundary
            if self._is_topic_boundary(boundary_score, curr_sent):
                boundaries.append(i)
                logger.debug(
                    f"Boundary at sentence {i}: score={boundary_score:.2f} "
                    f"text='{curr_sent.text[:50]}...'"
                )

        return boundaries

    def _compute_boundary_score(
        self,
        prev_sent: ParsedSentence,
        curr_sent: ParsedSentence
    ) -> float:
        """
        Compute boundary score (0.0-1.0) between two consecutive sentences.
        Higher score = more likely to be a topic boundary.

        Args:
            prev_sent: Previous sentence
            curr_sent: Current sentence

        Returns:
            Boundary score (0.0-1.0)
        """
        score = 0.0

        # Signal 1: Timestamp gap
        timestamp_score = self._compute_timestamp_gap_score(prev_sent, curr_sent)
        score += self.config.weight_timestamp_gap * timestamp_score

        # Signal 2: Speaker transition
        speaker_score = self._compute_speaker_transition_score(prev_sent, curr_sent)
        score += self.config.weight_speaker_transition * speaker_score

        # Signal 3: Transition phrase
        transition_score = self._compute_transition_phrase_score(curr_sent)
        score += self.config.weight_transition_phrase * transition_score

        # Signal 4: Semantic similarity (optional)
        if self.config.use_semantic_similarity:
            semantic_score = self._compute_semantic_similarity_score(prev_sent, curr_sent)
            score += self.config.weight_semantic_similarity * semantic_score

        return min(score, 1.0)  # Cap at 1.0

    def _compute_timestamp_gap_score(
        self,
        prev_sent: ParsedSentence,
        curr_sent: ParsedSentence
    ) -> float:
        """
        Compute score based on timestamp gap between sentences.

        Args:
            prev_sent: Previous sentence
            curr_sent: Current sentence

        Returns:
            Score 0.0-1.0 (higher = larger gap = more likely boundary)
        """
        if prev_sent.timestamp is None or curr_sent.timestamp is None:
            return 0.0

        gap = curr_sent.timestamp - prev_sent.timestamp

        # Already marked as long pause by parser
        if curr_sent.follows_long_pause:
            return 1.0

        # Scale gap: 0s=0.0, threshold=1.0
        score = gap / self.config.timestamp_gap_threshold
        return min(score, 1.0)

    def _compute_speaker_transition_score(
        self,
        prev_sent: ParsedSentence,
        curr_sent: ParsedSentence
    ) -> float:
        """
        Compute score based on speaker transitions.

        High score when:
        - Instructor resumes after participant question (end of Q&A)
        - Speaker changes AND current sentence has transition phrase

        Args:
            prev_sent: Previous sentence
            curr_sent: Current sentence

        Returns:
            Score 0.0-1.0
        """
        # No speaker info
        if not prev_sent.speaker or not curr_sent.speaker:
            return 0.0

        # No speaker change
        if not curr_sent.speaker_changed:
            return 0.0

        # Instructor resuming after participant = likely topic boundary
        if (prev_sent.speaker_role == "participant" and
            curr_sent.speaker_role == "instructor"):
            return 1.0

        # Speaker change + transition phrase = boundary
        if curr_sent.is_transition:
            return 0.8

        # Regular speaker change = weak signal
        return 0.3

    def _compute_transition_phrase_score(self, curr_sent: ParsedSentence) -> float:
        """
        Compute score based on transition phrases.

        Args:
            curr_sent: Current sentence

        Returns:
            Score 0.0-1.0 (1.0 if transition phrase detected)
        """
        return 1.0 if curr_sent.is_transition else 0.0

    def _compute_semantic_similarity_score(
        self,
        prev_sent: ParsedSentence,
        curr_sent: ParsedSentence
    ) -> float:
        """
        Compute score based on semantic similarity (keyword overlap).
        Low similarity = high boundary score.

        Args:
            prev_sent: Previous sentence
            curr_sent: Current sentence

        Returns:
            Score 0.0-1.0 (higher = less similar = more likely boundary)
        """
        # Extract keywords (simple approach: nouns/verbs, >3 chars, lowercased)
        def extract_keywords(text: str) -> set:
            words = text.lower().split()
            # Filter: length >3, not common words
            stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'will', 'have', 'your'}
            return {w for w in words if len(w) > 3 and w not in stopwords}

        prev_keywords = extract_keywords(prev_sent.text)
        curr_keywords = extract_keywords(curr_sent.text)

        if not prev_keywords or not curr_keywords:
            return 0.5  # Neutral if no keywords

        # Jaccard similarity: intersection / union
        intersection = len(prev_keywords & curr_keywords)
        union = len(prev_keywords | curr_keywords)
        similarity = intersection / union if union > 0 else 0.0

        # Return inverse: low similarity = high boundary score
        return 1.0 - similarity

    def _is_topic_boundary(self, boundary_score: float, curr_sent: ParsedSentence) -> bool:
        """
        Determine if a boundary score indicates a topic boundary.

        Args:
            boundary_score: Computed boundary score (0.0-1.0)
            curr_sent: Current sentence (for additional checks)

        Returns:
            True if this is a topic boundary
        """
        # Primary check: score threshold
        if boundary_score > self.config.boundary_score_threshold:
            return True

        # Override 1: Always boundary after very long pause
        if curr_sent.follows_long_pause and curr_sent.timestamp:
            return True

        # Override 2: Strong transition phrases likely indicate boundaries
        # (even if score doesn't quite reach threshold)
        if curr_sent.is_transition and boundary_score >= 0.30:
            return True

        return False

    def _create_segments(
        self,
        sentences: List[ParsedSentence],
        boundary_indices: List[int]
    ) -> List[TopicSegment]:
        """
        Create TopicSegment objects from boundary indices.

        Args:
            sentences: All parsed sentences
            boundary_indices: Indices where new topics start

        Returns:
            List of TopicSegment objects
        """
        segments = []

        for i, start_idx in enumerate(boundary_indices):
            # Determine end index
            if i < len(boundary_indices) - 1:
                end_idx = boundary_indices[i + 1]
            else:
                end_idx = len(sentences)

            # Extract sentences for this segment
            segment_sentences = sentences[start_idx:end_idx]

            # Create segment
            segment = TopicSegment(
                segment_index=i,
                sentences=segment_sentences
            )

            segments.append(segment)

        return segments

    def _merge_small_segments(self, segments: List[TopicSegment]) -> List[TopicSegment]:
        """
        Merge segments that are too small to be standalone topics.

        Strategy:
        - Merge segment with previous if < min_segment_sentences
        - Keep first segment even if small (introduction)

        Args:
            segments: List of initial segments

        Returns:
            List of merged segments
        """
        if len(segments) <= 1:
            return segments

        merged = []
        i = 0

        while i < len(segments):
            current = segments[i]

            # First segment or large enough: keep as-is
            if i == 0 or len(current.sentences) >= self.config.min_segment_sentences:
                merged.append(current)
                i += 1
            else:
                # Small segment: merge with previous
                if merged:
                    prev = merged[-1]

                    # Combine sentences
                    combined_sentences = prev.sentences + current.sentences

                    # Create new merged segment
                    merged_segment = TopicSegment(
                        segment_index=prev.segment_index,
                        sentences=combined_sentences
                    )

                    # Replace previous segment
                    merged[-1] = merged_segment

                    logger.debug(
                        f"Merged small segment {current.segment_index} "
                        f"({len(current.sentences)} sentences) into segment {prev.segment_index}"
                    )
                else:
                    # No previous segment to merge with (shouldn't happen)
                    merged.append(current)

                i += 1

        # Re-index segments
        for idx, segment in enumerate(merged):
            segment.segment_index = idx

        return merged

    def _ensure_minimum_segments(
        self,
        segments: List[TopicSegment],
        all_sentences: List[ParsedSentence]
    ) -> List[TopicSegment]:
        """
        Ensure minimum number of segments by splitting largest segment(s).

        This is a fallback for transcripts without clear topic boundaries.
        Strategy: Split largest segments evenly until we reach min_total_segments.

        Args:
            segments: Current list of segments (may be < min_total_segments)
            all_sentences: Full list of parsed sentences

        Returns:
            Expanded list with at least min_total_segments segments
        """
        if len(segments) >= self.config.min_total_segments:
            return segments

        # Calculate how many additional segments we need
        segments_needed = self.config.min_total_segments - len(segments)

        logger.info(
            f"Splitting largest segment(s) to create {segments_needed} additional segments "
            f"(min requirement: {self.config.min_total_segments})"
        )

        # Sort segments by size (largest first)
        sorted_segments = sorted(segments, key=lambda s: len(s.sentences), reverse=True)

        # We'll split the largest segment into (segments_needed + 1) parts
        largest_segment = sorted_segments[0]

        # Split evenly
        sentences = largest_segment.sentences
        num_splits = segments_needed + 1  # Original + new segments
        split_size = max(self.config.min_segment_sentences, len(sentences) // num_splits)

        new_segments = []
        start_idx = 0

        for i in range(num_splits):
            # Last split gets remaining sentences
            if i == num_splits - 1:
                end_idx = len(sentences)
            else:
                end_idx = min(start_idx + split_size, len(sentences))

            if start_idx < end_idx:
                split_sentences = sentences[start_idx:end_idx]

                # Create new segment
                new_segment = TopicSegment(
                    segment_index=-1,  # Will re-index later
                    sentences=split_sentences,
                    fallback_split=True  # Mark as fallback split
                )
                new_segments.append(new_segment)

            start_idx = end_idx

        # Replace largest segment with splits
        result_segments = []
        for seg in segments:
            if seg.segment_index == largest_segment.segment_index:
                # Replace with splits
                result_segments.extend(new_segments)
            else:
                result_segments.append(seg)

        # Re-index all segments
        for idx, segment in enumerate(result_segments):
            segment.segment_index = idx

        logger.info(
            f"Split largest segment ({len(largest_segment.sentences)} sentences) "
            f"into {len(new_segments)} segments"
        )

        return result_segments

    def _compute_segment_metrics(self, segments: List[TopicSegment]) -> List[TopicSegment]:
        """
        Compute quality metrics for each segment.

        Metrics:
        - coherence_score: Semantic coherence within segment (0.0-1.0)
        - action_density: Actions per sentence (computed later by pipeline)

        Args:
            segments: List of segments

        Returns:
            Same segments with metrics computed
        """
        for segment in segments:
            # Coherence: Average pairwise keyword similarity
            segment.coherence_score = self._compute_segment_coherence(segment)

        return segments

    def _compute_segment_coherence(self, segment: TopicSegment) -> float:
        """
        Compute internal coherence of a segment (0.0-1.0).

        Uses pairwise keyword similarity between sentences.

        Args:
            segment: Topic segment

        Returns:
            Coherence score (0.0-1.0, higher = more coherent)
        """
        if len(segment.sentences) < 2:
            return 1.0  # Single sentence is perfectly coherent

        # Extract keywords for each sentence
        def extract_keywords(text: str) -> set:
            words = text.lower().split()
            stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'will', 'have', 'your'}
            return {w for w in words if len(w) > 3 and w not in stopwords}

        sentence_keywords = [extract_keywords(s.text) for s in segment.sentences]

        # Compute pairwise similarities
        similarities = []
        for i in range(len(sentence_keywords)):
            for j in range(i + 1, len(sentence_keywords)):
                kw1 = sentence_keywords[i]
                kw2 = sentence_keywords[j]

                if not kw1 or not kw2:
                    continue

                # Jaccard similarity
                intersection = len(kw1 & kw2)
                union = len(kw1 | kw2)
                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)

        if not similarities:
            return 0.5  # Neutral if no comparisons

        # Average similarity
        return sum(similarities) / len(similarities)
