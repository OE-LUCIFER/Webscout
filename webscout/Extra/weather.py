import requests
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich import box
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.text import Text
from rich.columns import Columns

# Initialize Rich console with force terminal
console = Console(force_terminal=True)

def get_emoji(condition: str) -> str:
    """Get appropriate emoji for weather condition"""
    conditions = {
        'sunny': '*', 'clear': '*',
        'partly cloudy': '~', 'cloudy': '=',
        'rain': 'v', 'light rain': '.',
        'heavy rain': 'V', 'thunderstorm': 'V',
        'snow': '*', 'light snow': '*',
        'mist': '-', 'fog': '-',
        'overcast': '='
    }
    condition = condition.lower()
    for key, symbol in conditions.items():
        if key in condition:
            return symbol
    return '~'

def get_wind_arrow(degrees: int) -> str:
    """Convert wind degrees to arrow"""
    arrows = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = round(degrees / 45) % 8
    return arrows[index]

def format_temp(temp: str, scale='C') -> Text:
    """Format temperature with color based on value"""
    try:
        value = float(temp)
        if scale == 'C':
            if value <= 0:
                return Text(f"{temp}°{scale}", style="bold blue")
            elif value >= 30:
                return Text(f"{temp}°{scale}", style="bold red")
            else:
                return Text(f"{temp}°{scale}", style="bold green")
    except ValueError:
        pass
    return Text(f"{temp}°{scale}")

def create_current_weather_panel(data):
    """Create panel for current weather"""
    current = data['current_condition'][0]
    location = data['nearest_area'][0]
    location_name = f"{location['areaName'][0]['value']}, {location['country'][0]['value']}"
    
    weather_desc = current['weatherDesc'][0]['value']
    symbol = get_emoji(weather_desc)
    
    # Create weather info table
    table = Table(show_header=False, box=box.ROUNDED, expand=True)
    table.add_column("Label", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Location", f"@ {location_name}")
    table.add_row("Condition", f"{symbol} {weather_desc}")
    table.add_row("Temperature", 
                 f"{format_temp(current['temp_C'])} / {format_temp(current['temp_F'], 'F')}")
    table.add_row("Feels Like",
                 f"{format_temp(current['FeelsLikeC'])} / {format_temp(current['FeelsLikeF'], 'F')}")
    table.add_row("Humidity", f"~ {current['humidity']}%")
    
    wind_dir = get_wind_arrow(int(current['winddirDegree']))
    table.add_row("Wind", 
                 f"> {current['windspeedKmph']} km/h {wind_dir} ({current['winddir16Point']})")
    table.add_row("Visibility", f"O {current['visibility']} km")
    table.add_row("Pressure", f"# {current['pressure']} mb")
    
    return Panel(table, title="[bold]Current Weather[/]", border_style="blue")

def create_forecast_panel(data):
    """Create panel for weather forecast"""
    table = Table(show_header=True, box=box.ROUNDED, expand=True)
    table.add_column("Date", style="cyan")
    table.add_column("Condition")
    table.add_column("Temp (°C)")
    table.add_column("Rain")
    table.add_column("Wind")
    
    for day in data['weather'][:3]:
        date = datetime.strptime(day['date'], '%Y-%m-%d').strftime('%a, %b %d')
        # Get mid-day conditions (noon)
        noon = day['hourly'][4]
        condition = noon['weatherDesc'][0]['value']
        symbol = get_emoji(condition)
        temp_range = f"{day['mintempC']}° - {day['maxtempC']}°"
        rain_chance = f"v {noon['chanceofrain']}%"
        wind = f"> {noon['windspeedKmph']} km/h"
        
        table.add_row(
            date,
            f"{symbol} {condition}",
            temp_range,
            rain_chance,
            wind
        )
    
    return Panel(table, title="[bold]3-Day Forecast[/]", border_style="blue")

def get(location: str):
    """Get weather data with progress indicator"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Fetching weather data...", total=None)
        try:
            response = requests.get(f"https://wttr.in/{location}?format=j1", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]Error fetching weather data: {str(e)}[/]")
            return None

def display_weather(data):
    """Display weather information in a beautiful layout"""
    if not data:
        return
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="current", size=15),
        Layout(name="forecast", size=10)
    )
    
    # Update layout sections
    layout["current"].update(create_current_weather_panel(data))
    layout["forecast"].update(create_forecast_panel(data))
    
    # Print layout with a title
    console.print("\n")
    console.print(Align.center("[bold blue]Weather Report[/]"))
    console.print("\n")
    console.print(layout)
    console.print("\n")

def main():
    """Main function to run the weather app"""
    try:
        console.clear()
        console.print("\n[bold cyan]* Weather Information[/]\n")
        location = console.input("[cyan]Enter location: [/]")
        
        weather_data = get(location)
        if weather_data:
            display_weather(weather_data)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/] {str(e)}")

if __name__ == "__main__":
    main()