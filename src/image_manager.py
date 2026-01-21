import os
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.settings import Config
from PIL import Image, ImageDraw, ImageFont

# Try import for Vertex AI Vision
try:
    from vertexai.preview.vision_models import ImageGenerationModel
    IMAGEN_AVAILABLE = True
except ImportError:
    IMAGEN_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImageManager:
    def __init__(self, project_id: str = Config.PROJECT_ID, location: str = Config.LOCATION):
        self.output_dir = Config.IMAGES_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        if IMAGEN_AVAILABLE:
            try:
                self.model = ImageGenerationModel.from_pretrained(Config.IMAGEN_MODEL)
            except Exception as e:
                logger.warning(f"Failed to initialize Imagen Model: {e}")
                self.model = None
        else:
            self.model = None

    def _generate_single_image(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = scene["id"]
        prompt = scene["visual_prompt"]
        filepath = os.path.join(self.output_dir, f"{scene_id}.png")

        if os.path.exists(filepath):
            scene["image_file"] = filepath
            return scene

        logger.info(f"Generating image for {scene_id}...")
        try:
            images = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                language="en",
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )

            if images:
                images[0].save(location=filepath, include_generation_parameters=False)
                scene["image_file"] = filepath
                logger.info(f"Saved image: {filepath}")
            else:
                logger.error(f"No images generated for {scene_id}")
                scene["image_file"] = None # Explicitly set to None on failure

        except Exception as e:
            logger.error(f"Failed to generate image for {scene_id}: {e}")
            scene["image_file"] = None # Explicitly set to None on error

        return scene

    def generate_images(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.model:
            raise RuntimeError("Imagen model not initialized. Check credentials or use --mock.")

        # Use a ThreadPoolExecutor to generate images concurrently
        with ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_REQUESTS) as executor:
            # Create a future for each scene
            future_to_scene = {executor.submit(self._generate_single_image, scene): scene for scene in scenes}

            updated_scenes = []
            for future in as_completed(future_to_scene):
                original_scene = future_to_scene[future]
                try:
                    # Get the result from the future
                    updated_scene = future.result()
                    updated_scenes.append(updated_scene)
                except Exception as e:
                    logger.error(f"An exception occurred for scene {original_scene['id']}: {e}")
                    # Even on error, add the original scene back to maintain list integrity
                    original_scene['image_file'] = None
                    updated_scenes.append(original_scene)

        # Sort the results back into the original order, as concurrent execution can disorder them
        scene_order_map = {scene["id"]: i for i, scene in enumerate(scenes)}
        updated_scenes.sort(key=lambda s: scene_order_map[s["id"]])

        return updated_scenes


class MockImageManager:
    def __init__(self):
        self.output_dir = Config.IMAGES_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_images(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("MOCK: Generating images...")
        updated_scenes = []
        for scene in scenes:
            scene_id = scene["id"]
            prompt = scene["visual_prompt"]
            filepath = os.path.join(self.output_dir, f"{scene_id}.png")

            if not os.path.exists(filepath):
                self._create_placeholder_image(filepath, scene_id, prompt)
                logger.info(f"MOCK: Created {filepath}")

            scene["image_file"] = filepath
            updated_scenes.append(scene)
        return updated_scenes

    def _create_placeholder_image(self, filepath: str, title: str, text: str):
        width, height = Config.DEFAULT_RESOLUTION
        img = Image.new('RGB', (width, height), color=(73, 109, 137))
        draw = ImageDraw.Draw(img)

        # Load a font (or default if not found)
        try:
            # Try to use a standard font
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
        except IOError:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        # Draw Title
        draw.text((50, 50), title, font=title_font, fill=(255, 255, 255))

        # Draw Prompt Text (wrapped)
        margin = 50
        offset = 200
        for line in self._wrap_text(text, font, width - 2*margin):
            draw.text((margin, offset), line, font=font, fill=(255, 255, 255))
            offset += 50

        img.save(filepath)

    def _wrap_text(self, text, font, max_width):
        lines = []
        words = text.split()
        if not words:
            return lines

        current_line = words[0]
        for word in words[1:]:
            # Check width if we add this word
            try:
                bbox = font.getbbox(current_line + " " + word)
                w = bbox[2] - bbox[0]
            except AttributeError:
                 # Fallback for old Pillow versions or default font
                 w = len(current_line + " " + word) * 10

            if w <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines
