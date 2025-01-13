# from webscout import YTTranscriber
# from jprinter import jprint

# from webscout.Extra.YTToolkit.ytapi.query import Search
# # Get video transcript
# transcript = YTTranscriber.get_transcript('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
# jprint(transcript, prefix='[INFO] >>> ')

# from webscout import Channel

# # Retrieve channel information
# channel = Channel('@OEvortex')
# jprint(f"Channel Name: {channel.name}", prefix='[INFO] >>> ')
# jprint(f"Subscribers: {channel.subscribers}", prefix='[INFO] >>> ')
# jprint(f"Recent Uploads: {channel.uploads(5)}", prefix='[INFO] >>> ')


# from webscout import Video

# # Create a video instance
# video = Video('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

# print(video.metadata)


from webscout.Extra.YTToolkit.ytapi.query import Search
from rich import print
print(Search.videos("LET ME IN WWE SONG"))
print(Search.channels("OEvortex"))
print(Search.playlists("OEvortex"))
