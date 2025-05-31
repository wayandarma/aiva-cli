# AIVA CLI - Interactive Interface

A user-friendly command-line interface for generating AI-powered video content with interactive menus and easy navigation.

## ⚠️ Prerequisites

**IMPORTANT:** You must complete the setup process before using the CLI. The CLI does not include setup functionality.

## 🛠️ Setup Instructions

### Option 1: Conda Setup (Recommended)

1. **Create conda environment:**

   ```bash
   conda env create -f environment.yml
   conda activate aiva-cli
   ```

2. **Configure API key:**

   - Edit `aiva_cli/config/.env`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

### Option 2: Pip Setup

1. **Install dependencies:**

   ```bash
   pip install google-generativeai pillow typer rich python-dotenv pydantic requests
   ```

2. **Configure API key:**

   - Edit `aiva_cli/config/.env`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## 🚀 Launching the CLI

**After completing setup**, launch the interactive CLI:

```bash
# Make sure your conda environment is activated
conda activate aiva-cli

# Launch the interactive CLI
python cli.py
```

**Note:** The CLI will check for dependencies and guide you if anything is missing.

## 🎯 Features

### Interactive Menu System

- **🚀 Generate Video Content** - Create AI-powered video projects
- **📋 List Recent Projects** - View your generated content
- **🔧 Check Configuration** - Verify settings and API keys
- **📊 View System Status** - Check dependencies and system health
- **📖 Help & Documentation** - Get detailed usage information
- **🚪 Exit** - Close the application

### User-Friendly Experience

- ✅ Simple `python cli.py` command to start
- ✅ Interactive menu navigation
- ✅ Continuous operation with while loops
- ✅ Type "6" or Ctrl+C to exit gracefully
- ✅ Clear status messages and progress indicators
- ✅ Automatic project organization

## 📁 Project Structure

Each generated video project contains:

```
output/Your_Project_Name_TIMESTAMP/
├── manifest.json          # Project metadata
├── segments.json          # Segment information
├── transcript.txt         # Full video transcript
├── state.json            # Generation state
└── segment_XX/           # Individual segments
    ├── script.txt        # Segment script
    ├── prompt.txt        # Image generation prompt
    └── image.png         # AI-generated image
```

## 🔧 Configuration

### API Key Setup

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Edit `aiva_cli/config/.env`:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Settings Customization

Edit `aiva_cli/config/settings.json` to customize:

- AI model parameters
- Segmentation settings (target segments, duration)
- Output preferences
- Image generation settings

## 🎮 Usage Examples

### Basic Video Generation

1. Run `python cli.py`
2. Select option "1" (Generate Video Content)
3. Enter your topic: "How to make the perfect coffee"
4. Choose verbose mode (optional)
5. Wait for generation to complete
6. Find your project in the `output/` directory

### Managing Projects

1. Select option "2" (List Recent Projects)
2. View all your generated content with file sizes
3. Navigate to project folders to access files

## 🛠️ Troubleshooting

### Common Issues

**"Module not found" errors:**

```bash
# Ensure you're in the project directory
cd /path/to/your/project

# Activate conda environment
conda activate aiva-cli

# Or reinstall dependencies
pip install -r requirements.txt
```

**API key issues:**

- Verify your Gemini API key is valid
- Check the `.env` file format
- Ensure no extra spaces or quotes around the key

**Generation failures:**

- Check internet connection
- Verify API key has sufficient quota
- Try with a simpler topic first

### System Status Check

Use option "4" in the CLI menu to check:

- Python version
- Dependency status
- Configuration validity
- Output directory status

## 📋 Dependencies

- **Python 3.9+**
- **google-generativeai** - Gemini API integration
- **pillow** - Image processing
- **typer** - CLI framework
- **rich** - Beautiful terminal output
- **python-dotenv** - Environment variable management
- **pydantic** - Data validation
- **requests** - HTTP requests

## 🎯 Tips for Best Results

1. **Use descriptive topics:**

   - ✅ "Complete guide to brewing espresso at home"
   - ❌ "Coffee"

2. **Enable verbose mode** to see detailed progress

3. **Check configuration** before generating large projects

4. **Keep topics focused** for better segment organization

5. **Review generated content** in the output directory

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Use the "View System Status" option in the CLI
3. Verify your configuration with "Check Configuration"
4. Review the help documentation with option "5"

## 🎉 What's New

- **Simple CLI access** - Just `python cli.py` to start
- **Interactive menus** - No more complex command arguments
- **Continuous operation** - Stay in the app until you choose to exit
- **Better project management** - Easy access to recent projects
- **Improved setup** - Automated conda environment creation
- **Enhanced user experience** - Clear status messages and help

Enjoy creating amazing AI-powered video content! 🎬✨
