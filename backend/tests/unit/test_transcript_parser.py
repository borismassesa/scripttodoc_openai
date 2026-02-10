"""
Unit tests for transcript parser.
Tests timestamp extraction, speaker detection, and sentence analysis.
"""

import pytest
from script_to_doc.transcript_parser import TranscriptParser, ParsedSentence, TranscriptMetadata


class TestTimestampExtraction:
    """Test timestamp extraction in various formats."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_bracketed_timestamp(self):
        """Test [HH:MM:SS] format."""
        timestamp, text = self.parser._extract_timestamp("[00:01:05] Some text here")
        assert timestamp == 65.0  # 1 min 5 sec = 65 seconds
        assert text == "Some text here"

    def test_parenthesized_timestamp(self):
        """Test (HH:MM:SS) format."""
        timestamp, text = self.parser._extract_timestamp("(00:02:30) Some text here")
        assert timestamp == 150.0  # 2 min 30 sec
        assert text == "Some text here"

    def test_angle_bracket_timestamp(self):
        """Test <HH:MM:SS> format."""
        timestamp, text = self.parser._extract_timestamp("<00:00:15> Some text here")
        assert timestamp == 15.0
        assert text == "Some text here"

    def test_dash_timestamp(self):
        """Test HH:MM:SS - format."""
        timestamp, text = self.parser._extract_timestamp("00:03:45 - Some text here")
        assert timestamp == 225.0  # 3 min 45 sec
        assert text == "Some text here"

    def test_no_timestamp(self):
        """Test line without timestamp."""
        timestamp, text = self.parser._extract_timestamp("Just plain text")
        assert timestamp is None
        assert text == "Just plain text"

    def test_hours_minutes_seconds(self):
        """Test full HH:MM:SS with hours."""
        timestamp, text = self.parser._extract_timestamp("[01:15:30] Text")
        assert timestamp == 4530.0  # 1 hour 15 min 30 sec
        assert text == "Text"


class TestSpeakerExtraction:
    """Test speaker extraction in various formats."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_speaker_with_number(self):
        """Test 'Speaker 1:' format."""
        speaker, text = self.parser._extract_speaker("Speaker 1: Hello everyone")
        assert speaker == "Speaker 1"
        assert text == "Hello everyone"

    def test_speaker_without_number(self):
        """Test 'Speaker:' format."""
        speaker, text = self.parser._extract_speaker("Speaker: Hello everyone")
        assert speaker == "Speaker"
        assert text == "Hello everyone"

    def test_name_speaker(self):
        """Test 'JOHN:' or 'John:' format."""
        speaker, text = self.parser._extract_speaker("John: Hello everyone")
        assert speaker == "John"
        assert text == "Hello everyone"

    def test_bracketed_speaker(self):
        """Test '[Speaker 1]:' format."""
        speaker, text = self.parser._extract_speaker("[Speaker 2]: Hello everyone")
        assert speaker == "Speaker 2"
        assert text == "Hello everyone"

    def test_arrow_speaker(self):
        """Test '>> Speaker 1:' format."""
        speaker, text = self.parser._extract_speaker(">> Speaker 1: Hello everyone")
        assert speaker == "Speaker 1"
        assert text == "Hello everyone"

    def test_bold_speaker(self):
        """Test '**Speaker 1**:' format."""
        speaker, text = self.parser._extract_speaker("**Speaker 1**: Hello everyone")
        assert speaker == "Speaker 1"
        assert text == "Hello everyone"

    def test_no_speaker(self):
        """Test line without speaker."""
        speaker, text = self.parser._extract_speaker("Just plain text")
        assert speaker is None
        assert text == "Just plain text"


