import re


class _ChannelPatterns:
    name = re.compile('channelMetadataRenderer\":{\"title\":\"(.*?)\"')
    id = re.compile('channelId\":\"(.*?)\"')
    verified = re.compile('"label":"Verified"')
    check_live = re.compile('{"text":"LIVE"}')
    live = re.compile("thumbnailOverlays\":\[(.*?)]")
    video_id = re.compile('videoId\":\"(.*?)\"')
    uploads = re.compile("gridVideoRenderer\":{\"videoId\":\"(.*?)\"")
    subscribers = re.compile("\"subscriberCountText\":{\"accessibility\":(.*?),")
    views = re.compile("viewCountText\":{\"simpleText\":\"(.*?)\"}")
    creation = re.compile("{\"text\":\"Joined \"},{\"text\":\"(.*?)\"}")
    country = re.compile("country\":{\"simpleText\":\"(.*?)\"}")
    custom_url = re.compile("canonicalChannelUrl\":\"(.*?)\"")
    description = re.compile("{\"description\":{\"simpleText\":\"(.*?)\"}")
    avatar = re.compile("height\":88},{\"url\":\"(.*?)\"")
    banner = re.compile("width\":1280,\"height\":351},{\"url\":\"(.*?)\"")
    playlists = re.compile("{\"url\":\"/playlist\\?list=(.*?)\"")
    video_count = re.compile("videoCountText\":{\"runs\":\[{\"text\":(.*?)}")
    socials = re.compile("q=https%3A%2F%2F(.*?)\"")
    upload_ids = re.compile("videoId\":\"(.*?)\"")
    stream_ids = re.compile("videoId\":\"(.*?)\"")
    upload_chunk = re.compile("gridVideoRenderer\":{(.*?)\"navigationEndpoint")
    upload_chunk_fl_1 = re.compile("simpleText\":\"Streamed")
    upload_chunk_fl_2 = re.compile("default_live.")
    upcoming_check = re.compile("\"title\":\"Upcoming live streams\"")
    upcoming = re.compile("gridVideoRenderer\":{\"videoId\":\"(.*?)\"")


class _VideoPatterns:
    video_id = re.compile('videoId\":\"(.*?)\"')
    title = re.compile("title\":\"(.*?)\"")
    duration = re.compile("approxDurationMs\":\"(.*?)\"")
    upload_date = re.compile("uploadDate\":\"(.*?)\"")
    author_id = re.compile("channelIds\":\[\"(.*?)\"")
    description = re.compile("shortDescription\":\"(.*)\",\"isCrawlable")
    tags = re.compile("<meta name=\"keywords\" content=\"(.*?)\">")
    is_streamed = re.compile("simpleText\":\"Streamed live")
    is_premiered = re.compile("dateText\":{\"simpleText\":\"Premiered")
    views = re.compile("videoViewCountRenderer\":{\"viewCount\":{\"simpleText\":\"(.*?)\"")
    likes = re.compile("toggledText\":{\"accessibility\":{\"accessibilityData\":{\"label\":\"(.*?) ")
    thumbnail = re.compile("playerMicroformatRenderer\":{\"thumbnail\":{\"thumbnails\":\[{\"url\":\"(.*?)\"")


class _PlaylistPatterns:
    name = re.compile("{\"title\":\"(.*?)\"")
    video_count = re.compile("stats\":\[{\"runs\":\[{\"text\":\"(.*?)\"")
    video_id = re.compile("videoId\":\"(.*?)\"")
    thumbnail = re.compile("og:image\" content=\"(.*?)\?")


class _ExtraPatterns:
    video_id = re.compile("videoId\":\"(.*?)\"")


class _QueryPatterns:
    channel_id = re.compile("channelId\":\"(.*?)\"")
    video_id = re.compile("videoId\":\"(.*?)\"")
    playlist_id = re.compile("playlistId\":\"(.*?)\"")
