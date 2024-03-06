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
