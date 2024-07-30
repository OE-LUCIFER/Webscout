import sys
import logging
import re
from os import rename, getcwd
from dataclasses import dataclass
from webscout.YTdownloader import Handler
from webscout import transcriber, DeepInfra
import requests
from textblob import TextBlob
from fpdf import FPDF
from inquirer import List, prompt, Text
from yaspin import yaspin
from pyfiglet import figlet_format
from termcolor import colored

logging.basicConfig(level=logging.WARNING)
logging.getLogger('factory').setLevel(logging.WARNING)
logging.getLogger('yaspin').setLevel(logging.WARNING)
@dataclass
class Mood:
    emoji: str
    sentiment: float
    sentiment_review: str


def get_sentiment(only_transcript):
    """Gets the mood of the transcript."""
    blob = TextBlob(only_transcript)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return Mood(emoji="😃", sentiment=sentiment, sentiment_review="Positive")
    elif sentiment < 0:
        return Mood(emoji="😞", sentiment=sentiment, sentiment_review="Negative")
    else:
        return Mood(emoji="😐", sentiment=sentiment, sentiment_review="Neutral")


def download_audio(video_id):
    youtube_link = video_id
    handler = Handler(query=youtube_link)
    for third_query_data in handler.run(format='mp3', quality='128kbps', limit=1):
        audio_path = handler.save(third_query_data, dir=getcwd())
        rename(audio_path, "audio.mp3")


def extract_transcript(video_id):
    """Extracts the transcript from a YouTube video."""
    if video_id:
        transcript_list = transcriber.list_transcripts(video_id)
        for transcript in transcript_list:
            if transcript.language_code == 'en':
                with yaspin(text="Extracting transcript...", color="cyan") as spinner:
                    transcript_data_list = transcript.fetch()
                    spinner.ok("✅ ")
                transcript_text = "\n".join(
                    f"{line['start']:.2f} - {line['start'] + line['duration']:.2f}: {line['text']}"
                    for line in transcript_data_list
                )
                only_transcript = "".join(
                    line['text']
                    for line in transcript_data_list
                )
                return transcript_text, only_transcript
            elif transcript.is_translatable:
                with yaspin(text="Translating and extracting transcript...", color="cyan") as spinner:
                    english_transcript_list = transcript.translate('en').fetch()
                    spinner.ok("✅ ")
                transcript_text = "\n".join(
                    f"{line['start']:.2f} - {line['start'] + line['duration']:.2f}: {line['text']}"
                    for line in english_transcript_list
                )
                only_transcript = "".join(
                    line['text']
                    for line in english_transcript_list
                )
                return transcript_text, only_transcript


def translator(source_lang, target_lang, transcript_text):
    """Translates the transcript using the provided API endpoint."""
    translated_text = ""
    lines = transcript_text.splitlines()

    for line in lines:
        if ':' in line:
            timestamp, text = line.split(':', 1)
            api_url = f"https://oevortex-webscout-api.hf.space/api/google_translate?q={text}&from_={source_lang}&to={target_lang}"

            try:
                with yaspin(text=f"Translating: {text}", color="yellow") as spinner:
                    response = requests.get(api_url)
                    response.raise_for_status()  # Raise an error for bad status codes
                    translation_data = response.json()
                    translated_text += f"{timestamp}: {translation_data['translated']}\n"
                    spinner.ok("✅ ")

            except requests.exceptions.RequestException as e:
                print(colored(f"Error during translation: {e}", color="red"))
        else:
            translated_text += line + "\n"

    return translated_text


def create_srt_file(transcript_text, filename):
    """Creates an SRT file from a transcription with timestamps."""
    lines = transcript_text.splitlines()
    srt_lines = []
    current_index = 1

    for line in lines:
        if ':' in line:
            try:
                timestamp, text = line.split(':', 1)
                start_time, end_time = map(float, timestamp.split('-'))
                start_timestamp = f"{int(start_time // 3600):02d}:{int(start_time % 3600 // 60):02d}:{int(start_time % 60):02d},{int(start_time % 1 * 1000):03d}"
                end_timestamp = f"{int(end_time // 3600):02d}:{int(end_time % 3600 // 60):02d}:{int(end_time % 60):02d},{int(end_time % 1 * 1000):03d}"
                srt_lines.extend([
                    str(current_index),
                    f"{start_timestamp} --> {end_timestamp}",
                    text.strip(),
                    ''
                ])
                current_index += 1
            except ValueError:
                # Handle lines that do not contain proper timestamps
                continue
        else:
            # Handle non-timestamp lines (like speaker names)
            srt_lines.append(line)

    # Write to SRT file
    with open(f"{filename}.srt", 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_lines))


