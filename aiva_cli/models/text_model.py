#!/usr/bin/env python3
"""
Gemini Text Model Wrapper

Provides a clean interface for text generation using Google's Gemini Pro model
with built-in retry logic, error handling, and rate limiting support.
"""

import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package is required. Install with: pip install google-generativeai"
    )

from config.loader import load_config, get_gemini_api_key
from logs.logger import get_logger


class GeminiTextModel:
    """Wrapper for Gemini Pro text generation model."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize the Gemini text model.
        
        Args:
            api_key: Optional API key. If not provided, loads from config.
            model_name: Optional model name. If not provided, loads from config.
        """
        self.logger = get_logger("aiva.models.text")
        
        # Load configuration
        config = load_config()
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = model_name or config.models.text_model
        self.max_retries = config.max_retries
        self.temperature = config.models.temperature
        self.max_tokens = config.models.max_tokens
        self.timeout = config.models.timeout
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info(f"Initialized Gemini text model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the Gemini Pro model with retry logic.
        
        Args:
            prompt: The input prompt for text generation
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text as string
            
        Raises:
            ValueError: If prompt is empty or invalid
            RuntimeError: If generation fails after all retries
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Merge generation parameters
        generation_config = {
            'temperature': kwargs.get('temperature', self.temperature),
            'max_output_tokens': kwargs.get('max_tokens', self.max_tokens),
        }
        
        self.logger.info(
            f"Generating text with prompt length: {len(prompt)}",
            model=self.model_name,
            temperature=generation_config['temperature']
        )
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Generate content
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Check if response is valid
                if not response.text:
                    raise RuntimeError("Empty response from Gemini API")
                
                self.logger.info(
                    f"Successfully generated text on attempt {attempt + 1}",
                    response_length=len(response.text)
                )
                
                return response.text.strip()
                
            except Exception as e:
                last_exception = e
                wait_time = self._calculate_backoff(attempt)
                
                self.logger.warning(
                    f"Text generation attempt {attempt + 1} failed: {e}",
                    wait_time=wait_time,
                    remaining_attempts=self.max_retries - attempt - 1
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    break
        
        # All retries failed
        error_msg = f"Text generation failed after {self.max_retries} attempts. Last error: {last_exception}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = 1.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay
    
    def validate_connection(self) -> bool:
        """
        Validate the API connection by making a simple test request.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            test_response = self.generate_text("Hello")
            return bool(test_response)
        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'max_retries': self.max_retries
        }


# Convenience function for quick text generation
def generate_text(prompt: str, **kwargs) -> str:
    """
    Convenience function for quick text generation.
    
    Args:
        prompt: The input prompt
        **kwargs: Additional parameters
        
    Returns:
        Generated text
    """
    model = GeminiTextModel()
    return model.generate_text(prompt, **kwargs)