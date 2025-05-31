"""Prompt Enhancer Module

This module provides functionality to enhance basic textual scene descriptions
into rich, cinematic image generation prompts with various styling presets.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass


class StylePreset(Enum):
    """Available styling presets for prompt enhancement."""
    CINEMATIC_4K = "cinematic_4k"
    GOLDEN_HOUR = "golden_hour"
    DRAMATIC_LIGHTING = "dramatic_lighting"
    POV_PERSPECTIVE = "pov_perspective"
    DOCUMENTARY = "documentary"
    ARTISTIC = "artistic"
    REALISTIC = "realistic"
    VINTAGE = "vintage"


@dataclass
class EnhancementConfig:
    """Configuration for prompt enhancement."""
    style_preset: StylePreset
    quality_level: str = "ultra-high"
    aspect_ratio: str = "16:9"
    color_grading: Optional[str] = None
    camera_angle: Optional[str] = None
    lighting_style: Optional[str] = None
    mood: Optional[str] = None
    additional_tags: List[str] = None
    
    def __post_init__(self):
        if self.additional_tags is None:
            self.additional_tags = []


class PromptEnhancer:
    """Handles enhancement of basic scene descriptions into detailed image prompts."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_style_templates()
    
    def _setup_style_templates(self):
        """Initialize style templates for different presets."""
        self.style_templates = {
            StylePreset.CINEMATIC_4K: {
                "prefix": "Ultra-realistic cinematic shot",
                "quality": "4K resolution, professional cinematography",
                "lighting": "dramatic lighting, depth of field",
                "style": "film grain, color graded, cinematic composition",
                "camera": "shot with RED camera, shallow depth of field",
                "mood": "cinematic atmosphere"
            },
            StylePreset.GOLDEN_HOUR: {
                "prefix": "Beautiful golden hour scene",
                "quality": "high resolution, professional photography",
                "lighting": "warm golden hour lighting, soft shadows",
                "style": "warm color palette, glowing light",
                "camera": "perfect exposure, bokeh background",
                "mood": "serene and warm atmosphere"
            },
            StylePreset.DRAMATIC_LIGHTING: {
                "prefix": "Dramatically lit scene",
                "quality": "high contrast, professional lighting",
                "lighting": "dramatic chiaroscuro lighting, strong shadows",
                "style": "high contrast, moody atmosphere",
                "camera": "professional photography, sharp focus",
                "mood": "intense and dramatic mood"
            },
            StylePreset.POV_PERSPECTIVE: {
                "prefix": "First-person perspective view",
                "quality": "immersive POV shot, realistic perspective",
                "lighting": "natural lighting, realistic shadows",
                "style": "POV camera angle, immersive experience",
                "camera": "first-person viewpoint, wide angle lens",
                "mood": "immersive and engaging"
            },
            StylePreset.DOCUMENTARY: {
                "prefix": "Documentary-style photograph",
                "quality": "photojournalistic quality, authentic",
                "lighting": "natural lighting, realistic exposure",
                "style": "documentary photography, candid moment",
                "camera": "handheld camera feel, natural framing",
                "mood": "authentic and real"
            },
            StylePreset.ARTISTIC: {
                "prefix": "Artistic interpretation",
                "quality": "fine art quality, creative composition",
                "lighting": "artistic lighting, creative shadows",
                "style": "artistic style, creative interpretation",
                "camera": "artistic framing, unique perspective",
                "mood": "creative and inspiring"
            },
            StylePreset.REALISTIC: {
                "prefix": "Photorealistic scene",
                "quality": "ultra-realistic, lifelike detail",
                "lighting": "natural realistic lighting",
                "style": "photorealistic rendering, true-to-life",
                "camera": "realistic camera settings, natural perspective",
                "mood": "authentic and believable"
            },
            StylePreset.VINTAGE: {
                "prefix": "Vintage-style photograph",
                "quality": "vintage film quality, nostalgic feel",
                "lighting": "soft vintage lighting, film grain",
                "style": "retro color grading, vintage aesthetic",
                "camera": "vintage camera feel, classic composition",
                "mood": "nostalgic and timeless"
            }
        }
    
    def clean_description(self, description: str) -> str:
        """Clean and normalize the input description."""
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description.strip())
        
        # Remove any existing prompt enhancement keywords to avoid duplication
        enhancement_keywords = [
            'ultra-realistic', 'cinematic', '4k', 'professional', 'dramatic',
            'high resolution', 'depth of field', 'bokeh', 'film grain'
        ]
        
        for keyword in enhancement_keywords:
            description = re.sub(rf'\b{re.escape(keyword)}\b', '', description, flags=re.IGNORECASE)
        
        # Clean up any double spaces
        description = re.sub(r'\s+', ' ', description.strip())
        
        return description
    
    def extract_key_elements(self, description: str) -> Dict[str, List[str]]:
        """Extract key visual elements from the description."""
        elements = {
            'subjects': [],
            'objects': [],
            'locations': [],
            'actions': [],
            'colors': [],
            'emotions': []
        }
        
        # Simple keyword extraction (can be enhanced with NLP)
        color_words = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'golden', 'silver', 'purple', 'orange']
        emotion_words = ['happy', 'sad', 'angry', 'peaceful', 'excited', 'calm', 'intense', 'serene']
        location_words = ['room', 'street', 'forest', 'beach', 'mountain', 'city', 'office', 'home', 'park']
        
        words = description.lower().split()
        
        for word in words:
            if word in color_words:
                elements['colors'].append(word)
            elif word in emotion_words:
                elements['emotions'].append(word)
            elif word in location_words:
                elements['locations'].append(word)
        
        return elements
    
    def build_enhanced_prompt(self, description: str, config: EnhancementConfig) -> str:
        """Build an enhanced prompt from description and configuration."""
        template = self.style_templates[config.style_preset]
        
        # Start with the style prefix
        prompt_parts = [template["prefix"]]
        
        # Add the cleaned description
        cleaned_desc = self.clean_description(description)
        prompt_parts.append(f"of {cleaned_desc}")
        
        # Add quality specifications
        prompt_parts.append(template["quality"])
        
        # Add lighting
        if config.lighting_style:
            prompt_parts.append(config.lighting_style)
        else:
            prompt_parts.append(template["lighting"])
        
        # Add camera specifications
        if config.camera_angle:
            prompt_parts.append(config.camera_angle)
        else:
            prompt_parts.append(template["camera"])
        
        # Add style elements
        prompt_parts.append(template["style"])
        
        # Add mood
        if config.mood:
            prompt_parts.append(config.mood)
        else:
            prompt_parts.append(template["mood"])
        
        # Add aspect ratio if specified
        if config.aspect_ratio:
            prompt_parts.append(f"aspect ratio {config.aspect_ratio}")
        
        # Add color grading if specified
        if config.color_grading:
            prompt_parts.append(config.color_grading)
        
        # Add additional tags
        if config.additional_tags:
            prompt_parts.extend(config.additional_tags)
        
        # Join all parts with commas
        enhanced_prompt = ", ".join(prompt_parts)
        
        # Clean up the final prompt
        enhanced_prompt = re.sub(r',\s*,', ',', enhanced_prompt)  # Remove double commas
        enhanced_prompt = re.sub(r'\s+', ' ', enhanced_prompt)    # Normalize spaces
        
        return enhanced_prompt.strip()
    
    def enhance_prompt(self, description: str, style_preset: StylePreset = StylePreset.CINEMATIC_4K, 
                      **kwargs) -> str:
        """
        Main method to enhance a basic description into a detailed prompt.
        
        Args:
            description: Basic scene description
            style_preset: Style preset to apply
            **kwargs: Additional configuration options
            
        Returns:
            Enhanced prompt string
        """
        self.logger.debug(f"Enhancing prompt with style: {style_preset.value}")
        
        # Create configuration
        config = EnhancementConfig(
            style_preset=style_preset,
            quality_level=kwargs.get('quality_level', 'ultra-high'),
            aspect_ratio=kwargs.get('aspect_ratio', '16:9'),
            color_grading=kwargs.get('color_grading'),
            camera_angle=kwargs.get('camera_angle'),
            lighting_style=kwargs.get('lighting_style'),
            mood=kwargs.get('mood'),
            additional_tags=kwargs.get('additional_tags', [])
        )
        
        # Build enhanced prompt
        enhanced = self.build_enhanced_prompt(description, config)
        
        self.logger.debug(f"Original: {description}")
        self.logger.debug(f"Enhanced: {enhanced}")
        
        return enhanced
    
    def enhance_batch(self, descriptions: List[str], style_preset: StylePreset = StylePreset.CINEMATIC_4K,
                     **kwargs) -> List[str]:
        """
        Enhance multiple descriptions at once.
        
        Args:
            descriptions: List of basic scene descriptions
            style_preset: Style preset to apply to all
            **kwargs: Additional configuration options
            
        Returns:
            List of enhanced prompts
        """
        self.logger.info(f"Enhancing {len(descriptions)} prompts with style: {style_preset.value}")
        
        enhanced_prompts = []
        for i, desc in enumerate(descriptions):
            try:
                enhanced = self.enhance_prompt(desc, style_preset, **kwargs)
                enhanced_prompts.append(enhanced)
            except Exception as e:
                self.logger.error(f"Failed to enhance prompt {i+1}: {e}")
                # Fallback to original description
                enhanced_prompts.append(desc)
        
        return enhanced_prompts
    
    def get_preset_info(self, preset: StylePreset) -> Dict[str, str]:
        """Get information about a specific style preset."""
        if preset in self.style_templates:
            return self.style_templates[preset].copy()
        return {}
    
    def list_available_presets(self) -> List[str]:
        """List all available style presets."""
        return [preset.value for preset in StylePreset]
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """Validate an enhanced prompt for quality and completeness."""
        issues = []
        
        # Check length
        if len(prompt) < 50:
            issues.append("Prompt may be too short for detailed generation")
        elif len(prompt) > 500:
            issues.append("Prompt may be too long and could be truncated")
        
        # Check for essential elements
        essential_keywords = ['lighting', 'quality', 'resolution', 'style']
        missing_keywords = []
        
        for keyword in essential_keywords:
            if keyword.lower() not in prompt.lower():
                missing_keywords.append(keyword)
        
        if missing_keywords:
            issues.append(f"Missing essential elements: {', '.join(missing_keywords)}")
        
        # Check for redundancy
        words = prompt.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        repeated_words = [word for word, count in word_counts.items() if count > 2 and len(word) > 3]
        if repeated_words:
            issues.append(f"Repeated words detected: {', '.join(repeated_words[:3])}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": {
                "length": len(prompt),
                "word_count": len(words),
                "unique_words": len(set(words))
            }
        }


