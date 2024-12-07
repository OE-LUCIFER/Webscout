"""Wassup fam! 🔥 This module is your go-to for getting those YouTube transcripts! 

>>> from webscout import YTTranscriber
>>> transcript = YTTranscriber.get_transcript('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
>>> print(transcript)
{'text': 'Never gonna give you up', 'start': 0.0, 'duration': 4.5}

Built different by @HelpingAI 👑
"""

import requests  # For making those HTTP requests like a boss 🌐
import http.cookiejar as cookiejar  # Handling cookies and stuff 🍪
import json  # JSON parsing - keeping it clean! 📝
from xml.etree import ElementTree  # XML parsing magic ✨
import re  # Regex for pattern matching 🎯
import html  # HTML stuff made easy 💪
from typing import List, Dict, Union, Optional  # Type hints for that clean code 💯
from functools import lru_cache  # Cache that data for speed! ⚡
from concurrent.futures import ThreadPoolExecutor  # Parallel processing gang 🚀
import asyncio  # Async/await swag 😎
from webscout.exceptions import *  # All our custom exceptions 🛠️

WATCH_URL = 'https://www.youtube.com/watch?v={video_id}'
MAX_WORKERS = 4  # Keeping it optimal fam! 💪

class YTTranscriber:
    """Your boy for getting those YouTube transcripts! 🎥
    
    >>> transcript = YTTranscriber.get_transcript('https://youtu.be/dQw4w9WgXcQ')
    >>> print(transcript[0]['text'])
    'Never gonna give you up'
    """
    
    _session = None
    _executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    
    @classmethod
    def _get_session(cls):
        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
        return cls._session

    @classmethod
    @lru_cache(maxsize=100)
    def get_transcript(cls, video_url: str, languages: Optional[str] = 'en',
                      proxies: Dict[str, str] = None,
                      cookies: str = None,
                      preserve_formatting: bool = False) -> List[Dict[str, Union[str, float]]]:
        """
        Retrieves the transcript for a given YouTube video URL.

        Args:
            video_url (str): YouTube video URL (supports various formats).
            languages (str, optional): Language code for the transcript.
                                    If None, fetches the auto-generated transcript.
                                    Defaults to 'en'.
            proxies (Dict[str, str], optional): Proxies to use for the request. Defaults to None.
            cookies (str, optional): Path to the cookie file. Defaults to None.
            preserve_formatting (bool, optional): Whether to preserve formatting tags. Defaults to False.

        Returns:
            List[Dict[str, Union[str, float]]]: A list of dictionaries, each containing:
                - 'text': The transcribed text.
                - 'start': The start time of the text segment (in seconds).
                - 'duration': The duration of the text segment (in seconds).

        Raises:
            TranscriptRetrievalError: If there's an error retrieving the transcript.
        """
        video_id = cls._extract_video_id(video_url)
        http_client = cls._get_session()
        
        if proxies:
            http_client.proxies.update(proxies)
        
        if cookies:
            cls._load_cookies(cookies, video_id)

        transcript_list = TranscriptListFetcher(http_client).fetch(video_id)
        language_codes = [languages] if languages else None
        transcript = transcript_list.find_transcript(language_codes)
        
        return transcript.fetch(preserve_formatting)

    @staticmethod
    def _extract_video_id(video_url: str) -> str:
        """Extracts the video ID from different YouTube URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        if re.match(r'^[0-9A-Za-z_-]{11}$', video_url):
            return video_url
            
        raise InvalidVideoIdError(video_url)

    @staticmethod
    def _load_cookies(cookies: str, video_id: str) -> None:
        """Loads cookies from a file."""
        try:
            cj = cookiejar.MozillaCookieJar(cookies)
            cj.load()
            return cj
        except (cookiejar.LoadError, FileNotFoundError):
            raise CookiePathInvalidError(video_id)

class TranscriptListFetcher:
    """Fetches the list of transcripts for a YouTube video."""

    def __init__(self, http_client: requests.Session):
        """Initializes TranscriptListFetcher."""
        self._http_client = http_client

    def fetch(self, video_id: str):
        """Fetches and returns a TranscriptList."""
        return TranscriptList.build(
            self._http_client,
            video_id,
            self._extract_captions_json(self._fetch_video_html(video_id), video_id),
        )

    def _extract_captions_json(self, html: str, video_id: str) -> dict:
        """Extracts the captions JSON data from the video's HTML."""
        splitted_html = html.split('"captions":')

        if len(splitted_html) <= 1:
            if video_id.startswith('http://') or video_id.startswith('https://'):
                raise InvalidVideoIdError(video_id)
            if 'class="g-recaptcha"' in html:
                raise TooManyRequestsError(video_id)
            if '"playabilityStatus":' not in html:
                raise VideoUnavailableError(video_id)

            raise TranscriptsDisabledError(video_id)

        captions_json = json.loads(
            splitted_html[1].split(',"videoDetails')[0].replace('\n', '')
        ).get('playerCaptionsTracklistRenderer')
        if captions_json is None:
            raise TranscriptsDisabledError(video_id)

        if 'captionTracks' not in captions_json:
            raise TranscriptsDisabledError(video_id)

        return captions_json

    def _create_consent_cookie(self, html, video_id):
        match = re.search('name="v" value="(.*?)"', html)
        if match is None:
            raise FailedToCreateConsentCookieError(video_id)
        self._http_client.cookies.set('CONSENT', 'YES+' + match.group(1), domain='.youtube.com')

    def _fetch_video_html(self, video_id):
        html = self._fetch_html(video_id)
        if 'action="https://consent.youtube.com/s"' in html:
            self._create_consent_cookie(html, video_id)
            html = self._fetch_html(video_id)
            if 'action="https://consent.youtube.com/s"' in html:
                raise FailedToCreateConsentCookieError(video_id)
        return html

    def _fetch_html(self, video_id):
        response = self._http_client.get(WATCH_URL.format(video_id=video_id), headers={'Accept-Language': 'en-US'})
        return html.unescape(_raise_http_errors(response, video_id).text)


