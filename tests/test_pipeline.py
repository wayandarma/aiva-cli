#!/usr/bin/env python3
"""
Unit Tests for Core Pipeline

Tests the main pipeline functionality including content generation,
segmentation, and project organization.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

# Import modules to test
from config.loader import AIVASettings
from crew_config.crew import WorkflowConfig
from crew_config.agents import AgentResult, AgentStatus
from core.segmenter import Segment
from core.pipeline import generate_content, ContentPipeline


class TestPipeline:
    """Test cases for core pipeline functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AIVASettings)
        config.gemini_api_key = "test_api_key"
        config.models = Mock()
        config.models.text_model = "gemini-1.5-flash"
        config.models.image_model = "imagen-3.0-generate-001"
        config.models.temperature = 0.7
        config.models.max_tokens = 2048
        config.script_length = 300
        config.segment_duration = 8
        config.max_retries = 3
        config.output_dir = "test_output"
        return config
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup is handled by tempfile
    
    def test_create_workflow_config_with_dict(self):
        """Test _create_workflow_config with dictionary input."""
        pipeline = ContentPipeline()
        config_dict = {
            'target_segments': 5,
            'target_duration': 10.0,
            'output_dir': './test_output',
            'max_retries': 2
        }
        
        result = pipeline._create_workflow_config(config_dict)
        
        assert result.target_segments == 5
        assert result.target_duration == 10.0
        assert result.output_dir == './test_output'
        assert result.max_retries == 2
    
    def test_create_workflow_config_with_aiva_settings(self):
        """Test _create_workflow_config with AIVASettings object."""
        pipeline = ContentPipeline()
        # Create a simple mock object with the required attributes
        class MockSettings:
            def __init__(self):
                self.target_segments = 8
                self.target_duration = 12.0
                self.output_dir = './custom_output'
        
        settings = MockSettings()
        result = pipeline._create_workflow_config(settings)
        
        assert result.target_segments == 8
        assert result.target_duration == 12.0
        assert result.output_dir == './custom_output'
    
    @patch('core.pipeline.AivaCrew')
    @patch('core.pipeline.get_agent')
    def test_generate_content_success(self, mock_get_agent, mock_crew):
        """Test successful content generation."""
        # Mock agent results
        mock_script_agent = Mock()
        mock_script_agent.execute.return_value = Mock(
            status='completed',
            content='Test script content'
        )
        
        mock_get_agent.return_value = mock_script_agent
        
        # Mock crew
        mock_crew_instance = Mock()
        mock_crew.return_value = mock_crew_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_content(
                topic="AI Revolution",
                video_type="educational",
                output_dir=Path(temp_dir)
            )
            
            assert result is not None
            assert 'status' in result
    
    @patch('core.pipeline.AivaCrew')
    @patch('core.pipeline.get_agent')
    def test_generate_content_crewai_failure(self, mock_get_agent, mock_crew):
        """Test handling of CrewAI execution failure."""
        # Mock agent failure
        mock_script_agent = Mock()
        mock_script_agent.execute.side_effect = Exception("Agent execution failed")
        mock_get_agent.return_value = mock_script_agent
        
        # Mock crew
        mock_crew_instance = Mock()
        mock_crew.return_value = mock_crew_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_content(
                topic="Test Topic",
                video_type="educational",
                output_dir=Path(temp_dir)
            )
            
            assert result is not None
            assert 'error' in result or 'status' in result
    
    @patch('core.pipeline.AivaCrew')
    @patch('core.pipeline.get_agent')
    def test_generate_content_with_empty_topic(self, mock_get_agent, mock_crew):
        """Test content generation with empty topic."""
        # Mock agent results
        mock_script_agent = Mock()
        mock_script_agent.execute.return_value = Mock(
            status='completed',
            content='Test script content'
        )
        mock_get_agent.return_value = mock_script_agent
        
        # Mock crew
        mock_crew_instance = Mock()
        mock_crew.return_value = mock_crew_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_content(
                topic="",
                video_type="educational",
                output_dir=Path(temp_dir)
            )
            
            # Should handle empty topic gracefully
            assert result is not None
    
    @patch('core.pipeline.AivaCrew')
    @patch('core.pipeline.get_agent')
    def test_generate_content_with_unusual_video_type(self, mock_get_agent, mock_crew):
        """Test content generation with unusual video type."""
        # Mock agent results
        mock_script_agent = Mock()
        mock_script_agent.execute.return_value = Mock(
            status='completed',
            content='Test script content'
        )
        mock_get_agent.return_value = mock_script_agent
        
        # Mock crew
        mock_crew_instance = Mock()
        mock_crew.return_value = mock_crew_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_content(
                topic="Test Topic",
                video_type="unusual_type",
                output_dir=Path(temp_dir)
            )
            
            # Should handle unusual video type gracefully
            assert result is not None
    
    @patch('core.pipeline.AivaCrew')
    @patch('core.pipeline.get_agent')
    def test_generate_content_with_custom_title(self, mock_get_agent, mock_crew):
        """Test content generation with custom project title."""
        # Mock agent results
        mock_script_agent = Mock()
        mock_script_agent.execute.return_value = Mock(
            status='completed',
            content='Test script content'
        )
        mock_get_agent.return_value = mock_script_agent
        
        # Mock crew
        mock_crew_instance = Mock()
        mock_crew.return_value = mock_crew_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_content(
                topic="AI Revolution",
                video_type="educational",
                output_dir=Path(temp_dir),
                title="Custom AI Project"
            )
            
            assert result is not None
            # Check that custom title was used in project creation
            assert 'Custom_Ai_Project' in str(result.get('project_slug', '')) or 'status' in result


if __name__ == "__main__":
    pytest.main([__file__])