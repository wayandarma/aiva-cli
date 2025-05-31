#!/usr/bin/env python3
"""
AIVA CLI Models Package

Provides abstractions for AI model interactions including text and image generation
using Google's Gemini API with built-in retry logic and error handling.
"""

# Try to import models, but don't fail if dependencies are missing
try:
    from .text_model import GeminiTextModel, generate_text
    _text_model_available = True
except ImportError:
    GeminiTextModel = None
    generate_text = None
    _text_model_available = False

try:
    from .image_model import GeminiImageModel, generate_image
    _image_model_available = True
except ImportError:
    GeminiImageModel = None
    generate_image = None
    _image_model_available = False

__all__ = [
    'GeminiTextModel',
    'GeminiImageModel', 
    'generate_text',
    'generate_image',
    '_text_model_available',
    '_image_model_available'
]