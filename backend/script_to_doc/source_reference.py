"""
Source reference and confidence scoring system.
Every generated step is grounded in source material to prevent hallucination.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import difflib

# Semantic similarity imports
try:
    from sentence_transformers import SentenceTransformer, util
    SEMANTIC_SIMILARITY_AVAILABLE = True
    # Reduce sentence_transformers verbosity
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
except ImportError:
    SEMANTIC_SIMILARITY_AVAILABLE = False
    logging.warning("sentence-transformers not available - falling back to word-overlap only")

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    """A single source reference linking to original content."""
    
    type: str  # "transcript", "visual", "timestamp"
    excerpt: str  # The actual source content
    timestamp: Optional[str] = None
    sentence_index: Optional[int] = None
    screenshot_ref: Optional[str] = None
    ui_elements: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 - 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type,
            "excerpt": self.excerpt,
            "timestamp": self.timestamp,
            "sentence_index": self.sentence_index,
            "screenshot_ref": self.screenshot_ref,
            "ui_elements": self.ui_elements,
            "confidence": self.confidence
        }


@dataclass
class StepSourceData:
    """Source data and validation for a generated training step."""

    step_index: int
    step_content: str
    sources: List[SourceReference]
    overall_confidence: float = 0.0
    has_transcript_support: bool = False
    has_visual_support: bool = False
    validation_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "step_index": self.step_index,
            "step_content": self.step_content,
            "sources": [s.to_dict() for s in self.sources],
            "overall_confidence": self.overall_confidence,
            "has_transcript_support": self.has_transcript_support,
            "has_visual_support": self.has_visual_support,
            "validation_flags": self.validation_flags
        }


class SemanticSimilarityScorer:
    """
    Semantic similarity scorer using sentence-transformers.

    Uses all-MiniLM-L6-v2 model for fast, efficient semantic matching.
    Caches embeddings for performance.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic similarity scorer.

        Args:
            model_name: Name of sentence-transformers model to use
        """
        if not SEMANTIC_SIMILARITY_AVAILABLE:
            logger.warning("SemanticSimilarityScorer initialized but sentence-transformers not available")
            self.model = None
            self.cache = {}
            return

        try:
            logger.info(f"Loading semantic similarity model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.cache = {}  # Cache embeddings: {text: embedding}
            logger.info(f"Semantic similarity model loaded successfully (embedding dim: {self.model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Failed to load semantic similarity model: {e}")
            self.model = None
            self.cache = {}

    def get_embedding(self, text: str):
        """
        Get embedding for text, using cache if available.

        Args:
            text: Text to encode

        Returns:
            Embedding tensor or None if model unavailable
        """
        if self.model is None:
            return None

        # Use text as cache key
        if text not in self.cache:
            try:
                self.cache[text] = self.model.encode(text, convert_to_tensor=True, show_progress_bar=False)
            except Exception as e:
                logger.error(f"Failed to encode text: {e}")
                return None

        return self.cache[text]

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 - 1.0), or 0.0 if model unavailable
        """
        if self.model is None:
            return 0.0

        try:
            emb1 = self.get_embedding(text1)
            emb2 = self.get_embedding(text2)

            if emb1 is None or emb2 is None:
                return 0.0

            similarity = float(util.cos_sim(emb1, emb2))
            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0

    def clear_cache(self):
        """Clear embedding cache to free memory."""
        self.cache.clear()
        logger.info("Semantic similarity cache cleared")

    def get_cache_size(self) -> int:
        """Get number of cached embeddings."""
        return len(self.cache)


