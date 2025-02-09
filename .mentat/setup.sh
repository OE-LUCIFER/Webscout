# Install system dependencies
apt-get update
apt-get install -y pkg-config libcairo2-dev

# Fix pygetwindow import
sed -i 's/import pygetwindow as gw/try:\n    import pygetwindow as gw\nexcept NotImplementedError:\n    gw = None/' webscout/Extra/autocoder/rawdog.py

# Install Python dependencies
pip3 install setuptools wheel pip
pip3 install primp pyreqwest_impersonate httpx curl_cffi nest-asyncio rich markdownify requests google-generativeai lxml termcolor orjson PyYAML tls_client clipman playsound ollama pillow bson cloudscraper html5lib aiofiles emoji openai prompt-toolkit gradio_client psutil yaspin aiohttp pyfiglet
pip3 install -e .[dev]