"""Simple test runner for crew configuration verification.

This module provides basic tests to verify that agents are properly
registered and the crew orchestrator functions correctly without
requiring external testing frameworks.
"""

import sys
import traceback
from pathlib import Path
import pytest # Moved import here

try:
    # Import modules using absolute imports
    from aiva_cli.crew_config import agents as agents_module
    from aiva_cli.crew_config import crew as crew_module
    from aiva_cli.core import prompt_enhancer as enhancer_module
    
    # Extract specific classes and functions
    BaseAgent = agents_module.BaseAgent
    AgentResult = agents_module.AgentResult
    AgentStatus = agents_module.AgentStatus
    ScriptAgent = agents_module.ScriptAgent
    SegmenterAgent = agents_module.SegmenterAgent
    PromptGenAgent = agents_module.PromptGenAgent
    ImageRenderAgent = agents_module.ImageRenderAgent
    get_agent = agents_module.get_agent
    list_available_agents = agents_module.list_available_agents
    
    AivaCrew = crew_module.AivaCrew
    WorkflowConfig = crew_module.WorkflowConfig
    WorkflowResult = crew_module.WorkflowResult
    WorkflowStatus = crew_module.WorkflowStatus
    ConsoleProgressCallback = crew_module.ConsoleProgressCallback
    create_crew = crew_module.create_crew
    
    StylePreset = enhancer_module.StylePreset
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available.")
    traceback.print_exc()  # Add this line to print the full traceback
    sys.exit(1)


def test_agent_registry():
    """Test agent registration and retrieval."""
    print("\n🧪 Testing Agent Registry...")
    
    # Test list_available_agents
    try:
        agents = list_available_agents()
        expected_agents = ["script", "segmenter", "prompt_gen", "image_render"]
        
        print(f"   Available agents: {agents}")
        
        for agent_name in expected_agents:
            assert agent_name in agents, f"{agent_name} agent is missing"
            print(f"   ✅ {agent_name} agent is registered")
        
        print("   ✅ All agent registry checks passed")
        
    except Exception as e:
        print(f"   ❌ Error testing agent registry: {e}")
        raise # Re-raise the exception to fail the test


def test_agent_creation():
    """Test creating individual agents."""
    print("\n🧪 Testing Agent Creation...")
    
    agent_types = [
        ("script", ScriptAgent, "Script Analyst and Preprocessor"),
        ("segmenter", SegmenterAgent, "Script Segmentation Specialist"),
        ("prompt_gen", PromptGenAgent, "Cinematic Prompt Engineer"),
        ("image_render", ImageRenderAgent, "AI Image Generation Specialist")
    ]
    
    for agent_name, agent_class, expected_role in agent_types:
        try:
            # Test get_agent function
            agent = get_agent(agent_name)
            
            assert isinstance(agent, agent_class), f"{agent_name} agent has wrong type: {type(agent)}"
            print(f"   ✅ {agent_name} agent created successfully")
            
            # Test agent info
            info = agent.get_info()
            assert info.get("role") == expected_role, f"{agent_name} has wrong role: {info.get('role')}"
            print(f"   ✅ {agent_name} has correct role: {expected_role}")
            
            # Check info structure
            required_fields = ["role", "goal", "backstory", "tools"]
            for field in required_fields:
                assert field in info, f"{agent_name} missing {field} in info"
            
            print(f"   ✅ {agent_name} info structure is valid")
            
        except Exception as e:
            print(f"   ❌ Error creating {agent_name} agent: {e}")
            raise  # Re-raise the exception to fail the test
    
    print("   ✅ All agent creation checks passed")


def test_invalid_agent():
    """Test that invalid agent names raise errors."""
    print("\n🧪 Testing Invalid Agent Handling...")
    
    with pytest.raises(ValueError, match="Unknown agent type"):
        get_agent("nonexistent_agent")
    print("   ✅ Correctly raised ValueError for invalid agent with expected message")
    
    print("   ✅ All invalid agent handling checks passed")


def test_crew_creation():
    """Test crew creation and initialization."""
    print("\n🧪 Testing Crew Creation...")
    
    # Test default crew creation
    crew = AivaCrew()
    
    # Check agents are initialized
    assert len(crew.agents) == 4, f"Expected 4 agents, got {len(crew.agents)}"
    print(f"   ✅ Crew initialized with {len(crew.agents)} agents")
    
    # Check specific agents
    expected_agents = ["script", "segmenter", "prompt_gen", "image_render"]
    for agent_name in expected_agents:
        assert agent_name in crew.agents, f"{agent_name} agent missing from crew"
        print(f"   ✅ {agent_name} agent present in crew")
    
    # Check workflow graph
    expected_graph = {
        "script": [],
        "segmenter": ["script"],
        "prompt_gen": ["segmenter"],
        "image_render": ["prompt_gen"]
    }
    
    assert crew.workflow_graph == expected_graph, \
        f"Workflow graph mismatch. Expected: {expected_graph}, Got: {crew.workflow_graph}"
    print("   ✅ Workflow graph is correct")

    print("   ✅ All crew creation checks passed")


