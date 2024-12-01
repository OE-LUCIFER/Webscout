"""
Webscout Update Checker
A utility to check and compare Webscout versions
"""

import requests
import re
import subprocess
import sys
import os
from packaging import version
from typing import Optional

from webscout import LitLogger, LogFormat, ColorScheme

# Initialize logger with custom format
CUSTOM_FORMAT = """{message}"""

logger = LitLogger(
    name="WebscoutUpdate",
    format=CUSTOM_FORMAT,
    color_scheme=ColorScheme.OCEAN,
    level_styles={
        "TRACE": "DIM",
        "DEBUG": "NORMAL",
        "INFO": "BOLD",
        "SUCCESS": "BOLD",
        "WARNING": "BOLD",
        "ERROR": "BOLD",
        "CRITICAL": "BOLD"
    }
)

def get_installed_version() -> Optional[str]:
    """Get the installed version of webscout"""
    try:
        import importlib.metadata
        return importlib.metadata.version('webscout')
    except ImportError:
        try:
            import pkg_resources
            return pkg_resources.get_distribution('webscout').version
        except Exception:
            logger.error("Could not determine installed version using pkg_resources")
            return None
    except Exception:
        logger.error("Could not determine installed version using importlib.metadata")
        return None

def get_webscout_version() -> Optional[str]:
    """Get the current webscout version from CLI"""
    try:
        result = subprocess.run(['webscout', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version_match = re.search(r'\d+\.\d+\.\d+', result.stdout)
            if version_match:
                return version_match.group(0)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to get version from CLI: {str(e)}")
    return None

def get_pypi_version() -> Optional[str]:
    """Get the latest version from PyPI"""
    try:
        response = requests.get(
            "https://pypi.org/pypi/webscout/json",
            timeout=10
        )
        response.raise_for_status()
        return response.json()['info']['version']
    except requests.RequestException as e:
        logger.error(f"Failed to fetch PyPI version: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse PyPI response: {str(e)}")
    return None

def version_compare(v1: str, v2: str) -> int:
    """Compare two version strings"""
    try:
        return -1 if version.parse(v1) < version.parse(v2) else 1
    except version.InvalidVersion:
        return 0

def display_version_info(installed: Optional[str], current: Optional[str], latest: Optional[str]) -> None:
    """Display version information"""
    if installed:
        logger.info(f"Currently using Webscout version {installed}")
    
    if latest and installed:
        if version_compare(installed, latest) < 0:
            logger.warning(
                f"A new version of Webscout is available: {latest}\n"
                f"To update, run: pip install --upgrade webscout"
            )
        else:
            logger.success("You're running the latest version!")

def check_for_updates() -> None:
    """Check for Webscout updates"""
    logger.info("Checking for Webscout updates...")
    
    installed_version = get_installed_version()
    current_version = get_webscout_version()
    latest_version = get_pypi_version()
    
    if not installed_version:
        logger.error("Could not determine installed Webscout version")
        return
        
    if not latest_version:
        logger.error("Could not determine latest Webscout version from PyPI")
        return
    
    display_version_info(installed_version, current_version, latest_version)

if __name__ == "__main__":
    try:
        check_for_updates()
    except KeyboardInterrupt:
        logger.warning("Update check cancelled by user")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
