import time
import requests
import pathlib
from io import BytesIO
from playsound import playsound
from webscout import exceptions
from webscout.AIbase import TTSProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import utils

class ElevenlabsTTS(TTSProvider): 
    """
    Text-to-speech provider using the ElevenlabsTTS API.
    """
    # Request headers
    headers: dict[str, str] = {
        "User-Agent": LitAgent().random()
    }
    cache_dir = pathlib.Path("./audio_cache")
    all_voices: dict[str, str] = {"Brian": "nPczCjzI2devNBz1zQrb", "Alice":"Xb7hH8MSUJpSbSDYk0k2", "Bill":"pqHfZKP75CvOlQylNhV4", "Callum":"N2lVS1w4EtoT3dr4eOWO", "Charlie":"IKne3meq5aSn9XLyUdCD", "Charlotte":"XB0fDUnXU5powFXDhCwa", "Chris":"iP95p4xoKVk53GoZ742B", "Daniel":"onwK4e9ZLuTAKqWW03F9", "Eric":"cjVigY5qzO86Huf0OWal", "George":"JBFqnCBsd6RMkjVDRZzb", "Jessica":"cgSgspJ2msm6clMCkdW9", "Laura":"FGY2WhTYpPnrIDTdsKH5", "Liam":"TX3LPaxmHKxFdv7VOQHJ", "Lily":"pFZP5JQG7iQjIQuC4Bku", "Matilda":"XrExE9yKIg1WjnnlVkGX", "Sarah":"EXAVITQu4vr4xnSDxMaL", "Will":"bIHbv24MWmeRgasZH58o"}

    def __init__(self, timeout: int = 20, proxies: dict = None):
        """Initializes the ElevenlabsTTS TTS client."""
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.params = {'allow_unauthenticated': '1'}
        self.logger = LitLogger(
            name="ElevenlabsTTS",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.AURORA
        )

    def tts(self, text: str, voice: str = "Brian", verbose:bool = True) -> str:
        """
        Converts text to speech using the ElevenlabsTTS API and saves it to a file.
        """
        assert (
            voice in self.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(self.all_voices.keys())}]"

        filename = self.cache_dir / f"{int(time.time())}.mp3"  

        # Split text into sentences
        sentences = utils.split_sentences(text)

        # Function to request audio for each chunk
        def generate_audio_for_chunk(part_text: str, part_number: int):
            while True:
                try:
                    json_data = {'text': part_text, 'model_id': 'eleven_multilingual_v2'}
                    response = self.session.post(f'https://api.elevenlabs.io/v1/text-to-speech/{self.all_voices[voice]}',params=self.params, headers=self.headers, json=json_data, timeout=self.timeout)
                    response.raise_for_status()

                    # Create the audio_cache directory if it doesn't exist
                    self.cache_dir.mkdir(parents=True, exist_ok=True) 

                    # Check if the request was successful
                    if response.ok and response.status_code == 200:
                        if verbose:
                            self.logger.success(f"Chunk {part_number} processed successfully 🎉")
                        return part_number, response.content
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
    elevenlabs = ElevenlabsTTS()
    text = "This is a test of the ElevenlabsTTS text-to-speech API. It supports multiple sentences and advanced logging."

    elevenlabs.logger.info("Generating audio...")
    audio_file = elevenlabs.tts(text, voice="Brian") 

    elevenlabs.logger.info("Playing audio...")
    elevenlabs.play_audio(audio_file)