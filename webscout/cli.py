import csv
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import unquote
from pathlib import Path
import click
from curl_cffi import requests
import pyreqwest_impersonate as pri
from .webscout_search import WEBS
from .utils import json_dumps, json_loads
from .version import __version__

# Import rich for panel interface
from rich.panel import Panel
from rich.markdown import Markdown
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.align import Align
from rich.progress import track
from rich.prompt import Prompt, Confirm

logger = logging.getLogger(__name__)

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
    """Prints data using rich panels and markdown, asynchronously."""
    console = Console()
    if data:
        for i, e in enumerate(data, start=1):
            # Create a table for each result
            table = Table(title=f"{i}.", show_lines=True)
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")

            for j, (k, v) in enumerate(e.items(), start=1):
                if v:
                    width = 300 if k in ("content", "href", "image", "source", "thumbnail", "url") else 78
                    k = "language" if k == "detected_language" else k
                    text = click.wrap_text(
                        f"{v}", width=width, initial_indent="", subsequent_indent=" " * 12, preserve_paragraphs=True
                    )
                else:
                    text = v
                table.add_row(k, text)

            # Wrap the table in a panel with a title
            console.print(Panel(Align(table, align="left"), title=f"Result {i}", expand=False))
            console.print("\n")

def _sanitize_keywords(keywords):
    """Sanitizes keywords for file names and paths. Removes invalid characters like ':'. """
    keywords = (
        keywords.replace("filetype", "")
        .replace(":", "")  # Remove colons
        .replace('"', "'")
        .replace("site", "")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "")
    )
    return keywords

@click.group(chain=True)
def cli():
    """webscout CLI tool - Search the web with a rich UI."""
    pass


def safe_entry_point():
    try:
        cli()
    except Exception as ex:
        click.echo(f"{type(ex).__name__}: {ex}")


@cli.command()
def version():
    """Shows the current version of webscout."""
    console = Console()
    console.print(Panel(Text(f"webscout v{__version__}", style="cyan"), title="Version"))


