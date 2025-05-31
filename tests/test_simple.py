#!/usr/bin/env python3
"""
Simple test to verify basic functionality with mocking.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

# Mock external dependencies before importing
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()
sys.modules['crewai'] = MagicMock()
sys.modules['crewai.agent'] = MagicMock()
sys.modules['crewai.crew'] = MagicMock()
sys.modules['crewai.task'] = MagicMock()

def test_basic_imports():
    """Test that basic imports work with mocking."""
    try:
        from config.loader import AIVASettings
        from core.pipeline import ContentPipeline
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_content_pipeline_creation():
    """Test that ContentPipeline can be instantiated."""
    from core.pipeline import ContentPipeline
    
    pipeline = ContentPipeline()
    assert pipeline is not None
    assert hasattr(pipeline, '_create_workflow_config')

def test_workflow_config_creation():
    """Test workflow config creation with simple dict."""
    from core.pipeline import ContentPipeline
    
    pipeline = ContentPipeline()
    config = {'target_segments': 5, 'output_dir': './test'}
    
    result = pipeline._create_workflow_config(config)
    assert result.target_segments == 5
    assert result.output_dir == './test'