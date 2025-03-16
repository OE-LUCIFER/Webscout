##################################################################################
##  Modified version of code written by t.me/infip1217                          ##
##################################################################################
import time
import requests
import pathlib
import tempfile
from io import BytesIO
from webscout import exceptions
from webscout.AIbase import TTSProvider
from webscout.litagent import LitAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import utils

class SpeechMaTTS(TTSProvider):
    """
    Text-to-speech provider using the SpeechMa API.
    """
    # Request headers
    headers = {
        "accept": "*/*",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,en-AU;q=0.6",
        "content-type": "application/json",
        "origin": "https://speechma.com",
        "priority": "u=1, i",
        "User-Agent": LitAgent().random()
    }
    
    # Available voices with their IDs
    all_voices = {
        "Ava": "voice-110",     # Multilingual female voice
        "Emma": "voice-115",    # Multilingual female voice
        "Andrew": "voice-107",  # Multilingual male voice
        "Brian": "voice-112"    # Multilingual male voice
    }

    def __init__(self, timeout: int = 20, proxies: dict = None):
        """Initializes the SpeechMa TTS client."""
        self.api_url = "https://speechma.com/com.api/tts-api.php"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix="webscout_tts_")

    def tts(self, text: str, voice: str = "Emma", pitch: int = 0, rate: int = 0, verbose: bool = False) -> str:
        """
        Converts text to speech using the SpeechMa API and saves it to a file.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use for TTS (default: "Emma")
            pitch (int): Voice pitch adjustment (-10 to 10, default: 0)
            rate (int): Voice rate/speed adjustment (-10 to 10, default: 0)
            verbose (bool): Whether to print progress messages (default: True)

        Returns:
            str: Path to the generated audio file
        
        Raises:
            exceptions.FailedToGenerateResponseError: If there is an error generating or saving the audio.
        """
        assert (
            voice in self.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(self.all_voices.keys())}]"

        filename = pathlib.Path(tempfile.mktemp(suffix=".mp3", dir=self.temp_dir))
        
        # Get the voice ID
        voice_id = self.all_voices[voice]
        
        if verbose:
            print(f"[debug] Using voice: {voice} (ID: {voice_id})")
        
        # Split text into sentences for better processing
        sentences = utils.split_sentences(text)
        
        if verbose:
            print(f"[debug] Text split into {len(sentences)} sentences")
        
        # Function to request audio for each chunk
        def generate_audio_for_chunk(part_text: str, part_number: int):
            while True:
                try:
                    if verbose:
                        print(f"[debug] Processing chunk {part_number}: '{part_text[:30]}...'")
                    
                    # Prepare payload for this sentence
                    payload = {
                        "text": part_text,
                        "voice": voice_id,
                        "pitch": pitch,
                        "rate": rate
                    }
                    
                    response = self.session.post(
                        self.api_url, 
                        headers=self.headers, 
                        json=payload, 
                        timeout=self.timeout
                    )
                    response.raise_for_status()

                    # Check if the request was successful
                    if response.ok and response.status_code == 200:
                        # Ensure we got audio data
                        if len(response.content) > 100:  # Basic check for actual content
                            if verbose:
                                print(f"[debug] Chunk {part_number} processed successfully")
                            return part_number, response.content
                        else:
                            if verbose:
                                print(f"[debug] Received too small response for chunk {part_number}. Retrying...")
                    else:
                        if verbose:
                            print(f"[debug] Failed request for chunk {part_number} (status code: {response.status_code}). Retrying...")
                    
                    # If we get here, something went wrong with the request
                    time.sleep(1)
                except requests.RequestException as e:
                    if verbose:
                        print(f"[debug] Error for chunk {part_number}: {e}. Retrying...")
                    time.sleep(1)
        
        try:
            if verbose:
                print(f"[debug] Starting concurrent audio generation for {len(sentences)} chunks")
            
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
                        if verbose:
                            print(f"[debug] Received audio data for chunk {part_number}")
                    except Exception as e:
                        if verbose:
                            print(f"[debug] Failed to generate audio for chunk {chunk_num}: {e}")

            if verbose:
                print(f"[debug] Successfully processed {len(audio_chunks)}/{len(sentences)} chunks")

            # Combine audio chunks in the correct sequence
            combined_audio = BytesIO()
            for part_number in sorted(audio_chunks.keys()):
                combined_audio.write(audio_chunks[part_number])
                if verbose:
                    print(f"[debug] Added chunk {part_number} to the combined file")

            # Save the combined audio data to a single file
            with open(filename, 'wb') as f:
                f.write(combined_audio.getvalue())
                
            if verbose:
                print(f"[debug] Final audio saved as {filename}")
                
            return filename.as_posix()

        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"[debug] Failed to perform the operation: {e}")
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to perform the operation: {e}"
            )

# Example usage
if __name__ == "__main__":
    speechma = SpeechMaTTS()
    text = "This is a test of the SpeechMa text-to-speech API. It supports multiple sentences."
    audio_file = speechma.tts(text, voice="Emma")
    print(f"Audio saved to: {audio_file}")
