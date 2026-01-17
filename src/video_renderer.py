import os
import logging
from typing import List, Dict, Any

from moviepy import *
from config.settings import Config

logger = logging.getLogger(__name__)

class VideoRenderer:
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.resolution = Config.DEFAULT_RESOLUTION
        self.fps = Config.FPS

    def render_video(self, scenes: List[Dict[str, Any]], output_filename: str = "full_movie.mp4"):
        logger.info("Starting video rendering...")

        clips = []

        for scene in scenes:
            scene_id = scene["id"]
            image_path = scene.get("image_file")

            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Missing image for {scene_id}, skipping.")
                continue

            # 1. Determine Audio Duration & Create Audio Track
            audio_clips = []
            total_duration = 0

            # Sort dialogue by index to match order
            # The manifest generation (index in list) is strictly ordered
            dialogue = scene.get("dialogue", [])

            # Start time for next audio clip
            current_time = 0.5 # start with 0.5s silence

            for line in dialogue:
                audio_path = line.get("audio_file")
                if audio_path and os.path.exists(audio_path):
                    try:
                        aclip = AudioFileClip(audio_path)
                        # Set start time relative to the scene start
                        aclip = aclip.with_start(current_time)
                        audio_clips.append(aclip)
                        current_time += aclip.duration + 0.3  # Add 0.3s pause between lines
                    except Exception as e:
                        logger.error(f"Failed to load audio {audio_path}: {e}")

            # Total scene duration
            total_duration = current_time + 1.0 # Add 1s buffer at end
            if total_duration < 3.0:
                total_duration = 3.0 # Minimum 3s per scene

            # 2. Create Video Clip (Image)
            # Load image
            img_clip = ImageClip(image_path)

            # Resize to cover screen (handle aspect ratios)
            # Use 'resized' method to fit width/height while maintaining aspect ratio, then crop
            # MoviePy v2 uses 'resized' instead of 'resize' and 'cropped' instead of 'crop' usually,
            # but let's stick to standard v1.0.3 syntax if possible or adapt for v2 if installed.
            # The environment installed moviepy-2.1.1. In 2.x, methods are often `with_duration`, `resized`, etc.

            # Basic setup
            img_clip = img_clip.with_duration(total_duration)

            # Resize to fill (simple approach: resize to width, center crop height)
            img_w, img_h = img_clip.size
            target_w, target_h = self.resolution

            # Calculate scale to cover
            scale = max(target_w / img_w, target_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            img_clip = img_clip.resized(new_size=(new_w, new_h))
            img_clip = img_clip.with_position("center")

            # Apply Ken Burns Effect (Simple Zoom In)
            # We crop a window that gets smaller over time (zooming in)
            # Or simpler: Resize the clip from 1.0 to 1.1 over duration

            # Let's do a simple pan/zoom using a transformation function
            # Start: Center, Scale 1.0
            # End: Center, Scale 1.1

            # For simplicity and stability in this script, we will just use static images first.
            # Ken Burns in MoviePy can be computationally expensive and tricky with versions.
            # We will stick to static images for the MVP to ensure stability,
            # unless we want to try a simple "resize" animation.

            def zoom(t):
                # Zoom factor goes from 1.0 to 1.15
                return 1 + 0.15 * (t / total_duration)

            # Apply zoom
            # img_clip = img_clip.resized(zoom) # This works but is slow.
            # Using CompositeVideoClip to center it on a black background

            final_scene_clip = CompositeVideoClip([img_clip], size=self.resolution)
            final_scene_clip = final_scene_clip.with_duration(total_duration)

            # 3. Add Audio
            if audio_clips:
                scene_audio = CompositeAudioClip(audio_clips)
                final_scene_clip = final_scene_clip.with_audio(scene_audio)

            clips.append(final_scene_clip)
            logger.info(f"Prepared clip for {scene_id} ({total_duration:.2f}s)")

        if not clips:
            logger.error("No clips to render.")
            return

        # Concatenate
        final_video = concatenate_videoclips(clips)

        output_path = os.path.join(self.output_dir, output_filename)
        logger.info(f"Writing video file to {output_path}...")

        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac"
        )
        logger.info("Rendering complete.")
