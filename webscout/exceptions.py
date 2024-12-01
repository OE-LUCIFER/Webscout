class WebscoutE(Exception):
    """Base exception class for search."""


class APIConnectionError(Exception):
    """Raised when there are connection issues with an API."""
    pass


class RatelimitE(Exception):
    """Raised for rate limit exceeded errors during API requests."""


class ConversationLimitException(Exception):
    """Raised for conversation limit exceeded errors during API requests."""
    pass


class TimeoutE(Exception):
    """Raised for timeout errors during API requests."""


class FailedToGenerateResponseError(Exception):
    """Provider failed to fetch response"""


class AllProvidersFailure(Exception):
    """None of the providers generated response successfully"""
    pass


class FacebookInvalidCredentialsException(Exception):
    pass


class FacebookRegionBlocked(Exception):
    pass


class ModelUnloadedException(Exception):
    pass


class TranscriptRetrievalError(WebscoutE):
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
        message = 'The provided cookie path is invalid'
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