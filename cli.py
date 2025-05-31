#!/usr/bin/env python3
"""
AIVA CLI - Interactive Command Line Interface
Simplified access to AI Video Generation Assistant
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import termios
import tty
import select

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    """Print the AIVA CLI banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🎬 AIVA CLI 🎬                           ║
║              AI Video Generation Assistant                   ║
║                                                              ║
║              Interactive Command Interface                   ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_menu(selected_index=0):
    """Display the main menu options with selection highlighting."""
    menu_options = [
        "🚀 Generate Video Content",
        "📁 List Recent Projects", 
        "🔧 Check Configuration",
        "📊 View System Status",
        "📖 Help & Documentation",
        "🚪 Exit"
    ]
    
    print("\n📋 Main Menu:")
    print("Use ↑/↓ arrow keys to navigate, Enter to select, or type number (1-6)")
    print("-" * 60)
    
    for i, option in enumerate(menu_options):
        if i == selected_index:
            print(f"  ► {i+1}. {option} ◄")
        else:
            print(f"    {i+1}. {option}")
    print("-" * 60)

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    # Check each dependency individually
    deps_to_check = [
        ('google.generativeai', 'Google Generative AI'),
        ('PIL', 'Pillow'),
        ('typer', 'Typer'),
        ('rich', 'Rich')
    ]
    
    for module_name, display_name in deps_to_check:
        try:
            __import__(module_name)
        except ImportError:
            missing_deps.append(display_name)
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("\n💡 Please check the README_CLI.md for setup instructions.")
        print("   Make sure you have activated the conda environment and installed all dependencies.")
        return False
    
    return True

def select_video_type():
    """Interactive video type selection."""
    video_types = [
        ("long-form", "🎬 Long-form Video (10+ minutes, detailed content)"),
        ("short", "📱 Short Video (< 1 minute, quick content)")
    ]
    
    print("\n🎬 Select Video Type:")
    print("-" * 30)
    
    for i, (type_key, description) in enumerate(video_types, 1):
        print(f"{i}. {description}")
    
    while True:
        choice = input("\n👉 Select video type (1-2): ").strip()
        if choice == '1':
            return 'long-form'
        elif choice == '2':
            return 'short'
        else:
            print("❌ Please choose 1 or 2")

def get_generation_options():
    """Get generation options from user with enhanced interface."""
    options = {}
    
    # Get topic
    while True:
        topic = input("\n📝 Enter your video topic: ").strip()
        if topic:
            if len(topic) < 3:
                print("❌ Topic must be at least 3 characters long")
                continue
            elif len(topic) > 200:
                print("❌ Topic must be less than 200 characters")
                continue
            options['topic'] = topic
            break
        else:
            print("❌ Topic cannot be empty!")
    
    # Get custom title (optional)
    title = input("\n📰 Custom title (optional, press Enter to auto-generate): ").strip()
    if title:
        if len(title) > 100:
            print("⚠️  Title truncated to 100 characters")
            title = title[:100]
        options['title'] = title
    
    # Select video type
    options['video_type'] = select_video_type()
    
    # Ask for verbose mode
    while True:
        verbose_input = input("\n🔍 Enable verbose mode? (y/N): ").strip().lower()
        if verbose_input in ['y', 'yes']:
            options['verbose'] = True
            break
        elif verbose_input in ['n', 'no', '']:
            options['verbose'] = False
            break
        else:
            print("❌ Please enter 'y' for yes or 'n' for no")
    
    # Ask for custom output directory
    while True:
        output_input = input("\n📁 Custom output directory (optional, press Enter for default): ").strip()
        if not output_input:
            break
        else:
            output_path = Path(output_input)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                options['output_dir'] = str(output_path)
                print(f"✅ Output directory set to: {output_path}")
                break
            except (PermissionError, OSError) as e:
                print(f"❌ Cannot create directory '{output_input}': {e}")
                retry = input("Try again? (y/N): ").strip().lower()
                if retry not in ['y', 'yes']:
                    break
    
    return options

