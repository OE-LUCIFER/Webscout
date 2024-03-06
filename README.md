Search for words, documents, images, videos, news, maps and text translation using the DuckDuckGo.com, yep.com, phind.com and you.com
Also containes AI models that you can use
**⚠️ Warning: use AsyncWEBS in asynchronous code**

## Table of Contents
- [Webscout API Server](#webscout-api-server)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Text Search](#text-search)
    - [Image Search](#image-search)
    - [Video Search](#video-search)
    - [News Search](#news-search)
    - [Map Search](#map-search)
    - [Translation](#translation)
    - [Suggestions](#suggestions)
    - [Health Check](#health-check)
  - [Response Format](#response-format)
  - [Error Handling](#error-handling)
  - [License](#license)
- [IN python projects](#in-python-projects)
  - [CLI version](#cli-version)
  - [CLI version of webscout.AI](#cli-version-of-webscoutai)
  - [CLI to use LLM](#cli-to-use-llm)
  - [Regions](#regions)
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
  - [usage of special .LLM file from webscout (webscout.LLM)](#usage-of-special-llm-file-from-webscout-webscoutllm)
    - [`LLM`](#llm)

## Install
```python
pip install -U webscout
```
# Webscout API Server

This is a Flask server that provides an API for performing various types of searches using the `webscout` Python package. The server supports text, answers, images, videos, news, maps, translation, and suggestions searches.

## Installation

1. Install the required dependencies:

```bash
pip install flask webscout
```

2. Clone or download the repository containing the server code.

## Usage

1. Run the server:

```bash
python server.py
```

This will start the Flask server at `http://localhost:5000`.

2. Use the API endpoints to perform searches. Here are the available endpoints:

### Text Search

`GET /api/search`

Parameters:
- `q` (required): The search query string.
- `max_results` (optional, default=10): The maximum number of results to return.
- `timelimit` (optional): The time limit for the search (e.g., 'd' for day, 'w' for week, 'm' for month, 'y' for year).
- `safesearch` (optional, default='moderate'): The safe search level ('on', 'moderate', or 'off').
- `region` (optional, default='wt-wt'): The region for the search (e.g., 'us-en', 'uk-en', 'ru-ru').

Example: `http://localhost:5000/api/search?q=python&max_results=20&timelimit=d&safesearch=off&region=us-en`


### Image Search

`GET /api/images`

Parameters:
- `q` (required): The search query string.
- `max_results` (optional, default=10): The maximum number of results to return.
- `safesearch` (optional, default='moderate'): The safe search level ('on', 'moderate', or 'off').
- `region` (optional, default='wt-wt'): The region for the search (e.g., 'us-en', 'uk-en', 'ru-ru').

Example: `http://localhost:5000/api/images?q=butterfly&max_results=15&safesearch=off&region=uk-en`

### Video Search

`GET /api/videos`

Parameters:
- `q` (required): The search query string.
- `max_results` (optional, default=10): The maximum number of results to return.
- `safesearch` (optional, default='moderate'): The safe search level ('on', 'moderate', or 'off').
- `region` (optional, default='wt-wt'): The region for the search (e.g., 'us-en', 'uk-en', 'ru-ru').
- `timelimit` (optional): The time limit for the search (e.g., 'd' for day, 'w' for week, 'm' for month).
- `duration` (optional): The duration of the videos ('short', 'medium', 'long').

Example: `http://localhost:5000/api/videos?q=tesla&max_results=20&safesearch=off&region=us-en&timelimit=m&duration=long`

### News Search

`GET /api/news`

Parameters:
- `q` (required): The search query string.
- `max_results` (optional, default=10): The maximum number of results to return.
- `safesearch` (optional, default='moderate'): The safe search level ('on', 'moderate', or 'off').
- `region` (optional, default='wt-wt'): The region for the search (e.g., 'us-en', 'uk-en', 'ru-ru').
- `timelimit` (optional): The time limit for the search (e.g., 'd' for day, 'w' for week, 'm' for month).

Example: `http://localhost:5000/api/news?q=sports&max_results=20&safesearch=on&region=uk-en&timelimit=d`

### Map Search

`GET /api/maps`

Parameters:
- `q` (required): The search query string.
- `place` (optional): The place for the search (e.g., 'New York City').
- `max_results` (optional, default=10): The maximum number of results to return.

Example: `http://localhost:5000/api/maps?q=restaurants&place=Anantnag&max_results=15`

### Translation

`GET /api/translate`

Parameters:
- `q` (required): The text to translate.
- `to` (optional, default='en'): The language to translate to (e.g., 'es', 'fr', 'hi').

Example: `http://localhost:5000/api/translate?q=hello&to=es`

### Suggestions

`GET /api/suggestions`

Parameters:
- `q` (required): The query string for suggestions.

Example: `http://localhost:5000/api/suggestions?q=python`

### Health Check

`GET /api/health`

This endpoint returns a simple JSON response indicating that the server is running and ready to accept requests.

Example: `http://localhost:5000/api/health`

## Response Format

All endpoints return JSON responses with the following format:

```json
{
    "results": [
        {...},
        {...},
        ...
    ]
}
```

The `results` key contains a list of search results, where each result is a dictionary containing the relevant information for that search type.

## Error Handling

If an error occurs during the search, the server will return a JSON response with an appropriate error message.

```json
{
    "error": "Error message"
}
```

## License

This project is licensed under the [HelpingAI Simplified Universal License](https://raw.githubusercontent.com/OE-LUCIFER/Webscout/main/LICENSE.md).
# IN python projects
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


| Command                                    | Description                                                                                            |
|--------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `python -m webscout.AI phindsearch --query "your_query_here"` | CLI function to perform a search query using Webscout.AI's Phindsearch feature.              |
| `python -m webscout.AI yepchat --message "your_message_here"`   | CLI function to send a message using Webscout.AI's Yepchat feature.                             |
| `python -m webscout.AI youchat --prompt "your_prompt_here"`     | CLI function to generate a response based on a prompt using Webscout.AI's Youchat feature.      |
| `python -m webscout.AI gemini --message "tell me about gemma 7b"` | CLI function to get information about a specific topic using Webscout.AI's Gemini feature.    |
| `python -m webscout.AI prodia --prompt "car"`                   | CLI function to generate content related to a prompt using Webscout.AI's Prodia feature.        |



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


## WEBS and AsyncWEBS classes

The WEBS and AsyncWEBS classes are used to retrieve search results from DuckDuckGo.com and yep.com periodically.
To use the AsyncWEBS class, you can perform asynchronous operations using Python's asyncio library.
To initialize an instance of the WEBS or AsyncWEBS classes, you can provide the following optional arguments:

Here is an example of initializing the WEBS class:
```python3
from webscout import WEBS

# Instantiating the WEBS class from webscout module
WEBS_instance = WEBS()

# Fetching text results for the query "python programming" with a maximum of 5 results
results = [result for result in WEBS_instance.text("python programming", max_results=5)]

# Displaying the obtained results
print(results)
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
Thanks to Empyros for PhindSearch function
```python
from webscout.AI import PhindSearch

query = 'Webscout pypi'

# Create an instance of WEBSAI with the query
WEBSAI = PhindSearch(query)

WEBSAI.search()
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
