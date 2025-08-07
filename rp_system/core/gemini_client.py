"""Gemini API client with retry logic and comprehensive error handling."""

import logging
import time
from typing import Dict, Any, Optional, List
import os
from dataclasses import dataclass
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests


@dataclass
class GeminiResponse:
    """Response from Gemini API with metadata."""
    text: str
    usage: Dict[str, Any]
    finish_reason: str
    safety_ratings: List[Dict[str, Any]]


class GeminiClient:
    """Production-ready Gemini API client with intelligent retry and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set or api_key provided")
        
        self.model_name = model
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        
        # Configure model with safety settings for RP
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        self.logger.info(f"Initialized Gemini client with model {self.model_name}")
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        return delay
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        retryable_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
        )
        
        # Check for specific API errors
        error_str = str(error).lower()
        retryable_messages = [
            "rate limit",
            "quota exceeded", 
            "service unavailable",
            "internal error",
            "timeout",
            "connection error"
        ]
        
        return (
            isinstance(error, retryable_errors) or
            any(msg in error_str for msg in retryable_messages)
        )
    
    def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        **kwargs
    ) -> GeminiResponse:
        """Generate a response from Gemini with retry logic.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            GeminiResponse with text and metadata
            
        Raises:
            Exception: If all retries fail
        """
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        )
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Generating response (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Extract metadata
                usage = {}
                if hasattr(response, 'usage_metadata'):
                    usage = {
                        'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                        'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                        'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
                    }
                
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'STOP') if response.candidates else 'STOP'
                safety_ratings = [rating.__dict__ for rating in getattr(response.candidates[0], 'safety_ratings', [])] if response.candidates else []
                
                result = GeminiResponse(
                    text=response.text,
                    usage=usage,
                    finish_reason=str(finish_reason),
                    safety_ratings=safety_ratings
                )
                
                self.logger.info(f"Generated response: {usage.get('total_tokens', 0)} tokens")
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries and self._is_retryable_error(e):
                    delay = self._exponential_backoff(attempt)
                    self.logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    break
        
        # All retries failed
        self.logger.error(f"All generation attempts failed. Last error: {last_exception}")
        raise last_exception
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            self.logger.warning(f"Token counting failed: {e}")
            # Fallback estimate: ~4 characters per token
            return len(text) // 4
    
    def is_healthy(self) -> bool:
        """Check if the Gemini API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            test_response = self.generate_response("Hello", max_tokens=5)
            return bool(test_response.text)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False