def generate_video_content():
    """Handle video content generation with enhanced options."""
    print("\n🎬 Video Content Generation")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        return
    
    # Get generation options
    options = get_generation_options()
    
    # Show summary
    print("\n📋 Generation Summary:")
    print("-" * 25)
    print(f"🎯 Topic: {options['topic']}")
    if 'title' in options:
        print(f"📰 Title: {options['title']}")
    print(f"🎬 Type: {options['video_type']}")
    if 'output_dir' in options:
        print(f"📁 Output: {options['output_dir']}")
    print(f"🔍 Verbose: {'Yes' if options['verbose'] else 'No'}")
    
    # Confirm generation
    while True:
        confirm = input("\n👉 Proceed with generation? (Y/n): ").strip().lower()
        if confirm in ['y', 'yes', '']:
            break
        elif confirm in ['n', 'no']:
            print("❌ Generation cancelled")
            return
        else:
            print("❌ Please enter 'y' for yes or 'n' for no")
    
    print(f"\n🚀 Starting generation for: '{options['topic']}'")
    if 'title' in options:
        print(f"📰 Using custom title: '{options['title']}'")
    print(f"🎬 Video type: {options['video_type']}")
    if options['verbose']:
        print("📊 Verbose mode enabled")
    
    print("\n⏳ This may take a few minutes...")
    print("" * 50)
    
    try:
        # Import and call the generation function directly
        from aiva_cli.core.pipeline import generate_content
        from aiva_cli.config.loader import load_config
        
        # Load configuration
        config = load_config()
        
        # Determine output directory
        if 'output_dir' in options:
            out_dir = Path(options['output_dir'])
        else:
            out_dir = project_root / "output"
        
        # Call the generation pipeline directly
        result = generate_content(
            topic=options['topic'],
            video_type=options['video_type'],
            output_dir=out_dir,
            title=options.get('title'),
            config=config
        )
        
        if result and result.get('status') == 'success':
            print("\n✅ Video content generation completed successfully!")
            print("📁 Check the 'output' directory for your generated content.")
            print(f"📍 Project: {result.get('project_title', 'Unknown')}")
            print(f"📂 Output directory: {result.get('output_dir', out_dir)}")
            if result.get('segments_processed'):
                print(f"🎬 Generated {result['segments_processed']} segments")
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'Pipeline returned no result'
            print(f"\n❌ Generation failed: {error_msg}")
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure the AIVA CLI module is properly installed.")
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        print("💡 Make sure all dependencies are installed and configured properly.")

