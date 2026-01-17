import json
import os
import time
from typing import Dict, List, Any
import logging

from config.settings import Config

# Try importing vertexai, but handle failure for environments where it might not be configured
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class ScriptParser:
    def __init__(self, project_id: str = Config.PROJECT_ID, location: str = Config.LOCATION):
        self.project_id = project_id
        self.location = location
        if VERTEX_AI_AVAILABLE:
            try:
                vertexai.init(project=project_id, location=location)
                self.model = GenerativeModel(Config.GEMINI_MODEL)
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}")
                self.model = None
        else:
            self.model = None

    def parse(self, script_text: str) -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("Vertex AI model not initialized. Check credentials or use --mock.")

        prompt = self._construct_prompt(script_text)

        try:
            response = self.model.generate_content(prompt)
            # Clean up response to ensure it's valid JSON (sometimes models add backticks)
            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]

            return json.loads(text_response)
        except Exception as e:
            logger.error(f"Error parsing script with Gemini: {e}")
            raise

    def _construct_prompt(self, script_text: str) -> str:
        return f"""
        You are an AI assistant specialized in converting movie scripts into structured production manifests.

        Analyze the following script and output a valid JSON object.
        The JSON should have a 'scenes' list.
        Each 'scene' object must contain:
        - 'id': A unique identifier (e.g., 'scene_001').
        - 'location': The location header.
        - 'visual_prompt': A highly detailed image generation prompt (for Imagen) describing the visual elements, lighting, camera angle, and mood. Avoid mentioning specific character names in the visual prompt; describe their appearance instead.
        - 'dialogue': A list of objects, each with:
            - 'character': The character name (uppercase).
            - 'text': The spoken text.

        Here is the script:
        {script_text}
        """

class MockScriptParser:
    def parse(self, script_text: str) -> Dict[str, Any]:
        logger.info("MOCK: Parsing script...")
        # Return a sample structure based on the user's provided script snippet
        return {
            "title": "THE HUMAN OVERRIDE",
            "scenes": [
                {
                    "id": "scene_001",
                    "location": "UPSCALE RESTAURANT",
                    "visual_prompt": "Cinematic shot of a modern upscale restaurant interior at night in NYC. Intimate lighting, candlelit table. A well-dressed man in his 30s sits across from a stunning woman in designer clothes. They are laughing and drinking wine. Photorealistic, 8k, bokeh.",
                    "dialogue": [
                        {
                            "character": "NARRATOR",
                            "text": "What looks like a normal evening to two people is a system event to the building."
                        },
                        {
                            "character": "NARRATOR",
                            "text": "A resident returning home. With a guest. At 11:47 PM."
                        }
                    ]
                },
                {
                    "id": "scene_002",
                    "location": "BUILDING ENTRANCE",
                    "visual_prompt": "Night time street view of a high-tech apartment building entrance in Brooklyn. A man holds a key fob against a reader. The reader displays a harsh RED light. The man looks confused, the woman looks annoyed. Cyberpunk undertones, cold lighting.",
                    "dialogue": [
                        {
                            "character": "MARCUS",
                            "text": "That's weird."
                        },
                        {
                            "character": "NARRATOR",
                            "text": "At 11:47 p.m., the door stops recognizing him. No warning. Just a red light."
                        }
                    ]
                },
                 {
                    "id": "scene_003",
                    "location": "HALLWAY",
                    "visual_prompt": "Apartment hallway, sterile and cold. A man is pounding on a door in frustration. He looks exhausted and angry. A neighbor peaks out from another door with a fearful expression.",
                    "dialogue": [
                        {
                            "character": "MARCUS",
                            "text": "Why won't you let me in?! I pay rent! I live here!"
                        }
                    ]
                }
            ]
        }
