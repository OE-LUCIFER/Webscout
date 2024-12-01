"""
LitAgent - A lit user agent generator with infinite possibilities! 🔥

Examples:
>>> from webscout import LitAgent
>>> agent = LitAgent()
>>> 
>>> # Get random user agents
>>> agent.random()  # Random agent from any browser
>>> agent.mobile()  # Random mobile device agent
>>> agent.desktop()  # Random desktop agent
>>>
>>> # Browser specific agents
>>> agent.chrome()  # Latest Chrome browser
>>> agent.firefox()  # Latest Firefox browser
>>> agent.safari()  # Latest Safari browser
>>> agent.edge()  # Latest Edge browser
>>> agent.opera()  # Latest Opera browser
>>>
>>> # Refresh your agents
>>> agent.refresh()  # Get fresh new agents
"""

import random
from typing import Optional, List, Dict
from ..Litlogger import LitLogger, LogFormat, ColorScheme

logger = LitLogger(
    name="LitAgent",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)

class LitAgent:
    """A lit user agent generator that keeps it fresh! 🌟"""
    
    # Browser versions we support
    BROWSERS = {
        "chrome": (48, 120),
        "firefox": (48, 121),
        "safari": (605, 617),
        "edge": (79, 120),
        "opera": (48, 104)
    }
    
    # OS versions
    OS_VERSIONS = {
        "windows": ["10.0", "11.0"],
        "mac": ["10_15_7", "11_0", "12_0", "13_0", "14_0"],
        "linux": ["x86_64", "i686"],
        "android": ["10", "11", "12", "13", "14"],
        "ios": ["14_0", "15_0", "16_0", "17_0"]
    }
    
    # Device types
    DEVICES = {
        "mobile": [
            "iPhone", "iPad", "Samsung Galaxy", "Google Pixel",
            "OnePlus", "Xiaomi", "Huawei", "OPPO", "Vivo"
        ],
        "desktop": ["Windows PC", "MacBook", "iMac", "Linux Desktop"],
        "tablet": ["iPad", "Samsung Galaxy Tab", "Microsoft Surface"],
        "console": ["PlayStation 5", "Xbox Series X", "Nintendo Switch"],
        "tv": ["Samsung Smart TV", "LG WebOS", "Android TV", "Apple TV"]
    }

    def __init__(self):
        """Initialize LitAgent with style! 💫"""
        self.agents = self._generate_agents(100)  # Keep 100 agents in memory

    def _generate_agents(self, count: int) -> List[str]:
        """Generate some lit user agents! 🛠️"""
        agents = []
        for _ in range(count):
            browser = random.choice(list(self.BROWSERS.keys()))
            version = random.randint(*self.BROWSERS[browser])
            
            if browser in ['chrome', 'firefox', 'edge', 'opera']:
                os_type = random.choice(['windows', 'mac', 'linux'])
                os_ver = random.choice(self.OS_VERSIONS[os_type])
                
                if os_type == 'windows':
                    platform = f"Windows NT {os_ver}"
                elif os_type == 'mac':
                    platform = f"Macintosh; Intel Mac OS X {os_ver}"
                else:
                    platform = f"X11; Linux {os_ver}"
                
                agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) "
                if browser == 'chrome':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36"
                elif browser == 'firefox':
                    agent += f"Firefox/{version}.0"
                elif browser == 'edge':
                    agent += f"Edge/{version}.0.0.0"
                elif browser == 'opera':
                    agent += f"OPR/{version}.0.0.0"
            
            elif browser == 'safari':
                device = random.choice(['mac', 'ios'])
                if device == 'mac':
                    ver = random.choice(self.OS_VERSIONS['mac'])
                    agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {ver}) "
                else:
                    ver = random.choice(self.OS_VERSIONS['ios'])
                    device = random.choice(['iPhone', 'iPad'])
                    agent = f"Mozilla/5.0 ({device}; CPU OS {ver} like Mac OS X) "
                agent += f"AppleWebKit/{version}.1.15 (KHTML, like Gecko) Version/{version//100}.0 Safari/{version}.1.15"
            
            agents.append(agent)
        
        return list(set(agents))  # Remove any duplicates

    def random(self) -> str:
        """Get a random user agent! 🎲"""
        return random.choice(self.agents)

    def browser(self, name: str) -> str:
        """Get a browser-specific agent! 🌐"""
        name = name.lower()
        if name not in self.BROWSERS:
            logger.warning(f"Unknown browser: {name} - Using random browser")
            return self.random()
        
        agents = [a for a in self.agents if name in a.lower()]
        return random.choice(agents) if agents else self.random()

    def mobile(self) -> str:
        """Get a mobile device agent! 📱"""
        agents = [a for a in self.agents if any(d in a for d in self.DEVICES['mobile'])]
        return random.choice(agents) if agents else self.random()

    def desktop(self) -> str:
        """Get a desktop agent! 💻"""
        agents = [a for a in self.agents if 'Windows' in a or 'Macintosh' in a or 'Linux' in a]
        return random.choice(agents) if agents else self.random()

    def chrome(self) -> str:
        """Get a Chrome agent! 🌐"""
        return self.browser('chrome')

    def firefox(self) -> str:
        """Get a Firefox agent! 🦊"""
        return self.browser('firefox')

    def safari(self) -> str:
        """Get a Safari agent! 🧭"""
        return self.browser('safari')

    def edge(self) -> str:
        """Get an Edge agent! 📐"""
        return self.browser('edge')

    def opera(self) -> str:
        """Get an Opera agent! 🎭"""
        return self.browser('opera')

    def refresh(self) -> None:
        """Refresh the agents with new ones! 🔄"""
        self.agents = self._generate_agents(100)

agent = LitAgent()

if __name__ == "__main__":
    # Test it out! 🧪

    print("Random:", agent.random())
    print("Chrome:", agent.chrome())
    print("Firefox:", agent.firefox())
    print("Safari:", agent.safari())
    print("Mobile:", agent.mobile())
    print("Desktop:", agent.desktop())