def create_vtt_file(transcript_text, filename):
    """
    Creates a VTT file from a transcript string.

    Args:
        transcript_text: The transcript string.
        filename: The name of the VTT file to be created.
    """
    with open(f"{filename}.vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")

        for line in transcript_text.strip().splitlines():

            match = re.match(r"(\d+\.\d+) - (\d+\.\d+): (.*)", line)
            if match:
                start_time, end_time, text = match.groups()
                f.write(f"{start_time} --> {end_time}\n{text}\n\n")
            else:  # Handle lines without timestamps
                f.write(line + "\n\n")


def save_transcript(transcript_text, translated_text, format, filename):
    """Saves the transcript in the specified format."""
    if format == 'TXT':
        with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
            f.write(translated_text if translated_text else transcript_text)
    elif format == 'PDF':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 5, (translated_text if translated_text else transcript_text), align="L")
        pdf.output(f"{filename}.pdf")
    elif format == 'SRT':
        create_srt_file(translated_text if translated_text else transcript_text, filename)
    elif format == 'VTT':
        create_vtt_file(translated_text if translated_text else transcript_text, filename)
    else:
        print("Invalid output format. Please choose from TXT, PDF, SRT, or VTT.")


def modify_transcript(transcript_text, size):
    """Modifies the transcript based on the desired size."""
    lines = transcript_text.splitlines()
    modified_transcript = ""
    previous_end_time = 0.0

    for line in lines:
        if ':' in line:
            try:
                timestamp, text = line.split(':', 1)
                start_time, end_time = map(float, timestamp.split('-'))

                if size == 'Large':
                    start_time = max(previous_end_time, start_time - (end_time - start_time) * 0.25)
                elif size == 'Small':
                    start_time = start_time + (end_time - start_time) * 0.25
                else:
                    start_time = start_time  
                    end_time = end_time 

                modified_transcript += f"{start_time:.2f} - {end_time:.2f}: {text}\n"
                previous_end_time = end_time

            except ValueError:
                modified_transcript += line + "\n"
        else:
            modified_transcript += line + "\n"

    return modified_transcript

