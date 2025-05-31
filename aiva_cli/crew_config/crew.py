"""Crew Orchestrator for AIVA CLI System

This module provides the main orchestration logic for coordinating agents
in the AIVA video generation pipeline. It manages the sequential workflow,
dependency resolution, progress tracking, and error handling.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .agents import (
    get_agent, AgentResult, AgentStatus,
    AGENT_REGISTRY, list_available_agents, BaseAgent,
    ScriptAgent, SegmenterAgent, PromptGenAgent, ImageRenderAgent
)
from ..core.prompt_enhancer import StylePreset


class WorkflowStatus(Enum):
    """Overall workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""
    target_segments: int = 10
    target_duration: float = 8.0
    style_preset: StylePreset = StylePreset.CINEMATIC_4K
    output_dir: str = "./output"
    image_size: str = "1024x1024"
    enable_parallel: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
    

@dataclass
class WorkflowResult:
    """Result from workflow execution."""
    status: WorkflowStatus
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_final_output(self) -> Optional[Dict[str, Any]]:
        """Get the final output from the last successful agent."""
        if self.status != WorkflowStatus.COMPLETED:
            return None
        
        # Return output from ImageRenderAgent if available
        if "image_render" in self.agent_results:
            result = self.agent_results["image_render"]
            if result.status == AgentStatus.COMPLETED:
                return result.data
        
        # Fallback to last successful agent
        for agent_name in reversed(list(self.agent_results.keys())):
            result = self.agent_results[agent_name]
            if result.status == AgentStatus.COMPLETED:
                return result.data
        
        return None


class ProgressCallback:
    """Base class for progress callbacks."""
    
    def on_workflow_start(self, config: WorkflowConfig):
        """Called when workflow starts."""
        pass
    
    def on_agent_start(self, agent_name: str, agent: BaseAgent):
        """Called when an agent starts execution."""
        pass
    
    def on_agent_complete(self, agent_name: str, result: AgentResult):
        """Called when an agent completes execution."""
        pass
    
    def on_agent_error(self, agent_name: str, error: str):
        """Called when an agent encounters an error."""
        pass
    
    def on_workflow_complete(self, result: WorkflowResult):
        """Called when workflow completes."""
        pass


