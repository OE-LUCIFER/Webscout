from .utils import dup_filter
from .video import Video
from .channel import Channel
from .playlist import Playlist
from .patterns import _QueryPatterns as Patterns
from typing import Optional, Dict, Any, List
from .https import find_videos, find_channels, find_playlists


class Search:

    @staticmethod
    def video(keywords: str) -> Optional[Video]:
        video_ids = Patterns.video_id.findall(find_videos(keywords))
        return Video(video_ids[0]) if video_ids else None

    @staticmethod
    def channel(keywords: str) -> Optional[Channel]:
        channel_ids = Patterns.channel_id.findall(find_channels(keywords))
        return Channel(channel_ids[0]) if channel_ids else None

    @staticmethod
    def playlist(keywords: str) -> Optional[Playlist]:
        playlist_ids = Patterns.playlist_id.findall(find_playlists(keywords))
        return Playlist(playlist_ids[0]) if playlist_ids else None

    @staticmethod
    def videos(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.video_id.findall(find_videos(keywords)), limit)

    @staticmethod
    def channels(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.channel_id.findall(find_channels(keywords)), limit)

    @staticmethod
    def playlists(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.playlist_id.findall(find_playlists(keywords)), limit)
