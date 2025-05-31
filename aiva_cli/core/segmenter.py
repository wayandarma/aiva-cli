"""Script Segmenter Module

This module provides functionality to split video scripts into segments of approximately
8 seconds each, targeting 38 total segments for a 5-minute video.
"""

import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Segment:
    """Represents a single script segment."""
    index: int
    text: str
    duration: float
    word_count: int
    start_time: float
    end_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary format."""
        return {
            "index": self.index,
            "text": self.text,
            "duration": self.duration,
            "word_count": self.word_count,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class ScriptSegmenter:
    """Handles script segmentation into timed segments."""
    
    def __init__(self, target_segments: int = 38, target_duration: float = 8.0):
        """
        Initialize the segmenter.
        
        Args:
            target_segments: Target number of segments (default: 38)
            target_duration: Target duration per segment in seconds (default: 8.0)
        """
        self.target_segments = target_segments
        self.target_duration = target_duration
        self.total_duration = target_segments * target_duration  # 304 seconds ≈ 5 minutes
        self.logger = logging.getLogger(__name__)
        
        # Average speaking rate: 150-160 words per minute
        # For 8 seconds: ~20-22 words per segment
        self.words_per_second = 2.5  # Conservative estimate
        self.target_words_per_segment = int(target_duration * self.words_per_second)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize the input text."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove stage directions or annotations in brackets/parentheses
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Normalize punctuation spacing
        text = re.sub(r'\s*([.!?])\s*', r'\1 ', text)
        text = re.sub(r'\s*([,;:])\s*', r'\1 ', text)
        
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Split on sentence endings, keeping the punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def estimate_duration(self, text: str) -> float:
        """Estimate speaking duration for given text."""
        word_count = len(text.split())
        return word_count / self.words_per_second
    
    def create_initial_segments(self, text: str) -> List[Segment]:
        """Create initial segments based on sentence boundaries."""
        sentences = self.split_into_sentences(text)
        segments = []
        current_text = ""
        current_duration = 0.0
        start_time = 0.0
        
        for sentence in sentences:
            sentence_duration = self.estimate_duration(sentence)
            
            # If adding this sentence would exceed target duration, create a segment
            if current_text and (current_duration + sentence_duration) > self.target_duration:
                segment = Segment(
                    index=len(segments) + 1,
                    text=current_text.strip(),
                    duration=current_duration,
                    word_count=len(current_text.split()),
                    start_time=start_time,
                    end_time=start_time + current_duration
                )
                segments.append(segment)
                
                # Start new segment
                start_time += current_duration
                current_text = sentence
                current_duration = sentence_duration
            else:
                # Add sentence to current segment
                if current_text:
                    current_text += " " + sentence
                    current_duration += sentence_duration
                else:
                    current_text = sentence
                    current_duration = sentence_duration
        
        # Add final segment if there's remaining text
        if current_text:
            segment = Segment(
                index=len(segments) + 1,
                text=current_text.strip(),
                duration=current_duration,
                word_count=len(current_text.split()),
                start_time=start_time,
                end_time=start_time + current_duration
            )
            segments.append(segment)
        
        return segments
    
    def adjust_to_target_count(self, segments: List[Segment]) -> List[Segment]:
        """Adjust segments to match target count of 38."""
        current_count = len(segments)
        
        if current_count == self.target_segments:
            return segments
        
        elif current_count < self.target_segments:
            # Need to split some segments
            return self._split_segments(segments)
        
        else:
            # Need to merge some segments
            return self._merge_segments(segments)
    
    def _split_segments(self, segments: List[Segment]) -> List[Segment]:
        """Split segments to reach target count."""
        needed_splits = self.target_segments - len(segments)
        
        # Find longest segments to split
        segments_by_duration = sorted(segments, key=lambda s: s.duration, reverse=True)
        
        new_segments = segments.copy()
        
        for i in range(min(needed_splits, len(segments_by_duration))):
            segment_to_split = segments_by_duration[i]
            
            # Find this segment in the new_segments list
            split_index = next(j for j, s in enumerate(new_segments) if s.index == segment_to_split.index)
            
            # Split the segment roughly in half
            words = segment_to_split.text.split()
            mid_point = len(words) // 2
            
            first_half = " ".join(words[:mid_point])
            second_half = " ".join(words[mid_point:])
            
            first_duration = self.estimate_duration(first_half)
            second_duration = self.estimate_duration(second_half)
            
            # Create two new segments
            first_segment = Segment(
                index=segment_to_split.index,
                text=first_half,
                duration=first_duration,
                word_count=len(first_half.split()),
                start_time=segment_to_split.start_time,
                end_time=segment_to_split.start_time + first_duration
            )
            
            second_segment = Segment(
                index=segment_to_split.index + 0.5,  # Temporary index
                text=second_half,
                duration=second_duration,
                word_count=len(second_half.split()),
                start_time=segment_to_split.start_time + first_duration,
                end_time=segment_to_split.end_time
            )
            
            # Replace the original segment with the two new ones
            new_segments[split_index] = first_segment
            new_segments.insert(split_index + 1, second_segment)
        
        # Renumber all segments
        for i, segment in enumerate(new_segments):
            segment.index = i + 1
        
        return new_segments
    
    def _merge_segments(self, segments: List[Segment]) -> List[Segment]:
        """Merge segments to reach target count."""
        excess_segments = len(segments) - self.target_segments
        
        # Find shortest adjacent pairs to merge
        new_segments = segments.copy()
        
        for _ in range(excess_segments):
            if len(new_segments) <= 1:
                break
            
            # Find the pair of adjacent segments with shortest combined duration
            best_merge_index = 0
            best_combined_duration = float('inf')
            
            for i in range(len(new_segments) - 1):
                combined_duration = new_segments[i].duration + new_segments[i + 1].duration
                if combined_duration < best_combined_duration:
                    best_combined_duration = combined_duration
                    best_merge_index = i
            
            # Merge the two segments
            first = new_segments[best_merge_index]
            second = new_segments[best_merge_index + 1]
            
            merged_text = first.text + " " + second.text
            merged_duration = first.duration + second.duration
            
            merged_segment = Segment(
                index=first.index,
                text=merged_text,
                duration=merged_duration,
                word_count=len(merged_text.split()),
                start_time=first.start_time,
                end_time=second.end_time
            )
            
            # Replace the two segments with the merged one
            new_segments[best_merge_index] = merged_segment
            new_segments.pop(best_merge_index + 1)
        
        # Renumber all segments
        for i, segment in enumerate(new_segments):
            segment.index = i + 1
        
        return new_segments
    
    def segment_script(self, script_text: str) -> List[Segment]:
        """
        Main method to segment a script into the target number of segments.
        
        Args:
            script_text: The full script text to segment
            
        Returns:
            List of Segment objects, should be exactly target_segments in length
        """
        self.logger.info(f"Starting script segmentation. Target: {self.target_segments} segments")
        
        # Clean the input text
        cleaned_text = self.clean_text(script_text)
        self.logger.info(f"Cleaned script: {len(cleaned_text)} characters, {len(cleaned_text.split())} words")
        
        # Create initial segments based on natural breaks
        initial_segments = self.create_initial_segments(cleaned_text)
        self.logger.info(f"Created {len(initial_segments)} initial segments")
        
        # Adjust to target count
        final_segments = self.adjust_to_target_count(initial_segments)
        self.logger.info(f"Final segmentation: {len(final_segments)} segments")
        
        # Validate results
        total_duration = sum(s.duration for s in final_segments)
        avg_duration = total_duration / len(final_segments)
        
        self.logger.info(f"Segmentation complete:")
        self.logger.info(f"  - Total segments: {len(final_segments)}")
        self.logger.info(f"  - Total duration: {total_duration:.1f}s")
        self.logger.info(f"  - Average duration: {avg_duration:.1f}s")
        self.logger.info(f"  - Target duration: {self.target_duration}s")
        
        return final_segments
    
    def validate_segments(self, segments: List[Segment]) -> Dict[str, Any]:
        """Validate the segmentation results."""
        if not segments:
            return {"valid": False, "error": "No segments provided"}
        
        issues = []
        
        # Check segment count
        if len(segments) != self.target_segments:
            issues.append(f"Expected {self.target_segments} segments, got {len(segments)}")
        
        # Check for empty segments
        empty_segments = [s.index for s in segments if not s.text.strip()]
        if empty_segments:
            issues.append(f"Empty segments found: {empty_segments}")
        
        # Check duration distribution
        durations = [s.duration for s in segments]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        if max_duration > self.target_duration * 1.5:
            issues.append(f"Some segments too long (max: {max_duration:.1f}s)")
        
        if min_duration < self.target_duration * 0.3:
            issues.append(f"Some segments too short (min: {min_duration:.1f}s)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": {
                "count": len(segments),
                "avg_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "total_duration": sum(durations)
            }
        }


def segment_script(script_text: str, target_segments: int = 38, target_duration: float = 8.0) -> List[Segment]:
    """
    Convenience function to segment a script.
    
    Args:
        script_text: The script text to segment
        target_segments: Number of segments to create (default: 38)
        target_duration: Target duration per segment in seconds (default: 8.0)
        
    Returns:
        List of Segment objects
    """
    segmenter = ScriptSegmenter(target_segments, target_duration)
    return segmenter.segment_script(script_text)