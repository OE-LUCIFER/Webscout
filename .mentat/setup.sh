# Install system dependencies
apt-get update
apt-get install -y pkg-config libcairo2-dev

# Fix pygetwindow imports while preserving file content
for file in webscout/Extra/autocoder/rawdog.py webscout/Extra/autocoder/autocoder_utiles.py; do
    if [ -f "$file" ]; then
        awk '
        BEGIN {print "try:\n    import pygetwindow as gw\nexcept NotImplementedError:\n    gw = None"}
        !/import pygetwindow/ {print}
        ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
    fi
done

# Install Python dependencies
pip3 install setuptools wheel pip
pip3 install primp pyreqwest_impersonate httpx curl_cffi nest-asyncio rich markdownify requests google-generativeai lxml termcolor orjson PyYAML tls_client clipman playsound ollama pillow bson cloudscraper html5lib aiofiles emoji openai prompt-toolkit gradio_client psutil yaspin aiohttp pyfiglet colorama
pip3 install -e .[dev]