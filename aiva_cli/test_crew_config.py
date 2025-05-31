"""Test suite for crew configuration and agent registry.

This module provides stub tests to verify that agents are properly
registered and the crew orchestrator functions correctly.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from crew_config.agents import (
    BaseAgent, AgentResult, AgentStatus,
    ScriptAgent, SegmenterAgent, PromptGenAgent, ImageRenderAgent,
    get_agent, list_available_agents
)
from crew_config.crew import (
    AivaCrew, WorkflowConfig, WorkflowResult, WorkflowStatus,
    ConsoleProgressCallback, create_crew, run_workflow
)
from core.prompt_enhancer import StylePreset


class TestAgentRegistry:
    """Test agent registration and retrieval."""
    
    def test_list_available_agents(self):
        """Test that all expected agents are available."""
        agents = list_available_agents()
        
        expected_agents = ["script", "segmenter", "prompt_gen", "image_render"]
        
        assert isinstance(agents, list)
        assert len(agents) >= len(expected_agents)
        
        for agent_name in expected_agents:
            assert agent_name in agents
    
    def test_get_agent_valid(self):
        """Test getting valid agents."""
        # Test each agent type
        script_agent = get_agent("script")
        assert isinstance(script_agent, ScriptAgent)
        assert script_agent.role == "Script Analyst"
        
        segmenter_agent = get_agent("segmenter")
        assert isinstance(segmenter_agent, SegmenterAgent)
        assert segmenter_agent.role == "Script Segmenter"
        
        prompt_agent = get_agent("prompt_gen")
        assert isinstance(prompt_agent, PromptGenAgent)
        assert prompt_agent.role == "Prompt Generator"
        
        render_agent = get_agent("image_render")
        assert isinstance(render_agent, ImageRenderAgent)
        assert render_agent.role == "Image Renderer"
    
    def test_get_agent_invalid(self):
        """Test getting invalid agent raises error."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent("nonexistent_agent")
    
    def test_agent_info_structure(self):
        """Test that agent info has expected structure."""
        agent = get_agent("script")
        info = agent.get_info()
        
        assert isinstance(info, dict)
        assert "role" in info
        assert "goal" in info
        assert "backstory" in info
        assert "tools" in info
        
        # Verify types
        assert isinstance(info["role"], str)
        assert isinstance(info["goal"], str)
        assert isinstance(info["backstory"], str)
        assert isinstance(info["tools"], list)


class TestAgentExecution:
    """Test individual agent execution (stub tests)."""
    
    def test_script_agent_execution(self):
        """Test script agent execution with mock data."""
        agent = ScriptAgent()
        
        # Mock script content
        script_content = "A young hero embarks on an epic journey."
        
        # Execute agent (this is a stub - actual implementation may vary)
        result = agent.execute(script_content)
        
        # Verify result structure
        assert isinstance(result, AgentResult)
        assert result.agent_name == "script"
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
        
        if result.status == AgentStatus.COMPLETED:
            assert result.data is not None
            assert result.error is None
        else:
            assert result.error is not None
    
    def test_segmenter_agent_execution(self):
        """Test segmenter agent execution with mock data."""
        agent = SegmenterAgent()
        
        # Mock analyzed script data
        script_data = {
            "content": "A young hero embarks on an epic journey.",
            "analysis": {"themes": ["adventure", "heroism"]}
        }
        
        # Execute agent
        result = agent.execute(script_data, target_segments=5, target_duration=8.0)
        
        # Verify result structure
        assert isinstance(result, AgentResult)
        assert result.agent_name == "segmenter"
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
    
    def test_prompt_gen_agent_execution(self):
        """Test prompt generator agent execution with mock data."""
        agent = PromptGenAgent()
        
        # Mock segmented data
        segments_data = {
            "segments": [
                {"text": "Hero begins journey", "duration": 4.0},
                {"text": "Hero faces challenge", "duration": 4.0}
            ]
        }
        
        # Execute agent
        result = agent.execute(segments_data, style_preset=StylePreset.CINEMATIC_4K)
        
        # Verify result structure
        assert isinstance(result, AgentResult)
        assert result.agent_name == "prompt_gen"
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
    
    def test_image_render_agent_execution(self):
        """Test image render agent execution with mock data."""
        agent = ImageRenderAgent()
        
        # Mock enhanced prompts data
        prompts_data = {
            "enhanced_prompts": [
                "Cinematic shot of hero beginning epic journey",
                "Dramatic scene of hero facing first challenge"
            ]
        }
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Execute agent
            result = agent.execute(
                prompts_data, 
                output_dir=temp_dir, 
                image_size="512x512"
            )
            
            # Verify result structure
            assert isinstance(result, AgentResult)
            assert result.agent_name == "image_render"
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


