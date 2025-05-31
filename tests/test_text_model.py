#!/usr/bin/env python3
"""
Unit Tests for Gemini Text Model

Tests the GeminiTextModel class with mocked HTTP requests to ensure
proper functionality without making actual API calls.
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Mock the google.generativeai module before any imports
mock_genai = MagicMock()
sys.modules['google.generativeai'] = mock_genai
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai

# Add the aiva_cli directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

# Now we can safely import our modules
from models.text_model import GeminiTextModel, generate_text


class TestGeminiTextModel:
    """Test cases for GeminiTextModel class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.gemini_api_key = "test_api_key"
        config.models.text_model = "gemini-1.5-flash"
        config.models.temperature = 0.7
        config.models.max_tokens = 2048
        config.models.timeout = 30
        config.max_retries = 3
        return config
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the google.generativeai module."""
        with patch('aiva_cli.models.text_model.genai') as mock:
            mock_model = Mock()
            mock.GenerativeModel.return_value = mock_model
            yield mock, mock_model
    
    @pytest.fixture
    def text_model(self, mock_config, mock_genai):
        """Create a GeminiTextModel instance for testing."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.text_model.load_config', return_value=mock_config):
            model = GeminiTextModel()
            model.model = mock_model
            return model
    
    def test_initialization_success(self, mock_config, mock_genai):
        """Test successful model initialization."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.text_model.load_config', return_value=mock_config):
            model = GeminiTextModel()
            
            # Verify API configuration
            mock_genai_module.configure.assert_called_once_with(api_key="test_api_key")
            
            # Verify model initialization
            mock_genai_module.GenerativeModel.assert_called_once_with("gemini-1.5-flash")
            
            # Verify attributes
            assert model.api_key == "test_api_key"
            assert model.model_name == "gemini-1.5-flash"
            assert model.max_retries == 3
    
    def test_initialization_with_custom_params(self, mock_config, mock_genai):
        """Test initialization with custom parameters."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.text_model.load_config', return_value=mock_config):
            model = GeminiTextModel(api_key="custom_key", model_name="custom-model")
            
            assert model.api_key == "custom_key"
            assert model.model_name == "custom-model"
    
    def test_generate_text_success(self, text_model):
        """Test successful text generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Generated text response"
        text_model.model.generate_content.return_value = mock_response
        
        result = text_model.generate_text("Test prompt")
        
        assert result == "Generated text response"
        text_model.model.generate_content.assert_called_once()
    
    def test_generate_text_empty_prompt(self, text_model):
        """Test text generation with empty prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            text_model.generate_text("")
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            text_model.generate_text("   ")
    
    def test_generate_text_with_custom_params(self, text_model):
        """Test text generation with custom parameters."""
        mock_response = Mock()
        mock_response.text = "Custom response"
        text_model.model.generate_content.return_value = mock_response
        
        result = text_model.generate_text(
            "Test prompt",
            temperature=0.9,
            max_tokens=1024
        )
        
        assert result == "Custom response"
        
        # Verify generation config was passed correctly
        call_args = text_model.model.generate_content.call_args
        generation_config = call_args[1]['generation_config']
        assert generation_config['temperature'] == 0.9
        assert generation_config['max_output_tokens'] == 1024
    
    def test_generate_text_empty_response(self, text_model):
        """Test handling of empty response from API."""
        mock_response = Mock()
        mock_response.text = ""
        text_model.model.generate_content.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Empty response from Gemini API"):
            text_model.generate_text("Test prompt")
    
    def test_generate_text_retry_logic(self, text_model):
        """Test retry logic on API failures."""
        # Mock failures for first two attempts, success on third
        text_model.model.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            Mock(text="Success on third try")
        ]
        
        with patch('time.sleep') as mock_sleep:
            result = text_model.generate_text("Test prompt")
        
        assert result == "Success on third try"
        assert text_model.model.generate_content.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep called between retries
    
    def test_generate_text_max_retries_exceeded(self, text_model):
        """Test behavior when max retries are exceeded."""
        # Mock failures for all attempts
        text_model.model.generate_content.side_effect = Exception("Persistent API Error")
        
        with patch('time.sleep'):
            with pytest.raises(RuntimeError, match="Text generation failed after 3 attempts"):
                text_model.generate_text("Test prompt")
        
        assert text_model.model.generate_content.call_count == 3
    
    def test_calculate_backoff(self, text_model):
        """Test exponential backoff calculation."""
        assert text_model._calculate_backoff(0) == 1.0
        assert text_model._calculate_backoff(1) == 2.0
        assert text_model._calculate_backoff(2) == 4.0
        assert text_model._calculate_backoff(10) == 60.0  # Max delay
    
    def test_validate_connection_success(self, text_model):
        """Test successful connection validation."""
        mock_response = Mock()
        mock_response.text = "Hello response"
        text_model.model.generate_content.return_value = mock_response
        
        assert text_model.validate_connection() is True
    
    def test_validate_connection_failure(self, text_model):
        """Test connection validation failure."""
        text_model.model.generate_content.side_effect = Exception("Connection failed")
        
        assert text_model.validate_connection() is False
    
    def test_get_model_info(self, text_model):
        """Test model information retrieval."""
        info = text_model.get_model_info()
        
        expected_keys = ['model_name', 'temperature', 'max_tokens', 'timeout', 'max_retries']
        for key in expected_keys:
            assert key in info
        
        assert info['model_name'] == "gemini-1.5-flash"
        assert info['temperature'] == 0.7
        assert info['max_retries'] == 3


class TestConvenienceFunction:
    """Test cases for the convenience generate_text function."""
    
    @patch('aiva_cli.models.text_model.GeminiTextModel')
    def test_generate_text_convenience(self, mock_model_class):
        """Test the convenience generate_text function."""
        mock_instance = Mock()
        mock_instance.generate_text.return_value = "Generated text"
        mock_model_class.return_value = mock_instance
        
        result = generate_text("Test prompt", temperature=0.8)
        
        assert result == "Generated text"
        mock_model_class.assert_called_once()
        mock_instance.generate_text.assert_called_once_with("Test prompt", temperature=0.8)


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    def test_import_error_handling(self):
        """Test handling of missing google-generativeai package."""
        with patch.dict('sys.modules', {'google.generativeai': None}):
            with pytest.raises(ImportError, match="google-generativeai package is required"):
                # This would normally trigger the import error
                import importlib
                importlib.reload(__import__('aiva_cli.models.text_model', fromlist=['']))
    
    @patch('aiva_cli.models.text_model.load_config')
    @patch('aiva_cli.models.text_model.genai')
    def test_model_initialization_failure(self, mock_genai, mock_load_config):
        """Test handling of model initialization failure."""
        mock_config = Mock()
        mock_config.gemini_api_key = "test_key"
        mock_config.models.text_model = "invalid-model"
        mock_load_config.return_value = mock_config
        
        mock_genai.GenerativeModel.side_effect = Exception("Model not found")
        
        with pytest.raises(Exception, match="Model not found"):
            GeminiTextModel()


if __name__ == "__main__":
    pytest.main([__file__])