import time
from pathlib import Path
from typing import Generator
from playsound import playsound
from webscout import exceptions
from webscout.AIbase import TTSProvider

from gradio_client import Client
import os


class ParlerTTS(TTSProvider):
    """
    A class to interact with the Parler TTS API through Gradio Client.
    """

    def __init__(self, timeout: int = 20, proxies: dict = None):
        """Initializes the Parler TTS client."""
        self.api_endpoint = "/gen_tts"
        self.client = Client("parler-tts/parler_tts")  # Initialize the Gradio client
        self.timeout = timeout
        self.audio_cache_dir = Path("./audio_cache")

    def tts(self, text: str, description: str = "", use_large: bool = False) -> str:
        """
        Converts text to speech using the Parler TTS API.

        Args:
            text (str): The text to be converted to speech.
            description (str, optional): Description of the desired voice characteristics. Defaults to "".
            use_large (bool, optional): Whether to use the large model variant. Defaults to False.

        Returns:
            str: The filename of the saved audio file.

        Raises:
            exceptions.FailedToGenerateResponseError: If there is an error generating or saving the audio.
        """
        filename = self.audio_cache_dir / f"{int(time.time())}.wav"

        try:
            result = self.client.predict(
                text=text,
                description=description,
                use_large=use_large,
                api_name=self.api_endpoint,
            )

            if isinstance(result, bytes):
                audio_bytes = result
            elif isinstance(result, str) and os.path.isfile(result):
                with open(result, "rb") as f:
                    audio_bytes = f.read()
            else:
                raise ValueError(f"Unexpected response from API: {result}")

            self._save_audio(audio_bytes, filename)
            return filename.as_posix()

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Error generating audio after multiple retries: {e}"
            ) from e

    def _save_audio(self, audio_data: bytes, filename: Path):
        """Saves the audio data to a WAV file in the audio cache directory."""
        try:
            self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
            with open(filename, "wb") as f:
                f.write(audio_data)

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Error saving audio: {e}")

    def play_audio(self, filename: str):
        """
        Plays an audio file using playsound.

        Args:
            filename (str): The path to the audio file.

        Raises:
            RuntimeError: If there is an error playing the audio.
        """
        try:
            playsound(filename)
        except Exception as e:
            raise RuntimeError(f"Error playing audio: {e}")


# Example usage
if __name__ == "__main__":
    parlertts = ParlerTTS()
    text = (
        "All of the data, pre-processing, training code, and weights are released "
        "publicly under a permissive license, enabling the community to build on our work "
        "and develop their own powerful models."
    )
    voice_description = (
        "Laura's voice is monotone yet slightly fast in delivery, with a very close "
        "recording that almost has no background noise."
    )

    print("Generating audio...")
    audio_file = parlertts.tts(text, description=voice_description, use_large=False)

    print("Playing audio...")
    parlertts.play_audio(audio_file)