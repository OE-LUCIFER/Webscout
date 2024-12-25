import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import unquote
from pathlib import Path
from .swiftcli import CLI, option, argument, group
from curl_cffi import requests
import pyreqwest_impersonate as pri
from .webscout_search import WEBS
from .utils import json_dumps, json_loads
from .version import __version__
from .Litlogger import LitLogger, LogFormat, ColorScheme
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.align import Align
from rich.progress import track, Progress
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from pyfiglet import figlet_format

logger = LitLogger(
    name="webscout",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK,
    console_output=True
)

COLORS = {
    0: "black",
    1: "red",
    2: "green",
    3: "yellow",
    4: "blue",
    5: "magenta",
    6: "cyan",
    7: "bright_black",
    8: "bright_red",
    9: "bright_green",
    10: "bright_yellow",
    11: "bright_blue",
    12: "bright_magenta",
    13: "bright_cyan",
    14: "white",
    15: "bright_white",
}

def _print_data(data):
    """Prints data using rich panels and markdown."""
    console = Console()
    if data:
        for i, e in enumerate(data, start=1):
            table = Table(show_header=False, show_lines=True, expand=True, box=None)
            table.add_column("Key", style="cyan", no_wrap=True, width=15)
            table.add_column("Value", style="white")

            for j, (k, v) in enumerate(e.items(), start=1):
                if v:
                    width = 300 if k in ("content", "href", "image", "source", "thumbnail", "url") else 78
                    k = "language" if k == "detected_language" else k
                    text = Text(str(v), style="white")
                    text = text.wrap(width=width, console=console)
                else:
                    text = Text(str(v), style="white")
                table.add_row(k, text)

            console.print(Panel(table, title=f"Result {i}", expand=False, style="green on black"))
            console.print("\n")

# Initialize CLI app
app = CLI(name="webscout", help="Search the web with a rich UI", version=__version__)

@app.command()
def version():
    """Show the version of webscout."""
    console = Console()
    console.print(f"[bold green]webscout[/bold green] version: {__version__}")

@app.command()
@option("--proxy", help="Proxy URL to use for requests")
@option("--model", "-m", help="AI model to use", default="gpt-4o-mini", type=str)
def chat(proxy: str = None, model: str = "gpt-4o-mini"):
    """Interactive AI chat using DuckDuckGo's AI."""
    webs = WEBS(proxy=proxy)
    console = Console()
    
    # Display header
    console.print(f"[bold blue]{figlet_format('Webscout Chat')}[/]\n", justify="center")
    console.print(f"[bold green]Using model:[/] {model}\n")
    console.print("[cyan]Type your message and press Enter. Press Ctrl+C or type 'exit' to quit.[/]\n")
    
    # Start chat loop
    try:
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input or user_input.lower() in ['exit', 'quit']:
                    break
                    
                logger.info(f"Sending message to {model}")
                response = webs.chat(keywords=user_input, model=model)
                console.print(f"\nAI: {response}\n")
                logger.success("Received response from AI")
                
            except Exception as e:
                logger.error(f"Error in chat: {str(e)}")
                console.print(f"[bold red]Error:[/] {str(e)}\n")
                
    except KeyboardInterrupt:
        logger.info("Chat session terminated by user")
        
    console.print("\n[cyan]Chat session ended. Goodbye![/]")

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--region", "-r", help="Region for search results", default="wt-wt")
@option("--safesearch", "-s", help="SafeSearch setting", default="moderate")
@option("--timelimit", "-t", help="Time limit for results", default=None)
@option("--backend", "-b", help="Search backend to use", default="api")
@option("--max-results", "-m", help="Maximum number of results", type=int, default=25)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def text(keywords: str, region: str, safesearch: str, timelimit: str, backend: str, max_results: int, proxy: str = None):
    """Perform a text search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.text(keywords, region, safesearch, timelimit, backend, max_results)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in text search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def answers(keywords: str, proxy: str = None):
    """Perform an answers search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.answers(keywords)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in answers search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--region", "-r", help="Region for search results", default="wt-wt")
