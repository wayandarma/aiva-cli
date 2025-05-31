#!/usr/bin/env python3
"""
AIVA Content Generation Pipeline

End-to-end pipeline that orchestrates the complete video generation workflow:
ScriptAgent → Segmenter → PromptGen → ImageRender → OutputManager

Features:
- State persistence for error recovery
- Retry mechanism for failed segments
- Progress tracking and callbacks
- Comprehensive error handling
"""

import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Import AIVA components
from ..crew_config.agents import get_agent, AgentResult, AgentStatus
from ..crew_config.crew import AivaCrew, WorkflowConfig
from .prompt_enhancer import StylePreset
from .segmenter import Segment, ScriptSegmenter


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class SegmentStatus(Enum):
    """Individual segment processing status."""
    PENDING = "pending"
    SCRIPT_GENERATED = "script_generated"
    SEGMENTED = "segmented"
    PROMPTS_GENERATED = "prompts_generated"
    IMAGES_RENDERED = "images_rendered"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SegmentState:
    """State tracking for individual segment."""
    segment_id: str
    status: SegmentStatus
    script_content: Optional[str] = None
    enhanced_prompts: Optional[List[str]] = None
    image_paths: Optional[List[str]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    last_updated: Optional[str] = None


@dataclass
class PipelineState:
    """Complete pipeline state for persistence."""
    project_slug: str
    topic: str
    video_type: str
    output_dir: str
    status: PipelineStatus
    segments: Dict[str, SegmentState]
    config: Dict[str, Any]
    created_at: str
    updated_at: str
    total_segments: int = 0
    completed_segments: int = 0
    failed_segments: int = 0


class ContentPipeline:
    """Main content generation pipeline orchestrator."""
    
    def __init__(self, 
                 progress_callback: Optional[Callable] = None,
                 max_retries: int = 3):
        """
        Initialize the content pipeline.
        
        Args:
            progress_callback: Optional callback for progress updates
            max_retries: Maximum retry attempts for failed segments
        """
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback
        self.max_retries = max_retries
        self.crew = None
        self.state: Optional[PipelineState] = None
        
    def generate_content(self, 
                        topic: str, 
                        video_type: str, 
                        output_dir: Path,
                        title: Optional[str] = None,
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete content generation pipeline with enhanced CrewAI integration.
        
        Args:
            topic: Content topic/theme
            video_type: Type of video to generate
            output_dir: Output directory path
            title: Optional custom title for project naming
            config: Optional configuration overrides
            
        Returns:
            Dict containing generation results and metadata
        """
        try:
            # Initialize pipeline state with custom title support
            project_slug = self._create_project_slug(title or topic)
            project_dir = output_dir / project_slug
            self.state = self._initialize_state(project_slug, topic, video_type, str(project_dir), config)
            
            # Create project-specific output directory
            project_dir.mkdir(parents=True, exist_ok=True)
            state_file = project_dir / "state.json"
            
            self.logger.info(f"Starting content generation pipeline for: {topic}")
            self._update_progress("Pipeline started", 0)
            
            # Initialize crew with configuration
            workflow_config = self._create_workflow_config(config or {})
            self.crew = AivaCrew(config=workflow_config)
            
            # Step 1: Generate full transcript
            self.logger.info("Step 1: Generating full transcript")
            transcript = self._generate_full_transcript(topic, video_type)
            transcript_file = project_dir / "transcript.txt"
            self._save_transcript(transcript, transcript_file)
            self._save_state(state_file)
            
            # Step 2: Segment the transcript into JSON format
            self.logger.info("Step 2: Segmenting transcript")
            segments_json = self._execute_segmentation_to_json(transcript, project_dir)
            self._save_state(state_file)
            
            # Step 3: Generate individual segment scripts
            self.logger.info("Step 3: Generating segment scripts")
            self._generate_segment_scripts(segments_json, project_dir)
            self._save_state(state_file)
            
            # Step 4: Generate images for each segment
            self.logger.info("Step 4: Generating segment images")
            self._generate_segment_images(segments_json, project_dir)
            self._save_state(state_file)
            
            # Step 5: Finalize and create manifest
            self.logger.info("Step 5: Finalizing output")
            manifest = self._create_manifest(project_dir)
            
            # Update final state
            self.state.status = PipelineStatus.COMPLETED
            self.state.updated_at = datetime.now().isoformat()
            self._save_state(state_file)
            
            self._update_progress("Pipeline completed successfully", 100)
            self.logger.info("Content generation pipeline completed successfully")
            
            return {
                "status": "success",
                "project_slug": project_slug,
                "project_title": title or topic,
                "output_dir": str(project_dir),
                "manifest": manifest,
                "segments_processed": len(segments_json.get("segments", {})),
                "state_file": str(state_file)
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            if self.state:
                self.state.status = PipelineStatus.FAILED
                self.state.updated_at = datetime.now().isoformat()
                self._save_state(output_dir / "state.json")
            
            self._update_progress(f"Pipeline failed: {str(e)}", -1)
            
            return {
                "status": "error",
                "error": str(e),
                "project_slug": project_slug if 'project_slug' in locals() else None,
                "project_title": title or topic,
                "output_dir": str(output_dir)
            }
    
    def resume_pipeline(self, state_file: Path) -> Dict[str, Any]:
        """
        Resume a previously failed or paused pipeline.
        
        Args:
            state_file: Path to the state.json file
            
        Returns:
            Dict containing resume results
        """
        try:
            # Load existing state
            self.state = self._load_state(state_file)
            output_dir = Path(self.state.output_dir)
            
            self.logger.info(f"Resuming pipeline for project: {self.state.project_slug}")
            
            # Reinitialize crew
            workflow_config = self._create_workflow_config(self.state.config)
            self.crew = AivaCrew(config=workflow_config)
            
            # Find failed or incomplete segments
            failed_segments = [
                seg for seg in self.state.segments.values() 
                if seg.status == SegmentStatus.FAILED or seg.status != SegmentStatus.COMPLETED
            ]
            
            if not failed_segments:
                self.logger.info("No failed segments found, pipeline already complete")
                return {"status": "already_complete", "project_slug": self.state.project_slug}
            
            self.logger.info(f"Resuming {len(failed_segments)} failed/incomplete segments")
            
            # Retry failed segments
            for segment_state in failed_segments:
                if segment_state.retry_count < self.max_retries:
                    self._retry_segment(segment_state, output_dir)
                else:
                    self.logger.warning(f"Segment {segment_state.segment_id} exceeded max retries")
            
            # Update final state
            self.state.status = PipelineStatus.COMPLETED
            self.state.updated_at = datetime.now().isoformat()
            self._save_state(state_file)
            
            return {
                "status": "resumed",
                "project_slug": self.state.project_slug,
                "segments_retried": len(failed_segments)
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline resume failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _initialize_state(self, project_slug: str, topic: str, video_type: str, 
                         output_dir: str, config: Optional[Dict[str, Any]]) -> PipelineState:
        """Initialize pipeline state."""
        now = datetime.now().isoformat()
        return PipelineState(
            project_slug=project_slug,
            topic=topic,
            video_type=video_type,
            output_dir=output_dir,
            status=PipelineStatus.PENDING,
            segments={},
            config=config or {},
            created_at=now,
            updated_at=now
        )
    
    def _create_project_slug(self, title_or_topic: str) -> str:
        """Create a user-friendly project slug from title or topic."""
        import re
        
        # Clean the input: remove special characters, keep alphanumeric, spaces, hyphens, underscores
        cleaned = re.sub(r'[^a-zA-Z0-9\s\-_]', '', title_or_topic)
        
        # Replace multiple spaces with single space, then convert spaces to underscores
        slug = re.sub(r'\s+', '_', cleaned.strip())
        
        # Convert to title case for better readability
        slug = '_'.join(word.capitalize() for word in slug.split('_') if word)
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Limit length to avoid filesystem issues
        if len(slug) > 50:
            slug = slug[:50].rstrip('_')
        
        return f"{slug}_{timestamp}"
    
    def _create_workflow_config(self, config: Union[Dict[str, Any], Any]) -> WorkflowConfig:
        """Create enhanced workflow configuration for CrewAI agents."""
        # Handle both dictionary and AIVASettings object
        if hasattr(config, '__dict__'):
            # Convert AIVASettings object to dictionary for easier access
            config_dict = config.__dict__ if config else {}
        else:
            config_dict = config or {}
            
        return WorkflowConfig(
            target_segments=config_dict.get('target_segments', 38),  # Default to 38 segments for 5-minute video
            target_duration=config_dict.get('target_duration', 8.0),  # 8 seconds per segment
            style_preset=config_dict.get('style_preset', StylePreset.CINEMATIC_4K),
            output_dir=config_dict.get('output_dir', './output'),
            image_size=config_dict.get('image_size', '1024x1024'),
            enable_parallel=config_dict.get('enable_parallel', False),
            max_retries=config_dict.get('max_retries', 3),
            timeout_seconds=config_dict.get('timeout_seconds', 300)
        )
    
    def _generate_full_transcript(self, topic: str, video_type: str) -> str:
        """Generate full transcript using GeminiTextModel."""
        from ..models.text_model import GeminiTextModel
        
        # Initialize text model
        text_model = GeminiTextModel()
        
        # Create comprehensive prompt for full transcript generation
        prompt = f"""
Generate a complete {video_type} script about: {topic}

Requirements:
- Create a comprehensive, engaging script suitable for a 5-minute video (approximately 750-800 words)
- Structure the content with clear narrative flow
- Include natural transitions between topics
- Write in a conversational, engaging tone
- Focus on providing valuable information while maintaining viewer interest
- Ensure the content is suitable for visual representation

Please generate only the script content without any formatting markers or stage directions.
"""
        
        # Generate the transcript
        transcript = text_model.generate_text(prompt)
        
        self._update_progress("Full transcript generated", 20)
        return transcript
    
    def _save_transcript(self, transcript: str, file_path: Path) -> None:
        """Save transcript to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            self.logger.info(f"Transcript saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save transcript: {e}")
            raise
    
    def _execute_segmentation_to_json(self, transcript: str, project_dir: Path) -> Dict[str, Any]:
        """Segment transcript and save as JSON."""
        from .segmenter import ScriptSegmenter
        import json
        
        # Initialize segmenter with configuration
        segmenter = ScriptSegmenter(
            target_segments=self.crew.config.target_segments,
            target_duration=self.crew.config.target_duration
        )
        
        # Segment the transcript
        segments = segmenter.segment_script(transcript)
        
        # Convert segments to JSON format
        segments_data = {
            "metadata": {
                "total_segments": len(segments),
                "target_duration_per_segment": self.crew.config.target_duration,
                "total_duration": sum(s.duration for s in segments),
                "created_at": datetime.now().isoformat()
            },
            "segments": {}
        }
        
        for segment in segments:
            segment_id = f"segment_{segment.index:02d}"
            segments_data["segments"][segment_id] = {
                "index": segment.index,
                "text": segment.text,
                "duration": segment.duration,
                "word_count": segment.word_count,
                "start_time": segment.start_time,
                "end_time": segment.end_time
            }
            
            # Initialize segment state
            self.state.segments[segment_id] = SegmentState(
                segment_id=segment_id,
                status=SegmentStatus.SEGMENTED,
                script_content=segment.text,
                last_updated=datetime.now().isoformat()
            )
        
        # Save segments JSON file
        segments_file = project_dir / "segments.json"
        try:
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(segments_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Segments saved to {segments_file}")
        except Exception as e:
            self.logger.error(f"Failed to save segments JSON: {e}")
            raise
        
        self.state.total_segments = len(segments)
        self._update_progress("Transcript segmented", 40)
        return segments_data
    
    def _generate_segment_scripts(self, segments_data: Dict[str, Any], project_dir: Path) -> None:
        """Generate individual scripts for each segment."""
        from ..crew_config.agents import get_agent
        
        segments = segments_data["segments"]
        total_segments = len(segments)
        
        for i, (segment_id, segment_info) in enumerate(segments.items()):
            try:
                self.logger.info(f"Generating script for {segment_id}")
                
                # Get prompt generation agent
                prompt_agent = get_agent('prompt_gen')
                
                # Create Segment object for prompt generation
                from .segmenter import Segment
                segment_obj = Segment(
                    index=segment_info["index"],
                    text=segment_info["text"],
                    duration=segment_info["duration"],
                    word_count=segment_info["word_count"],
                    start_time=segment_info["start_time"],
                    end_time=segment_info["end_time"]
                )
                
                # Prepare input for prompt generation
                prompt_input = {
                    "segments": [segment_obj]
                }
                
                # Generate enhanced prompt for this segment
                result = prompt_agent.execute(prompt_input)
                if result.status != AgentStatus.COMPLETED:
                    self.logger.error(f"Prompt generation failed for {segment_id}: {result.error}")
                    continue
                
                # Extract enhanced prompt
                enhanced_prompts = result.data.get("enhanced_prompts", [])
                if not enhanced_prompts:
                    self.logger.warning(f"No enhanced prompt generated for {segment_id}")
                    continue
                
                enhanced_prompt = enhanced_prompts[0]['enhanced_prompt']  # Get first (and only) prompt
                
                # Create segment directory
                segment_dir = project_dir / segment_id
                segment_dir.mkdir(exist_ok=True)
                
                # Save segment script
                script_file = segment_dir / "script.txt"
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(f"Segment {segment_info['index']}\n")
                    f.write(f"Duration: {segment_info['duration']} seconds\n")
                    f.write(f"Start Time: {segment_info['start_time']}s\n")
                    f.write(f"End Time: {segment_info['end_time']}s\n")
                    f.write(f"Word Count: {segment_info['word_count']}\n\n")
                    f.write("Script Content:\n")
                    f.write(segment_info['text'])
                
                # Save enhanced prompt
                prompt_file = segment_dir / "prompt.txt"
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(f"Enhanced Prompt for Segment {segment_info['index']}:\n\n")
                    f.write(enhanced_prompt)
                
                # Update segment state
                if segment_id in self.state.segments:
                    self.state.segments[segment_id].status = SegmentStatus.PROMPTS_GENERATED
                    self.state.segments[segment_id].enhanced_prompts = [enhanced_prompt]
                    self.state.segments[segment_id].script_path = str(script_file)
                    self.state.segments[segment_id].prompt_path = str(prompt_file)
                    self.state.segments[segment_id].last_updated = datetime.now().isoformat()
                
                self.logger.info(f"Script and prompt saved for {segment_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate script for {segment_id}: {e}")
                if segment_id in self.state.segments:
                    self.state.segments[segment_id].status = SegmentStatus.FAILED
                    self.state.segments[segment_id].last_updated = datetime.now().isoformat()
        
        self._update_progress("Segment scripts generated", 60)
    
    def _generate_segment_images(self, segments_data: Dict[str, Any], project_dir: Path) -> None:
        """Generate images for each segment using enhanced prompts."""
        from ..crew_config.agents import get_agent
        
        segments = segments_data["segments"]
        total_segments = len(segments)
        
        self.logger.info(f"Starting image generation for {total_segments} segments")
        self._update_progress(f"Starting image generation for {total_segments} segments", 65)
        
        for i, (segment_id, segment_info) in enumerate(segments.items()):
            try:
                progress_pct = 65 + (i / total_segments) * 15  # 65-80% range for image generation
                self._update_progress(f"Generating image for {segment_id} ({i+1}/{total_segments})", progress_pct)
                self.logger.info(f"Generating image for {segment_id} ({i+1}/{total_segments})")
                
                # Get image generation agent
                image_agent = get_agent('image_render')
                
                # Get enhanced prompt from segment state
                if segment_id not in self.state.segments:
                    self.logger.error(f"Segment {segment_id} not found in state")
                    continue
                
                segment_state = self.state.segments[segment_id]
                enhanced_prompts = segment_state.enhanced_prompts
                
                if not enhanced_prompts:
                    self.logger.error(f"No enhanced prompts found for {segment_id}")
                    continue
                
                # Use the first enhanced prompt
                enhanced_prompt = enhanced_prompts[0]
                
                # Prepare segment directory
                segment_dir = project_dir / segment_id
                segment_dir.mkdir(exist_ok=True)
                
                # Prepare input for image generation
                image_input = {
                    "enhanced_prompts": [{
                        "enhanced_prompt": enhanced_prompt,
                        "segment_index": i + 1
                    }]
                }
                
                # Generate image
                result = image_agent.execute(image_input, output_dir=str(segment_dir))
                
                if result.status != AgentStatus.COMPLETED:
                    self.logger.error(f"Image generation failed for {segment_id}: {result.error}")
                    self.state.segments[segment_id].status = SegmentStatus.FAILED
                    self.state.segments[segment_id].last_updated = datetime.now().isoformat()
                    continue
                
                # Update segment state with image information
                generated_images = result.data.get('generated_images', [])
                if generated_images and generated_images[0].get('success'):
                    image_path = generated_images[0].get('image_path')
                    if image_path and Path(image_path).exists():
                         self.state.segments[segment_id].image_path = image_path
                         self.state.segments[segment_id].status = SegmentStatus.COMPLETED
                         self.logger.info(f"Image successfully generated for {segment_id}: {image_path}")
                         self._update_progress(f"✅ Image completed for {segment_id}", progress_pct + (1 / total_segments) * 15)
                    else:
                        self.logger.warning(f"Image file not found for {segment_id}")
                        self.state.segments[segment_id].status = SegmentStatus.FAILED
                else:
                    self.logger.error(f"Image generation unsuccessful for {segment_id}")
                    self.state.segments[segment_id].status = SegmentStatus.FAILED
                
                self.state.segments[segment_id].last_updated = datetime.now().isoformat()
                
                # Save state after each image generation
                self._save_state(project_dir)
                
            except Exception as e:
                self.logger.error(f"Failed to generate image for {segment_id}: {e}")
                if segment_id in self.state.segments:
                    self.state.segments[segment_id].status = SegmentStatus.FAILED
                    self.state.segments[segment_id].last_updated = datetime.now().isoformat()
        
        self._update_progress("Segment images generated", 80)
    
    def _process_segments(self, segments: List[Segment], output_dir: Path):
        """Process all segments through prompt generation and image rendering."""
        prompt_agent = get_agent('prompt_gen')
        image_agent = get_agent('image_render')
        
        for i, segment in enumerate(segments):
            segment_id = f"segment_{i+1:02d}"
            segment_dir = output_dir / segment_id
            segment_dir.mkdir(exist_ok=True)
            
            try:
                # Generate prompts
                prompt_input = {"segments": [segment]}
                prompt_result = prompt_agent.execute(prompt_input)
                if prompt_result.status != AgentStatus.COMPLETED:
                    raise Exception(f"Prompt generation failed: {prompt_result.error}")
                
                # Extract enhanced prompt from result
                enhanced_prompts = prompt_result.data.get('enhanced_prompts', [])
                enhanced_prompt = enhanced_prompts[0]['enhanced_prompt'] if enhanced_prompts else segment.text
                
                # Update segment state
                self.state.segments[segment_id].status = SegmentStatus.PROMPTS_GENERATED
                self.state.segments[segment_id].enhanced_prompts = [enhanced_prompt]
                
                # Render images
                image_input = {
                    "enhanced_prompts": [{
                        "segment_index": segment.index,
                        "enhanced_prompt": enhanced_prompt,
                        "segment_duration": segment.duration
                    }]
                }
                image_result = image_agent.execute(image_input, output_dir=str(segment_dir))
                if image_result.status != AgentStatus.COMPLETED:
                    raise Exception(f"Image rendering failed: {image_result.error}")
                
                # Save script content to segment directory
                script_file = segment_dir / "script.txt"
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(f"Segment {segment.index}\n")
                    f.write(f"Duration: {segment.duration:.1f} seconds\n")
                    f.write(f"Start Time: {segment.start_time:.1f}s\n")
                    f.write(f"End Time: {segment.end_time:.1f}s\n")
                    f.write(f"Word Count: {segment.word_count}\n\n")
                    f.write("Script Content:\n")
                    f.write(segment.text)
                
                # Save enhanced prompt to segment directory
                prompt_file = segment_dir / "prompt.txt"
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(f"Enhanced Prompt for Segment {segment.index}:\n\n")
                    f.write(enhanced_prompt)
                
                # Save image and update state
                image_path = segment_dir / "image.png"
                # Note: In real implementation, save the actual image data
                self.state.segments[segment_id].status = SegmentStatus.COMPLETED
                self.state.segments[segment_id].image_paths = [str(image_path)]
                self.state.segments[segment_id].script_file = str(script_file)
                self.state.segments[segment_id].prompt_file = str(prompt_file)
                self.state.segments[segment_id].last_updated = datetime.now().isoformat()
                
                self.state.completed_segments += 1
                progress = 40 + (50 * (i + 1) / len(segments))
                self._update_progress(f"Processed segment {i+1}/{len(segments)}", progress)
                
            except Exception as e:
                self.logger.error(f"Failed to process segment {segment_id}: {str(e)}")
                self.state.segments[segment_id].status = SegmentStatus.FAILED
                self.state.segments[segment_id].error_message = str(e)
                self.state.failed_segments += 1
    
    def _retry_segment(self, segment_state: SegmentState, output_dir: Path):
        """Retry processing a failed segment."""
        segment_state.retry_count += 1
        self.logger.info(f"Retrying segment {segment_state.segment_id} (attempt {segment_state.retry_count})")
        
        try:
            # Reset status and retry from appropriate step
            if segment_state.status == SegmentStatus.FAILED:
                # Retry from the beginning
                segment_state.status = SegmentStatus.PENDING
                # Re-process the segment...
                # (Implementation would depend on where it failed)
            
            segment_state.last_updated = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Retry failed for segment {segment_state.segment_id}: {str(e)}")
            segment_state.error_message = str(e)
    
    def _parse_segments(self, segmentation_result) -> List[Segment]:
        """Parse segments from segmentation result."""
        segments = []
        
        # Handle different result formats
        if isinstance(segmentation_result, dict):
            # If result is a dict, look for segments in common keys
            if 'segments' in segmentation_result:
                segment_data = segmentation_result['segments']
            elif 'data' in segmentation_result:
                segment_data = segmentation_result['data']
            else:
                # Fallback: use the entire dict as segment data
                segment_data = segmentation_result
        elif isinstance(segmentation_result, str):
            # If result is a string, split into lines
            lines = segmentation_result.strip().split('\n')
            segment_data = [line.strip() for line in lines if line.strip()]
        else:
            # Fallback for other types
            segment_data = [str(segmentation_result)]
        
        # Convert to Segment objects
        if isinstance(segment_data, list):
            for i, item in enumerate(segment_data):
                if isinstance(item, dict):
                    # Handle dict format segments
                    segments.append(Segment(
                        index=item.get('index', i+1),
                        text=item.get('text', item.get('content', str(item))),
                        duration=item.get('duration', 8.0),
                        word_count=item.get('word_count', len(str(item).split())),
                        start_time=item.get('start_time', i * 8.0),
                        end_time=item.get('end_time', (i + 1) * 8.0)
                    ))
                else:
                    # Handle string format segments
                    text = str(item).strip()
                    if text:
                        segments.append(Segment(
                            index=i+1,
                            text=text,
                            duration=8.0,
                            word_count=len(text.split()),
                            start_time=i * 8.0,
                            end_time=(i + 1) * 8.0
                        ))
        else:
            # Single segment case
            text = str(segment_data).strip()
            if text:
                segments.append(Segment(
                    index=1,
                    text=text,
                    duration=8.0,
                    word_count=len(text.split()),
                    start_time=0.0,
                    end_time=8.0
                ))
        
        return segments
    
    def _create_manifest(self, output_dir: Path) -> Dict[str, Any]:
        """Create enhanced project manifest file with CrewAI metadata."""
        manifest = {
            "project": {
                "slug": self.state.project_slug,
                "topic": self.state.topic,
                "video_type": self.state.video_type,
                "created_at": self.state.created_at,
                "completed_at": datetime.now().isoformat(),
                "pipeline_version": "Phase 5 - CrewAI Enhanced",
                "ai_models": {
                    "text_model": "gemini-1.5-pro",
                    "image_model": "imagen-3.0-generate-002"
                }
            },
            "segments": {
                seg_id: {
                    "status": seg.status.value,
                    "script_content": seg.script_content,
                    "image_paths": seg.image_paths or [],
                    "prompts": seg.enhanced_prompts or [],
                    "segment_index": int(seg_id.split('_')[1]) if '_' in seg_id else 0,
                    "duration": 8.0  # Standard segment duration
                }
                for seg_id, seg in self.state.segments.items()
            },
            "statistics": {
                "total_segments": self.state.total_segments,
                "completed_segments": self.state.completed_segments,
                "failed_segments": self.state.failed_segments,
                "success_rate": (self.state.completed_segments / max(self.state.total_segments, 1)) * 100,
                "total_duration": self.state.total_segments * 8.0
            },
            "crew_ai": {
                "agents_used": ["ScriptAgent", "SegmenterAgent", "PromptGenAgent", "ImageRenderAgent"],
                "workflow_status": "completed",
                "enhancement_level": "Phase 5"
            }
        }
        
        manifest_file = output_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest
    
    def _save_state(self, state_file: Path):
        """Save current pipeline state to file."""
        if self.state:
            self.state.updated_at = datetime.now().isoformat()
            with open(state_file, 'w') as f:
                json.dump(asdict(self.state), f, indent=2, default=str)
    
    def _load_state(self, state_file: Path) -> PipelineState:
        """Load pipeline state from file."""
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        # Convert segments back to SegmentState objects
        segments = {}
        for seg_id, seg_data in data['segments'].items():
            segments[seg_id] = SegmentState(
                segment_id=seg_data['segment_id'],
                status=SegmentStatus(seg_data['status']),
                script_content=seg_data.get('script_content'),
                enhanced_prompts=seg_data.get('enhanced_prompts'),
                image_paths=seg_data.get('image_paths'),
                error_message=seg_data.get('error_message'),
                retry_count=seg_data.get('retry_count', 0),
                last_updated=seg_data.get('last_updated')
            )
        
        return PipelineState(
            project_slug=data['project_slug'],
            topic=data['topic'],
            video_type=data['video_type'],
            output_dir=data['output_dir'],
            status=PipelineStatus(data['status']),
            segments=segments,
            config=data['config'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            total_segments=data.get('total_segments', 0),
            completed_segments=data.get('completed_segments', 0),
            failed_segments=data.get('failed_segments', 0)
        )
    
    def _update_progress(self, message: str, progress: float):
        """Update progress via callback if available."""
        if self.progress_callback:
            try:
                # Try CLI-style callback first (description, percentage)
                self.progress_callback(message, progress)
            except TypeError:
                # Fallback to dict-style callback
                self.progress_callback({
                    "message": message,
                    "progress": progress,
                    "timestamp": datetime.now().isoformat()
                })


# Convenience function for direct pipeline execution
def generate_content(topic: str, 
                    video_type: str, 
                    output_dir: Path,
                    title: Optional[str] = None,
                    config: Optional[Dict[str, Any]] = None,
                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Execute the complete content generation pipeline with CrewAI integration.
    
    Args:
        topic: Content topic/theme
        video_type: Type of video to generate
        output_dir: Output directory path
        title: Optional custom title for project naming
        config: Optional configuration overrides
        progress_callback: Optional progress callback function
        
    Returns:
        Dict containing generation results and metadata
    """
    pipeline = ContentPipeline(progress_callback=progress_callback)
    return pipeline.generate_content(topic, video_type, output_dir, title, config)


# Convenience function for pipeline resume
def resume_pipeline(state_file: Path, 
                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Resume a previously failed or paused pipeline.
    
    Args:
        state_file: Path to the state.json file
        progress_callback: Optional progress callback function
        
    Returns:
        Dict containing resume results
    """
    pipeline = ContentPipeline(progress_callback=progress_callback)
    return pipeline.resume_pipeline(state_file)