def main():
    print(colored(figlet_format("Webscout Transcript AI"), color="cyan"))
    video_url = input("Enter the video link: ")
    # video_url = colored("https://www.youtube.com/watch?v=fLeJJPxua3E", color="blue")
    print(colored("Enter the video link: ", color="green"),video_url)
    translation_question = [
        List('translation',
             message="Do you want to translate the transcript?",
             choices=['Yes', 'No'],
             ),
    ]
    translation_answer = prompt(translation_question)
    if video_url:
        video_id = video_url.split("=")[1]
        print(colored(f"Video URL: {video_url}", color="blue"))
        save_question = [
            List('save',
                 message="Do you want to save the transcript?",
                 choices=['Yes', 'No'],
                 ),
        ]
        save_answer = prompt(save_question)
        sentiment_question = [
            List('sentiment',
                 message="Do you want to analyze the sentiment of the transcript?",
                 choices=['Yes', 'No'],
                 ),
        ]
        sentiment_answer = prompt(sentiment_question)
        modify_question = [
            List('modify',
                 message="Do you want to modify the transcript size?",
                 choices=['Yes', 'No'],
                 ),
        ]
        modify_answer = prompt(modify_question)
        print(colored("Press 'Enter' to get the transcript or type 'exit' to quit: ", color="green"))
        submit = input()
        if submit == '':
            print(colored("Extracting Transcript...", color="magenta"))
            transcript_t, only_t = extract_transcript(video_id)
            print(colored('Transcript:', color="yellow"))
            print(transcript_t)
            print(colored("__________________________________________________________________________________", color="white"))

            if translation_answer['translation'] == 'Yes':
                source_lang = "auto"
                target_lang_question = [
                    Text('target_lang',
                         message="Enter the target language: ",
                         ),
                ]
                target_lang_answer = prompt(target_lang_question)
                target_lang = target_lang_answer['target_lang']
                print(colored('Translated:', color="yellow"))
                translated_text = translator(source_lang, target_lang, transcript_t)
                print(translated_text)
                print(colored("__________________________________________________________________________________", color="white"))
                if save_answer['save'] == 'Yes':
                    output_format_question = [
                        List('output_format',
                             message="Enter the desired output format",
                             choices=['TXT', 'PDF', 'SRT', 'VTT'],
                             ),
                    ]
                    output_format_answer = prompt(output_format_question)
                    output_format = output_format_answer['output_format']
                    filename_question = [
                        Text('filename',
                             message="Enter a filename for the output",
                             ),
                    ]
                    filename_answer = prompt(filename_question)
                    filename = filename_answer['filename']
                    save_transcript(transcript_t, translated_text, output_format, filename)
                    print(colored(f"Transcript saved as {filename}.{output_format.lower()}", color="green"))
                else:
                    print(colored("Transcript not saved.", color="red"))
                if sentiment_answer['sentiment'] == 'Yes':
                    mood: Mood = get_sentiment(only_t)
                    print(
                        colored(f"{mood.emoji} Sentiment: {mood.sentiment_review} ({mood.sentiment:.2f})", color="blue"))
                elif sentiment_answer['sentiment'] == 'No':
                    pass
                if modify_answer['modify'] == 'Yes':
                    size_question = [
                        List('size',
                             message="Choose the desired size:",
                             choices=['Small', 'Medium', 'Large'],
                             ),
                    ]
                    size_answer = prompt(size_question)
                    size = size_answer['size']
                    if size == 'Small' or size == 'Large':
                        transcript_t = modify_transcript(transcript_t, size)
                        print(colored('Modified Transcript:', color="yellow"))
                        print(transcript_t)
                        print(colored("__________________________________________________________________________________", color="white"))
                    else:
                        print(colored("Transcript size not modified.", color="red"))
                ai_bot_question = [
                    List('ai_bot',
                         message="Do you want to use the AI bot to chat with the transcript?",
                         choices=['Yes', 'No'],
                         ),
                ]
                ai_bot_answer = prompt(ai_bot_question)
                if ai_bot_answer['ai_bot'] == 'Yes':
                    deepinfra = DeepInfra(is_conversation=True,
                                          max_tokens=8000, timeout=30, model="microsoft/WizardLM-2-8x22B", )
                    while True:
                        prompt_message = "Enter your prompt (type 'exit' to exit): "
                        print(colored(prompt_message, color="green"), end="")
                        user_prompt = input()
                        if user_prompt.lower() == 'exit':
                            break
                        else:
                            optimized_prompt = f"[YT video]: {video_url}\n [Transcription]: {transcript_t}\n [User]: {user_prompt}"
                            with yaspin(text="Thinking...", color="green") as spinner:
                                response = deepinfra.ask(optimized_prompt)
                                spinner.ok("✅ ")
                            message = deepinfra.get_message(response)
                            print(colored(f"AI: {message}", color="blue"))
                elif ai_bot_answer['ai_bot'] == 'No':
                    pass

            elif translation_answer['translation'] == 'No':
                if save_answer['save'] == 'Yes':
                    output_format_question = [
                        List('output_format',
                             message="Enter the desired output format",
                             choices=['TXT', 'PDF', 'SRT', 'VTT'],
                             ),
                    ]
                    output_format_answer = prompt(output_format_question)
                    output_format = output_format_answer['output_format']
                    filename_question = [
                        Text('filename',
                             message="Enter a filename for the output: ",
                             ),
                    ]
                    filename_answer = prompt(filename_question)
                    filename = filename_answer['filename']
                    save_transcript(transcript_t, None, output_format, filename)
                    print(colored(f"Transcript saved as {filename}.{output_format.lower()}", color="green"))
                else:
                    print(colored("Transcript not saved.", color="red"))
                if sentiment_answer['sentiment'] == 'Yes':
                    mood: Mood = get_sentiment(only_t)
                    print(
                        colored(f"{mood.emoji} Sentiment: {mood.sentiment_review} ({mood.sentiment:.2f})", color="blue"))
                elif sentiment_answer['sentiment'] == 'No':
                    pass
                if modify_answer['modify'] == 'Yes':
                    size_question = [
                        List('size',
                             message="Choose the desired size:",
                             choices=['Small', 'Medium', 'Large'],
                             ),
                    ]
                    size_answer = prompt(size_question)
                    size = size_answer['size']
                    if size == 'Small' or size == 'Large':
                        transcript_t = modify_transcript(transcript_t, size)
                        print(colored('Modified Transcript:', color="yellow"))
                        print(transcript_t)
                        print(colored("__________________________________________________________________________________", color="white"))
                    else:
                        print(colored("Transcript size not modified.", color="red"))
                ai_bot_question = [
                    List('ai_bot',
                         message="Do you want to use AI bot to chat with the transcript?",
                         choices=['Yes', 'No'],
                         ),
                ]
                ai_bot_answer = prompt(ai_bot_question)
                if ai_bot_answer['ai_bot'] == 'Yes':
                    deepinfra = DeepInfra(is_conversation=True,
                                          max_tokens=8000, timeout=30, model="microsoft/WizardLM-2-8x22B", )
                    while True:
                        prompt_message = "Enter your prompt (type 'exit' to exit): "
                        print(colored(prompt_message, color="green"), end="")
                        user_prompt = input()
                        if user_prompt.lower() == 'exit':
                            break
                        else:
                            optimized_prompt = f"[YT video]: {video_url}\n [Transcription]: {transcript_t}\n [User]: {user_prompt}"
                            with yaspin(text="Thinking...", color="green") as spinner:
                                response = deepinfra.ask(optimized_prompt)
                                spinner.ok("✅ ")
                            message = deepinfra.get_message(response)
                            print(colored(f"AI: {message}", color="blue"))
                elif ai_bot_answer['ai_bot'] == 'No':
                    pass

        elif submit.lower() == 'exit':
            print(colored("Exiting...", color="red"))
            sys.exit()
        else:
            print(colored("Invalid input. Please try again.", color="red"))


if __name__ == "__main__":
    main()