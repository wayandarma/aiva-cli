# Fix for Image Model Issue

The issue you're experiencing is due to using an outdated Google AI package and incorrect model configuration. Here's how to fix it:

## Problem

The current implementation uses the old `google-generativeai` package which doesn't properly support Imagen 3 image generation. The error occurs because:

1. Wrong package: Using `google-generativeai` instead of `google-genai`
2. Incorrect API usage: The old package has different API methods
3. Wrong model name: Using `imagen-3.0-fast-generate-002` instead of `imagen-3.0-generate-002`

## Solution

### 1. Install the correct package

```bash
# Uninstall the old package
pip uninstall google-generativeai

# Install the new package
pip install google-genai
```

### 2. Updated files

I've already updated the following files for you:

- `aiva_cli/models/image_model.py` - Updated to use the new `google-genai` package
- `requirements.txt` - Changed dependency from `google-generativeai` to `google-genai`
- `aiva_cli/config/.env` - Fixed model name to `imagen-3.0-generate-002`

### 3. Key changes made

#### In `image_model.py`:

- Changed import from `import google.generativeai as genai` to `from google import genai`
- Added `from google.genai import types` import
- Updated client initialization to use `genai.Client(api_key=self.api_key)`
- Fixed image generation to use proper Imagen 3 API: `client.models.generate_images()`
- Removed placeholder image generation and implemented real image generation

#### In `.env`:

- Changed `MODEL_IMAGE=imagen-3.0-fast-generate-002` to `MODEL_IMAGE=imagen-3.0-generate-002`

### 4. What the fix does

The updated code now:

- Uses the correct Google AI package (`google-genai`)
- Properly calls the Imagen 3 API
- Generates real images instead of placeholder text images
- Handles image bytes correctly and saves them as actual image files

### 5. Next steps

1. Run `pip install google-genai` to install the correct package
2. Run your AIVA CLI again
3. The image generation should now work properly and create actual AI-generated images

### 6. Verification

After installing the new package, you can test the image generation by running your CLI again. The system should now:

- Generate actual AI images using Imagen 3
- Save them as proper image files (PNG format)
- Display success messages with file sizes
- Create the expected number of images (not 0 as shown in your error)

The "Created 0 images" message in your output should now show the actual number of generated images.
