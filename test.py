from os import rename, getcwd
from webscout import YTdownloader
def download_audio(video_id):
    youtube_link = video_id 
    handler = YTdownloader.Handler(query=youtube_link)
    for third_query_data in handler.run(format='mp3', quality='128kbps', limit=1):
        audio_path = handler.save(third_query_data, dir=getcwd())  
        rename(audio_path, "audio.mp3")

def download_video(video_id):
    youtube_link = video_id 
    handler = YTdownloader.Handler(query=youtube_link)
    for third_query_data in handler.run(format='mp4', quality='auto', limit=1):
        video_path = handler.save(third_query_data, dir=getcwd())  
        rename(video_path, "video.mp4")
        
if __name__ == "__main__":
    download_audio("https://www.youtube.com/watch?v=c0tMvzB0OKw")
    download_video("https://www.youtube.com/watch?v=c0tMvzB0OKw")