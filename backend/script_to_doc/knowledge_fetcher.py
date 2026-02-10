"""
Knowledge source fetcher for ScriptToDoc.
Fetches and extracts content from URLs.
"""

import asyncio
import logging
import re
import time
import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin, quote_plus
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not available, async fetching disabled")

logger = logging.getLogger(__name__)


class KnowledgeFetcher:
    """Fetch and extract knowledge from URLs with intelligent content extraction."""

    def __init__(
        self,
        timeout: int = 30,
        max_content_length: int = 100000,  # Increased from 50k to 100k for better context
        cache_dir: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 86400  # 24 hours in seconds
    ):
        """
        Initialize knowledge fetcher.

        Args:
            timeout: Request timeout in seconds
            max_content_length: Maximum content length to extract (characters)
            cache_dir: Directory for caching (None = in-memory only)
            enable_cache: Enable caching of fetched content
            cache_ttl: Cache time-to-live in seconds
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # In-memory cache
        self._memory_cache: Dict[str, Tuple[Dict, float]] = {}

        # File-based cache
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached(self, url: str) -> Optional[Dict]:
        """Get cached content if available and not expired."""
        if not self.enable_cache:
            return None
        
        cache_key = self._get_cache_key(url)
        current_time = time.time()
        
        # Check in-memory cache
        if cache_key in self._memory_cache:
            cached_data, cached_time = self._memory_cache[cache_key]
            if current_time - cached_time < self.cache_ttl:
                logger.info(f"Using cached content for URL: {url}")
                return cached_data
            else:
                # Expired, remove from cache
                del self._memory_cache[cache_key]
        
        # Check file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    cached_time = cache_data.get('cached_at', 0)
                    if current_time - cached_time < self.cache_ttl:
                        logger.info(f"Using file-cached content for URL: {url}")
                        return cache_data.get('content')
                    else:
                        # Expired, remove file
                        cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Error reading cache file: {e}")
        
        return None
    
    def _set_cached(self, url: str, content: Dict):
        """Cache content for URL."""
        if not self.enable_cache:
            return
        
        cache_key = self._get_cache_key(url)
        current_time = time.time()
        
        # Store in memory cache
        self._memory_cache[cache_key] = (content, current_time)
        
        # Store in file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'url': url,
                        'cached_at': current_time,
                        'content': content
                    }, f, indent=2)
            except Exception as e:
                logger.warning(f"Error writing cache file: {e}")
    
    def fetch_url_content(self, url: str) -> Optional[Dict[str, any]]:
        """
        Fetch and extract content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with 'url', 'title', 'content', 'type', 'error' or None if failed
        """
        # Check cache first
        cached = self._get_cached(url)
        if cached:
            return cached
        
        try:
            logger.info(f"Fetching content from URL: {url}")
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"Invalid URL format: {url}")
                return {
                    "url": url,
                    "title": "Invalid URL",
                    "content": "",
                    "type": "error",
                    "error": "Invalid URL format"
                }
            
            # Fetch content
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Handle different content types
            result = None
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                result = self._extract_pdf_content(url, response.content)
            elif 'text/html' in content_type or 'text' in content_type:
                result = self._extract_html_content(url, response.text)
            else:
                # Try to extract as text
                try:
                    text_content = response.text[:self.max_content_length]
                    result = {
                        "url": url,
                        "title": self._extract_title_from_url(url),
                        "content": text_content,
                        "type": "text",
                        "error": None
                    }
                except:
                    logger.warning(f"Could not extract text from {url}")
                    result = {
                        "url": url,
                        "title": self._extract_title_from_url(url),
                        "content": "",
                        "type": "error",
                        "error": "Unsupported content type"
                    }
            
            # Cache successful results
            if result and not result.get("error"):
                self._set_cached(url, result)
            
            return result
                    
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching URL: {url}")
            return {
                "url": url,
                "title": "Timeout",
                "content": "",
                "type": "error",
                "error": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return {
                "url": url,
                "title": "Error",
                "content": "",
                "type": "error",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching URL {url}: {str(e)}", exc_info=True)
            return {
                "url": url,
                "title": "Error",
                "content": "",
                "type": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _extract_html_content(self, url: str, html_content: str) -> Dict[str, any]:
        """Extract text content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else self._extract_title_from_url(url)
            
            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I))
            
            if main_content:
                text_content = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to body
                body = soup.find('body')
                text_content = body.get_text(separator=' ', strip=True) if body else ""
            
            # Clean up whitespace
            text_content = re.sub(r'\s+', ' ', text_content)
            text_content = text_content[:self.max_content_length]
            
            return {
                "url": url,
                "title": title_text,
                "content": text_content,
                "type": "web",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error extracting HTML content from {url}: {str(e)}")
            return {
                "url": url,
                "title": self._extract_title_from_url(url),
                "content": "",
                "type": "error",
                "error": f"HTML extraction error: {str(e)}"
            }
    
    def _extract_pdf_content(self, url: str, pdf_bytes: bytes) -> Dict[str, any]:
        """Extract text content from PDF."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            
            text_content = ' '.join(text_parts)
            text_content = re.sub(r'\s+', ' ', text_content)
            text_content = text_content[:self.max_content_length]
            
            # Extract title from metadata or first line
            title = reader.metadata.get('/Title', '') if reader.metadata else ''
            if not title:
                # Try first line of content
                first_line = text_content.split('\n')[0][:100] if text_content else ''
                title = first_line or self._extract_title_from_url(url)
            
            return {
                "url": url,
                "title": title,
                "content": text_content,
                "type": "pdf",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error extracting PDF content from {url}: {str(e)}")
            return {
                "url": url,
                "title": self._extract_title_from_url(url),
                "content": "",
                "type": "error",
                "error": f"PDF extraction error: {str(e)}"
            }
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if path:
            # Use last part of path
            title = path.split('/')[-1]
            # Remove file extension
            title = title.rsplit('.', 1)[0] if '.' in title else title
            # Replace hyphens/underscores with spaces
            title = title.replace('-', ' ').replace('_', ' ')
            return title.title()
        return parsed.netloc
    
    def fetch_multiple_urls(self, urls: List[str]) -> List[Dict[str, any]]:
        """
        Fetch content from multiple URLs.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of content dictionaries
        """
        # Try async first if available
        if HAS_AIOHTTP:
            try:
                return asyncio.run(self.fetch_multiple_urls_async(urls))
            except Exception as e:
                logger.warning(f"Async fetch failed, falling back to sync: {e}")

        # Fallback to synchronous fetching
        results = []
        for url in urls:
            if not url or not url.strip():
                continue

            result = self.fetch_url_content(url.strip())
            if result:
                results.append(result)

            # Small delay to avoid overwhelming servers
            time.sleep(0.5)

        return results

    async def fetch_multiple_urls_async(self, urls: List[str]) -> List[Dict[str, any]]:
        """
        Fetch content from multiple URLs in parallel using async.

        This is 5-10x faster than sequential fetching for multiple URLs.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of content dictionaries
        """
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp required for async fetching")

        # Filter empty URLs
        valid_urls = [url.strip() for url in urls if url and url.strip()]

        if not valid_urls:
            return []

        logger.info(f"Fetching {len(valid_urls)} URLs in parallel")

        # Create async tasks
        async with aiohttp.ClientSession(
            headers={'User-Agent': self.session.headers['User-Agent']},
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            tasks = [self._fetch_url_async(session, url) for url in valid_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Async fetch error: {result}")
            elif result:
                valid_results.append(result)

        logger.info(f"Successfully fetched {len(valid_results)}/{len(valid_urls)} URLs")
        return valid_results

    async def _fetch_url_async(self, session: 'aiohttp.ClientSession', url: str) -> Optional[Dict[str, any]]:
        """
        Fetch a single URL asynchronously.

        Args:
            session: aiohttp client session
            url: URL to fetch

        Returns:
            Content dictionary or None if failed
        """
        # Check cache first
        cached = self._get_cached(url)
        if cached:
            return cached

        try:
            logger.info(f"Async fetching: {url}")

            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    "url": url,
                    "title": "Invalid URL",
                    "content": "",
                    "type": "error",
                    "error": "Invalid URL format"
                }

            async with session.get(url, allow_redirects=True) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '').lower()

                # Handle different content types
                result = None
                if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                    content_bytes = await response.read()
                    result = self._extract_pdf_content(url, content_bytes)
                elif 'text/html' in content_type or 'text' in content_type:
                    html_content = await response.text()
                    result = self._extract_html_content(url, html_content)
                else:
                    try:
                        text_content = await response.text()
                        result = {
                            "url": url,
                            "title": self._extract_title_from_url(url),
                            "content": text_content[:self.max_content_length],
                            "type": "text",
                            "error": None
                        }
                    except:
                        result = {
                            "url": url,
                            "title": self._extract_title_from_url(url),
                            "content": "",
                            "type": "error",
                            "error": "Unsupported content type"
                        }

                # Cache successful results
                if result and not result.get("error"):
                    self._set_cached(url, result)

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching URL: {url}")
            return {
                "url": url,
                "title": "Timeout",
                "content": "",
                "type": "error",
                "error": "Request timeout"
            }
        except aiohttp.ClientError as e:
            logger.error(f"Client error fetching URL {url}: {str(e)}")
            return {
                "url": url,
                "title": "Error",
                "content": "",
                "type": "error",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching URL {url}: {str(e)}", exc_info=True)
            return {
                "url": url,
                "title": "Error",
                "content": "",
                "type": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def get_knowledge_summary(self, knowledge_sources: List[Dict[str, any]]) -> str:
        """
        Create a summary of knowledge sources for LLM prompts.

        Args:
            knowledge_sources: List of knowledge source dictionaries

        Returns:
            Formatted summary string
        """
        if not knowledge_sources:
            return ""

        summary_parts = ["ADDITIONAL KNOWLEDGE SOURCES:"]

        for idx, source in enumerate(knowledge_sources, 1):
            if source.get("error"):
                continue  # Skip failed sources

            url = source.get("url", "")
            title = source.get("title", "Untitled")
            content = source.get("content", "")

            if content:
                # Truncate content if too long
                content_preview = content[:2000] + "..." if len(content) > 2000 else content
                summary_parts.append(f"\n[{idx}] {title} ({url})")
                summary_parts.append(f"Content: {content_preview}")

        return "\n".join(summary_parts)

    def find_relevant_excerpts(
        self,
        knowledge_sources: List[Dict[str, any]],
        search_text: str,
        max_excerpts_per_source: int = 3,
        excerpt_length: int = 500
    ) -> List[Dict[str, any]]:
        """
        Find relevant excerpts from knowledge sources based on search text.

        Uses semantic similarity to find the most relevant sections of each
        knowledge source related to the search text (e.g., a transcript chunk).

        Args:
            knowledge_sources: List of knowledge source dictionaries
            search_text: Text to search for (e.g., transcript chunk)
            max_excerpts_per_source: Maximum excerpts to extract per source
            excerpt_length: Length of each excerpt in characters

        Returns:
            List of relevant excerpts with metadata
        """
        try:
            from sentence_transformers import SentenceTransformer, util
            has_semantic = True
            # Reduce sentence_transformers verbosity
            import logging as log
            log.getLogger('sentence_transformers').setLevel(log.WARNING)
        except ImportError:
            logger.warning("sentence-transformers not available, using keyword matching only")
            has_semantic = False

        relevant_excerpts = []

        # Load model if available
        if has_semantic:
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                search_embedding = model.encode(search_text, convert_to_tensor=True, show_progress_bar=False)
            except Exception as e:
                logger.error(f"Failed to load semantic model: {e}")
                has_semantic = False

        for source in knowledge_sources:
            if source.get("error"):
                continue

            content = source.get("content", "")
            if not content:
                continue

            url = source.get("url", "")
            title = source.get("title", "Untitled")

            # Split content into chunks
            chunks = self._split_into_chunks(content, chunk_size=excerpt_length)

            if has_semantic:
                # Score chunks using semantic similarity
                chunk_scores = []
                for chunk in chunks:
                    try:
                        chunk_embedding = model.encode(chunk, convert_to_tensor=True, show_progress_bar=False)
                        similarity = float(util.cos_sim(search_embedding, chunk_embedding))
                        chunk_scores.append((chunk, similarity))
                    except:
                        chunk_scores.append((chunk, 0.0))

                # Sort by similarity
                chunk_scores.sort(key=lambda x: x[1], reverse=True)
                top_chunks = chunk_scores[:max_excerpts_per_source]
            else:
                # Fallback: keyword matching
                search_keywords = set(search_text.lower().split())
                chunk_scores = []
                for chunk in chunks:
                    chunk_words = set(chunk.lower().split())
                    overlap = len(search_keywords & chunk_words) / max(len(search_keywords), 1)
                    chunk_scores.append((chunk, overlap))

                chunk_scores.sort(key=lambda x: x[1], reverse=True)
                top_chunks = chunk_scores[:max_excerpts_per_source]

            # Add relevant excerpts
            for chunk, score in top_chunks:
                if score > 0.1:  # Minimum relevance threshold
                    relevant_excerpts.append({
                        "source_url": url,
                        "source_title": title,
                        "excerpt": chunk,
                        "relevance_score": score
                    })

        # Sort all excerpts by relevance
        relevant_excerpts.sort(key=lambda x: x["relevance_score"], reverse=True)

        return relevant_excerpts

    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into overlapping chunks for better context.

        Args:
            text: Text to split
            chunk_size: Size of each chunk in characters

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Keep last 20% of words for overlap
                    overlap_size = max(1, len(current_chunk) // 5)
                    current_chunk = current_chunk[-overlap_size:]
                    current_length = sum(len(w) + 1 for w in current_chunk)
            current_chunk.append(word)
            current_length += word_length

        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