class TranscriptList:
    """Yo fam! This class is all about managing those YouTube transcript lists! 🎯
    
    >>> transcript_list = TranscriptList.build(http_client, video_id, captions_json)
    >>> transcript = transcript_list.find_transcript(['en'])
    >>> print(transcript)
    en ("English")[TRANSLATABLE]
    """

    def __init__(self, video_id, manually_created_transcripts, generated_transcripts, translation_languages):
        """Init that transcript list with all the good stuff! 💯"""
        self.video_id = video_id
        self._manually_created_transcripts = manually_created_transcripts
        self._generated_transcripts = generated_transcripts
        self._translation_languages = translation_languages

    @staticmethod
    def build(http_client, video_id, captions_json):
        """
        Factory method for TranscriptList.

        :param http_client: http client which is used to make the transcript retrieving http calls
        :type http_client: requests.Session
        :param video_id: the id of the video this TranscriptList is for
        :type video_id: str
        :param captions_json: the JSON parsed from the YouTube pages static HTML
        :type captions_json: dict
        :return: the created TranscriptList
        :rtype TranscriptList:
        """
        translation_languages = [
            {
                'language': translation_language['languageName']['simpleText'],
                'language_code': translation_language['languageCode'],
            } for translation_language in captions_json.get('translationLanguages', [])
        ]

        manually_created_transcripts = {}
        generated_transcripts = {}

        for caption in captions_json['captionTracks']:
            if caption.get('kind', '') == 'asr':
                transcript_dict = generated_transcripts
            else:
                transcript_dict = manually_created_transcripts

            transcript_dict[caption['languageCode']] = Transcript(
                http_client,
                video_id,
                caption['baseUrl'],
                caption['name']['simpleText'],
                caption['languageCode'],
                caption.get('kind', '') == 'asr',
                translation_languages if caption.get('isTranslatable', False) else [],
            )

        return TranscriptList(
            video_id,
            manually_created_transcripts,
            generated_transcripts,
            translation_languages,
        )

    def __iter__(self):
        return iter(list(self._manually_created_transcripts.values()) + list(self._generated_transcripts.values()))

    def find_transcript(self, language_codes):
        """
        Finds a transcript for a given language code. If no language is provided, it will
        return the auto-generated transcript.

        :param language_codes: A list of language codes in a descending priority. 
        :type languages: list[str]
        :return: the found Transcript
        :rtype Transcript:
        :raises: NoTranscriptFound
        """
        if 'any' in language_codes:
            for transcript in self:
                return transcript
        return self._find_transcript(language_codes, [self._manually_created_transcripts, self._generated_transcripts])

    def find_generated_transcript(self, language_codes):
        """
        Finds an automatically generated transcript for a given language code.

        :param language_codes: A list of language codes in a descending priority. For example, if this is set to
        ['de', 'en'] it will first try to fetch the german transcript (de) and then fetch the english transcript (en) if
        it fails to do so.
        :type languages: list[str]
        :return: the found Transcript
        :rtype Transcript:
        :raises: NoTranscriptFound
        """
        if 'any' in language_codes:
            for transcript in self:
                if transcript.is_generated:
                    return transcript
        return self._find_transcript(language_codes, [self._generated_transcripts])

    def find_manually_created_transcript(self, language_codes):
        """
        Finds a manually created transcript for a given language code.

        :param language_codes: A list of language codes in a descending priority. For example, if this is set to
        ['de', 'en'] it will first try to fetch the german transcript (de) and then fetch the english transcript (en) if
        it fails to do so.
        :type languages: list[str]
        :return: the found Transcript
        :rtype Transcript:
        :raises: NoTranscriptFound
        """
        return self._find_transcript(language_codes, [self._manually_created_transcripts])

    def _find_transcript(self, language_codes, transcript_dicts):
        for language_code in language_codes:
            for transcript_dict in transcript_dicts:
                if language_code in transcript_dict:
                    return transcript_dict[language_code]

        raise NoTranscriptFoundError(
            self.video_id,
            language_codes,
            self
        )

    def __str__(self):
        return (
            'For this video ({video_id}) transcripts are available in the following languages:\n\n'
            '(MANUALLY CREATED)\n'
            '{available_manually_created_transcript_languages}\n\n'
            '(GENERATED)\n'
            '{available_generated_transcripts}\n\n'
            '(TRANSLATION LANGUAGES)\n'
            '{available_translation_languages}'
        ).format(
            video_id=self.video_id,
            available_manually_created_transcript_languages=self._get_language_description(
                str(transcript) for transcript in self._manually_created_transcripts.values()
            ),
            available_generated_transcripts=self._get_language_description(
                str(transcript) for transcript in self._generated_transcripts.values()
            ),
            available_translation_languages=self._get_language_description(
                '{language_code} ("{language}")'.format(
                    language=translation_language['language'],
                    language_code=translation_language['language_code'],
                ) for translation_language in self._translation_languages
            )
        )

    def _get_language_description(self, transcript_strings):
        description = '\n'.join(' - {transcript}'.format(transcript=transcript) for transcript in transcript_strings)
        return description if description else 'None'


