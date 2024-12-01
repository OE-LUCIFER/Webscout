# 🔥 LitAgent - The Lit User Agent Generator

LitAgent is a powerful and modern user agent generator that keeps your requests fresh and undetectable! Built with style and packed with features, it's your go-to solution for managing user agents in your web scraping projects.

## 🚀 Quick Start

```python
from webscout import LitAgent

# Create a LitAgent instance
agent = LitAgent()

# Get a random user agent
ua = agent.random()
print(ua)  # Mozilla/5.0 (Windows NT 11.0) AppleWebKit/537.36 ...
```

## 🎯 Features

### Browser-Specific Agents

```python
# Get agents for specific browsers
chrome_ua = agent.chrome()    # Latest Chrome agent
firefox_ua = agent.firefox()  # Latest Firefox agent
safari_ua = agent.safari()    # Latest Safari agent
edge_ua = agent.edge()       # Latest Edge agent
opera_ua = agent.opera()     # Latest Opera agent
```

### Device-Specific Agents

```python
# Get mobile or desktop agents
mobile_ua = agent.mobile()    # Mobile device agent
desktop_ua = agent.desktop()  # Desktop device agent
```

### Keep It Fresh

```python
# Refresh your agents pool anytime
agent.refresh()  # Generates new set of agents
```

## 💫 Real-World Examples

### With Requests

```python
import requests
from webscout import LitAgent

agent = LitAgent()

def make_request(url):
    headers = {
        'User-Agent': agent.random(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    return requests.get(url, headers=headers)

# Make requests with different agents
response1 = make_request('https://api.example.com')  # Random agent
response2 = make_request('https://mobile.example.com')  # Another random agent
```

### With aiohttp

```python
import aiohttp
import asyncio
from webscout import LitAgent

agent = LitAgent()

async def fetch(url):
    headers = {'User-Agent': agent.random()}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.text()

# Use it in your async code
async def main():
    urls = [
        'https://api1.example.com',
        'https://api2.example.com',
        'https://api3.example.com'
    ]
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### With Selenium

```python
from selenium import webdriver
from webscout import LitAgent

agent = LitAgent()

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={agent.chrome()}')
    return webdriver.Chrome(options=options)

# Use it with Selenium
driver = create_driver()
driver.get('https://example.com')
```

## 🌟 Pro Tips

1. **Rotate Agents**: Refresh your agents pool periodically to avoid detection
   ```python
   agent = LitAgent()
   for _ in range(10):
       response = requests.get(url, headers={'User-Agent': agent.random()})
       if _ % 3 == 0:  # Refresh every 3 requests
           agent.refresh()
   ```

2. **Device-Specific Scraping**: Use appropriate agents for different platforms
   ```python
   # Mobile site scraping
   mobile_response = requests.get(
       'https://m.example.com',
       headers={'User-Agent': agent.mobile()}
   )

   # Desktop site scraping
   desktop_response = requests.get(
       'https://example.com',
       headers={'User-Agent': agent.desktop()}
   )
   ```

3. **Browser Consistency**: Stick to one browser type per session
   ```python
   chrome_agent = agent.chrome()
   headers = {
       'User-Agent': chrome_agent,
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
   }
   # Use these headers for all requests in this session
   ```

## 🔧 Supported Browsers & Devices

- **Browsers**: Chrome, Firefox, Safari, Edge, Opera
- **Operating Systems**: Windows, macOS, Linux, Android, iOS
- **Devices**: Mobile phones, Tablets, Desktops, Game consoles, Smart TVs

## 🎨 Why LitAgent?

- 🚀 Modern and up-to-date user agents
- 💪 Easy to use, hard to detect
- 🔄 Fresh agents on demand
- 📱 Device-specific agents
- 🌐 All major browsers supported
- ⚡ Lightweight and fast

Made with 💖 by the HelpingAI team
