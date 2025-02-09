# Create patch to handle pygetwindow gracefully
cat > fix_imports.patch << 'EOF'
--- a/webscout/Extra/autocoder/rawdog.py
+++ b/webscout/Extra/autocoder/rawdog.py
@@ -8,7 +8,10 @@
 import sys
 import tempfile
 import time
-import pygetwindow as gw
+try:
+    import pygetwindow as gw
+except NotImplementedError:
+    gw = None

 class RawDog:
     def __init__(self):
EOF

# Apply patch
patch -p1 < fix_imports.patch

# Install dependencies and package
pip3 install setuptools wheel pip
pip3 install primp pyreqwest_impersonate httpx curl_cffi nest-asyncio rich markdownify requests google-generativeai lxml termcolor orjson PyYAML tls_client clipman playsound ollama pillow bson cloudscraper html5lib aiofiles emoji openai prompt-toolkit gradio_client psutil yaspin aiohttp pyfiglet pygobject
pip3 install -e .[dev]