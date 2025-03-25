"""Main LitAgent implementation."""

import random
import threading
from typing import List, Dict, Any, Optional

from webscout.litagent.constants import BROWSERS, OS_VERSIONS, DEVICES, FINGERPRINTS


class LitAgent:
    """A lit user agent generator that keeps it fresh! 🌟"""

    def __init__(self, thread_safe: bool = False):
        """Initialize LitAgent with style! 💫

        Args:
            thread_safe (bool): Enable thread-safety for multi-threaded applications
        """
        self.agents = self._generate_agents(100)  # Keep 100 agents in memory
        self.thread_safe = thread_safe
        self.lock = threading.RLock() if thread_safe else None
        self._refresh_timer = None
        self._stats = {
            "total_generated": 100,
            "requests_served": 0,
            "browser_usage": {browser: 0 for browser in BROWSERS.keys()},
            "device_usage": {device: 0 for device in DEVICES.keys()}
        }

    def _generate_agents(self, count: int) -> List[str]:
        """Generate some lit user agents! 🛠️"""
        agents = []
        for _ in range(count):
            browser = random.choice(list(BROWSERS.keys()))
            version = random.randint(*BROWSERS[browser])
            
            if browser in ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi']:
                os_type = random.choice(['windows', 'mac', 'linux'])
                os_ver = random.choice(OS_VERSIONS[os_type])
                
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
                elif browser == 'brave':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 Brave/{version}.0.0.0"
                elif browser == 'vivaldi':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 Vivaldi/{version}.0.{random.randint(1000, 9999)}"
            
            elif browser == 'safari':
                device = random.choice(['mac', 'ios'])
                if device == 'mac':
                    ver = random.choice(OS_VERSIONS['mac'])
                    agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {ver}) "
                else:
                    ver = random.choice(OS_VERSIONS['ios'])
                    device = random.choice(['iPhone', 'iPad'])
                    agent = f"Mozilla/5.0 ({device}; CPU OS {ver} like Mac OS X) "
                agent += f"AppleWebKit/{version}.1.15 (KHTML, like Gecko) Version/{version//100}.0 Safari/{version}.1.15"
            
            agents.append(agent)
        
        return list(set(agents))  # Remove any duplicates

    def _update_stats(self, browser_type=None, device_type=None):
        """Update usage statistics."""
        if self.thread_safe and self.lock:
            with self.lock:
                self._stats["requests_served"] += 1
                if browser_type:
                    self._stats["browser_usage"][browser_type] = self._stats["browser_usage"].get(browser_type, 0) + 1
                if device_type:
                    self._stats["device_usage"][device_type] = self._stats["device_usage"].get(device_type, 0) + 1
        else:
            self._stats["requests_served"] += 1
            if browser_type:
                self._stats["browser_usage"][browser_type] = self._stats["browser_usage"].get(browser_type, 0) + 1
            if device_type:
                self._stats["device_usage"][device_type] = self._stats["device_usage"].get(device_type, 0) + 1

    def random(self) -> str:
        """Get a random user agent! 🎲"""
        if self.thread_safe and self.lock:
            with self.lock:
                agent = random.choice(self.agents)
                self._update_stats()
                return agent
        else:
            agent = random.choice(self.agents)
            self._update_stats()
            return agent

    def browser(self, name: str) -> str:
        """Get a browser-specific agent! 🌐"""
        name = name.lower()
        if name not in BROWSERS:
            return self.random()
        
        if self.thread_safe and self.lock:
            with self.lock:
                agents = [a for a in self.agents if name in a.lower()]
                agent = random.choice(agents) if agents else self.random()
                self._update_stats(browser_type=name)
                return agent
        else:
            agents = [a for a in self.agents if name in a.lower()]
            agent = random.choice(agents) if agents else self.random()
            self._update_stats(browser_type=name)
            return agent

    def mobile(self) -> str:
        """Get a mobile device agent! 📱"""
        if self.thread_safe and self.lock:
            with self.lock:
                agents = [a for a in self.agents if any(d in a for d in DEVICES['mobile'])]
                agent = random.choice(agents) if agents else self.random()
                self._update_stats(device_type="mobile")
                return agent
        else:
            agents = [a for a in self.agents if any(d in a for d in DEVICES['mobile'])]
            agent = random.choice(agents) if agents else self.random()
            self._update_stats(device_type="mobile")
            return agent

    def desktop(self) -> str:
        """Get a desktop agent! 💻"""
        if self.thread_safe and self.lock:
            with self.lock:
                agents = [a for a in self.agents if 'Windows' in a or 'Macintosh' in a or 'Linux' in a]
                agent = random.choice(agents) if agents else self.random()
                self._update_stats(device_type="desktop")
                return agent
        else:
            agents = [a for a in self.agents if 'Windows' in a or 'Macintosh' in a or 'Linux' in a]
            agent = random.choice(agents) if agents else self.random()
            self._update_stats(device_type="desktop")
            return agent

    def tablet(self) -> str:
        """Get a tablet agent! 📱"""
        if self.thread_safe and self.lock:
            with self.lock:
                # Focus on iPad and Android tablets
                agents = [a for a in self.agents if 'iPad' in a or 'Android' in a and not 'Mobile' in a]
                agent = random.choice(agents) if agents else self.random()
                self._update_stats(device_type="tablet")
                return agent
        else:
            agents = [a for a in self.agents if 'iPad' in a or 'Android' in a and not 'Mobile' in a]
            agent = random.choice(agents) if agents else self.random()
            self._update_stats(device_type="tablet")
            return agent

    def smart_tv(self) -> str:
        """Get a Smart TV agent! 📺"""
        # Create a TV-specific agent since they may not be in our standard pool
        tv_type = random.choice(DEVICES['tv'])
        if 'Samsung' in tv_type:
            agent = f"Mozilla/5.0 (SMART-TV; SAMSUNG; {tv_type}; Tizen 5.5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.38 Safari/537.36"
        elif 'LG' in tv_type:
            agent = f"Mozilla/5.0 (Web0S; {tv_type}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
        elif 'Android' in tv_type:
            agent = f"Mozilla/5.0 (Linux; Android 9; {tv_type}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
        elif 'Apple' in tv_type:
            agent = f"Mozilla/5.0 (AppleTV; CPU like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        else:
            agent = f"Mozilla/5.0 (Linux; {tv_type}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
        
        self._update_stats(device_type="tv")
        return agent

    def gaming(self) -> str:
        """Get a gaming console agent! 🎮"""
        console_type = random.choice(DEVICES['console'])
        if 'PlayStation' in console_type:
            agent = f"Mozilla/5.0 ({console_type}/5.0) AppleWebKit/601.2 (KHTML, like Gecko)"
        elif 'Xbox' in console_type:
            agent = f"Mozilla/5.0 ({console_type}; Xbox; Xbox One) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19041"
        elif 'Nintendo' in console_type:
            agent = f"Mozilla/5.0 (Nintendo Switch; {console_type}) AppleWebKit/601.6 (KHTML, like Gecko) NintendoBrowser/5.1.0.13343"
        else:
            agent = self.random()
        
        self._update_stats(device_type="console")
        return agent

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
    
    def brave(self) -> str:
        """Get a Brave agent! 🦁"""
        return self.browser('brave')
    
    def vivaldi(self) -> str:
        """Get a Vivaldi agent! 🎨"""
        return self.browser('vivaldi')
    
    # OS-specific agents
    def windows(self) -> str:
        """Get a Windows agent! 🪟"""
        agents = [a for a in self.agents if 'Windows' in a]
        agent = random.choice(agents) if agents else self.random()
        self._update_stats()
        return agent
    
    def macos(self) -> str:
        """Get a macOS agent! 🍎"""
        agents = [a for a in self.agents if 'Macintosh' in a]
        agent = random.choice(agents) if agents else self.random()
        self._update_stats()
        return agent
    
    def linux(self) -> str:
        """Get a Linux agent! 🐧"""
        agents = [a for a in self.agents if 'Linux' in a and 'Android' not in a]
        agent = random.choice(agents) if agents else self.random()
        self._update_stats()
        return agent
    
    def android(self) -> str:
        """Get an Android agent! 🤖"""
        agents = [a for a in self.agents if 'Android' in a]
        agent = random.choice(agents) if agents else self.random()
        self._update_stats()
        return agent
    
    def ios(self) -> str:
        """Get an iOS agent! 📱"""
        agents = [a for a in self.agents if 'iPhone' in a or 'iPad' in a]
        agent = random.choice(agents) if agents else self.random()
        self._update_stats()
        return agent

    def custom(self, browser: str, version: Optional[str] = None, 
               os: Optional[str] = None, os_version: Optional[str] = None, 
               device_type: Optional[str] = None) -> str:
        """Generate a custom user agent with specified parameters! 🛠️
        
        Args:
            browser: Browser name (chrome, firefox, safari, edge, opera)
            version: Browser version (optional)
            os: Operating system (windows, mac, linux, android, ios)
            os_version: OS version (optional)
            device_type: Device type (desktop, mobile, tablet)
            
        Returns:
            Customized user agent string
        """
        browser = browser.lower() if browser else 'chrome'
        if browser not in BROWSERS:
            browser = 'chrome'
            
        if version:
            try:
                version_num = int(version.split('.')[0])
            except (ValueError, IndexError):
                version_num = random.randint(*BROWSERS[browser])
        else:
            version_num = random.randint(*BROWSERS[browser])
            
        os = os.lower() if os else random.choice(['windows', 'mac', 'linux'])
        if os not in OS_VERSIONS:
            os = 'windows'
            
        os_ver = os_version or random.choice(OS_VERSIONS[os])
        
        device_type = device_type.lower() if device_type else 'desktop'
        
        # Build the user agent
        if os == 'windows':
            platform = f"Windows NT {os_ver}"
        elif os == 'mac':
            platform = f"Macintosh; Intel Mac OS X {os_ver}"
        elif os == 'linux':
            platform = f"X11; Linux {OS_VERSIONS['linux'][0]}"
        elif os == 'android':
            platform = f"Linux; Android {os_ver}; {random.choice(DEVICES['mobile'])}"
        elif os == 'ios':
            device = 'iPhone' if device_type == 'mobile' else 'iPad'
            platform = f"{device}; CPU OS {os_ver} like Mac OS X"
        else:
            platform = f"Windows NT 10.0"  # Default fallback
        
        agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) "
        
        if browser == 'chrome':
            agent += f"Chrome/{version_num}.0.0.0 Safari/537.36"
        elif browser == 'firefox':
            agent += f"Firefox/{version_num}.0"
        elif browser == 'safari':
            safari_ver = random.randint(*BROWSERS['safari'])
            agent += f"Version/{version_num}.0 Safari/{safari_ver}.0"
        elif browser == 'edge':
            agent += f"Chrome/{version_num}.0.0.0 Safari/537.36 Edg/{version_num}.0.0.0"
        elif browser == 'opera':
            agent += f"Chrome/{version_num}.0.0.0 Safari/537.36 OPR/{version_num}.0.0.0"
        elif browser == 'brave':
            agent += f"Chrome/{version_num}.0.0.0 Safari/537.36 Brave/{version_num}.1.0"
        
        self._update_stats(browser_type=browser, device_type=device_type)
        return agent

    def generate_fingerprint(self, browser: Optional[str] = None) -> Dict[str, str]:
        """Generate a consistent browser fingerprint! 👆
        
        This creates a coherent set of headers for anti-fingerprinting.
        
        Args:
            browser: Specific browser to generate fingerprint for
            
        Returns:
            Dictionary with fingerprinting headers
        """
        # Get a random user agent using the random() method
        user_agent = self.random()
        
        # If browser is specified, try to get a matching one
        if browser:
            browser = browser.lower()
            if browser in BROWSERS:
                user_agent = self.browser(browser)
        
        accept_language = random.choice(FINGERPRINTS["accept_language"])
        accept = random.choice(FINGERPRINTS["accept"])
        platform = random.choice(FINGERPRINTS["platforms"])
        
        # Generate sec-ch-ua based on the user agent
        sec_ch_ua = ""
        for browser_name in FINGERPRINTS["sec_ch_ua"]:
            if browser_name in user_agent.lower():
                version = random.randint(*BROWSERS[browser_name])
                sec_ch_ua = FINGERPRINTS["sec_ch_ua"][browser_name].format(version, version)
                break
        
        fingerprint = {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "accept": accept,
            "sec_ch_ua": sec_ch_ua,
            "platform": platform
        }
        
        self._update_stats(browser_type=browser)
        return fingerprint

    def refresh(self) -> None:
        """Refresh the agents with new ones! 🔄"""
        if self.thread_safe and self.lock:
            with self.lock:
                self.agents = self._generate_agents(100)
                self._stats["total_generated"] += 100
        else:
            self.agents = self._generate_agents(100)
            self._stats["total_generated"] += 100
        

    def auto_refresh(self, interval_minutes: int = 30) -> None:
        """Set up automatic refreshing of agents pool! ⏱️
        
        Args:
            interval_minutes: Minutes between refreshes
        """
        if self._refresh_timer:
            self._refresh_timer.cancel()
            
        def _refresh_task():
            self.refresh()
            self._refresh_timer = threading.Timer(interval_minutes * 60, _refresh_task)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()
        
        self._refresh_timer = threading.Timer(interval_minutes * 60, _refresh_task)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about agent usage! 📊
        
        Returns:
            Dictionary with usage statistics
        """
        stats_copy = self._stats.copy()
        # Calculate top browser
        top_browser = max(stats_copy["browser_usage"].items(), key=lambda x: x[1])[0] if stats_copy["browser_usage"] else None
        stats_copy["top_browser"] = top_browser
        
        # Calculate fake detection avoidance rate (just for fun)
        stats_copy["avoidance_rate"] = min(99.9, 90 + (stats_copy["total_generated"] / 1000))
        
        return stats_copy
        
    def export_stats(self, filename: str) -> bool:
        """Export usage statistics to a file! 💾
        
        Args:
            filename: Path to export the stats
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(self.get_stats(), f, indent=2)
            return True
        except Exception as e:
            return False

if __name__ == "__main__":
    # Test it out! 🧪
    agent = LitAgent()
    print("Random:", agent.random())
    print("Chrome:", agent.chrome())
    print("Firefox:", agent.firefox())
    print("Safari:", agent.safari())
    print("Mobile:", agent.mobile())
    print("Desktop:", agent.desktop())
    print("Tablet:", agent.tablet())
    print("Smart TV:", agent.smart_tv())
    print("Gaming:", agent.gaming())
    
    # Test custom agent
    print("Custom:", agent.custom(browser="chrome", os="windows", os_version="10.0"))
    
    # Test fingerprinting
    print("Fingerprint:", agent.generate_fingerprint("chrome"))