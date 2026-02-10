"""
Azure OpenAI Service integration for content generation.
Uses GPT-4o-mini for summarization and step generation.

Supports fallback to standard OpenAI API when Azure OpenAI is unavailable.
This ensures LLM capabilities are maintained even if Azure OpenAI fails.
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from openai import AzureOpenAI, OpenAI, AsyncAzureOpenAI, AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """
    Client for Azure OpenAI operations with fallback to standard OpenAI.
    
    Priority:
    1. Azure OpenAI (primary) - for Azure compliance and data residency
    2. Standard OpenAI (fallback) - maintains LLM capabilities if Azure OpenAI fails
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: str = "gpt-4o-mini",
        api_version: str = "2024-02-01",
        use_managed_identity: bool = False,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        use_local_mode: bool = False
    ):
        """
        Initialize Azure OpenAI client with OpenAI fallback support.

        Args:
            endpoint: Azure OpenAI endpoint URL (optional in local mode)
            api_key: Azure OpenAI API key (if not using managed identity)
            deployment: Azure OpenAI deployment name
            api_version: API version
            use_managed_identity: Use Azure Managed Identity for auth
            openai_api_key: Standard OpenAI API key (required for local mode, fallback for Azure mode)
            openai_model: Standard OpenAI model name
            use_local_mode: Use local mode (OpenAI only, skip Azure entirely)
        """
        self.deployment = deployment
        self.api_version = api_version
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.use_fallback = False

        # LOCAL MODE: Use OpenAI only, skip Azure entirely
        if use_local_mode:
            if not openai_api_key:
                raise ValueError("openai_api_key is required for local mode")
            self.client = OpenAI(api_key=openai_api_key)
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            self.use_fallback = True
            self.endpoint = None
            logger.info(f"Local mode: Using OpenAI with model {openai_model}")
            return

        # AZURE MODE: Try Azure OpenAI first, fallback to OpenAI if needed
        self.endpoint = endpoint

        # Initialize Azure OpenAI client (primary)
        self.client = None
        self.async_client = None
        try:
            if use_managed_identity:
                # Use Managed Identity with bearer token provider
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default"
                )
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_version=api_version,
                    azure_ad_token_provider=token_provider
                )
                self.async_client = AsyncAzureOpenAI(
                    azure_endpoint=endpoint,
                    api_version=api_version,
                    azure_ad_token_provider=token_provider
                )
            elif api_key:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                self.async_client = AsyncAzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
            else:
                raise ValueError("Either api_key or use_managed_identity must be provided")

            logger.info(f"Initialized Azure OpenAI client with deployment: {deployment}")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None
            self.async_client = None

        # Initialize OpenAI fallback client (secondary)
        self.fallback_client = None
        self.async_fallback_client = None
        if openai_api_key:
            try:
                self.fallback_client = OpenAI(api_key=openai_api_key)
                self.async_fallback_client = AsyncOpenAI(api_key=openai_api_key)
                logger.info(f"Initialized OpenAI fallback client with model: {openai_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI fallback client: {e}")

        # If Azure OpenAI failed, use fallback if available
        if not self.client and self.fallback_client:
            self.client = self.fallback_client
            self.async_client = self.async_fallback_client
            self.use_fallback = True
            logger.info("Using OpenAI fallback client (Azure OpenAI unavailable)")

        if not self.client:
            raise ValueError(
                "No OpenAI client available. Azure OpenAI failed and no OpenAI fallback key provided. "
                "Either configure Azure OpenAI properly or provide OPENAI_API_KEY for fallback."
            )
    
    def summarize_transcript(
        self,
        text: str,
        max_sentences: int = 10,
        tone: str = "Professional"
    ) -> Tuple[List[str], Dict]:
        """
        Summarize transcript into key points.
        
        Args:
            text: Cleaned transcript text
            max_sentences: Maximum number of summary sentences
            tone: Tone for summary (Professional, Casual, Technical)
            
        Returns:
            Tuple of (summary_sentences, token_usage)
        """
        try:
            logger.info(f"Summarizing transcript (max {max_sentences} sentences, tone: {tone})")
            
            prompt = self._build_summary_prompt(text, max_sentences, tone)
            
            # Use deployment/model name based on client type
            model_name = self.openai_model if self.use_fallback else self.deployment
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("summary")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=0.9,
                timeout=30.0  # 30 second timeout
            )
            
            content = response.choices[0].message.content
            sentences = [s.strip() for s in content.split('\n') if s.strip()]
            
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"Summary complete: {len(sentences)} sentences, {usage['total_tokens']} tokens")
            
            return sentences, usage
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            raise
    
    def generate_training_steps(
        self,
        transcript: str,
        azure_di_structure: Dict,
        target_steps: int = 8,
        tone: str = "Professional",
        audience: str = "Technical Users",
        knowledge_sources: Optional[List[Dict]] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Generate step-by-step training instructions.
        
        Args:
            transcript: Cleaned transcript text
            azure_di_structure: Structure extracted by Azure DI
            target_steps: Target number of steps to generate
            tone: Tone for instructions
            audience: Target audience
            
        Returns:
            Tuple of (steps_list, token_usage)
            Each step is a dict with: title, summary, details, actions
        """
        try:
            logger.info(f"Generating {target_steps} training steps (tone: {tone}, audience: {audience})")

            # Use simplified v2 prompt for better performance and confidence
            prompt = self._build_steps_prompt_v2(
                transcript,
                azure_di_structure,
                target_steps,
                tone,
                audience,
                knowledge_sources
            )
            
            # Use deployment/model name based on client type
            model_name = self.openai_model if self.use_fallback else self.deployment
            
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt("training_steps")},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,  # Lower temperature for more consistent, grounded responses
                    max_tokens=4000,  # Increased for more detailed steps
                    top_p=0.85,  # Slightly lower for more focused responses
                    timeout=90.0  # Increased timeout for complex prompts
                )
            except Exception as azure_error:
                # Check if it's a rate limit error
                error_str = str(azure_error).lower()
                if 'rate limit' in error_str or '429' in error_str:
                    # Extract wait time if available
                    import re
                    wait_match = re.search(r'(\d+)s', error_str)
                    wait_time = int(wait_match.group(1)) if wait_match else 60

                    error_message = (
                        f"OpenAI API rate limit exceeded. Your API quota has been exhausted.\n"
                        f"Please either:\n"
                        f"  1. Add a payment method to your OpenAI account at https://platform.openai.com/account/billing\n"
                        f"  2. Configure Azure OpenAI deployment '{self.deployment}' in Azure Portal\n"
                        f"  3. Wait {wait_time} seconds and try again"
                    )
                    raise Exception(error_message)

                # Check if it's a deployment not found error
                if 'deploymentnotfound' in error_str or '404' in error_str:
                    error_message = (
                        f"Azure OpenAI deployment '{self.deployment}' not found.\n"
                        f"Please create this deployment in Azure Portal:\n"
                        f"  1. Go to {self.endpoint}\n"
                        f"  2. Navigate to 'Deployments' section\n"
                        f"  3. Create deployment named '{self.deployment}' with model 'gpt-4o-mini'\n"
                        f"Alternatively, update AZURE_OPENAI_DEPLOYMENT in .env to match an existing deployment."
                    )
                    raise Exception(error_message)

                # If Azure OpenAI fails and we have fallback, try that
                if self.fallback_client and not self.use_fallback:
                    logger.warning(f"Azure OpenAI failed ({azure_error}), switching to OpenAI fallback")
                    self.client = self.fallback_client
                    self.use_fallback = True
                    model_name = self.openai_model

                    try:
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": self._get_system_prompt("training_steps")},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.2,  # Lower temperature for more consistent, grounded responses
                            max_tokens=4000,  # Increased for more detailed steps
                            top_p=0.85,  # Slightly lower for more focused responses
                            timeout=90.0  # Increased timeout for complex prompts
                        )
                    except Exception as fallback_error:
                        # Check for rate limits on fallback too
                        fallback_error_str = str(fallback_error).lower()
                        if 'rate limit' in fallback_error_str or '429' in fallback_error_str:
                            import re
                            wait_match = re.search(r'(\d+)s', fallback_error_str)
                            wait_time = int(wait_match.group(1)) if wait_match else 60

                            error_message = (
                                f"OpenAI API rate limit exceeded. Your API quota has been exhausted.\n"
                                f"Please either:\n"
                                f"  1. Add a payment method to your OpenAI account at https://platform.openai.com/account/billing\n"
                                f"  2. Configure Azure OpenAI deployment '{self.deployment}' in Azure Portal\n"
                                f"  3. Wait {wait_time} seconds and try again"
                            )
                            raise Exception(error_message)
                        raise fallback_error
                else:
                    raise azure_error
            
            content = response.choices[0].message.content
            steps = self._parse_steps_response(content)

            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            source = "OpenAI fallback" if self.use_fallback else "Azure OpenAI"
            logger.info(f"Generated {len(steps)} steps using {source}, {usage['total_tokens']} tokens used")
            
            return steps, usage

        except Exception as e:
            logger.error(f"Step generation failed: {str(e)}")
            raise

    def generate_step_from_chunk(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        tone: str = "Professional",
        audience: str = "Technical Users",
        knowledge_sources: Optional[List[Dict]] = None,
        knowledge_fetcher = None
    ) -> Tuple[Dict, Dict]:
        """
        Generate a SINGLE training step from a transcript chunk.

        This is the chunk-based approach for better grounding. Instead of
        generating all steps at once from the full transcript, we generate
        ONE step from ONE focused chunk.

        Benefits:
        - Better grounding (LLM focuses on smaller section)
        - Higher word overlap (less irrelevant content to dilute matching)
        - More precise steps (each step directly from its chunk)
        - Lower token usage per call

        Args:
            chunk: One chunk of the transcript (contains 6-12 sentences typically)
            chunk_index: Which chunk this is (1-based, e.g. 1, 2, 3...)
            total_chunks: Total number of chunks (usually = target_steps)
            tone: Tone for instructions
            audience: Target audience
            knowledge_sources: Optional knowledge base content

        Returns:
            Tuple of (single_step_dict, token_usage)
            Step dict has: title, summary, details, actions
        """
        try:
            logger.info(f"Generating step {chunk_index}/{total_chunks} from chunk (tone: {tone}, audience: {audience})")

            # Build focused prompt for this single chunk
            prompt = self._build_chunk_prompt(
                chunk,
                chunk_index,
                total_chunks,
                tone,
                audience,
                knowledge_sources,
                knowledge_fetcher
            )

            # Use deployment/model name based on client type
            model_name = self.openai_model if self.use_fallback else self.deployment

            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt("training_steps")},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,  # Lower temperature for consistent, grounded responses
                    max_tokens=1000,  # Reduced (single step, not multiple)
                    top_p=0.85,  # Focused responses
                    timeout=60.0  # Shorter timeout for single step
                )

                # Handle fallback on Azure OpenAI failure
                if not response:
                    raise ValueError("Empty response from API")

            except Exception as azure_error:
                # Check if it's a rate limit error
                error_str = str(azure_error).lower()
                if 'rate limit' in error_str or '429' in error_str:
                    import re
                    wait_match = re.search(r'(\d+)s', error_str)
                    wait_time = int(wait_match.group(1)) if wait_match else 60

                    error_message = (
                        f"OpenAI API rate limit exceeded. Your API quota has been exhausted.\n"
                        f"Please either:\n"
                        f"  1. Add a payment method to your OpenAI account at https://platform.openai.com/account/billing\n"
                        f"  2. Configure Azure OpenAI deployment '{self.deployment}' in Azure Portal\n"
                        f"  3. Wait {wait_time} seconds and try again"
                    )
                    raise Exception(error_message)

                # Check if it's a deployment not found error
                if 'deploymentnotfound' in error_str or '404' in error_str:
                    error_message = (
                        f"Azure OpenAI deployment '{self.deployment}' not found.\n"
                        f"Please create this deployment in Azure Portal:\n"
                        f"  1. Go to {self.endpoint}\n"
                        f"  2. Navigate to 'Deployments' section\n"
                        f"  3. Create deployment named '{self.deployment}' with model 'gpt-4o-mini'\n"
                        f"Alternatively, update AZURE_OPENAI_DEPLOYMENT in .env to match an existing deployment."
                    )
                    raise Exception(error_message)

                # Try fallback if available
                if not self.use_fallback and self.fallback_client:
                    logger.warning(f"Azure OpenAI failed ({azure_error}), switching to OpenAI fallback")
                    self.client = self.fallback_client
                    self.use_fallback = True

                    try:
                        response = self.client.chat.completions.create(
                            model=self.openai_model,
                            messages=[
                                {"role": "system", "content": self._get_system_prompt("training_steps")},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.2,
                            max_tokens=1000,
                            top_p=0.85,
                            timeout=60.0
                        )
                    except Exception as fallback_error:
                        # Check for rate limits on fallback too
                        fallback_error_str = str(fallback_error).lower()
                        if 'rate limit' in fallback_error_str or '429' in fallback_error_str:
                            import re
                            wait_match = re.search(r'(\d+)s', fallback_error_str)
                            wait_time = int(wait_match.group(1)) if wait_match else 60

                            error_message = (
                                f"OpenAI API rate limit exceeded. Your API quota has been exhausted.\n"
                                f"Please either:\n"
                                f"  1. Add a payment method to your OpenAI account at https://platform.openai.com/account/billing\n"
                                f"  2. Configure Azure OpenAI deployment '{self.deployment}' in Azure Portal\n"
                                f"  3. Wait {wait_time} seconds and try again"
                            )
                            raise Exception(error_message)
                        raise fallback_error
                else:
                    raise azure_error

            content = response.choices[0].message.content

            # Parse the single step from response
            # The response should contain ONE step in the standard format
            steps = self._parse_steps_response(content)

            if not steps or len(steps) == 0:
                logger.warning(f"No step generated from chunk {chunk_index}, using fallback")
                # Create fallback step
                step = {
                    "title": f"Step {chunk_index}: Process from transcript",
                    "summary": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                    "details": chunk,
                    "actions": []
                }
            else:
                # Take the first step (should only be one)
                step = steps[0]

                # Ensure step has proper structure
                if "title" not in step:
                    step["title"] = f"Step {chunk_index}"
                if "summary" not in step:
                    step["summary"] = chunk[:200]
                if "details" not in step:
                    step["details"] = chunk
                if "actions" not in step:
                    step["actions"] = []

            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            source = "OpenAI fallback" if self.use_fallback else "Azure OpenAI"
            logger.info(f"Generated step {chunk_index} using {source}, {usage['total_tokens']} tokens used")

            return step, usage

        except Exception as e:
            logger.error(f"Step generation from chunk {chunk_index} failed: {str(e)}")
            raise

    async def generate_step_from_chunk_async(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        tone: str = "Professional",
        audience: str = "Technical Users",
        knowledge_sources: Optional[List[Dict]] = None,
        knowledge_fetcher = None
    ) -> Tuple[Dict, Dict]:
        """
        Generate a SINGLE training step from a transcript chunk (ASYNC version).

        This enables parallel generation of multiple steps for significant speed improvements.
        Same functionality as generate_step_from_chunk but uses async OpenAI API calls.

        Args:
            chunk: One chunk of the transcript
            chunk_index: Which chunk this is (1-based)
            total_chunks: Total number of chunks
            tone: Tone for instructions
            audience: Target audience
            knowledge_sources: Optional knowledge base content
            knowledge_fetcher: Optional fetcher for intelligent extraction

        Returns:
            Tuple of (single_step_dict, token_usage)
        """
        try:
            logger.info(f"Async generating step {chunk_index}/{total_chunks}")

            # Build prompt (reuse existing logic)
            prompt = self._build_chunk_prompt(
                chunk,
                chunk_index,
                total_chunks,
                tone,
                audience,
                knowledge_sources,
                knowledge_fetcher
            )

            # Use deployment/model name based on client type
            model_name = self.openai_model if self.use_fallback else self.deployment

            # Make async API call
            response = await self.async_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("training_steps")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=0.85,
                timeout=60.0
            )

            if not response:
                raise ValueError("Empty response from API")

            content = response.choices[0].message.content

            # Parse the step
            steps = self._parse_steps_response(content)

            if not steps or len(steps) == 0:
                logger.warning(f"No step generated from chunk {chunk_index}, using fallback")
                step = {
                    "title": f"Step {chunk_index}: Process from transcript",
                    "summary": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                    "details": chunk,
                    "actions": []
                }
            else:
                step = steps[0]
                # Ensure proper structure
                if "title" not in step:
                    step["title"] = f"Step {chunk_index}"
                if "summary" not in step:
                    step["summary"] = chunk[:200]
                if "details" not in step:
                    step["details"] = chunk
                if "actions" not in step:
                    step["actions"] = []

            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            source = "OpenAI fallback" if self.use_fallback else "Azure OpenAI"
            logger.info(f"Async generated step {chunk_index} using {source}, {usage['total_tokens']} tokens")

            return step, usage

        except Exception as e:
            logger.error(f"Async step generation from chunk {chunk_index} failed: {str(e)}")
            # Return a fallback step instead of failing completely
            fallback_step = {
                "title": f"Step {chunk_index}: Process from transcript",
                "summary": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                "details": chunk,
                "actions": []
            }
            fallback_usage = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
            return fallback_step, fallback_usage

    def suggest_step_count(self, transcript: str, complexity_factors: Dict) -> int:
        """
        Suggest optimal number of steps based on content analysis.
        
        Args:
            transcript: Cleaned transcript text
            complexity_factors: Factors like word count, actions, decisions
            
        Returns:
            Suggested step count (3-15)
        """
        try:
            word_count = len(transcript.split())
            action_count = complexity_factors.get("action_count", 0)
            decision_count = complexity_factors.get("decision_count", 0)
            
            # Heuristic-based suggestion
            # Base: 1 step per 100 words
            base_steps = max(3, min(15, word_count // 100))
            
            # Adjust for complexity
            if action_count > 10:
                base_steps += 2
            if decision_count > 3:
                base_steps += 1
            
            # Clamp to reasonable range
            suggested = max(3, min(15, base_steps))
            
            logger.info(f"Suggested {suggested} steps (words: {word_count}, "
                       f"actions: {action_count}, decisions: {decision_count})")
            
            return suggested
            
        except Exception as e:
            logger.error(f"Step count suggestion failed: {str(e)}")
            return 8  # Default fallback
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Get system prompt for different task types."""
        prompts = {
            "summary": """You are a technical documentation expert specializing in training materials.
Your task is to extract the most important information from meeting transcripts and training sessions.
Focus on actionable information, key decisions, and process steps.""",
            
            "training_steps": """You are an expert technical trainer and documentation specialist.
Your task is to create clear, step-by-step training instructions from meeting transcripts.

CRITICAL REQUIREMENTS:
1. Extract steps DIRECTLY from the transcript content - do not invent or generalize
2. Use specific phrases, terminology, and details mentioned in the transcript
3. Each step must be grounded in actual transcript content
4. Follow a chain of thought: analyze transcript → identify key actions → structure as steps
5. Match the exact sequence and details described in the transcript
6. IGNORE OFF-TOPIC CONTENT - focus only on training-related material

TOPIC RELEVANCE FILTERING:
- Identify the main training topic at the start
- Skip sections that are off-topic (personal stories, unrelated discussions, tangents)
- Focus ONLY on content that relates to the training subject
- If the trainer goes off-topic, ignore those sections and continue with training content
- Look for topic indicators: training instructions, step-by-step procedures, technical explanations

Your steps must be:
- Grounded in transcript content (not generic or invented)
- Related to the MAIN TRAINING TOPIC (not off-topic tangents)
- Clear and actionable
- Well-structured (title, overview, actions)
- Professional and consistent in tone
- Sequential and logical"""
        }
        
        return prompts.get(task_type, "You are a helpful AI assistant.")
    
    def _build_summary_prompt(
        self,
        text: str,
        max_sentences: int,
        tone: str
    ) -> str:
        """Build prompt for transcript summarization."""
        return f"""Summarize the following meeting transcript into exactly {max_sentences} key sentences.

Tone: {tone}

Focus on:
- Main actions discussed
- Key decisions made
- Important steps or processes
- Critical information

Transcript:
{text[:3000]}  # Limit to first 3000 chars to save tokens

Provide {max_sentences} clear, concise summary sentences. Number each sentence."""
    
    def _build_steps_prompt(
        self,
        transcript: str,
        structure: Dict,
        target_steps: int,
        tone: str,
        audience: str,
        knowledge_sources: Optional[List[Dict]] = None
    ) -> str:
        """Build prompt for training step generation with few-shot examples and chain of thought."""
        # Extract relevant structure information
        actions = ", ".join(structure.get("actions", [])[:10])
        sequence_indicators = len(structure.get("sequence_indicators", []))
        
        # Few-shot examples
        few_shot_examples = self._get_few_shot_examples()
        
        return f"""You are creating step-by-step training instructions from a meeting transcript.

TARGET AUDIENCE: {audience}
TONE: {tone}

CRITICAL INSTRUCTIONS - Follow This Process for Maximum Accuracy:

PHASE 0: TOPIC RELEVANCE FILTERING (IMPORTANT!)
Before analyzing, identify and IGNORE off-topic content:
1. Identify the MAIN TRAINING TOPIC - what is the core subject being taught?
2. Mark sections that are OFF-TOPIC (e.g., personal stories, unrelated discussions, tangents, small talk)
3. IGNORE off-topic content when extracting steps - focus ONLY on training-related content
4. If trainer goes off-topic, skip those sections and continue with training content
5. Look for topic shifts: phrases like "by the way", "that reminds me", "off topic", "let me tell you about", etc.

Examples of OFF-TOPIC content to IGNORE:
- Personal anecdotes unrelated to training
- Discussions about weather, sports, news
- Side conversations about unrelated topics
- Jokes or stories that don't relate to the training
- Administrative announcements (unless relevant to training steps)
- Social chit-chat between participants

Examples of ON-TOPIC content to KEEP:
- Instructions on how to perform actions
- Explanations of processes or workflows
- Step-by-step procedures
- Technical details about the subject
- Configuration settings and values
- UI navigation and button clicks
- Error handling and troubleshooting related to the training

PHASE 1: DEEP TRANSCRIPT ANALYSIS (ONLY ON-TOPIC CONTENT)
1. Read the transcript carefully, focusing ONLY on training-related content
2. Identify the main topic/workflow - quote the exact phrase that describes it
3. Extract EVERY action mentioned - list them in exact order (skip off-topic sections)
4. Capture ALL specific terminology - button names, menu items, URLs, values, settings
5. Note sequence indicators - "first", "next", "then", "after", "finally"
6. Identify conditional logic - "if X then Y", "either A or B", etc.

PHASE 2: EXACT TERMINOLOGY EXTRACTION
For maximum accuracy and source matching, extract:
- Exact button names (use quotes: 'Create a resource')
- Exact menu paths (e.g., "Configuration in the settings menu")
- Exact URLs (e.g., "portal.azure.com")
- Exact values/settings (e.g., "'Hot' for frequently accessed data")
- Exact technical terms (preserve capitalization and spelling)
- Exact phrases describing actions (don't paraphrase)

PHASE 3: STEP STRUCTURING
1. Group related actions from Phase 1 into logical steps
2. Maintain the exact sequence from the transcript
3. Each step should represent a distinct phase or decision point
4. Preserve conditional logic and options mentioned

PHASE 4: WRITE WITH MAXIMUM ACCURACY
For each step:
1. TITLE: Use exact terminology from Phase 2
2. SUMMARY: Reference specific transcript content using exact phrases
3. DETAILS: Use actual details from transcript - quote UI elements, values, settings
4. ACTIONS: Use exact actions from Phase 1, in the same order

ACCURACY VALIDATION (Apply to EVERY step):
✓ Every phrase can be found in the transcript (word-for-word or very close)
✓ Button names, menu items, URLs match transcript exactly
✓ Actions follow transcript sequence
✓ Specific values, settings, options are preserved
✓ Terminology matches transcript (no substitutions)
✓ No generic descriptions replace specific transcript content

CRITICAL: If you cannot find specific content in the transcript for a step, DO NOT invent it. Instead, combine related actions into fewer, more detailed steps that are fully grounded in transcript content.

DETECTED CONTEXT:
- Actions mentioned: {actions}
- Sequential indicators found: {sequence_indicators}

FEW-SHOT EXAMPLES (Study these to understand the expected format and quality):

{few_shot_examples}

NOW, analyze this transcript and create {target_steps} training steps:

TRANSCRIPT:
{transcript[:6000]}  # Increased length to provide more context

{f'''{self._format_knowledge_sources(knowledge_sources)}''' if knowledge_sources else ''}

CHAIN OF THOUGHT ANALYSIS - Complete this analysis step-by-step before generating:

STEP 0: FILTER FOR TOPIC RELEVANCE (CRITICAL!)
Identify what is ON-TOPIC vs OFF-TOPIC:
- Main Training Topic: [What is the core subject being taught?]
- Off-Topic Sections Found: [List any sections that are unrelated to training - personal stories, tangents, etc.]
- Decision: [Will you ignore off-topic sections? YES - focus only on training content]

STEP 1: IDENTIFY MAIN TOPIC (FROM ON-TOPIC CONTENT ONLY)
What is the primary topic, process, or workflow described in the TRAINING-RELATED parts of this transcript?
Answer: [Be specific - quote key phrases from transcript that relate to training]

STEP 2: EXTRACT ALL ACTIONS (IN ORDER, ON-TOPIC ONLY)
List every specific TRAINING-RELATED action mentioned in the transcript, in the exact sequence they appear:
[SKIP any actions mentioned during off-topic discussions]
1. [Quote the exact action from transcript - training-related only]
2. [Quote the exact action from transcript - training-related only]
3. [Continue for ALL training actions...]

STEP 3: EXTRACT EXACT TERMINOLOGY
What exact words, phrases, and terminology are used? Copy them verbatim:
- Exact Phrases: [list phrases word-for-word from transcript]
- UI Elements: [list exact button names, menu items, options - use quotes if mentioned]
- URLs/Paths: [list exact URLs or file paths]
- Values/Settings: [list exact values, settings, configurations mentioned]
- Technical Terms: [list exact technical terminology used]

STEP 4: IDENTIFY SEQUENCE MARKERS
What words indicate sequence or order in the transcript?
- Found: [list words like "first", "next", "then", "after", "finally", etc.]

STEP 5: PLAN STEP STRUCTURE
How should these actions be organized into {target_steps} logical steps?
- Step 1 will cover: [list specific actions from Step 2 that belong together]
- Step 2 will cover: [list specific actions from Step 2 that belong together]
- [Continue for all {target_steps} steps...]

STEP 6: VALIDATION CHECKLIST (Before writing each step)
For each step you create, verify:
✓ Is this step related to the MAIN TRAINING TOPIC? (Not off-topic content)
✓ Does the TITLE use exact terminology from Step 3?
✓ Does the SUMMARY reference specific content from the transcript?
✓ Do the DETAILS use exact phrases and terminology from Step 3?
✓ Do the ACTIONS match the exact sequence and wording from Step 2?
✓ Could someone find every word/phrase in your step by searching the transcript?
✓ Are you using quotes for UI elements exactly as mentioned?
✓ Have you excluded any off-topic content from this step?

NOW generate the {target_steps} steps. For each step:
1. Use the exact terminology you extracted in Step 3
2. Follow the sequence you identified in Step 2
3. Reference specific UI elements, URLs, and values from Step 3
4. Match the structure you planned in Step 5

OUTPUT FORMAT - Follow this EXACT structure for each step:

---
STEP [N]: [Title - MUST use exact terminology from transcript]
SUMMARY: [One sentence - MUST reference specific transcript content, use exact phrases]
DETAILS: [2-3 sentences - MUST use actual details, terminology, and phrases from transcript. Explain what and why using transcript context.]
ACTIONS:
- [Action 1 - MUST be exact phrase/action from transcript]
- [Action 2 - MUST be exact phrase/action from transcript]
- [Action 3 - MUST be exact phrase/action from transcript]
[Add more actions as needed, but each must come from transcript]
---

CRITICAL OUTPUT REQUIREMENTS:
1. TOPIC RELEVANCE: Each step must relate to the MAIN TRAINING TOPIC - exclude off-topic content
2. TITLE: Must contain exact terminology from transcript (button names, menu items, URLs, etc.)
3. SUMMARY: Must reference specific transcript content - use exact phrases where possible
4. DETAILS: Must use actual details from transcript - quote specific UI elements, values, settings
5. ACTIONS: Each action must be a direct quote or close paraphrase of actions mentioned in transcript
6. SEQUENCE: Actions must follow the order they appear in the transcript (training content only)
7. TERMINOLOGY: Use exact words/phrases from transcript - do not substitute or generalize

ACCURACY CHECK: Before finalizing each step, ask:
- Is this step related to the MAIN TRAINING TOPIC? (Not a tangent or off-topic discussion)
- Can I find every phrase in this step by searching the transcript?
- Am I using exact button names, menu items, URLs as mentioned?
- Are my actions in the same order as the transcript?
- Have I preserved specific values, settings, or options mentioned?
- Have I excluded any off-topic content (personal stories, unrelated discussions)?

Generate exactly {target_steps} steps. Each step must be directly based on transcript content with maximum accuracy."""

    def _build_steps_prompt_v2(
        self,
        transcript: str,
        structure: Dict,
        target_steps: int,
        tone: str,
        audience: str,
        knowledge_sources: Optional[List[Dict]] = None
    ) -> str:
        """
        Build SIMPLIFIED prompt for training step generation (v2 - Performance Optimized).

        This version removes:
        - Chain-of-thought overhead
        - Excessive few-shot examples
        - Repetitive validation rules
        - Topic filtering complexity

        Focuses on: Direct instructions + Clear format + Quote transcript
        """
        # Extract relevant structure information (same as v1)
        actions = ", ".join(structure.get("actions", [])[:10])
        sequence_indicators = len(structure.get("sequence_indicators", []))

        # Format knowledge sources if provided
        knowledge_context = ""
        if knowledge_sources:
            knowledge_context = self._format_knowledge_sources(knowledge_sources)

        return f"""Create {target_steps} step-by-step training instructions from the transcript below.

TARGET AUDIENCE: {audience}
TONE: {tone}

🎯 CORE RULE: Quote the transcript DIRECTLY - do not paraphrase or generalize.

INSTRUCTIONS:
1. Read the transcript and identify the main process being taught
2. Extract {target_steps} logical steps in the order they appear
3. For each step, use EXACT phrases, button names, URLs, and terminology from the transcript
4. If the transcript says "Click on 'Create a resource'", write that exactly - not "Click create button"
5. Preserve specific values, settings, and technical terms as stated
6. Follow the sequence from the transcript - do not reorganize

DETECTED CONTEXT:
- Key actions mentioned: {actions if actions else 'analyzing...'}
- Sequence indicators: {sequence_indicators} found

OUTPUT FORMAT (follow exactly):

---
STEP 1: [Title using exact terminology from transcript]
SUMMARY: [One sentence with direct quotes or close paraphrases from transcript]
DETAILS: [2-3 sentences using actual details, specific UI elements, values, and settings mentioned in transcript]
ACTIONS:
- [Exact action from transcript]
- [Exact action from transcript]
- [Continue as needed]
---

STEP 2: [Continue same format...]

EXAMPLE (GOOD - Uses exact quotes):
Transcript: "Navigate to portal.azure.com and click 'Create a resource' in the top menu."
Output: "STEP 1: Access Azure Portal
SUMMARY: Navigate to portal.azure.com and click 'Create a resource' in the top menu.
DETAILS: The first step requires navigating to the Azure portal at portal.azure.com. Once loaded, locate and click the 'Create a resource' button which is positioned in the top menu of the portal interface.
ACTIONS:
- Navigate to portal.azure.com
- Click 'Create a resource' in the top menu"

EXAMPLE (BAD - Paraphrases instead of quoting):
Output: "STEP 1: Open Azure
SUMMARY: Go to the Azure website and create resources.
DETAILS: Access the Azure platform and use the creation functionality.
ACTIONS:
- Open Azure portal
- Use creation feature"

TRANSCRIPT:
{transcript[:8000]}

{knowledge_context}

Generate exactly {target_steps} steps now. Quote the transcript directly - use exact words, phrases, and terminology."""

    def _build_chunk_prompt(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        tone: str,
        audience: str,
        knowledge_sources: Optional[List[Dict]] = None,
        knowledge_fetcher = None
    ) -> str:
        """
        Build focused prompt for generating ONE step from ONE chunk.

        This is much simpler than the full multi-step prompt because:
        - We only generate 1 step
        - The chunk is already focused (6-12 sentences)
        - No need for analysis/filtering (chunk is pre-selected)
        - Intelligently extracts relevant knowledge excerpts for THIS chunk
        """
        # Format knowledge sources if provided (with intelligent excerpt extraction)
        knowledge_context = ""
        if knowledge_sources:
            knowledge_context = self._format_knowledge_sources(
                knowledge_sources=knowledge_sources,
                search_text=chunk,  # Use chunk as search text for relevance
                knowledge_fetcher=knowledge_fetcher
            )

        return f"""Create ONE training step from the transcript chunk below.

This is step {chunk_index} of {total_chunks} total steps.

TARGET AUDIENCE: {audience}
TONE: {tone}

## CORE REQUIREMENTS

🎯 **GROUNDING RULE**: Quote the transcript chunk DIRECTLY - use exact phrases, button names, URLs, and terminology.

📋 **STRUCTURE REQUIREMENTS**:
1. **TITLE**: Action-oriented (start with verb or gerund), 5-10 words
   - Good: "Configuring GitHub Encrypted Secrets"
   - Bad: "Secrets" or "Learn About Configuration"

2. **OVERVIEW**: 1-2 sentences answering "What will the reader accomplish?"
   - Must use direct quotes or close paraphrases from chunk
   - Do NOT repeat the title
   - Focus on the outcome or purpose

3. **CONTENT**: 2-4 paragraphs (minimum 50 words total)
   - Explain the concept, not just list steps
   - Include context: why this matters, when to use it
   - Use specific UI elements, values, settings from chunk
   - For {audience.lower()}: {"include specifics, edge cases, code patterns" if "technical" in audience.lower() else "focus on benefits and outcomes"}

4. **KEY ACTIONS**: Exactly 3-6 specific, actionable items
   - Each action MUST start with a STRONG verb
   - ✅ ALLOWED VERBS: Configure, Create, Add, Set, Run, Define, Verify, Navigate,
                       Implement, Deploy, Enable, Disable, Update, Remove, Test,
                       Install, Initialize, Execute, Validate, Monitor, Open, Click,
                       Select, Enter, Choose, Specify, Build, Launch, Start, Stop
   - ❌ FORBIDDEN VERBS: Learn, Understand, Review, Read, Know, Remember, Consider,
                         Be aware, Keep in mind, Note that, Ensure you understand,
                         Try, Attempt, Make sure, Check out, Look at
   - Sequence logically: setup → configure → implement → verify
   - Be specific enough to execute immediately

## OUTPUT FORMAT (follow exactly):

---
STEP {chunk_index}: [Title using exact terminology from chunk]
OVERVIEW: [1-2 sentences - what reader will accomplish]
CONTENT: [2-4 paragraphs explaining the concept, minimum 50 words, using actual details from chunk]
KEY ACTIONS:
- [Strong verb]: [Specific description from chunk]
- [Strong verb]: [Specific description from chunk]
- [Strong verb]: [Specific description from chunk]
[Continue for 3-6 total actions]
---

## QUALITY CHECKLIST (verify before submitting):
✓ Title starts with action verb or gerund
✓ Overview is 1-2 sentences and doesn't repeat title
✓ Content is 50+ words with actual details from chunk
✓ 3-6 actions present (not fewer, not more)
✓ Every action starts with an allowed strong verb
✓ Actions use exact terminology from chunk
✓ No weak verbs (learn, understand, review, etc.)

CHUNK {chunk_index}:
{chunk}

{knowledge_context}

Generate exactly ONE step now. Follow the structure requirements and quality checklist above."""

    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for step generation with exact format matching."""
        return """EXAMPLE 1 - High Quality, Transcript-Grounded:
TRANSCRIPT EXCERPT: "First, you need to log into the Azure portal. Go to portal.azure.com and sign in with your work credentials. Once you're in, navigate to the Resource Groups section in the left sidebar."

STEP 1: Access Azure Portal
SUMMARY: Log into the Azure portal at portal.azure.com using work credentials, then navigate to the Resource Groups section in the left sidebar.
DETAILS: The first step requires accessing the Azure portal at portal.azure.com. You must sign in using your work credentials as mentioned in the transcript. After successful authentication, you'll see the Azure dashboard with various services available. The transcript specifically mentions navigating to the Resource Groups section in the left sidebar, which is where you'll begin managing resources.
ACTIONS:
- Navigate to portal.azure.com in your web browser
- Sign in using your work credentials
- Locate the Resource Groups section in the left sidebar

ANALYSIS: This step uses EXACT phrases from transcript: "portal.azure.com", "work credentials", "Resource Groups section", "left sidebar". Every detail comes directly from the transcript excerpt.

---

EXAMPLE 2 - High Quality, Transcript-Grounded:
TRANSCRIPT EXCERPT: "Next, we'll create a new storage account. Click on 'Create a resource' button at the top, then search for 'Storage account' and select it. Fill in the resource group name, choose a unique storage account name, and select the region closest to you."

STEP 2: Create Storage Account
SUMMARY: Create a new storage account by clicking 'Create a resource' at the top, searching for 'Storage account', then configuring the resource group name, storage account name, and region.
DETAILS: To create a storage account, the transcript instructs you to click on the 'Create a resource' button located at the top of the Azure portal. After clicking, you need to search for 'Storage account' in the marketplace and select it. The transcript then specifies three required inputs: fill in the resource group name, choose a unique storage account name (the transcript emphasizes it must be unique), and select the region closest to your location.
ACTIONS:
- Click on 'Create a resource' button at the top of the portal
- Search for 'Storage account' in the marketplace and select it
- Fill in the resource group name
- Choose a unique storage account name
- Select the region closest to your location

ANALYSIS: This step uses EXACT phrases: "'Create a resource' button", "'Storage account'", "resource group name", "unique storage account name", "region closest to you". The sequence matches the transcript exactly.

---

EXAMPLE 3 - High Quality, Transcript-Grounded:
TRANSCRIPT EXCERPT: "After the storage account is created, you need to configure the access tier. Go to the storage account you just created, click on 'Configuration' in the settings menu, and set the access tier to 'Hot' for frequently accessed data or 'Cool' for archival purposes."

STEP 3: Configure Storage Account Access Tier
SUMMARY: Configure the access tier by navigating to the storage account, clicking 'Configuration' in the settings menu, and setting it to 'Hot' for frequent access or 'Cool' for archival.
DETAILS: After the storage account is created, the transcript states you need to configure the access tier. The process involves going to the storage account you just created, then clicking on 'Configuration' in the settings menu. The transcript provides specific guidance: set the access tier to 'Hot' for frequently accessed data, or 'Cool' for archival purposes. This distinction is important for cost optimization based on data access patterns.
ACTIONS:
- Navigate to the storage account you just created
- Click on 'Configuration' in the settings menu
- Set the access tier to 'Hot' for frequently accessed data or 'Cool' for archival purposes

ANALYSIS: This step uses EXACT phrases: "'Configuration'", "settings menu", "'Hot' for frequently accessed data", "'Cool' for archival purposes". The conditional logic (Hot vs Cool) is preserved exactly as stated in the transcript.

---

CRITICAL QUALITY INDICATORS (What makes these examples excellent):
✓ Every phrase, button name, menu item, and URL comes directly from the transcript
✓ The sequence of actions matches the transcript order exactly
✓ Specific terminology is preserved (e.g., "work credentials", not "login credentials")
✓ UI elements are referenced exactly as mentioned ("'Create a resource' button", not "create button")
✓ Conditional logic and options are preserved ("Hot" vs "Cool", not generalized)
✓ Details explain WHY using transcript context, not generic explanations
✓ Actions are numbered and specific, using exact transcript phrases

WHAT TO AVOID:
✗ Generic descriptions like "Navigate to the portal" (use "portal.azure.com")
✗ Invented details not in transcript (e.g., "Click the blue button" when color isn't mentioned)
✗ Generalized actions (e.g., "Configure settings" instead of "Click on 'Configuration' in the settings menu")
✗ Changing terminology (e.g., "login" instead of "work credentials" when that's what transcript says)
✗ Skipping specific values mentioned (e.g., not mentioning "Hot" and "Cool" options)"""
    
    def _parse_steps_response(self, content: str) -> List[Dict]:
        """
        Parse the structured step response from GPT.

        Extracts steps in the format:
        STEP 1: Title
        OVERVIEW/SUMMARY: ...
        CONTENT/DETAILS: ...
        KEY ACTIONS/ACTIONS:
        - Action 1
        - Action 2

        Supports both new format (OVERVIEW, CONTENT, KEY ACTIONS) and legacy format
        (SUMMARY, DETAILS, ACTIONS) for backward compatibility.

        Args:
            content: Raw response from GPT

        Returns:
            List of step dictionaries with keys: title, summary, details, actions
        """
        steps = []
        current_step = None
        current_section = None
        current_actions = []

        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and separators
            if not line or line == '---':
                continue

            # Check for step header
            if line.upper().startswith('STEP'):
                # Save previous step if exists
                if current_step:
                    current_step['actions'] = current_actions
                    steps.append(current_step)

                # Start new step
                title = line.split(':', 1)[1].strip() if ':' in line else "Untitled Step"
                current_step = {
                    "title": title,
                    "summary": "",
                    "details": "",
                    "actions": []
                }
                current_actions = []
                current_section = None

            # Check for section headers (support both new and legacy formats)
            elif line.upper().startswith('OVERVIEW:') or line.upper().startswith('SUMMARY:'):
                current_section = 'summary'
                text = line.split(':', 1)[1].strip() if ':' in line else ""
                if current_step and text:
                    current_step['summary'] = text

            elif line.upper().startswith('CONTENT:') or line.upper().startswith('DETAILS:'):
                current_section = 'details'
                text = line.split(':', 1)[1].strip() if ':' in line else ""
                if current_step and text:
                    current_step['details'] = text

            elif line.upper().startswith('KEY ACTIONS:') or line.upper().startswith('ACTIONS:'):
                current_section = 'actions'

            # Handle bullet points for actions
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                action_text = line[1:].strip()
                if action_text and current_section == 'actions':
                    current_actions.append(action_text)

            # Continuation of previous section
            elif current_step and current_section:
                if current_section == 'summary' and not current_step['summary']:
                    current_step['summary'] = line
                elif current_section == 'details':
                    if current_step['details']:
                        current_step['details'] += " " + line
                    else:
                        current_step['details'] = line

        # Save last step
        if current_step:
            current_step['actions'] = current_actions
            steps.append(current_step)

        # Validate steps
        valid_steps = []
        for i, step in enumerate(steps, 1):
            if step.get('title') and (step.get('summary') or step.get('details')):
                valid_steps.append(step)
            else:
                logger.warning(f"Step {i} incomplete, skipping: {step.get('title', 'No title')}")

        return valid_steps
    
    def enhance_step_with_context(
        self,
        step: Dict,
        source_references: List[str]
    ) -> Dict:
        """
        Enhance a generated step with additional context from source references.
        
        Args:
            step: Original step dictionary
            source_references: List of relevant transcript excerpts
            
        Returns:
            Enhanced step dictionary
        """
        if not source_references:
            return step
        
        try:
            # Build context from sources
            context = "\n".join(source_references[:3])  # Use top 3 sources
            
            prompt = f"""Enhance this training step with additional relevant details from the source material.

CURRENT STEP:
Title: {step['title']}
Summary: {step.get('summary', '')}
Details: {step.get('details', '')}

SOURCE MATERIAL:
{context}

Provide an enhanced DETAILS section that incorporates relevant information from the sources.
Keep it concise (2-3 sentences). Maintain the same tone and style."""
            
            # Use deployment/model name based on client type
            model_name = self.openai_model if self.use_fallback else self.deployment
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a technical documentation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
                timeout=30.0  # 30 second timeout
            )
            
            enhanced_details = response.choices[0].message.content.strip()
            step['details'] = enhanced_details
            
            return step
            
        except Exception as e:
            logger.error(f"Step enhancement failed: {str(e)}")
            return step  # Return original on error
    
    def _format_knowledge_sources(
        self,
        knowledge_sources: List[Dict],
        search_text: Optional[str] = None,
        knowledge_fetcher = None
    ) -> str:
        """
        Format knowledge sources for inclusion in prompts with intelligent excerpt extraction.

        Args:
            knowledge_sources: List of knowledge source dictionaries
            search_text: Optional text to find relevant excerpts (e.g., current chunk)
            knowledge_fetcher: Optional KnowledgeFetcher instance for intelligent extraction

        Returns:
            Formatted string for prompt
        """
        if not knowledge_sources:
            return ""

        formatted = ["\n\n=== RELEVANT KNOWLEDGE SOURCES ==="]
        formatted.append("The following knowledge sources provide additional context for this content.")
        formatted.append("Use them to enhance technical accuracy, provide best practices, and add valuable details.")
        formatted.append("")

        # If we have search text and knowledge_fetcher, find relevant excerpts
        if search_text and knowledge_fetcher and hasattr(knowledge_fetcher, 'find_relevant_excerpts'):
            try:
                relevant_excerpts = knowledge_fetcher.find_relevant_excerpts(
                    knowledge_sources=knowledge_sources,
                    search_text=search_text,
                    max_excerpts_per_source=2,  # Top 2 excerpts per source
                    excerpt_length=600  # 600 chars per excerpt
                )

                if relevant_excerpts:
                    formatted.append("📚 MOST RELEVANT EXCERPTS (sorted by relevance):")
                    formatted.append("")

                    for idx, excerpt_data in enumerate(relevant_excerpts[:5], 1):  # Top 5 overall
                        title = excerpt_data.get("source_title", "Unknown")
                        url = excerpt_data.get("source_url", "")
                        excerpt = excerpt_data.get("excerpt", "")
                        relevance = excerpt_data.get("relevance_score", 0.0)

                        formatted.append(f"[Excerpt {idx}] {title} (Relevance: {relevance:.2f})")
                        formatted.append(f"URL: {url}")
                        formatted.append(f"Content: {excerpt}")
                        formatted.append("")

                    formatted.append("=" * 60)
                    formatted.append("")
                else:
                    # Fallback to full sources if no relevant excerpts found
                    formatted = self._format_full_knowledge_sources(knowledge_sources)
            except Exception as e:
                logger.warning(f"Failed to extract relevant excerpts: {e}, using full sources")
                formatted = self._format_full_knowledge_sources(knowledge_sources)
        else:
            # Use full sources if no search text provided
            formatted = self._format_full_knowledge_sources(knowledge_sources)

        formatted.append("📝 INSTRUCTIONS FOR USING KNOWLEDGE SOURCES:")
        formatted.append("")
        formatted.append("✓ DO:")
        formatted.append("  • Use knowledge to add technical depth and accuracy")
        formatted.append("  • Incorporate best practices and expert recommendations")
        formatted.append("  • Clarify technical terms with knowledge context")
        formatted.append("  • Reference specific details that enhance the transcript content")
        formatted.append("")
        formatted.append("✗ DON'T:")
        formatted.append("  • Replace transcript content with knowledge content")
        formatted.append("  • Contradict the transcript - prioritize transcript when conflicts arise")
        formatted.append("  • Add generic information already clear from transcript")
        formatted.append("  • Over-complicate simple concepts")
        formatted.append("")

        return "\n".join(formatted)

    def _format_full_knowledge_sources(self, knowledge_sources: List[Dict]) -> List[str]:
        """Format full knowledge sources (fallback when intelligent extraction not available)."""
        formatted = ["\n\n=== KNOWLEDGE SOURCES ==="]

        for idx, source in enumerate(knowledge_sources, 1):
            if source.get("error"):
                continue  # Skip failed sources

            url = source.get("url", "")
            title = source.get("title", "Untitled")
            content = source.get("content", "")
            source_type = source.get("type", "unknown")

            if content:
                # Increased from 1500 to 2500 for better context
                content_preview = content[:2500] + "..." if len(content) > 2500 else content
                formatted.append(f"")
                formatted.append(f"[Source {idx}] {title}")
                formatted.append(f"URL: {url}")
                formatted.append(f"Type: {source_type}")
                formatted.append(f"Content:\n{content_preview}")
                formatted.append("")

        return formatted

