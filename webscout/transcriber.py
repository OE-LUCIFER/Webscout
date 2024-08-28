import requests
import http.cookiejar as cookiejar
import json
from xml.etree import ElementTree
import re
import html.parser
from typing import List, Dict, Union, Optional

html_parser = html.parser.HTMLParser()


def unescape(string):
    return html.unescape(string)


WATCH_URL = 'https://www.youtube.com/watch?v={video_id}'


class TranscriptRetrievalError(Exception):
    """Base class for transcript retrieval errors."""

    def __init__(self, video_id, message):
        super().__init__(message.format(video_url=WATCH_URL.format(video_id=video_id)))
        self.video_id = video_id


class YouTubeRequestFailedError(TranscriptRetrievalError):
    """Raised when a request to YouTube fails."""

    def __init__(self, video_id, http_error):
        message = 'Request to YouTube failed: {reason}'
        super().__init__(video_id, message.format(reason=str(http_error)))


class VideoUnavailableError(TranscriptRetrievalError):
    """Raised when the video is unavailable."""

    def __init__(self, video_id):
        message = 'The video is no longer available'
        super().__init__(video_id, message)


class InvalidVideoIdError(TranscriptRetrievalError):
    """Raised when an invalid video ID is provided."""

    def __init__(self, video_id):
        message = (
            'You provided an invalid video id. Make sure you are using the video id and NOT the url!\n\n'
            'Do NOT run: `YTTranscriber.get_transcript("https://www.youtube.com/watch?v=1234")`\n'
            'Instead run: `YTTranscriber.get_transcript("1234")`'
        )
        super().__init__(video_id, message)


class TooManyRequestsError(TranscriptRetrievalError):
    """Raised when YouTube rate limits the requests."""

    def __init__(self, video_id):
        message = (
            'YouTube is receiving too many requests from this IP and now requires solving a captcha to continue. '
            'One of the following things can be done to work around this:\n\
            - Manually solve the captcha in a browser and export the cookie. '
            '- Use a different IP address\n\
            - Wait until the ban on your IP has been lifted'
        )
        super().__init__(video_id, message)


class TranscriptsDisabledError(TranscriptRetrievalError):
    """Raised when transcripts are disabled for the video."""

    def __init__(self, video_id):
        message = 'Subtitles are disabled for this video'
        super().__init__(video_id, message)


class NoTranscriptAvailableError(TranscriptRetrievalError):
    """Raised when no transcripts are available for the video."""

    def __init__(self, video_id):
        message = 'No transcripts are available for this video'
        super().__init__(video_id, message)


class NotTranslatableError(TranscriptRetrievalError):
    """Raised when the transcript is not translatable."""

    def __init__(self, video_id):
        message = 'The requested language is not translatable'
        super().__init__(video_id, message)


class TranslationLanguageNotAvailableError(TranscriptRetrievalError):
    """Raised when the requested translation language is not available."""

    def __init__(self, video_id):
        message = 'The requested translation language is not available'
        super().__init__(video_id, message)


class CookiePathInvalidError(TranscriptRetrievalError):
    """Raised when the cookie path is invalid."""

    def __init__(self, video_id):
        message = 'The provided cookie file was unable to be loaded'
        super().__init__(video_id, message)


class CookiesInvalidError(TranscriptRetrievalError):
    """Raised when the provided cookies are invalid."""

    def __init__(self, video_id):
        message = 'The cookies provided are not valid (may have expired)'
        super().__init__(video_id, message)


class FailedToCreateConsentCookieError(TranscriptRetrievalError):
    """Raised when consent cookie creation fails."""

    def __init__(self, video_id):
        message = 'Failed to automatically give consent to saving cookies'
        super().__init__(video_id, message)


class NoTranscriptFoundError(TranscriptRetrievalError):
    """Raised when no transcript is found for the requested language codes."""

    def __init__(self, video_id, requested_language_codes, transcript_data):
        message = (
            'No transcripts were found for any of the requested language codes: {requested_language_codes}\n\n'
            '{transcript_data}'
        )
        super().__init__(video_id, message.format(
            requested_language_codes=requested_language_codes,
            transcript_data=str(transcript_data)
        ))


