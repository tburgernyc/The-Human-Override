import argparse
import os
import sys
import json
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track

from config.settings import Config
from src.script_parser import ScriptParser, MockScriptParser
from src.audio_manager import AudioManager, MockAudioManager
from src.image_manager import ImageManager, MockImageManager
from src.video_renderer import VideoRenderer

# Configure Logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("tho_cli")
console = Console()

def load_script(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def save_manifest(manifest, filepath="manifest.json"):
    path = os.path.join(Config.OUTPUT_DIR, filepath)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {path}")
    return path

def load_manifest(filepath="manifest.json"):
    path = os.path.join(Config.OUTPUT_DIR, filepath)
    if not os.path.exists(path):
        logger.error(f"Manifest not found at {path}. Run 'parse' first.")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="The Human Override - Video Generation Pipeline")
    parser.add_argument("command", choices=["parse", "assets", "render", "build", "ui"], help="Pipeline stage to run")
    parser.add_argument("--input", default=os.path.join(Config.INPUT_DIR, "script.txt"), help="Path to input script text file")
    parser.add_argument("--mock", action="store_true", help="Run in Mock Mode (no API costs)")
    parser.add_argument("--audio-mode", choices=["tts", "external"], default="tts", help="Audio generation mode")

    args = parser.parse_args()

    # 1. Initialize Components
    if args.mock:
        logger.warning("[bold yellow]RUNNING IN MOCK MODE[/bold yellow]", extra={"markup": True})
        script_parser = MockScriptParser()
        audio_manager = MockAudioManager()
        image_manager = MockImageManager()
    else:
        script_parser = ScriptParser()
        audio_manager = AudioManager()
        image_manager = ImageManager()

    video_renderer = VideoRenderer()

    # Pipeline State
    manifest = None

    # --- UI MODE ---
    if args.command == "ui":
        console.rule("[bold blue]Launching Director Mode UI[/bold blue]")
        import subprocess
        subprocess.run(["streamlit", "run", "src/app.py"])
        return

    # --- STAGE 1: PARSE ---
    if args.command in ["parse", "build"]:
        console.rule("[bold blue]Stage 1: Script Parsing[/bold blue]")
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)

        raw_text = load_script(args.input)
        with console.status("Parsing script with AI...", spinner="dots"):
            parsed_data = script_parser.parse(raw_text)

        # Ensure 'scenes' key exists
        if "scenes" not in parsed_data:
             logger.error("Parsed data missing 'scenes' key.")
             sys.exit(1)

        manifest = parsed_data["scenes"]
        save_manifest(manifest)
        logger.info(f"Parsed {len(manifest)} scenes.")

    # --- STAGE 2: ASSETS ---
    if args.command in ["assets", "build"]:
        console.rule("[bold blue]Stage 2: Asset Generation[/bold blue]")
        if not manifest:
            manifest = load_manifest()

        # Images
        with console.status("Generating Images...", spinner="dots"):
            manifest = image_manager.generate_images(manifest)
        save_manifest(manifest) # Save paths

        # Audio
        if args.audio_mode == "tts":
            with console.status("Generating TTS Audio...", spinner="dots"):
                manifest = audio_manager.generate_tts(manifest)
            save_manifest(manifest)
        else:
            logger.info("Checking external audio files...")
            missing = audio_manager.check_external_audio(manifest)
            if missing:
                logger.error(f"Missing external audio files:\n" + "\n".join(missing))
                logger.error("Please place files in assets/audio/ and re-run.")
                sys.exit(1)
            save_manifest(manifest)

    # --- STAGE 3: RENDER ---
    if args.command in ["render", "build"]:
        console.rule("[bold blue]Stage 3: Video Rendering[/bold blue]")
        if not manifest:
            manifest = load_manifest()

        with console.status("Rendering Final Video...", spinner="dots"):
            video_renderer.render_video(manifest)

    console.rule("[bold green]Pipeline Complete[/bold green]")

if __name__ == "__main__":
    main()
