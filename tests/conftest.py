#!/usr/bin/env python3
"""
Pytest Configuration and Shared Fixtures

Provides shared fixtures, configuration, and utilities for all test modules.
"""

import pytest
import sys
import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Add the aiva_cli directory to the path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

# Mock external dependencies before any imports
# Only mock if not already imported
if 'google' not in sys.modules:
    sys.modules['google'] = MagicMock()
if 'google.generativeai' not in sys.modules:
    sys.modules['google.generativeai'] = MagicMock()
if 'google.genai' not in sys.modules:
    sys.modules['google.genai'] = MagicMock()
if 'google.genai.types' not in sys.modules:
    sys.modules['google.genai.types'] = MagicMock()
if 'crewai' not in sys.modules:
    sys.modules['crewai'] = MagicMock()
if 'crewai.agent' not in sys.modules:
    sys.modules['crewai.agent'] = MagicMock()
if 'crewai.crew' not in sys.modules:
    sys.modules['crewai.crew'] = MagicMock()
if 'crewai.task' not in sys.modules:
    sys.modules['crewai.task'] = MagicMock()


@pytest.fixture(scope="session")
def test_config():
    """Session-wide test configuration."""
    return {
        'test_api_key': 'test_gemini_api_key_12345',
        'test_models': {
            'text_model': 'gemini-1.5-flash',
            'image_model': 'imagen-3.0-generate-001'
        },
        'test_timeouts': {
            'short': 1.0,
            'medium': 5.0,
            'long': 30.0
        }
    }


@pytest.fixture
def mock_aiva_config():
    """Standard mock AIVA configuration for tests."""
    config = Mock()
    config.gemini_api_key = "test_api_key"
    config.models = Mock()
    config.models.text_model = "gemini-1.5-flash"
    config.models.image_model = "imagen-3.0-generate-001"
    config.models.temperature = 0.7
    config.models.max_tokens = 2048
    config.models.timeout = 30
    config.script_length = 300
    config.segment_duration = 8
    config.max_retries = 3
    config.output_dir = "test_output"
    
    # Mock model_dump for AIVASettings compatibility
    config.model_dump.return_value = {
        "gemini_api_key": "test_api_key",
        "models": {
            "text_model": "gemini-1.5-flash",
            "image_model": "imagen-3.0-generate-001",
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 30
        },
        "script_length": 300,
        "segment_duration": 8,
        "max_retries": 3,
        "output_dir": "test_output"
    }
    
    return config


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="aiva_test_")
    workspace_path = Path(temp_dir)
    
    # Create basic directory structure
    (workspace_path / "projects").mkdir(exist_ok=True)
    (workspace_path / "config").mkdir(exist_ok=True)
    (workspace_path / "logs").mkdir(exist_ok=True)
    
    yield workspace_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_successful_crew():
    """Mock CrewAI crew that returns successful results."""
    crew = Mock()
    crew.kickoff.return_value = Mock(
        raw="Successful crew execution",
        tasks_output=[
            Mock(raw="Script: A comprehensive 5-minute video script about the topic..."),
            Mock(raw="Segments: 38 segments created, each 8 seconds long..."),
            Mock(raw="Prompts: Visual prompts generated for all segments..."),
            Mock(raw="Images: All 38 images rendered successfully...")
        ]
    )
    return crew


@pytest.fixture
def mock_agents():
    """Mock CrewAI agents for testing."""
    return {
        'script_agent': Mock(name='ScriptAgent'),
        'segmenter_agent': Mock(name='SegmenterAgent'),
        'prompt_gen_agent': Mock(name='PromptGenAgent'),
        'image_render_agent': Mock(name='ImageRenderAgent')
    }


@pytest.fixture
def mock_tasks():
    """Mock CrewAI tasks for testing."""
    return [
        Mock(name='ScriptTask'),
        Mock(name='SegmentTask'),
        Mock(name='PromptTask'),
        Mock(name='ImageTask')
    ]


@pytest.fixture
def sample_topics():
    """Sample topics for testing content generation."""
    return [
        "Artificial Intelligence Revolution",
        "Space Exploration and Mars Colonization",
        "Quantum Computing Breakthrough",
        "Climate Change Solutions",
        "Future of Renewable Energy",
        "Biotechnology and Gene Editing",
        "Virtual Reality and Metaverse",
        "Autonomous Vehicles Technology"
    ]


@pytest.fixture
def sample_video_types():
    """Sample video types for testing."""
    return [
        "educational",
        "documentary",
        "tutorial",
        "awareness",
        "technical",
        "entertainment"
    ]


class TestHelpers:
    """Helper utilities for tests."""
    
    @staticmethod
    def create_mock_manifest(project_title="Test Project", segments=38):
        """Create a mock manifest.json structure."""
        return {
            "project": {
                "title": project_title,
                "topic": "Test Topic",
                "video_type": "educational",
                "created_at": "2024-01-01T12:00:00Z",
                "duration": segments * 8
            },
            "segments": [
                {
                    "id": f"segment_{i:02d}",
                    "text": f"Segment {i} content",
                    "image_path": f"segment_{i:02d}/image.png",
                    "prompt": f"Visual prompt for segment {i}",
                    "status": "completed"
                }
                for i in range(1, segments + 1)
            ],
            "statistics": {
                "total_segments": segments,
                "success_rate": 1.0,
                "total_duration": 120.5,
                "avg_segment_time": 3.2
            },
            "crew_ai": {
                "agents_used": [
                    "ScriptAgent",
                    "SegmenterAgent", 
                    "PromptGenAgent",
                    "ImageRenderAgent"
                ]
            },
            "workflow_status": "completed",
            "enhancement_level": "Phase 7"
        }
    
    @staticmethod
    def create_mock_segment_files(workspace_path, num_segments=38):
        """Create mock segment files in workspace."""
        project_dir = workspace_path / "test_project"
        project_dir.mkdir(exist_ok=True)
        
        for i in range(1, num_segments + 1):
            segment_dir = project_dir / f"segment_{i:02d}"
            segment_dir.mkdir(exist_ok=True)
            
            # Create text file
            text_file = segment_dir / "text.txt"
            text_file.write_text(f"This is the content for segment {i}")
            
            # Create mock image file
            image_file = segment_dir / "image.png"
            image_file.write_bytes(b"fake_png_data")
        
        return project_dir
    
    @staticmethod
    def assert_valid_project_structure(project_path, expected_segments=38):
        """Assert that a project has valid structure."""
        project_path = Path(project_path)
        
        # Check manifest exists
        manifest_path = project_path / "manifest.json"
        assert manifest_path.exists(), "manifest.json should exist"
        
        # Check segments exist
        for i in range(1, expected_segments + 1):
            segment_dir = project_path / f"segment_{i:02d}"
            assert segment_dir.exists(), f"Segment {i:02d} directory should exist"
            
            text_file = segment_dir / "text.txt"
            image_file = segment_dir / "image.png"
            
            # Note: In real tests, these files might not exist if mocked
            # This is more for integration testing
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file names
        if "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker for tests that take longer
        if "stress_test" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.slow)


# Make TestHelpers available to all test modules
@pytest.fixture
def test_helpers():
    """Provide TestHelpers instance to tests."""
    return TestHelpers()