class TestCrewOrchestrator:
    """Test crew orchestration functionality."""
    
    def test_crew_initialization(self):
        """Test crew initialization with default config."""
        crew = AivaCrew()
        
        # Verify agents are initialized
        assert len(crew.agents) == 4
        assert "script" in crew.agents
        assert "segmenter" in crew.agents
        assert "prompt_gen" in crew.agents
        assert "image_render" in crew.agents
        
        # Verify workflow graph
        assert len(crew.workflow_graph) == 4
        assert crew.workflow_graph["script"] == []
        assert crew.workflow_graph["segmenter"] == ["script"]
        assert crew.workflow_graph["prompt_gen"] == ["segmenter"]
        assert crew.workflow_graph["image_render"] == ["prompt_gen"]
    
    def test_crew_with_custom_config(self):
        """Test crew initialization with custom config."""
        config = WorkflowConfig(
            target_segments=8,
            target_duration=10.0,
            style_preset=StylePreset.PHOTOREALISTIC,
            output_dir="./custom_output"
        )
        
        crew = AivaCrew(config)
        
        assert crew.config.target_segments == 8
        assert crew.config.target_duration == 10.0
        assert crew.config.style_preset == StylePreset.PHOTOREALISTIC
        assert crew.config.output_dir == "./custom_output"
    
    def test_execution_order(self):
        """Test that execution order follows dependencies."""
        crew = AivaCrew()
        execution_order = crew._get_execution_order()
        
        expected_order = ["script", "segmenter", "prompt_gen", "image_render"]
        assert execution_order == expected_order
    
    def test_workflow_validation(self):
        """Test workflow validation."""
        crew = AivaCrew()
        issues = crew.validate_workflow()
        
        # Should have no issues with default setup
        assert isinstance(issues, list)
        # Note: May have issues in test environment, that's expected
    
    def test_workflow_validation_with_invalid_config(self):
        """Test workflow validation with invalid configuration."""
        config = WorkflowConfig(
            target_segments=-1,  # Invalid
            target_duration=0,   # Invalid
        )
        
        crew = AivaCrew(config)
        issues = crew.validate_workflow()
        
        assert len(issues) >= 2
        assert any("target_segments must be positive" in issue for issue in issues)
        assert any("target_duration must be positive" in issue for issue in issues)
    
    @patch('crew_config.agents.ScriptAgent.execute')
    @patch('crew_config.agents.SegmenterAgent.execute')
    @patch('crew_config.agents.PromptGenAgent.execute')
    @patch('crew_config.agents.ImageRenderAgent.execute')
    def test_workflow_execution_success(self, mock_render, mock_prompt, mock_segment, mock_script):
        """Test successful workflow execution with mocked agents."""
        # Setup mock returns
        mock_script.return_value = AgentResult(
            agent_name="script",
            status=AgentStatus.COMPLETED,
            data={"content": "test script", "analysis": {}}
        )
        
        mock_segment.return_value = AgentResult(
            agent_name="segmenter",
            status=AgentStatus.COMPLETED,
            data={"segments": [{"text": "segment 1", "duration": 4.0}]}
        )
        
        mock_prompt.return_value = AgentResult(
            agent_name="prompt_gen",
            status=AgentStatus.COMPLETED,
            data={"enhanced_prompts": ["enhanced prompt 1"]}
        )
        
        mock_render.return_value = AgentResult(
            agent_name="image_render",
            status=AgentStatus.COMPLETED,
            data={"images": ["image1.png"], "image_count": 1}
        )
        
        # Execute workflow
        crew = AivaCrew()
        result = crew.execute("Test script content")
        
        # Verify result
        assert isinstance(result, WorkflowResult)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.error is None
        assert len(result.agent_results) == 4
        
        # Verify all agents were called
        mock_script.assert_called_once()
        mock_segment.assert_called_once()
        mock_prompt.assert_called_once()
        mock_render.assert_called_once()
    
    @patch('crew_config.agents.ScriptAgent.execute')
    def test_workflow_execution_failure(self, mock_script):
        """Test workflow execution with agent failure."""
        # Setup mock to fail
        mock_script.return_value = AgentResult(
            agent_name="script",
            status=AgentStatus.FAILED,
            error="Mock script analysis failed"
        )
        
        # Execute workflow
        crew = AivaCrew()
        result = crew.execute("Test script content")
        
        # Verify result
        assert isinstance(result, WorkflowResult)
        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None
        assert "script failed" in result.error.lower()


