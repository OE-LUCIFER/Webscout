import requests
from rich.console import Console
from rich.table import Table
from yaspin import yaspin
from pyfiglet import figlet_format

console = Console()

def get(location):
    """Fetches weather data for the given location.

    Args:
        location (str): The location for which to fetch weather data.

    Returns:
        dict: A dictionary containing weather data if the request is successful,
              otherwise a string indicating the error.
    """
    url = f"https://wttr.in/{location}?format=j1"
    
    with yaspin(text="Fetching weather data...") as spinner:
        response = requests.get(url)
        spinner.ok("✅ ")

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
        console.print(f"[bold red]Error:[/] {weather_data}")
        return

    current = weather_data['current_condition'][0]
    location_name = weather_data['nearest_area'][0]['areaName'][0]['value']

    console.print(f"[bold blue]\n{figlet_format('Weather Report')}[/]\n", justify="center")
    console.print(f"[bold green]Weather in {location_name}:[/]\n")

    table = Table(show_header=False, show_lines=True)
    table.add_row("Temperature:", f"{current['temp_C']}°C / {current['temp_F']}°F")
    table.add_row("Condition:", current['weatherDesc'][0]['value'])
    table.add_row("Humidity:", f"{current['humidity']}%")
    table.add_row("Wind:", f"{current['windspeedKmph']} km/h, {current['winddir16Point']}")
    console.print(table)

    console.print(f"\n[bold green]Forecast:[/]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Date", style="dim", width=12)
    table.add_column("Temperature Range")
    table.add_column("Description")
    
    for day in weather_data['weather']:
        date = day['date']
        max_temp = day['maxtempC']
        min_temp = day['mintempC']
        desc = day['hourly'][4]['weatherDesc'][0]['value'] 
        table.add_row(date, f"{min_temp}°C to {max_temp}°C", desc)
    console.print(table)

