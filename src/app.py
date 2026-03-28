import streamlit as st
import os
import json
import logging
from PIL import Image

from config.settings import Config
from src.image_manager import ImageManager, MockImageManager
from src.video_renderer import VideoRenderer
from src.script_parser import ScriptParser, MockScriptParser
from src.audio_manager import AudioManager, MockAudioManager

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")

st.set_page_config(page_title="The Human Override - Director Mode", layout="wide")

# Initialize Session State
if "manifest" not in st.session_state:
    manifest_path = os.path.join(Config.OUTPUT_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            st.session_state.manifest = json.load(f)
    else:
        st.session_state.manifest = None

if "mock_mode" not in st.session_state:
    st.session_state.mock_mode = True # Default to Mock for safety, user can toggle

def save_manifest():
    manifest_path = os.path.join(Config.OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(st.session_state.manifest, f, indent=2)

def get_image_manager():
    if st.session_state.mock_mode:
        return MockImageManager()
    return ImageManager()

def get_video_renderer():
    return VideoRenderer()

# Sidebar
st.sidebar.title("Production Control")
st.session_state.mock_mode = st.sidebar.checkbox("Mock Mode", value=st.session_state.mock_mode)

if st.sidebar.button("Reload Manifest"):
    manifest_path = os.path.join(Config.OUTPUT_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            st.session_state.manifest = json.load(f)
        st.sidebar.success("Manifest Reloaded")
    else:
        st.sidebar.error("No manifest.json found.")

if st.sidebar.button("Render Full Video"):
    with st.spinner("Rendering Video..."):
        renderer = get_video_renderer()
        renderer.render_video(st.session_state.manifest)
    st.sidebar.success("Video Rendered!")
    # Force reload of video player
    st.rerun()


# Main Content
st.title("🎬 The Human Override: Director Mode")

# Video Player
video_path = os.path.join(Config.OUTPUT_DIR, "full_movie.mp4")
if os.path.exists(video_path):
    st.header("Latest Cut")
    st.video(video_path)
else:
    st.info("No video rendered yet.")

st.divider()

if st.session_state.manifest:
    st.header("Scene Editor")

    for i, scene in enumerate(st.session_state.manifest):
        with st.expander(f"Scene {i+1}: {scene.get('id')} - {scene.get('location')}", expanded=(i==0)):
            col1, col2 = st.columns([1, 1])

            with col1:
                # Image Display
                img_path = scene.get("image_file")
                if img_path and os.path.exists(img_path):
                    image = Image.open(img_path)
                    st.image(image, caption="Current Visual", use_container_width=True)
                else:
                    st.warning("No image generated.")

            with col2:
                # Prompt Editor
                current_prompt = scene.get("visual_prompt", "")
                new_prompt = st.text_area(f"Visual Prompt ({scene['id']})", value=current_prompt, height=150)

                if new_prompt != current_prompt:
                    scene["visual_prompt"] = new_prompt
                    save_manifest()
                    st.success("Prompt updated (saved to manifest).")

                if st.button(f"Regenerate Image {scene['id']}"):
                    with st.spinner("Regenerating..."):
                        mgr = get_image_manager()
                        # Force regeneration by temporarily removing file path or calling specific method
                        # ImageManager.generate_images checks if file exists.
                        # We need to delete the old file to force regen or update logic.
                        if img_path and os.path.exists(img_path):
                            os.remove(img_path)

                        # Pass only this scene to generate_images to save time
                        updated_scenes = mgr.generate_images([scene])
                        st.session_state.manifest[i] = updated_scenes[0]
                        save_manifest()
                    st.success("Image Regenerated!")
                    st.rerun()

                st.subheader("Dialogue")
                for line in scene.get("dialogue", []):
                    st.text(f"{line['character']}: {line['text']}")

else:
    st.warning("No manifest loaded. Please run 'python main.py parse' first or check 'output/manifest.json'.")