def show_project_details(project):
    """Show detailed information about a specific project."""
    print(f"\n📁 Project Details: {project.name}")
    print("=" * 50)
    
    # Get project info
    mod_time = datetime.fromtimestamp(project.stat().st_mtime)
    
    # Count files in project
    all_files = list(project.rglob('*'))
    file_count = sum(1 for f in all_files if f.is_file())
    image_count = sum(1 for f in all_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg'])
    script_count = sum(1 for f in all_files if f.name == 'script.txt')
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in all_files if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print(f"📅 Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📄 Total Files: {file_count}")
    print(f"🖼️  Images: {image_count}")
    print(f"📝 Scripts: {script_count}")
    print(f"💾 Size: {size_mb:.1f} MB")
    print(f"📍 Path: {project}")
    
    # Check for manifest file
    manifest_file = project / "manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                print(f"\n📋 Manifest Information:")
                if 'topic' in manifest:
                    print(f"  🎯 Topic: {manifest['topic']}")
                if 'title' in manifest:
                    print(f"  📰 Title: {manifest['title']}")
                if 'video_type' in manifest:
                    print(f"  🎬 Type: {manifest['video_type']}")
                if 'segments_count' in manifest:
                    print(f"  🎞️  Segments: {manifest['segments_count']}")
                if 'generation_time' in manifest:
                    print(f"  ⏱️  Generation Time: {manifest['generation_time']}s")
        except Exception as e:
            print(f"  ⚠️  Error reading manifest: {e}")
    
    # Show segment structure
    segments = [d for d in project.iterdir() if d.is_dir() and d.name.startswith('segment_')]
    if segments:
        segments.sort(key=lambda x: int(x.name.split('_')[1]))
        print(f"\n🎞️  Segments ({len(segments)} total):")
        for i, segment in enumerate(segments[:5], 1):  # Show first 5 segments
            segment_files = list(segment.iterdir())
            has_image = any(f.suffix.lower() in ['.png', '.jpg', '.jpeg'] for f in segment_files)
            has_script = any(f.name == 'script.txt' for f in segment_files)
            has_prompt = any(f.name == 'prompt.txt' for f in segment_files)
            
            status_icons = []
            if has_script: status_icons.append('📝')
            if has_prompt: status_icons.append('💭')
            if has_image: status_icons.append('🖼️')
            
            print(f"  {segment.name}: {' '.join(status_icons) if status_icons else '❌'}")
        
        if len(segments) > 5:
            print(f"  ... and {len(segments) - 5} more segments")

def list_recent_projects():
    """List recent projects with enhanced selection."""
    print("\n📁 Recent Projects")
    print("=" * 30)
    
    selected_project = enhanced_project_selector()
    
    if selected_project is None:
        return
    elif selected_project == 'all':
        # Show all projects with basic info
        output_dir = project_root / "output"
        projects = [d for d in output_dir.iterdir() if d.is_dir()]
        projects.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print(f"\n📊 All Projects ({len(projects)} total):\n")
        
        for i, project in enumerate(projects, 1):
            mod_time = datetime.fromtimestamp(project.stat().st_mtime)
            all_files = list(project.rglob('*'))
            file_count = sum(1 for f in all_files if f.is_file())
            image_count = sum(1 for f in all_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg'])
            total_size = sum(f.stat().st_size for f in all_files if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            print(f"{i:2d}. 📁 {project.name}")
            print(f"    📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    📄 {file_count} files ({image_count} images) - {size_mb:.1f} MB")
            
            # Show topic if available
            manifest_file = project / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                        if 'topic' in manifest:
                            print(f"    🎯 {manifest['topic']}")
                except:
                    pass
            print()
    else:
        # Show detailed info for selected project
        show_project_details(selected_project)
        
        # Ask if user wants to open the project folder
        while True:
            action = input("\n👉 Open project folder? (y/N): ").strip().lower()
            if action in ['y', 'yes']:
                try:
                    subprocess.run(['open', str(selected_project)], check=True)
                    print("✅ Project folder opened in Finder")
                except subprocess.CalledProcessError:
                    print(f"📍 Project location: {selected_project}")
                except FileNotFoundError:
                    print(f"📍 Project location: {selected_project}")
                break
            elif action in ['n', 'no', '']:
                break
            else:
                print("❌ Please enter 'y' for yes or 'n' for no")

def configuration_menu():
    """Interactive configuration menu."""
    config_options = [
        ("check", "🔍 Check Current Configuration"),
        ("edit", "✏️  Edit Configuration File"),
        ("test", "🧪 Test API Connection"),
        ("reset", "🔄 Reset to Default Settings")
    ]
    
    print("\n🔧 Configuration Options:")
    print("-" * 30)
    
    for i, (key, description) in enumerate(config_options, 1):
        print(f"{i}. {description}")
    
    while True:
        choice = input("\n👉 Select option (1-4) or 'b' to go back: ").strip().lower()
        if choice == '1' or choice == 'check':
            return 'check'
        elif choice == '2' or choice == 'edit':
            return 'edit'
        elif choice == '3' or choice == 'test':
            return 'test'
        elif choice == '4' or choice == 'reset':
            return 'reset'
        elif choice == 'b' or choice == 'back':
            return None
        else:
            print("❌ Please choose 1-4 or 'b' to go back")

def test_api_connection():
    """Test API connection with detailed feedback."""
    print("\n🧪 Testing API Connection")
    print("=" * 30)
    
    env_file = project_root / "aiva_cli" / "config" / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Run configuration setup first")
        return
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            
        # Extract API key
        api_key = None
        for line in content.split('\n'):
            if line.startswith('GEMINI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
        
        if not api_key or api_key == 'your_api_key_here':
            print("❌ API key not configured")
            print("💡 Please set your GEMINI_API_KEY in the .env file")
            return
        
        print("🔑 API key found, testing connection...")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Test by listing models
            models = list(genai.list_models())
            print(f"✅ Connection successful! Found {len(models)} available models")
            
            # Show some model info
            text_models = [m for m in models if 'gemini' in m.name.lower() and 'pro' in m.name.lower()]
            if text_models:
                print(f"📝 Text models available: {len(text_models)}")
            
            image_models = [m for m in models if 'imagen' in m.name.lower()]
            if image_models:
                print(f"🖼️  Image models available: {len(image_models)}")
            else:
                print("⚠️  No image models found - image generation may not work")
                
        except ImportError:
            print("❌ google-generativeai package not installed")
            print("💡 Install with: pip install google-generativeai")
        except Exception as e:
            print(f"❌ API connection failed: {str(e)}")
            print("💡 Check your API key and internet connection")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

def edit_configuration():
    """Open configuration file for editing."""
    print("\n✏️  Edit Configuration")
    print("=" * 25)
    
    env_file = project_root / "aiva_cli" / "config" / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found")
        create = input("Create new .env file? (y/N): ").strip().lower()
        if create in ['y', 'yes']:
            template_file = project_root / "aiva_cli" / "config" / ".env.template"
            if template_file.exists():
                import shutil
                shutil.copy2(template_file, env_file)
                print(f"✅ Created .env file from template")
            else:
                print("❌ Template file not found")
                return
        else:
            return
    
    print(f"📍 Configuration file: {env_file}")
    
    # Try to open with system editor
    editors = ['code', 'nano', 'vim', 'open']
    
    for editor in editors:
        try:
            subprocess.run([editor, str(env_file)], check=True)
            print(f"✅ Opened with {editor}")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("⚠️  Could not open editor automatically")
    print(f"📝 Please edit manually: {env_file}")

def reset_configuration():
    """Reset configuration to default settings."""
    print("\n🔄 Reset Configuration")
    print("=" * 25)
    
    print("⚠️  This will reset your configuration to defaults")
    print("❗ Your current API key and settings will be lost")
    
    confirm = input("\nAre you sure you want to continue? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Reset cancelled")
        return
    
    env_file = project_root / "aiva_cli" / "config" / ".env"
    template_file = project_root / "aiva_cli" / "config" / ".env.template"
    
    try:
        if template_file.exists():
            import shutil
            shutil.copy2(template_file, env_file)
            print("✅ Configuration reset to defaults")
            print("💡 Please edit the .env file and add your API key")
        else:
            print("❌ Template file not found")
            print("💡 Cannot reset - template missing")
    except Exception as e:
        print(f"❌ Error resetting configuration: {e}")

def check_configuration():
    """Enhanced configuration check with interactive options."""
    print("\n🔧 Configuration Management")
    print("=" * 35)
    
    action = configuration_menu()
    
    if action is None:
        return
    elif action == 'check':
        check_basic_configuration()
    elif action == 'edit':
        edit_configuration()
    elif action == 'test':
        test_api_connection()
    elif action == 'reset':
        reset_configuration()

def check_basic_configuration():
    """Check basic system configuration and API keys."""
    print("\n🔍 Configuration Status")
    print("=" * 30)
    
    # Check .env file
    env_file = project_root / "aiva_cli" / "config" / ".env"
    
    print("\n📋 Configuration Status:")
    
    if env_file.exists():
        print("✅ .env file found")
        
        # Check for API key (without revealing it)
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'GEMINI_API_KEY' in content and '=' in content:
                    # Check if there's a value after the equals sign
                    for line in content.split('\n'):
                        if line.startswith('GEMINI_API_KEY='):
                            key_value = line.split('=', 1)[1].strip()
                            if key_value and key_value != 'your_api_key_here':
                                print("✅ Gemini API key configured")
                                # Test API key validity
                                try:
                                    import google.generativeai as genai
                                    genai.configure(api_key=key_value)
                                    models = list(genai.list_models())
                                    print("✅ API key is valid and working")
                                except ImportError:
                                    print("⚠️  Cannot test API key - google.generativeai not installed")
                                except Exception as e:
                                    print(f"⚠️  API key configured but may be invalid: {str(e)[:50]}...")
                            else:
                                print("❌ Gemini API key not set or using placeholder")
                                print("💡 Edit aiva_cli/config/.env and add your API key")
                            break
                    else:
                        print("❌ GEMINI_API_KEY not found in .env file")
                else:
                    print("❌ GEMINI_API_KEY not found in .env file")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ .env file not found")
        print("💡 Copy .env.template to .env and configure your API key")
    
    # Check settings file
    settings_file = project_root / "aiva_cli" / "config" / "settings.json"
    if settings_file.exists():
        print("✅ Settings file found")
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                print(f"✅ Settings loaded successfully ({len(settings)} sections)")
        except Exception as e:
            print(f"⚠️  Settings file exists but has errors: {e}")
    else:
        print("⚠️  Settings file not found (will use defaults)")
    
    # Check output directory
    output_dir = project_root / "output"
    if output_dir.exists():
        print("✅ Output directory exists")
        project_count = len([d for d in output_dir.iterdir() if d.is_dir()])
        print(f"📊 Contains {project_count} project(s)")
    else:
        print("⚠️  Output directory will be created when needed")
    
    # Check if AIVA CLI module can be imported
    try:
        import aiva_cli.cli
        print("✅ AIVA CLI module can be imported")
    except ImportError as e:
        print(f"⚠️  Cannot import AIVA CLI module: {e}")
        print("💡 This is expected if dependencies are not installed")

def view_system_status():
    """View system status and dependencies."""
    print("\n📊 System Status")
    print("=" * 25)
    
    # Python version
    print(f"\n🐍 Python Version: {sys.version.split()[0]}")
    
    # Check if we're in a conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"🐍 Conda Environment: {conda_env}")
    else:
        print("🐍 Conda Environment: Not detected")
    
    # Check dependencies
    dependencies = [
        ('google.generativeai', 'Google Generative AI'),
        ('PIL', 'Pillow (Image processing)'),
        ('typer', 'Typer (CLI framework)'),
        ('rich', 'Rich (Terminal formatting)'),
        ('dotenv', 'Python-dotenv (Environment variables)'),
        ('pydantic', 'Pydantic (Data validation)'),
        ('requests', 'Requests (HTTP client)')
    ]
    
    print("\n📦 Dependencies:")
    missing_deps = []
    for dep_module, dep_name in dependencies:
        try:
            module = __import__(dep_module)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep_name} ({version})")
        except ImportError:
            print(f"❌ {dep_name} (not installed)")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n⚠️  Missing {len(missing_deps)} dependencies")
        print("💡 Check README_CLI.md for installation instructions")
    
    # Check project structure
    print("\n📁 Project Structure:")
    important_paths = [
        ("aiva_cli/", "Main package directory"),
        ("aiva_cli/cli.py", "CLI entry point"),
        ("aiva_cli/config/", "Configuration directory"),
        ("aiva_cli/config/.env.template", "Environment template"),
        ("aiva_cli/core/", "Core modules"),
        ("aiva_cli/models/", "AI models"),
        ("aiva_cli/crew_config/", "Agent configuration")
    ]
    
    for path, description in important_paths:
        full_path = project_root / path
        if full_path.exists():
            print(f"✅ {path} - {description}")
        else:
            print(f"❌ {path} - {description} (missing)")
    
    # Memory and disk usage
    print("\n💾 System Resources:")
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        print(f"🧠 Memory: {memory.percent}% used ({memory.available // (1024**3)} GB available)")
        print(f"💿 Disk: {disk.percent}% used ({disk.free // (1024**3)} GB available)")
    except ImportError:
        print("⚠️  psutil not installed - cannot show system resource info")
        print("💡 Install psutil for detailed system info")

def show_help():
    """Show help and documentation."""
    print("\n📖 Help & Documentation")
    print("=" * 35)
    
    help_text = """
🎯 AIVA CLI Usage Guide:

1. 🚀 Generate Video Content:
   - Enter a descriptive topic for your video
   - Choose verbose mode for detailed progress
   - Generated content will be saved in 'output/' directory
   - Each project includes scripts, images, and metadata

2. 📁 List Recent Projects:
   - View all your generated video projects
   - See creation dates, file counts, and sizes
   - Navigate to project folders to access files
   - View project topics from manifest files

3. 🔧 Check Configuration:
   - Verify your API key is set up correctly
   - Test API key validity with Google services
   - Check if all required files are present
   - Troubleshoot configuration issues

4. 📊 View System Status:
   - Check Python version and conda environment
   - Verify all dependencies are installed with versions
   - Check project structure integrity
   - View system resource usage
   - Diagnose installation problems

💡 Tips for Best Results:
   • Use descriptive, specific topics (e.g., "Complete guide to brewing espresso")
   • Ensure stable internet connection for API calls
   • Check API key quota if generation fails
   • Enable verbose mode for troubleshooting
   • Keep topics focused for better segment organization

🔧 Configuration Files:
   • 'aiva_cli/config/.env' - API keys and secrets
   • 'aiva_cli/config/settings.json' - Generation preferences
   • 'environment.yml' - Conda environment specification
   • 'README_CLI.md' - Detailed setup instructions

🆘 Troubleshooting:
   • Use option 3 to check configuration status
   • Use option 4 to verify system dependencies
   • Ensure conda environment 'aiva-cli' is activated
   • Check internet connection for API calls
   • Review generated logs in project directories
   • Check README_CLI.md for dependency installation instructions

🎬 Project Structure:
   Each generated project contains:
   • manifest.json - Project metadata and settings
   • segments.json - Segment breakdown information
   • transcript.txt - Complete video transcript
   • segment_XX/ - Individual segment folders
     ├── script.txt - Segment narration script
     ├── prompt.txt - Image generation prompt
     └── image.png - AI-generated visual content
    """
    
    print(help_text)

def get_key():
    """Get a single keypress from stdin with improved arrow key detection."""
    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            
            # Handle escape sequences (arrow keys)
            if key == '\x1b':  # ESC sequence
                # Check if more characters are available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key += sys.stdin.read(1)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key += sys.stdin.read(1)
                else:
                    # Just ESC key pressed
                    return key
            
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        # Fallback for systems without termios
        raise Exception("Terminal input not supported")

def interactive_menu():
    """Interactive menu with arrow key navigation."""
    selected_index = 0
    menu_functions = [
        generate_video_content,
        list_recent_projects,
        check_configuration,
        view_system_status,
        show_help,
        lambda: None  # Exit function
    ]
    
    while True:
        clear_screen()
        print_banner()
        show_menu(selected_index)
        
        print("\n💡 Navigation: ↑/↓ arrows, Enter to select, 'q' to quit, or type 1-6")
        
        try:
            # Get key input without showing prompt
            key = get_key()
            
            # Handle arrow keys
            if key == '\x1b[A':  # Up arrow
                selected_index = (selected_index - 1) % 6
                continue
            elif key == '\x1b[B':  # Down arrow
                selected_index = (selected_index + 1) % 6
                continue
            elif key == '\r' or key == '\n':  # Enter
                if selected_index == 5:  # Exit
                    print("\n👋 Thank you for using AIVA CLI!")
                    print("🎬 Happy video creating! ✨")
                    break
                else:
                    menu_functions[selected_index]()
                    input("\n⏸️  Press Enter to continue...")
                    continue
            
            # Handle direct number input
            elif key in ['1', '2', '3', '4', '5', '6']:
                choice_num = int(key) - 1
                if choice_num == 5:  # Exit
                    print("\n👋 Thank you for using AIVA CLI!")
                    print("🎬 Happy video creating! ✨")
                    break
                else:
                    menu_functions[choice_num]()
                    input("\n⏸️  Press Enter to continue...")
            
            # Handle quit command
            elif key.lower() in ['q']:
                print("\n👋 Thank you for using AIVA CLI!")
                print("🎬 Happy video creating! ✨")
                break
            
            # Handle escape key
            elif key == '\x1b':
                continue
            
            else:
                # For other keys, show error briefly
                print(f"\n❌ Invalid key. Use ↑/↓ arrows, Enter, 1-6, or 'q'")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using AIVA CLI!")
            break
        except Exception as e:
            # Fallback to traditional input method
            print("\n⚠️  Arrow keys not supported on this terminal")
            choice = input("👉 Enter choice (1-6) or 'q' to quit: ").strip().lower()
            
            if choice in ['1', '2', '3', '4', '5', '6']:
                choice_num = int(choice) - 1
                if choice_num == 5:  # Exit
                    print("\n👋 Thank you for using AIVA CLI!")
                    print("🎬 Happy video creating! ✨")
                    break
                else:
                    menu_functions[choice_num]()
                    input("\n⏸️  Press Enter to continue...")
            elif choice in ['q', 'quit', 'exit']:
                print("\n👋 Thank you for using AIVA CLI!")
                print("🎬 Happy video creating! ✨")
                break
            else:
                print("\n❌ Invalid option. Please choose 1-6 or 'q' to quit.")
                input("\n⏸️  Press Enter to continue...")

def enhanced_project_selector():
    """Enhanced project selection with better navigation."""
    output_dir = project_root / "output"
    
    if not output_dir.exists():
        print("\n📂 No output directory found.")
        print("💡 Generate some content first!")
        return None
    
    projects = [d for d in output_dir.iterdir() if d.is_dir()]
    
    if not projects:
        print("\n📂 No projects found in output directory.")
        print("💡 Generate some content first!")
        return None
    
    # Sort by modification time (newest first)
    projects.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"\n📊 Found {len(projects)} project(s). Select one to view details:\n")
    
    for i, project in enumerate(projects[:10], 1):
        mod_time = datetime.fromtimestamp(project.stat().st_mtime)
        print(f"{i:2d}. 📁 {project.name}")
        print(f"    📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show topic if available
        manifest_file = project / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    if 'topic' in manifest:
                        print(f"    🎯 {manifest['topic']}")
            except:
                pass
        print()
    
    while True:
        try:
            choice = input("\n👉 Select project number (1-10), 'a' for all details, or 'b' to go back: ").strip().lower()
            
            if choice == 'b' or choice == 'back':
                return None
            elif choice == 'a' or choice == 'all':
                return 'all'
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= min(10, len(projects)):
                    return projects[choice_num - 1]
                else:
                    print(f"\n❌ Please choose a number between 1 and {min(10, len(projects))}")
            else:
                print("\n❌ Invalid input. Please enter a number, 'a' for all, or 'b' to go back.")
        except ValueError:
            print("\n❌ Invalid input. Please enter a number, 'a' for all, or 'b' to go back.")

def main():
    """Main CLI loop with enhanced navigation."""
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using AIVA CLI!")
    except EOFError:
        print("\n\n👋 Goodbye! Thanks for using AIVA CLI!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check your installation and try again.")
        print("🔧 Check README_CLI.md for installation instructions.")

if __name__ == "__main__":
    main()