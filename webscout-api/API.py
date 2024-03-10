import logging
from typing import Optional

from flask import Flask, jsonify, request
from webscout import WEBS

app = Flask(__name__)

TIMEOUT = 10
PROXY = None

@app.route('/api/search', methods=['GET'])
def search_text():
    query = request.args.get('q', '')
    max_results = request.args.get('max_results', 10, type=int)
    timelimit = request.args.get('timelimit', None)
    safesearch = request.args.get('safesearch', 'moderate')
    region = request.args.get('region', 'wt-wt')
    WEBS_instance = WEBS() # Instantiate WEBS without context manager
    results = []
    with WEBS() as webs:
        for result in enumerate(WEBS_instance.text(query, max_results=max_results, timelimit=timelimit, safesearch=safesearch, region=region)):
            results.append(result)

    return jsonify({'results': results})


@app.route('/api/images', methods=['GET'])
def search_images():
    query = request.args.get('q', '')
    max_results = request.args.get('max_results', 10, type=int)
    safesearch = request.args.get('safesearch', 'moderate')
    region = request.args.get('region', 'wt-wt')
    WEBS_instance = WEBS()
    results = []
    with WEBS() as webs:
        for result in enumerate(WEBS_instance.images(query, max_results=max_results, safesearch=safesearch, region=region)):
            results.append(result)

    return jsonify({'results': results})

@app.route('/api/videos', methods=['GET'])
def search_videos():
    query = request.args.get('q', '')
    max_results = request.args.get('max_results', 10, type=int)
    safesearch = request.args.get('safesearch', 'moderate')
    region = request.args.get('region', 'wt-wt')
    timelimit = request.args.get('timelimit', None)
    resolution = request.args.get('resolution', None)
    duration = request.args.get('duration', None)
    WEBS_instance = WEBS()
    results = []
    with WEBS() as webs:
        for result in enumerate(WEBS_instance.videos(query, max_results=max_results, safesearch=safesearch, region=region, timelimit=timelimit, resolution=resolution, duration=duration)):
            results.append(result)

    return jsonify({'results': results})

@app.route('/api/news', methods=['GET'])
def search_news():
    query = request.args.get('q', '')
    max_results = request.args.get('max_results', 10, type=int)
    safesearch = request.args.get('safesearch', 'moderate')
    region = request.args.get('region', 'wt-wt')
    timelimit = request.args.get('timelimit', None)
    WEBS_instance = WEBS()
    results = []
    with WEBS() as webs:
        for result in enumerate(WEBS_instance.news(query, max_results=max_results, safesearch=safesearch, region=region, timelimit=timelimit)):
            results.append(result)

    return jsonify({'results': results})

@app.route('/api/maps', methods=['GET'])
def search_maps():
    query = request.args.get('q', '')
    place = request.args.get('place', None)
    max_results = request.args.get('max_results', 10, type=int)
    WEBS_instance = WEBS()
    results = []
    with WEBS() as webs:
        for result in enumerate(WEBS_instance.maps(query, place=place, max_results=max_results)):
            results.append(result)

    return jsonify({'results': results})

@app.route('/api/translate', methods=['GET'])
def translate_text():
    query = request.args.get('q', '')
    to_lang = request.args.get('to', 'en')
    WEBS_instance = WEBS()
    with WEBS() as webs:
        translation = enumerate(WEBS_instance.translate(query, to=to_lang))

    return jsonify({'translation': translation})

@app.route('/api/suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter missing'})

    results = []
    try:
        with WEBS() as webs:
            for result in webs.suggestions(query):
                results.append(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'results': results})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'working'})

if __name__ == '__main__':
    app.run(debug=True)
