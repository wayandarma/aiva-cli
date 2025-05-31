# AIVA CLI - AI Video Assistant

🎬 **AI-powered YouTube content generator** that creates complete video packages including scripts, visual prompts, and AI-generated images.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd aiva-cli

# Create virtual environment
python -m venv aiva_env
source aiva_env/bin/activate  # On Windows: aiva_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python aiva_cli/cli.py init
```

### Basic Usage

```bash
# Generate content for a topic
python aiva_cli/cli.py generate "The Future of Artificial Intelligence"

# Generate short-form content
python aiva_cli/cli.py generate "Quick AI Tips" --type short

# Custom output directory
python aiva_cli/cli.py generate "Machine Learning Basics" --output-dir ./my_videos

# Dry run to preview generation plan
python aiva_cli/cli.py generate "Climate Change Solutions" --dry-run

# Verbose output for debugging
python aiva_cli/cli.py generate "Space Exploration" --verbose --dry-run

# Check system status
python aiva_cli/cli.py status

# Get help
python aiva_cli/cli.py --help
python aiva_cli/cli.py generate --help
```

## Features

- 🤖 **Multi-Agent System**: Script Writer, Director, Visual Designer, and Image Generator
- 📝 **Smart Script Generation**: Creates engaging 5-minute YouTube scripts
- ✂️ **Automatic Segmentation**: Breaks content into 38 timed segments (8 seconds each)
- 🎨 **Visual Prompt Creation**: Generates cinematic visual descriptions
- 🖼️ **AI Image Generation**: Creates high-quality images for each segment
- ⚙️ **Flexible Configuration**: Environment-based settings with JSON config
- 📊 **Structured Logging**: JSON-formatted logs with daily rotation
- 🔍 **Dry Run Mode**: Preview generation plans without API calls

## Configuration

AIVA CLI uses a combination of environment variables (`.env`) and JSON settings (`config/settings.json`):

### Environment Variables (.env)

```bash
# API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Custom settings
AIVA_LOG_LEVEL=INFO
AIVA_OUTPUT_DIR=projects
```

### Settings File (config/settings.json)

The settings file contains default configurations for agents, output formats, and generation parameters. It's automatically created during initialization.

## Project Structure

```
aiva_cli/
├── cli.py              # Main CLI interface
├── config/
│   └── loader.py       # Configuration management
├── logs/
│   └── logger.py       # Structured logging system
├── core/               # Core business logic (Phase 3+)
├── crew_config/        # CrewAI agent configurations (Phase 4+)
├── models/             # Data models (Phase 5+)
└── projects/           # Generated content output

config/
├── .env               # Environment variables
└── settings.json      # Application settings

logs/                  # Application logs (auto-created)
```

## Development Status

- ✅ **Phase 1**: Project setup and basic CLI structure
- ✅ **Phase 2**: CLI implementation, config loader, and structured logging
- 🔄 **Phase 3**: Core infrastructure development (Next)
- ⏳ **Phase 4**: CrewAI agent system
- ⏳ **Phase 5**: Data models and validation
- ⏳ **Phase 6**: Complete workflow implementation

## Requirements

- Python 3.8+
- Google API key (for Gemini models)
- OpenAI API key (optional, for additional models)

## License

MIT License - see LICENSE file for details.
