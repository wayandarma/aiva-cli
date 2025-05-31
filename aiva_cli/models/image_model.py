#!/usr/bin/env python3
"""
Gemini Image Model Wrapper

Provides a clean interface for image generation using Google's Imagen 3 model
with built-in retry logic, error handling, and automatic file saving.
"""

import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import base64

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package is required. Install with: pip install google-generativeai"
    )

from ..config.loader import load_config, get_gemini_api_key
from ..logs.logger import get_logger


class GeminiImageModel:
    """Wrapper for Gemini Imagen 3 image generation model."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize the Gemini image model.
        
        Args:
            api_key: Optional API key. If not provided, loads from config.
            model_name: Optional model name. If not provided, loads from config.
        """
        self.logger = get_logger("aiva.models.image")
        
        # Load configuration
        config = load_config()
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = model_name or config.models.image_model
        self.max_retries = config.max_retries
        self.timeout = config.models.timeout
        self.image_format = config.output.image_format
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info(f"Initialized Gemini image model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini image model: {e}")
            raise
    
    def generate_image(self, prompt: str, output_path: Path, **kwargs) -> Path:
        """
        Generate an image using the Gemini Imagen model with retry logic.
        
        Args:
            prompt: The input prompt for image generation
            output_path: Path where the generated image will be saved
            **kwargs: Additional generation parameters
            
        Returns:
            Path to the saved image file
            
        Raises:
            ValueError: If prompt is empty or path is invalid
            RuntimeError: If generation fails after all retries
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Ensure output path is a Path object
        output_path = Path(output_path)
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure the file has the correct extension
        if not output_path.suffix:
            output_path = output_path.with_suffix(f".{self.image_format}")
        
        # Generation parameters
        generation_config = {
            'response_modalities': ['TEXT', 'IMAGE'],
            **kwargs
        }
        
        self.logger.info(
            f"Generating image with prompt length: {len(prompt)}",
            model=self.model_name,
            output_path=str(output_path)
        )
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Generate content with image response
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Extract image data from response
                image_data = None
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        break
                
                if not image_data:
                    raise RuntimeError("No image data found in response")
                
                # Save the image
                self._save_image(image_data, output_path)
                
                self.logger.info(
                    f"Successfully generated and saved image on attempt {attempt + 1}",
                    file_size=output_path.stat().st_size if output_path.exists() else 0
                )
                
                return output_path
                
            except Exception as e:
                last_exception = e
                wait_time = self._calculate_backoff(attempt)
                
                self.logger.warning(
                    f"Image generation attempt {attempt + 1} failed: {e}",
                    wait_time=wait_time,
                    remaining_attempts=self.max_retries - attempt - 1
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    break
        
        # All retries failed
        error_msg = f"Image generation failed after {self.max_retries} attempts. Last error: {last_exception}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _save_image(self, image_data: bytes, output_path: Path) -> None:
        """
        Save image data to file.
        
        Args:
            image_data: Raw image bytes
            output_path: Path to save the image
        """
        try:
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            self.logger.debug(f"Image saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save image to {output_path}: {e}")
            raise
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = 2.0  # Slightly longer for image generation
        max_delay = 120.0  # Longer max delay for image operations
        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay
    
    def validate_connection(self) -> bool:
        """
        Validate the API connection by checking model availability.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list available models to test connection
            models = list(genai.list_models())
            return len(models) > 0
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
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'image_format': self.image_format
        }
    
    def generate_multiple_images(self, prompts: list, output_dir: Path, **kwargs) -> list[Path]:
        """
        Generate multiple images from a list of prompts.
        
        Args:
            prompts: List of prompts for image generation
            output_dir: Directory to save generated images
            **kwargs: Additional generation parameters
            
        Returns:
            List of paths to generated images
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_paths = []
        
        for i, prompt in enumerate(prompts):
            try:
                output_path = output_dir / f"image_{i+1:03d}.{self.image_format}"
                result_path = self.generate_image(prompt, output_path, **kwargs)
                generated_paths.append(result_path)
                
                self.logger.info(f"Generated image {i+1}/{len(prompts)}: {result_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate image {i+1}: {e}")
                # Continue with next image instead of failing completely
                continue
        
        return generated_paths


# Convenience function for quick image generation
def generate_image(prompt: str, output_path: Path, **kwargs) -> Path:
    """
    Convenience function for quick image generation.
    
    Args:
        prompt: The input prompt
        output_path: Path to save the image
        **kwargs: Additional parameters
        
    Returns:
        Path to the generated image
    """
    model = GeminiImageModel()
    return model.generate_image(prompt, output_path, **kwargs)