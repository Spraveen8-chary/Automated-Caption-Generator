import importlib.util
from abc import ABC, abstractmethod

from utils.transcription import TranscriptionService as GeminiTranscriptionService

class ProviderConfigurationError(ValueError):
    """Raised when the selected transcription provider cannot be built."""


class TranscriptionProvider(ABC):
    """Abstract transcription provider interface."""

    provider_name = 'base'

    @abstractmethod
    def transcribe(self, audio_path, language='en'):
        raise NotImplementedError

    def get_supported_languages(self):
        return {}


class GeminiTranscriptionProvider(TranscriptionProvider):
    """Adapter around the existing Gemini transcription implementation."""

    provider_name = 'gemini'

    def __init__(self, api_key):
        self._service = GeminiTranscriptionService(api_key)

    def transcribe(self, audio_path, language='en'):
        return self._service.transcribe(audio_path, language)

    def transcribe_with_retry(self, audio_path, language='en', max_retries=3):
        return self._service.transcribe_with_retry(audio_path, language, max_retries)

    def get_supported_languages(self):
        return self._service.get_supported_languages()


class WhisperTranscriptionProvider(TranscriptionProvider):
    """Transcribe audio with openai-whisper or faster-whisper."""

    provider_name = 'whisper'

    def __init__(self, model_name='base'):
        self.model_name = model_name or 'base'
        self._backend_name, self._backend = self._load_backend()
        self._model = None

    def _load_backend(self):
        if importlib.util.find_spec('whisper') is not None:
            import whisper

            return 'whisper', whisper

        if importlib.util.find_spec('faster_whisper') is not None:
            from faster_whisper import WhisperModel

            return 'faster_whisper', WhisperModel

        raise ProviderConfigurationError(
            'TRANSCRIPTION_PROVIDER=whisper requires the whisper or faster-whisper package'
        )

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        if self._backend_name == 'whisper':
            self._model = self._backend.load_model(self.model_name)
        else:
            self._model = self._backend(self.model_name, device='cpu', compute_type='int8')
        return self._model

    @staticmethod
    def _normalize_segments(segments):
        normalized = []
        for index, segment in enumerate(segments):
            start = float(getattr(segment, 'start', 0.0))
            end = float(getattr(segment, 'end', start))
            text = getattr(segment, 'text', '')
            normalized.append({
                'id': index,
                'start': start,
                'end': end,
                'duration': max(end - start, 0.0),
                'text': text.strip() if isinstance(text, str) else str(text),
            })
        return normalized

    def transcribe(self, audio_path, language='en'):
        model = self._ensure_model()

        if self._backend_name == 'whisper':
            result = model.transcribe(audio_path, language=language)
            segments = self._normalize_segments(result.get('segments', []))
            text = (result.get('text') or ' '.join(segment['text'] for segment in segments)).strip()
        else:
            segment_iter, info = model.transcribe(audio_path, language=language)
            segments = self._normalize_segments(segment_iter)
            text = ' '.join(segment['text'] for segment in segments).strip()
            if not text:
                text = getattr(info, 'language', language) or language

        duration = segments[-1]['end'] if segments else 0
        return {
            'text': text,
            'language': language,
            'duration': duration,
            'segments': segments,
        }


class AssemblyAITranscriptionProvider(TranscriptionProvider):
    """Transcribe audio through the AssemblyAI API."""

    provider_name = 'assemblyai'

    def __init__(self, api_key):
        if not api_key:
            raise ProviderConfigurationError(
                'ASSEMBLYAI_API_KEY is required when TRANSCRIPTION_PROVIDER=assemblyai'
            )

        if importlib.util.find_spec('assemblyai') is None:
            raise ProviderConfigurationError(
                'TRANSCRIPTION_PROVIDER=assemblyai requires the assemblyai package'
            )

        import assemblyai as aai

        aai.settings.api_key = api_key
        self._aai = aai

    @staticmethod
    def _normalize_segments(result):
        raw_segments = []
        for attr_name in ('utterances', 'segments'):
            value = getattr(result, attr_name, None)
            if value:
                raw_segments = list(value)
                break

        normalized = []
        for index, segment in enumerate(raw_segments):
            start = float(getattr(segment, 'start', 0.0))
            end = float(getattr(segment, 'end', start))
            text = getattr(segment, 'text', '')
            normalized.append({
                'id': index,
                'start': start,
                'end': end,
                'duration': max(end - start, 0.0),
                'text': text.strip() if isinstance(text, str) else str(text),
            })

        if normalized:
            return normalized

        transcript_text = getattr(result, 'text', '') or ''
        if transcript_text:
            return [{
                'id': 0,
                'start': 0.0,
                'end': float(getattr(result, 'audio_duration', 0.0) or 0.0),
                'duration': float(getattr(result, 'audio_duration', 0.0) or 0.0),
                'text': transcript_text.strip(),
            }]

        return []

    def transcribe(self, audio_path, language='en'):
        transcriber = self._aai.Transcriber()
        config = None
        config_cls = getattr(self._aai, 'TranscriptionConfig', None)
        if config_cls is not None:
            config_kwargs = {}
            if language:
                config_kwargs['language_code'] = language
            try:
                config = config_cls(**config_kwargs)
            except TypeError:
                config = None

        try:
            result = transcriber.transcribe(audio_path, config=config) if config is not None else transcriber.transcribe(audio_path)
        except TypeError:
            result = transcriber.transcribe(audio_path)

        if getattr(result, 'error', None):
            raise ProviderConfigurationError(getattr(result, 'error', 'AssemblyAI transcription failed'))

        segments = self._normalize_segments(result)
        text = getattr(result, 'text', '') or ' '.join(segment['text'] for segment in segments)
        duration = segments[-1]['end'] if segments else float(getattr(result, 'audio_duration', 0.0) or 0.0)
        return {
            'text': text.strip(),
            'language': language,
            'duration': duration,
            'segments': segments,
        }


def build_transcription_provider(provider_name, google_api_key=None, whisper_model='base', assemblyai_api_key=None):
    """Build the configured transcription provider."""
    normalized_name = (provider_name or 'gemini').strip().lower()

    if normalized_name == 'gemini':
        return GeminiTranscriptionProvider(google_api_key)

    if normalized_name == 'whisper':
        return WhisperTranscriptionProvider(model_name=whisper_model)

    if normalized_name == 'assemblyai':
        return AssemblyAITranscriptionProvider(assemblyai_api_key)

    raise ProviderConfigurationError(
        f"Invalid TRANSCRIPTION_PROVIDER '{normalized_name}'. Expected gemini, whisper, or assemblyai."
    )