@cli.command()
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def chat(proxy):
    """Interactive AI chat using DuckDuckGo's AI."""
    models = ["gpt-3.5", "claude-3-haiku", "llama-3-70b", "mixtral-8x7b"]
    client = WEBS(proxy=proxy)

    console = Console()
    console.print(Panel(Text("Available AI Models:", style="cyan"), title="DuckDuckGo AI Chat"))
    for idx, model in enumerate(models, start=1):
        console.print(f"{idx}. {model}")
    chosen_model_idx = Prompt.ask("Choose a model by entering its number [1]", choices=[str(i) for i in range(1, len(models) + 1)], default="1")
    chosen_model_idx = int(chosen_model_idx) - 1
    model = models[chosen_model_idx]
    console.print(f"Using model: {model}")

    while True:
        user_input = input(f"{'-'*78}\nYou: ")
        if not user_input.strip():
            break

        resp_answer = client.chat(keywords=user_input, model=model)
        text = click.wrap_text(resp_answer, width=78, preserve_paragraphs=True)
        console.print(Panel(Text(f"AI: {text}", style="green"), title="AI Response"))

        if "exit" in user_input.lower() or "quit" in user_input.lower():
            console.print(Panel(Text("Exiting chat session.", style="cyan"), title="Goodbye"))
            break


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for text search.")
@click.option("-r", "--region", default="wt-wt", help="Region (e.g., wt-wt, us-en, ru-ru) - See https://duckduckgo.com/params for more options.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]), help="Safe search level.")
@click.option("-t", "--timelimit", default=None, type=click.Choice(["d", "w", "m", "y"]), help="Time limit (d: day, w: week, m: month, y: year).")
@click.option("-m", "--max_results", default=20, help="Maximum number of results to retrieve (default: 20).")
@click.option("-b", "--backend", default="api", type=click.Choice(["api", "html", "lite"]), help="Backend to use (api, html, lite).")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def text(keywords, region, safesearch, timelimit, backend, max_results, proxy):
    """Performs a text search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).text(
        keywords=keywords,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        backend=backend,
        max_results=max_results,
    )
    _print_data(data)

@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for answers search.")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def answers(keywords, proxy):
    """Performs an answers search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).answers(keywords=keywords)
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for images search.")
@click.option("-r", "--region", default="wt-wt", help="Region (e.g., wt-wt, us-en, ru-ru) - See https://duckduckgo.com/params for more options.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]), help="Safe search level.")
@click.option("-t", "--timelimit", default=None, type=click.Choice(["Day", "Week", "Month", "Year"]), help="Time limit (Day, Week, Month, Year).")
@click.option("-size", "--size", default=None, type=click.Choice(["Small", "Medium", "Large", "Wallpaper"]), help="Image size (Small, Medium, Large, Wallpaper).")
@click.option(
    "-c",
    "--color",
    default=None,
    type=click.Choice(
        [
            "color",
            "Monochrome",
            "Red",
            "Orange",
            "Yellow",
            "Green",
            "Blue",
            "Purple",
            "Pink",
            "Brown",
            "Black",
            "Gray",
            "Teal",
            "White",
        ]
    ),
    help="Image color (color, Monochrome, Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Black, Gray, Teal, White).",
)
@click.option(
    "-type", "--type_image", default=None, type=click.Choice(["photo", "clipart", "gif", "transparent", "line"]), help="Image type (photo, clipart, gif, transparent, line)."
)
@click.option("-l", "--layout", default=None, type=click.Choice(["Square", "Tall", "Wide"]), help="Image layout (Square, Tall, Wide).")
@click.option(
    "-lic",
    "--license_image",
    default=None,
    type=click.Choice(["any", "Public", "Share", "Modify", "ModifyCommercially"]),
    help="Image license (any, Public, Share, Modify, ModifyCommercially).",
)
@click.option("-m", "--max_results", default=90, help="Maximum number of results to retrieve (default: 90).")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def images(
    keywords,
    region,
    safesearch,
    timelimit,
    size,
    color,
    type_image,
    layout,
    license_image,
    max_results,
    proxy,
):
    """Performs an images search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).images(
        keywords=keywords,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        size=size,
        color=color,
        type_image=type_image,
        layout=layout,
        license_image=license_image,
        max_results=max_results,
    )
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for videos search.")
@click.option("-r", "--region", default="wt-wt", help="Region (e.g., wt-wt, us-en, ru-ru) - See https://duckduckgo.com/params for more options.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]), help="Safe search level.")
@click.option("-t", "--timelimit", default=None, type=click.Choice(["d", "w", "m"]), help="Time limit (d: day, w: week, m: month).")
@click.option("-res", "--resolution", default=None, type=click.Choice(["high", "standart"]), help="Video resolution (high, standart).")
@click.option("-d", "--duration", default=None, type=click.Choice(["short", "medium", "long"]), help="Video duration (short, medium, long).")
@click.option("-lic", "--license_videos", default=None, type=click.Choice(["creativeCommon", "youtube"]), help="Video license (creativeCommon, youtube).")
@click.option("-m", "--max_results", default=50, help="Maximum number of results to retrieve (default: 50).")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def videos(keywords, region, safesearch, timelimit, resolution, duration, license_videos, max_results, proxy):
    """Performs a videos search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).videos(
        keywords=keywords,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        resolution=resolution,
        duration=duration,
        license_videos=license_videos,
        max_results=max_results,
    )
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for news search.")
@click.option("-r", "--region", default="wt-wt", help="Region (e.g., wt-wt, us-en, ru-ru) - See https://duckduckgo.com/params for more options.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]), help="Safe search level.")
@click.option("-t", "--timelimit", default=None, type=click.Choice(["d", "w", "m", "y"]), help="Time limit (d: day, w: week, m: month, y: year).")
@click.option("-m", "--max_results", default=25, help="Maximum number of results to retrieve (default: 25).")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def news(keywords, region, safesearch, timelimit, max_results, proxy):
    """Performs a news search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).news(
        keywords=keywords, region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results
    )
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for maps search.")
@click.option("-p", "--place", default=None, help="Simplified search - if set, the other parameters are not used.")
@click.option("-s", "--street", default=None, help="House number/street.")
@click.option("-c", "--city", default=None, help="City of search.")
@click.option("-county", "--county", default=None, help="County of search.")
@click.option("-state", "--state", default=None, help="State of search.")
@click.option("-country", "--country", default=None, help="Country of search.")
@click.option("-post", "--postalcode", default=None, help="Postal code of search.")
@click.option("-lat", "--latitude", default=None, help="Geographic coordinate (north-south position).")
@click.option("-lon", "--longitude", default=None, help="Geographic coordinate (east-west position); if latitude and longitude are set, the other parameters are not used.")
@click.option("-r", "--radius", default=0, help="Expand the search square by the distance in kilometers.")
@click.option("-m", "--max_results", default=50, help="Number of results (default: 50).")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def maps(
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
    proxy,
):
    """Performs a maps search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).maps(
        keywords=keywords,
        place=place,
        street=street,
        city=city,
        county=county,
        state=state,
        country=country,
        postalcode=postalcode,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        max_results=max_results,
    )
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Text for translation.")
@click.option("-f", "--from_", help="Language to translate from (defaults automatically).")
@click.option("-t", "--to", default="en", help="Language to translate to (default: 'en').")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def translate(keywords, from_, to, proxy):
    """Performs translation using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).translate(keywords=keywords, from_=from_, to=to)
    _print_data(data)


@cli.command()
@click.option("-k", "--keywords", required=True, help="Keywords for query.")
@click.option("-r", "--region", default="wt-wt", help="Region (e.g., wt-wt, us-en, ru-ru) - See https://duckduckgo.com/params for more options.")
@click.option("-p", "--proxy", default=None, help="Proxy to send requests (e.g., socks5://localhost:9150)")
def suggestions(keywords, region, proxy):
    """Performs a suggestions search using DuckDuckGo API with a rich UI."""
    data = WEBS(proxy=proxy).suggestions(keywords=keywords, region=region)
    _print_data(data)


if __name__ == "__main__":
    cli(prog_name="WEBS")