class ConsoleProgressCallback(ProgressCallback):
    """Console-based progress callback."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = logging.getLogger("aiva.crew.progress")
    
    def on_workflow_start(self, config: WorkflowConfig):
        if self.verbose:
            print(f"🚀 Starting AIVA workflow with {config.target_segments} segments")
            print(f"   Style: {config.style_preset.value}")
            print(f"   Output: {config.output_dir}")
    
    def on_agent_start(self, agent_name: str, agent: BaseAgent):
        if self.verbose:
            print(f"🤖 {agent_name}: {agent.role}")
            print(f"   Goal: {agent.goal}")
    
    def on_agent_complete(self, agent_name: str, result: AgentResult):
        if result.status == AgentStatus.COMPLETED:
            if self.verbose:
                print(f"✅ {agent_name}: Completed successfully")
                if result.metadata:
                    for key, value in result.metadata.items():
                        print(f"   {key}: {value}")
        else:
            print(f"❌ {agent_name}: Failed - {result.error}")
    
    def on_agent_error(self, agent_name: str, error: str):
        print(f"💥 {agent_name}: Error - {error}")
    
    def on_workflow_complete(self, result: WorkflowResult):
        if result.status == WorkflowStatus.COMPLETED:
            print(f"🎉 Workflow completed in {result.execution_time:.2f}s")
            final_output = result.get_final_output()
            if final_output:
                print(f"📊 Generated {final_output.get('image_count', 0)} images")
        else:
            print(f"💔 Workflow failed: {result.error}")


class AivaCrew:
    """Main orchestrator for the AIVA agent workflow."""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        self.logger = logging.getLogger("aiva.crew")
        self.agents = self._initialize_agents()
        self.workflow_graph = self._build_workflow_graph()
        self.callbacks: List[ProgressCallback] = []
        
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all required agents."""
        agents = {}
        
        try:
            agents["script"] = ScriptAgent()
            agents["segmenter"] = SegmenterAgent()
            agents["prompt_gen"] = PromptGenAgent()
            agents["image_render"] = ImageRenderAgent()
            
            self.logger.info(f"Initialized {len(agents)} agents")
            return agents
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def _build_workflow_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph for agent execution order."""
        # Define dependencies: agent -> [required_inputs]
        return {
            "script": [],  # No dependencies
            "segmenter": ["script"],  # Needs script output
            "prompt_gen": ["segmenter"],  # Needs segmentation output
            "image_render": ["prompt_gen"]  # Needs prompt generation output
        }
    
    def add_callback(self, callback: ProgressCallback):
        """Add progress callback."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: ProgressCallback):
        """Remove progress callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_workflow_start(self):
        """Notify callbacks of workflow start."""
        for callback in self.callbacks:
            try:
                callback.on_workflow_start(self.config)
            except Exception as e:
                self.logger.warning(f"Callback error on workflow start: {e}")
    
    def _notify_agent_start(self, agent_name: str, agent: BaseAgent):
        """Notify callbacks of agent start."""
        for callback in self.callbacks:
            try:
                callback.on_agent_start(agent_name, agent)
            except Exception as e:
                self.logger.warning(f"Callback error on agent start: {e}")
    
    def _notify_agent_complete(self, agent_name: str, result: AgentResult):
        """Notify callbacks of agent completion."""
        for callback in self.callbacks:
            try:
                callback.on_agent_complete(agent_name, result)
            except Exception as e:
                self.logger.warning(f"Callback error on agent complete: {e}")
    
    def _notify_agent_error(self, agent_name: str, error: str):
        """Notify callbacks of agent error."""
        for callback in self.callbacks:
            try:
                callback.on_agent_error(agent_name, error)
            except Exception as e:
                self.logger.warning(f"Callback error on agent error: {e}")
    
    def _notify_workflow_complete(self, result: WorkflowResult):
        """Notify callbacks of workflow completion."""
        for callback in self.callbacks:
            try:
                callback.on_workflow_complete(result)
            except Exception as e:
                self.logger.warning(f"Callback error on workflow complete: {e}")
    
    def _get_execution_order(self) -> List[str]:
        """Get agent execution order based on dependencies."""
        # Simple topological sort for our linear pipeline
        return ["script", "segmenter", "prompt_gen", "image_render"]
    
    def _prepare_agent_input(self, agent_name: str, previous_results: Dict[str, AgentResult]) -> Any:
        """Prepare input data for agent based on previous results."""
        dependencies = self.workflow_graph[agent_name]
        
        if not dependencies:
            # No dependencies, agent will receive raw input
            return None
        
        # Get data from the most recent dependency
        latest_dep = dependencies[-1]
        if latest_dep in previous_results:
            result = previous_results[latest_dep]
            if result.status == AgentStatus.COMPLETED:
                return result.data
        
        # If no successful dependency, return None
        return None
    
    def _prepare_agent_kwargs(self, agent_name: str) -> Dict[str, Any]:
        """Prepare keyword arguments for agent execution."""
        kwargs = {}
        
        if agent_name == "segmenter":
            kwargs.update({
                "target_segments": self.config.target_segments,
                "target_duration": self.config.target_duration
            })
        elif agent_name == "prompt_gen":
            kwargs.update({
                "style_preset": self.config.style_preset
            })
        elif agent_name == "image_render":
            kwargs.update({
                "output_dir": self.config.output_dir,
                "image_size": self.config.image_size
            })
        
        return kwargs
    
    def execute(self, script_content: str) -> WorkflowResult:
        """Execute the complete workflow."""
        start_time = time.time()
        
        # Initialize result
        result = WorkflowResult(status=WorkflowStatus.PENDING)
        
        try:
            # Notify workflow start
            result.status = WorkflowStatus.RUNNING
            self._notify_workflow_start()
            
            # Get execution order
            execution_order = self._get_execution_order()
            
            # Track results from each agent
            agent_results = {}
            current_input = script_content
            
            # Execute agents in order
            for agent_name in execution_order:
                try:
                    agent = self.agents[agent_name]
                    
                    # Notify agent start
                    self._notify_agent_start(agent_name, agent)
                    
                    # Prepare input and kwargs
                    if agent_name == "script":
                        agent_input = current_input  # Raw script for first agent
                    else:
                        agent_input = self._prepare_agent_input(agent_name, agent_results)
                    
                    agent_kwargs = self._prepare_agent_kwargs(agent_name)
                    
                    # Execute agent
                    self.logger.info(f"Executing {agent_name} agent")
                    agent_result = agent.execute(agent_input, **agent_kwargs)
                    
                    # Store result
                    agent_results[agent_name] = agent_result
                    
                    # Notify completion
                    self._notify_agent_complete(agent_name, agent_result)
                    
                    # Check if agent failed
                    if agent_result.status == AgentStatus.FAILED:
                        error_msg = f"Agent {agent_name} failed: {agent_result.error}"
                        self.logger.error(error_msg)
                        self._notify_agent_error(agent_name, agent_result.error)
                        
                        # Decide whether to continue or fail
                        if self._should_continue_on_error(agent_name):
                            self.logger.warning(f"Continuing workflow despite {agent_name} failure")
                            continue
                        else:
                            raise Exception(error_msg)
                    
                    # Update current input for next agent
                    current_input = agent_result.data
                    
                except Exception as e:
                    error_msg = f"Error executing {agent_name}: {str(e)}"
                    self.logger.error(error_msg)
                    self._notify_agent_error(agent_name, str(e))
                    
                    # Store failed result
                    agent_results[agent_name] = AgentResult(
                        agent_name=agent_name,
                        status=AgentStatus.FAILED,
                        error=str(e)
                    )
                    
                    # Fail the workflow
                    result.status = WorkflowStatus.FAILED
                    result.error = error_msg
                    result.agent_results = agent_results
                    break
            
            # Check final status
            if result.status == WorkflowStatus.RUNNING:
                # All agents completed successfully
                result.status = WorkflowStatus.COMPLETED
                result.agent_results = agent_results
                
                # Add metadata
                result.metadata = {
                    "total_agents": len(execution_order),
                    "successful_agents": len([r for r in agent_results.values() if r.status == AgentStatus.COMPLETED]),
                    "failed_agents": len([r for r in agent_results.values() if r.status == AgentStatus.FAILED]),
                    "config": {
                        "target_segments": self.config.target_segments,
                        "style_preset": self.config.style_preset.value,
                        "output_dir": self.config.output_dir
                    }
                }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
        
        finally:
            # Calculate execution time
            result.execution_time = time.time() - start_time
            
            # Notify workflow completion
            self._notify_workflow_complete(result)
        
        return result
    
    def _should_continue_on_error(self, agent_name: str) -> bool:
        """Determine if workflow should continue when an agent fails."""
        # For now, fail fast on any agent error
        # Could be made configurable in the future
        return False
    
    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all agents."""
        return {name: agent.get_info() for name, agent in self.agents.items()}
    
    def validate_workflow(self) -> List[str]:
        """Validate workflow configuration and dependencies."""
        issues = []
        
        # Check if all required agents are available
        required_agents = set(self.workflow_graph.keys())
        available_agents = set(self.agents.keys())
        
        missing_agents = required_agents - available_agents
        if missing_agents:
            issues.append(f"Missing agents: {missing_agents}")
        
        # Check dependency resolution
        for agent_name, dependencies in self.workflow_graph.items():
            for dep in dependencies:
                if dep not in available_agents:
                    issues.append(f"Agent {agent_name} depends on missing agent {dep}")
        
        # Check configuration
        if self.config.target_segments <= 0:
            issues.append("target_segments must be positive")
        
        if self.config.target_duration <= 0:
            issues.append("target_duration must be positive")
        
        # Check output directory
        try:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create output directory: {e}")
        
        return issues