class TestQuestionDetection:
    """Test question detection logic."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_question_mark(self):
        """Test detection of sentence ending with ?"""
        assert self.parser._is_question("Is this a question?")
        assert not self.parser._is_question("This is not a question")

    def test_question_words(self):
        """Test detection of questions starting with question words."""
        assert self.parser._is_question("What is the answer")
        assert self.parser._is_question("How do I do this")
        assert self.parser._is_question("When should we start")
        assert self.parser._is_question("Where can I find it")
        assert self.parser._is_question("Why did this happen")
        assert self.parser._is_question("Who is responsible")

    def test_can_could_would(self):
        """Test auxiliary verb questions."""
        assert self.parser._is_question("Can you help me")
        assert self.parser._is_question("Could this work")
        assert self.parser._is_question("Would that be okay")
        assert self.parser._is_question("Should I proceed")

    def test_non_question(self):
        """Test non-question sentences."""
        assert not self.parser._is_question("This is a statement")
        assert not self.parser._is_question("Navigate to the portal")
        assert not self.parser._is_question("Click the button")


class TestTransitionDetection:
    """Test transition phrase detection."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_explicit_transitions(self):
        """Test explicit transition phrases."""
        assert self.parser._is_transition("Now let's move on to the next topic")
        assert self.parser._is_transition("Okay, let's talk about authentication")
        assert self.parser._is_transition("Next, we'll deploy the application")
        assert self.parser._is_transition("Moving on to step 2")

    def test_section_markers(self):
        """Test section marker phrases."""
        assert self.parser._is_transition("First, we need to configure the settings")
        assert self.parser._is_transition("Second, deploy the application")
        assert self.parser._is_transition("Finally, test the deployment")

    def test_topic_introductions(self):
        """Test topic introduction phrases."""
        assert self.parser._is_transition("Let's talk about resource groups")
        assert self.parser._is_transition("Let's discuss the pricing tiers")
        assert self.parser._is_transition("The next thing is deployment")

    def test_non_transition(self):
        """Test non-transition sentences."""
        assert not self.parser._is_transition("Click the button")
        assert not self.parser._is_transition("Navigate to the portal")
        assert not self.parser._is_transition("This is a regular instruction")


