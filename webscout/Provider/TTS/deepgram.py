import time
import requests
import pathlib
import base64
import tempfile
from io import BytesIO
from webscout import exceptions
from webscout.AIbase import TTSProvider
from concurrent.futures import ThreadPoolExecutor, as_completed
from webscout.litagent import LitAgent
from . import utils 

class DeepgramTTS(TTSProvider): 
    """
    Text-to-speech provider using the DeepgramTTS API.
    """
    # Request headers
    headers: dict[str, str] = {
        "User-Agent": LitAgent().random()
    }
    all_voices: dict[str, str] = {
        "Asteria": "aura-asteria-en", "Arcas": "aura-arcas-en", "Luna": "aura-luna-en",
        "Zeus": "aura-zeus-en", "Orpheus": "aura-orpheus-en", "Angus": "aura-angus-en",
        "Athena": "aura-athena-en", "Helios": "aura-helios-en", "Hera": "aura-hera-en",
        "Orion": "aura-orion-en", "Perseus": "aura-perseus-en", "Stella": "aura-stella-en"
    }

    def __init__(self, timeout: int = 20, proxies: dict = None):
        """Initializes the DeepgramTTS TTS client."""
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix="webscout_tts_")

    def tts(self, text: str, voice: str = "Brian", verbose: bool = True) -> str:
        """
        Converts text to speech using the DeepgramTTS API and saves it to a file.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use for TTS (default: "Brian")
            verbose (bool): Whether to print progress messages (default: True)

        Returns:
            str: Path to the generated audio file

        Raises:
            AssertionError: If the specified voice is not available
            requests.RequestException: If there's an error communicating with the API
            RuntimeError: If there's an error processing the audio
        """
        assert (
            voice in self.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(self.all_voices.keys())}]"

        url = "https://deepgram.com/api/ttsAudioGeneration"
        filename = pathlib.Path(tempfile.mktemp(suffix=".mp3", dir=self.temp_dir))

        # Split text into sentences using the utils module
        sentences = utils.split_sentences(text)
        if verbose:
            for index, sen in enumerate(sentences):
                print(f"[debug] Sentence {index}: {sen}")

        def generate_audio_for_chunk(part_text: str, part_number: int):
            """
            Generate audio for a single chunk of text.

            Args:
                part_text (str): The text chunk to convert
                part_number (int): The chunk number for ordering

            Returns:
                tuple: (part_number, audio_data)

            Raises:
                requests.RequestException: If there's an API error
            """
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    payload = {"text": part_text, "model": self.all_voices[voice]}
                    response = self.session.post(
                        url=url, 
                        headers=self.headers, 
                        json=payload, 
                        stream=True, 
                        timeout=self.timeout
                    )
                    response.raise_for_status()

                    response_data = response.json().get('data')
                    if response_data:
                        audio_data = base64.b64decode(response_data)
                        if verbose:
                            print(f"[debug] Chunk {part_number} processed successfully")
                        return part_number, audio_data
                    
                    if verbose:
                        print(f"[debug] No data received for chunk {part_number}. Attempt {retry_count + 1}/{max_retries}")
                    
                except requests.RequestException as e:
                    if verbose:
                        print(f"[debug] Error processing chunk {part_number}: {str(e)}. Attempt {retry_count + 1}/{max_retries}")
                    if retry_count == max_retries - 1:
                        raise
                
                retry_count += 1
                time.sleep(1)
            
            raise RuntimeError(f"Failed to generate audio for chunk {part_number} after {max_retries} attempts")

        try:
            # Using ThreadPoolExecutor to handle requests concurrently
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(generate_audio_for_chunk, sentence.strip(), chunk_num): chunk_num 
                    for chunk_num, sentence in enumerate(sentences, start=1)
                }
                
                # Dictionary to store results with order preserved
                audio_chunks = {}

                for future in as_completed(futures):
                    chunk_num = futures[future]
                    try:
                        part_number, audio_data = future.result()
                        audio_chunks[part_number] = audio_data
                    except Exception as e:
                        raise RuntimeError(f"Failed to generate audio for chunk {chunk_num}: {str(e)}")

                # Combine all audio chunks in order
                with open(filename, 'wb') as f:
                    for chunk_num in sorted(audio_chunks.keys()):
                        f.write(audio_chunks[chunk_num])

                if verbose:
                    print(f"[debug] Audio saved to {filename}")
                return str(filename)

        except Exception as e:
            print(f"[debug] Failed to generate audio: {str(e)}") if verbose else None
            raise RuntimeError(f"Failed to generate audio: {str(e)}")

# Example usage
if __name__ == "__main__":
    deepgram = DeepgramTTS()
    text = "This is a test of the DeepgramTTS text-to-speech API. It supports multiple sentences. Let's see how it works!"

    print("[debug] Generating audio...")
    audio_file = deepgram.tts(text, voice="Asteria") 
    print(f"Audio saved to: {audio_file}")