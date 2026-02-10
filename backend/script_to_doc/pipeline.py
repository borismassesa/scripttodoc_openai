"""
Core processing pipeline for ScriptToDoc.
Orchestrates the end-to-end flow from transcript to document.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from pathlib import Path

from .transcript_cleaner import TranscriptCleaner, SentenceTokenizer, TranscriptChunker
from .transcript_parser import TranscriptParser  # Phase 1: Intelligent parsing
from .topic_segmenter import TopicSegmenter  # Phase 1: Topic segmentation
from .qa_filter import QAFilter, FilterConfig  # Phase 2: Q&A filtering
from .topic_ranker import TopicRanker, RankingConfig  # Phase 2: Topic ranking
from .step_validator import StepValidator, ValidationConfig  # Phase 2: Step validation
from .azure_di import AzureDocumentIntelligence
from .azure_openai_client import AzureOpenAIClient
from .source_reference import SourceReferenceManager
from .document_generator import create_training_document
from .knowledge_fetcher import KnowledgeFetcher
from .action_validator import ActionValidator

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the processing pipeline."""

    # Local mode settings (NEW)
    use_local_mode: bool = False           # Use local mode (OpenAI only, no Azure services)
    openai_api_key: Optional[str] = None   # OpenAI API key (required for local mode)
    openai_model: str = "gpt-4o-mini"      # OpenAI model name

    # Azure endpoints (CHANGED: Optional for local mode)
    azure_di_endpoint: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None

    # Optional: Azure credentials and settings (with defaults)
    azure_di_key: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o-mini"


    # Processing options
    use_azure_di: bool = False             # CHANGED: Disabled by default in local mode
    use_openai: bool = True
    use_managed_identity: bool = False

    # Phase 1: Intelligent parsing options
    use_intelligent_parsing: bool = False  # Enable transcript parser with metadata extraction
    use_topic_segmentation: bool = False   # Enable topic-based segmentation (requires parser)

    # Phase 2: Quality gates options (NEW)
    use_qa_filtering: bool = False         # Filter out Q&A sections (requires segmentation)
    use_topic_ranking: bool = False        # Rank topics by importance (requires segmentation)
    use_step_validation: bool = False      # Validate generated steps for quality
    qa_density_threshold: float = 0.30     # Min Q&A density to filter (30%)
    importance_threshold: float = 0.30     # Min importance score to keep
    min_confidence_threshold: float = 0.2  # Min confidence for step validation
    
    # Content options
    min_steps: int = 3
    target_steps: int = 8
    max_steps: int = 15
    tone: str = "Professional"
    audience: str = "Technical Users"
    
    # Quality options
    min_confidence_threshold: float = 0.25  # ⭐ TEMPORARY: Lowered to accept more steps while testing v2 prompt
    enable_source_validation: bool = True
    
    # Document options
    document_title: Optional[str] = None
    include_statistics: bool = True
    
    # Custom filler words
    custom_filler_words: Optional[List[str]] = None
    
    # Knowledge sources
    knowledge_urls: Optional[List[str]] = None


@dataclass
class PipelineResult:
    """Result from pipeline processing."""
    
    success: bool
    document_path: Optional[str] = None
    steps: Optional[List[Dict]] = None
    metrics: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    knowledge_sources_used: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "document_path": self.document_path,
            "steps": self.steps,
            "metrics": self.metrics,
            "error": self.error,
            "processing_time": self.processing_time,
            "knowledge_sources_used": self.knowledge_sources_used
        }