def test_crew_with_config():
    """Test crew creation with custom configuration."""
    print("\n🧪 Testing Crew with Custom Config...")
    
    config = WorkflowConfig(
        target_segments=8,
        target_duration=10.0,
        style_preset=StylePreset.REALISTIC,
        output_dir="./test_output"
    )
    
    crew = AivaCrew(config)
    
    # Verify config is applied
    assert crew.config.target_segments == 8, f"target_segments wrong: {crew.config.target_segments}"
    print("   ✅ target_segments config applied")
    
    assert crew.config.target_duration == 10.0, f"target_duration wrong: {crew.config.target_duration}"
    print("   ✅ target_duration config applied")
    
    assert crew.config.style_preset == StylePreset.REALISTIC, f"style_preset wrong: {crew.config.style_preset}"
    print("   ✅ style_preset config applied")
    
    # output_dir is also part of the config, let's assert that too for completeness
    assert crew.config.output_dir == "./test_output", f"output_dir wrong: {crew.config.output_dir}"
    print("   ✅ output_dir config applied")

    print("   ✅ All custom config checks passed")


def test_execution_order():
    """Test that execution order follows dependencies."""
    print("\n🧪 Testing Execution Order...")
    
    crew = AivaCrew()
    execution_order = crew._get_execution_order()
    
    expected_order = ["script", "segmenter", "prompt_gen", "image_render"]
    
    assert execution_order == expected_order, \
        f"Execution order wrong. Expected: {expected_order}, Got: {execution_order}"
    print(f"   ✅ Execution order is correct: {execution_order}")
    
    print("   ✅ All execution order checks passed")


def test_workflow_validation():
    """Test workflow validation."""
    print("\n🧪 Testing Workflow Validation...")
    
    # Test valid configuration
    crew = AivaCrew()
    issues = crew.validate_workflow()
    # Assuming a valid default config should have 0 issues.
    # If there can be informational 'issues' for a valid config, this assert might need adjustment.
    assert len(issues) == 0, f"Expected 0 validation issues for default config, got {len(issues)}: {issues}"
    print(f"   Validation issues found for default config: {len(issues)}")
    for issue in issues:
        print(f"   ⚠️  {issue}")
    
    # Test invalid configuration
    invalid_config = WorkflowConfig(
        target_segments=-1,
        target_duration=0
    )
    
    invalid_crew = AivaCrew(invalid_config)
    invalid_issues = invalid_crew.validate_workflow()
    
    expected_issue_substrings = [
        "target_segments must be positive",
        "target_duration must be positive"
    ]
    
    # Check that each expected substring is present in at least one of the reported issues
    for expected_substring in expected_issue_substrings:
        assert any(expected_substring in issue for issue in invalid_issues), \
            f"Missing expected validation issue containing: '{expected_substring}' in {invalid_issues}"
        print(f"   ✅ Found expected validation issue: {expected_substring}")

    # Optionally, assert the exact number of issues if it's strictly defined for this invalid case
    # assert len(invalid_issues) == len(expected_issue_substrings), \
    #     f"Expected {len(expected_issue_substrings)} issues for invalid config, got {len(invalid_issues)}: {invalid_issues}"

    print("   ✅ Validation correctly identifies invalid config")


def test_convenience_functions():
    """Test convenience functions."""
    print("\n🧪 Testing Convenience Functions...")
    
    # Test create_crew
    crew = create_crew()
    assert isinstance(crew, AivaCrew), f"create_crew() returned wrong type: {type(crew)}"
    print("   ✅ create_crew() works")
    
    # Test create_crew with config
    config = WorkflowConfig(target_segments=5)
    crew_custom = create_crew(config)
    assert crew_custom.config.target_segments == 5, \
        f"create_crew(config) wrong segments: {crew_custom.config.target_segments}"
    print("   ✅ create_crew(config) works")
    
    print("   ✅ All convenience function checks passed")


def test_progress_callbacks():
    """Test progress callback functionality."""
    print("\n🧪 Testing Progress Callbacks...")
    
    # Test callback creation
    callback = ConsoleProgressCallback(verbose=True)
    assert callback.verbose is True, "ConsoleProgressCallback verbose flag wrong"
    print("   ✅ ConsoleProgressCallback created")
    
    # Test callback registration
    crew = AivaCrew()
    crew.add_callback(callback)
    assert callback in crew.callbacks, "Callback not added to crew"
    print("   ✅ Callback added to crew")
    
    # Test callback removal
    crew.remove_callback(callback)
    assert callback not in crew.callbacks, "Callback not removed from crew"
    print("   ✅ Callback removed from crew")
    
    # Test callback methods exist
    required_methods = [
        'on_workflow_start', 'on_agent_start', 'on_agent_complete',
        'on_agent_error', 'on_workflow_complete'
    ]
    
    for method_name in required_methods:
        assert hasattr(callback, method_name) and callable(getattr(callback, method_name)), \
            f"{method_name} method missing or not callable"
        print(f"   ✅ {method_name} method exists")
    
    print("   ✅ All progress callback checks passed")


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting AIVA Crew Configuration Tests")
    print("=" * 50)
    
    tests = [
        ("Agent Registry", test_agent_registry),
        ("Agent Creation", test_agent_creation),
        ("Invalid Agent Handling", test_invalid_agent),
        ("Crew Creation", test_crew_creation),
        ("Crew with Custom Config", test_crew_with_config),
        ("Execution Order", test_execution_order),
        ("Workflow Validation", test_workflow_validation),
        ("Convenience Functions", test_convenience_functions),
        ("Progress Callbacks", test_progress_callbacks)
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
                failed_tests.append(test_name)
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
            traceback.print_exc()
            failed += 1
            failed_tests.append(test_name)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Agent registry is working correctly.")
        return True
    else:
        print(f"💔 {failed} tests failed: {', '.join(failed_tests)}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)