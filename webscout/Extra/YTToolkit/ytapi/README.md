# 🎥 YTApi: YouTube Data Extraction Module

## Overview

YTApi is a powerful, lightweight YouTube data extraction module within the Webscout Python package. It provides comprehensive tools for retrieving and analyzing YouTube channel, video, and playlist information without using the official YouTube API.

## 🚀 Features

- **Channel Metadata Extraction**
  - Retrieve comprehensive channel information
  - Extract subscriber count, views, description
  - Fetch channel avatars and banners

- **Video Information**
  - Detailed video metadata retrieval
  - Stream and upload history tracking
  - Upcoming video detection

- **Advanced Search Capabilities**
  - Trending videos across categories
  - Flexible search and filtering

- **No Official API Required**
  - Web scraping-based extraction
  - No API key needed

## 📦 Installation

Install as part of the Webscout package:

```bash
pip install webscout
```

## 💡 Quick Examples

### Channel Information

```python
from webscout import Channel

# Create a channel instance
channel = Channel('PewDiePie')

# Access channel metadata
print(channel.name)          # Channel name
print(channel.subscribers)   # Subscriber count
print(channel.description)   # Channel description

# Get recent uploads
recent_videos = channel.uploads(10)  # Get 10 most recent video IDs

# Check live status
if channel.live:
    print(f"Currently streaming: {channel.streaming_now}")
```

### Video Extraction

```python
from webscout import Video

# Create a video instance
video = Video('dQw4w9WgXcQ')

# Access video metadata
print(video.title)        # Video title
print(video.views)        # View count
print(video.description)  # Video description
```

### Trending Videos

```python
from webscout import Extras

# Get trending videos
trending = Extras.trending_videos()
music_videos = Extras.music_videos()
gaming_videos = Extras.gaming_videos()
```

## 🛠 Modules

- `channel.py`: Channel metadata and interaction
- `video.py`: Video information extraction
- `extras.py`: Trending and category-based video retrieval
- `query.py`: Advanced search capabilities
- `playlist.py`: Playlist metadata extraction

## ⚠️ Disclaimer

This module uses web scraping techniques. YouTube's HTML structure may change, potentially affecting extraction reliability.

## 🤝 Contributing

Contributions are welcome! Please submit pull requests or open issues on the Webscout GitHub repository.

