"""
Q&A Filter: Identifies and filters question/answer sections from procedural content.

Phase 2 Component - Builds on Phase 1's transcript parser metadata.
Uses ParsedSentence.is_question and speaker information to detect Q&A sections.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import logging

# Import Phase 1 components
from .transcript_parser import ParsedSentence, TranscriptMetadata
from .topic_segmenter import TopicSegment

logger = logging.getLogger(__name__)


@dataclass
class QASection:
    """
    Represents a question/answer section in the transcript.

    Q&A sections are characterized by:
    - High density of questions (>30% sentences are questions)
    - Speaker changes (instructor answering participant questions)
    - Lack of procedural content (no sequential instructions)
    """
    segment_index: int
    start_sentence_index: int
    end_sentence_index: int
    question_count: int
    total_sentences: int
    qa_density: float  # 0.0-1.0 (% of questions)
    is_qa_dense: bool  # True if qa_density > threshold
    primary_speaker: Optional[str] = None
    speakers: List[str] = field(default_factory=list)


@dataclass
class FilterConfig:
    """Configuration for Q&A filtering."""

    # Q&A detection thresholds
    min_qa_density: float = 0.30  # 30% questions = Q&A section
    min_questions: int = 2         # At least 2 questions to be Q&A

    # Filtering behavior
    filter_qa_sections: bool = True       # Remove Q&A sections
    keep_instructor_only: bool = False    # Keep only instructor-led segments
    instructor_role: str = "instructor"   # How instructor is identified

    # Logging
    verbose: bool = False

    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.min_qa_density <= 1.0:
            raise ValueError(f"min_qa_density must be 0.0-1.0, got {self.min_qa_density}")
        if self.min_questions < 0:
            raise ValueError(f"min_questions must be >= 0, got {self.min_questions}")


class QAFilter:
    """
    Filters question/answer sections from topic segments.

    Uses Phase 1 parser metadata (is_question, speaker, speaker_role)
    to identify and filter Q&A sections, keeping only procedural content.
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize Q&A filter.

        Args:
            config: Filter configuration (uses defaults if None)
        """
        self.config = config or FilterConfig()
        logger.info(f"Q&A Filter initialized: min_qa_density={self.config.min_qa_density}")

    def identify_qa_sections(
        self,
        segments: List[TopicSegment],
        metadata: Optional[TranscriptMetadata] = None
    ) -> List[QASection]:
        """
        Identify Q&A sections in topic segments.

        Args:
            segments: Topic segments from Phase 1 segmenter
            metadata: Optional transcript metadata

        Returns:
            List of identified Q&A sections
        """
        qa_sections = []

        for segment in segments:
            # Compute Q&A density for this segment
            qa_density = self._compute_qa_density(segment)
            question_count = sum(1 for s in segment.sentences if s.is_question)

            # Check if this is a Q&A section
            is_qa_dense = (
                qa_density >= self.config.min_qa_density and
                question_count >= self.config.min_questions
            )

            if is_qa_dense or self.config.verbose:
                # Get speaker information
                speakers = self._get_speakers(segment)
                primary_speaker = segment.primary_speaker

                qa_section = QASection(
                    segment_index=segment.segment_index,
                    start_sentence_index=segment.sentences[0].sentence_index,
                    end_sentence_index=segment.sentences[-1].sentence_index,
                    question_count=question_count,
                    total_sentences=len(segment.sentences),
                    qa_density=qa_density,
                    is_qa_dense=is_qa_dense,
                    primary_speaker=primary_speaker,
                    speakers=speakers
                )

                if is_qa_dense:
                    qa_sections.append(qa_section)
                    logger.info(
                        f"Q&A section detected: segment {segment.segment_index}, "
                        f"{question_count}/{len(segment.sentences)} questions ({qa_density:.0%})"
                    )

        return qa_sections

    def filter_segments(
        self,
        segments: List[TopicSegment],
        metadata: Optional[TranscriptMetadata] = None
    ) -> List[TopicSegment]:
        """
        Filter segments to remove Q&A sections and optionally keep only instructor content.

        Args:
            segments: Topic segments from Phase 1 segmenter
            metadata: Optional transcript metadata

        Returns:
            Filtered segments (procedural content only)
        """
        if not self.config.filter_qa_sections:
            # Filtering disabled, return all segments
            return segments

        # Identify Q&A sections
        qa_sections = self.identify_qa_sections(segments, metadata)
        qa_segment_indices = {qa.segment_index for qa in qa_sections}

        filtered_segments = []

        for segment in segments:
            # Check if this segment is a Q&A section
            if segment.segment_index in qa_segment_indices:
                logger.info(f"Filtering out Q&A segment {segment.segment_index}")
                continue

            # Check if we should filter by speaker role
            if self.config.keep_instructor_only:
                if not self._is_instructor_led(segment):
                    logger.info(
                        f"Filtering out non-instructor segment {segment.segment_index} "
                        f"(primary speaker: {segment.primary_speaker})"
                    )
                    continue

            # This segment passes all filters
            filtered_segments.append(segment)

        logger.info(
            f"Filtered segments: {len(segments)} → {len(filtered_segments)} "
            f"({len(qa_sections)} Q&A sections removed)"
        )

        return filtered_segments

    def _compute_qa_density(self, segment: TopicSegment) -> float:
        """
        Compute Q&A density for a segment (% of questions).

        Args:
            segment: Topic segment

        Returns:
            Q&A density (0.0-1.0)
        """
        if not segment.sentences:
            return 0.0

        question_count = sum(1 for s in segment.sentences if s.is_question)
        return question_count / len(segment.sentences)

    def _get_speakers(self, segment: TopicSegment) -> List[str]:
        """
        Get unique speakers in a segment.

        Args:
            segment: Topic segment

        Returns:
            List of unique speaker names
        """
        speakers = set()
        for sentence in segment.sentences:
            if sentence.speaker:
                speakers.add(sentence.speaker)
        return sorted(speakers)

    def _is_instructor_led(self, segment: TopicSegment) -> bool:
        """
        Check if segment is instructor-led (vs participant-led).

        Args:
            segment: Topic segment

        Returns:
            True if instructor-led, False otherwise
        """
        # Check primary speaker role
        for sentence in segment.sentences:
            if sentence.speaker == segment.primary_speaker:
                if sentence.speaker_role == self.config.instructor_role:
                    return True
                # If role is not set, use heuristics
                if sentence.speaker_role is None:
                    # Instructor often has fewer questions
                    instructor_questions = sum(
                        1 for s in segment.sentences
                        if s.speaker == segment.primary_speaker and s.is_question
                    )
                    instructor_sentences = sum(
                        1 for s in segment.sentences
                        if s.speaker == segment.primary_speaker
                    )
                    if instructor_sentences > 0:
                        question_rate = instructor_questions / instructor_sentences
                        # Instructor typically has <20% questions
                        return question_rate < 0.2

        return False

    def get_statistics(
        self,
        segments: List[TopicSegment],
        metadata: Optional[TranscriptMetadata] = None
    ) -> dict:
        """
        Get Q&A filtering statistics.

        Args:
            segments: Topic segments
            metadata: Optional transcript metadata

        Returns:
            Statistics dictionary with counts and percentages
        """
        qa_sections = self.identify_qa_sections(segments, metadata)
        filtered = self.filter_segments(segments, metadata)

        total_questions = sum(
            sum(1 for s in seg.sentences if s.is_question)
            for seg in segments
        )

        total_sentences = sum(len(seg.sentences) for seg in segments)

        return {
            "total_segments": len(segments),
            "qa_segments": len(qa_sections),
            "filtered_segments": len(filtered),
            "removed_segments": len(segments) - len(filtered),
            "total_questions": total_questions,
            "total_sentences": total_sentences,
            "overall_qa_density": total_questions / total_sentences if total_sentences > 0 else 0.0,
            "filter_rate": (len(segments) - len(filtered)) / len(segments) if segments else 0.0
        }
