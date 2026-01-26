import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "mock-project-id")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    # AI Models
    GEMINI_MODEL = "gemini-1.5-pro-preview-0409"
    IMAGEN_MODEL = "imagegeneration@006"

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, "input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
    AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")

    # Defaults
    DEFAULT_RESOLUTION = (1920, 1080)
    FPS = 24
    MAX_CONCURRENT_REQUESTS = 5
