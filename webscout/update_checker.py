"""
Ayy, check it out! 👀
>>> from webscout import check_for_updates
>>> check_for_updates()
'Yo, new Webscout version just dropped: 2.0.0! 🔥
Level up with: `pip install --upgrade webscout`'
"""

from typing import Optional

import requests
from packaging import version

from webscout import LitLogger, ColorScheme
from importlib.metadata import version as get_package_version
from importlib.metadata import PackageNotFoundError

# Setting up that clean logger format, no cap! 💯
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
        "CRITICAL": "BOLD",
    },
)


def get_installed_version() -> Optional[str]:
    """Yo, let's check what version you're running! 🔍

    What this function's all about:
    - Checking your setup real quick 💨
    - Getting them version deets 📱
    - Handling any problems like a boss 💪

    Returns:
        Optional[str]: Your version number or None if we can't find it

    Examples:
        >>> version = get_installed_version()
        >>> print(version)
        '1.2.3'
    """
    try:
        return get_package_version("webscout")
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def get_pypi_version() -> Optional[str]:
    """Let's see what's fresh on PyPI! 🚀

    This function's vibe:
    - Hitting up PyPI for the latest drop 🌐
    - Keeping it smooth with timeout handling ⚡
    - Making sure we get good data fr fr 💯

    Returns:
        Optional[str]: Latest version or None if something's not right

    Examples:
        >>> latest = get_pypi_version()
        >>> print(latest)
        '2.0.0'
    """
    try:
        response = requests.get("https://pypi.org/pypi/webscout/json", timeout=10)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except requests.RequestException:
        pass
    except (KeyError, ValueError):
        pass
    except Exception:
        pass
    return None


def version_compare(v1: str, v2: str) -> int:
    """Time to compare these versions! 💪

    Args:
        v1: First version we checking
        v2: Second version to compare with

    Returns:
        int: -1 if v1's older, 1 if v1's newer, 0 if they twins

    Examples:
        >>> version_compare('1.0.0', '2.0.0')
        -1
    """
    try:
        version1 = version.parse(v1)
        version2 = version.parse(v2)
        if version1 < version2:
            return -1
        if version1 > version2:
            return 1
        return 0
    except version.InvalidVersion:
        pass
        return 0
    except Exception:
        pass
        return 0


def display_version_info(installed: Optional[str], latest: Optional[str]) -> None:
    """Let's break down your version status! 📱

    What we doing here:
    - Comparing your version with the latest drop 🔄
    - Letting you know if you need to level up ⬆️
    - Keeping you in the loop with style 💯

    Args:
        installed: What you running rn
        latest: What's fresh out there

    Examples:
        >>> display_version_info('1.0.0', '2.0.0')
        'Yo, new Webscout version just dropped: 2.0.0! 🔥'
    """
    if installed:
        pass

    if latest and installed:
        comparison_result = version_compare(installed, latest)
        if comparison_result < 0:
            logger.warning(
                f"Yo, new Webscout version just dropped: {latest}! 🔥\n"
                f"Level up with: `pip install --upgrade webscout`"
            )
        elif comparison_result > 0:
            logger.success("You already got the latest version, no cap! 💯")


def check_for_updates() -> None:
    """Time to check if you're running the latest! 🚀

    What we doing:
    - Peeking at your current setup 📱
    - Checking what's new out there 🌐
    - Keeping you updated fr fr ⚡

    Examples:
        >>> check_for_updates()
        # We got you with them version checks fam!
    """
    installed_version = get_installed_version()
    latest_version = get_pypi_version()

    if not installed_version:
        pass
        return

    if not latest_version:
        pass
        return

    display_version_info(installed_version, latest_version)


if __name__ == "__main__":
    try:
        check_for_updates()
    except KeyboardInterrupt:
        logger.warning("Update check got cancelled, no worries fam! 🤚")
    except Exception as e:
        logger.error(f"Uh oh, something went wrong: {str(e)} 😔")