@option("--safesearch", "-s", help="SafeSearch setting", default="moderate")
@option("--timelimit", "-t", help="Time limit for results", default=None)
@option("--size", "-size", help="Image size", default=None)
@option("--color", "-c", help="Image color", default=None)
@option("--type", "-type", help="Image type", default=None)
@option("--layout", "-l", help="Image layout", default=None)
@option("--license", "-lic", help="Image license", default=None)
@option("--max-results", "-m", help="Maximum number of results", type=int, default=90)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def images(
    keywords: str,
    region: str,
    safesearch: str,
    timelimit: str,
    size: str,
    color: str,
    type: str,
    layout: str,
    license: str,
    max_results: int,
    proxy: str = None,
):
    """Perform an images search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.images(keywords, region, safesearch, timelimit, size, color, type, layout, license, max_results)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in images search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--region", "-r", help="Region for search results", default="wt-wt")
@option("--safesearch", "-s", help="SafeSearch setting", default="moderate")
@option("--timelimit", "-t", help="Time limit for results", default=None)
@option("--resolution", "-res", help="Video resolution", default=None)
@option("--duration", "-d", help="Video duration", default=None)
@option("--license", "-lic", help="Video license", default=None)
@option("--max-results", "-m", help="Maximum number of results", type=int, default=50)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def videos(
    keywords: str,
    region: str,
    safesearch: str,
    timelimit: str,
    resolution: str,
    duration: str,
    license: str,
    max_results: int,
    proxy: str = None,
):
    """Perform a videos search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.videos(keywords, region, safesearch, timelimit, resolution, duration, license, max_results)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in videos search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--region", "-r", help="Region for search results", default="wt-wt")
@option("--safesearch", "-s", help="SafeSearch setting", default="moderate")
@option("--timelimit", "-t", help="Time limit for results", default=None)
@option("--max-results", "-m", help="Maximum number of results", type=int, default=25)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def news(keywords: str, region: str, safesearch: str, timelimit: str, max_results: int, proxy: str = None):
    """Perform a news search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.news(keywords, region, safesearch, timelimit, max_results)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in news search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--place", "-p", help="Simplified search - if set, the other parameters are not used")
@option("--street", "-s", help="House number/street")
@option("--city", "-c", help="City of search")
@option("--county", "-county", help="County of search")
@option("--state", "-state", help="State of search")
@option("--country", "-country", help="Country of search")
@option("--postalcode", "-post", help="Postal code of search")
@option("--latitude", "-lat", help="Geographic coordinate (north-south position)")
@option("--longitude", "-lon", help="Geographic coordinate (east-west position); if latitude and longitude are set, the other parameters are not used")
@option("--radius", "-r", help="Expand the search square by the distance in kilometers", type=int, default=0)
@option("--max-results", "-m", help="Number of results", type=int, default=50)
@option("--proxy", "-p", help="Proxy URL to use for requests")
def maps(
    keywords: str,
    place: str,
    street: str,
    city: str,
    county: str,
    state: str,
    country: str,
    postalcode: str,
    latitude: str,
    longitude: str,
    radius: int,
    max_results: int,
    proxy: str = None,
):
    """Perform a maps search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.maps(
            keywords,
            place,
            street,
            city,
            county,
            state,
            country,
            postalcode,
            latitude,
            longitude,
            radius,
            max_results,
        )
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in maps search: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Text for translation", required=True)
@option("--from", "-f", help="Language to translate from (defaults automatically)")
@option("--to", "-t", help="Language to translate to (default: 'en')", default="en")
@option("--proxy", "-p", help="Proxy URL to use for requests")
def translate(keywords: str, from_: str, to: str, proxy: str = None):
    """Perform translation using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.translate(keywords, from_, to)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        raise e

@app.command()
@option("--keywords", "-k", help="Search keywords", required=True)
@option("--region", "-r", help="Region for search results", default="wt-wt")
@option("--proxy", "-p", help="Proxy URL to use for requests")
def suggestions(keywords: str, region: str, proxy: str = None):
    """Perform a suggestions search using DuckDuckGo API."""
    webs = WEBS(proxy=proxy)
    try:
        results = webs.suggestions(keywords, region)
        _print_data(results)
    except Exception as e:
        logger.error(f"Error in suggestions search: {e}")
        raise e

def main():
    """Main entry point for the CLI."""
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
