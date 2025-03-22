<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://t.me/PyscoutAI"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  <a href="https://www.instagram.com/oevortex/"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"></a>
  <a href="https://www.linkedin.com/in/oe-vortex-29a407265/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
</div>

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://youtube.com/@OEvortex">▶️ Vortex's YouTube Channel</a>
</div>
<div align="center">
  <a href="https://youtube.com/@devsdocode">▶️ Devs Do Code's YouTube Channel</a>
</div>
<div align="center">
  <a href="https://t.me/ANONYMOUS_56788">📢 Anonymous Coder's Telegram</a>
</div>

<p align="center">
  <strong>Webscout</strong> is the all-in-one search and AI toolkit you need.
  <br>
  Discover insights with Yep.com, DuckDuckGo, and Phind; access cutting-edge AI models; transcribe YouTube videos; generate temporary emails and phone numbers; perform text-to-speech conversions; and much more!
</p>

<div align="center">
  <img src="https://img.shields.io/badge/WebScout-API-blue?style=for-the-badge&logo=WebScout" alt="WebScout API Badge">
  <a href="#"><img src="https://img.shields.io/pypi/pyversions/webscout" alt="Python Version"></a>
  <a href="https://pepy.tech/project/webscout"><img src="https://static.pepy.tech/badge/webscout" alt="Downloads"></a>
</div>

---

## 🚀 Features

* **Comprehensive Search:** Leverage Google, DuckDuckGo for diverse search results.
* **AI Powerhouse:** Access and interact with various AI models, including OpenAI, Cohere, and more.
* **[YouTube Toolkit](webscout/Extra/YTToolkit):** Advanced YouTube video and transcript management with multi-language support, versatile downloading, and intelligent data extraction
* **[GitAPI](webscout/Extra/GitToolkit/gitapi):** Powerful GitHub data extraction toolkit for seamless repository and user information retrieval, featuring commit tracking, issue management, and comprehensive user analytics - all without authentication requirements for public data
* **Tempmail & Temp Number:** Generate temporary email addresses and phone numbers for enhanced privacy.
* **[Text-to-Speech (TTS)](webscout/Provider/TTS/README.md):** Convert text into natural-sounding speech using multiple AI-powered providers like ElevenLabs, StreamElements, and Voicepods.
* **GGUF Conversion & Quantization:** Convert and quantize Hugging Face models to GGUF format.
* **[SwiftCLI](webscout/swiftcli/Readme.md):** A powerful and elegant CLI framework that makes it easy to create beautiful command-line interfaces.
* **[LitPrinter](webscout/litprinter/Readme.md):** Provides beautiful, styled console output with rich formatting and colors
* **[LitLogger](webscout/litlogger/Readme.md):** Simplifies logging with customizable formats and color schemes
* **[LitAgent](webscout/litagent/Readme.md):** Powerful and modern user agent generator that keeps your requests fresh and undetectable
* **[Text-to-Image](webscout/Provider/TTI/README.md):** Generate high-quality images using a wide range of AI art providers
* **[Scout](webscout/scout/README.md):** Advanced web parsing and crawling library with intelligent HTML/XML parsing, web crawling, and Markdown conversion
* **[Awesome Prompts (Act)](webscout/Extra/Act.md):** A curated collection of system prompts designed to transform Webscout into specialized personas, enhancing its ability to assist with specific tasks. Simply prefix your request with the act name or index number to leverage these tailored capabilities.
* **[Weather Tool kit](webscout/Extra/weather.md)** Webscout provides tools to retrieve weather information.
* **[AIsearch](webscout/Provider/AISEARCH)** AI Search Providers offer powerful and flexible AI-powered search Search Engine

## ⚙️ Installation

```python
pip install -U webscout
```

## 🖥️ CLI Usage

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
| python -m webscout weather -k Text        | CLI function to get weather information for a location using Webscout.                          |



## ✉️ TempMail and VNEngine

