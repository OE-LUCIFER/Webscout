import requests

def get(location):
    """Fetches ASCII art weather data for the given location.
    Args:
        location (str): The location for which to fetch weather data.

    Returns:
        str: ASCII art weather report if the request is successful,
             otherwise an error message.
    """
    url = f"https://wttr.in/{location}"
    response = requests.get(url, headers={'User-Agent': 'curl'}) 

    if response.status_code == 200:
        return "\n".join(response.text.splitlines()[:-1]) 
    else:
        return f"Error: Unable to fetch weather data. Status code: {response.status_code}"