# Convenience functions
def create_crew(config: Optional[WorkflowConfig] = None) -> AivaCrew:
    """Create a new AIVA crew with optional configuration."""
    return AivaCrew(config)


def run_workflow(script_content: str, 
                config: Optional[WorkflowConfig] = None,
                verbose: bool = True) -> WorkflowResult:
    """Run the complete AIVA workflow with a script."""
    crew = create_crew(config)
    
    # Add console callback if verbose
    if verbose:
        crew.add_callback(ConsoleProgressCallback(verbose=True))
    
    # Validate workflow
    issues = crew.validate_workflow()
    if issues:
        raise ValueError(f"Workflow validation failed: {issues}")
    
    # Execute workflow
    return crew.execute(script_content)


def get_workflow_status(result: WorkflowResult) -> Dict[str, Any]:
    """Get detailed status information from workflow result."""
    return {
        "status": result.status.value,
        "execution_time": result.execution_time,
        "error": result.error,
        "agent_count": len(result.agent_results),
        "successful_agents": len([r for r in result.agent_results.values() if r.status == AgentStatus.COMPLETED]),
        "failed_agents": len([r for r in result.agent_results.values() if r.status == AgentStatus.FAILED]),
        "final_output_available": result.get_final_output() is not None,
        "metadata": result.metadata
    }