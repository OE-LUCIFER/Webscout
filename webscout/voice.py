import requests
import typing

def play_audio(message: str, voice: str = "Brian") -> typing.Union[str, typing.NoReturn]:
    """
    Text to speech using StreamElements API

    Parameters:
        message (str): The text to convert to speech
        voice (str): The voice to use for speech synthesis. Default is "Brian".

    Returns:
        result (Union[str, None]): Temporary file path or None in failure
    """
    # Base URL for provider API
    url: str = f"https://api.streamelements.com/kappa/v2/speech?voice={voice}&text={{{message}}}"
    
    # Request headers
    headers: typing.Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    # Try to send request or return None on failure
    try:
        result = requests.get(url=url, headers=headers)
        return result.content
    except:
        return None