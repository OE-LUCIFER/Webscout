import time
import requests
import pathlib
import base64
import re
from io import BytesIO
from playsound import playsound
from webscout import exceptions
from webscout.AIbase import TTSProvider
from concurrent.futures import ThreadPoolExecutor, as_completed

class DeepgramTTS(TTSProvider): 
    """
    Text-to-speech provider using the DeepgramTTS API.
    """
    # Request headers
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    cache_dir = pathlib.Path("./audio_cache")
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

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """
        Custom sentence splitting method.
        Splits text into sentences based on common sentence-ending punctuation.
        
        Args:
            text (str): Input text to split into sentences.
        
        Returns:
            list[str]: List of sentences.
        """
        # Regular expression to split sentences
        # Handles .  !  ? and their variations with optional spaces and quotes
        sentence_pattern = r'(?<=[.!?])\s*'
        sentences = re.split(sentence_pattern, text.strip())
        
        # Remove any empty strings and strip whitespace
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        
        return sentences

    def tts(self, text: str, voice: str = "Brian", verbose:bool = True) -> str:
        """
        Converts text to speech using the DeepgramTTS API and saves it to a file.
        """
        assert (
            voice in self.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(self.all_voices.keys())}]"

        url = "https://deepgram.com/api/ttsAudioGeneration"
        filename = self.cache_dir / f"{int(time.time())}.mp3"  

        # Split text into sentences using custom method
        sentences = self._split_sentences(text)
        for index, sen in enumerate(sentences):
            print(f"{index}. Sentence: {sen}\n")

        # Function to request audio for each chunk
        def generate_audio_for_chunk(part_text: str, part_number: int):
            while True:
                try:
                    payload = {"text": part_text, "model": self.all_voices[voice]}
                    response = self.session.post(url=url, headers=self.headers, json=payload, stream=True, timeout=self.timeout)
                    response.raise_for_status()

                    # Create the audio_cache directory if it doesn't exist
                    self.cache_dir.mkdir(parents=True, exist_ok=True) 

                    response_data = response.json().get('data')
                    if response_data:
                        audio_data = base64.b64decode(response_data)
                        if verbose:
                            print(f"Chunk {part_number} processed successfully.")
                        return part_number, audio_data
                    else:
                        if verbose:
                            print(f"No data received for chunk {part_number}. Retrying...")
                except requests.RequestException as e:
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
                            print(f"Failed to generate audio for chunk {chunk_num}: {e}")

            # Combine audio chunks in the correct sequence
            combined_audio = BytesIO()
            for part_number in sorted(audio_chunks.keys()):
                combined_audio.write(audio_chunks[part_number])
                if verbose:
                    print(f"Added chunk {part_number} to the combined file.")

            # Save the combined audio data to a single file
            with open(filename, 'wb') as f:
                f.write(combined_audio.getvalue())
            if verbose:print(f"\033[1;93mFinal Audio Saved as {filename}.\033[0m")
            return filename.as_posix()

        except requests.exceptions.RequestException as e:
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
            raise RuntimeError(f"Error playing audio: {e}")

# Example usage
if __name__ == "__main__":
    deepgram = DeepgramTTS()
    text = "This is a test of the DeepgramTTS text-to-speech API. It supports multiple sentences. Let's see how it works!"

    print("Generating audio...")
    audio_file = deepgram.tts(text, voice="Brian") 

    print("Playing audio...")
    deepgram.play_audio(audio_file)