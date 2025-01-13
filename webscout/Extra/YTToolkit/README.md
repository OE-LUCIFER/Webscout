# 🎥 YTToolkit: YouTube Video Downloader and Transcriber

## 🔧 Modules in YTToolkit

### Core Modules

* **[Video Downloader](YTdownloader.py):** Powerful YouTube video downloading with advanced features
  - Multiple format support (MP4, MP3)
  - Customizable quality selection
  - Progress tracking and auto-save
  - Download history management

* **[Transcript Retriever](transcriber.py):** Advanced YouTube transcript extraction
  - Multi-language transcript support
  - Automatic and manual transcript fetching
  - Real-time translation capabilities
  - Flexible parsing options

### Extended Modules

* **[YTApi](ytapi/README.md):** Comprehensive YouTube Data Extraction
  - Channel metadata retrieval
  - Detailed video information
  - Advanced search capabilities
  - No official API dependency

## 🚀 Quick Start

### Installation

```bash
pip install webscout
```

### Usage Examples

#### Video Downloader

```python
from webscout import Handler

# Basic video download
downloader = Handler('https://youtube.com/video_link')
downloader.save()

# Advanced download with custom settings
downloader = Handler(
    query='tutorial video', 
    format='mp4', 
    quality='720p', 
    limit=5
)
downloader.auto_save(dir='./downloads')
```

#### Transcript Retriever

```python
from webscout import YTTranscriber

# Get video transcript
transcript = YTTranscriber.get_transcript('https://youtube.com/video_link')
print(transcript)

# Get transcript in a specific language
spanish_transcript = YTTranscriber.get_transcript('video_link', languages='es')
```

#### YouTube Data Extraction

```python
from webscout import Channel

# Retrieve channel information
channel = Channel('@PewDiePie')
print(f"Channel Name: {channel.name}")
print(f"Subscribers: {channel.subscribers}")
print(f"Recent Uploads: {channel.uploads(5)}")
```
