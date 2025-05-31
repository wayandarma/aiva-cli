#!/usr/bin/env python3
"""
Configuration Loader for AIVA CLI

Loads environment variables from .env file and merges with settings.json
to create a unified configuration using Pydantic models.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator # Updated import
from dotenv import load_dotenv


class AgentConfig(BaseModel):
    """Configuration for individual CrewAI agents."""
    name: str
    role: str
    goal: str
    backstory: str
    tools: List[str] = []
    verbose: bool = True
    allow_delegation: bool = False


class ContentConfig(BaseModel):
    """Content generation configuration."""
    script_length: int = Field(default=300, description="Target script length in words")
    segment_duration: int = Field(default=8, description="Duration per segment in seconds")
    total_duration: int = Field(default=300, description="Total video duration in seconds")
    target_audience: str = Field(default="20-35 year olds in Indonesia")
    content_style: str = Field(default="cinematic and educational")
    image_quality: str = Field(default="4K")
    image_style: str = Field(default="dramatic lighting")


class ModelConfig(BaseModel):
    """AI model configuration."""
    text_model: str = Field(default="gemini-2.0-flash")
    image_model: str = Field(default="imagen-3.0-generate-002")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    timeout: int = Field(default=30, gt=0)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file_enabled: bool = Field(default=True)
    console_enabled: bool = Field(default=True)
    max_file_size: str = Field(default="10MB")
    backup_count: int = Field(default=5)
    log_dir: str = Field(default="logs")


class OutputConfig(BaseModel):
    """Output configuration."""
    base_dir: str = Field(default="output")
    create_manifest: bool = Field(default=True)
    include_metadata: bool = Field(default=True)
    compress_images: bool = Field(default=False)
    image_format: str = Field(default="png")


class AIVASettings(BaseModel):
    """Main AIVA CLI configuration model."""
    
    # API Keys
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    
    # Model Configuration
    models: ModelConfig = Field(default_factory=ModelConfig)
    
    # Content Configuration
    content: ContentConfig = Field(default_factory=ContentConfig)
    
    # Logging Configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Output Configuration
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Agent Configurations
    agents: List[AgentConfig] = Field(default_factory=list)
    
    # System Configuration
    debug: bool = Field(default=False)
    max_retries: int = Field(default=3, ge=0)
    concurrent_tasks: int = Field(default=2, ge=1, le=10)
    
    @field_validator('gemini_api_key') # Updated decorator
    @classmethod # Added classmethod decorator as per Pydantic V2 style for field_validator
    def validate_api_key(cls, v):
        if not v:
            raise ValueError('Gemini API key is required')
        # Allow placeholder values for testing/development
        if v.startswith('your_') and len(v) < 20:
            # This is a placeholder, warn but don't fail
            pass
        elif len(v) < 10:
            raise ValueError('Valid Gemini API key is required')
        return v
    
    @field_validator('logging') # Updated decorator
    @classmethod # Added classmethod decorator as per Pydantic V2 style for field_validator
    def validate_logging_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.level.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        v.level = v.level.upper()
        return v


class ConfigLoader:
    """Loads and manages AIVA CLI configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the config loader.
        
        Args:
            config_dir: Directory containing config files. Defaults to current dir/config
        """
        if config_dir is None:
            # Try multiple locations for config directory
            possible_dirs = [
                Path.cwd() / "config",
                Path.cwd() / "aiva_cli" / "config",
                Path(__file__).parent
            ]
            
            for dir_path in possible_dirs:
                if dir_path.exists():
                    config_dir = dir_path
                    break
            else:
                config_dir = Path.cwd() / "config"
        
        self.config_dir = Path(config_dir)
        self.env_file = self.config_dir / ".env"
        self.settings_file = self.config_dir / "settings.json"
        
    def load_env_vars(self) -> Dict[str, Any]:
        """Load environment variables from .env file."""
        env_vars = {}
        
        # Load from .env file if it exists
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Extract relevant environment variables
        env_mapping = {
            'GEMINI_API_KEY': 'gemini_api_key',
            'MODEL_TEXT': 'models.text_model',
            'MODEL_IMAGE': 'models.image_model',
            'MODEL_TEMPERATURE': 'models.temperature',
            'MODEL_MAX_TOKENS': 'models.max_tokens',
            'MODEL_TIMEOUT': 'models.timeout',
            'SCRIPT_LENGTH': 'content.script_length',
            'SEGMENT_DURATION': 'content.segment_duration',
            'TOTAL_DURATION': 'content.total_duration',
            'TARGET_AUDIENCE': 'content.target_audience',
            'CONTENT_STYLE': 'content.content_style',
            'IMAGE_QUALITY': 'content.image_quality',
            'IMAGE_STYLE': 'content.image_style',
            'LOG_LEVEL': 'logging.level',
            'LOG_FORMAT': 'logging.format',
            'LOG_FILE_ENABLED': 'logging.file_enabled',
            'LOG_CONSOLE_ENABLED': 'logging.console_enabled',
            'LOG_DIR': 'logging.log_dir',
            'OUTPUT_BASE_DIR': 'output.base_dir',
            'OUTPUT_CREATE_MANIFEST': 'output.create_manifest',
            'OUTPUT_IMAGE_FORMAT': 'output.image_format',
            'DEBUG': 'debug',
            'MAX_RETRIES': 'max_retries',
            'CONCURRENT_TASKS': 'concurrent_tasks'
        }
        
        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                # Convert string values to appropriate types
                if env_key in ['MODEL_TEMPERATURE']:
                    value = float(value)
                elif env_key in ['MODEL_MAX_TOKENS', 'MODEL_TIMEOUT', 'SCRIPT_LENGTH', 
                               'SEGMENT_DURATION', 'TOTAL_DURATION', 'MAX_RETRIES', 'CONCURRENT_TASKS']:
                    value = int(value)
                elif env_key in ['LOG_FILE_ENABLED', 'LOG_CONSOLE_ENABLED', 
                               'OUTPUT_CREATE_MANIFEST', 'DEBUG']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self._set_nested_value(env_vars, config_key, value)
        
        return env_vars
    
    def load_settings_json(self) -> Dict[str, Any]:
        """Load settings from settings.json file."""
        if not self.settings_file.exists():
            return {}
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Error loading settings.json: {e}")
    
    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """Set a nested dictionary value using dot notation."""
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_config(self) -> AIVASettings:
        """Load complete configuration from all sources."""
        try:
            # Load base configuration from settings.json
            settings_config = self.load_settings_json()
            
            # Load environment variables
            env_config = self.load_env_vars()
            
            # Merge configurations (env vars override settings.json)
            merged_config = self._merge_configs(settings_config, env_config)
            
            # Convert agents dict to list format if needed
            if 'agents' in merged_config and isinstance(merged_config['agents'], dict):
                agents_list = []
                for name, agent_config in merged_config['agents'].items():
                    agent_data = agent_config.copy()
                    agent_data['name'] = name
                    agents_list.append(agent_data)
                merged_config['agents'] = agents_list
            
            # Create and validate Pydantic model
            return AIVASettings(**merged_config)
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    def validate_config(self, config: AIVASettings) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check API key
        if not config.gemini_api_key or config.gemini_api_key.startswith('your_'):
            issues.append("Gemini API key is not configured")
        
        # Check directories exist
        log_dir = Path(config.logging.log_dir)
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create log directory: {e}")
        
        output_dir = Path(config.output.base_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create output directory: {e}")
        
        return issues


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None
_cached_config: Optional[AIVASettings] = None


def get_config_loader(config_dir: Optional[Path] = None) -> ConfigLoader:
    """Get or create the global config loader instance."""
    global _config_loader
    if _config_loader is None or config_dir is not None:
        _config_loader = ConfigLoader(config_dir)
    return _config_loader


def get_gemini_api_key() -> str:
    """
    Get the Gemini API key from configuration.
    
    Returns:
        str: The Gemini API key
        
    Raises:
        ValueError: If the API key is not configured or is invalid
    """
    try:
        config = load_config()
        api_key = config.gemini_api_key
        
        if not api_key or api_key.strip() == "":
            raise ValueError("Gemini API key is not configured")
            
        if api_key == "your_gemini_api_key_here":
            raise ValueError("Please set a valid Gemini API key in your configuration")
            
        return api_key
    except Exception as e:
        raise ValueError(f"Failed to retrieve Gemini API key: {str(e)}")


def load_config(config_dir: Optional[Path] = None, force_reload: bool = False) -> AIVASettings:
    """Load configuration using the global config loader."""
    global _cached_config
    
    if _cached_config is None or force_reload:
        loader = get_config_loader(config_dir)
        _cached_config = loader.load_config()
    
    return _cached_config


def validate_config(config: Optional[AIVASettings] = None) -> List[str]:
    """Validate configuration and return list of issues."""
    if config is None:
        config = load_config()
    
    loader = get_config_loader()
    return loader.validate_config(config)