class TestEmphasisDetection:
    """Test emphasis marker detection."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_all_caps(self):
        """Test ALL CAPS detection."""
        assert self.parser._has_emphasis("This is VERY important")
        assert self.parser._has_emphasis("CRITICAL: Do not skip this step")
        assert not self.parser._has_emphasis("This is normal text")

    def test_markdown_bold(self):
        """Test **bold** detection."""
        assert self.parser._has_emphasis("This is **very important** text")
        assert self.parser._has_emphasis("__This is underlined__")

    def test_markdown_italic(self):
        """Test *italic* detection."""
        assert self.parser._has_emphasis("This is *emphasized* text")
        assert self.parser._has_emphasis("This is _emphasized_ text")

    def test_no_emphasis(self):
        """Test normal text without emphasis."""
        assert not self.parser._has_emphasis("This is normal text")
        assert not self.parser._has_emphasis("A sentence without any emphasis")


class TestFullParsing:
    """Test full transcript parsing end-to-end."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_sample_meeting_format(self):
        """Test parsing sample_meeting.txt format."""
        transcript = """[00:00:05] Speaker 1: Good morning everyone. Today we're going to set up Azure.

[00:00:23] Speaker 2: Great! Let's get started.

[00:00:28] Speaker 1: First, you need to open the Azure portal.

[00:01:05] Speaker 2: Right, and if you don't see it, you can search for it?

[00:01:10] Speaker 1: Exactly! Now let's move on to creating a resource group."""

        parsed_sentences, metadata = self.parser.parse(transcript)

        # Check sentence count
        assert len(parsed_sentences) > 0
        assert metadata.total_sentences == len(parsed_sentences)

        # Check first sentence
        first = parsed_sentences[0]
        assert first.text.startswith("Good morning")
        assert first.timestamp == 5.0
        assert first.speaker == "Speaker 1"
        assert first.speaker_role == "instructor"
        assert not first.is_question

        # Check speaker metadata
        assert metadata.total_speakers == 2
        assert metadata.primary_speaker == "Speaker 1"
        assert metadata.primary_speaker_ratio > 0.5

        # Check question detection
        question_sentences = [s for s in parsed_sentences if s.is_question]
        assert len(question_sentences) > 0

        # Check transition detection
        transition_sentences = [s for s in parsed_sentences if s.is_transition]
        assert len(transition_sentences) > 0

    def test_no_timestamps(self):
        """Test parsing transcript without timestamps."""
        transcript = """Speaker 1: Hello everyone.
Speaker 2: Hi there!
Speaker 1: Let's begin the tutorial."""

        parsed_sentences, metadata = self.parser.parse(transcript)

        assert len(parsed_sentences) > 0
        assert not metadata.has_timestamps
        assert metadata.duration_seconds is None

        # Should still detect speakers
        assert metadata.total_speakers == 2
        assert metadata.primary_speaker == "Speaker 1"

    def test_no_speakers(self):
        """Test parsing transcript without speaker labels."""
        transcript = """[00:00:05] Hello everyone. Let's get started.
[00:00:15] First, navigate to the portal.
[00:00:30] Click the resource groups button."""

        parsed_sentences, metadata = self.parser.parse(transcript)

        assert len(parsed_sentences) > 0
        assert metadata.has_timestamps
        assert metadata.total_speakers == 0

        # Should still extract timestamps
        first = parsed_sentences[0]
        assert first.timestamp == 5.0

    def test_plain_text_no_metadata(self):
        """Test parsing plain text without any metadata."""
        transcript = """Hello everyone. Let's get started with Azure.
First, navigate to the portal. Then click resource groups.
Now let's create a new resource group."""

        parsed_sentences, metadata = self.parser.parse(transcript)

        assert len(parsed_sentences) > 0
        assert not metadata.has_timestamps
        assert metadata.total_speakers == 0

        # Should still detect transitions
        transition_sentences = [s for s in parsed_sentences if s.is_transition]
        assert len(transition_sentences) > 0

    def test_speaker_changes(self):
        """Test speaker change detection."""
        transcript = """Speaker 1: Hello.
Speaker 2: Hi there.
Speaker 1: How are you?"""

        parsed_sentences, metadata = self.parser.parse(transcript)

        assert len(parsed_sentences) >= 3

        # First sentence: no speaker change (it's the first)
        assert not parsed_sentences[0].speaker_changed

        # Second sentence: speaker changed
        if len(parsed_sentences) > 1:
            assert parsed_sentences[1].speaker_changed

        # Third sentence: speaker changed back
        if len(parsed_sentences) > 2:
            assert parsed_sentences[2].speaker_changed

    def test_long_pauses(self):
        """Test long pause detection (>90 seconds)."""
        transcript = """[00:00:05] Speaker 1: First topic here.
[00:02:00] Speaker 1: New topic after long pause."""

        parsed_sentences, metadata = self.parser.parse(transcript)

        if len(parsed_sentences) > 1:
            # Second sentence should follow a long pause (115 seconds)
            assert parsed_sentences[1].follows_long_pause


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        self.parser = TranscriptParser()

    def test_empty_transcript(self):
        """Test parsing empty transcript."""
        parsed_sentences, metadata = self.parser.parse("")

        assert len(parsed_sentences) == 0
        assert metadata.total_sentences == 0
        assert metadata.total_speakers == 0

    def test_only_whitespace(self):
        """Test parsing transcript with only whitespace."""
        parsed_sentences, metadata = self.parser.parse("\n\n   \n\t\n")

        assert len(parsed_sentences) == 0
        assert metadata.total_sentences == 0

    def test_malformed_timestamps(self):
        """Test handling malformed timestamps."""
        transcript = """[invalid] Speaker 1: Hello
[99:99:99] Speaker 2: Hi
Normal text without any format"""

        parsed_sentences, metadata = self.parser.parse(transcript)

        # Should still parse the text, ignoring invalid timestamps
        assert len(parsed_sentences) > 0

    def test_very_long_sentence(self):
        """Test handling very long sentences."""
        long_text = " ".join(["word"] * 500)
        transcript = f"[00:00:05] Speaker 1: {long_text}"

        parsed_sentences, metadata = self.parser.parse(transcript)

        assert len(parsed_sentences) > 0
        first = parsed_sentences[0]
        assert len(first.text) > 1000


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
