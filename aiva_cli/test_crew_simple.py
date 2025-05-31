"""Simple test runner for crew configuration verification.

This module provides basic tests to verify that agents are properly
registered and the crew orchestrator functions correctly without
requiring external testing frameworks.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Import modules using absolute imports
    import crew_config.agents as agents_module
    import crew_config.crew as crew_module
    import core.prompt_enhancer as enhancer_module
    
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
            if agent_name in agents:
                print(f"   ✅ {agent_name} agent is registered")
            else:
                print(f"   ❌ {agent_name} agent is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing agent registry: {e}")
        return False


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
            
            if isinstance(agent, agent_class):
                print(f"   ✅ {agent_name} agent created successfully")
            else:
                print(f"   ❌ {agent_name} agent has wrong type: {type(agent)}")
                return False
            
            # Test agent info
            info = agent.get_info()
            if info.get("role") == expected_role:
                print(f"   ✅ {agent_name} has correct role: {expected_role}")
            else:
                print(f"   ❌ {agent_name} has wrong role: {info.get('role')}")
                return False
            
            # Check info structure
            required_fields = ["role", "goal", "backstory", "tools"]
            for field in required_fields:
                if field not in info:
                    print(f"   ❌ {agent_name} missing {field} in info")
                    return False
            
            print(f"   ✅ {agent_name} info structure is valid")
            
        except Exception as e:
            print(f"   ❌ Error creating {agent_name} agent: {e}")
            return False
    
    return True


def test_invalid_agent():
    """Test that invalid agent names raise errors."""
    print("\n🧪 Testing Invalid Agent Handling...")
    
    try:
        get_agent("nonexistent_agent")
        print("   ❌ Should have raised error for invalid agent")
        return False
    except ValueError as e:
        if "Unknown agent type" in str(e):
            print("   ✅ Correctly raised error for invalid agent")
            return True
        else:
            print(f"   ❌ Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_crew_creation():
    """Test crew creation and initialization."""
    print("\n🧪 Testing Crew Creation...")
    
    try:
        # Test default crew creation
        crew = AivaCrew()
        
        # Check agents are initialized
        if len(crew.agents) == 4:
            print(f"   ✅ Crew initialized with {len(crew.agents)} agents")
        else:
            print(f"   ❌ Expected 4 agents, got {len(crew.agents)}")
            return False
        
        # Check specific agents
        expected_agents = ["script", "segmenter", "prompt_gen", "image_render"]
        for agent_name in expected_agents:
            if agent_name in crew.agents:
                print(f"   ✅ {agent_name} agent present in crew")
            else:
                print(f"   ❌ {agent_name} agent missing from crew")
                return False
        
        # Check workflow graph
        expected_graph = {
            "script": [],
            "segmenter": ["script"],
            "prompt_gen": ["segmenter"],
            "image_render": ["prompt_gen"]
        }
        
        if crew.workflow_graph == expected_graph:
            print("   ✅ Workflow graph is correct")
        else:
            print(f"   ❌ Workflow graph mismatch:")
            print(f"      Expected: {expected_graph}")
            print(f"      Got: {crew.workflow_graph}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating crew: {e}")
        traceback.print_exc()
        return False


def test_crew_with_config():
    """Test crew creation with custom configuration."""
    print("\n🧪 Testing Crew with Custom Config...")
    
    try:
        config = WorkflowConfig(
            target_segments=8,
            target_duration=10.0,
            style_preset=StylePreset.REALISTIC,
            output_dir="./test_output"
        )
        
        crew = AivaCrew(config)
        
        # Verify config is applied
        if crew.config.target_segments == 8:
            print("   ✅ target_segments config applied")
        else:
            print(f"   ❌ target_segments wrong: {crew.config.target_segments}")
            return False
        
        if crew.config.target_duration == 10.0:
            print("   ✅ target_duration config applied")
        else:
            print(f"   ❌ target_duration wrong: {crew.config.target_duration}")
            return False
        
        if crew.config.style_preset == StylePreset.REALISTIC:
            print("   ✅ style_preset config applied")
        else:
            print(f"   ❌ style_preset wrong: {crew.config.style_preset}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing custom config: {e}")
        return False


def test_execution_order():
    """Test that execution order follows dependencies."""
    print("\n🧪 Testing Execution Order...")
    
    try:
        crew = AivaCrew()
        execution_order = crew._get_execution_order()
        
        expected_order = ["script", "segmenter", "prompt_gen", "image_render"]
        
        if execution_order == expected_order:
            print(f"   ✅ Execution order is correct: {execution_order}")
            return True
        else:
            print(f"   ❌ Execution order wrong:")
            print(f"      Expected: {expected_order}")
            print(f"      Got: {execution_order}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing execution order: {e}")
        return False


def test_workflow_validation():
    """Test workflow validation."""
    print("\n🧪 Testing Workflow Validation...")
    
    try:
        # Test valid configuration
        crew = AivaCrew()
        issues = crew.validate_workflow()
        
        print(f"   Validation issues found: {len(issues)}")
        for issue in issues:
            print(f"   ⚠️  {issue}")
        
        # Test invalid configuration
        invalid_config = WorkflowConfig(
            target_segments=-1,
            target_duration=0
        )
        
        invalid_crew = AivaCrew(invalid_config)
        invalid_issues = invalid_crew.validate_workflow()
        
        expected_issues = [
            "target_segments must be positive",
            "target_duration must be positive"
        ]
        
        found_expected = 0
        for expected in expected_issues:
            for issue in invalid_issues:
                if expected in issue:
                    found_expected += 1
                    print(f"   ✅ Found expected validation issue: {expected}")
                    break
        
        if found_expected == len(expected_issues):
            print("   ✅ Validation correctly identifies invalid config")
            return True
        else:
            print(f"   ❌ Missing expected validation issues")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing workflow validation: {e}")
        return False


def test_convenience_functions():
    """Test convenience functions."""
    print("\n🧪 Testing Convenience Functions...")
    
    try:
        # Test create_crew
        crew = create_crew()
        if isinstance(crew, AivaCrew):
            print("   ✅ create_crew() works")
        else:
            print(f"   ❌ create_crew() returned wrong type: {type(crew)}")
            return False
        
        # Test create_crew with config
        config = WorkflowConfig(target_segments=5)
        crew_custom = create_crew(config)
        if crew_custom.config.target_segments == 5:
            print("   ✅ create_crew(config) works")
        else:
            print(f"   ❌ create_crew(config) wrong segments: {crew_custom.config.target_segments}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing convenience functions: {e}")
        return False


def test_progress_callbacks():
    """Test progress callback functionality."""
    print("\n🧪 Testing Progress Callbacks...")
    
    try:
        # Test callback creation
        callback = ConsoleProgressCallback(verbose=True)
        if callback.verbose is True:
            print("   ✅ ConsoleProgressCallback created")
        else:
            print("   ❌ ConsoleProgressCallback verbose flag wrong")
            return False
        
        # Test callback registration
        crew = AivaCrew()
        crew.add_callback(callback)
        
        if callback in crew.callbacks:
            print("   ✅ Callback added to crew")
        else:
            print("   ❌ Callback not added to crew")
            return False
        
        # Test callback removal
        crew.remove_callback(callback)
        if callback not in crew.callbacks:
            print("   ✅ Callback removed from crew")
        else:
            print("   ❌ Callback not removed from crew")
            return False
        
        # Test callback methods exist
        required_methods = [
            'on_workflow_start', 'on_agent_start', 'on_agent_complete',
            'on_agent_error', 'on_workflow_complete'
        ]
        
        for method_name in required_methods:
            if hasattr(callback, method_name) and callable(getattr(callback, method_name)):
                print(f"   ✅ {method_name} method exists")
            else:
                print(f"   ❌ {method_name} method missing or not callable")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing progress callbacks: {e}")
        return False


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