```python
import json
import asyncio
from webscout import VNEngine
from webscout import TempMail

async def main():
    vn = VNEngine()
    countries = vn.get_online_countries()
    if countries:
        country = countries[0]['country']
        numbers = vn.get_country_numbers(country)
        if numbers:
            number = numbers[0]['full_number']
            inbox = vn.get_number_inbox(country, number)
            
            # Serialize inbox data to JSON string
            json_data = json.dumps(inbox, ensure_ascii=False, indent=4)
            
            # Print with UTF-8 encoding
            print(json_data)
    
    async with TempMail() as client:
        domains = await client.get_domains()
        print("Available Domains:", domains)
        email_response = await client.create_email(alias="testuser")
        print("Created Email:", email_response)
        messages = await client.get_messages(email_response.email)
        print("Messages:", messages)
        await client.delete_email(email_response.email, email_response.token)
        print("Email Deleted")

if __name__ == "__main__":
    asyncio.run(main())
```

...

### 🔍 `YepSearch` - Search using Yep.com

```python
from webscout import YepSearch

# Initialize YepSearch
yep = YepSearch(
    timeout=20,  # Optional: Set custom timeout
    proxies=None,  # Optional: Use proxies
    verify=True   # Optional: SSL verification
)

# Text Search
text_results = yep.text(
    keywords="artificial intelligence",
    region="all",           # Optional: Region for results
    safesearch="moderate",  # Optional: "on", "moderate", "off"
    max_results=10          # Optional: Limit number of results
)
print(text_results)

# Image Search
image_results = yep.images(
    keywords="nature photography",
    region="all",
    safesearch="moderate",
    max_results=10
)
print(image_results)


# Suggestions
suggestions = yep.suggestions("hist")
print(suggestions)
```

## 🔍 GoogleS (formerly DWEBS)

```python
from webscout import GoogleS
from rich import print
searcher = GoogleS()
results = searcher.search("HelpingAI-9B", max_results=20, extract_text=False, max_text_length=200)
for result in results:
    print(result)
```

## 🦆 WEBS and AsyncWEBS

The `WEBS` and `AsyncWEBS` classes are used to retrieve search results from DuckDuckGo.com.

To use the `AsyncWEBS` class, you can perform asynchronous operations using Python's `asyncio` library.

To initialize an instance of the `WEBS` or `AsyncWEBS` classes, you can provide the following optional arguments:

**Example - WEBS:**

```python
from webscout import WEBS

R = WEBS().text("python programming", max_results=5)
print(R)
```

**Example - AsyncWEBS:**

```python
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

**Important Note:** The `WEBS` and `AsyncWEBS` classes should always be used as a context manager (with statement). This ensures proper resource management and cleanup, as the context manager will automatically handle opening and closing the HTTP client connection.

## ⚠️ Exceptions

**Exceptions:**

* `WebscoutE`: Raised when there is a generic exception during the API request.

## 💻 Usage of WEBS

### 1. `text()` - Text Search by DuckDuckGo.com

```python
from webscout import WEBS

# Text search for 'live free or die' using DuckDuckGo.com 
with WEBS() as WEBS:
    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)

    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10):
        print(r)
```

### 2. `answers()` - Instant Answers by DuckDuckGo.com

```python
from webscout import WEBS

# Instant answers for the query "sun" using DuckDuckGo.com 
with WEBS() as WEBS:
    for r in WEBS.answers("sun"):
        print(r)
```

### 3. `images()` - Image Search by DuckDuckGo.com

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

### 4. `videos()` - Video Search by DuckDuckGo.com

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

### 5. `news()` - News Search by DuckDuckGo.com

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

### 6. `maps()` - Map Search by DuckDuckGo.com

```python
from webscout import WEBS

# Map search for the keyword 'school' in 'anantnag' using DuckDuckGo.com
with WEBS() as WEBS:
    for r in WEBS.maps("school", place="anantnag", max_results=50):
        print(r)
```

### 7. `translate()` - Translation by DuckDuckGo.com

```python
from webscout import WEBS

# Translation of the keyword 'school' to German ('hi') using DuckDuckGo.com
with WEBS() as WEBS:
    keywords = 'school'
    r = WEBS.translate(keywords, to="hi")
    print(r)
```

### 8. `suggestions()` - Suggestions by DuckDuckGo.com

```python
from webscout import WEBS