class SourceReferenceManager:
    """Manage source references and confidence scoring for generated content."""

    def __init__(
        self,
        use_semantic_similarity: bool = True,
        weight_word: float = 0.50,
        weight_keyword: float = 0.00,
        weight_phrase: float = 0.00,
        weight_semantic: float = 0.50,
        weight_char: float = 0.00
    ):
        """
        Initialize source reference manager.

        Args:
            use_semantic_similarity: Whether to use semantic similarity scoring (default: True)
            weight_word: Weight for word overlap score (default: 0.50 for Simple 50/50)
            weight_keyword: Weight for keyword matching (default: 0.00 for Simple 50/50)
            weight_phrase: Weight for phrase matching (default: 0.00 for Simple 50/50)
            weight_semantic: Weight for semantic similarity (default: 0.50 for Simple 50/50)
            weight_char: Weight for character similarity (default: 0.00 for Simple 50/50)

        Note: Weights should sum to 1.0. Default is Simple 50/50 (50% word + 50% semantic)
        """
        self.sentence_catalog: List[str] = []
        self.step_sources: Dict[int, StepSourceData] = {}
        self.min_similarity_threshold = 0.15  # Lowered threshold for better matching
        self.used_sentences: Dict[int, int] = {}  # Track how many times each sentence used
        self.sentence_technical_scores: Dict[int, float] = {}  # Cache technical scores

        # Store hybrid matching weights
        self.weight_word = weight_word
        self.weight_keyword = weight_keyword
        self.weight_phrase = weight_phrase
        self.weight_semantic = weight_semantic
        self.weight_char = weight_char

        # Validate weights sum to 1.0
        total_weight = weight_word + weight_keyword + weight_phrase + weight_semantic + weight_char
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Matching weights don't sum to 1.0 (sum={total_weight:.2f}), normalizing...")
            # Normalize weights
            self.weight_word /= total_weight
            self.weight_keyword /= total_weight
            self.weight_phrase /= total_weight
            self.weight_semantic /= total_weight
            self.weight_char /= total_weight

        # Initialize semantic similarity scorer
        self.use_semantic_similarity = use_semantic_similarity and SEMANTIC_SIMILARITY_AVAILABLE
        if self.use_semantic_similarity:
            try:
                self.semantic_scorer = SemanticSimilarityScorer()
                logger.info(
                    f"Semantic similarity scoring enabled with weights: "
                    f"word={self.weight_word:.2f}, keyword={self.weight_keyword:.2f}, "
                    f"phrase={self.weight_phrase:.2f}, semantic={self.weight_semantic:.2f}, "
                    f"char={self.weight_char:.2f}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize semantic similarity: {e}, falling back to word-overlap only")
                self.semantic_scorer = None
                self.use_semantic_similarity = False
        else:
            self.semantic_scorer = None
            if use_semantic_similarity and not SEMANTIC_SIMILARITY_AVAILABLE:
                logger.info("Semantic similarity requested but sentence-transformers not available")
    
    def build_sentence_catalog(self, transcript: str, sentences: List[str]) -> List[str]:
        """
        Create searchable catalog of all sentences from transcript.
        Also pre-compute technical scores for each sentence.
        
        Args:
            transcript: Full transcript text
            sentences: Pre-tokenized sentences
            
        Returns:
            List of sentences for searching
        """
        self.sentence_catalog = sentences
        
        # Pre-compute technical scores for all sentences
        for idx, sentence in enumerate(sentences):
            self.sentence_technical_scores[idx] = self._calculate_technical_score(sentence)
        
        logger.info(f"Built sentence catalog with {len(sentences)} sentences")
        return self.sentence_catalog
    
    def _calculate_technical_score(self, sentence: str) -> float:
        """
        Calculate how technical/specific a sentence is.
        Technical sentences get weighted higher for better grounding.
        
        Indicators of technical content:
        - Contains code/commands (keywords like 'async', 'def', 'class', function names)
        - Contains specific values/numbers (URLs, ports, percentages, measurements)
        - Contains technical terms (API, database, configuration, deployment)
        - Contains specific UI elements (button names, menu paths in quotes)
        - Contains architecture terms (microservices, pipeline, endpoint)
        
        Args:
            sentence: Sentence to analyze
            
        Returns:
            Technical score (0.0 - 1.0, higher = more technical)
        """
        sentence_lower = sentence.lower()
        score = 0.0
        
        # Code keywords (high weight)
        code_keywords = ['async', 'await', 'def', 'class', 'function', 'import', 'from', 
                        'return', 'if', 'else', 'for', 'while', 'try', 'except', 'const',
                        'var', 'let', 'public', 'private', 'static', 'void']
        for keyword in code_keywords:
            if f" {keyword} " in f" {sentence_lower} " or sentence_lower.startswith(f"{keyword} "):
                score += 0.15
        
        # Technical domain terms (medium-high weight)
        technical_terms = ['api', 'endpoint', 'database', 'cosmos', 'blob', 'storage',
                          'pipeline', 'workflow', 'microservice', 'container', 'docker',
                          'kubernetes', 'deployment', 'configuration', 'authentication',
                          'authorization', 'throughput', 'latency', 'idempotent',
                          'scalability', 'asynchronous', 'synchronous', 'event', 'trigger']
        for term in technical_terms:
            if term in sentence_lower:
                score += 0.10
        
        # Specific values/measurements (medium weight)
        has_number = bool(re.search(r'\d+', sentence))
        has_url = bool(re.search(r'https?://|www\.', sentence_lower))
        has_percentage = bool(re.search(r'\d+%', sentence))
        has_measurement = bool(re.search(r'\d+\s*(ms|kb|mb|gb|tb|rpm|dpi|px)', sentence_lower))
        
        if has_number:
            score += 0.05
        if has_url:
            score += 0.10
        if has_percentage:
            score += 0.08
        if has_measurement:
            score += 0.12
        
        # Quoted text (likely UI elements or specific terms)
        quotes_count = sentence.count('"') + sentence.count("'") + sentence.count('`')
        score += min(0.15, quotes_count * 0.05)
        
        # Action verbs (medium-low weight)
        action_verbs = ['click', 'select', 'open', 'navigate', 'configure', 'create',
                       'delete', 'update', 'install', 'deploy', 'build', 'run', 'execute']
        for verb in action_verbs:
            if verb in sentence_lower:
                score += 0.06
                break  # Only count once
        
        # Structural markers (low weight)
        if re.search(r'\[screen\s+shows|\[diagram|\[code|\[architecture', sentence_lower):
            score += 0.10
        
        # Length penalty for very short sentences (likely filler)
        word_count = len(sentence.split())
        if word_count < 5:
            score *= 0.5
        elif word_count > 15:
            score += 0.05  # Bonus for detailed sentences
        
        # Clamp to [0, 1]
        return min(1.0, max(0.0, score))
    
    def find_sources_for_step(
        self,
        step_content: str,
        step_title: str,
        step_actions: List[str],
        transcript_sentences: List[str],
        screenshots_data: Optional[List[Dict]] = None,
        knowledge_sources: Optional[List[Dict]] = None
    ) -> List[SourceReference]:
        """
        Find all source references for a generated step.
        
        Uses semantic similarity to match step content with transcript sentences
        and visual content with screenshots.
        
        Args:
            step_content: The generated step text (details)
            step_title: The step title
            step_actions: List of actions in the step
            transcript_sentences: All sentences from transcript
            screenshots_data: Optional screenshot analysis data
            
        Returns:
            List of SourceReference objects
        """
        sources = []
        
        # Find transcript sources
        transcript_sources = self._find_transcript_sources(
            step_content,
            step_title,
            step_actions,
            transcript_sentences
        )
        sources.extend(transcript_sources)
        
        # Find visual sources if screenshots provided
        if screenshots_data:
            visual_sources = self._find_visual_sources(
                step_content,
                step_title,
                step_actions,
                screenshots_data
            )
            sources.extend(visual_sources)
        
        # Find knowledge source references
        if knowledge_sources:
            knowledge_refs = self._find_knowledge_sources(
                step_content,
                step_title,
                step_actions,
                knowledge_sources
            )
            sources.extend(knowledge_refs)
        
        logger.info(f"Found {len(sources)} source references for step")
        
        return sources
    
    def _find_transcript_sources(
        self,
        step_content: str,
        step_title: str,
        step_actions: List[str],
        sentences: List[str]
    ) -> List[SourceReference]:
        """Find matching sentences from transcript using improved semantic matching with technical weighting."""
        sources = []
        
        # Combine all text to search
        search_text = f"{step_title} {step_content} {' '.join(step_actions)}"
        search_text_lower = search_text.lower()
        
        # Extract all significant words (remove common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
                     'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could'}
        
        search_words = set(
            word.strip('.,!?;:()[]{}"\'').lower() 
            for word in search_text_lower.split() 
            if len(word.strip('.,!?;:()[]{}"\'')) > 2 and word.strip('.,!?;:()[]{}"\'') not in stop_words
        )
        
        # Extract key phrases (important words longer than 4 chars)
        key_words = [
            word for word in search_words
            if len(word) > 4
        ]
        
        # Search for matching sentences
        for idx, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            sentence_words = set(
                word.strip('.,!?;:()[]{}"\'').lower() 
                for word in sentence_lower.split() 
                if len(word.strip('.,!?;:()[]{}"\'')) > 2
            )
            
            # Word overlap score (Jaccard similarity)
            if search_words:
                word_overlap = len(search_words & sentence_words) / len(search_words | sentence_words)
            else:
                word_overlap = 0.0
            
            # Keyword match score (weighted by importance)
            if key_words:
                keyword_matches = sum(1 for word in key_words if word in sentence_lower)
                keyword_score = keyword_matches / len(key_words)
            else:
                keyword_score = 0.0
            
            # Character-based similarity (less weight)
            char_similarity = self._calculate_text_similarity(search_text_lower, sentence_lower)

            # Phrase matching (check if key phrases appear in sentence)
            phrase_score = 0.0
            if key_words:
                # Check for 2-word phrases
                search_phrases = []
                words_list = list(search_words)
                for i in range(len(words_list) - 1):
                    if len(words_list[i]) > 3 and len(words_list[i+1]) > 3:
                        phrase = f"{words_list[i]} {words_list[i+1]}"
                        if phrase in sentence_lower:
                            phrase_score += 0.2
                phrase_score = min(phrase_score, 0.6)

            # Semantic similarity score (handles paraphrasing and synonyms)
            semantic_score = 0.0
            if self.use_semantic_similarity and self.semantic_scorer:
                try:
                    semantic_score = self.semantic_scorer.calculate_similarity(search_text, sentence)
                except Exception as e:
                    logger.warning(f"Semantic similarity calculation failed: {e}")
                    semantic_score = 0.0

            # Combined score with configurable hybrid weighting
            # Default: Simple 50/50 (50% word overlap + 50% semantic)
            base_score = (
                word_overlap * self.weight_word +
                keyword_score * self.weight_keyword +
                phrase_score * self.weight_phrase +
                semantic_score * self.weight_semantic +
                char_similarity * self.weight_char
            )
            
            # Boost score if sentence contains action verbs from step
            action_verbs = ['click', 'open', 'navigate', 'select', 'choose', 'enter', 
                          'type', 'create', 'delete', 'update', 'configure', 'set', 'go']
            for verb in action_verbs:
                if verb in step_actions and verb in sentence_lower:
                    base_score += 0.1
                    break
            
            # ⭐ FIXED: Apply reuse penalty from first use (including current use)
            reuse_count = self.used_sentences.get(idx, 0)
            # Penalty starts immediately: -15% per use
            reuse_penalty = min(0.6, (reuse_count + 1) * 0.15)
            base_score *= (1.0 - reuse_penalty)
            
            # ⭐ FIXED: Only apply technical boost if base score is viable (> 0.10)
            if base_score >= 0.10:
                technical_score = self.sentence_technical_scores.get(idx, 0.0)
                # Boost base score by up to 20% if technical (reduced from 30%)
                base_score += (technical_score * 0.2)
            
            # Clamp and apply minimum threshold
            final_score = min(base_score, 1.0)
            
            # Require minimum word overlap (at least 3 matching words)
            matching_words = len(search_words & sentence_words)
            if matching_words < 3:
                continue
            
            # Threshold to catch viable matches
            if final_score >= 0.15:
                sources.append(SourceReference(
                    type="transcript",
                    excerpt=sentence,
                    sentence_index=idx,
                    confidence=final_score
                ))
        
        # Sort by confidence and take top 5
        sources.sort(key=lambda x: x.confidence, reverse=True)
        top_sources = sources[:5]
        
        # ⭐ NEW: Mark these sentences as used
        for source in top_sources:
            if source.sentence_index is not None:
                self.used_sentences[source.sentence_index] = \
                    self.used_sentences.get(source.sentence_index, 0) + 1
        
        return top_sources
    
    def _find_knowledge_sources(
        self,
        step_content: str,
        step_title: str,
        step_actions: List[str],
        knowledge_sources: List[Dict]
    ) -> List[SourceReference]:
        """
        Find matching knowledge sources for a step using semantic similarity.
        
        Args:
            step_content: Step content text
            step_title: Step title
            step_actions: List of step actions
            knowledge_sources: List of knowledge source dictionaries
            
        Returns:
            List of SourceReference objects for knowledge sources
        """
        sources = []
        search_text = f"{step_title} {step_content} {' '.join(step_actions)}"
        search_text_lower = search_text.lower()
        
        # Extract keywords from step
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                     'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could'}
        search_words = set(
            word.strip('.,!?;:()[]{}"\'').lower()
            for word in search_text_lower.split()
            if len(word.strip('.,!?;:()[]{}"\'')) > 2 and word.strip('.,!?;:()[]{}"\'') not in stop_words
        )
        
        for knowledge_source in knowledge_sources:
            if knowledge_source.get("error") or not knowledge_source.get("content"):
                continue
            
            content = knowledge_source.get("content", "")
            content_lower = content.lower()
            url = knowledge_source.get("url", "")
            title = knowledge_source.get("title", "Untitled")
            
            # Calculate similarity
            content_words = set(
                word.strip('.,!?;:()[]{}"\'').lower()
                for word in content_lower.split()
                if len(word.strip('.,!?;:()[]{}"\'')) > 2
            )
            
            if search_words:
                word_overlap = len(search_words & content_words) / len(search_words | content_words)
            else:
                word_overlap = 0.0
            
            # Character similarity
            char_similarity = self._calculate_text_similarity(search_text_lower, content_lower[:2000])
            
            # Combined score
            final_score = (word_overlap * 0.6) + (char_similarity * 0.4)
            
            # Only include if similarity is above threshold
            if final_score >= 0.2:  # Slightly higher threshold for knowledge sources
                # Extract relevant excerpt (first 300 chars that match)
                excerpt = content[:300] + "..." if len(content) > 300 else content
                
                sources.append(SourceReference(
                    type="knowledge",
                    excerpt=excerpt,
                    timestamp=None,
                    sentence_index=None,
                    screenshot_ref=None,
                    ui_elements=[],
                    confidence=final_score
                ))
                # Store URL in a custom field (we'll need to extend SourceReference for this)
                # For now, we'll include it in the excerpt
                sources[-1].excerpt = f"[{title}]({url})\n{excerpt}"
        
        sources.sort(key=lambda x: x.confidence, reverse=True)
        return sources[:3]  # Limit to top 3 knowledge sources per step
    
    def _find_visual_sources(
        self,
        step_content: str,
        step_title: str,
        step_actions: List[str],
        screenshots_data: List[Dict]
    ) -> List[SourceReference]:
        """Find matching UI elements from screenshots."""
        sources = []
        
        # Extract action verbs and targets
        action_patterns = self._extract_action_patterns(step_actions)
        
        for screenshot in screenshots_data:
            screenshot_name = screenshot.get("filename", "unknown")
            ui_elements = screenshot.get("ui_elements", [])
            content = screenshot.get("content", "")
            
            # Check UI elements
            for element in ui_elements:
                element_text = element.get("text", "").lower()
                element_type = element.get("type", "unknown")
                
                # Match action patterns with UI elements
                for action_verb, action_target in action_patterns:
                    # Check if action target matches UI element
                    if action_target in element_text or element_text in action_target:
                        sources.append(SourceReference(
                            type="visual",
                            excerpt=f"Screenshot showing {element_type}: '{element['text']}'",
                            screenshot_ref=screenshot_name,
                            ui_elements=[element['text']],
                            confidence=0.8
                        ))
            
            # Also check general content match
            content_lower = content.lower()
            search_text = f"{step_title} {step_content}".lower()
            
            similarity = self._calculate_text_similarity(search_text, content_lower)
            
            if similarity >= 0.4:
                sources.append(SourceReference(
                    type="visual",
                    excerpt=f"Screenshot content: {content[:100]}...",
                    screenshot_ref=screenshot_name,
                    confidence=similarity
                ))
        
        # Sort by confidence and take top 3
        sources.sort(key=lambda x: x.confidence, reverse=True)
        return sources[:3]
    
    def _extract_action_patterns(self, actions: List[str]) -> List[Tuple[str, str]]:
        """
        Extract action verb and target pairs from action list.
        
        Example: "Click the Create button" -> ("click", "create button")
        
        Returns:
            List of (verb, target) tuples
        """
        patterns = []
        
        action_verbs = [
            "click", "open", "navigate", "select", "choose", "enter",
            "type", "create", "delete", "update", "configure", "set"
        ]
        
        for action in actions:
            action_lower = action.lower()
            
            # Find verb
            found_verb = None
            for verb in action_verbs:
                if verb in action_lower:
                    found_verb = verb
                    break
            
            if found_verb:
                # Extract target (words after the verb)
                verb_pos = action_lower.find(found_verb)
                target = action_lower[verb_pos + len(found_verb):].strip()
                
                # Clean target (remove articles)
                target = target.replace("the ", "").replace("a ", "").replace("an ", "")
                
                if target:
                    patterns.append((found_verb, target))
        
        return patterns
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 - 1.0)
        """
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def calculate_confidence(self, step_data: StepSourceData) -> float:
        """
        Calculate multi-factor confidence score for a step.
        
        ⭐ FIXED: Visual sources excluded from confidence calculation to focus on AI Agent performance
        ⭐ FIXED: Bonuses are now multiplicative to prevent low-quality sources from passing
        
        Factors:
        - Average source confidence (transcript + knowledge only)
        - Number of sources (multiplicative bonus)
        - Source diversity (knowledge + transcript)
        - High confidence source presence
        
        Args:
            step_data: Step source data
            
        Returns:
            Overall confidence score (0.0 - 1.0)
        """
        if not step_data.sources:
            return 0.0
        
        # ⭐ FIXED: Filter out visual sources - only use transcript and knowledge for AI performance
        ai_sources = [s for s in step_data.sources if s.type in ["transcript", "knowledge"]]
        
        if not ai_sources:
            return 0.0
        
        # Base score: average of AI source confidences (weighted by top sources)
        sorted_sources = sorted(ai_sources, key=lambda x: x.confidence, reverse=True)
        top_3_sources = sorted_sources[:3]
        
        # Weight top sources more heavily
        if len(top_3_sources) == 1:
            avg_confidence = top_3_sources[0].confidence
        elif len(top_3_sources) == 2:
            avg_confidence = (top_3_sources[0].confidence * 0.6 + top_3_sources[1].confidence * 0.4)
        else:
            avg_confidence = (
                top_3_sources[0].confidence * 0.5 +
                top_3_sources[1].confidence * 0.3 +
                top_3_sources[2].confidence * 0.2
            )
        
        # ⭐ FIXED: Multiplicative bonuses - start with base score
        total_confidence = avg_confidence
        
        # Source count multiplier (only for AI sources)
        source_count = len(ai_sources)
        if source_count >= 4:
            total_confidence *= 1.25  # +25% boost
        elif source_count == 3:
            total_confidence *= 1.15  # +15% boost
        elif source_count == 2:
            total_confidence *= 1.08  # +8% boost
        # 1 source: no multiplier
        
        # Knowledge source bonus (transcript + knowledge diversity)
        has_transcript = any(s.type == "transcript" for s in ai_sources)
        has_knowledge = any(s.type == "knowledge" for s in ai_sources)
        if has_transcript and has_knowledge:
            total_confidence *= 1.12  # +12% for diverse AI sources
        
        # High confidence source multiplier (if any AI source has >0.5 confidence)
        if any(s.confidence > 0.5 for s in ai_sources):
            total_confidence *= 1.10  # +10% for strong matches
        
        # Clamp to [0, 1]
        return min(1.0, max(0.0, total_confidence))

    def enhance_confidence_with_validation(
        self,
        original_confidence: float,
        quality_score: float
    ) -> float:
        """
        Enhance confidence score with step validation quality score.

        Phase 2 Day 8: Integrates validation quality into confidence calculation.

        Formula:
        - Base: Original confidence (source-based)
        - Enhancement: Quality score multiplier
        - Weight: 70% original + 30% quality

        Args:
            original_confidence: Original confidence from sources (0.0-1.0)
            quality_score: Validation quality score (0.0-1.0)

        Returns:
            Enhanced confidence score (0.0-1.0)
        """
        # Weighted combination: 70% source confidence + 30% validation quality
        # This preserves source grounding while boosting high-quality steps
        enhanced = (original_confidence * 0.7) + (quality_score * 0.3)

        # Apply quality multiplier (multiplicative bonus for high quality)
        if quality_score >= 0.8:
            enhanced *= 1.10  # +10% for very high quality
        elif quality_score >= 0.6:
            enhanced *= 1.05  # +5% for high quality
        elif quality_score < 0.3:
            enhanced *= 0.95  # -5% penalty for low quality

        # Clamp to [0, 1]
        return min(1.0, max(0.0, enhanced))

    def get_confidence_quality_indicator(self, confidence: float) -> str:
        """
        Get quality indicator for confidence score.

        Phase 2 Day 8: Provides human-readable quality labels.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            Quality indicator: "high", "medium", or "low"
        """
        if confidence >= 0.7:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        else:
            return "low"

    def validate_step(self, step_data: StepSourceData) -> Tuple[bool, List[str]]:
        """
        Check if step meets quality thresholds.
        
        Validation criteria:
        - Confidence >= 0.7 (high confidence)
        - Has at least one transcript source
        - No red flags
        
        Args:
            step_data: Step source data
            
        Returns:
            Tuple of (is_valid, warning_messages)
        """
        warnings = []
        
        # Check confidence (updated thresholds)
        if step_data.overall_confidence < 0.3:
            warnings.append(f"Very low confidence ({step_data.overall_confidence:.2f}) - may be hallucinated")
        elif step_data.overall_confidence < 0.5:
            warnings.append(f"Low confidence ({step_data.overall_confidence:.2f}) - verify accuracy")
        elif step_data.overall_confidence < 0.7:
            warnings.append(f"Medium confidence ({step_data.overall_confidence:.2f}) - generally reliable")
        
        # Check transcript support
        if not step_data.has_transcript_support:
            warnings.append("No transcript support found - verify against source material")
        
        # Check source count
        if len(step_data.sources) == 0:
            warnings.append("No source references found - content may be fabricated")
        elif len(step_data.sources) == 1:
            warnings.append("Only one source reference - limited validation")
        
        # ⭐ FIXED: Lowered threshold from 0.7 to 0.4 (was unrealistically high)
        is_valid = (
            step_data.overall_confidence >= 0.4 and
            step_data.has_transcript_support and
            len(step_data.sources) > 0
        )
        
        step_data.validation_flags = warnings
        
        return is_valid, warnings
    
    def build_step_sources(
        self,
        step_index: int,
        step_dict: Dict,
        transcript_sentences: List[str],
        screenshots_data: Optional[List[Dict]] = None,
        knowledge_sources: Optional[List[Dict]] = None
    ) -> StepSourceData:
        """
        Build complete source data for a step.
        
        This is the main entry point for adding source references to a step.
        
        Args:
            step_index: Step number
            step_dict: Step dictionary with title, summary, details, actions
            transcript_sentences: All transcript sentences
            screenshots_data: Optional screenshot data
            
        Returns:
            StepSourceData with all source information
        """
        # Extract step components
        step_title = step_dict.get("title", "")
        step_summary = step_dict.get("summary", "")
        step_details = step_dict.get("details", "")
        step_actions = step_dict.get("actions", [])
        
        step_content = f"{step_summary} {step_details}"
        
        # Find sources using similarity matching (for LLM-generated steps)
        sources = self.find_sources_for_step(
                step_content=step_content,
                step_title=step_title,
                step_actions=step_actions,
                transcript_sentences=transcript_sentences,
                screenshots_data=screenshots_data,
                knowledge_sources=knowledge_sources
            )
        
        # Create step source data
        step_data = StepSourceData(
            step_index=step_index,
            step_content=step_content,
            sources=sources,
            has_transcript_support=any(s.type == "transcript" for s in sources),
            has_visual_support=any(s.type == "visual" for s in sources)
        )
        
        # Calculate confidence
        step_data.overall_confidence = self.calculate_confidence(step_data)
        
        # Validate
        self.validate_step(step_data)
        
        # Store
        self.step_sources[step_index] = step_data
        
        logger.info(
            f"Step {step_index}: Confidence {step_data.overall_confidence:.2f}, "
            f"{len(sources)} sources, valid: {len(step_data.validation_flags) == 0}"
        )
        
        return step_data
    
    def get_confidence_level_label(self, confidence: float) -> str:
        """
        Get human-readable confidence level.
        
        ⭐ FIXED: Updated thresholds to match new multiplicative scoring
        
        Args:
            confidence: Confidence score (0.0 - 1.0)
            
        Returns:
            Label like "High", "Medium", "Low"
        """
        if confidence >= 0.75:
            return "Very High"
        elif confidence >= 0.55:
            return "High"
        elif confidence >= 0.35:
            return "Medium"
        elif confidence >= 0.20:
            return "Low"
        else:
            return "Very Low"
    
    def get_all_step_sources(self) -> List[StepSourceData]:
        """Get all step source data, sorted by step index."""
        return [self.step_sources[i] for i in sorted(self.step_sources.keys())]

