"""AIVA CLI Core Business Logic Module

This module contains the core business logic components for content generation:
- Script segmentation into timed segments
- Prompt enhancement for visual generation
- Output management and project structure
"""

from core.segmenter import ScriptSegmenter, Segment, segment_script
from core.prompt_enhancer import PromptEnhancer, StylePreset, enhance_prompt, enhance_prompts_batch
from core.output_manager import OutputManager, ProjectMetadata, SegmentOutput, create_project, load_project

__all__ = [
    # Segmenter
    'ScriptSegmenter',
    'Segment', 
    'segment_script',
    
    # Prompt Enhancer
    'PromptEnhancer',
    'StylePreset',
    'enhance_prompt',
    'enhance_prompts_batch',
    
    # Output Manager
    'OutputManager',
    'ProjectMetadata',
    'SegmentOutput',
    'create_project',
    'load_project'
]

# Version info
__version__ = '1.0.0'
__author__ = 'AIVA CLI Team'
__description__ = 'Core business logic for AI-powered content generation'