#!/usr/bin/env python3
"""
AIVA CLI - Agentic Content Generator via CLI

A command-line tool that uses CrewAI to orchestrate multiple AI agents
for generating YouTube-ready content including scripts, segments, and images.
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import os
import sys

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import AIVA modules
try:
    from .config.loader import load_config, validate_config, AIVASettings
    from .logs.logger import setup_logging, get_logger, performance_timer
    from .core.pipeline import generate_content
except ImportError as e:
    # Fallback for development
    print(f"Warning: Could not import AIVA modules: {e}")
    load_config = None
    validate_config = None
    AIVASettings = None
    setup_logging = None
    get_logger = None
    performance_timer = None
    generate_content = None

# Initialize Typer app and Rich console
app = typer.Typer(
    name="aiva",
    help="🎬 AIVA CLI - Agentic Content Generator for YouTube",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

# Version information
__version__ = "1.0.0"


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print(f"[bold blue]AIVA CLI[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", 
        callback=version_callback,
        help="Show version and exit"
    )
):
    """🎬 AIVA CLI - Agentic Content Generator for YouTube
    
    Generate complete YouTube content including scripts, segments, and AI images
    using CrewAI orchestrated agents powered by Gemini models.
    """
    pass


@app.command()
def generate(
    topic: str = typer.Argument(
        ..., 
        help="Topic for the YouTube video content"
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title", "-T",
        help="Custom title for the content (used for project folder name)"
    ),
    video_type: str = typer.Option(
        "long-form", 
        "--type", "-t",
        help="Video type: 'short' or 'long-form'"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir", "-o",
        help="Custom output directory (default: output/)"
    ),
    config_file: Optional[str] = typer.Option(
        None,
        "--config", "-c",
        help="Custom configuration file path"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be generated without actually generating"
    )
):
    """🚀 Generate YouTube content for a given topic
    
    This command orchestrates multiple CrewAI agents to create:
    - A comprehensive YouTube script
    - Timed segments (8 seconds each)
    - Enhanced visual prompts for each segment
    - AI-generated images using Imagen 3.0
    - Organized project structure with custom naming
    
    Examples:
        aiva generate "The History of Artificial Intelligence"
        aiva generate "Climate Change Solutions" --title "Climate Solutions Guide"
        aiva generate "Space Exploration" --output-dir ./my_videos --title "Space Journey"
        aiva generate "Machine Learning" --dry-run --verbose
    """
    
    # Input validation
    validation_errors = _validate_generate_inputs(topic, video_type, output_dir, title)
    if validation_errors:
        console.print("[red]❌ Input validation failed:[/red]")
        for error in validation_errors:
            console.print(f"  • {error}")
        raise typer.Exit(1)
    
    # Load and validate configuration
    try:
        if load_config:
            config = load_config()
            config_issues = validate_config(config) if validate_config else []
            
            if config_issues:
                console.print("[yellow]⚠️  Configuration issues detected:[/yellow]")
                for issue in config_issues:
                    console.print(f"  • {issue}")
                if not dry_run:
                    console.print("[blue]💡 Run with --dry-run to test without API calls[/blue]")
            
            # Setup logging with config
            if setup_logging:
                setup_logging(config.logging.model_dump())
                logger = get_logger("aiva.generate")
                logger.info("Starting content generation", topic=topic, video_type=video_type)
        else:
            config = None
            logger = None
            
    except Exception as e:
        console.print(f"[red]❌ Configuration error: {str(e)}[/red]")
        console.print("[blue]💡 Run 'aiva init' to set up configuration[/blue]")
        if not dry_run:
            raise typer.Exit(1)
        config = None
        logger = None
    
    # Display welcome message
    welcome_text = Text()
    welcome_text.append("🎬 AIVA CLI Content Generator (Phase 5 Enhanced)\n", style="bold blue")
    welcome_text.append(f"Topic: {topic}\n", style="green")
    welcome_text.append(f"Title: {title or 'Auto-generated from topic'}\n", style="magenta")
    welcome_text.append(f"Type: {video_type}\n", style="yellow")
    if output_dir:
        welcome_text.append(f"Output: {output_dir}\n", style="cyan")
    
    console.print(Panel(
        welcome_text,
        title="[bold]Starting Content Generation[/bold]",
        border_style="blue"
    ))
    
    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No actual generation will occur[/yellow]")
        _show_generation_plan(topic, video_type, output_dir, config)
        return
    
    try:
        # Use the new generation pipeline
        if generate_content:
            # Determine output directory
            if output_dir:
                out_dir = Path(output_dir)
            else:
                out_dir = Path("output")
            
            console.print("[blue]🚀 Starting content generation pipeline...[/blue]")
            
            # Add loading animation and progress tracking
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
            from rich.live import Live
            import time
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True
            ) as progress:
                
                # Create progress tasks
                main_task = progress.add_task("[cyan]Generating content...", total=100)
                
                # Show initial progress
                progress.update(main_task, advance=10, description="[cyan]Initializing pipeline...")
                time.sleep(0.5)
                
                # Call the enhanced pipeline with CrewAI integration
                result = generate_content(topic, video_type, out_dir, title=title, config=config, progress_callback=lambda desc, pct: progress.update(main_task, completed=pct, description=f"[cyan]{desc}"))
                
                # Complete progress
                progress.update(main_task, completed=100, description="[green]Content generation completed!")
                time.sleep(0.5)
            
            if result and result.get('status') == 'success':
                console.print(f"[green]✅ Content generation completed successfully![/green]")
                console.print(f"[cyan]📁 Project: {result.get('project_title', 'Unknown')}[/cyan]")
                console.print(f"[cyan]📂 Output directory: {result.get('output_dir', out_dir)}[/cyan]")
                if result.get('segments_processed'):
                    console.print(f"[yellow]🎬 Generated {result['segments_processed']} segments (8 seconds each)[/yellow]")
                if result.get('manifest'):
                    console.print(f"[magenta]📋 Enhanced manifest created with CrewAI metadata[/magenta]")
                console.print(f"[blue]🤖 CrewAI agents successfully coordinated the workflow[/blue]")
                console.print(f"[green]🎯 Phase 5 enhancements: Custom project naming & improved organization[/green]")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Pipeline returned no result'
                console.print(f"[red]❌ Generation failed: {error_msg}[/red]")
                if result and result.get('state_file'):
                    console.print(f"[blue]💡 You can resume from: {result.get('state_file')}[/blue]")
                raise typer.Exit(1)
        else:
            console.print("[red]❌ Pipeline not available - module import failed[/red]")
            console.print("[blue]💡 Please check your installation and dependencies[/blue]")
            raise typer.Exit(1)
        
    except Exception as e:
        if logger:
            logger.exception("Generation failed", topic=topic, error=str(e))
        console.print(f"[red]❌ Error during generation: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    directory: Optional[str] = typer.Argument(
        None,
        help="Directory to initialize (default: current directory)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing configuration files"
    )
):
    """🔧 Initialize AIVA CLI configuration
    
    Creates necessary configuration files and directories.
    """
    
    target_dir = Path(directory) if directory else Path.cwd()
    config_dir = target_dir / "config"
    
    console.print(f"[blue]🔧 Initializing AIVA CLI in: {target_dir}[/blue]")
    
    try:
        # Create config directory if it doesn't exist
        config_dir.mkdir(exist_ok=True)
        
        # Copy .env.template to .env if it doesn't exist
        env_template = project_root / "config" / ".env.template"
        env_file = config_dir / ".env"
        
        if not env_file.exists() or force:
            if env_template.exists():
                import shutil
                shutil.copy2(env_template, env_file)
                console.print(f"[green]✅ Created configuration file: {env_file}[/green]")
                console.print("[yellow]⚠️  Please edit the .env file and add your API keys[/yellow]")
            else:
                console.print(f"[red]❌ Template file not found: {env_template}[/red]")
        else:
            console.print(f"[yellow]⚠️  Configuration file already exists: {env_file}[/yellow]")
            console.print("[blue]💡 Use --force to overwrite[/blue]")
            
    except Exception as e:
        console.print(f"[red]❌ Error during initialization: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """📊 Show AIVA CLI status and configuration
    
    Displays current configuration, API connectivity, and system status.
    """
    
    console.print("[blue]📊 AIVA CLI Status[/blue]")
    
    # Check configuration in multiple locations
    config_locations = [
        Path.cwd() / "config" / ".env",  # Current directory
        project_root / "config" / ".env"  # Project root
    ]
    
    config_found = False
    for config_file in config_locations:
        if config_file.exists():
            console.print(f"[green]✅ Configuration file found: {config_file}[/green]")
            config_found = True
            break
    
    if not config_found:
        console.print(f"[red]❌ Configuration file not found in expected locations[/red]")
        console.print("[blue]💡 Run 'aiva init' to create configuration[/blue]")
    
    # Check project structure
    required_dirs = ["crew_config", "core", "models", "config", "logs", "output"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            console.print(f"[green]✅ Directory exists: {dir_name}/[/green]")
        else:
            console.print(f"[red]❌ Directory missing: {dir_name}/[/red]")
    
    # TODO: Add API connectivity checks
    console.print("[yellow]⚠️  API connectivity checks not yet implemented[/yellow]")


def _validate_generate_inputs(topic: str, video_type: str, output_dir: Optional[str], title: Optional[str] = None) -> list[str]:
    """Validate inputs for the generate command"""
    errors = []
    
    # Validate topic
    if not topic or len(topic.strip()) < 3:
        errors.append("Topic must be at least 3 characters long")
    elif len(topic) > 200:
        errors.append("Topic must be less than 200 characters")
    
    # Validate title if provided
    if title is not None:
        if len(title.strip()) < 2:
            errors.append("Title must be at least 2 characters long")
        elif len(title) > 100:
            errors.append("Title must be less than 100 characters")
        elif not title.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            errors.append("Title should contain only letters, numbers, spaces, hyphens, and underscores")
    
    # Validate video type
    valid_types = ["short", "long-form"]
    if video_type not in valid_types:
        errors.append(f"Video type must be one of: {', '.join(valid_types)}")
    
    # Validate output directory
    if output_dir:
        output_path = Path(output_dir)
        if output_path.exists() and not output_path.is_dir():
            errors.append(f"Output path '{output_dir}' exists but is not a directory")
        
        # Check if path is writable (create parent if needed)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            errors.append(f"Cannot create output directory '{output_dir}': {str(e)}")
    
    return errors


def _show_generation_plan(topic: str, video_type: str, output_dir: Optional[str], config: Optional[object]):
    """Display the generation plan for dry run mode"""
    plan_text = Text()
    plan_text.append("📋 Generation Plan\n\n", style="bold cyan")
    
    # Basic info
    plan_text.append(f"Topic: {topic}\n", style="green")
    plan_text.append(f"Video Type: {video_type}\n", style="yellow")
    
    # Output directory
    if output_dir:
        plan_text.append(f"Output Directory: {output_dir}\n", style="cyan")
    else:
        plan_text.append("Output Directory: output/ (default)\n", style="cyan")
    
    # Configuration status
    if config:
        plan_text.append("Configuration: ✅ Loaded\n", style="green")
    else:
        plan_text.append("Configuration: ⚠️  Using defaults\n", style="yellow")
    
    plan_text.append("\n🤖 Agents to be deployed:\n", style="bold blue")
    
    # Agent roles
    agents = [
        ("📝 Script Writer", "Creates engaging YouTube script"),
        ("🎬 Director", "Breaks script into timed segments"),
        ("🎨 Visual Designer", "Generates visual prompts"),
        ("🖼️  Image Generator", "Creates AI images for each segment")
    ]
    
    for agent_name, description in agents:
        plan_text.append(f"  • {agent_name}: {description}\n", style="white")
    
    plan_text.append("\n📁 Expected Output Structure:\n", style="bold magenta")
    plan_text.append("  • script.md - Complete video script\n")
    plan_text.append("  • segments.json - Timed segment breakdown\n")
    plan_text.append("  • prompts/ - Visual prompts for each segment\n")
    plan_text.append("  • images/ - Generated images\n")
    plan_text.append("  • metadata.json - Generation metadata\n")
    
    console.print(Panel(
        plan_text,
        title="[bold]Dry Run Preview[/bold]",
        border_style="cyan"
    ))


def _placeholder_generation(topic: str, video_type: str, output_dir: Optional[str], verbose: bool, config: Optional[object], logger: Optional[object]):
    """Placeholder for the actual generation pipeline."""
    import time
    
    if logger:
        logger.info("Starting placeholder generation", topic=topic, video_type=video_type)
    
    console.print("\n[blue]🔄 Starting generation pipeline...[/blue]")
    
    # Simulate progress
    steps = [
        "📝 Initializing Script Writer agent",
        "🎬 Setting up Director agent", 
        "🎨 Preparing Visual Designer agent",
        "🖼️  Loading Image Generator agent",
        "⚙️  Configuring workflow"
    ]
    
    for i, step in enumerate(steps, 1):
        console.print(f"  {step}...")
        if verbose:
            console.print(f"    [dim]Step {i}/{len(steps)} - Configuration: {'✅' if config else '⚠️'}[/dim]")
        time.sleep(0.5)  # Simulate work
        
        if logger:
            logger.debug(f"Completed step: {step}", step=i, total_steps=len(steps))
    
    console.print("\n[green]✅ Pipeline setup complete![/green]")
    console.print("[yellow]⏳ Actual implementation coming in Phase 6[/yellow]")
    
    if logger:
        logger.info("Placeholder generation completed", topic=topic)


if __name__ == "__main__":
    app()