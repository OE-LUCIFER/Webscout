# Install system dependencies
apt-get update
apt-get install -y pkg-config libcairo2-dev

# Fix pygetwindow imports in both files
cat > webscout/Extra/autocoder/rawdog.py.new << 'EOF'
try:
    import pygetwindow as gw
except NotImplementedError:
    gw = None
EOF
cat webscout/Extra/autocoder/rawdog.py | grep -v "import pygetwindow" >> webscout/Extra/autocoder/rawdog.py.new
mv webscout/Extra/autocoder/rawdog.py.new webscout/Extra/autocoder/rawdog.py

cat > webscout/Extra/autocoder/autocoder_utiles.py.new << 'EOF'
try:
    import pygetwindow as gw
except NotImplementedError:
    gw = None
EOF
cat webscout/Extra/autocoder/autocoder_utiles.py | grep -v "import pygetwindow" >> webscout/Extra/autocoder/autocoder_utiles.py.new
mv webscout/Extra/autocoder/autocoder_utiles.py.new webscout/Extra/autocoder/autocoder_utiles.py

# Install Python dependencies
pip3 install setuptools wheel pip
pip3 install primp pyreqwest_impersonate httpx curl_cffi nest-asyncio rich markdownify requests google-generativeai lxml termcolor orjson PyYAML tls_client clipman playsound ollama pillow bson cloudscraper html5lib aiofiles emoji openai prompt-toolkit gradio_client psutil yaspin aiohttp pyfiglet
pip3 install -e .[dev]