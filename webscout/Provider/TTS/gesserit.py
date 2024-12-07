import time
import requests
import pathlib
import base64
from io import BytesIO
from playsound import playsound
from webscout import exceptions
from webscout.AIbase import TTSProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import utils

class GesseritTTS(TTSProvider): 
    """Text-to-speech provider using the GesseritTTS API."""
    # Request headers
    headers: dict[str, str] = {
        "User-Agent": LitAgent().random()
    }
    cache_dir = pathlib.Path("./audio_cache")
    all_voices: dict[str, str] = {
        "Emma": "en_us_001",  # Female Voice
        "Liam": "en_us_006",  # Male Voice
        "Noah": "en_us_007",  # Male Voice
        "Oliver": "en_us_009",  # Male Voice
        "Elijah": "en_us_010",  # Male Voice
        "James": "en_male_narration",  # Male Voice
        "Charlie": "en_male_funny",  # Male Voice
        "Sophia": "en_female_emotional",  # Female Voice
        "Cody": "en_male_cody",  # Male Voice
    }

    def __init__(self, timeout: int = 20, proxies: dict = None):
        """Initializes the GesseritTTS TTS client."""
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.logger = LitLogger(
            name="GesseritTTS",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.AURORA
        )

    def tts(self, text: str, voice: str = "Oliver", verbose:bool = True) -> str:
        """Converts text to speech using the GesseritTTS API and saves it to a file."""
        assert (
            voice in self.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(self.all_voices.keys())}]"

        filename = self.cache_dir / f"{int(time.time())}.mp3"

        voice_id = self.all_voices[voice]

        # Split text into sentences
        sentences = utils.split_sentences(text)

        # Function to request audio for each chunk
        def generate_audio_for_chunk(part_text: str, part_number: int):
            while True:
                try:
                    payload = {
                        "text": part_text,
                        "voice": voice_id
                    }
                    response = self.session.post('https://gesserit.co/api/tiktok-tts', headers=self.headers, json=payload, timeout=self.timeout)
                    response.raise_for_status()

                    # Create the audio_cache directory if it doesn't exist
                    self.cache_dir.mkdir(parents=True, exist_ok=True) 

                    # Check if the request was successful
                    if response.ok and response.status_code == 200:
                        data = response.json()
                        audio_base64 = data["audioUrl"].split(",")[1]
                        audio_data = base64.b64decode(audio_base64)
                        if verbose:
                            self.logger.success(f"Chunk {part_number} processed successfully 🎉")
                        return part_number, audio_data
                    else:
                        if verbose:
                            self.logger.warning(f"No data received for chunk {part_number}. Retrying...")
                except requests.RequestException as e:
                    if verbose:
                        self.logger.error(f"Error for chunk {part_number}: {e}. Retrying... 🔄")
                    time.sleep(1)
        try:
            # Using ThreadPoolExecutor to handle requests concurrently
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(generate_audio_for_chunk, sentence.strip(), chunk_num): chunk_num 
                        for chunk_num, sentence in enumerate(sentences, start=1)}
                
                # Dictionary to store results with order preserved
                audio_chunks = {}

                for future in as_completed(futures):
                    chunk_num = futures[future]
                    try:
                        part_number, audio_data = future.result()
                        audio_chunks[part_number] = audio_data  # Store the audio data in correct sequence
                    except Exception as e:
                        if verbose:
                            self.logger.error(f"Failed to generate audio for chunk {chunk_num}: {e} 🚨")

            # Combine audio chunks in the correct sequence
            combined_audio = BytesIO()
            for part_number in sorted(audio_chunks.keys()):
                combined_audio.write(audio_chunks[part_number])
                if verbose:
                    self.logger.debug(f"Added chunk {part_number} to the combined file.")

            # Save the combined audio data to a single file
            with open(filename, 'wb') as f:
                f.write(combined_audio.getvalue())
            if verbose:
                self.logger.info(f"Final Audio Saved as {filename} 🔊")
            return filename.as_posix()

        except requests.exceptions.RequestException as e:
            self.logger.critical(f"Failed to perform the operation: {e} 🚨")
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to perform the operation: {e}"
            )
        
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
            self.logger.error(f"Error playing audio: {e} 🔇")
            raise RuntimeError(f"Error playing audio: {e}")

# Example usage
if __name__ == "__main__":
    gesserit = GesseritTTS()
    text = "This is a test of the GesseritTTS text-to-speech API. It supports multiple sentences and advanced logging."

    gesserit.logger.info("Generating audio...")
    audio_file = gesserit.tts(text, voice="Oliver") 

    gesserit.logger.info("Playing audio...")
    gesserit.play_audio(audio_file)