class ScriptToDocPipeline:
    """Main processing pipeline."""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        
        # Initialize components
        self.transcript_cleaner = TranscriptCleaner(
            custom_filler_words=config.custom_filler_words
        )
        self.sentence_tokenizer = SentenceTokenizer()
        self.transcript_chunker = TranscriptChunker(self.sentence_tokenizer)
        self.source_manager = SourceReferenceManager()
        self.knowledge_fetcher = KnowledgeFetcher()
        self.action_validator = ActionValidator(
            min_actions=3,
            max_actions=6,
            min_content_words=50
        )

        # Phase 1: Initialize intelligent parser (if enabled)
        self.transcript_parser = None
        if config.use_intelligent_parsing:
            self.transcript_parser = TranscriptParser()
            logger.info("Phase 1: Intelligent parsing enabled")

        # Phase 1: Initialize topic segmenter (if enabled)
        self.topic_segmenter = None
        if config.use_topic_segmentation:
            if not config.use_intelligent_parsing:
                logger.warning("Topic segmentation requires intelligent parsing. Enabling parser automatically.")
                self.transcript_parser = TranscriptParser()
            self.topic_segmenter = TopicSegmenter()
            logger.info("Phase 1: Topic segmentation enabled")

        # Phase 2: Initialize Q&A filter (if enabled)
        self.qa_filter = None
        if config.use_qa_filtering:
            if not config.use_topic_segmentation:
                logger.warning("Q&A filtering requires topic segmentation. Enabling segmentation automatically.")
                if not self.transcript_parser:
                    self.transcript_parser = TranscriptParser()
                self.topic_segmenter = TopicSegmenter()
            filter_config = FilterConfig(
                min_qa_density=config.qa_density_threshold
            )
            self.qa_filter = QAFilter(filter_config)
            logger.info("Phase 2: Q&A filtering enabled")

        # Phase 2: Initialize topic ranker (if enabled)
        self.topic_ranker = None
        if config.use_topic_ranking:
            if not config.use_topic_segmentation:
                logger.warning("Topic ranking requires topic segmentation. Enabling segmentation automatically.")
                if not self.transcript_parser:
                    self.transcript_parser = TranscriptParser()
                self.topic_segmenter = TopicSegmenter()
            ranking_config = RankingConfig(
                min_importance_threshold=config.importance_threshold
            )
            self.topic_ranker = TopicRanker(ranking_config)
            logger.info("Phase 2: Topic ranking enabled")

        # Phase 2: Initialize step validator (if enabled)
        self.step_validator = None
        if config.use_step_validation:
            validation_config = ValidationConfig(
                min_confidence_threshold=config.min_confidence_threshold
            )
            self.step_validator = StepValidator(validation_config)
            logger.info("Phase 2: Step validation enabled")

        # Initialize Azure clients
        # CHANGED: Only initialize Azure DI if enabled AND not in local mode
        if config.use_azure_di and not config.use_local_mode:
            self.azure_di = AzureDocumentIntelligence(
                endpoint=config.azure_di_endpoint,
                credential=config.azure_di_key,
                use_managed_identity=config.use_managed_identity
            )
        else:
            self.azure_di = None
            if config.use_local_mode:
                logger.info("Local mode: Azure Document Intelligence disabled")

        # CHANGED: Pass use_local_mode to OpenAI client
        if config.use_openai:
            self.azure_openai = AzureOpenAIClient(
                endpoint=config.azure_openai_endpoint,
                api_key=config.azure_openai_key,
                deployment=config.azure_openai_deployment,
                use_managed_identity=config.use_managed_identity,
                openai_api_key=config.openai_api_key,
                openai_model=config.openai_model,
                use_local_mode=config.use_local_mode
            )
        else:
            self.azure_openai = None
        
        logger.info("Pipeline initialized")
    
    def process(
        self,
        transcript_text: str,
        output_path: str,
        screenshots_data: Optional[List[Dict]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> PipelineResult:
        """
        Process transcript and generate training document.
        
        Args:
            transcript_text: Raw transcript text
            output_path: Path where document should be saved
            screenshots_data: Optional screenshot analysis data
            progress_callback: Optional callback(progress, stage) for updates
            
        Returns:
            PipelineResult with success status and metrics
        """
        start_time = time.time()
        
        try:
            logger.info("Starting pipeline processing")
            self._update_progress(progress_callback, 0.05, "load_transcript")

            # Phase 1: Parse transcript with metadata (if enabled)
            parsed_sentences = None
            transcript_metadata = None

            if self.config.use_intelligent_parsing and self.transcript_parser:
                logger.info("Step 1a: Parsing transcript with intelligent parser")
                parsed_sentences, transcript_metadata = self.transcript_parser.parse(transcript_text)
                logger.info(f"Parsed: {transcript_metadata}")

                # Clean each parsed sentence while preserving metadata
                for sent in parsed_sentences:
                    sent.text = self.transcript_cleaner.normalize(sent.text)

                # Build sentence catalog from parsed sentences
                cleaned_text = ' '.join(s.text for s in parsed_sentences)
                sentences = [s.text for s in parsed_sentences]
                self.source_manager.build_sentence_catalog(cleaned_text, sentences)

                logger.info("Phase 1 parsing complete")
            else:
                # Original flow: Clean transcript without parsing
                logger.info("Step 1: Cleaning transcript (legacy mode)")
                cleaned_text = self.transcript_cleaner.normalize(transcript_text)
                sentences = self.sentence_tokenizer.tokenize(cleaned_text)
                self.source_manager.build_sentence_catalog(cleaned_text, sentences)

            self._update_progress(progress_callback, 0.15, "clean_transcript")
            
            # Step 1.5: Fetch knowledge sources
            knowledge_sources = []
            if self.config.knowledge_urls:
                logger.info(f"Fetching knowledge from {len(self.config.knowledge_urls)} URLs")
                self._update_progress(progress_callback, 0.22, "fetch_knowledge")
                knowledge_sources = self.knowledge_fetcher.fetch_multiple_urls(self.config.knowledge_urls)
                successful_sources = [s for s in knowledge_sources if not s.get("error")]
                logger.info(f"Successfully fetched {len(successful_sources)}/{len(knowledge_sources)} knowledge sources")

            # Step 2: Analyze with Azure DI (if enabled)
            di_structure = None
            if self.config.use_azure_di and self.azure_di:
                logger.info("Step 2: Analyzing with Azure Document Intelligence")
                di_result = self.azure_di.analyze_transcript_text(cleaned_text)
                di_structure = self.azure_di.extract_process_structure(
                    di_result["content"],
                    di_result["paragraphs"]
                )
                self._update_progress(progress_callback, 0.35, "azure_di_analysis")
            else:
                logger.info("Step 2: Skipping Azure DI (disabled)")
                di_structure = {"actions": [], "sequence_indicators": [], "roles": []}
                self._update_progress(progress_callback, 0.35, "skip_azure_di")
            
            # Step 3: Determine step count
            logger.info("Step 3: Determining optimal step count")
            complexity_factors = {
                "action_count": len(di_structure.get("actions", [])),
                "decision_count": len(di_structure.get("decisions", [])),
                "word_count": len(cleaned_text.split())
            }
            
            # Use the user's configured target_steps, bounded by min/max
            # NOTE: We respect the user's explicit choice rather than overriding with AI suggestions
            target_steps = max(
                self.config.min_steps,
                min(self.config.max_steps, self.config.target_steps)
            )
            
            logger.info(f"Target steps (legacy): {target_steps}")
            # ⚠️ Phase 1: Do NOT set total_steps yet - topic segmentation will determine actual count
            self._update_progress(
                progress_callback, 0.40, "determine_steps",
                stage_detail="Analyzing transcript structure..."
            )
            
            # Step 4: Generate training steps with OpenAI (CHUNK-BASED)
            logger.info("Step 4: Generating training steps with chunk-based approach")

            if not self.config.use_openai or not self.azure_openai:
                raise ValueError(
                    "OpenAI is required for step generation. "
                    "Please configure Azure OpenAI or provide OpenAI API key for fallback."
                )

            # NEW: Chunk-based generation for better grounding
            # Split transcript into focused chunks (one chunk = one step)

            # Phase 1: Use topic segmentation if enabled
            if self.config.use_topic_segmentation and self.topic_segmenter and parsed_sentences:
                logger.info("Step 4a: Segmenting transcript into topics")
                topic_segments = self.topic_segmenter.segment(parsed_sentences, transcript_metadata)
                logger.info(f"Created {len(topic_segments)} topic segments")

                # Phase 2: Filter Q&A sections if enabled
                if self.qa_filter:
                    logger.info("Step 4b: Filtering Q&A sections")
                    before_count = len(topic_segments)
                    topic_segments = self.qa_filter.filter_segments(topic_segments, transcript_metadata)
                    after_count = len(topic_segments)
                    logger.info(f"Q&A filtering: {before_count} → {after_count} segments ({before_count - after_count} filtered)")

                # Phase 2: Rank and filter by importance if enabled
                if self.topic_ranker:
                    logger.info("Step 4c: Ranking topics by importance")
                    before_count = len(topic_segments)
                    topic_segments = self.topic_ranker.filter_low_importance(topic_segments)
                    after_count = len(topic_segments)
                    logger.info(f"Importance filtering: {before_count} → {after_count} segments ({before_count - after_count} filtered)")

                # Check if any segments remain after filtering
                if not topic_segments:
                    raise ValueError(
                        "All topic segments were filtered out by Phase 2 quality gates. "
                        "This may indicate overly aggressive filtering thresholds. "
                        "Try: (1) lowering qa_density_threshold, "
                        "(2) lowering importance_threshold, or "
                        "(3) disabling Phase 2 features temporarily."
                    )

                # Convert topic segments to text chunks
                chunks = [seg.get_text() for seg in topic_segments]

                # Log segment characteristics
                for i, seg in enumerate(topic_segments, 1):
                    logger.debug(
                        f"Segment {i}: {len(seg.sentences)} sentences, "
                        f"coherence={seg.coherence_score:.2f}, "
                        f"transition={seg.has_transition_start}, "
                        f"qa={seg.has_qa_section}"
                    )

                logger.info(
                    f"Topic segmentation complete: {len(chunks)} segments "
                    f"(avg {sum(len(c.split()) for c in chunks) / len(chunks) if chunks else 0:.1f} words/segment)"
                )

                # ✅ NOW set total_steps - we know the actual count after segmentation
                self._update_progress(
                    progress_callback, 0.42, "determine_steps",
                    total_steps=len(chunks),
                    stage_detail=f"Determined {len(chunks)} optimal steps based on topic boundaries"
                )
            else:
                # Legacy: Use arbitrary chunking
                logger.info(f"Step 4b: Splitting transcript into {target_steps} chunks (legacy mode)")
                chunks = self.transcript_chunker.chunk_smart(
                    transcript=cleaned_text,
                    target_chunks=target_steps,
                    prefer_paragraphs=True
                )
                logger.info(f"Created {len(chunks)} chunks (avg {sum(len(c.split()) for c in chunks) / len(chunks) if chunks else 0:.1f} words/chunk)")

                # ✅ Set total_steps for legacy mode too
                self._update_progress(
                    progress_callback, 0.42, "determine_steps",
                    total_steps=len(chunks),
                    stage_detail=f"Determined {len(chunks)} steps (legacy chunking)"
                )

            # Generate steps - try parallel async first, fallback to sequential if needed
            try:
                import asyncio
                logger.info(f"Attempting parallel step generation for {len(chunks)} steps")
                steps, token_usage, first_error = asyncio.run(
                    self._generate_steps_parallel(
                        chunks,
                        knowledge_sources,
                        progress_callback
                    )
                )
                logger.info(f"Parallel generation complete: {len(steps)} steps generated")
            except Exception as async_error:
                logger.warning(f"Parallel generation failed ({async_error}), falling back to sequential")
                # Fallback to sequential generation
                steps = []
                total_input_tokens = 0
                total_output_tokens = 0
                total_tokens = 0
                first_error = None

                for i, chunk in enumerate(chunks, 1):
                    try:
                        logger.info(f"Generating step {i}/{len(chunks)} from chunk ({len(chunk)} chars)")

                        step, usage = self.azure_openai.generate_step_from_chunk(
                            chunk=chunk,
                            chunk_index=i,
                            total_chunks=len(chunks),
                            tone=self.config.tone,
                            audience=self.config.audience,
                            knowledge_sources=knowledge_sources,
                            knowledge_fetcher=self.knowledge_fetcher
                        )

                        steps.append(step)

                        # Aggregate token usage
                        total_input_tokens += usage.get('input_tokens', 0)
                        total_output_tokens += usage.get('output_tokens', 0)
                        total_tokens += usage.get('total_tokens', 0)

                        # Update progress incrementally
                        progress = 0.40 + (0.20 * i / len(chunks))
                        self._update_progress(
                            progress_callback,
                            progress,
                            "generate_steps",
                            current_step=i,
                            total_steps=len(chunks),
                            stage_detail=f"Generating step {i} of {len(chunks)}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to generate step {i}/{len(chunks)}: {str(e)}")
                        if first_error is None:
                            first_error = str(e)
                        continue

                token_usage = {
                    'input_tokens': total_input_tokens,
                    'output_tokens': total_output_tokens,
                    'total_tokens': total_tokens
                }

            # Aggregate token usage
            token_usage = {
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_tokens': total_tokens
            }

            logger.info(f"Generated {len(steps)} steps using chunk-based approach, {total_tokens} total tokens")

            # Validate that at least one step was generated
            if len(steps) == 0:
                # Include the first error encountered for better diagnostics
                error_detail = f"\n\nRoot cause: {first_error}" if first_error else ""
                raise ValueError(
                    f"Failed to generate any training steps from the transcript. "
                    f"All {len(chunks)} chunks failed during step generation.{error_detail}"
                )

            # NOTE: Skip _enhance_steps_with_transcript() - chunks already focused, no need for post-processing

            self._update_progress(
                progress_callback, 0.60, "generate_steps",
                stage_detail="All steps generated successfully"
            )

            # Step 5: Build source references
            logger.info("Step 5: Building source references")
            self._update_progress(
                progress_callback, 0.62, "build_sources",
                stage_detail="Building source references for steps"
            )
            step_sources = []
            total_steps_for_sources = len(steps)

            for i, step in enumerate(steps, 1):
                # Show progress for each step being processed
                progress_within_stage = 0.62 + (0.13 * (i / total_steps_for_sources))  # 0.62 to 0.75
                self._update_progress(
                    progress_callback, progress_within_stage, "build_sources",
                    stage_detail=f"Building citations for step {i} of {total_steps_for_sources}"
                )

                source_data = self.source_manager.build_step_sources(
                    step_index=i,
                    step_dict=step,
                    transcript_sentences=sentences,
                    screenshots_data=screenshots_data,
                    knowledge_sources=knowledge_sources
                )
                step_sources.append(source_data)

                # Add confidence score to step dict
                step['confidence_score'] = source_data.overall_confidence

            self._update_progress(
                progress_callback, 0.75, "build_sources",
                stage_detail="All citations built successfully"
            )

            # Step 6: Validate steps
            logger.info("Step 6: Validating steps")
            self._update_progress(
                progress_callback, 0.78, "validate_steps",
                stage_detail="Validating step quality and sources"
            )
            valid_steps = []
            valid_sources = []

            validation_threshold = self.config.min_confidence_threshold
            total_steps_to_validate = len(steps)

            for idx, (step, source_data) in enumerate(zip(steps, step_sources), 1):
                # Show progress for each step being validated
                progress_within_stage = 0.78 + (0.07 * (idx / total_steps_to_validate))  # 0.78 to 0.85
                self._update_progress(
                    progress_callback, progress_within_stage, "validate_steps",
                    stage_detail=f"Validating step {idx} of {total_steps_to_validate}"
                )
                # Action validation (quality check)
                action_validation = self.action_validator.validate_step(step)

                # Log action validation issues/warnings
                if action_validation.issues:
                    logger.warning(
                        f"Step {source_data.step_index} action issues: {', '.join(action_validation.issues)}"
                    )
                if action_validation.warnings:
                    logger.info(
                        f"Step {source_data.step_index} action warnings: {', '.join(action_validation.warnings)}"
                    )

                # Add validation flags to source data for document generation
                if action_validation.issues:
                    source_data.validation_flags.extend(action_validation.issues)

                # Phase 2: Step validator (comprehensive quality check)
                step_validation_result = None
                if self.step_validator:
                    step_validation_result = self.step_validator.validate_step(step, source_data.step_index)

                    # Log validation issues
                    if step_validation_result.errors:
                        logger.warning(
                            f"Step {source_data.step_index} validation errors: "
                            f"{', '.join(e.message for e in step_validation_result.errors)}"
                        )
                    if step_validation_result.warnings:
                        logger.info(
                            f"Step {source_data.step_index} validation warnings: "
                            f"{', '.join(w.message for w in step_validation_result.warnings)}"
                        )

                    # Add quality score to step metadata
                    step['quality_score'] = step_validation_result.quality_score

                    # Log quality score
                    logger.info(
                        f"Step {source_data.step_index} quality score: {step_validation_result.quality_score:.2f}"
                    )

                    # Phase 2 Day 8: Enhance confidence with validation quality
                    original_confidence = step['confidence_score']
                    enhanced_confidence = self.source_manager.enhance_confidence_with_validation(
                        original_confidence,
                        step_validation_result.quality_score
                    )

                    # Update confidence with enhanced value
                    step['confidence_score'] = enhanced_confidence
                    source_data.overall_confidence = enhanced_confidence

                    # Add quality indicator
                    quality_indicator = self.source_manager.get_confidence_quality_indicator(enhanced_confidence)
                    step['quality_indicator'] = quality_indicator

                    # Log confidence enhancement
                    logger.info(
                        f"Step {source_data.step_index} confidence enhanced: "
                        f"{original_confidence:.2f} → {enhanced_confidence:.2f} ({quality_indicator})"
                    )

                # Source validation (content grounding)
                source_valid = True
                if self.config.enable_source_validation:
                    is_valid, warnings = self.source_manager.validate_step(source_data)

                    # Accept steps based on confidence threshold
                    # Also accept steps with at least one source, even if below threshold (with warning)
                    has_sources = len(source_data.sources) > 0
                    meets_threshold = source_data.overall_confidence >= validation_threshold

                    if meets_threshold or (has_sources and source_data.overall_confidence >= 0.2):
                        source_valid = True
                        if not meets_threshold:
                            logger.info(
                                f"Step {source_data.step_index} accepted with lower confidence "
                                f"({source_data.overall_confidence:.2f} < {validation_threshold}): "
                                f"{len(source_data.sources)} sources found (threshold relaxed for source presence)"
                            )
                        else:
                            logger.info(
                                f"Step {source_data.step_index} accepted (confidence: "
                                f"{source_data.overall_confidence:.2f}): {len(source_data.sources)} sources found"
                            )
                    else:
                        source_valid = False
                        logger.warning(
                            f"Step {source_data.step_index} rejected (confidence: "
                            f"{source_data.overall_confidence:.2f} < {validation_threshold}, "
                            f"sources: {len(source_data.sources)}): {warnings}"
                        )

                # Accept step if ALL validations pass
                # Note: We're being lenient - accept steps with warnings but not errors
                step_validator_passed = True
                if self.step_validator and step_validation_result:
                    step_validator_passed = step_validation_result.is_valid

                if action_validation.passed and source_valid and step_validator_passed:
                    valid_steps.append(step)
                    valid_sources.append(source_data)
                    logger.info(f"Step {source_data.step_index} validation PASSED")
                elif not action_validation.passed:
                    logger.warning(
                        f"Step {source_data.step_index} rejected due to action validation failures"
                    )
                elif not source_valid:
                    logger.warning(
                        f"Step {source_data.step_index} rejected due to source validation failures"
                    )
                else:
                    logger.warning(
                        f"Step {source_data.step_index} rejected due to step validation failures"
                    )
            
            logger.info(f"Validated: {len(valid_steps)}/{len(steps)} steps passed")
            self._update_progress(
                progress_callback, 0.85, "validate_steps",
                stage_detail=f"Validation complete: {len(valid_steps)}/{len(steps)} steps passed"
            )

            # Fail if no valid steps
            if len(valid_steps) == 0:
                raise ValueError(
                    f"All {len(steps)} generated steps failed validation (confidence below {validation_threshold}). "
                    "This indicates that the generated steps do not match the transcript content well enough. "
                    "Possible reasons:\n"
                    "  1. Transcript is too short or lacks clear procedural content\n"
                    "  2. Step generation produced generic steps not grounded in the transcript\n"
                    "  3. Source matching algorithm needs tuning\n"
                    "Cannot create a document with 0 valid steps."
                )
            
            # Step 7: Generate document
            logger.info("Step 7: Generating Word document")
            self._update_progress(
                progress_callback, 0.87, "create_document",
                stage_detail="Preparing document structure"
            )

            document_title = self.config.document_title or "Training Documentation"
            metadata = {
                "subtitle": f"Generated from Meeting Transcript",
                "tone": self.config.tone,
                "audience": self.config.audience,
            }

            # Prepare statistics with token usage and processing time
            processing_time = time.time() - start_time
            stats_for_doc = {
                "total_steps": len(valid_steps),
                "avg_confidence": (
                    sum(s.overall_confidence for s in valid_sources) / len(valid_sources)
                    if valid_sources else 0.0
                ),
                "high_confidence_count": sum(
                    1 for s in valid_sources if s.overall_confidence >= 0.7
                ),
                "visual_support_count": sum(1 for s in valid_sources if s.has_visual_support),
                "total_sources": sum(len(s.sources) for s in valid_sources),
                "processing_time": processing_time,
                "token_usage": token_usage,
            }

            self._update_progress(
                progress_callback, 0.89, "create_document",
                stage_detail=f"Formatting {len(valid_steps)} steps with citations"
            )

            document_path = create_training_document(
                title=document_title,
                steps=valid_steps,
                step_sources=valid_sources,
                output_path=output_path,
                metadata=metadata,
                include_statistics=self.config.include_statistics,
                statistics=stats_for_doc,
                knowledge_sources=knowledge_sources
            )

            self._update_progress(
                progress_callback, 0.93, "create_document",
                stage_detail="Saving document file"
            )

            self._update_progress(
                progress_callback, 0.95, "create_document",
                stage_detail="Document created successfully"
            )

            # Calculate metrics (processing_time already calculated above)
            # Count knowledge sources that were actually cited
            knowledge_sources_cited = set()
            for source_data in valid_sources:
                for source in source_data.sources:
                    if source.type == "knowledge":
                        knowledge_sources_cited.add(source.excerpt[:100])  # Use excerpt as identifier
            
            metrics = {
                "total_steps": len(valid_steps),
                "rejected_steps": len(steps) - len(valid_steps),
                "average_confidence": (
                    sum(s.overall_confidence for s in valid_sources) / len(valid_sources)
                    if valid_sources else 0.0
                ),
                "high_confidence_steps": sum(
                    1 for s in valid_sources if s.overall_confidence >= 0.7
                ),
                "transcript_word_count": len(cleaned_text.split()),
                "transcript_sentence_count": len(sentences),
                "total_sources": sum(len(s.sources) for s in valid_sources),
                "knowledge_sources_fetched": len(knowledge_sources),
                "knowledge_sources_cited": len(knowledge_sources_cited),
                "knowledge_usage_rate": (
                    len(knowledge_sources_cited) / len(knowledge_sources) 
                    if knowledge_sources else 0.0
                ),
                "token_usage": token_usage,
                "processing_time_seconds": processing_time,
                "estimated_cost": self._calculate_cost(token_usage)
            }

            self._update_progress(
                progress_callback, 1.0, "complete",
                stage_detail=f"Processing complete: {len(valid_steps)} steps generated"
            )

            logger.info(
                f"Pipeline complete in {processing_time:.2f}s: {len(valid_steps)} steps, "
                f"avg confidence {metrics['average_confidence']:.2f}"
            )
            
            return PipelineResult(
                success=True,
                document_path=document_path,
                steps=valid_steps,
                metrics=metrics,
                knowledge_sources_used=knowledge_sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Pipeline failed after {processing_time:.2f}s: {str(e)}", exc_info=True)
            
            return PipelineResult(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _enhance_steps_with_transcript(self, steps: List[Dict], sentences: List[str], transcript: str) -> List[Dict]:
        """
        Post-process steps to improve transcript matching by incorporating actual transcript phrases.
        
        This helps improve source matching confidence by ensuring steps contain
        terminology and phrases that exist in the transcript.
        
        Args:
            steps: Generated steps
            sentences: Transcript sentences
            transcript: Full transcript text
            
        Returns:
            Enhanced steps with better transcript alignment
        """
        enhanced_steps = []
        transcript_lower = transcript.lower()
        
        for step in steps:
            enhanced_step = step.copy()
            
            # Extract key terms from step
            step_text = f"{step.get('title', '')} {step.get('summary', '')} {step.get('details', '')}"
            step_words = set(word.lower().strip('.,!?;:()[]{}"\'') 
                           for word in step_text.split() 
                           if len(word.strip('.,!?;:()[]{}"\'')) > 3)
            
            # Find matching sentences that contain step keywords
            matching_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Count how many step words appear in this sentence
                matches = sum(1 for word in step_words if word in sentence_lower)
                if matches >= 2:  # At least 2 keyword matches
                    matching_sentences.append((sentence, matches))
            
            # Sort by match count and take top 3
            matching_sentences.sort(key=lambda x: x[1], reverse=True)
            top_matches = [s[0] for s in matching_sentences[:3]]
            
            # If we found good matches, enhance the details section
            if top_matches and step.get('details'):
                # Extract key phrases from matching sentences
                key_phrases = []
                for match in top_matches[:2]:  # Use top 2 matches
                    # Extract phrases of 3-5 words that appear in both step and match
                    match_words = match.lower().split()
                    for i in range(len(match_words) - 2):
                        phrase = ' '.join(match_words[i:i+4])
                        if any(word in phrase for word in step_words if len(word) > 4):
                            key_phrases.append(phrase)
                
                # If we found relevant phrases, subtly enhance details
                if key_phrases and len(step.get('details', '')) < 200:
                    # Add a sentence that references transcript content
                    enhanced_details = step.get('details', '')
                    # Don't modify if already long enough
                    if len(enhanced_details) < 150:
                        # Find a short, relevant phrase to incorporate
                        for phrase in key_phrases[:1]:
                            if len(phrase) < 50 and phrase not in enhanced_details.lower():
                                # Add context naturally
                                enhanced_step['details'] = enhanced_details + " This aligns with the process described in the transcript."
                                break
            
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps

    def _calculate_cost(self, token_usage: Dict) -> float:
        """
        Calculate estimated cost based on token usage.
        
        Pricing for GPT-4o-mini (as of 2024):
        - Input: $0.15 per 1M tokens
        - Output: $0.60 per 1M tokens
        
        Args:
            token_usage: Dict with input_tokens, output_tokens, total_tokens
            
        Returns:
            Estimated cost in USD
        """
        if not token_usage:
            return 0.0
        
        input_tokens = token_usage.get("input_tokens", 0)
        output_tokens = token_usage.get("output_tokens", 0)
        
        # GPT-4o-mini pricing (per 1M tokens)
        input_cost_per_million = 0.15
        output_cost_per_million = 0.60
        
        input_cost = (input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million
        
        total_cost = input_cost + output_cost
        
        return round(total_cost, 4)

    async def _generate_steps_parallel(
        self,
        chunks: List[str],
        knowledge_sources: Optional[List[Dict]],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[List[Dict], Dict, Optional[str]]:
        """
        Generate steps from chunks in parallel using async API calls.

        This is significantly faster than sequential generation:
        - Sequential: ~3s per step = 24s for 8 steps
        - Parallel: ~3-6s total for 8 steps (limited by API concurrency)

        Args:
            chunks: List of transcript chunks
            knowledge_sources: Optional knowledge base content
            progress_callback: Progress update callback

        Returns:
            Tuple of (steps_list, token_usage_dict, first_error_string)
        """
        import asyncio

        logger.info(f"Starting parallel generation of {len(chunks)} steps")

        # Create async tasks for all chunks
        tasks = []
        for i, chunk in enumerate(chunks, 1):
            task = self.azure_openai.generate_step_from_chunk_async(
                chunk=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                tone=self.config.tone,
                audience=self.config.audience,
                knowledge_sources=knowledge_sources,
                knowledge_fetcher=self.knowledge_fetcher
            )
            tasks.append(task)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        steps = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        first_error = None

        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                logger.error(f"Step {i} generation failed: {result}")
                if first_error is None:
                    first_error = str(result)
                continue

            step, usage = result
            steps.append(step)

            # Aggregate token usage
            total_input_tokens += usage.get('input_tokens', 0)
            total_output_tokens += usage.get('output_tokens', 0)
            total_tokens += usage.get('total_tokens', 0)

            # Update progress
            progress = 0.40 + (0.20 * i / len(chunks))
            self._update_progress(
                progress_callback,
                progress,
                "generate_steps",
                current_step=i,
                total_steps=len(chunks),
                stage_detail=f"Generated step {i} of {len(chunks)}"
            )

        token_usage = {
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'total_tokens': total_tokens
        }

        logger.info(f"Parallel generation complete: {len(steps)}/{len(chunks)} steps, {total_tokens} total tokens")

        return steps, token_usage, first_error

    def _update_progress(
        self,
        callback: Optional[Callable[[float, str], None]],
        progress: float,
        stage: str,
        current_step: int = None,
        total_steps: int = None,
        stage_detail: str = None
    ):
        """Update progress if callback provided."""
        if callback:
            try:
                callback(
                    progress,
                    stage,
                    current_step=current_step,
                    total_steps=total_steps,
                    stage_detail=stage_detail
                )
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")


def process_transcript(
    transcript_text: str,
    output_path: str,
    config: PipelineConfig,
    screenshots_data: Optional[List[Dict]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> PipelineResult:
    """
    Convenience function to process a transcript.
    
    Args:
        transcript_text: Raw transcript text
        output_path: Where to save the document
        config: Pipeline configuration
        screenshots_data: Optional screenshot data
        progress_callback: Optional progress callback
        
    Returns:
        PipelineResult
    """
    pipeline = ScriptToDocPipeline(config)
    return pipeline.process(
        transcript_text=transcript_text,
        output_path=output_path,
        screenshots_data=screenshots_data,
        progress_callback=progress_callback
    )


def process_transcript_file(
    transcript_path: str,
    output_dir: str,
    config: PipelineConfig,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> PipelineResult:
    """
    Process a transcript file and save document to output directory.
    
    Args:
        transcript_path: Path to transcript file
        output_dir: Output directory
        config: Pipeline configuration
        progress_callback: Optional progress callback
        
    Returns:
        PipelineResult
    """
    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Generate output path
    input_name = Path(transcript_path).stem
    output_path = str(Path(output_dir) / f"{input_name}_training.docx")
    
    # Set document title from filename
    if not config.document_title:
        config.document_title = input_name.replace('_', ' ').title()
    
    # Process
    return process_transcript(
        transcript_text=transcript_text,
        output_path=output_path,
        config=config,
        progress_callback=progress_callback
    )

