"""
Transcript cleaning and normalization module.
Removes timestamps, filler words, speaker labels, and other noise.
"""

import re
from typing import List, Set


class TranscriptCleaner:
    """Clean and normalize transcript text for processing."""
    
    # Common filler words to remove
    DEFAULT_FILLER_WORDS = {
        "um", "uh", "umm", "uhh", "er", "ah", "like", "you know",
        "i mean", "sort of", "kind of", "basically", "actually",
        "literally", "right", "okay", "ok", "yeah", "yep", "mhm"
    }
    
    # Common transcriber tags to remove
    TRANSCRIBER_TAGS = {
        "[inaudible]", "[crosstalk]", "[laughter]", "[music]",
        "[applause]", "[silence]", "(inaudible)", "(crosstalk)",
        "(laughter)", "(laughs)", "(music)", "(applause)", "(silence)",
        "[unintelligible]", "(unintelligible)"
    }
    
    # Repetitive template phrases that lower source quality (common in training transcripts)
    REPETITIVE_TEMPLATES = [
        r"continuing in our hands[- ]on section",
        r"let's continue with (?:the|our) hands[- ]on",
        r"moving on to (?:the )?next (?:part|section|topic)",
        r"as (?:i|we) mentioned (?:before|earlier)",
        r"like (?:i|we) said",
        r"(?:so|now),? let's move on",
        r"(?:okay|alright),? (?:so|now)",
        r"and that's it for (?:this|that) (?:part|section)",
        r"we(?:'ll| will) get (?:back )?to (?:this|that) later",
        r"we(?:'ll| will) discuss (?:this|that) (?:more )?(?:later|soon)"
    ]
    
    # Visual/structural markers to PRESERVE (important for understanding)
    VISUAL_MARKERS = [
        r"\[screen shows[^\]]*\]",
        r"\[diagram[^\]]*\]",
        r"\[slide[^\]]*\]",
        r"\[demo[^\]]*\]",
        r"\[code[^\]]*\]",
        r"\[architecture[^\]]*\]",
        r"\[showing[^\]]*\]"
    ]
    
    def __init__(self, custom_filler_words: List[str] = None):
        """
        Initialize cleaner with optional custom filler words.
        
        Args:
            custom_filler_words: Additional filler words to remove
        """
        self.filler_words = self.DEFAULT_FILLER_WORDS.copy()
        if custom_filler_words:
            self.filler_words.update(word.lower() for word in custom_filler_words)
    
    def remove_timestamps(self, text: str) -> str:
        """
        Remove timestamps in various formats.
        
        Supported formats:
        - [00:15:32]
        - [00:15:32.123]
        - (00:15:32)
        - 00:15:32 -
        - <00:15:32>
        
        Args:
            text: Input text with timestamps
            
        Returns:
            Text without timestamps
        """
        # Pattern: [HH:MM:SS] or [HH:MM:SS.mmm] or (HH:MM:SS)
        patterns = [
            r'\[\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?\]',  # [00:15:32] or [00:15:32.123]
            r'\(\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?\)',  # (00:15:32)
            r'<\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?>',   # <00:15:32>
            r'\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?\s*-\s*',  # 00:15:32 -
            r'^\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?\s+',  # 00:15:32 at start of line
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text)
        
        return text
    
    def remove_speaker_labels(self, text: str) -> str:
        """
        Remove speaker labels and identifiers.
        
        Formats:
        - Speaker 1:
        - JOHN:
        - Speaker:
        - [John]:
        - >> Speaker 1:
        
        Args:
            text: Input text with speaker labels
            
        Returns:
            Text without speaker labels
        """
        patterns = [
            r'^(?:Speaker\s*\d*|[A-Z][a-z]+)\s*:\s*',  # Speaker 1: or JOHN:
            r'^\[(?:Speaker\s*\d*|[A-Z][a-z]+)\]\s*:\s*',  # [Speaker 1]:
            r'^>>\s*(?:Speaker\s*\d*|[A-Z][a-z]+)\s*:\s*',  # >> Speaker 1:
            r'^\*\*(?:Speaker\s*\d*|[A-Z][a-z]+)\*\*\s*:\s*',  # **Speaker 1**:
        ]
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            for pattern in patterns:
                line = re.sub(pattern, '', line, flags=re.IGNORECASE | re.MULTILINE)
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def remove_transcriber_tags(self, text: str) -> str:
        """
        Remove transcriber annotations like [inaudible], (laughs), etc.
        BUT preserve visual/structural markers.
        
        Args:
            text: Input text with transcriber tags
            
        Returns:
            Text without transcriber tags (but with visual markers preserved)
        """
        # Remove known tags
        for tag in self.TRANSCRIBER_TAGS:
            text = text.replace(tag, '')
        
        # Remove remaining bracketed/parenthesized tags EXCEPT visual markers
        # First, temporarily replace visual markers with placeholders
        preserved_markers = {}
        marker_placeholder_template = "__VISUAL_MARKER_{}_"
        
        for i, pattern in enumerate(self.VISUAL_MARKERS):
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
            # Process matches in reverse to maintain indices
            for j, match in reversed(list(enumerate(matches))):
                placeholder = marker_placeholder_template.format(f"{i}_{j}")
                preserved_markers[placeholder] = match.group(0)
                text = text[:match.start()] + placeholder + text[match.end():]
        
        # Now remove other bracketed/parenthesized content
        text = re.sub(r'\[[\w\s]+\]', '', text)
        text = re.sub(r'\([\w\s]+\)', '', text)
        
        # Restore visual markers
        for placeholder, original in preserved_markers.items():
            text = text.replace(placeholder, original)
        
        return text
    
    def remove_filler_words(self, text: str) -> str:
        """
        Remove filler words and verbal tics.
        
        Args:
            text: Input text with filler words
            
        Returns:
            Text without filler words
        """
        # Create pattern for filler words
        # Use word boundaries to avoid partial matches
        for filler in self.filler_words:
            # Handle multi-word fillers
            pattern = r'\b' + re.escape(filler) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def remove_repetitive_templates(self, text: str) -> str:
        """
        Remove repetitive template phrases that add no value.
        
        These are common transition phrases used by instructors that get
        repeated many times and lower source quality when cited.
        
        Args:
            text: Input text with template phrases
            
        Returns:
            Text without repetitive templates
        """
        for pattern in self.REPETITIVE_TEMPLATES:
            # Remove the phrase (case-insensitive)
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def detect_and_merge_duplicates(self, text: str, similarity_threshold: float = 0.9) -> str:
        """
        Detect near-duplicate sentences and keep only one.
        
        This handles cases where the same content is repeated verbatim or nearly
        verbatim, which causes citation problems.
        
        Args:
            text: Input text
            similarity_threshold: How similar sentences need to be (0.0-1.0)
            
        Returns:
            Text with duplicate sentences removed
        """
        import difflib
        
        sentences = text.split('. ')
        unique_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if this sentence is similar to any already kept
            is_duplicate = False
            for kept_sentence in unique_sentences:
                similarity = difflib.SequenceMatcher(None, sentence.lower(), kept_sentence.lower()).ratio()
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    def remove_webvtt_artifacts(self, text: str) -> str:
        """
        Remove WEBVTT format artifacts.
        
        WEBVTT headers:
        - WEBVTT
        - NOTE ...
        - STYLE ...
        
        Args:
            text: Input text potentially containing WEBVTT artifacts
            
        Returns:
            Text without WEBVTT artifacts
        """
        # Remove WEBVTT header
        text = re.sub(r'WEBVTT\s*', '', text, flags=re.IGNORECASE)
        
        # Remove NOTE blocks
        text = re.sub(r'NOTE\s+[^\n]*\n', '', text, flags=re.IGNORECASE)
        
        # Remove STYLE blocks
        text = re.sub(r'STYLE\s+[^\n]*\n', '', text, flags=re.IGNORECASE)
        
        # Remove position/alignment tags
        text = re.sub(r'<v\s+[^>]+>', '', text)
        text = re.sub(r'</v>', '', text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace: collapse multiple spaces, fix line breaks.
        
        Args:
            text: Input text with irregular whitespace
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove spaces at start/end of lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove empty lines at start and end
        text = text.strip()
        
        return text
    
    def fix_punctuation(self, text: str) -> str:
        """
        Fix common punctuation issues.
        
        - Add space after punctuation if missing
        - Remove space before punctuation
        - Capitalize after sentence end
        
        Args:
            text: Input text with punctuation issues
            
        Returns:
            Text with fixed punctuation
        """
        # Add space after punctuation if missing
        text = re.sub(r'([.!?,;:])([A-Za-z])', r'\1 \2', text)
        
        # Remove space before punctuation
        text = re.sub(r'\s+([.!?,;:])', r'\1', text)
        
        # Fix multiple punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        return text
    
    def normalize(self, text: str, remove_duplicates: bool = True) -> str:
        """
        Apply full cleaning pipeline.
        
        Pipeline order:
        1. Remove WEBVTT artifacts
        2. Remove timestamps
        3. Remove speaker labels
        4. Remove transcriber tags (preserve visual markers)
        5. Remove filler words
        6. Remove repetitive templates (NEW)
        7. Detect and merge duplicates (NEW - optional)
        8. Fix punctuation
        9. Normalize whitespace
        
        Args:
            text: Raw transcript text
            remove_duplicates: Whether to deduplicate similar sentences
            
        Returns:
            Cleaned and normalized text
        """
        # Apply cleaning steps in order
        text = self.remove_webvtt_artifacts(text)
        text = self.remove_timestamps(text)
        text = self.remove_speaker_labels(text)
        text = self.remove_transcriber_tags(text)  # Now preserves visual markers
        text = self.remove_filler_words(text)
        text = self.remove_repetitive_templates(text)  # Remove template phrases
        if remove_duplicates:
            text = self.detect_and_merge_duplicates(text)  # Deduplicate content
        text = self.fix_punctuation(text)
        text = self.normalize_whitespace(text)
        
        return text


class SentenceTokenizer:
    """Break transcript into sentences using NLTK."""
    
    def __init__(self):
        """Initialize tokenizer and download NLTK data if needed."""
        try:
            import nltk
            # Try to use punkt tokenizer
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                # Download if not available
                nltk.download('punkt', quiet=True)
            
            self.tokenizer = nltk.tokenize.sent_tokenize
        except Exception as e:
            # Fallback to simple regex tokenizer
            print(f"Warning: NLTK not available ({e}), using simple tokenizer")
            self.tokenizer = self._simple_tokenize
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """
        Simple fallback sentence tokenizer using regex.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Split on sentence-ending punctuation followed by space and capital
        sentences = re.split(r'([.!?]+)\s+(?=[A-Z])', text)
        
        # Recombine punctuation with sentences
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + sentences[i + 1]
            result.append(sentence.strip())
        
        # Add last sentence if exists
        if sentences and len(sentences) % 2 == 1:
            result.append(sentences[-1].strip())
        
        return [s for s in result if s]
    
    def tokenize(self, text: str) -> List[str]:
        """
        Break text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        sentences = self.tokenizer(text)
        
        # Filter out very short sentences (likely artifacts)
        sentences = [s for s in sentences if len(s.strip()) > 3]

        return sentences


class TranscriptChunker:
    """
    Split transcript into focused chunks for better LLM grounding.

    Instead of sending the entire transcript to the LLM, we split it into
    target_steps chunks. Each chunk contains roughly equal content and will
    generate 1 step. This improves:
    - Focus on relevant sections
    - Better word matching (less irrelevant content)
    - More precise step generation
    - Reduced token usage per call
    """

    def __init__(self, sentence_tokenizer: SentenceTokenizer = None):
        """
        Initialize chunker.

        Args:
            sentence_tokenizer: Optional tokenizer to use. If None, creates new one.
        """
        self.tokenizer = sentence_tokenizer or SentenceTokenizer()

    def chunk_by_sentences(
        self,
        transcript: str,
        target_chunks: int,
        min_sentences_per_chunk: int = 2,
        max_sentences_per_chunk: int = 20
    ) -> List[str]:
        """
        Split transcript into chunks with roughly equal sentence counts.

        Args:
            transcript: Full transcript text
            target_chunks: Desired number of chunks (usually = target_steps)
            min_sentences_per_chunk: Minimum sentences per chunk (for quality)
            max_sentences_per_chunk: Maximum sentences per chunk (for token limits)

        Returns:
            List of chunk strings, each containing multiple sentences
        """
        # Tokenize into sentences
        sentences = self.tokenizer.tokenize(transcript)

        if not sentences:
            return []

        total_sentences = len(sentences)

        # If we have fewer sentences than target chunks, return sentence-per-chunk
        if total_sentences <= target_chunks:
            return sentences

        # Calculate sentences per chunk (ceiling division)
        sentences_per_chunk = max(
            min_sentences_per_chunk,
            min(max_sentences_per_chunk, -(-total_sentences // target_chunks))  # Ceiling division
        )

        # Create chunks
        chunks = []
        for i in range(0, total_sentences, sentences_per_chunk):
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            # Join sentences with space
            chunk_text = ' '.join(chunk_sentences)
            chunks.append(chunk_text.strip())

        return chunks

    def chunk_by_paragraphs(
        self,
        transcript: str,
        target_chunks: int
    ) -> List[str]:
        """
        Split transcript into chunks based on paragraph boundaries.

        This preserves natural topic boundaries in the transcript.

        Args:
            transcript: Full transcript text
            target_chunks: Desired number of chunks

        Returns:
            List of chunk strings
        """
        # Split by double newlines (paragraph boundaries)
        paragraphs = [p.strip() for p in transcript.split('\n\n') if p.strip()]

        if not paragraphs:
            # Fallback to sentence-based chunking
            return self.chunk_by_sentences(transcript, target_chunks)

        if len(paragraphs) <= target_chunks:
            # Already have fewer paragraphs than target chunks
            return paragraphs

        # Group paragraphs into target_chunks groups
        paragraphs_per_chunk = -(-len(paragraphs) // target_chunks)  # Ceiling division

        chunks = []
        for i in range(0, len(paragraphs), paragraphs_per_chunk):
            chunk_paragraphs = paragraphs[i:i + paragraphs_per_chunk]
            # Join paragraphs with double newline
            chunk_text = '\n\n'.join(chunk_paragraphs)
            chunks.append(chunk_text.strip())

        return chunks

    def chunk_smart(
        self,
        transcript: str,
        target_chunks: int,
        prefer_paragraphs: bool = True
    ) -> List[str]:
        """
        Smart chunking that tries paragraph-based first, falls back to sentences.

        Args:
            transcript: Full transcript text
            target_chunks: Desired number of chunks
            prefer_paragraphs: If True, prefer paragraph boundaries

        Returns:
            List of chunk strings
        """
        if prefer_paragraphs and '\n\n' in transcript:
            # Try paragraph-based chunking
            paragraph_chunks = self.chunk_by_paragraphs(transcript, target_chunks)

            # ⭐ FIXED: Only accept paragraph chunks if within ±1 of target (stricter)
            # This gives users more precise control over step count
            if abs(len(paragraph_chunks) - target_chunks) <= 1:
                return paragraph_chunks

        # Fall back to sentence-based chunking for exact control
        return self.chunk_by_sentences(transcript, target_chunks)

    def get_chunk_metadata(self, chunks: List[str]) -> List[dict]:
        """
        Get metadata about each chunk for debugging/analysis.

        Args:
            chunks: List of chunk strings

        Returns:
            List of metadata dicts with chunk stats
        """
        metadata = []

        for i, chunk in enumerate(chunks):
            sentences = self.tokenizer.tokenize(chunk)
            words = chunk.split()

            metadata.append({
                'chunk_index': i,
                'char_count': len(chunk),
                'word_count': len(words),
                'sentence_count': len(sentences),
                'preview': chunk[:100] + '...' if len(chunk) > 100 else chunk
            })

        return metadata

