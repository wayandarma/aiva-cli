#!/usr/bin/env python3
"""
Unit Tests for CLI Module

Tests the command-line interface functionality including argument parsing,
validation, and command execution.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

# Add the aiva_cli directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

from cli import app, generate, init, status


class TestCLI:
    """Test cases for CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.gemini_api_key = "test_api_key"
        config.models = Mock()
        config.models.text_model = "gemini-1.5-flash"
        config.output_dir = "test_output"
        return config
    
    def test_app_help(self, runner):
        """Test that the main app shows help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AIVA CLI" in result.stdout
        assert "generate" in result.stdout
        assert "init" in result.stdout
        assert "status" in result.stdout
    
    @patch('cli.load_config')
    @patch('cli.generate_content')
    def test_generate_command_basic(self, mock_generate, mock_load_config, runner):
        """Test basic generate command."""
        mock_load_config.return_value = Mock()
        mock_generate.return_value = "test_output_dir"
        
        result = runner.invoke(app, ["generate", "AI Revolution"])
        
        assert result.exit_code == 0
        mock_generate.assert_called_once()
        assert "Content generation completed" in result.stdout
    
    @patch('cli.load_config')
    @patch('cli.generate_content')
    def test_generate_command_with_options(self, mock_generate, mock_load_config, runner):
        """Test generate command with all options."""
        mock_load_config.return_value = Mock()
        mock_generate.return_value = "test_output_dir"
        
        result = runner.invoke(app, [
            "generate", "AI Revolution",
            "--type", "educational",
            "--output-dir", "custom_output",
            "--title", "Custom AI Guide"
        ])
        
        assert result.exit_code == 0
        mock_generate.assert_called_once()
        
        # Check that the function was called with correct parameters
        call_args = mock_generate.call_args
        assert call_args[1]['topic'] == "AI Revolution"
        assert call_args[1]['video_type'] == "educational"
        assert call_args[1]['out_dir'] == "custom_output"
        assert call_args[1]['title'] == "Custom AI Guide"
    
    @patch('cli.load_config')
    def test_generate_command_config_error(self, mock_load_config, runner):
        """Test generate command with configuration error."""
        mock_load_config.side_effect = Exception("Config load failed")
        
        result = runner.invoke(app, ["generate", "AI Revolution"])
        
        assert result.exit_code == 1
        assert "Error loading configuration" in result.stdout
    
    @patch('cli.load_config')
    @patch('cli.generate_content')
    def test_generate_command_generation_error(self, mock_generate, mock_load_config, runner):
        """Test generate command with generation error."""
        mock_load_config.return_value = Mock()
        mock_generate.side_effect = Exception("Generation failed")
        
        result = runner.invoke(app, ["generate", "AI Revolution"])
        
        assert result.exit_code == 1
        assert "Error during content generation" in result.stdout
    
    def test_generate_command_empty_topic(self, runner):
        """Test generate command with empty topic."""
        result = runner.invoke(app, ["generate", ""])
        
        assert result.exit_code == 2  # Typer validation error
    
    def test_generate_command_invalid_video_type(self, runner):
        """Test generate command with invalid video type."""
        result = runner.invoke(app, [
            "generate", "AI Revolution",
            "--type", "invalid_type"
        ])
        
        assert result.exit_code == 2  # Typer validation error
    
    @patch('cli.load_config')
    @patch('cli.generate_content')
    def test_generate_command_dry_run(self, mock_generate, mock_load_config, runner):
        """Test generate command with dry run option."""
        mock_load_config.return_value = Mock()
        
        result = runner.invoke(app, [
            "generate", "AI Revolution",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        mock_generate.assert_not_called()
    
    @patch('cli.Path.exists')
    @patch('cli.Path.mkdir')
    @patch('builtins.open')
    def test_init_command_new_config(self, mock_open, mock_mkdir, mock_exists, runner):
        """Test init command creating new configuration."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["init"])
        
        assert result.exit_code == 0
        assert "Configuration initialized" in result.stdout
        mock_mkdir.assert_called()
    
    @patch('cli.Path.exists')
    def test_init_command_existing_config(self, mock_exists, runner):
        """Test init command with existing configuration."""
        mock_exists.return_value = True
        
        result = runner.invoke(app, ["init"])
        
        assert result.exit_code == 0
        assert "Configuration already exists" in result.stdout
    
    @patch('cli.Path.exists')
    @patch('cli.load_config')
    def test_status_command_with_config(self, mock_load_config, mock_exists, runner):
        """Test status command with valid configuration."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.gemini_api_key = "test_key"
        mock_config.models = Mock()
        mock_config.models.text_model = "gemini-1.5-flash"
        mock_config.models.image_model = "imagen-3.0-generate-001"
        mock_load_config.return_value = mock_config
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "AIVA CLI Status" in result.stdout
        assert "Configuration: ✅ Valid" in result.stdout
        assert "API Key: ✅ Configured" in result.stdout
    
    @patch('cli.Path.exists')
    def test_status_command_no_config(self, mock_exists, runner):
        """Test status command without configuration."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "Configuration: ❌ Not found" in result.stdout
    
    @patch('cli.Path.exists')
    @patch('cli.load_config')
    def test_status_command_config_error(self, mock_load_config, mock_exists, runner):
        """Test status command with configuration error."""
        mock_exists.return_value = True
        mock_load_config.side_effect = Exception("Config error")
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "Configuration: ❌ Error loading" in result.stdout
    
    def test_generate_command_title_validation(self, runner):
        """Test generate command title validation."""
        # Test with very long title
        long_title = "A" * 101  # Assuming 100 char limit
        
        with patch('cli.load_config') as mock_load_config:
            mock_load_config.return_value = Mock()
            
            result = runner.invoke(app, [
                "generate", "AI Revolution",
                "--title", long_title
            ])
            
            # Should handle long titles gracefully
            assert result.exit_code in [0, 1]  # Either success or handled error
    
    @patch('cli.load_config')
    @patch('cli.generate_content')
    def test_generate_command_verbose_output(self, mock_generate, mock_load_config, runner):
        """Test generate command with verbose output."""
        mock_load_config.return_value = Mock()
        mock_generate.return_value = "test_output_dir"
        
        result = runner.invoke(app, [
            "generate", "AI Revolution",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        # Verbose mode should show more detailed output
        assert "Content generation completed" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])