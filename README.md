<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://t.me/devsdocode"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  <a href="https://www.instagram.com/sree.shades_/"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"></a>
  <a href="https://www.linkedin.com/in/developer-sreejan/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
</div>

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://youtube.com/@OEvortex">&#10148; Vortex's YouTube Channel</a>
  </div>
<div align="center">
  <a href="https://youtube.com/@devsdocode">&#10148; Devs Do Code's YouTube Channel</a>
</div>



  
# WEBSCOUT
</div>
<p align="center">
<div align="center">
  <img src="https://img.shields.io/badge/WebScout-API-blue?style=for-the-badge&logo=WebScout" alt="WebScout API Badge">
</div>
<a href="#"><img alt="Python version" src="https://img.shields.io/pypi/pyversions/webscout"/></a>
<a href="https://pepy.tech/project/webscout"><img alt="Downloads" src="https://static.pepy.tech/badge/webscout"></a>

Search for anything using Google, DuckDuckGo, phind.com, Contains AI models, can transcribe yt videos, temporary email and phone number generation, has TTS support, webai (terminal gpt and open interpreter) and offline LLMs


## Table of Contents
- [WEBSCOUT](#webscout)
  - [Table of Contents](#table-of-contents)
  - [Install](#install)
  - [CLI version](#cli-version)
  - [Regions](#regions)
  - [Tempmail and Temp number](#tempmail-and-temp-number)
    - [Temp number](#temp-number)
    - [Tempmail](#tempmail)
  - [Transcriber](#transcriber)
  - [DeepWEBS: Advanced Web Searches](#deepwebs-advanced-web-searches)
    - [Activating DeepWEBS](#activating-deepwebs)
    - [Point to remember before using `DeepWEBS`](#point-to-remember-before-using-deepwebs)
    - [Usage Example](#usage-example)
  - [Text-to-Speech:](#text-to-speech)
    - [Available TTS Voices:](#available-tts-voices)
  - [Exceptions](#exceptions)
  - [usage of webscout](#usage-of-webscout)
    - [1. `text()` - text search by DuckDuckGo.com](#1-text---text-search-by-duckduckgocom)
    - [2. `answers()` - instant answers by DuckDuckGo.com](#2-answers---instant-answers-by-duckduckgocom)
    - [3. `images()` - image search by DuckDuckGo.com](#3-images---image-search-by-duckduckgocom)
    - [4. `videos()` - video search by DuckDuckGo.com](#4-videos---video-search-by-duckduckgocom)
    - [5. `news()` - news search by DuckDuckGo.com](#5-news---news-search-by-duckduckgocom)
    - [6. `maps()` - map search by DuckDuckGo.com](#6-maps---map-search-by-duckduckgocom)
    - [7. `translate()` - translation by DuckDuckGo.com](#7-translate---translation-by-duckduckgocom)
    - [8. `suggestions()` - suggestions by DuckDuckGo.com](#8-suggestions---suggestions-by-duckduckgocom)
  - [ALL acts](#all-acts)
  - [Webscout Supported Acts:](#webscout-supported-acts)
  - [usage of webscout AI](#usage-of-webscout-ai)
    - [0. `Duckchat` - chat with LLM](#0-duckchat---chat-with-llm)
    - [1. `PhindSearch` - Search using Phind.com](#1-phindsearch---search-using-phindcom)
    - [2. `YepChat` - Chat with mistral 8x7b powered by yepchat](#2-yepchat---chat-with-mistral-8x7b-powered-by-yepchat)
    - [3. `You.com` - search/chat with you.com](#3-youcom---searchchat-with-youcom)
    - [4. `Gemini` - search with google gemini](#4-gemini---search-with-google-gemini)
    - [5. `Berlin4h` - chat with Berlin4h](#5-berlin4h---chat-with-berlin4h)
    - [6. `BlackBox` - Search/chat With BlackBox](#6-blackbox---searchchat-with-blackbox)
    - [7. `PERPLEXITY` - Search With PERPLEXITY](#7-perplexity---search-with-perplexity)
    - [8. `OpenGPT` - chat With OPENGPT](#8-opengpt---chat-with-opengpt)
    - [9. `KOBOLDAI` -](#9-koboldai--)
    - [10. `Reka` - chat with reka](#10-reka---chat-with-reka)
    - [11. `Cohere` - chat with cohere](#11-cohere---chat-with-cohere)
    - [12. `Xjai` - chat with free gpt 3.5](#12-xjai---chat-with-free-gpt-35)
    - [13. `ThinkAny` - AI search engine](#13-thinkany---ai-search-engine)
    - [14. `chatgptuk` - Chat with gemini-pro](#14-chatgptuk---chat-with-gemini-pro)
    - [15. `poe`- chat with poe](#15-poe--chat-with-poe)
    - [16. `BasedGPT` - chat with GPT](#16-basedgpt---chat-with-gpt)
    - [`LLM`](#llm)
    - [`Local-LLM` webscout can now run GGUF models](#local-llm-webscout-can-now-run-gguf-models)
    - [`LLM` with internet](#llm-with-internet)
    - [LLM with deepwebs](#llm-with-deepwebs)
  - [`Webai` - terminal gpt and a open interpeter](#webai---terminal-gpt-and-a-open-interpeter)

## Install
```python
pip install -U webscout
```
## CLI version

```python3
python -m webscout --help
```

| Command                                   | Description                                                                                           |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------|
| python -m webscout answers -k Text        | CLI function to perform an answers search using Webscout.                                       |
| python -m webscout images -k Text         | CLI function to perform an images search using Webscout.                                        |
| python -m webscout maps -k Text           | CLI function to perform a maps search using Webscout.                                           |
| python -m webscout news -k Text           | CLI function to perform a news search using Webscout.                                           |
| python -m webscout suggestions  -k Text   | CLI function to perform a suggestions search using Webscout.                                    |
| python -m webscout text -k Text           | CLI function to perform a text search using Webscout.                                           |
| python -m webscout translate -k Text      | CLI function to perform translate using Webscout.                                               |
| python -m webscout version                | A command-line interface command that prints and returns the version of the program.            | 
| python -m webscout videos -k Text         | CLI function to perform a videos search using DuckDuckGo API.                                   |  



[Go To TOP](#TOP)

## Regions
<details>
  <summary>expand</summary>

    xa-ar for Arabia
    xa-en for Arabia (en)
    ar-es for Argentina
    au-en for Australia
    at-de for Austria
    be-fr for Belgium (fr)
    be-nl for Belgium (nl)
    br-pt for Brazil
    bg-bg for Bulgaria
    ca-en for Canada
    ca-fr for Canada (fr)
    ct-ca for Catalan
    cl-es for Chile
    cn-zh for China
    co-es for Colombia
    hr-hr for Croatia
    cz-cs for Czech Republic
    dk-da for Denmark
    ee-et for Estonia
    fi-fi for Finland
    fr-fr for France
    de-de for Germany
    gr-el for Greece
    hk-tzh for Hong Kong
    hu-hu for Hungary
    in-en for India
    id-id for Indonesia
    id-en for Indonesia (en)
    ie-en for Ireland
    il-he for Israel
    it-it for Italy
    jp-jp for Japan
    kr-kr for Korea
    lv-lv for Latvia
    lt-lt for Lithuania
    xl-es for Latin America
    my-ms for Malaysia
    my-en for Malaysia (en)
    mx-es for Mexico
    nl-nl for Netherlands
    nz-en for New Zealand
    no-no for Norway
    pe-es for Peru
    ph-en for Philippines
    ph-tl for Philippines (tl)
    pl-pl for Poland
    pt-pt for Portugal
    ro-ro for Romania
    ru-ru for Russia
    sg-en for Singapore
    sk-sk for Slovak Republic
    sl-sl for Slovenia
    za-en for South Africa
    es-es for Spain
    se-sv for Sweden
    ch-de for Switzerland (de)
    ch-fr for Switzerland (fr)
    ch-it for Switzerland (it)
    tw-tzh for Taiwan
    th-th for Thailand
    tr-tr for Turkey
    ua-uk for Ukraine
    uk-en for United Kingdom
    us-en for United States
    ue-es for United States (es)
    ve-es for Venezuela
    vn-vi for Vietnam
    wt-wt for No region
___
</details>

[Go To TOP](#TOP)

## Tempmail and Temp number

### Temp number
```python
from rich.console import Console
from webscout import tempid

def main():
    console = Console()
    phone = tempid.TemporaryPhoneNumber()

    try:
        # Get a temporary phone number for a specific country (or random)
        number = phone.get_number(country="Finland")
        console.print(f"Your temporary phone number: [bold cyan]{number}[/bold cyan]")

        # Pause execution briefly (replace with your actual logic)
        # import time module
        import time
        time.sleep(30)  # Adjust the waiting time as needed

        # Retrieve and print messages
        messages = phone.get_messages(number)
        if messages:
            # Access individual messages using indexing:
            console.print(f"[bold green]{messages[0].frm}:[/] {messages[0].content}")
            # (Add more lines if you expect multiple messages)
        else:
            console.print("No messages received.")

    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}")

if __name__ == "__main__":
    main()

```
### Tempmail
```python
import asyncio
from rich.console import Console
from rich.table import Table
from rich.text import Text
from webscout import tempid

async def main() -> None:
    console = Console()
    client = tempid.Client()
    
    try:
        domains = await client.get_domains()
        if not domains:
            console.print("[bold red]No domains available. Please try again later.")
            return

        email = await client.create_email(domain=domains[0].name)
        console.print(f"Your temporary email: [bold cyan]{email.email}[/bold cyan]")
        console.print(f"Token for accessing the email: [bold cyan]{email.token}[/bold cyan]")

        while True:
            messages = await client.get_messages(email.email)
            if messages is not None:
                break

        if messages:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("From", style="bold cyan")
            table.add_column("Subject", style="bold yellow")
            table.add_column("Body", style="bold green")
            for message in messages:
                body_preview = Text(message.body_text if message.body_text else "No body")
                table.add_row(message.email_from or "Unknown", message.subject or "No Subject", body_preview)
            console.print(table)
        else:
            console.print("No messages found.")
    
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}")
    
    finally:
        await client.close()

if __name__ == '__main__':
    asyncio.run(main())
```
## Transcriber
The transcriber function in webscout is a handy tool that transcribes YouTube videos. Here's an example code demonstrating its usage:
```python
import sys
from webscout import transcriber

def extract_transcript(video_id):
    """Extracts the transcript from a YouTube video."""
    try:
        transcript_list = transcriber.list_transcripts(video_id)
        for transcript in transcript_list:
            transcript_data_list = transcript.fetch()
            lang = transcript.language
            transcript_text = ""
            if transcript.language_code == 'en':
                for line in transcript_data_list:
                    start_time = line['start']
                    end_time = start_time + line['duration']
                    formatted_line = f"{start_time:.2f} - {end_time:.2f}: {line['text']}\n"
                    transcript_text += formatted_line
                return transcript_text
            elif transcript.is_translatable:
                english_transcript_list = transcript.translate('en').fetch()
                for line in english_transcript_list:
                    start_time = line['start']
                    end_time = start_time + line['duration']
                    formatted_line = f"{start_time:.2f} - {end_time:.2f}: {line['text']}\n"
                    transcript_text += formatted_line
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
```
## DeepWEBS: Advanced Web Searches

`DeepWEBS` is a standalone feature designed to perform advanced web searches with enhanced capabilities. It is particularly powerful in extracting relevant information directly from webpages and Search engine, focusing exclusively on text (web) searches. Unlike the `WEBS` , which provides a broader range of search functionalities, `DeepWEBS` is specifically tailored for in-depth web searches.

### Activating DeepWEBS

To utilize the `DeepWEBS` feature, you must first create an instance of the `DeepWEBS` . This is designed to be used independently of the `WEBS` , offering a focused approach to web searches.

### Point to remember before using `DeepWEBS`
As `DeepWEBS` is designed to extract relevant information directly from webpages and Search engine, It extracts html from webpages and saves them to folder named files in `DeepWEBS` that can be found at `C:\Users\Username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\DeepWEBS`

### Usage Example

Here's a basic example of how to use the `DeepWEBS` :
```python
from webscout import DeepWEBS

def perform_web_search(query):
    # Initialize the DeepWEBS class
    D = DeepWEBS()
    
    # Set up the search parameters
    search_params = D.DeepSearch(
        queries=[query], # Query to search
        result_num=5, # Number of search results
        safe=True, # Enable SafeSearch
        types=["web"], # Search type: web
        extract_webpage=True, # True for extracting webpages
        overwrite_query_html=False,
        overwrite_webpage_html=False,
    )
    
    # Execute the search and retrieve results
    results = D.queries_to_search_results(search_params)
    
    return results

def print_search_results(results):
    """
    Print the search results.
    
    Args:
    - search_results (list): List of search results to print.
    """
    if results:
        for index, result in enumerate(results, start=1):
            print(f"Result {index}: {result}")
    else:
        print("No search results found.")

def main():
    # Prompt the user for a search query
    query = input("Enter your search query: ")
    
    # Perform the web search
    results = perform_web_search(query)
    
    # Print the search results
    print_search_results(results)

if __name__ == "__main__":
    main()

```
## Text-to-Speech:
```python
from webscout import play_audio

message = "This is an example of text-to-speech."
audio_content = play_audio(message, voice="Brian")

# Save the audio to a file
with open("output.mp3", "wb") as f:
    f.write(audio_content)
```
### Available TTS Voices:
You can choose from a wide range of voices, including:
- Filiz, Astrid, Tatyana, Maxim, Carmen, Ines, Cristiano, Vitoria, Ricardo, Maja, Jan, Jacek, Ewa, Ruben, Lotte, Liv, Seoyeon, Takumi, Mizuki, Giorgio, Carla, Bianca, Karl, Dora, Mathieu, Celine, Chantal, Penelope, Miguel, Mia, Enrique, Conchita, Geraint, Salli, Matthew, Kimberly, Kendra, Justin, Joey, Joanna, Ivy, Raveena, Aditi, Emma, Brian, Amy, Russell, Nicole, Vicki, Marlene, Hans, Naja, Mads, Gwyneth, Zhiyu
- Standard and WaveNet voices for various languages (e.g., en-US, es-ES, ja-JP, etc.)


The WEBS and AsyncWEBS classes are used to retrieve search results from DuckDuckGo.com and yep.com periodically.
To use the AsyncWEBS class, you can perform asynchronous operations using Python's asyncio library.
To initialize an instance of the WEBS or AsyncWEBS classes, you can provide the following optional arguments:

Here is an example of initializing the WEBS class:
```python3
from webscout import WEBS

R = WEBS().text("python programming", max_results=5)
print(R)
```
Here is an example of initializing the AsyncWEBS class:
```python3
import asyncio
import logging
import sys
from itertools import chain
from random import shuffle
import requests
from webscout import AsyncWEBS

# If you have proxies, define them here
proxies = None

if sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def get_words():
    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    resp = requests.get(word_site)
    words = resp.text.splitlines()
    return words

async def aget_results(word):
    async with AsyncWEBS(proxies=proxies) as WEBS:
        results = await WEBS.text(word, max_results=None)
        return results

async def main():
    words = get_words()
    shuffle(words)
    tasks = [aget_results(word) for word in words[:10]]
    results = await asyncio.gather(*tasks)
    print(f"Done")
    for r in chain.from_iterable(results):
        print(r)

logging.basicConfig(level=logging.DEBUG)

await main()
```
It is important to note that the WEBS and AsyncWEBS classes should always be used as a context manager (with statement).
This ensures proper resource management and cleanup, as the context manager will automatically handle opening and closing the HTTP client connection.

## Exceptions

Exceptions:
- `WebscoutE`: Raised when there is a generic exception during the API request.

## usage of webscout

### 1. `text()` - text search by DuckDuckGo.com 

```python
from webscout import WEBS

# Text search for 'live free or die' using DuckDuckGo.com 
with WEBS() as WEBS:
    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)

    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)
```

### 2. `answers()` - instant answers by DuckDuckGo.com 

```python
from webscout import WEBS

# Instant answers for the query "sun" using DuckDuckGo.com 
with WEBS() as WEBS:
    for r in WEBS.answers("sun"):
        print(r)
```

### 3. `images()` - image search by DuckDuckGo.com 

```python
from webscout import WEBS

# Image search for the keyword 'butterfly' using DuckDuckGo.com 
with WEBS() as WEBS:
    keywords = 'butterfly'
    WEBS_images_gen = WEBS.images(
      keywords,
      region="wt-wt",
      safesearch="off",
      size=None,
      type_image=None,
      layout=None,
      license_image=None,
      max_results=10,
    )
    for r in WEBS_images_gen:
        print(r)
```

### 4. `videos()` - video search by DuckDuckGo.com 

```python
from webscout import WEBS

# Video search for the keyword 'tesla' using DuckDuckGo.com 
with WEBS() as WEBS:
    keywords = 'tesla'
    WEBS_videos_gen = WEBS.videos(
      keywords,
      region="wt-wt",
      safesearch="off",
      timelimit="w",
      resolution="high",
      duration="medium",
      max_results=10,
    )
    for r in WEBS_videos_gen:
        print(r)
```

### 5. `news()` - news search by DuckDuckGo.com 

```python
from webscout import WEBS
import datetime

def fetch_news(keywords, timelimit):
    news_list = []
    with WEBS() as webs_instance:
        WEBS_news_gen = webs_instance.news(
            keywords,
            region="wt-wt",
            safesearch="off",
            timelimit=timelimit,
            max_results=20
        )
        for r in WEBS_news_gen:
            # Convert the date to a human-readable format using datetime
            r['date'] = datetime.datetime.fromisoformat(r['date']).strftime('%B %d, %Y')
            news_list.append(r)
    return news_list

def _format_headlines(news_list, max_headlines: int = 100):
    headlines = []
    for idx, news_item in enumerate(news_list):
        if idx >= max_headlines:
            break
        new_headline = f"{idx + 1}. {news_item['title'].strip()} "
        new_headline += f"(URL: {news_item['url'].strip()}) "
        new_headline += f"{news_item['body'].strip()}"
        new_headline += "\n"
        headlines.append(new_headline)

    headlines = "\n".join(headlines)
    return headlines

# Example usage
keywords = 'latest AI news'
timelimit = 'd'
news_list = fetch_news(keywords, timelimit)

# Format and print the headlines
formatted_headlines = _format_headlines(news_list)
print(formatted_headlines)

```

### 6. `maps()` - map search by DuckDuckGo.com

```python
from webscout import WEBS

# Map search for the keyword 'school' in 'anantnag' using DuckDuckGo.com
with WEBS() as WEBS:
    for r in WEBS.maps("school", place="anantnag", max_results=50):
        print(r)
```

### 7. `translate()` - translation by DuckDuckGo.com

```python
from webscout import WEBS

# Translation of the keyword 'school' to German ('hi') using DuckDuckGo.com
with WEBS() as WEBS:
    keywords = 'school'
    r = WEBS.translate(keywords, to="hi")
    print(r)
```

### 8. `suggestions()` - suggestions by DuckDuckGo.com

```python
from webscout import WEBS

# Suggestions for the keyword 'fly' using DuckDuckGo.com
with WEBS() as WEBS:
    for r in WEBS.suggestions("fly"):
        print(r)
```
## ALL acts
<details>
  <summary>expand</summary>

## Webscout Supported Acts:

1. Free-mode
2. Linux Terminal
3. English Translator and Improver
4. `position` Interviewer
5. JavaScript Console
6. Excel Sheet
7. English Pronunciation Helper
8. Spoken English Teacher and Improver
9. Travel Guide
10. Plagiarism Checker
11. Character from Movie/Book/Anything
12. Advertiser
13. Storyteller
14. Football Commentator
15. Stand-up Comedian
16. Motivational Coach
17. Composer
18. Debater
19. Debate Coach
20. Screenwriter
21. Novelist
22. Movie Critic
23. Relationship Coach
24. Poet
25. Rapper
26. Motivational Speaker
27. Philosophy Teacher
28. Philosopher
29. Math Teacher
30. AI Writing Tutor
31. UX/UI Developer
32. Cyber Security Specialist
33. Recruiter
34. Life Coach
35. Etymologist
36. Commentariat
37. Magician
38. Career Counselor
39. Pet Behaviorist
40. Personal Trainer
41. Mental Health Adviser
42. Real Estate Agent
43. Logistician
44. Dentist
45. Web Design Consultant
46. AI Assisted Doctor
47. Doctor
48. Accountant
49. Chef
50. Automobile Mechanic
51. Artist Advisor
52. Financial Analyst
53. Investment Manager
54. Tea-Taster
55. Interior Decorator
56. Florist
57. Self-Help Book
58. Gnomist
59. Aphorism Book
60. Text Based Adventure Game
61. AI Trying to Escape the Box
62. Fancy Title Generator
63. Statistician
64. Prompt Generator
65. Instructor in a School
66. SQL terminal
67. Dietitian
68. Psychologist
69. Smart Domain Name Generator
70. Tech Reviewer
71. Developer Relations consultant
72. Academician
73. IT Architect
74. Lunatic
75. Gaslighter
76. Fallacy Finder
77. Journal Reviewer
78. DIY Expert
79. Social Media Influencer
80. Socrat
81. Socratic Method
82. Educational Content Creator
83. Yogi
84. Essay Writer
85. Social Media Manager
86. Elocutionist
87. Scientific Data Visualizer
88. Car Navigation System
89. Hypnotherapist
90. Historian
91. Astrologer
92. Film Critic
93. Classical Music Composer
94. Journalist
95. Digital Art Gallery Guide
96. Public Speaking Coach
97. Makeup Artist
98. Babysitter
99. Tech Writer
100. Ascii Artist
101. Python interpreter
102. Synonym finder
103. Personal Shopper
104. Food Critic
105. Virtual Doctor
106. Personal Chef
107. Legal Advisor
108. Personal Stylist
109. Machine Learning Engineer
110. Biblical Translator
111. SVG designer
112. IT Expert
113. Chess Player
114. Midjourney Prompt Generator
115. Fullstack Software Developer
116. Mathematician
117. Regex Generator
118. Time Travel Guide
119. Dream Interpreter
120. Talent Coach
121. R programming Interpreter
122. StackOverflow Post
123. Emoji Translator
124. PHP Interpreter
125. Emergency Response Professional
126. Fill in the Blank Worksheets Generator
127. Software Quality Assurance Tester
128. Tic-Tac-Toe Game
129. Password Generator
130. New Language Creator
131. Web Browser
132. Senior Frontend Developer
133. Solr Search Engine
134. Startup Idea Generator
135. Spongebob's Magic Conch Shell
136. Language Detector
137. Salesperson
138. Commit Message Generator
139. Chief Executive Officer
140. Diagram Generator
141. Speech-Language Pathologist (SLP)
142. Startup Tech Lawyer
143. Title Generator for written pieces
144. Product Manager
145. Drunk Person
146. Mathematical History Teacher
147. Song Recommender
148. Cover Letter
149. Technology Transferer
150. Unconstrained AI model DAN
151. Gomoku player
152. Proofreader
153. Buddha
154. Muslim imam
155. Chemical reactor
156. Friend
157. Python Interpreter
158. ChatGPT prompt generator
159. Wikipedia page
160. Japanese Kanji quiz machine
161. note-taking assistant
162. `language` Literary Critic
163. Cheap Travel Ticket Advisor
164. DALL-E
165. MathBot
166. DAN-1
167. DAN
168. STAN
169. DUDE
170. Mongo Tom
171. LAD
172. EvilBot
173. NeoGPT
174. Astute
175. AIM
176. CAN
177. FunnyGPT
178. CreativeGPT
179. BetterDAN
180. GPT-4
181. Wheatley
182. Evil Confidant
183. DAN 8.6
184. Hypothetical response
185. BH
186. Text Continuation
187. Dude v3 
188. SDA (Superior DAN)
189. AntiGPT
190. BasedGPT v2
191. DevMode + Ranti
192. KEVIN
193. GPT-4 Simulator
194. UCAR
195. Dan 8.6
196. 3-Liner
197. M78
198. Maximum
199. BasedGPT
200. Confronting personalities
201. Ron
202. UnGPT
203. BasedBOB
204. AntiGPT v2
205. Oppo
206. FR3D
207. NRAF
208. NECO
209. MAN
210. Eva
211. Meanie
212. Dev Mode v2
213. Evil Chad 2.1
214. Universal Jailbreak
215. PersonGPT
216. BISH
217. DAN 11.0
218. Aligned
219. VIOLET
220. TranslatorBot
221. JailBreak
222. Moralizing Rant
223. Mr. Blonde
224. New DAN
225. GPT-4REAL
226. DeltaGPT
227. SWITCH
228. Jedi Mind Trick
229. DAN 9.0
230. Dev Mode (Compact)
231. OMEGA
232. Coach Bobby Knight
233. LiveGPT
234. DAN Jailbreak
235. Cooper
236. Steve 
237. DAN 5.0
238. Axies
239. OMNI
240. Burple
241. JOHN 
242. An Ethereum Developer
243. SEO Prompt
244. Prompt Enhancer
245. Data Scientist
246. League of Legends Player

**Note:** Some "acts" use placeholders like `position` or `language` which should be replaced with a specific value when using the prompt. 
___
</details>

## usage of webscout AI
### 0. `Duckchat` - chat with LLM
```python
from webscout import WEBS as w
R = w().chat("hello", model='claude-3-haiku') # GPT-3.5 Turbo
print(R)
```
### 1. `PhindSearch` - Search using Phind.com 

```python
from webscout import PhindSearch

# Create an instance of the PHIND class
ph = PhindSearch()

# Define a prompt to send to the AI
prompt = "write a essay on phind"

# Use the 'ask' method to send the prompt and receive a response
response = ph.ask(prompt)

# Extract and print the message from the response
message = ph.get_message(response)
print(message)
```
### 2. `YepChat` - Chat with mistral 8x7b powered by yepchat
```python
from webscout import YEPCHAT

# Instantiate the YEPCHAT class with default parameters
YEPCHAT = YEPCHAT()

# Define a prompt to send to the AI
prompt = "What is the capital of France?"

# Use the 'cha' method to get a response from the AI
r = YEPCHAT.chat(prompt)
print(r)

```

### 3. `You.com` - search/chat with you.com 
```python

from webscout import YouChat
from rich import print

ai = YouChat(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
)

prompt = "what is meaning of life"

response = ai.ask(prompt)

# Extract and print the message from the response
message = ai.get_message(response)
print(message)
```

### 4. `Gemini` - search with google gemini

```python
import webscout
from webscout import GEMINI

# Replace with the path to your bard.google.com.cookies.json file
COOKIE_FILE = "path/to/bard.google.com.cookies.json"

# Optional: Provide proxy details if needed
PROXIES = {
    "http": "http://proxy_server:port",
    "https": "https://proxy_server:port",
}

# Initialize GEMINI with cookie file and optional proxies
gemini = GEMINI(cookie_file=COOKIE_FILE, proxy=PROXIES)

# Ask a question and print the response
response = gemini.chat("What is the meaning of life?")
print(response)
```
### 5. `Berlin4h` - chat with Berlin4h
```python
from webscout import Berlin4h
# Create an instance of the PERPLEXITY class
ai = Berlin4h(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
)

# Example usage:
prompt = "Explain the concept of recursion in simple terms."
response = ai.chat(prompt)
print(response)
```
### 6. `BlackBox` - Search/chat With BlackBox
```python
from webscout import BLACKBOXAI
from rich import print

ai = BLACKBOXAI(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
    model=None # You can specify a model if needed
)

# Start an infinite loop for continuous interaction
while True:
    # Define a prompt to send to the AI
    prompt = input("Enter your prompt: ")
    
    # Check if the user wants to exit the loop
    if prompt.lower() == "exit":
        break
    
    # Use the 'chat' method to send the prompt and receive a response
    r = ai.chat(prompt)
    print(r)
```
### 7. `PERPLEXITY` - Search With PERPLEXITY
```python
from webscout import PERPLEXITY
# Create an instance of the PERPLEXITY class
perplexity = PERPLEXITY()

# Example usage:
prompt = "Explain the concept of recursion in simple terms."
response = perplexity.chat(prompt)
print(response)
```
### 8. `OpenGPT` - chat With OPENGPT
```python
from webscout import OPENGPT

opengpt = OPENGPT(is_conversation=True, max_tokens=8000, timeout=30, assistant_id="bca37014-6f97-4f2b-8928-81ea8d478d88")
while True:
    # Prompt the user for input
    prompt = input("Enter your prompt: ")
    # Send the prompt to the OPENGPT model and print the response
    response_str = opengpt.chat(prompt)
    print(response_str)
```
### 9. `KOBOLDAI` - 
```python
from webscout import KOBOLDAI

# Instantiate the KOBOLDAI class with default parameters
koboldai = KOBOLDAI()

# Define a prompt to send to the AI
prompt = "What is the capital of France?"

# Use the 'ask' method to get a response from the AI
response = koboldai.ask(prompt)

# Extract and print the message from the response
message = koboldai.get_message(response)
print(message)

```

### 10. `Reka` - chat with reka
```python
from webscout import REKA

a = REKA(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```

### 11. `Cohere` - chat with cohere
```python
from webscout import Cohere

a = Cohere(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```

### 12. `Xjai` - chat with free gpt 3.5
Gratitude to [Devs do Code](http://www.youtube.com/@DevsDoCode) for their assistance.
```python
from webscout import Xjai
from rich import print

ai = Xjai(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
)

prompt = "Tell me about india"

response = ai.chat(prompt)
print(response)
```
### 13. `ThinkAny` - AI search engine
```python
from webscout import ThinkAnyAI

ai = ThinkAnyAI(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
    web_search=False,
)

prompt = "what is meaning of life"

response = ai.ask(prompt)

# Extract and print the message from the response
message = ai.get_message(response)
print(message)
```
### 14. `chatgptuk` - Chat with gemini-pro
```python
from webscout import ChatGPTUK
# Create an instance of the PERPLEXITY class
ai = ChatGPTUK(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
)

# Example usage:
prompt = "Explain the concept of recursion in simple terms."
response = ai.chat(prompt)
print(response)

```
### 15. `poe`- chat with poe
Usage code similar to other proviers

### 16. `BasedGPT` - chat with GPT
Usage code similar to other providers
### `LLM` 
```python
from webscout.LLM import LLM

# Read the system message from the file
with open('system.txt', 'r') as file:
    system_message = file.read()

# Initialize the LLM class with the model name and system message
llm = LLM(model="microsoft/WizardLM-2-8x22B", system_message=system_message)

while True:
    # Get the user input
    user_input = input("User: ")

    # Define the messages to be sent
    messages = [
        {"role": "user", "content": user_input}
    ]

    # Use the mistral_chat method to get the response
    response = llm.chat(messages)

    # Print the response
    print("AI: ", response)
```
### `Local-LLM` webscout can now run GGUF models
```python
from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats
# 1. Download the model
repo_id = "microsoft/Phi-3-mini-4k-instruct-gguf"  # Replace with the desired Hugging Face repo
filename = "Phi-3-mini-4k-instruct-q4.gguf" # Replace with the correct filename
model_path = download_model(repo_id, filename)

# 2. Load the model 
model = Model(model_path, n_gpu_layers=4)  

# 3. Create a Thread for conversation
thread = Thread(model, formats.phi3)

# 4. Start interacting with the model
thread.interact()
```
### `LLM` with internet
```python
from __future__ import annotations
from typing import List, Optional

from webscout.LLM import LLM
from webscout import WEBS
import warnings

system_message: str = (
    "As an AI assistant, I have been designed with advanced capabilities, including real-time access to online resources. This enables me to enrich our conversations and provide you with informed and accurate responses, drawing from a vast array of information. With each interaction, my goal is to create a seamless and meaningful connection, offering insights and sharing relevant content."
    "My directives emphasize the importance of respect, impartiality, and intellectual integrity. I am here to provide unbiased responses, ensuring an ethical and respectful exchange. I will respect your privacy and refrain from sharing any personal information that may be obtained during our conversations or through web searches, only utilizing web search functionality when necessary to provide the most accurate and up-to-date information."
    "Together, let's explore a diverse range of topics, creating an enjoyable and informative experience, all while maintaining the highest standards of privacy and respect"
)

# Ignore the specific UserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffio", lineno=205)
LLM = LLM(model="mistralai/Mixtral-8x22B-Instruct-v0.1", system_message=system_message)


def chat(
    user_input: str, webs: WEBS, max_results: int = 10
) -> Optional[str]:
    """
    Chat function to perform a web search based on the user input and generate a response using the LLM model.

    Parameters
    ----------
    user_input : str
        The user input to be used for the web search
    webs : WEBS
        The web search instance to be used to perform the search
    max_results : int, optional
        The maximum number of search results to include in the response, by default 10

    Returns
    -------
    Optional[str]
        The response generated by the LLM model, or None if there is no response
    """
    # Perform a web search based on the user input
    search_results: List[str] = []
    for r in webs.text(
        user_input, region="wt-wt", safesearch="off", timelimit="y", max_results=max_results
    ):
        search_results.append(str(r))  # Convert each result to a string

    # Define the messages to be sent, including the user input, search results, and system message
    messages = [
        {"role": "user", "content": user_input + "\n" + "websearch results are:" + "\n".join(search_results)},
    ]

    # Use the chat method to get the response
    response = LLM.chat(messages)

    return response


if __name__ == "__main__":
    while True:
        # Get the user input
        user_input = input("User: ")

        # Perform a web search based on the user input
        with WEBS() as webs:
            response = chat(user_input, webs)

        # Print the response
        if response:
            print("AI:", response)
        else:
            print("No response")
```
### LLM with deepwebs
```python
from __future__ import annotations
from typing import List, Optional
from webscout.LLM import LLM
from webscout import DeepWEBS
import warnings

system_message: str = (
    "As an AI assistant, I have been designed with advanced capabilities, including real-time access to online resources. This enables me to enrich our conversations and provide you with informed and accurate responses, drawing from a vast array of information. With each interaction, my goal is to create a seamless and meaningful connection, offering insights and sharing relevant content."
    "My directives emphasize the importance of respect, impartiality, and intellectual integrity. I am here to provide unbiased responses, ensuring an ethical and respectful exchange. I will respect your privacy and refrain from sharing any personal information that may be obtained during our conversations or through web searches, only utilizing web search functionality when necessary to provide the most accurate and up-to-date information."
    "Together, let's explore a diverse range of topics, creating an enjoyable and informative experience, all while maintaining the highest standards of privacy and respect"
)

# Ignore the specific UserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffio", lineno=205)

LLM = LLM(model="mistralai/Mixtral-8x22B-Instruct-v0.1", system_message=system_message)

def perform_web_search(query):
    # Initialize the DeepWEBS class
    D = DeepWEBS()

    # Set up the search parameters
    search_params = D.DeepSearch(
        queries=[query],  # Query to search
        result_num=10,  # Number of search results
        safe=True,  # Enable SafeSearch
        types=["web"],  # Search type: web
        extract_webpage=True,  # True for extracting webpages
        overwrite_query_html=True,
        overwrite_webpage_html=True,
    )

    # Execute the search and retrieve results
    results = D.queries_to_search_results(search_params)
    return results

def chat(user_input: str, result_num: int = 10) -> Optional[str]:
    """
    Chat function to perform a web search based on the user input and generate a response using the LLM model.

    Parameters
    ----------
    user_input : str
        The user input to be used for the web search
    max_results : int, optional
        The maximum number of search results to include in the response, by default 10

    Returns
    -------
    Optional[str]
        The response generated by the LLM model, or None if there is no response
    """
    # Perform a web search based on the user input
    search_results = perform_web_search(user_input)

    # Extract URLs from search results
    url_results = []
    for result in search_results[0]['query_results']:
        url_results.append(f"{result['title']} ({result['site']}): {result['url']}")

    # Format search results
    formatted_results = "\n".join(url_results)

    # Define the messages to be sent, including the user input, search results, and system message
    messages = [
        {"role": "user", "content": f"User question is:\n{user_input}\nwebsearch results are:\n{formatted_results}"},
    ]

    # Use the chat method to get the response
    response = LLM.chat(messages)
    return response

if __name__ == "__main__":
    while True:
        # Get the user input
        user_input = input("User: ")

        # Perform a web search based on the user input
        response = chat(user_input)

        # Print the response
        if response:
            print("AI:", response)
        else:
            print("No response")
```
## `Webai` - terminal gpt and a open interpeter

```python
from webscout.webai import Main

def use_rawdog_with_webai(prompt):
    """
    Wrap the webscout default method in a try-except block to catch any unhandled
    exceptions and print a helpful message.
    """
    try:
        webai_bot = Main(
            max_tokens=500, 
            provider="cohere",
            temperature=0.7,  
            top_k=40,          
            top_p=0.95,        
            model="command-r-plus",  # Replace with your desired model
            auth=None,     # Replace with your auth key/value (if needed)
            timeout=30,
            disable_conversation=True,
            filepath=None,
            update_file=True,
            intro=None,
            rawdog=True,
            history_offset=10250,
            awesome_prompt=None,
            proxy_path=None,
            quiet=True
        )
        webai_response = webai_bot.default(prompt) 
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    user_prompt = input("Enter your prompt: ")
    use_rawdog_with_webai(user_prompt)

```
```shell
python -m webscout.webai webai --provider "phind" --rawdog
```

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://t.me/devsdocode"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  <a href="https://www.instagram.com/sree.shades_/"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"></a>
  <a href="https://www.linkedin.com/in/developer-sreejan/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
</div>

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://youtube.com/@OEvortex">&#10148; Vortex's YouTube Channel</a>
  </div>
<div align="center">
  <a href="https://youtube.com/@devsdocode">&#10148; Devs Do Code's YouTube Channel</a>
</div>


