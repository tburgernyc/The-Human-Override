import os
import logging
from typing import List, Dict, Any, Optional
import wave
import struct

from config.settings import Config

# Try import for TTS
try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.output_dir = Config.AUDIO_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        if TTS_AVAILABLE:
            try:
                self.client = texttospeech.TextToSpeechClient()
            except Exception as e:
                logger.warning(f"Failed to initialize TTS Client: {e}")
                self.client = None
        else:
            self.client = None

        # Voice Mapping Configuration
        self.voice_map = {
            "NARRATOR": {"name": "en-US-Studio-M", "gender": texttospeech.SsmlVoiceGender.MALE},
            "MARCUS": {"name": "en-US-Neural2-D", "gender": texttospeech.SsmlVoiceGender.MALE},
            "SOFIA": {"name": "en-US-Neural2-F", "gender": texttospeech.SsmlVoiceGender.FEMALE},
            "AI SUPERVISOR": {"name": "en-US-News-K", "gender": texttospeech.SsmlVoiceGender.FEMALE},
            "OFFICER 1": {"name": "en-US-Wavenet-C", "gender": texttospeech.SsmlVoiceGender.FEMALE},
            "OFFICER 2": {"name": "en-US-Wavenet-D", "gender": texttospeech.SsmlVoiceGender.MALE},
            "DETECTIVE HARRIS": {"name": "en-US-Wavenet-B", "gender": texttospeech.SsmlVoiceGender.MALE},
            "DETECTIVE RODRIGUEZ": {"name": "en-US-Wavenet-E", "gender": texttospeech.SsmlVoiceGender.FEMALE},
        }

    def generate_tts(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.client:
             raise RuntimeError("Google TTS client not initialized. Check credentials or use --mock.")

        logger.info("Generating TTS audio...")
        updated_scenes = []

        for scene in scenes:
            dialogue_list = scene.get("dialogue", [])
            for i, line in enumerate(dialogue_list):
                character = line["character"]
                text = line["text"]
                filename = f"{scene['id']}_{character}_{i}.wav".replace(" ", "_")
                filepath = os.path.join(self.output_dir, filename)

                # Skip if already exists
                if os.path.exists(filepath):
                    line["audio_file"] = filepath
                    continue

                voice_config = self.voice_map.get(character, self.voice_map["NARRATOR"])

                synthesis_input = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name=voice_config["name"],
                    ssml_gender=voice_config["gender"]
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16
                )

                try:
                    response = self.client.synthesize_speech(
                        input=synthesis_input, voice=voice, audio_config=audio_config
                    )

                    with open(filepath, "wb") as out:
                        out.write(response.audio_content)

                    line["audio_file"] = filepath
                    logger.info(f"Generated audio: {filepath}")

                except Exception as e:
                    logger.error(f"Failed to generate TTS for {character}: {e}")

            updated_scenes.append(scene)

        return updated_scenes

    def check_external_audio(self, scenes: List[Dict[str, Any]]) -> List[str]:
        missing_files = []
        for scene in scenes:
            for i, line in enumerate(scene.get("dialogue", [])):
                character = line["character"]
                expected_filename = f"{scene['id']}_{character}_{i}.wav".replace(" ", "_")
                filepath = os.path.join(self.output_dir, expected_filename)

                if not os.path.exists(filepath):
                    missing_files.append(expected_filename)
                else:
                    line["audio_file"] = filepath
        return missing_files


class MockAudioManager:
    def __init__(self):
        self.output_dir = Config.AUDIO_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_tts(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("MOCK: Generating audio...")
        for scene in scenes:
            for i, line in enumerate(scene.get("dialogue", [])):
                character = line["character"]
                filename = f"{scene['id']}_{character}_{i}.wav".replace(" ", "_")
                filepath = os.path.join(self.output_dir, filename)

                # Generate a 2-second silent WAV file
                self._create_silent_wav(filepath, duration_sec=2)
                line["audio_file"] = filepath
                logger.info(f"MOCK: Created {filepath}")
        return scenes

    def check_external_audio(self, scenes: List[Dict[str, Any]]) -> List[str]:
        return []

    def _create_silent_wav(self, filepath: str, duration_sec: int = 2, sample_rate: int = 44100):
        if os.path.exists(filepath):
            return

        num_samples = duration_sec * sample_rate
        # Create silent frames (all zeros)
        # linear16, mono
        data = struct.pack('<h', 0) * num_samples

        with wave.open(filepath, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(data)
