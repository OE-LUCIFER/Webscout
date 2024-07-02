import requests

def get(location):
    """Fetches weather data for the given location.

    Args:
        location (str): The location for which to fetch weather data.

    Returns:
        dict: A dictionary containing weather data if the request is successful,
              otherwise a string indicating the error.
    """
    url = f"https://wttr.in/{location}?format=j1"
    
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: Unable to fetch weather data. Status code: {response.status_code}"

def print_weather(weather_data):
    """Prints the weather data in a user-friendly format.

    Args:
        weather_data (dict or str): The weather data returned from get_weather() 
                                  or an error message.
    """
    if isinstance(weather_data, str):
        print(weather_data)
        return

    current = weather_data['current_condition'][0]
    location_name = weather_data['nearest_area'][0]['areaName'][0]['value']

    print(f"Weather in {location_name}:")
    print(f"Temperature: {current['temp_C']}°C / {current['temp_F']}°F")
    print(f"Condition: {current['weatherDesc'][0]['value']}")
    print(f"Humidity: {current['humidity']}%")
    print(f"Wind: {current['windspeedKmph']} km/h, {current['winddir16Point']}")


    print("\nForecast:")
    for day in weather_data['weather']:
        date = day['date']
        max_temp = day['maxtempC']
        min_temp = day['mintempC']
        desc = day['hourly'][4]['weatherDesc'][0]['value'] 
        print(f"{date}: {min_temp}°C to {max_temp}°C, {desc}")
