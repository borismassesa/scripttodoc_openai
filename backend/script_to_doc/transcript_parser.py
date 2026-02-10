"""
Transcript parsing module for intelligent conversation analysis.
Extracts metadata (timestamps, speakers, questions) from raw transcripts.
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ParsedSentence:
    """A single parsed sentence with metadata and characteristics."""

    # Core content
    text: str                           # Cleaned sentence text
    raw_text: str                       # Original text (with timestamps, speaker labels)
    sentence_index: int                 # 0-based index in transcript

    # Temporal metadata
    timestamp: Optional[float] = None   # Seconds from start (e.g., 65.0 for [00:01:05])

    # Speaker metadata
    speaker: Optional[str] = None       # e.g., "Speaker 1", "John", "PRESENTER"
    speaker_role: Optional[str] = None  # "instructor" or "participant" (heuristic)

    # Sentence characteristics
    is_question: bool = False           # Ends with "?" or has question words
    is_transition: bool = False         # Contains transition phrases
    has_emphasis: bool = False          # Contains emphasis markers (ALL CAPS, **bold**, etc.)

    # Relationships to other sentences
    follows_long_pause: bool = False    # >90 seconds since last sentence
    speaker_changed: bool = False       # Different speaker than previous sentence

    def __str__(self) -> str:
        """String representation for debugging."""
        parts = [f"[{self.sentence_index}]"]
        if self.timestamp is not None:
            mins = int(self.timestamp // 60)
            secs = int(self.timestamp % 60)
            parts.append(f"{mins:02d}:{secs:02d}")
        if self.speaker:
            parts.append(self.speaker)
        parts.append(self.text[:50] + "..." if len(self.text) > 50 else self.text)
        return " ".join(parts)


@dataclass
class TranscriptMetadata:
    """Overall transcript metadata and statistics."""

    total_sentences: int
    total_speakers: int
    speaker_names: List[str] = field(default_factory=list)

    # Temporal information
    duration_seconds: Optional[float] = None
    has_timestamps: bool = False

    # Speaker information
    primary_speaker: Optional[str] = None       # Most frequent speaker (likely instructor)
    primary_speaker_ratio: float = 0.0          # % of sentences from primary speaker

    # Content characteristics
    has_qa_sections: bool = False               # Contains Q&A patterns
    question_count: int = 0
    transition_count: int = 0

    def __str__(self) -> str:
        """String representation for logging."""
        parts = [
            f"{self.total_sentences} sentences",
            f"{self.total_speakers} speakers"
        ]
        if self.duration_seconds:
            mins = int(self.duration_seconds // 60)
            secs = int(self.duration_seconds % 60)
            parts.append(f"{mins}m {secs}s")
        if self.primary_speaker:
            parts.append(f"primary: {self.primary_speaker} ({self.primary_speaker_ratio:.0%})")
        return ", ".join(parts)


class TranscriptParser:
    """
    Parse raw transcript into structured sentences with metadata.

    Handles multiple transcript formats:
    - Timestamps: [HH:MM:SS], (HH:MM:SS), HH:MM:SS -
    - Speakers: Speaker 1:, JOHN:, [Speaker]:, >> Person:

    Extracts:
    - Temporal metadata (timestamps, pauses)
    - Speaker metadata (names, roles)
    - Sentence characteristics (questions, transitions, emphasis)
    """

    # Transition phrases that often indicate topic changes
    TRANSITION_PHRASES = [
        # Explicit transitions
        r'\b(?:now|next|okay|alright|so),?\s+let\'?s\s+',
        r'\bmoving on\b',
        r'\bnow (?:let\'s|we\'ll|we will)\b',
        r'\bnext,?\s+(?:we\'ll|we\'re|we will|up|step|part|section)\b',

        # Section markers
        r'\b(?:first|second|third|finally|lastly)\b',
        r'\bstep \d+\b',
        r'\bpart \d+\b',

        # Topic introductions
        r'\blet\'s talk about\b',
        r'\blet\'s discuss\b',
        r'\blet\'s move (?:on )?to\b',
        r'\bthe next (?:thing|topic|item)\b',
    ]

    # Question indicators (beyond just "?")
    QUESTION_WORDS = [
        'what', 'when', 'where', 'who', 'whom', 'whose',
        'why', 'how', 'which', 'can', 'could', 'would',
        'should', 'is', 'are', 'do', 'does', 'did'
    ]

    def __init__(self):
        """Initialize parser with compiled regex patterns."""
        self.transition_pattern = re.compile(
            '|'.join(self.TRANSITION_PHRASES),
            re.IGNORECASE
        )

    def parse(self, raw_transcript: str) -> Tuple[List[ParsedSentence], TranscriptMetadata]:
        """
        Parse raw transcript into structured sentences with metadata.

        Process:
        1. Split into lines
        2. Extract timestamps and speakers from each line (BEFORE cleaning)
        3. Break into sentences
        4. Associate metadata with each sentence
        5. Identify sentence characteristics (question, transition, etc.)
        6. Compute relationships (pauses, speaker changes)
        7. Build overall metadata

        Args:
            raw_transcript: Raw transcript text with timestamps, speakers, etc.

        Returns:
            (parsed_sentences, transcript_metadata)
        """
        logger.info("Parsing transcript...")

        # Step 1: Parse lines with metadata
        lines_with_metadata = self._parse_lines(raw_transcript)

        if not lines_with_metadata:
            logger.warning("No lines parsed from transcript")
            return [], TranscriptMetadata(
                total_sentences=0,
                total_speakers=0
            )

        # Step 2: Break lines into sentences
        sentences_with_metadata = self._split_into_sentences(lines_with_metadata)

        # Step 3: Analyze sentence characteristics
        parsed_sentences = self._analyze_sentences(sentences_with_metadata)

        # Step 4: Compute relationships (pauses, speaker changes)
        parsed_sentences = self._compute_relationships(parsed_sentences)

        # Step 5: Build transcript metadata
        metadata = self._build_metadata(parsed_sentences)

        logger.info(f"Parsed {len(parsed_sentences)} sentences: {metadata}")

        return parsed_sentences, metadata

    def _parse_lines(self, raw_transcript: str) -> List[Dict]:
        """
        Parse transcript lines and extract timestamp/speaker metadata.

        Args:
            raw_transcript: Raw transcript text

        Returns:
            List of dicts with keys: text, timestamp, speaker, raw
        """
        lines_with_metadata = []

        for line in raw_transcript.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Extract timestamp
            timestamp, line_after_timestamp = self._extract_timestamp(line)

            # Extract speaker
            speaker, text = self._extract_speaker(line_after_timestamp)

            # Store metadata
            lines_with_metadata.append({
                'text': text.strip(),
                'timestamp': timestamp,
                'speaker': speaker,
                'raw': line
            })

        return lines_with_metadata

    def _extract_timestamp(self, line: str) -> Tuple[Optional[float], str]:
        """
        Extract timestamp from line and return (timestamp_seconds, remaining_text).

        Supported formats:
        - [HH:MM:SS] or [HH:MM:SS.mmm]
        - (HH:MM:SS) or (HH:MM:SS.mmm)
        - <HH:MM:SS>
        - HH:MM:SS - (with dash)
        - HH:MM:SS (at start of line with space after)

        Args:
            line: Input line with potential timestamp

        Returns:
            (timestamp_in_seconds, line_without_timestamp)
        """
        # Try bracketed formats: [HH:MM:SS], (HH:MM:SS), <HH:MM:SS>
        patterns = [
            r'^\[(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{3}))?\]\s*',  # [00:01:05] or [00:01:05.123]
            r'^\((\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{3}))?\)\s*',  # (00:01:05)
            r'^<(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{3}))?>?\s*',   # <00:01:05>
            r'^(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{3}))?\s*-\s*',  # 00:01:05 -
            r'^(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{3}))?\s+',      # 00:01:05 (space after)
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                hours = int(groups[0])
                minutes = int(groups[1])
                seconds = int(groups[2])
                # milliseconds = int(groups[3]) if groups[3] else 0

                total_seconds = hours * 3600 + minutes * 60 + seconds
                remaining_text = line[match.end():]

                return total_seconds, remaining_text

        # No timestamp found
        return None, line

    def _extract_speaker(self, line: str) -> Tuple[Optional[str], str]:
        """
        Extract speaker from line and return (speaker_name, remaining_text).

        Supported formats:
        - Speaker 1: or Speaker:
        - JOHN: or John:
        - [Speaker 1]: or [John]:
        - >> Speaker 1: or >> John:
        - **Speaker 1**: or **John**:

        Args:
            line: Input line with potential speaker label

        Returns:
            (speaker_name, line_without_speaker)
        """
        patterns = [
            r'^(Speaker\s*\d*)\s*:\s*',                          # Speaker 1: or Speaker:
            r'^([A-Z][a-z]+)\s*:\s*',                            # JOHN: or John:
            r'^\[(Speaker\s*\d*|[A-Z][a-z]+)\]\s*:\s*',          # [Speaker 1]: or [John]:
            r'^>>\s*(Speaker\s*\d*|[A-Z][a-z]+)\s*:\s*',         # >> Speaker 1:
            r'^\*\*(Speaker\s*\d*|[A-Z][a-z]+)\*\*\s*:\s*',      # **Speaker 1**:
        ]

        for pattern in patterns:
            match = re.match(pattern, line, flags=re.IGNORECASE)
            if match:
                speaker = match.group(1)
                remaining_text = line[match.end():]
                return speaker, remaining_text

        # No speaker found
        return None, line

    def _split_into_sentences(self, lines_with_metadata: List[Dict]) -> List[Dict]:
        """
        Split lines into sentences while preserving metadata.

        Args:
            lines_with_metadata: Lines with timestamp/speaker metadata

        Returns:
            Sentences with metadata (each sentence inherits line's metadata)
        """
        from .transcript_cleaner import SentenceTokenizer

        tokenizer = SentenceTokenizer()
        sentences_with_metadata = []

        for line_meta in lines_with_metadata:
            text = line_meta['text']
            if not text:
                continue

            # Split into sentences
            sentences = tokenizer.tokenize(text)

            # Each sentence inherits the line's metadata
            for sentence_text in sentences:
                sentences_with_metadata.append({
                    'text': sentence_text,
                    'timestamp': line_meta['timestamp'],
                    'speaker': line_meta['speaker'],
                    'raw': line_meta['raw']
                })

        return sentences_with_metadata

    def _analyze_sentences(self, sentences_with_metadata: List[Dict]) -> List[ParsedSentence]:
        """
        Analyze sentence characteristics and create ParsedSentence objects.

        Args:
            sentences_with_metadata: Sentences with basic metadata

        Returns:
            List of ParsedSentence objects with full analysis
        """
        parsed_sentences = []

        for i, sent_meta in enumerate(sentences_with_metadata):
            text = sent_meta['text']

            # Create ParsedSentence with analysis
            parsed = ParsedSentence(
                text=text,
                raw_text=sent_meta['raw'],
                sentence_index=i,
                timestamp=sent_meta['timestamp'],
                speaker=sent_meta['speaker'],
                speaker_role=None,  # Will be set later

                # Analyze characteristics
                is_question=self._is_question(text),
                is_transition=self._is_transition(text),
                has_emphasis=self._has_emphasis(text),

                # Relationships (will be computed later)
                follows_long_pause=False,
                speaker_changed=False
            )

            parsed_sentences.append(parsed)

        return parsed_sentences

    def _is_question(self, text: str) -> bool:
        """
        Determine if sentence is a question.

        Checks:
        1. Ends with "?"
        2. Starts with question word (what, when, where, how, etc.)
        3. Has inverted word order (auxiliary verb first)

        Args:
            text: Sentence text

        Returns:
            True if sentence is a question
        """
        text_lower = text.lower().strip()

        # Check for "?"
        if text.strip().endswith('?'):
            return True

        # Check for question words at start
        for word in self.QUESTION_WORDS:
            if text_lower.startswith(word + ' ') or text_lower == word:
                return True

        return False

    def _is_transition(self, text: str) -> bool:
        """
        Determine if sentence contains transition phrases.

        Args:
            text: Sentence text

        Returns:
            True if sentence has transition phrase
        """
        return bool(self.transition_pattern.search(text))

    def _has_emphasis(self, text: str) -> bool:
        """
        Determine if sentence has emphasis markers.

        Checks for:
        - ALL CAPS words (3+ letters)
        - **bold** or __underline__
        - *italic* or _italic_

        Args:
            text: Sentence text

        Returns:
            True if sentence has emphasis markers
        """
        # Check for ALL CAPS words (3+ letters)
        if re.search(r'\b[A-Z]{3,}\b', text):
            return True

        # Check for markdown emphasis
        if re.search(r'\*\*[^*]+\*\*|__[^_]+__|[*_][^*_]+[*_]', text):
            return True

        return False

    def _compute_relationships(self, parsed_sentences: List[ParsedSentence]) -> List[ParsedSentence]:
        """
        Compute relationships between sentences (pauses, speaker changes).

        Args:
            parsed_sentences: Sentences with basic analysis

        Returns:
            Same sentences with relationships computed
        """
        for i, sentence in enumerate(parsed_sentences):
            if i == 0:
                continue

            prev_sentence = parsed_sentences[i - 1]

            # Check for long pause (>90 seconds)
            if sentence.timestamp and prev_sentence.timestamp:
                pause_duration = sentence.timestamp - prev_sentence.timestamp
                if pause_duration > 90:
                    sentence.follows_long_pause = True

            # Check for speaker change
            if sentence.speaker and prev_sentence.speaker:
                if sentence.speaker != prev_sentence.speaker:
                    sentence.speaker_changed = True

        return parsed_sentences

    def _build_metadata(self, parsed_sentences: List[ParsedSentence]) -> TranscriptMetadata:
        """
        Build overall transcript metadata from parsed sentences.

        Args:
            parsed_sentences: All parsed sentences

        Returns:
            TranscriptMetadata summary
        """
        if not parsed_sentences:
            return TranscriptMetadata(
                total_sentences=0,
                total_speakers=0
            )

        # Count speakers
        speaker_counts = Counter(
            s.speaker for s in parsed_sentences if s.speaker
        )
        speaker_names = list(speaker_counts.keys())
        total_speakers = len(speaker_names)

        # Identify primary speaker (most frequent)
        primary_speaker = None
        primary_speaker_ratio = 0.0
        if speaker_counts:
            primary_speaker = speaker_counts.most_common(1)[0][0]
            primary_speaker_ratio = speaker_counts[primary_speaker] / len(parsed_sentences)

        # Assign speaker roles (primary = instructor, others = participants)
        for sentence in parsed_sentences:
            if sentence.speaker:
                if sentence.speaker == primary_speaker:
                    sentence.speaker_role = "instructor"
                else:
                    sentence.speaker_role = "participant"

        # Compute duration
        timestamps = [s.timestamp for s in parsed_sentences if s.timestamp is not None]
        duration_seconds = max(timestamps) if timestamps else None
        has_timestamps = len(timestamps) > 0

        # Count characteristics
        question_count = sum(1 for s in parsed_sentences if s.is_question)
        transition_count = sum(1 for s in parsed_sentences if s.is_transition)

        # Detect Q&A sections (questions from participants)
        has_qa_sections = any(
            s.is_question and s.speaker_role == "participant"
            for s in parsed_sentences
        )

        return TranscriptMetadata(
            total_sentences=len(parsed_sentences),
            total_speakers=total_speakers,
            speaker_names=speaker_names,
            duration_seconds=duration_seconds,
            has_timestamps=has_timestamps,
            primary_speaker=primary_speaker,
            primary_speaker_ratio=primary_speaker_ratio,
            has_qa_sections=has_qa_sections,
            question_count=question_count,
            transition_count=transition_count
        )
