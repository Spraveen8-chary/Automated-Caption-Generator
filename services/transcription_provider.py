import importlib.util
import time
from abc import ABC, abstractmethod

import requests

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
    def _read_field(segment, field_name, default=None):
        if isinstance(segment, dict):
            return segment.get(field_name, default)
        return getattr(segment, field_name, default)

    @classmethod
    def _normalize_segments(cls, segments):
        normalized = []
        for index, segment in enumerate(segments):
            start = float(cls._read_field(segment, 'start', 0.0))
            end = float(cls._read_field(segment, 'end', start))
            text = cls._read_field(segment, 'text', '')
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
        requested_language = (language or '').strip().lower() if isinstance(language, str) else language
        auto_detect_language = not requested_language or requested_language == 'auto'

        if self._backend_name == 'whisper':
            transcribe_kwargs = {'fp16': False}
            if not auto_detect_language:
                transcribe_kwargs['language'] = language
            try:
                result = model.transcribe(audio_path, **transcribe_kwargs)
            except TypeError:
                transcribe_kwargs.pop('fp16', None)
                try:
                    result = model.transcribe(audio_path, **transcribe_kwargs)
                except TypeError:
                    if auto_detect_language:
                        result = model.transcribe(audio_path)
                    else:
                        result = model.transcribe(audio_path, language=language)
            segments = self._normalize_segments(result.get('segments', []))
            text = (result.get('text') or ' '.join(segment['text'] for segment in segments)).strip()
            detected_language = result.get('language') or language or 'en'
        else:
            if auto_detect_language:
                segment_iter, info = model.transcribe(audio_path)
            else:
                segment_iter, info = model.transcribe(audio_path, language=language)
            segments = self._normalize_segments(segment_iter)
            text = ' '.join(segment['text'] for segment in segments).strip()
            if not text:
                text = getattr(info, 'language', language) or language
            detected_language = getattr(info, 'language', None) or language or 'en'

        duration = segments[-1]['end'] if segments else 0
        return {
            'text': text,
            'language': detected_language,
            'duration': duration,
            'segments': segments,
        }


