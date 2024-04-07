#  webscout
<p align="center">

<a href="#"><img alt="Python version" src="https://img.shields.io/pypi/pyversions/webscout"/></a>
<a href="https://pepy.tech/project/webscout"><img alt="Downloads" src="https://static.pepy.tech/badge/webscout"></a>

Search for words, documents, images, videos, news, maps and text translation using the Google, DuckDuckGo.com, yep.com, phind.com, you.com, etc Also containes AI models and now can transcribe yt videos


## Table of Contents
- [webscout](#webscout)
  - [Table of Contents](#table-of-contents)
  - [Install](#install)
  - [CLI version](#cli-version)
  - [CLI version of webscout.AI](#cli-version-of-webscoutai)
  - [CLI to use LLM](#cli-to-use-llm)
  - [Regions](#regions)
  - [Transcriber](#transcriber)
  - [DeepWEBS: Advanced Web Searches](#deepwebs-advanced-web-searches)
    - [Activating DeepWEBS](#activating-deepwebs)
    - [Point to remember before using `DeepWEBS`](#point-to-remember-before-using-deepwebs)
    - [Usage Example](#usage-example)
  - [WEBS and AsyncWEBS classes](#webs-and-asyncwebs-classes)
  - [Exceptions](#exceptions)
  - [usage of webscout](#usage-of-webscout)
    - [1. `text()` - text search by DuckDuckGo.com and Yep.com](#1-text---text-search-by-duckduckgocom-and-yepcom)
    - [2. `answers()` - instant answers by DuckDuckGo.com and Yep.com](#2-answers---instant-answers-by-duckduckgocom-and-yepcom)
    - [3. `images()` - image search by DuckDuckGo.com and Yep.com](#3-images---image-search-by-duckduckgocom-and-yepcom)
    - [4. `videos()` - video search by DuckDuckGo.com](#4-videos---video-search-by-duckduckgocom)
    - [5. `news()` - news search by DuckDuckGo.com and yep.com](#5-news---news-search-by-duckduckgocom-and-yepcom)
    - [6. `maps()` - map search by DuckDuckGo.com and](#6-maps---map-search-by-duckduckgocom-and)
    - [7. `translate()` - translation by DuckDuckGo.com and Yep.com](#7-translate---translation-by-duckduckgocom-and-yepcom)
    - [8. `suggestions()` - suggestions by DuckDuckGo.com and Yep.com](#8-suggestions---suggestions-by-duckduckgocom-and-yepcom)
  - [usage of webscout.AI](#usage-of-webscoutai)
    - [1. `PhindSearch` - Search using Phind.com](#1-phindsearch---search-using-phindcom)
    - [2. `YepChat` - Chat with mistral 8x7b powered by yepchat](#2-yepchat---chat-with-mistral-8x7b-powered-by-yepchat)
    - [3. `You.com` - search with you.com](#3-youcom---search-with-youcom)
    - [4. `Gemini` - search with google gemini](#4-gemini---search-with-google-gemini)
  - [usage of image generator from Webscout.AI](#usage-of-image-generator-from-webscoutai)
    - [5. `Prodia` - make image using prodia](#5-prodia---make-image-using-prodia)
    - [6. `BlackBox` - Search/chat With BlackBox](#6-blackbox---searchchat-with-blackbox)
    - [7. `PERPLEXITY` - Search With PERPLEXITY](#7-perplexity---search-with-perplexity)
    - [8. `OpenGPT` - chat With OPENGPT](#8-opengpt---chat-with-opengpt)
    - [9. `KOBOLDIA` -](#9-koboldia--)
  - [usage of special .LLM file from webscout (webscout.LLM)](#usage-of-special-llm-file-from-webscout-webscoutllm)
    - [`LLM`](#llm)

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



## CLI version of webscout.AI
| Command | Description |
|-----------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `python -m webscout.AI phindsearch --prompt "your search query"` | CLI function to perform a search query using Webscout.AI's Phindsearch feature. |
| `python -m webscout.AI yepchat --message "your_message_here"` | CLI function to send a message using Webscout.AI's Yepchat feature. |
| `python -m webscout.AI youchat --prompt "your_prompt_here"` | CLI function to generate a response based on a prompt using Webscout.AI's Youchat feature. |
| `python -m webscout.AI gemini --message "tell me about gemma 7b"` | CLI function to get information about a specific topic using Webscout.AI's Gemini feature. |
| `python -m webscout.AI prodia --prompt "car"` | CLI function to generate content related to a prompt using Webscout.AI's Prodia feature. |
| `python -m webscout.AI blackboxai --prompt "Your prompt here"` | CLI function to perform a search using Webscout.AI's Blackbox search feature. |
| `python -m webscout.AI perplexity --prompt "Your prompt here"` | CLI function to perform a search using Webscout.AI's PERPLEXITY feature. |
| `python -m webscout.AI opengpt --prompt "Your prompt here"` | CLI function to perform a search using Webscout.AI's OPENGPT feature. |


## CLI to use LLM 
```python
python -m webscout.LLM model_name 
```
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
## WEBS and AsyncWEBS classes

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

# bypass curl-cffi NotImplementedError in windows https://curl-cffi.readthedocs.io/en/latest/faq/
if sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def get_words():
    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    resp = requests.get(word_site)
    words = resp.text.splitlines()
    return words

async def aget_results(word):
    async with AsyncWEBS(proxies=proxies) as WEBS:
        results = [r async for r in WEBS.text(word, max_results=None)]
        return results

async def main():
    words = get_words()
    shuffle(words)
    tasks = []
    for word in words[:10]:
        tasks.append(aget_results(word))
    results = await asyncio.gather(*tasks)
    print(f"Done")
    for r in chain.from_iterable(results):
        print(r)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
```
It is important to note that the WEBS and AsyncWEBS classes should always be used as a context manager (with statement).
This ensures proper resource management and cleanup, as the context manager will automatically handle opening and closing the HTTP client connection.

## Exceptions

Exceptions:
- `WebscoutE`: Raised when there is a generic exception during the API request.

## usage of webscout

### 1. `text()` - text search by DuckDuckGo.com and Yep.com

```python
from webscout import WEBS

# Text search for 'live free or die' using DuckDuckGo.com and Yep.com
with WEBS() as WEBS:
    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)

    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)
```

### 2. `answers()` - instant answers by DuckDuckGo.com and Yep.com

```python
from webscout import WEBS

# Instant answers for the query "sun" using DuckDuckGo.com and Yep.com
with WEBS() as WEBS:
    for r in WEBS.answers("sun"):
        print(r)
```

### 3. `images()` - image search by DuckDuckGo.com and Yep.com

```python
from webscout import WEBS

# Image search for the keyword 'butterfly' using DuckDuckGo.com and Yep.com
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

### 5. `news()` - news search by DuckDuckGo.com and yep.com

```python
from webscout import WEBS

# News search for the keyword 'holiday' using DuckDuckGo.com and yep.com
with WEBS() as WEBS:
    keywords = 'holiday'
    WEBS_news_gen = WEBS.news(
      keywords,
      region="wt-wt",
      safesearch="off",
      timelimit="m",
      max_results=20
    )
    for r in WEBS_news_gen:
        print(r)
```

### 6. `maps()` - map search by DuckDuckGo.com and

```python
from webscout import WEBS

# Map search for the keyword 'school' in 'anantnag' using DuckDuckGo.com
with WEBS() as WEBS:
    for r in WEBS.maps("school", place="anantnag", max_results=50):
        print(r)
```

### 7. `translate()` - translation by DuckDuckGo.com and Yep.com

```python
from webscout import WEBS

# Translation of the keyword 'school' to German ('hi') using DuckDuckGo.com and Yep.com
with WEBS() as WEBS:
    keywords = 'school'
    r = WEBS.translate(keywords, to="hi")
    print(r)
```

### 8. `suggestions()` - suggestions by DuckDuckGo.com and Yep.com

```python
from webscout import WEBS

# Suggestions for the keyword 'fly' using DuckDuckGo.com and Yep
with WEBS() as WEBS:
    for r in WEBS.suggestions("fly"):
        print(r)
```
## usage of webscout.AI

### 1. `PhindSearch` - Search using Phind.com 

```python
from webscout.AI import PhindSearch

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
Thanks To Divyansh Shukla for This code
```python
from webscout.AI import YepChat

def main():
    # Initialize the YepChat class with your message
    yep_chat = YepChat(message="who is pm of india")
    
    # Send the request and process the response
    response = yep_chat.send_request()
    processed_response = yep_chat.process_response(response)
    
    # Print the processed response
    print(processed_response)

if __name__ == "__main__":
    main()
```

### 3. `You.com` - search with you.com
```python
from webscout.AI import youChat

# Instantiate the youchat class
youChat = youChat()

while True:
    # Ask the user for a prompt
    prompt = input("💡 Enter a prompt (or type 'exit' to quit): ")
    
    # Exit condition
    if prompt.lower() == 'exit':
        break
    
    # Generate a completion based on the prompt
    try:
        completion = youChat.create(prompt)
        print("💬:", completion)
    except Exception as e:
        print("⚠️ An error occurred:", e)
```

### 4. `Gemini` - search with google gemini

```python
from webscout.AI import Gemini

# Create an instance of the Gemini class
gemini = Gemini()

# Use the chat method to send a message to the Gemini assistant
response = gemini.chat("Your message here")

# Print the response from the Gemini assistant
print(response)
```
##  usage of image generator from Webscout.AI
### 5. `Prodia` - make image using prodia
```python
from webscout.AI import Prodia

# Define a prompt for the image generation
prompt = "A beautiful sunset over the ocean"

# Use the prodia_cli method to generate an image based on the prompt
Prodia.prodia_cli(prompt)
```
### 6. `BlackBox` - Search/chat With BlackBox
```python
from webscout.AI import BLACKBOXAI
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

# Define a prompt to send to the AI
prompt = "Tell me about india"

# Use the 'ask' method to send the prompt and receive a response
response = ai.ask(prompt)

# Extract the text from the response
response_text = ai.get_message(response)

# Print the response text
print(response_text)
```
### 7. `PERPLEXITY` - Search With PERPLEXITY
```python
from webscout.AI import PERPLEXITY
# Create an instance of the PERPLEXITY class
perplexity = PERPLEXITY()

# Example usage:
prompt = "Explain the concept of recursion in simple terms."
response = perplexity.chat(prompt)
print(response)
```
### 8. `OpenGPT` - chat With OPENGPT
```python
from webscout.AI import OPENGPT

opengpt = OPENGPT(is_conversation=True, max_tokens=8000, timeout=30)
# This example sends a simple greeting and prints the response
prompt = "tell me about india"
response_str = opengpt.chat(prompt)
print(response_str)
```
### 9. `KOBOLDIA` - 
```python
from webscout.AI import KOBOLDAI

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

## usage of special .LLM file from webscout (webscout.LLM)

### `LLM`
```python
from webscout.LLM import LLM

def chat(model_name, system_message="You are Jarvis"):# system prompt
    AI = LLM(model_name, system_message)
    AI.chat()

if __name__ == "__main__":
    model_name = "mistralai/Mistral-7B-Instruct-v0.1" # name of the model you wish to use It supports ALL text generation models on deepinfra.com.
    chat(model_name)
```
