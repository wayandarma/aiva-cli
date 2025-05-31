"""Agent Definitions for AIVA CLI System

This module defines specialized agents for the AIVA video generation pipeline.
Each agent has a specific role in the workflow: script processing, segmentation,
prompt generation, and image rendering.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import core components
from ..core.segmenter import ScriptSegmenter, segment_script
from ..core.prompt_enhancer import PromptEnhancer, enhance_prompt, StylePreset
from ..models.text_model import GeminiTextModel
from ..models.image_model import GeminiImageModel


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_name: str
    status: AgentStatus
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent:
    """Base class for all AIVA agents."""
    
    def __init__(self, name: str, role: str, goal: str, backstory: str):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"aiva.agent.{name}")
        self.tools = self._setup_tools()
    
    def _setup_tools(self) -> List[Any]:
        """Setup agent-specific tools. Override in subclasses."""
        return []
    
    def execute(self, input_data: Any, **kwargs) -> AgentResult:
        """Execute agent task. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data. Override in subclasses."""
        return input_data is not None
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "status": self.status.value,
            "tools": self.tools
        }


class ScriptAgent(BaseAgent):
    """Agent responsible for script analysis and preprocessing."""
    
    def __init__(self):
        super().__init__(
            name="ScriptAgent",
            role="Script Analyst and Preprocessor",
            goal="Analyze and preprocess script content for optimal video generation",
            backstory="I am an expert in narrative structure and storytelling. "
                     "I analyze scripts to identify key scenes, dialogue, and "
                     "visual elements that will translate well to video format."
        )
    
    def _setup_tools(self) -> List[Any]:
        """Setup script analysis tools."""
        return [
            "text_analyzer",
            "scene_detector",
            "dialogue_extractor",
            "visual_element_identifier"
        ]
    
    def execute(self, input_data: str, **kwargs) -> AgentResult:
        """Analyze and preprocess script content."""
        try:
            self.status = AgentStatus.RUNNING
            self.logger.info(f"Processing script: {len(input_data)} characters")
            
            if not self.validate_input(input_data):
                raise ValueError("Invalid script input")
            
            # Analyze script structure
            analysis = self._analyze_script(input_data)
            
            # Preprocess for segmentation
            processed_script = self._preprocess_script(input_data, analysis)
            
            self.status = AgentStatus.COMPLETED
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                data={
                    "original_script": input_data,
                    "processed_script": processed_script,
                    "analysis": analysis
                },
                metadata={
                    "character_count": len(input_data),
                    "scene_count": analysis.get("scene_count", 0),
                    "processing_time": kwargs.get("processing_time", 0)
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Script processing failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                error=str(e)
            )
    
    def _analyze_script(self, script: str) -> Dict[str, Any]:
        """Analyze script structure and content."""
        lines = script.split('\n')
        scenes = [line for line in lines if line.strip().startswith(('SCENE', 'INT.', 'EXT.'))]
        
        return {
            "total_lines": len(lines),
            "scene_count": len(scenes),
            "estimated_duration": len(script.split()) * 0.5,  # Rough estimate
            "has_dialogue": ':' in script or '"' in script,
            "scenes": scenes[:5]  # First 5 scenes for preview
        }
    
    def _preprocess_script(self, script: str, analysis: Dict[str, Any]) -> str:
        """Preprocess script for optimal segmentation."""
        # Clean up formatting
        processed = script.strip()
        
        # Normalize line breaks
        processed = processed.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        lines = [line.strip() for line in processed.split('\n')]
        processed = '\n'.join(line for line in lines if line)
        
        return processed
    
    def validate_input(self, input_data: str) -> bool:
        """Validate script input."""
        return isinstance(input_data, str) and len(input_data.strip()) > 0


class SegmenterAgent(BaseAgent):
    """Agent responsible for script segmentation."""
    
    def __init__(self):
        super().__init__(
            name="SegmenterAgent",
            role="Script Segmentation Specialist",
            goal="Divide scripts into optimal segments for video generation",
            backstory="I am a master of pacing and timing in visual storytelling. "
                     "I understand how to break down narratives into digestible "
                     "segments that maintain narrative flow while optimizing for "
                     "video generation constraints."
        )
        self.segmenter = ScriptSegmenter()
    
    def _setup_tools(self) -> List[Any]:
        """Setup segmentation tools."""
        return [
            "script_segmenter",
            "duration_calculator",
            "scene_boundary_detector",
            "segment_optimizer"
        ]
    
    def execute(self, input_data: Dict[str, Any], **kwargs) -> AgentResult:
        """Segment script into optimal chunks."""
        try:
            self.status = AgentStatus.RUNNING
            
            script = input_data.get("processed_script", "")
            target_segments = kwargs.get("target_segments", 10)
            target_duration = kwargs.get("target_duration", 8.0)
            
            self.logger.info(f"Segmenting script into {target_segments} segments")
            
            if not self.validate_input(script):
                raise ValueError("Invalid script input for segmentation")
            
            # Configure segmenter
            self.segmenter.target_segments = target_segments
            self.segmenter.target_duration = target_duration
            
            # Perform segmentation
            segments = self.segmenter.segment_script(script)
            
            self.status = AgentStatus.COMPLETED
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                data={
                    "segments": segments,
                    "segment_count": len(segments),
                    "total_duration": sum(s.duration for s in segments)
                },
                metadata={
                    "target_segments": target_segments,
                    "target_duration": target_duration,
                    "actual_segments": len(segments),
                    "avg_segment_duration": sum(s.duration for s in segments) / len(segments) if segments else 0
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Segmentation failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                error=str(e)
            )
    
    def validate_input(self, input_data: str) -> bool:
        """Validate script input for segmentation."""
        return isinstance(input_data, str) and len(input_data.strip()) > 10


class PromptGenAgent(BaseAgent):
    """Agent responsible for generating enhanced prompts."""
    
    def __init__(self):
        super().__init__(
            name="PromptGenAgent",
            role="Cinematic Prompt Engineer",
            goal="Transform script segments into detailed, cinematic image generation prompts",
            backstory="I am a visionary cinematographer with deep knowledge of "
                     "visual storytelling techniques. I excel at translating "
                     "narrative descriptions into rich, detailed prompts that "
                     "capture the essence of each scene with cinematic quality."
        )
        self.enhancer = PromptEnhancer()
    
    def _setup_tools(self) -> List[Any]:
        """Setup prompt generation tools."""
        return [
            "prompt_enhancer",
            "style_preset_selector",
            "visual_element_extractor",
            "cinematic_composer"
        ]
    
    def execute(self, input_data: Dict[str, Any], **kwargs) -> AgentResult:
        """Generate enhanced prompts from segments."""
        try:
            self.status = AgentStatus.RUNNING
            
            segments = input_data.get("segments", [])
            style_preset = kwargs.get("style_preset", StylePreset.CINEMATIC_4K)
            
            self.logger.info(f"Generating prompts for {len(segments)} segments")
            
            if not self.validate_input(segments):
                raise ValueError("Invalid segments input for prompt generation")
            
            # Generate enhanced prompts
            enhanced_prompts = []
            for i, segment in enumerate(segments):
                try:
                    # Create basic prompt from segment
                    basic_prompt = self._create_basic_prompt(segment)
                    
                    # Enhance with cinematic styling
                    enhanced = self.enhancer.enhance_prompt(basic_prompt, style_preset)
                    
                    enhanced_prompts.append({
                        "segment_index": i + 1,
                        "basic_prompt": basic_prompt,
                        "enhanced_prompt": enhanced,
                        "style_preset": style_preset.value,
                        "segment_duration": segment.duration
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to enhance prompt for segment {i+1}: {e}")
                    enhanced_prompts.append({
                        "segment_index": i + 1,
                        "basic_prompt": segment.text[:100] + "...",
                        "enhanced_prompt": segment.text,
                        "style_preset": "fallback",
                        "segment_duration": segment.duration,
                        "error": str(e)
                    })
            
            self.status = AgentStatus.COMPLETED
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                data={
                    "enhanced_prompts": enhanced_prompts,
                    "prompt_count": len(enhanced_prompts),
                    "style_preset": style_preset.value
                },
                metadata={
                    "total_segments": len(segments),
                    "successful_enhancements": len([p for p in enhanced_prompts if "error" not in p]),
                    "failed_enhancements": len([p for p in enhanced_prompts if "error" in p])
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Prompt generation failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                error=str(e)
            )
    
    def _create_basic_prompt(self, segment) -> str:
        """Create basic prompt from segment."""
        # Extract key visual elements from segment text
        text = segment.text.strip()
        
        # Simple prompt creation - can be enhanced with NLP
        if len(text) > 200:
            # Summarize long segments
            sentences = text.split('. ')
            key_sentences = sentences[:2]  # Take first 2 sentences
            basic = '. '.join(key_sentences)
        else:
            basic = text
        
        return f"Scene depicting: {basic}"
    
    def validate_input(self, input_data: List) -> bool:
        """Validate segments input."""
        return isinstance(input_data, list) and len(input_data) > 0


class ImageRenderAgent(BaseAgent):
    """Agent responsible for image generation and rendering."""
    
    def __init__(self):
        super().__init__(
            name="ImageRenderAgent",
            role="AI Image Generation Specialist",
            goal="Generate high-quality images from enhanced prompts using AI models",
            backstory="I am a cutting-edge AI artist with mastery over multiple "
                     "image generation models. I understand the nuances of prompt "
                     "engineering and can produce stunning visuals that bring "
                     "stories to life with photorealistic quality."
        )
        self.image_model = GeminiImageModel()
    
    def _setup_tools(self) -> List[Any]:
        """Setup image generation tools."""
        return [
            "image_generator",
            "quality_enhancer",
            "style_transfer",
            "batch_processor"
        ]
    
    def execute(self, input_data: Dict[str, Any], **kwargs) -> AgentResult:
        """Generate images from enhanced prompts."""
        try:
            self.status = AgentStatus.RUNNING
            
            enhanced_prompts = input_data.get("enhanced_prompts", [])
            output_dir = kwargs.get("output_dir", "./generated_images")
            image_size = kwargs.get("image_size", "1024x1024")
            
            self.logger.info(f"Generating {len(enhanced_prompts)} images")
            
            if not self.validate_input(enhanced_prompts):
                raise ValueError("Invalid prompts input for image generation")
            
            # Generate images
            generated_images = []
            for i, prompt_data in enumerate(enhanced_prompts):
                try:
                    # Extract prompt
                    prompt = prompt_data.get("enhanced_prompt", "")
                    
                    # Generate image using the AI model
                    image_result = self._generate_image(prompt, image_size, i + 1, output_dir)
                    
                    generated_images.append({
                        "segment_index": prompt_data.get("segment_index", i + 1),
                        "prompt": prompt,
                        "image_path": image_result.get("path"),
                        "image_size": image_size,
                        "generation_time": image_result.get("generation_time", 0),
                        "success": True
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to generate image for segment {i+1}: {e}")
                    generated_images.append({
                        "segment_index": prompt_data.get("segment_index", i + 1),
                        "prompt": prompt_data.get("enhanced_prompt", ""),
                        "error": str(e),
                        "success": False
                    })
            
            self.status = AgentStatus.COMPLETED
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                data={
                    "generated_images": generated_images,
                    "image_count": len(generated_images),
                    "output_directory": output_dir
                },
                metadata={
                    "total_prompts": len(enhanced_prompts),
                    "successful_generations": len([img for img in generated_images if img.get("success")]),
                    "failed_generations": len([img for img in generated_images if not img.get("success")]),
                    "image_size": image_size
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Image generation failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                error=str(e)
            )
    
    def _generate_image(self, prompt: str, size: str, index: int, output_dir: str = "./generated_images") -> Dict[str, Any]:
        """Generate image from prompt using the image model."""
        import time
        import os
        from pathlib import Path
        
        start_time = time.time()
        
        try:
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate image using the model
            image_path = os.path.join(output_dir, "image.png")
            
            # Use the image model to generate the image
            result = self.image_model.generate_image(
                prompt=prompt,
                output_path=image_path
            )
            
            generation_time = time.time() - start_time
            
            return {
                "path": image_path,
                "generation_time": generation_time,
                "size": size,
                "format": "PNG",
                "success": True
            }
            
        except Exception as e:
            generation_time = time.time() - start_time
            self.logger.error(f"Image generation failed: {e}")
            return {
                "path": None,
                "generation_time": generation_time,
                "size": size,
                "format": "PNG",
                "success": False,
                "error": str(e)
            }
    
    def validate_input(self, input_data: List) -> bool:
        """Validate prompts input."""
        return isinstance(input_data, list) and len(input_data) > 0


# Agent Registry
AGENT_REGISTRY = {
    "script": ScriptAgent,
    "segmenter": SegmenterAgent,
    "prompt_gen": PromptGenAgent,
    "image_render": ImageRenderAgent
}


def get_agent(agent_type: str) -> BaseAgent:
    """Get agent instance by type."""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return AGENT_REGISTRY[agent_type]()


def list_available_agents() -> List[str]:
    """List all available agent types."""
    return list(AGENT_REGISTRY.keys())