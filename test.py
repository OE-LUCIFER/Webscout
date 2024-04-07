import sys
from webscout import transcriber

def extract_transcript(video_id):
    """Extracts the transcript from a YouTube video."""
    try:
        transcript_list = transcriber.list_transcripts(video_id)
        for transcript in transcript_list:
            transcript_text_list = transcript.fetch()
            lang = transcript.language
            transcript_text = ""
            if transcript.language_code == 'en':
                for line in transcript_text_list:
                    transcript_text += " " + line["text"]
                return transcript_text
            elif transcript.is_translatable:
                english_transcript_list = transcript.translate('en').fetch()
                for line in english_transcript_list:
                    transcript_text += " " + line["text"]
                return transcript_text
        print("Transcript extraction failed. Please check the video URL.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    video_url = input("Enter the video link: ")

    if video_url:
        video_id = video_url.split("=")[1]
        print("Video URL:", video_url)
        submit = input("Press 'Enter' to get the transcript or type 'exit' to quit: ")
        if submit == '':
            print("Extracting Transcript...")
            transcript = extract_transcript(video_id)
            print('Transcript:')
            print(transcript)
            print("__________________________________________________________________________________")
        elif submit.lower() == 'exit':
            print("Exiting...")
            sys.exit()
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()