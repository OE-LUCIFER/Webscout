"""Main LitAgent implementation."""

import random
from typing import List
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent.constants import BROWSERS, OS_VERSIONS, DEVICES

logger = LitLogger(
    name="LitAgent", format=LogFormat.MODERN_EMOJI, color_scheme=ColorScheme.CYBERPUNK
)


class LitAgent:
    """A lit user agent generator that keeps it fresh! 🌟"""

    def __init__(self):
        """Initialize LitAgent with style! 💫"""
        self.agents = self._generate_agents(100)  # Keep 100 agents in memory

    def _generate_agents(self, count: int) -> List[str]:
        """Generate some lit user agents! 🛠️"""
        agents = []
        for _ in range(count):
            browser = random.choice(list(BROWSERS.keys()))
            version = random.randint(*BROWSERS[browser])

            if browser in ["chrome", "firefox", "edge", "opera"]:
                os_type = random.choice(["windows", "mac", "linux"])
                os_ver = random.choice(OS_VERSIONS[os_type])

                if os_type == "windows":
                    platform = f"Windows NT {os_ver}"
                elif os_type == "mac":
                    platform = f"Macintosh; Intel Mac OS X {os_ver}"
                else:
                    platform = f"X11; Linux {os_ver}"

                agent = (
                    f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) "
                )
                if browser == "chrome":
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36"
                elif browser == "firefox":
                    agent += f"Firefox/{version}.0"
                elif browser == "edge":
                    agent += f"Edge/{version}.0.0.0"
                elif browser == "opera":
                    agent += f"OPR/{version}.0.0.0"

            elif browser == "safari":
                device = random.choice(["mac", "ios"])
                if device == "mac":
                    ver = random.choice(OS_VERSIONS["mac"])
                    agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {ver}) "
                else:
                    ver = random.choice(OS_VERSIONS["ios"])
                    device = random.choice(["iPhone", "iPad"])
                    agent = f"Mozilla/5.0 ({device}; CPU OS {ver} like Mac OS X) "
                agent += f"AppleWebKit/{version}.1.15 (KHTML, like Gecko) Version/{version // 100}.0 Safari/{version}.1.15"

            agents.append(agent)

        return list(set(agents))  # Remove any duplicates

    def random(self) -> str:
        """Get a random user agent! 🎲"""
        return random.choice(self.agents)

    def browser(self, name: str) -> str:
        """Get a browser-specific agent! 🌐"""
        name = name.lower()
        if name not in BROWSERS:
            logger.warning(f"Unknown browser: {name} - Using random browser")
            return self.random()

        agents = [a for a in self.agents if name in a.lower()]
        return random.choice(agents) if agents else self.random()

    def mobile(self) -> str:
        """Get a mobile device agent! 📱"""
        agents = [a for a in self.agents if any(d in a for d in DEVICES["mobile"])]
        return random.choice(agents) if agents else self.random()

    def desktop(self) -> str:
        """Get a desktop agent! 💻"""
        agents = [
            a for a in self.agents if "Windows" in a or "Macintosh" in a or "Linux" in a
        ]
        return random.choice(agents) if agents else self.random()

    def chrome(self) -> str:
        """Get a Chrome agent! 🌐"""
        return self.browser("chrome")

    def firefox(self) -> str:
        """Get a Firefox agent! 🦊"""
        return self.browser("firefox")

    def safari(self) -> str:
        """Get a Safari agent! 🧭"""
        return self.browser("safari")

    def edge(self) -> str:
        """Get an Edge agent! 📐"""
        return self.browser("edge")

    def opera(self) -> str:
        """Get an Opera agent! 🎭"""
        return self.browser("opera")

    def refresh(self) -> None:
        """Refresh the agents with new ones! 🔄"""
        self.agents = self._generate_agents(100)


if __name__ == "__main__":
    # Test it out! 🧪
    agent = LitAgent()
    print("Random:", agent.random())
    print("Chrome:", agent.chrome())
    print("Firefox:", agent.firefox())
    print("Safari:", agent.safari())
    print("Mobile:", agent.mobile())
    print("Desktop:", agent.desktop())
