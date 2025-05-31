# Gemini API Abstractions Guide

This guide covers the Gemini API abstractions implemented in AIVA CLI for text and image generation.

## Overview

The AIVA CLI provides clean, robust abstractions for Google's Gemini API with built-in retry logic, error handling, and centralized configuration management.

## Features

### Text Generation (`models/text_model.py`)

- **GeminiTextModel**: Wrapper for Gemini Pro text generation
- **Retry Logic**: Exponential backoff with 3 retry attempts
- **Error Handling**: Comprehensive error handling with descriptive messages
- **Configuration**: Centralized configuration loading
- **Validation**: Input validation and connection testing

### Image Generation (`models/image_model.py`)

- **GeminiImageModel**: Wrapper for Gemini Imagen 3 image generation
- **Automatic Saving**: PNG format with automatic file naming
- **Batch Generation**: Support for multiple image generation
- **Path Handling**: Flexible output path management
- **Retry Logic**: Same robust retry mechanism as text model

### Centralized Configuration (`config/loader.py`)

- **get_gemini_api_key()**: Centralized API key retrieval
- **Validation**: API key validation and error handling
- **Security**: Prevents exposure of placeholder keys

## Usage Examples

### Text Generation

```python
from aiva_cli.models.text_model import GeminiTextModel, generate_text

# Using the class directly
text_model = GeminiTextModel()
response = text_model.generate_text(
    "Write a short story about AI",
    temperature=0.7,
    max_tokens=1000
)

# Using the convenience function
response = generate_text("Explain quantum computing", temperature=0.5)
```

### Image Generation

```python
from aiva_cli.models.image_model import GeminiImageModel, generate_image
from pathlib import Path

# Using the class directly
image_model = GeminiImageModel()
output_path = image_model.generate_image(
    "A beautiful sunset over mountains",
    Path("./outputs/sunset.png")
)

# Using the convenience function
output_path = generate_image(
    "A futuristic city",
    Path("./outputs/city.png")
)

# Generate multiple images
prompts = ["Ocean waves", "Forest path", "Desert dunes"]
results = image_model.generate_multiple_images(prompts, Path("./outputs/"))
```

### API Key Configuration

```python
from aiva_cli.config.loader import get_gemini_api_key

# Get the configured API key
try:
    api_key = get_gemini_api_key()
    print(f"API key loaded: {api_key[:10]}...")
except ValueError as e:
    print(f"API key error: {e}")
```

## Configuration

### Settings File (`settings.json`)

```json
{
  "gemini_api_key": "your_actual_api_key_here",
  "models": {
    "text_model": "gemini-1.5-flash",
    "image_model": "imagen-3.0-generate-001",
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 30
  },
  "max_retries": 3
}
```

### Environment Variables

```bash
export GEMINI_API_KEY="your_actual_api_key_here"
export AIVA_TEXT_MODEL="gemini-1.5-flash"
export AIVA_IMAGE_MODEL="imagen-3.0-generate-001"
```

## Error Handling

### Common Errors

1. **Missing API Key**

   ```python
   ValueError: Gemini API key is not configured
   ```

2. **Invalid API Key**

   ```python
   ValueError: Please set a valid Gemini API key in your configuration
   ```

3. **Network/API Errors**

   ```python
   RuntimeError: Text generation failed after 3 attempts: [error details]
   ```

4. **Empty Response**
   ```python
   RuntimeError: Empty response from Gemini API
   ```

### Retry Logic

Both models implement exponential backoff:

- **Attempt 1**: Immediate
- **Attempt 2**: 1 second delay
- **Attempt 3**: 2 seconds delay
- **Attempt 4**: 4 seconds delay
- **Maximum delay**: 60 seconds

## Testing

### Unit Tests

Comprehensive unit tests with HTTP mocking:

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run text model tests
python -m pytest tests/test_text_model.py -v

# Run image model tests
python -m pytest tests/test_image_model.py -v

# Run all tests
python -m pytest tests/ -v
```

### Integration Testing

The models include validation methods:

```python
# Test text model connection
text_model = GeminiTextModel()
if text_model.validate_connection():
    print("Text model connection successful")

# Test image model connection
image_model = GeminiImageModel()
if image_model.validate_connection():
    print("Image model connection successful")
```

## Dependencies

### Required Packages

```bash
pip install google-generativeai>=0.3.0
pip install Pillow>=9.0.0
```

### Development Dependencies

```bash
pip install pytest>=7.0.0
pip install pytest-mock>=3.10.0
```

## Model Information

### Get Model Details

```python
# Text model info
text_model = GeminiTextModel()
info = text_model.get_model_info()
print(f"Model: {info['model_name']}")
print(f"Temperature: {info['temperature']}")
print(f"Max tokens: {info['max_tokens']}")

# Image model info
image_model = GeminiImageModel()
info = image_model.get_model_info()
print(f"Model: {info['model_name']}")
print(f"Timeout: {info['timeout']}")
```

## Best Practices

1. **API Key Security**

   - Never hardcode API keys in source code
   - Use environment variables or secure configuration files
   - Validate API keys before use

2. **Error Handling**

   - Always wrap API calls in try-catch blocks
   - Handle rate limiting gracefully
   - Provide meaningful error messages to users

3. **Resource Management**

   - Use appropriate timeouts
   - Implement proper retry logic
   - Monitor API usage and costs

4. **Testing**
   - Use mocking for unit tests
   - Test error scenarios
   - Validate input parameters

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   pip install google-generativeai
   ```

2. **API Key Issues**

   - Check configuration files
   - Verify environment variables
   - Ensure API key is valid and active

3. **Network Issues**

   - Check internet connectivity
   - Verify firewall settings
   - Consider proxy configuration

4. **File Permission Issues**
   - Ensure write permissions for output directories
   - Check disk space availability

## Support

For issues and questions:

1. Check the error messages for specific guidance
2. Review the configuration settings
3. Consult the Google Generative AI documentation
4. Check the AIVA CLI logs for detailed error information