class Transcript:
    """Your personal transcript handler! 🎭
    
    >>> transcript = transcript_list.find_transcript(['en'])
    >>> print(transcript.language)
    'English'
    >>> if transcript.is_translatable:
    ...     es_transcript = transcript.translate('es')
    ...     print(es_transcript.language)
    'Spanish'
    """

    def __init__(self, http_client, video_id, url, language, language_code, is_generated, translation_languages):
        """Initialize with all the goodies! 🎁"""
        self._http_client = http_client
        self.video_id = video_id
        self._url = url
        self.language = language
        self.language_code = language_code
        self.is_generated = is_generated
        self.translation_languages = translation_languages
        self._translation_languages_dict = {
            translation_language['language_code']: translation_language['language']
            for translation_language in translation_languages
        }

    def fetch(self, preserve_formatting=False):
        """Get that transcript data! 🎯
        
        Args:
            preserve_formatting (bool): Keep HTML formatting? Default is nah fam.
            
        Returns:
            list: That sweet transcript data with text, start time, and duration! 📝
        """
        response = self._http_client.get(self._url, headers={'Accept-Language': 'en-US'})
        return TranscriptParser(preserve_formatting=preserve_formatting).parse(
            _raise_http_errors(response, self.video_id).text,
        )

    def __str__(self):
        """String representation looking clean! 💅"""
        return '{language_code} ("{language}"){translation_description}'.format(
            language=self.language,
            language_code=self.language_code,
            translation_description='[TRANSLATABLE]' if self.is_translatable else ''
        )

    @property
    def is_translatable(self):
        """Can we translate this? 🌍"""
        return len(self.translation_languages) > 0

    def translate(self, language_code):
        """Translate to another language! 🌎
        
        Args:
            language_code (str): Which language you want fam?
            
        Returns:
            Transcript: A fresh transcript in your requested language! 🔄
            
        Raises:
            NotTranslatableError: If we can't translate this one 😢
            TranslationLanguageNotAvailableError: If that language isn't available 🚫
        """
        if not self.is_translatable:
            raise NotTranslatableError(self.video_id)

        if language_code not in self._translation_languages_dict:
            raise TranslationLanguageNotAvailableError(self.video_id)

        return Transcript(
            self._http_client,
            self.video_id,
            '{url}&tlang={language_code}'.format(url=self._url, language_code=language_code),
            self._translation_languages_dict[language_code],
            language_code,
            True,
            [],
        )


