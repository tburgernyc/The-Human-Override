import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
from src.audio_manager import AudioManager
from config.settings import Config

@pytest.fixture
def mock_tts_client():
    with patch('src.audio_manager.texttospeech.TextToSpeechClient') as MockClient:
        mock_instance = MockClient.return_value
        # Default behavior: return a success response
        response = MagicMock()
        response.audio_content = b'mock_audio_content'
        mock_instance.synthesize_speech.return_value = response
        yield mock_instance

@pytest.fixture
def audio_manager(mock_tts_client):
    # Setup
    if os.path.exists(Config.AUDIO_DIR):
        shutil.rmtree(Config.AUDIO_DIR)

    manager = AudioManager()
    # Force the client to be our mock (in case __init__ logic varies)
    manager.client = mock_tts_client

    yield manager

    # Teardown
    if os.path.exists(Config.AUDIO_DIR):
        shutil.rmtree(Config.AUDIO_DIR)

def test_generate_tts_success(audio_manager, mock_tts_client):
    scenes = [
        {
            "id": "scene_1",
            "dialogue": [
                {"character": "MARCUS", "text": "Hello world."},
                {"character": "SOFIA", "text": "Hi Marcus."}
            ]
        }
    ]

    updated_scenes = audio_manager.generate_tts(scenes)

    # Check that 2 files were generated
    files = os.listdir(audio_manager.output_dir)
    assert len(files) == 2
    assert "scene_1_MARCUS_0.wav" in files
    assert "scene_1_SOFIA_1.wav" in files

    # Check that updated_scenes contains the file paths
    assert "audio_file" in updated_scenes[0]["dialogue"][0]
    assert "audio_file" in updated_scenes[0]["dialogue"][1]

    # Check API was called twice
    assert mock_tts_client.synthesize_speech.call_count == 2

def test_generate_tts_skip_existing(audio_manager, mock_tts_client):
    # Create a dummy file first
    filename = "scene_1_MARCUS_0.wav"
    filepath = os.path.join(audio_manager.output_dir, filename)
    os.makedirs(audio_manager.output_dir, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(b"existing_audio")

    scenes = [
        {
            "id": "scene_1",
            "dialogue": [
                {"character": "MARCUS", "text": "Hello world."},
            ]
        }
    ]

    audio_manager.generate_tts(scenes)

    # Check API was NOT called
    assert mock_tts_client.synthesize_speech.call_count == 0

def test_generate_tts_partial_failure(audio_manager, mock_tts_client):
    """Test that if one call fails, others still proceed."""
    scenes = [
        {
            "id": "scene_err",
            "dialogue": [
                {"character": "MARCUS", "text": "I will fail."},
                {"character": "SOFIA", "text": "I will succeed."}
            ]
        }
    ]

    # Configure mock to raise exception for the first call, succeed for second
    # Note: calls might happen in any order in parallel, but here we test sequential (baseline)
    # For parallel, we need side_effect to depend on input text or just be an iterator

    def side_effect(input, voice, audio_config):
        if input.text == "I will fail.":
            raise RuntimeError("TTS API Error")
        response = MagicMock()
        response.audio_content = b'success'
        return response

    mock_tts_client.synthesize_speech.side_effect = side_effect

    audio_manager.generate_tts(scenes)

    files = os.listdir(audio_manager.output_dir)
    # Should have 1 file (SOFIA)
    assert len(files) == 1
    assert "scene_err_SOFIA_1.wav" in files

    # MARCUS should not have audio_file in the returned structure (or it stays empty)
    # The current implementation adds "audio_file" key only on success.
    # We need to verify what happens.

    # The logic in audio_manager.py:
    # if os.path.exists(filepath): line["audio_file"] = filepath; continue
    # try: ... write ... line["audio_file"] = filepath

    # So if it fails, "audio_file" key is missing.

    # We need to capture the returned structure
    # But generate_tts returns updated_scenes which is a modified list

    # Wait, the code says: `updated_scenes.append(scene)` after the inner loop.
    # And `line` is modified in place (reference).

    # So we check the input list objects or the return value

    assert "audio_file" not in scenes[0]["dialogue"][0] # Failed one
    assert "audio_file" in scenes[0]["dialogue"][1] # Success one