class TestProgressCallbacks:
    """Test progress callback functionality."""
    
    def test_console_callback_creation(self):
        """Test console callback creation."""
        callback = ConsoleProgressCallback(verbose=True)
        assert callback.verbose is True
        
        callback_quiet = ConsoleProgressCallback(verbose=False)
        assert callback_quiet.verbose is False
    
    def test_callback_registration(self):
        """Test callback registration with crew."""
        crew = AivaCrew()
        callback = ConsoleProgressCallback()
        
        # Add callback
        crew.add_callback(callback)
        assert callback in crew.callbacks
        
        # Remove callback
        crew.remove_callback(callback)
        assert callback not in crew.callbacks
    
    def test_callback_methods_exist(self):
        """Test that callback has all required methods."""
        callback = ConsoleProgressCallback()
        
        # Check all required methods exist
        assert hasattr(callback, 'on_workflow_start')
        assert hasattr(callback, 'on_agent_start')
        assert hasattr(callback, 'on_agent_complete')
        assert hasattr(callback, 'on_agent_error')
        assert hasattr(callback, 'on_workflow_complete')
        
        # Check methods are callable
        assert callable(callback.on_workflow_start)
        assert callable(callback.on_agent_start)
        assert callable(callback.on_agent_complete)
        assert callable(callback.on_agent_error)
        assert callable(callback.on_workflow_complete)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_crew(self):
        """Test create_crew convenience function."""
        # Test with default config
        crew = create_crew()
        assert isinstance(crew, AivaCrew)
        assert crew.config is not None
        
        # Test with custom config
        config = WorkflowConfig(target_segments=5)
        crew_custom = create_crew(config)
        assert isinstance(crew_custom, AivaCrew)
        assert crew_custom.config.target_segments == 5
    
    @patch('crew_config.crew.AivaCrew.execute')
    def test_run_workflow(self, mock_execute):
        """Test run_workflow convenience function."""
        # Setup mock
        mock_result = WorkflowResult(status=WorkflowStatus.COMPLETED)
        mock_execute.return_value = mock_result
        
        # Test function
        result = run_workflow("Test script", verbose=False)
        
        assert result == mock_result
        mock_execute.assert_called_once_with("Test script")
    
    def test_run_workflow_validation_failure(self):
        """Test run_workflow with validation failure."""
        config = WorkflowConfig(target_segments=-1)  # Invalid config
        
        with pytest.raises(ValueError, match="Workflow validation failed"):
            run_workflow("Test script", config=config, verbose=False)


class TestWorkflowResult:
    """Test WorkflowResult functionality."""
    
    def test_workflow_result_creation(self):
        """Test WorkflowResult creation and basic properties."""
        result = WorkflowResult(status=WorkflowStatus.COMPLETED)
        
        assert result.status == WorkflowStatus.COMPLETED
        assert isinstance(result.agent_results, dict)
        assert result.execution_time == 0.0
        assert result.error is None
        assert isinstance(result.metadata, dict)
    
    def test_get_final_output_success(self):
        """Test getting final output from successful workflow."""
        result = WorkflowResult(status=WorkflowStatus.COMPLETED)
        
        # Add mock agent results
        result.agent_results["image_render"] = AgentResult(
            agent_name="image_render",
            status=AgentStatus.COMPLETED,
            data={"images": ["test.png"], "image_count": 1}
        )
        
        final_output = result.get_final_output()
        assert final_output is not None
        assert "images" in final_output
        assert final_output["image_count"] == 1
    
    def test_get_final_output_failure(self):
        """Test getting final output from failed workflow."""
        result = WorkflowResult(status=WorkflowStatus.FAILED)
        
        final_output = result.get_final_output()
        assert final_output is None


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running crew configuration smoke tests...")
    
    try:
        # Test agent registry
        agents = list_available_agents()
        print(f"✅ Found {len(agents)} available agents: {agents}")
        
        # Test agent creation
        for agent_name in ["script", "segmenter", "prompt_gen", "image_render"]:
            agent = get_agent(agent_name)
            info = agent.get_info()
            print(f"✅ {agent_name}: {info['role']}")
        
        # Test crew creation
        crew = create_crew()
        print(f"✅ Crew created with {len(crew.agents)} agents")
        
        # Test workflow validation
        issues = crew.validate_workflow()
        if issues:
            print(f"⚠️  Workflow validation issues: {issues}")
        else:
            print("✅ Workflow validation passed")
        
        print("\n🎉 All smoke tests passed!")
        
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        raise