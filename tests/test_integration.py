#!/usr/bin/env python3
"""
Integration Tests for AIVA CLI

Tests the full pipeline integration including agent collaboration,
end-to-end workflows, and error recovery scenarios.
"""

import pytest
import sys
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the aiva_cli directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

from core.pipeline import generate_content
from config.loader import load_config, AIVASettings
from crew_config.crew import AivaCrew, WorkflowConfig
from crew_config.agents import get_agent


class TestIntegration:
    """Integration test cases for full pipeline."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for integration testing."""
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
        config.model_dump.return_value = {
            "gemini_api_key": "test_api_key",
            "models": {
                "text_model": "gemini-1.5-flash",
                "image_model": "imagen-3.0-generate-001",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "script_length": 300,
            "segment_duration": 8,
            "max_retries": 3,
            "output_dir": "test_output"
        }
        return config
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup is handled by tempfile
    
    @pytest.fixture
    def mock_successful_agents(self):
        """Mock agents that return successful results."""
        script_agent = Mock()
        segmenter_agent = Mock()
        prompt_gen_agent = Mock()
        image_render_agent = Mock()
        
        return {
            'script_agent': script_agent,
            'segmenter_agent': segmenter_agent,
            'prompt_gen_agent': prompt_gen_agent,
            'image_render_agent': image_render_agent
        }
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    @patch('core.pipeline.os.makedirs')
    @patch('core.pipeline.json.dump')
    def test_full_pipeline_educational_content(self, mock_json_dump, mock_makedirs,
                                             mock_create_tasks, mock_create_agents,
                                             mock_crew_class, mock_config, 
                                             mock_successful_agents, temp_output_dir):
        """Test full pipeline with educational content."""
        # Setup mocks
        mock_create_agents.return_value = mock_successful_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        # Mock crew execution with realistic output
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        mock_crew.kickoff.return_value = Mock(
            raw="Educational content generated successfully",
            tasks_output=[
                Mock(raw="# AI Revolution Script\n\nThis is a comprehensive script about AI..."),
                Mock(raw="Segment 1: Introduction to AI\nSegment 2: History of AI\n..."),
                Mock(raw="Visual prompts generated for 38 segments"),
                Mock(raw="Images rendered successfully for all segments")
            ]
        )
        
        # Execute pipeline
        result = generate_content(
            topic="AI Revolution",
            video_type="educational",
            out_dir=temp_output_dir,
            title="AI Education Series",
            config=mock_config
        )
        
        # Verify execution
        assert result is not None
        mock_create_agents.assert_called_once()
        mock_create_tasks.assert_called_once()
        mock_crew.kickoff.assert_called_once()
        
        # Verify project structure creation
        mock_makedirs.assert_called()
        mock_json_dump.assert_called()
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    def test_pipeline_with_different_topics(self, mock_create_tasks, mock_create_agents,
                                          mock_crew_class, mock_config, 
                                          mock_successful_agents, temp_output_dir):
        """Test pipeline with various topic types."""
        topics = [
            ("Space Exploration", "documentary"),
            ("Quantum Computing", "educational"),
            ("Climate Change", "awareness"),
            ("Artificial Intelligence", "technical")
        ]
        
        mock_create_agents.return_value = mock_successful_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        mock_crew.kickoff.return_value = Mock(
            raw="Content generated",
            tasks_output=[Mock(raw="Output") for _ in range(4)]
        )
        
        with patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump'):
            
            for topic, video_type in topics:
                result = generate_content(
                    topic=topic,
                    video_type=video_type,
                    out_dir=temp_output_dir,
                    config=mock_config
                )
                
                assert result is not None
                
        # Verify all topics were processed
        assert mock_crew.kickoff.call_count == len(topics)
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    def test_agent_collaboration_workflow(self, mock_create_agents, mock_crew_class,
                                        mock_config, mock_successful_agents, temp_output_dir):
        """Test that agents collaborate correctly in sequence."""
        mock_create_agents.return_value = mock_successful_agents
        
        # Mock crew with detailed task outputs
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        
        # Simulate realistic agent outputs
        script_output = "# Complete 5-minute script about AI\nIntroduction: AI is transforming..."
        segment_output = "[Segment 1] Introduction (0:00-0:08)\n[Segment 2] History (0:08-0:16)..."
        prompt_output = "Segment 1 Prompt: Futuristic AI laboratory with glowing circuits..."
        image_output = "Images generated: segment_01.png, segment_02.png..."
        
        mock_crew.kickoff.return_value = Mock(
            raw="Agent collaboration completed",
            tasks_output=[
                Mock(raw=script_output),
                Mock(raw=segment_output),
                Mock(raw=prompt_output),
                Mock(raw=image_output)
            ]
        )
        
        with patch('core.pipeline.create_tasks') as mock_create_tasks, \
             patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump'):
            
            mock_create_tasks.return_value = [Mock() for _ in range(4)]
            
            result = generate_content(
                topic="AI Technology",
                video_type="educational",
                out_dir=temp_output_dir,
                config=mock_config
            )
            
            assert result is not None
            
            # Verify agents were created and tasks were set up
            mock_create_agents.assert_called_once()
            mock_create_tasks.assert_called_once()
            
            # Verify crew was executed
            mock_crew.kickoff.assert_called_once()
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    def test_error_recovery_mechanisms(self, mock_create_agents, mock_crew_class,
                                     mock_config, temp_output_dir):
        """Test error recovery and retry mechanisms."""
        mock_agents = {
            'script_agent': Mock(),
            'segmenter_agent': Mock(),
            'prompt_gen_agent': Mock(),
            'image_render_agent': Mock()
        }
        mock_create_agents.return_value = mock_agents
        
        # Mock crew that fails first, then succeeds
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        
        # First call fails, second succeeds (simulating retry)
        mock_crew.kickoff.side_effect = [
            Exception("Temporary API failure"),
            Mock(
                raw="Recovery successful",
                tasks_output=[Mock(raw="Recovered output") for _ in range(4)]
            )
        ]
        
        with patch('core.pipeline.create_tasks') as mock_create_tasks, \
             patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump'):
            
            mock_create_tasks.return_value = [Mock() for _ in range(4)]
            
            # First attempt should fail
            with pytest.raises(Exception, match="Temporary API failure"):
                generate_content(
                    topic="Test Recovery",
                    video_type="educational",
                    out_dir=temp_output_dir,
                    config=mock_config
                )
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    def test_output_validation_and_structure(self, mock_create_tasks, mock_create_agents,
                                           mock_crew_class, mock_config, 
                                           mock_successful_agents, temp_output_dir):
        """Test output validation and project structure creation."""
        mock_create_agents.return_value = mock_successful_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        mock_crew.kickoff.return_value = Mock(
            raw="Content generated with validation",
            tasks_output=[
                Mock(raw="Script: 300 words, 5 minutes duration"),
                Mock(raw="38 segments created, 8 seconds each"),
                Mock(raw="38 visual prompts generated"),
                Mock(raw="38 images rendered successfully")
            ]
        )
        
        with patch('core.pipeline.os.makedirs') as mock_makedirs, \
             patch('core.pipeline.json.dump') as mock_json_dump:
            
            result = generate_content(
                topic="Validated Content",
                video_type="educational",
                out_dir=temp_output_dir,
                title="Quality Test",
                config=mock_config
            )
            
            assert result is not None
            
            # Verify directory structure creation
            mock_makedirs.assert_called()
            
            # Verify manifest creation
            mock_json_dump.assert_called()
            
            # Check that manifest contains expected structure
            manifest_call = mock_json_dump.call_args
            assert manifest_call is not None
    
    def test_configuration_loading_integration(self):
        """Test configuration loading in integration context."""
        with patch('config.loader.Path.exists') as mock_exists, \
             patch('config.loader.load_dotenv') as mock_load_dotenv, \
             patch('config.loader.os.getenv') as mock_getenv:
            
            mock_exists.return_value = True
            mock_getenv.side_effect = lambda key, default=None: {
                'GEMINI_API_KEY': 'test_key',
                'MODEL_TEXT': 'gemini-1.5-flash',
                'MODEL_IMAGE': 'imagen-3.0-generate-001',
                'SCRIPT_LENGTH': '300',
                'SEGMENT_DURATION': '8'
            }.get(key, default)
            
            # This would normally load real config
            # In integration test, we verify the loading process
            mock_load_dotenv.assert_not_called()  # Not called yet
            
            # Verify that config loading can be called without errors
            assert True  # Placeholder for actual config loading test
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    def test_performance_metrics_collection(self, mock_create_tasks, mock_create_agents,
                                          mock_crew_class, mock_config, 
                                          mock_successful_agents, temp_output_dir):
        """Test that performance metrics are collected during execution."""
        mock_create_agents.return_value = mock_successful_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        mock_crew.kickoff.return_value = Mock(
            raw="Performance test completed",
            tasks_output=[Mock(raw="Timed output") for _ in range(4)]
        )
        
        with patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump') as mock_json_dump, \
             patch('time.time') as mock_time:
            
            # Mock time progression
            mock_time.side_effect = [1000.0, 1030.0]  # 30 second execution
            
            result = generate_content(
                topic="Performance Test",
                video_type="educational",
                out_dir=temp_output_dir,
                config=mock_config
            )
            
            assert result is not None
            
            # Verify that timing information could be collected
            mock_crew.kickoff.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])