# Convenience functions
def enhance_prompt(description: str, style: str = "cinematic_4k", **kwargs) -> str:
    """
    Convenience function to enhance a single prompt.
    
    Args:
        description: Basic scene description
        style: Style preset name (default: "cinematic_4k")
        **kwargs: Additional configuration options
        
    Returns:
        Enhanced prompt string
    """
    enhancer = PromptEnhancer()
    
    # Convert string style to enum
    try:
        style_preset = StylePreset(style)
    except ValueError:
        style_preset = StylePreset.CINEMATIC_4K
    
    return enhancer.enhance_prompt(description, style_preset, **kwargs)


def enhance_prompts_batch(descriptions: List[str], style: str = "cinematic_4k", **kwargs) -> List[str]:
    """
    Convenience function to enhance multiple prompts.
    
    Args:
        descriptions: List of basic scene descriptions
        style: Style preset name (default: "cinematic_4k")
        **kwargs: Additional configuration options
        
    Returns:
        List of enhanced prompts
    """
    enhancer = PromptEnhancer()
    
    # Convert string style to enum
    try:
        style_preset = StylePreset(style)
    except ValueError:
        style_preset = StylePreset.CINEMATIC_4K
    
    return enhancer.enhance_batch(descriptions, style_preset, **kwargs)


# Preset-specific convenience functions
def enhance_cinematic_4k(description: str, **kwargs) -> str:
    """Enhance with cinematic 4K style."""
    return enhance_prompt(description, "cinematic_4k", **kwargs)


def enhance_golden_hour(description: str, **kwargs) -> str:
    """Enhance with golden hour style."""
    return enhance_prompt(description, "golden_hour", **kwargs)


def enhance_dramatic_lighting(description: str, **kwargs) -> str:
    """Enhance with dramatic lighting style."""
    return enhance_prompt(description, "dramatic_lighting", **kwargs)


def enhance_pov_perspective(description: str, **kwargs) -> str:
    """Enhance with POV perspective style."""
    return enhance_prompt(description, "pov_perspective", **kwargs)