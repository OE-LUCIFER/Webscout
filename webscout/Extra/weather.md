
## ☀️ Weather Toolkit

Webscout provides tools to retrieve weather information in various formats.

### 🌡️ Current Weather Data

Retrieve structured current weather information for any location.

```python
from webscout.Extra import weather

# Get weather for a specific location
forecast = weather.get("London")

# Access current conditions
print(f"Current weather: {forecast.summary}")

# Access temperature details
if forecast.current_condition:
    print(f"Temperature: {forecast.current_condition.temp_c}°C / {forecast.current_condition.temp_f}°F")
    print(f"Feels like: {forecast.current_condition.feels_like_c}°C")
    print(f"Conditions: {forecast.current_condition.weather_desc}")
    print(f"Wind: {forecast.current_condition.wind_speed_kmph} km/h from {forecast.current_condition.wind_direction}")
```

### 🔮 Weather Forecast

Access forecast information for today and upcoming days.

```python
from webscout.Extra import weather

forecast = weather.get("Tokyo")

# Today's forecast
if forecast.today:
    print(f"Today ({forecast.today.date_formatted}):")
    print(f"  Temperature range: {forecast.today.min_temp_c}°C - {forecast.today.max_temp_c}°C")
    print(f"  Sunrise: {forecast.today.sunrise}, Sunset: {forecast.today.sunset}")
    
    # Access noon forecast
    if forecast.today.hourly and len(forecast.today.hourly) > 4:
        noon = forecast.today.hourly[4]  # Noon (12:00) is usually index 4
        print(f"  Noon conditions: {noon.weather_desc}")
        print(f"  Chance of rain: {noon.chance_of_rain}%")

# Tomorrow's forecast
if forecast.tomorrow:
    print(f"\nTomorrow ({forecast.tomorrow.date_formatted}):")
    print(f"  Temperature range: {forecast.tomorrow.min_temp_c}°C - {forecast.tomorrow.max_temp_c}°C")
```

### 🎨 ASCII Art Weather

Retrieve weather information as ASCII art.

```python
from webscout.Extra import weather_ascii

# Get ASCII art weather 
result = weather_ascii.get("Paris")

# Display the ASCII art weather
print(result.content)
```