# Suggestions for the keyword 'fly' using DuckDuckGo.com
with WEBS() as WEBS:
    for r in WEBS.suggestions("fly"):
        print(r)
```

### 9. `weather()` - Weather Information by DuckDuckGo.com

```python
from webscout import WEBS

# Get weather information for a location using DuckDuckGo.com
with WEBS() as webs:
    weather_data = webs.weather("New York")
    print(weather_data)

```


#### 📜 List Available LLM Models

Retrieve a comprehensive list of all supported LLMs.

```python
from webscout import model
from rich import print

all_models = model.llm.list()
print("Available models:")
print(all_models)
```

#### 📊 LLM Model Summary

Obtain a summary of the available LLMs, including provider details.

```python
from webscout import model
from rich import print

summary = model.llm.summary()
print("Summary of models:")
print(summary)
```

#### 🔍 Provider-Specific LLM Models

Filter and display LLMs available from a specific provider.

```python
from webscout import model
from rich import print

provider_name = "PerplexityLabs"  # Example provider
available_models = model.llm.get(provider_name)

if isinstance(available_models, list):
    print(f"Available models for {provider_name}: {', '.join(available_models)}")
else:
    print(f"Available models for {provider_name}: {available_models}")
```

### TTS Voices

#### 🎤 List Available TTS Voices

Retrieve a comprehensive list of all supported TTS voices.

```python
from webscout import model
from rich import print

all_voices = model.tts.list()
print("Available TTS voices:")
print(all_voices)
```

#### 📊 TTS Voice Summary

Obtain a summary of the available TTS voices, including provider details.

```python
from webscout import model
from rich import print

summary = model.tts.summary()
print("Summary of TTS voices:")
print(summary)
```

#### 🔍 Provider-Specific TTS Voices

Filter and display TTS voices available from a specific provider.

```python
from webscout import model
from rich import print

provider_name = "ElevenlabsTTS"  # Example provider
available_voices = model.tts.get(provider_name)

if isinstance(available_voices, list):
    print(f"Available voices for {provider_name}: {', '.join(available_voices)}")
elif isinstance(available_voices, dict):
    print(f"Available voices for {provider_name}:")
    for voice_name, voice_id in available_voices.items():
        print(f"  - {voice_name}: {voice_id}")
else:
    print(f"Available voices for {provider_name}: {available_voices}")
```




### 💬 `Duckchat` - Chat with LLM

```python
from webscout import WEBS as w
R = w().chat("Who are you", model='gpt-4o-mini') # mixtral-8x7b, llama-3.1-70b, claude-3-haiku, gpt-4o-mini
print(R)
```

### 🔎 `PhindSearch` - Search using Phind.com

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

**Using phindv2:**

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

### ♊ `Gemini` - Search with Google Gemini

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

### 💬 `YEPCHAT`

```python
from webscout import YEPCHAT
ai = YEPCHAT()
response = ai.chat(input(">>> "))
for chunk in response:
    print(chunk, end="", flush=True)

```

### ⬛ `BlackBox` - Search/Chat with BlackBox

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


# Define a prompt to send to the AI
prompt = "Tell me about india"
# Use the 'chat' method to send the prompt and receive a response
r = ai.chat(prompt)
print(r)
```

### 🤖 `Meta AI` - Chat with Meta AI

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

### `KOBOLDAI`

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

### `Reka` - Chat with Reka

```python
from webscout import REKA

a = REKA(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```

### `Cohere` - Chat with Cohere

```python
from webscout import Cohere

a = Cohere(is_conversation=True, max_tokens=8000, timeout=30,api_key="")

prompt = "tell me about india"
response_str = a.chat(prompt)
print(response_str)
```

### `Deepinfra`

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

### `GROQ`

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

### `LLama 70b` - Chat with Meta's Llama 3 70b

```python

from webscout import LLAMA

llama = LLAMA()

r = llama.chat("What is the meaning of life?")
print(r)
```

### `AndiSearch`

```python
from webscout import AndiSearch
a = AndiSearch()
print(a.chat("HelpingAI-9B"))
```

