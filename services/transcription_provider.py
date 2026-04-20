from abc import ABC, abstractmethod

from utils.transcription import TranscriptionService as GeminiTranscriptionService


class TranscriptionProvider(ABC):
    """Abstract transcription provider interface."""

    @abstractmethod
    def transcribe(self, audio_path, language='en'):
        raise NotImplementedError

    def get_supported_languages(self):
        return {}


class GeminiTranscriptionProvider(TranscriptionProvider):
    """Adapter around the existing Gemini transcription implementation."""

    def __init__(self, api_key):
        self._service = GeminiTranscriptionService(api_key)

    def transcribe(self, audio_path, language='en'):
        return self._service.transcribe(audio_path, language)

    def transcribe_with_retry(self, audio_path, language='en', max_retries=3):
        return self._service.transcribe_with_retry(audio_path, language, max_retries)

    def get_supported_languages(self):
        return self._service.get_supported_languages()