class YTTranscriber:
    """
    Main class for retrieving YouTube transcripts.
    """

    @staticmethod
    def get_transcript(video_url: str, languages: Optional[str] = 'en',
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
        video_id = YTTranscriber._extract_video_id(video_url)

        with requests.Session() as http_client:
            if cookies:
                http_client.cookies = YTTranscriber._load_cookies(cookies, video_id)
            http_client.proxies = proxies if proxies else {}
            transcript_list_fetcher = TranscriptListFetcher(http_client)
            transcript_list = transcript_list_fetcher.fetch(video_id)

            if languages is None:  # Get auto-generated transcript
                return transcript_list.find_generated_transcript(['any']).fetch(
                    preserve_formatting=preserve_formatting)
            else:
                return transcript_list.find_transcript([languages]).fetch(preserve_formatting=preserve_formatting)

    @staticmethod
    def _extract_video_id(video_url: str) -> str:
        """Extracts the video ID from different YouTube URL formats."""
        if 'youtube.com/watch?v=' in video_url:
            video_id = video_url.split('youtube.com/watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_url:
            video_id = video_url.split('youtu.be/')[1].split('?')[0]
        else:
            raise InvalidVideoIdError(video_url)
        return video_id

    @staticmethod
    def _load_cookies(cookies: str, video_id: str) -> cookiejar.MozillaCookieJar:
        """Loads cookies from a file."""
        try:
            cookie_jar = cookiejar.MozillaCookieJar()
            cookie_jar.load(cookies)
            if not cookie_jar:
                raise CookiesInvalidError(video_id)
            return cookie_jar
        except:
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
        return unescape(_raise_http_errors(response, video_id).text)


class TranscriptList:
    """Represents a list of available transcripts."""

    def __init__(self, video_id, manually_created_transcripts, generated_transcripts, translation_languages):
        """
        The constructor is only for internal use. Use the static build method instead.

        :param video_id: the id of the video this TranscriptList is for
        :type video_id: str
        :param manually_created_transcripts: dict mapping language codes to the manually created transcripts
        :type manually_created_transcripts: dict[str, Transcript]
        :param generated_transcripts: dict mapping language codes to the generated transcripts
        :type generated_transcripts: dict[str, Transcript]
        :param translation_languages: list of languages which can be used for translatable languages
        :type translation_languages: list[dict[str, str]]
        """
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
    """Represents a single transcript."""

    def __init__(self, http_client, video_id, url, language, language_code, is_generated, translation_languages):
        """
        You probably don't want to initialize this directly. Usually you'll access Transcript objects using a
        TranscriptList.

        :param http_client: http client which is used to make the transcript retrieving http calls
        :type http_client: requests.Session
        :param video_id: the id of the video this TranscriptList is for
        :type video_id: str
        :param url: the url which needs to be called to fetch the transcript
        :param language: the name of the language this transcript uses
        :param language_code:
        :param is_generated:
        :param translation_languages:
        """
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
        """
        Loads the actual transcript data.
        :param preserve_formatting: whether to keep select HTML text formatting
        :type preserve_formatting: bool
        :return: a list of dictionaries containing the 'text', 'start' and 'duration' keys
        :rtype [{'text': str, 'start': float, 'end': float}]:
        """
        response = self._http_client.get(self._url, headers={'Accept-Language': 'en-US'})
        return TranscriptParser(preserve_formatting=preserve_formatting).parse(
            _raise_http_errors(response, self.video_id).text,
        )

    def __str__(self):
        return '{language_code} ("{language}"){translation_description}'.format(
            language=self.language,
            language_code=self.language_code,
            translation_description='[TRANSLATABLE]' if self.is_translatable else ''
        )

    @property
    def is_translatable(self):
        return len(self.translation_languages) > 0

    def translate(self, language_code):
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
    """Parses the transcript data from XML."""
    _FORMATTING_TAGS = [
        'strong',  # important
        'em',  # emphasized
        'b',  # bold
        'i',  # italic
        'mark',  # marked
        'small',  # smaller
        'del',  # deleted
        'ins',  # inserted
        'sub',  # subscript
        'sup',  # superscript
    ]

    def __init__(self, preserve_formatting=False):
        self._html_regex = self._get_html_regex(preserve_formatting)

    def _get_html_regex(self, preserve_formatting):
        if preserve_formatting:
            formats_regex = '|'.join(self._FORMATTING_TAGS)
            formats_regex = r'<\/?(?!\/?(' + formats_regex + r')\b).*?\b>'
            html_regex = re.compile(formats_regex, re.IGNORECASE)
        else:
            html_regex = re.compile(r'<[^>]*>', re.IGNORECASE)
        return html_regex

    def parse(self, plain_data):
        return [
            {
                'text': re.sub(self._html_regex, '', unescape(xml_element.text)),
                'start': float(xml_element.attrib['start']),
                'duration': float(xml_element.attrib.get('dur', '0.0')),
            }
            for xml_element in ElementTree.fromstring(plain_data)
            if xml_element.text is not None
        ]


def _raise_http_errors(response, video_id):
    try:
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as error:
        raise YouTubeRequestFailedError(video_id, error) 

if __name__ == "__main__":
    from rich import print
    video_url = input("Enter the YouTube video URL: ") 
    transcript = YTTranscriber.get_transcript(video_url, languages=None) 
    print(transcript)