class AssemblyAITranscriptionProvider(TranscriptionProvider):
    """Transcribe audio through the AssemblyAI API."""

    provider_name = 'assemblyai'
    base_url = 'https://api.assemblyai.com'

    def __init__(self, api_key):
        if not api_key:
            raise ProviderConfigurationError(
                'ASSEMBLYAI_API_KEY is required when TRANSCRIPTION_PROVIDER=assemblyai'
            )

        self.api_key = api_key
        self._mode = 'http'
        self._aai = None

        if importlib.util.find_spec('assemblyai') is not None:
            try:
                import assemblyai as aai

                aai.settings.api_key = api_key
                self._aai = aai
                self._mode = 'sdk'
            except Exception:
                self._aai = None
                self._mode = 'http'

    @staticmethod
    def _read_field(segment, field_name, default=None):
        if isinstance(segment, dict):
            return segment.get(field_name, default)
        return getattr(segment, field_name, default)

    @classmethod
    def _normalize_segments(cls, result):
        raw_segments = []
        for attr_name in ('utterances', 'segments'):
            value = cls._read_field(result, attr_name, None)
            if value:
                raw_segments = list(value)
                break

        normalized = []
        for index, segment in enumerate(raw_segments):
            start = float(cls._read_field(segment, 'start', 0.0))
            end = float(cls._read_field(segment, 'end', start))
            text = cls._read_field(segment, 'text', '')
            normalized.append({
                'id': index,
                'start': start,
                'end': end,
                'duration': max(end - start, 0.0),
                'text': text.strip() if isinstance(text, str) else str(text),
            })

        if normalized:
            return normalized

        transcript_text = cls._read_field(result, 'text', '') or ''
        if transcript_text:
            return [{
                'id': 0,
                'start': 0.0,
                'end': float(cls._read_field(result, 'audio_duration', 0.0) or 0.0),
                'duration': float(cls._read_field(result, 'audio_duration', 0.0) or 0.0),
                'text': transcript_text.strip(),
            }]

        return []

    def _http_headers(self):
        return {
            'authorization': self.api_key,
        }

    @staticmethod
    def _response_error(response, fallback_message):
        details = fallback_message
        try:
            payload = response.json()
            if isinstance(payload, dict):
                details = payload.get('error') or payload.get('message') or fallback_message
        except ValueError:
            body = (response.text or '').strip()
            if body:
                details = body

        raise ProviderConfigurationError(
            f"AssemblyAI request failed ({getattr(response, 'status_code', 'unknown')}): {details}"
        )

    @staticmethod
    def _response_ok(response):
        ok = getattr(response, 'ok', None)
        if ok is not None:
            return bool(ok)

        status_code = getattr(response, 'status_code', None)
        if status_code is None:
            return True
        return 200 <= int(status_code) < 300

    def _upload_audio(self, audio_path):
        with open(audio_path, 'rb') as audio_file:
            response = requests.post(
                f'{self.base_url}/v2/upload',
                headers=self._http_headers(),
                data=audio_file,
                timeout=120,
            )
        if not self._response_ok(response):
            self._response_error(response, 'AssemblyAI upload failed')
        payload = response.json()
        upload_url = payload.get('upload_url')
        if not upload_url:
            raise ProviderConfigurationError('AssemblyAI upload did not return an upload_url')
        return upload_url

    def _create_transcript(self, audio_url):
        data = {
            'audio_url': audio_url,
            'language_detection': True,
            'speech_models': ['universal-2'],
        }

        response = requests.post(
            f'{self.base_url}/v2/transcript',
            headers=self._http_headers(),
            json=data,
            timeout=120,
        )
        if not self._response_ok(response):
            self._response_error(response, 'AssemblyAI transcript creation failed')
        payload = response.json()
        transcript_id = payload.get('id')
        if not transcript_id:
            raise ProviderConfigurationError('AssemblyAI did not return a transcript id')
        return transcript_id

    def _poll_transcript(self, transcript_id):
        polling_endpoint = f'{self.base_url}/v2/transcript/{transcript_id}'
        while True:
            response = requests.get(
                polling_endpoint,
                headers=self._http_headers(),
                timeout=120,
            )
            if not self._response_ok(response):
                self._response_error(response, 'AssemblyAI transcript polling failed')
            payload = response.json()
            status = payload.get('status')
            if status == 'completed':
                return payload
            if status == 'error':
                raise ProviderConfigurationError(payload.get('error') or 'AssemblyAI transcription failed')
            time.sleep(3)

    def transcribe(self, audio_path, language='en'):
        try:
            if self._mode == 'sdk':
                transcriber = self._aai.Transcriber()
                try:
                    result = transcriber.transcribe(audio_path)
                except TypeError:
                    result = transcriber.transcribe(audio_path, config=None)

                if self._read_field(result, 'error', None):
                    raise ProviderConfigurationError(self._read_field(result, 'error', 'AssemblyAI transcription failed'))

            else:
                upload_url = self._upload_audio(audio_path)
                transcript_id = self._create_transcript(upload_url)
                result = self._poll_transcript(transcript_id)
        except requests.RequestException as error:
            raise ProviderConfigurationError(f'AssemblyAI request failed: {error}') from error

        segments = self._normalize_segments(result)
        text = self._read_field(result, 'text', '') or ' '.join(segment['text'] for segment in segments)
        duration = segments[-1]['end'] if segments else float(self._read_field(result, 'audio_duration', 0.0) or 0.0)
        detected_language = (
            self._read_field(result, 'language_code', None)
            or self._read_field(result, 'language', None)
            or language
            or 'en'
        )
        return {
            'text': text.strip(),
            'language': detected_language,
            'duration': duration,
            'segments': segments,
        }


def build_transcription_provider(provider_name, google_api_key=None, whisper_model='base', assemblyai_api_key=None):
    """Build the configured transcription provider."""
    normalized_name = (provider_name or 'auto').strip().lower()

    if normalized_name in {'', 'auto'}:
        if assemblyai_api_key:
            return AssemblyAITranscriptionProvider(assemblyai_api_key)

        if importlib.util.find_spec('whisper') is not None or importlib.util.find_spec('faster_whisper') is not None:
            return WhisperTranscriptionProvider(model_name=whisper_model)

        raise ProviderConfigurationError(
            'No transcription backend is available. Install whisper or faster-whisper, '
            'or configure TRANSCRIPTION_PROVIDER=assemblyai with the AssemblyAI SDK installed and an API key.'
        )

    if normalized_name == 'gemini':
        raise ProviderConfigurationError(
            'Gemini is reserved for style generation. Use whisper or assemblyai for transcription.'
        )

    if normalized_name == 'whisper':
        return WhisperTranscriptionProvider(model_name=whisper_model)

    if normalized_name == 'assemblyai':
        return AssemblyAITranscriptionProvider(assemblyai_api_key)

    raise ProviderConfigurationError(
        f"Invalid TRANSCRIPTION_PROVIDER '{normalized_name}'. Expected auto, whisper, or assemblyai."
    )
