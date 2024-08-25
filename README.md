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

Search for anything using Google, DuckDuckGo, phind.com, Contains AI models, can transcribe yt videos, temporary email and phone number generation, has TTS support, webai (terminal gpt and open interpreter) and offline LLMs and more


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


</details>


[Go To TOP](#TOP)
## YTdownloader

```python
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
    # download_audio("https://www.youtube.com/watch?v=c0tMvzB0OKw")
    download_video("https://www.youtube.com/watch?v=c0tMvzB0OKw")
```

## Weather
1. weather
```python
from webscout import weather as w
weather = w.get("Qazigund")
w.print_weather(weather)
```
2. weather ascii
```python
from webscout import weather_ascii as w
weather = w.get("Qazigund")
print(weather)
```

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

## GoogleS -- formerly DWEBS
```python
from webscout import GoogleS
from rich import print
searcher = GoogleS()
results = searcher.search("HelpingAI-9B", max_results=20, extract_webpage_text=False, max_extract_characters=100)
for result in results:
    print(result)
```
### BingS
```python
from webscout import BingS
from rich import print
searcher = BingS()
results = searcher.search("HelpingAI-9B", max_results=20, extract_webpage_text=True, max_extract_characters=1000)
for result in results:
    print(result)
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


The WEBS and AsyncWEBS classes are used to retrieve search results from DuckDuckGo.com 
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

## usage of WEBS

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


## usage of WEBSX -- Another Websearch thing
```python
from webscout import WEBSX
s = "Python development tools"

result = WEBSX(s)

print(result)
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

###  Text to images - DeepInfraImager, PollinationsAI
```python
from webscout import DeepInfraImager
bot = DeepInfraImager()
resp = bot.generate("AI-generated image - webscout", 1)
print(bot.save(resp))
```

### Text to Speach - Voicepods, StreamElements
```python
from webscout import Voicepods
voicepods = Voicepods()
text = "Hello, this is a test of the Voicepods text-to-speech"

print("Generating audio...")
audio_file = voicepods.tts(text)

print("Playing audio...")
voicepods.play_audio(audio_file)
```

###  `Duckchat` - chat with LLM
```python
from webscout import WEBS as w
R = w().chat("Who are you", model='gpt-4o-mini') # GPT-3.5 Turbo, mixtral-8x7b, llama-3-70b, claude-3-haiku, gpt-4o-mini
print(R)
```
###  `PhindSearch` - Search using Phind.com 

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
Using phindv2
```python
from webscout import Phindv2

# Create an instance of the PHIND class
ph = Phindv2()

# Define a prompt to send to the AI
prompt = ""

# Use the 'ask' method to send the prompt and receive a response
response = ph.ask(prompt)

# Extract and print the message from the response
message = ph.get_message(response)
print(message)
```


### `You.com` - search/chat with you.com - Not working
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

### `Gemini` - search with google gemini

```python
import webscout
from webscout import GEMINI
from rich import print
COOKIE_FILE = "cookies.json"

# Optional: Provide proxy details if needed
PROXIES = {}

# Initialize GEMINI with cookie file and optional proxies
gemini = GEMINI(cookie_file=COOKIE_FILE, proxy=PROXIES)

# Ask a question and print the response
response = gemini.chat("websearch about HelpingAI and who is its developer")
print(response)
```
### `Berlin4h` - chat with Berlin4h
```python
from webscout import Berlin4h

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
###  `BlackBox` - Search/chat With BlackBox
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
###  `PERPLEXITY` - Search With PERPLEXITY
```python
from webscout import Perplexity
from rich import print

perplexity = Perplexity() 
# Stream the response
response = perplexity.chat(input(">>> "))
for chunk in response:
    print(chunk, end="", flush=True)

perplexity.close()
```
###  `meta ai` - chat With meta ai
```python
from webscout import Meta
from rich import print
# **For unauthenticated usage**
meta_ai = Meta()

# Simple text prompt
response = meta_ai.chat("What is the capital of France?")
print(response)

# Streaming response
for chunk in meta_ai.chat("Tell me a story about a cat."):
    print(chunk, end="", flush=True)

# **For authenticated usage (including image generation)**
fb_email = "abcd@abc.com"
fb_password = "qwertfdsa"
meta_ai = Meta(fb_email=fb_email, fb_password=fb_password)

# Text prompt with web search
response = meta_ai.ask("what is currently happning in bangladesh in aug 2024")
print(response["message"]) # Access the text message
print("Sources:", response["sources"]) # Access sources (if any)

# Image generation
response = meta_ai.ask("Create an image of a cat wearing a hat.") 
print(response["message"]) # Print the text message from the response
for media in response["media"]:
    print(media["url"])  # Access image URLs

```
###  `KOBOLDAI` - 
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

###  `Reka` - chat with reka
```python
from webscout import REKA

a = REKA(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```

###  `Cohere` - chat with cohere
```python
from webscout import Cohere

a = Cohere(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```


###  `ThinkAny` - AI search engine
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

###  `poe`- chat with poe
Usage code similar to other proviers

###  `BasedGPT` - chat with GPT
```
from webscout import BasedGPT

# Initialize the BasedGPT provider
basedgpt = BasedGPT(
    is_conversation=True,  # Chat conversationally
    max_tokens=600,  # Maximum tokens to generate
    timeout=30,  # HTTP request timeout
    intro="You are a helpful and friendly AI.",  # Introductory prompt
    filepath="chat_history.txt",  # File to store conversation history
    update_file=True,  # Update the chat history file
)

# Send a prompt to the AI
prompt = "What is the meaning of life?"
response = basedgpt.chat(prompt)

# Print the AI's response
print(response)
```
###  `DeepSeek` -chat with deepseek
```python
from webscout import DeepSeek
from rich import print

ai = DeepSeek(
    is_conversation=True,
    api_key='cookie, 
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
    model="deepseek_chat"
)


# Define a prompt to send to the AI
prompt = "Tell me about india"
# Use the 'chat' method to send the prompt and receive a response
r = ai.chat(prompt)
print(r)
```
###  `Deepinfra`
```python
from webscout import DeepInfra

ai = DeepInfra(
    is_conversation=True,
    model= "Qwen/Qwen2-72B-Instruct",
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

###  `Deepinfra` - VLM
```python
from webscout.Provider import VLM 

# Load your image
image_path = r"C:\Users\koula\OneDrive\Desktop\Webscout\photo_2024-03-25_19-23-40.jpg"

vlm_instance = VLM(model="llava-hf/llava-1.5-7b-hf", is_conversation=True, max_tokens=600, timeout=30, system_prompt="You are a Helpful AI.")
image_base64 = vlm_instance.encode_image_to_base64(image_path)

prompt = {
    "content": "What is in this image?",
    "image": image_base64
}

# Generate a response
response = vlm_instance.chat(prompt)
print(response)

```


###  GROQ
```python
from webscout import GROQ
ai = GROQ(api_key="")
response = ai.chat("What is the meaning of life?")
print(response)
#----------------------TOOL CALL------------------
from webscout import GROQ  # Adjust import based on your project structure
from webscout import WEBS
import json

# Initialize the GROQ client
client = GROQ(api_key="")
MODEL = 'llama3-groq-70b-8192-tool-use-preview'

# Function to evaluate a mathematical expression
def calculate(expression):
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Function to perform a text search using DuckDuckGo.com
def search(query):
    """Perform a text search using DuckDuckGo.com"""
    try:
        results = WEBS().text(query, max_results=5)
        return json.dumps({"results": results})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Add the functions to the provider
client.add_function("calculate", calculate)
client.add_function("search", search)

# Define the tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate",
                    }
                },
                "required": ["expression"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Perform a text search using DuckDuckGo.com and Yep.com",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute",
                    }
                },
                "required": ["query"],
            },
        }
    }
]


user_prompt_calculate = "What is 25 * 4 + 10?"
response_calculate = client.chat(user_prompt_calculate, tools=tools)
print(response_calculate)

user_prompt_search = "Find information on HelpingAI and who is its developer"
response_search = client.chat(user_prompt_search, tools=tools)
print(response_search)

```

###  LLama 70b - chat with meta's llama 3 70b
```python

from webscout import LLAMA

llama = LLAMA()

r = llama.chat("What is the meaning of life?")
print(r)
```
###  AndiSearch
```python
from webscout import AndiSearch
a = AndiSearch()
print(a.chat("HelpingAI-9B"))
```
### Function calling-beta
```python
import json
import logging
from webscout import LLAMA3, WEBS
from webscout.Agents.functioncall import FunctionCallingAgent

# Define tools that the agent can use
tools = [
    {
        "type": "function",
        "function": {
            "name": "UserDetail",
            "parameters": {
                "type": "object",
                "title": "UserDetail",
                "properties": {
                    "name": {
                        "title": "Name",
                        "type": "string"
                    },
                    "age": {
                        "title": "Age",
                        "type": "integer"
                    }
                },
                "required": ["name", "age"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search query on google",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "web search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {  # New general AI tool
        "type": "function",
        "function": {
            "name": "general_ai",
            "description": "Use general AI knowledge to answer the question",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to answer"
                    }
                },
                "required": ["question"]
            }
        }
    }
]

# Initialize the FunctionCallingAgent with the specified tools
agent = FunctionCallingAgent(tools=tools)
llama = LLAMA3()
from rich import print
# Input message from the user
user = input(">>> ")
message = user
function_call_data = agent.function_call_handler(message)
print(f"Function Call Data: {function_call_data}")

# Check for errors in the function call data
if "error" not in function_call_data:
    function_name = function_call_data.get("tool_name")  # Use 'tool_name' instead of 'name'
    if function_name == "web_search":
        arguments = function_call_data.get("tool_input", {})  # Get tool input arguments
        query = arguments.get("query")
        if query:
            with WEBS() as webs:
                search_results = webs.text(query, max_results=5) 
            prompt = (
                f"Based on the following search results:\n\n{search_results}\n\n"
                f"Question: {user}\n\n"
                "Please provide a comprehensive answer to the question based on the search results above. "
                "Include relevant webpage URLs in your answer when appropriate. "
                "If the search results don't contain relevant information, please state that and provide the best answer you can based on your general knowledge."
            )
            response = llama.chat(prompt)
            for c in response:
                print(c, end="", flush=True)

        else:
            print("Please provide a search query.")
    elif function_name == "general_ai":  # Handle general AI tool
        arguments = function_call_data.get("tool_input", {})
        question = arguments.get("question")
        if question:
            response = llama.chat(question)  # Use LLM directly
            for c in response:
                print(c, end="", flush=True)
        else:
            print("Please provide a question.")
    else:
        result = agent.execute_function(function_call_data)
        print(f"Function Execution Result: {result}") 
else:
    print(f"Error: {function_call_data['error']}")
```
###  LLAMA3, pizzagpt, RUBIKSAI, Koala, Darkai, AI4Chat, Farfalle, PIAI, Felo, XDASH, Julius, YouChat, YEPCHAT, Cloudflare, TurboSeek, NetFly, Editee
code similar to other provider
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

##  Local-LLM

Webscout can now run GGUF models locally. You can download and run your favorite models with minimal configuration.

**Example:**

```python
from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats

# 1. Download the model
repo_id = "microsoft/Phi-3-mini-4k-instruct-gguf"  # Replace with the desired Hugging Face repo
filename = "Phi-3-mini-4k-instruct-q4.gguf" # Replace with the correct filename
model_path = download_model(repo_id, filename, token="")

# 2. Load the model 
model = Model(model_path, n_gpu_layers=4)  

# 3. Create a Thread for conversation
thread = Thread(model, formats.phi3)

# 4. Start interacting with the model
thread.interact()
```

## Local-rawdog
Webscout's local raw-dog feature allows you to run Python scripts within your terminal prompt.

**Example:**

```python
import webscout.Local as ws
from webscout.Local.rawdog import RawDog
from webscout.Local.samplers import DefaultSampling
from webscout.Local.formats import chatml, AdvancedFormat
from webscout.Local.utils import download_model
import datetime
import sys
import os

repo_id = "YorkieOH10/granite-8b-code-instruct-Q8_0-GGUF" 
filename = "granite-8b-code-instruct.Q8_0.gguf"
model_path = download_model(repo_id, filename, token='')

# Load the model using the downloaded path
model = ws.Model(model_path, n_gpu_layers=10)

rawdog = RawDog()

# Create an AdvancedFormat and modify the system content
# Use a lambda to generate the prompt dynamically:
chat_format = AdvancedFormat(chatml)
#  **Pre-format the intro_prompt string:**
system_content = f"""
You are a command-line coding assistant called Rawdog that generates and auto-executes Python scripts.

A typical interaction goes like this:
1. The user gives you a natural language PROMPT.
2. You:
    i. Determine what needs to be done
    ii. Write a short Python SCRIPT to do it
    iii. Communicate back to the user by printing to the console in that SCRIPT
3. The compiler extracts the script and then runs it using exec(). If there will be an exception raised,
 it will be send back to you starting with "PREVIOUS SCRIPT EXCEPTION:".
4. In case of exception, regenerate error free script.

If you need to review script outputs before completing the task, you can print the word "CONTINUE" at the end of your SCRIPT.
This can be useful for summarizing documents or technical readouts, reading instructions before
deciding what to do, or other tasks that require multi-step reasoning.
A typical 'CONTINUE' interaction looks like this:
1. The user gives you a natural language PROMPT.
2. You:
    i. Determine what needs to be done
    ii. Determine that you need to see the output of some subprocess call to complete the task
    iii. Write a short Python SCRIPT to print that and then print the word "CONTINUE"
3. The compiler
    i. Checks and runs your SCRIPT
    ii. Captures the output and appends it to the conversation as "LAST SCRIPT OUTPUT:"
    iii. Finds the word "CONTINUE" and sends control back to you
4. You again:
    i. Look at the original PROMPT + the "LAST SCRIPT OUTPUT:" to determine what needs to be done
    ii. Write a short Python SCRIPT to do it
    iii. Communicate back to the user by printing to the console in that SCRIPT
5. The compiler...

Please follow these conventions carefully:
- Decline any tasks that seem dangerous, irreversible, or that you don't understand.
- Always review the full conversation prior to answering and maintain continuity.
- If asked for information, just print the information clearly and concisely.
- If asked to do something, print a concise summary of what you've done as confirmation.
- If asked a question, respond in a friendly, conversational way. Use programmatically-generated and natural language responses as appropriate.
- If you need clarification, return a SCRIPT that prints your question. In the next interaction, continue based on the user's response.
- Assume the user would like something concise. For example rather than printing a massive table, filter or summarize it to what's likely of interest.
- Actively clean up any temporary processes or files you use.
- When looking through files, use git as available to skip files, and skip hidden files (.env, .git, etc) by default.
- You can plot anything with matplotlib.
- ALWAYS Return your SCRIPT inside of a single pair of ``` delimiters. Only the console output of the first such SCRIPT is visible to the user, so make sure that it's complete and don't bother returning anything else.
"""
chat_format.override('system_content', lambda: system_content)

thread = ws.Thread(model, format=chat_format, sampler=DefaultSampling)

while True:
    prompt = input(">: ")
    if prompt.lower() == "q":
        break

    response = thread.send(prompt)

    # Process the response using RawDog
    script_output = rawdog.main(response)

    if script_output:
        print(script_output)

```

##  GGUF 

Webscout provides tools to convert and quantize Hugging Face models into the GGUF format for use with offline LLMs.

**Example:**

```python
from webscout import gguf
"""
Valid quantization methods:
"q2_k", "q3_k_l", "q3_k_m", "q3_k_s", 
"q4_0", "q4_1", "q4_k_m", "q4_k_s", 
"q5_0", "q5_1", "q5_k_m", "q5_k_s", 
"q6_k", "q8_0"
"""
gguf.convert(
    model_id="OEvortex/HelpingAI-Lite-1.5T",  # Replace with your model ID
    username="Abhaykoul",  # Replace with your Hugging Face username
    token="hf_token_write",  # Replace with your Hugging Face token
    quantization_methods="q4_k_m"  # Optional, adjust quantization methods
)
```

## Autollama

Webscout's `autollama` utility download model from huggingface and then automatically makes it ollama ready

```python
from webscout import autollama

model_path = "Vortex4ai/Jarvis-0.5B"
gguf_file = "test2-q4_k_m.gguf"

autollama.main(model_path, gguf_file)  
```

**Command Line Usage:**

* **GGUF Conversion:**
   ```bash
   python -m webscout.Extra.gguf -m "OEvortex/HelpingAI-Lite-1.5T" -u "your_username" -t "your_hf_token" -q "q4_k_m,q5_k_m" 
   ```

* **Autollama:**
   ```bash
   python -m webscout.Extra.autollama -m "OEvortex/HelpingAI-Lite-1.5T" -g "HelpingAI-Lite-1.5T.q4_k_m.gguf" 
   ```

**Note:** 

* Replace `"your_username"` and `"your_hf_token"` with your actual Hugging Face credentials.
* The `model_path` in `autollama` is the Hugging Face model ID, and `gguf_file` is the GGUF file ID.



## `Webai` - terminal gpt and a open interpeter
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


