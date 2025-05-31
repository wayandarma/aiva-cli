#!/usr/bin/env python3
"""
Unit Tests for Gemini Image Model

Tests the GeminiImageModel class with mocked HTTP requests to ensure
proper functionality without making actual API calls.
"""

import pytest
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

# Mock the google.generativeai module before any imports
mock_genai = MagicMock()
sys.modules['google.generativeai'] = mock_genai
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai

# Now we can safely import our modules
from aiva_cli.models.image_model import GeminiImageModel, generate_image


class TestGeminiImageModel:
    """Test cases for GeminiImageModel class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.gemini_api_key = "test_api_key"
        config.models.image_model = "imagen-3.0-generate-001"
        config.models.timeout = 60
        config.max_retries = 3
        return config
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the google.generativeai module."""
        with patch('aiva_cli.models.image_model.genai') as mock:
            mock_model = Mock()
            mock.GenerativeModel.return_value = mock_model
            yield mock, mock_model
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def image_model(self, mock_config, mock_genai):
        """Create a GeminiImageModel instance for testing."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.image_model.load_config', return_value=mock_config):
            model = GeminiImageModel()
            model.model = mock_model
            return model
    
    def test_initialization_success(self, mock_config, mock_genai):
        """Test successful model initialization."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.image_model.load_config', return_value=mock_config):
            model = GeminiImageModel()
            
            # Verify API configuration
            mock_genai_module.configure.assert_called_once_with(api_key="test_api_key")
            
            # Verify model initialization
            mock_genai_module.GenerativeModel.assert_called_once_with("imagen-3.0-generate-001")
            
            # Verify attributes
            assert model.api_key == "test_api_key"
            assert model.model_name == "imagen-3.0-generate-001"
            assert model.max_retries == 3
    
    def test_initialization_with_custom_params(self, mock_config, mock_genai):
        """Test initialization with custom parameters."""
        mock_genai_module, mock_model = mock_genai
        
        with patch('aiva_cli.models.image_model.load_config', return_value=mock_config):
            model = GeminiImageModel(api_key="custom_key", model_name="custom-model")
            
            assert model.api_key == "custom_key"
            assert model.model_name == "custom-model"
    
    def test_generate_image_success(self, image_model, temp_dir):
        """Test successful image generation."""
        # Mock successful response with image data
        mock_response = Mock()
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        image_model.model.generate_content.return_value = mock_response
        
        output_path = temp_dir / "test_image.png"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = image_model.generate_image("A beautiful sunset", output_path)
        
        assert result == output_path
        image_model.model.generate_content.assert_called_once()
        mock_image._pil_image.save.assert_called_once_with(output_path, format='PNG')
    
    def test_generate_image_empty_prompt(self, image_model, temp_dir):
        """Test image generation with empty prompt."""
        output_path = temp_dir / "test_image.png"
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            image_model.generate_image("", output_path)
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            image_model.generate_image("   ", output_path)
    
    def test_generate_image_invalid_path(self, image_model):
        """Test image generation with invalid output path."""
        invalid_path = Path("/nonexistent/directory/image.png")
        
        with pytest.raises(ValueError, match="Output directory does not exist"):
            image_model.generate_image("Test prompt", invalid_path)
    
    def test_generate_image_auto_filename(self, image_model, temp_dir):
        """Test image generation with automatic filename generation."""
        mock_response = Mock()
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        image_model.model.generate_content.return_value = mock_response
        
        with patch('builtins.open', mock_open()):
            with patch('aiva_cli.models.image_model.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
                
                result = image_model.generate_image("Test prompt", temp_dir)
        
        expected_path = temp_dir / "generated_image_20240101_120000.png"
        assert result == expected_path
    
    def test_generate_image_no_image_in_response(self, image_model, temp_dir):
        """Test handling of response without image data."""
        mock_response = Mock()
        mock_response.candidates = [Mock(content=Mock(parts=[]))]
        image_model.model.generate_content.return_value = mock_response
        
        output_path = temp_dir / "test_image.png"
        
        with pytest.raises(RuntimeError, match="No image found in API response"):
            image_model.generate_image("Test prompt", output_path)
    
    def test_generate_image_retry_logic(self, image_model, temp_dir):
        """Test retry logic on API failures."""
        # Mock failures for first two attempts, success on third
        mock_success_response = Mock()
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_success_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        
        image_model.model.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_success_response
        ]
        
        output_path = temp_dir / "test_image.png"
        
        with patch('time.sleep') as mock_sleep:
            with patch('builtins.open', mock_open()):
                result = image_model.generate_image("Test prompt", output_path)
        
        assert result == output_path
        assert image_model.model.generate_content.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep called between retries
    
    def test_generate_image_max_retries_exceeded(self, image_model, temp_dir):
        """Test behavior when max retries are exceeded."""
        # Mock failures for all attempts
        image_model.model.generate_content.side_effect = Exception("Persistent API Error")
        
        output_path = temp_dir / "test_image.png"
        
        with patch('time.sleep'):
            with pytest.raises(RuntimeError, match="Image generation failed after 3 attempts"):
                image_model.generate_image("Test prompt", output_path)
        
        assert image_model.model.generate_content.call_count == 3
    
    def test_generate_multiple_images_success(self, image_model, temp_dir):
        """Test successful generation of multiple images."""
        # Mock successful responses
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_response = Mock()
        mock_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        image_model.model.generate_content.return_value = mock_response
        
        prompts = ["Sunset", "Mountain", "Ocean"]
        
        with patch('builtins.open', mock_open()):
            with patch('aiva_cli.models.image_model.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.side_effect = [
                    "20240101_120001", "20240101_120002", "20240101_120003"
                ]
                
                results = image_model.generate_multiple_images(prompts, temp_dir)
        
        assert len(results) == 3
        assert image_model.model.generate_content.call_count == 3
        
        # Verify all expected paths are returned
        expected_paths = [
            temp_dir / "generated_image_20240101_120001.png",
            temp_dir / "generated_image_20240101_120002.png",
            temp_dir / "generated_image_20240101_120003.png"
        ]
        assert results == expected_paths
    
    def test_generate_multiple_images_partial_failure(self, image_model, temp_dir):
        """Test multiple image generation with some failures."""
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_success_response = Mock()
        mock_success_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        
        # First succeeds, second fails, third succeeds
        image_model.model.generate_content.side_effect = [
            mock_success_response,
            Exception("API Error"),
            mock_success_response
        ]
        
        prompts = ["Sunset", "Mountain", "Ocean"]
        
        with patch('builtins.open', mock_open()):
            with patch('aiva_cli.models.image_model.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.side_effect = [
                    "20240101_120001", "20240101_120003"
                ]
                with patch('time.sleep'):
                    results = image_model.generate_multiple_images(prompts, temp_dir)
        
        # Should return 2 successful results
        assert len(results) == 2
    
    def test_calculate_backoff(self, image_model):
        """Test exponential backoff calculation."""
        assert image_model._calculate_backoff(0) == 1.0
        assert image_model._calculate_backoff(1) == 2.0
        assert image_model._calculate_backoff(2) == 4.0
        assert image_model._calculate_backoff(10) == 60.0  # Max delay
    
    def test_validate_connection_success(self, image_model, temp_dir):
        """Test successful connection validation."""
        mock_response = Mock()
        mock_image = Mock()
        mock_image._pil_image.save = Mock()
        mock_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        image_model.model.generate_content.return_value = mock_response
        
        with patch('builtins.open', mock_open()):
            assert image_model.validate_connection() is True
    
    def test_validate_connection_failure(self, image_model):
        """Test connection validation failure."""
        image_model.model.generate_content.side_effect = Exception("Connection failed")
        
        assert image_model.validate_connection() is False
    
    def test_get_model_info(self, image_model):
        """Test model information retrieval."""
        info = image_model.get_model_info()
        
        expected_keys = ['model_name', 'timeout', 'max_retries']
        for key in expected_keys:
            assert key in info
        
        assert info['model_name'] == "imagen-3.0-generate-001"
        assert info['max_retries'] == 3