class TranscriptParser:
    """Parsing those transcripts like a pro! 🎯
    
    >>> parser = TranscriptParser(preserve_formatting=True)
    >>> data = parser.parse(xml_data)
    >>> print(data[0])
    {'text': 'Never gonna give you up', 'start': 0.0, 'duration': 4.5}
    """
    
    _FORMATTING_TAGS = [
        'strong',  # For that extra emphasis 💪
        'em',      # When you need that italic swag 🎨
        'b',       # Bold and beautiful 💯
        'i',       # More italic vibes ✨
        'mark',    # Highlight that text 🌟
        'small',   # Keep it lowkey 🤫
        'del',     # Strike it out ⚡
        'ins',     # Insert new stuff 🆕
        'sub',     # Subscript gang 📉
        'sup',     # Superscript squad 📈
    ]

    def __init__(self, preserve_formatting=False):
        """Get ready to parse with style! 🎨"""
        self._html_regex = self._get_html_regex(preserve_formatting)

    def _get_html_regex(self, preserve_formatting):
        """Get that regex pattern ready! 🎯"""
        if preserve_formatting:
            formats_regex = '|'.join(self._FORMATTING_TAGS)
            formats_regex = r'<\/?(?!\/?(' + formats_regex + r')\b).*?\b>'
            html_regex = re.compile(formats_regex, re.IGNORECASE)
        else:
            html_regex = re.compile(r'<[^>]*>', re.IGNORECASE)
        return html_regex

    def parse(self, plain_data):
        """Parse that XML data into something beautiful! ✨"""
        return [
            {
                'text': re.sub(self._html_regex, '', html.unescape(xml_element.text)),
                'start': float(xml_element.attrib['start']),
                'duration': float(xml_element.attrib.get('dur', '0.0')),
            }
            for xml_element in ElementTree.fromstring(plain_data)
            if xml_element.text is not None
        ]


def _raise_http_errors(response, video_id):
    """Handle those HTTP errors with style! 🛠️"""
    try:
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as error:
        raise YouTubeRequestFailedError(video_id, error)


if __name__ == "__main__":
    # Let's get this party started! 🎉
    from rich import print
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    transcript = YTTranscriber.get_transcript(video_url, languages=None)
    print("Here's what we got! 🔥")
    print(transcript)