### `LLAMA`, `C4ai`, `Venice`, `Copilot`, `HuggingFaceChat`, `TwoAI`, `HeckAI`, `AllenAI`, `PerplexityLabs`, `AkashGPT`, `DeepSeek`, `WiseCat`, `IBMGranite`, `QwenLM`, `ChatGPTGratis`, `TextPollinationsAI`, `GliderAI`, `Cohere`, `REKA`, `GROQ`, `AsyncGROQ`, `OPENAI`, `AsyncOPENAI`, `KOBOLDAI`, `AsyncKOBOLDAI`, `BLACKBOXAI`, `PhindSearch`, `GEMINI`, `DeepInfra`, `AI4Chat`, `Phindv2`, `OLLAMA`, `AndiSearch`, `PIZZAGPT`, `Sambanova`, `DARKAI`, `KOALA`, `Meta`, `AskMyAI`, `PiAI`, `Julius`, `YouChat`, `YEPCHAT`, `Cloudflare`, `TurboSeek`, `Editee`, `TeachAnything`, `AI21`, `Chatify`, `X0GPT`, `Cerebras`, `Lepton`, `GEMINIAPI`, `Cleeai`, `Elmo`, `Free2GPT`, `GPTWeb`, `Netwrck`, `LlamaTutor`, `PromptRefine`, `TutorAI`, `ChatGPTES`, `Bagoodex`, `AIMathGPT`, `GaurishCerebras`, `GeminiPro`, `LLMChat`, `Talkai`, `Llama3Mitril`, `Marcus`, `TypeGPT`, `Netwrck`, `MultiChatAI`, `JadveOpenAI`, `ChatGLM`, `NousHermes`, `FreeAIChat`, `ElectronHub`, `GithubChat`, `Flowith`, `SonusAI`, `UncovrAI`, `LabyrinthAI`, `WebSim`, `LambdaChat`, `ChatGPTClone`

Code is similar to other providers.

### `LLM`

```python
from webscout.LLM import LLM, VLM

# Chat with text
llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
response = llm.chat([{"role": "user", "content": "What's good?"}])

# Chat with images
vlm = VLM("cogvlm-grounding-generalist")
response = vlm.chat([{
    "role": "user",
    "content": [
        {"type": "image", "image_url": "cool_pic.jpg"},
        {"type": "text", "text": "What's in this image?"}
    ]
}])
```

## GGUF

Webscout provides tools to convert and quantize Hugging Face models into the GGUF format for use with offline LLMs.

**Example:**

```python
from webscout.Extra.gguf import ModelConverter
"""
Valid quantization methods:
"q2_k", "q3_k_l", "q3_k_m", "q3_k_s", 
"q4_0", "q4_1", "q4_k_m", "q4_k_s", 
"q5_0", "q5_1", "q5_k_m", "q5_k_s", 
"q6_k", "q8_0"
"""
# Create a converter instance
converter = ModelConverter(
    model_id="prithivMLmods/QWQ-500M",
    quantization_methods="q2_k"
)

# Run the conversion
converter.convert()
```


**Command Line Usage:**

* **GGUF Conversion:**

   ```bash
    python -m webscout.Extra.gguf convert -m "prithivMLmods/QWQ-500M" -q "q2_k"
   ```


**Note:**

* Replace `"your_username"` and `"your_hf_token"` with your actual Hugging Face credentials.
* The `model_path` in `autollama` is the Hugging Face model ID, and `gguf_file` is the GGUF file ID.

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://t.me/PyscoutAI"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  <a href="https://www.instagram.com/oevortex/"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"></a>
  <a href="https://www.linkedin.com/in/oe-vortex-29a407265/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
</div>

<div align="center">
  <!-- Replace `#` with your actual links -->
  <a href="https://youtube.com/@OEvortex">▶️ Vortex's YouTube Channel</a>
</div>
<div align="center">
  <a href="https://youtube.com/@devsdocode">▶️ Devs Do Code's YouTube Channel</a>
</div>
<div align="center">
  <a href="https://t.me/ANONYMOUS_56788">📢 Anonymous Coder's Telegram</a>
</div>

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to Webscout, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive messages.
4. Push your branch to your forked repository.
5. Submit a pull request to the main repository.

## 🙏 Acknowledgments

* All the amazing developers who have contributed to the project!
* The open-source community for their support and inspiration.