class TestConvenienceFunction:
    """Test cases for the convenience generate_image function."""
    
    @patch('aiva_cli.models.image_model.GeminiImageModel')
    def test_generate_image_convenience(self, mock_model_class):
        """Test the convenience generate_image function."""
        mock_instance = Mock()
        mock_instance.generate_image.return_value = Path("/test/image.png")
        mock_model_class.return_value = mock_instance
        
        result = generate_image("Test prompt", Path("/test/output.png"))
        
        assert result == Path("/test/image.png")
        mock_model_class.assert_called_once()
        mock_instance.generate_image.assert_called_once_with("Test prompt", Path("/test/output.png"))


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    def test_import_error_handling(self):
        """Test handling of missing google-generativeai package."""
        with patch.dict('sys.modules', {'google.generativeai': None}):
            with pytest.raises(ImportError, match="google-generativeai package is required"):
                # This would normally trigger the import error
                import importlib
                importlib.reload(__import__('aiva_cli.models.image_model', fromlist=['']))
    
    @patch('aiva_cli.models.image_model.load_config')
    @patch('aiva_cli.models.image_model.genai')
    def test_model_initialization_failure(self, mock_genai, mock_load_config):
        """Test handling of model initialization failure."""
        mock_config = Mock()
        mock_config.gemini_api_key = "test_key"
        mock_config.models.image_model = "invalid-model"
        mock_load_config.return_value = mock_config
        
        mock_genai.GenerativeModel.side_effect = Exception("Model not found")
        
        with pytest.raises(Exception, match="Model not found"):
            GeminiImageModel()
    
    def test_file_save_error(self, image_model, temp_dir):
        """Test handling of file save errors."""
        mock_response = Mock()
        mock_image = Mock()
        mock_image._pil_image.save.side_effect = Exception("Save failed")
        mock_response.candidates = [Mock(content=Mock(parts=[mock_image]))]
        image_model.model.generate_content.return_value = mock_response
        
        output_path = temp_dir / "test_image.png"
        
        with pytest.raises(RuntimeError, match="Failed to save image"):
            image_model.generate_image("Test prompt", output_path)


if __name__ == "__main__":
    pytest.main([__file__])