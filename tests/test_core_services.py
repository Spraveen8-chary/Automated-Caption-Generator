import importlib
import os
import tempfile
import unittest
import sys
from datetime import datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask
from flask_login import LoginManager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import auth as auth_blueprint
from config import Config
from models import db, PaymentRequest, User, VideoProcessing, TranscriptJob
from repositories.processing_repository import ProcessingRepository
from repositories.transcript_repository import TranscriptRepository
from services.export_service import ExportService
from services.upload_service import UploadService
from services.style_service import StyleService
from services.transcription_provider import (
    AssemblyAITranscriptionProvider,
    ProviderConfigurationError,
    WhisperTranscriptionProvider,
    build_transcription_provider,
)
from services.transcript_service import TranscriptService
from utils.caption_formatter import CaptionFormatter


class FakeTranscriptionProvider:
    provider_name = 'fake-provider'

    def __init__(self, transcript):
        self.transcript = transcript
        self.calls = []

    def transcribe(self, audio_path, language='en'):
        self.calls.append({'audio_path': audio_path, 'language': language})
        return self.transcript


class FakeUploadFile:
    def __init__(self, filename, content=b'video'):
        self.filename = filename
        self.content = content

    def save(self, path):
        with open(path, 'wb') as handle:
            handle.write(self.content)


class FakeVideoProcessor:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.calls = []

    def extract_audio(self, video_path):
        audio_path = os.path.join(
            self.upload_folder,
            f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3",
        )
        with open(audio_path, 'w', encoding='utf-8') as handle:
            handle.write('audio')
        self.calls.append({'action': 'extract_audio', 'video_path': video_path, 'audio_path': audio_path})
        return audio_path

    def cleanup_processing_artifacts(self, video_path, cleanup_source=True):
        audio_path = os.path.join(
            self.upload_folder,
            f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3",
        )
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if cleanup_source and os.path.exists(video_path):
            os.remove(video_path)
        self.calls.append(
            {
                'action': 'cleanup_processing_artifacts',
                'video_path': video_path,
                'cleanup_source': cleanup_source,
            }
        )


class FakeExportService:
    def __init__(self, upload_folder):
        self.output_folder = upload_folder
        self.upload_folder = upload_folder
        self.calls = []

    @staticmethod
    def build_srt_filename(source_filename, style, language=None):
        base_name = source_filename.rsplit('.', 1)[0]
        if language:
            return f"{base_name}_{style}_{language}.srt"
        return f"{base_name}_{style}.srt"

    @staticmethod
    def build_burned_video_filename(source_filename, style, language=None):
        base_name = source_filename.rsplit('.', 1)[0]
        if language:
            return f"{base_name}_{style}_{language}_captions.mp4"
        return f"{base_name}_{style}_captions.mp4"

    def export_srt(self, captions, source_filename, style, language=None):
        srt_filename = self.build_srt_filename(source_filename, style, language=language)
        srt_path = os.path.join(self.output_folder, srt_filename)
        with open(srt_path, 'w', encoding='utf-8') as handle:
            handle.write('placeholder srt')
        self.calls.append({'action': 'export_srt', 'language': language, 'srt_path': srt_path})
        return {'srt_filename': srt_filename, 'srt_path': srt_path}

    def export_burned_video(self, source_video_path, srt_path, source_filename, style, language=None):
        burned_video_filename = self.build_burned_video_filename(source_filename, style, language=language)
        burned_video_path = os.path.join(self.output_folder, burned_video_filename)
        with open(burned_video_path, 'wb') as handle:
            handle.write(b'placeholder video')
        self.calls.append(
            {
                'action': 'export_burned_video',
                'source_video_path': source_video_path,
                'srt_path': srt_path,
                'language': language,
                'burned_video_path': burned_video_path,
            }
        )
        return {'burned_video_filename': burned_video_filename, 'burned_video_path': burned_video_path}


class CoreServiceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.outputdir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='test-secret',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            UPLOAD_FOLDER=self.tempdir.name,
            OUTPUT_FOLDER=self.outputdir.name,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            user = User(email='test@example.com', username='tester')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()
        self.outputdir.cleanup()

    def test_caption_formatter_and_export_service_write_srt(self):
        formatter = CaptionFormatter()
        transcript = {
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'hello world from caption generator'},
                {'start': 2.0, 'end': 4.0, 'text': 'another segment here'},
            ]
        }

        meme_captions = formatter.format(transcript, 'meme')
        formal_captions = formatter.format(transcript, 'formal')

        self.assertGreater(len(meme_captions), 1)
        self.assertEqual(meme_captions[0]['text'], 'HELLO WORLD FROM CAPTION')
        self.assertTrue(formal_captions[0]['text'].endswith('.'))

        export_service = ExportService(self.outputdir.name, caption_formatter=formatter)
        export_data = export_service.export_srt(meme_captions, 'clip.mp4', 'meme')

        self.assertTrue(os.path.exists(export_data['srt_path']))
        self.assertEqual(export_data['srt_filename'], 'clip_meme.srt')
        self.assertTrue(export_data['srt_path'].startswith(self.outputdir.name))

    def test_upload_service_saves_file_and_logs_without_reserved_keys(self):
        upload_service = UploadService(self.tempdir.name, {'mp4', 'mov', 'avi'})
        file_storage = FakeUploadFile('demo clip.mp4')

        result = upload_service.save_uploaded_file(file_storage)

        self.assertTrue(result['filename'].endswith('.mp4'))
        self.assertTrue(os.path.exists(result['filepath']))
        self.assertEqual(result['original_filename'], 'demo_clip.mp4')

    def test_build_transcription_provider_rejects_gemini(self):
        with self.assertRaises(ProviderConfigurationError):
            build_transcription_provider(
                provider_name='gemini',
                google_api_key='test-key',
                whisper_model='base',
                assemblyai_api_key='assembly-key',
            )

    def test_validate_app_config_rejects_invalid_provider(self):
        with patch.object(Config, 'TRANSCRIPTION_PROVIDER', 'invalid-provider'), patch.object(Config, 'FREE_USER_VIDEO_LIMIT', 2), patch.object(Config, 'MAX_TARGET_LANGUAGES_PER_JOB', 5):
            with self.assertRaises(ValueError):
                Config.validate_app_config()

    def test_config_reads_free_limit_from_environment(self):
        import config as config_module

        with patch.dict(
            os.environ,
            {
                'FREE_USER_VIDEO_LIMIT': '9',
                'MAX_TARGET_LANGUAGES_PER_JOB': '3',
            },
            clear=False,
        ):
            reloaded_config = importlib.reload(config_module)
            self.assertEqual(reloaded_config.Config.FREE_USER_VIDEO_LIMIT, 9)
            self.assertEqual(reloaded_config.Config.MAX_TARGET_LANGUAGES_PER_JOB, 3)

        importlib.reload(config_module)

    def test_transcript_service_reads_configured_free_limit(self):
        transcript = {'text': 'hello world', 'duration': 1.0, 'segments': []}
        fake_provider = FakeTranscriptionProvider(transcript)
        fake_video_processor = FakeVideoProcessor(self.tempdir.name)
        with patch.object(Config, 'FREE_USER_VIDEO_LIMIT', 7):
            service = TranscriptService(
                self.tempdir.name,
                api_key='test-key',
                video_processor=fake_video_processor,
                transcription_provider=fake_provider,
                transcript_repository=TranscriptRepository(),
                processing_repository=ProcessingRepository(),
            )

        self.assertEqual(service.free_user_video_limit, 7)

    def test_transcript_service_uses_configured_provider_when_not_injected(self):
        fake_provider = FakeTranscriptionProvider({'text': 'hello', 'duration': 1.0, 'segments': []})

        with patch.object(Config, 'TRANSCRIPTION_PROVIDER', 'whisper'), patch.object(Config, 'WHISPER_MODEL', 'small'), patch.object(Config, 'ASSEMBLYAI_API_KEY', 'assembly-key'), patch(
            'services.transcript_service.build_transcription_provider',
            return_value=fake_provider,
        ) as build_provider:
            service = TranscriptService(self.tempdir.name, api_key='google-key')
            resolved_provider = service._get_transcription_provider()

        build_provider.assert_called_once_with(
            provider_name='whisper',
            google_api_key='google-key',
            whisper_model='small',
            assemblyai_api_key='assembly-key',
        )
        self.assertIs(resolved_provider, fake_provider)

    def test_style_service_uses_gemini_for_caption_styles(self):
        transcript = {
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'hello world'},
            ]
        }

        class FakeGeminiResponse:
            text = '{"captions":[{"start":0.0,"end":2.0,"text":"HELLO WORLD"}]}'

        class FakeGeminiModels:
            def generate_content(self, model, contents):
                self.last_model = model
                self.last_contents = contents
                return FakeGeminiResponse()

        class FakeGeminiClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.models = FakeGeminiModels()

        with patch('services.style_service.genai.Client', FakeGeminiClient):
            service = StyleService(gemini_api_key='test-key', gemini_model='gemini-style-test')
            captions = service.format(transcript, 'formal')

        self.assertEqual(captions[0]['text'], 'HELLO WORLD')
        self.assertEqual(captions[0]['start'], 0.0)
        self.assertEqual(captions[0]['end'], 2.0)

    def test_user_can_process_video_uses_configured_limit(self):
        with patch.object(Config, 'FREE_USER_VIDEO_LIMIT', 1):
            with self.app.app_context():
                job = TranscriptJob(
                    user_id=self.user_id,
                    source_filename='clip.mp4',
                    original_filename='clip.mp4',
                    language='en',
                    provider='fake-provider',
                    transcript_text='hello world',
                    transcript_payload='{}',
                )
                db.session.add(job)
                db.session.commit()

                user = db.session.get(User, self.user_id)
                self.assertFalse(user.can_process_video())

    def test_pending_payment_request_does_not_unlock_premium_limit(self):
        with self.app.app_context():
            payment_request = PaymentRequest(
                user_id=self.user_id,
                amount=499,
                currency='INR',
                upi_id='9390425742@ybl',
                payee_name='Caption Generator',
                status='pending',
                approved_video_limit=50,
            )
            db.session.add(payment_request)
            db.session.commit()

            user = db.session.get(User, self.user_id)
            self.assertEqual(user.get_active_video_limit(), Config.FREE_USER_VIDEO_LIMIT)
            self.assertEqual(user.get_plan_label(), 'Free')

    def test_approved_payment_request_grants_fifty_video_limit(self):
        with self.app.app_context():
            payment_request = PaymentRequest(
                user_id=self.user_id,
                amount=499,
                currency='INR',
                upi_id='9390425742@ybl',
                payee_name='Caption Generator',
                status='approved',
                approved_video_limit=50,
                approved_at=datetime.utcnow(),
            )
            db.session.add(payment_request)
            db.session.commit()

            user = db.session.get(User, self.user_id)
            self.assertEqual(user.get_active_video_limit(), 50)
            self.assertIn('50 videos', user.get_plan_label())

    def test_premium_usage_count_resets_from_approval_time(self):
        with self.app.app_context():
            approved_at = datetime.utcnow()
            payment_request = PaymentRequest(
                user_id=self.user_id,
                amount=499,
                currency='INR',
                upi_id='9390425742@ybl',
                payee_name='Caption Generator',
                status='approved',
                approved_video_limit=50,
                approved_at=approved_at,
            )
            db.session.add(payment_request)

            before_job = TranscriptJob(
                user_id=self.user_id,
                source_filename='before.mp4',
                original_filename='before.mp4',
                language='en',
                provider='whisper',
                transcript_text='before',
                transcript_payload='{}',
                processed_at=approved_at - timedelta(days=1),
            )
            after_job = TranscriptJob(
                user_id=self.user_id,
                source_filename='after.mp4',
                original_filename='after.mp4',
                language='en',
                provider='whisper',
                transcript_text='after',
                transcript_payload='{}',
                processed_at=approved_at + timedelta(seconds=1),
            )
            db.session.add(before_job)
            db.session.add(after_job)
            db.session.commit()

            user = db.session.get(User, self.user_id)
            self.assertEqual(user.get_usage_count(), 1)
            self.assertEqual(user.get_remaining_video_count(), 49)

    def test_login_page_displays_configured_free_limit(self):
        project_root = os.path.dirname(os.path.dirname(__file__))
        app = Flask(__name__, template_folder=os.path.join(project_root, 'templates'))
        app.config.update(
            TESTING=True,
            SECRET_KEY='test-secret',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(app)
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.user_loader(lambda user_id: None)
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        with patch.object(Config, 'FREE_USER_VIDEO_LIMIT', 7):
            with app.app_context():
                client = app.test_client()
                response = client.get('/auth/login')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'7 Free Videos', response.data)

    def test_build_transcription_provider_uses_whisper_backend(self):
        fake_whisper_module = ModuleType('whisper')

        class FakeWhisperModel:
            def transcribe(self, audio_path, language='en'):
                return {
                    'text': 'hello world',
                    'segments': [
                        {'start': 0.0, 'end': 1.5, 'text': 'hello world'},
                    ],
                }

        fake_whisper_module.load_model = lambda model_name: FakeWhisperModel()

        with patch.dict(sys.modules, {'whisper': fake_whisper_module}), patch(
            'services.transcription_provider.importlib.util.find_spec',
            side_effect=lambda name: object() if name == 'whisper' else None,
        ):
            provider = build_transcription_provider(
                provider_name='whisper',
                google_api_key='unused',
                whisper_model='tiny',
                assemblyai_api_key='unused',
            )

            self.assertIsInstance(provider, WhisperTranscriptionProvider)
            result = provider.transcribe('audio.mp3', language='en')

        self.assertEqual(result['language'], 'en')
        self.assertEqual(result['segments'][0]['text'], 'hello world')
        self.assertEqual(result['text'], 'hello world')

    def test_build_transcription_provider_uses_assemblyai_backend(self):
        fake_assemblyai_module = ModuleType('assemblyai')
        fake_assemblyai_module.settings = SimpleNamespace(api_key=None)

        class FakeTranscriptionConfig:
            def __init__(self, language_code=None):
                self.language_code = language_code

        class FakeAssemblyAIResult:
            def __init__(self):
                self.text = 'bonjour'
                self.audio_duration = 2.25
                self.error = None
                self.segments = [
                    SimpleNamespace(start=0.0, end=2.25, text='bonjour'),
                ]

        class FakeTranscriber:
            def transcribe(self, audio_path, config=None):
                return FakeAssemblyAIResult()

        fake_assemblyai_module.TranscriptionConfig = FakeTranscriptionConfig
        fake_assemblyai_module.Transcriber = FakeTranscriber

        with patch.dict(sys.modules, {'assemblyai': fake_assemblyai_module}), patch(
            'services.transcription_provider.importlib.util.find_spec',
            side_effect=lambda name: object() if name == 'assemblyai' else None,
        ):
            provider = build_transcription_provider(
                provider_name='assemblyai',
                google_api_key='unused',
                whisper_model='base',
                assemblyai_api_key='assembly-key',
            )

            self.assertIsInstance(provider, AssemblyAITranscriptionProvider)
            result = provider.transcribe('audio.mp3', language='fr')

        self.assertEqual(result['language'], 'fr')
        self.assertEqual(result['segments'][0]['text'], 'bonjour')
        self.assertEqual(result['text'], 'bonjour')

    def test_transcript_repository_persists_and_updates_segments(self):
        repository = TranscriptRepository()
        transcript = {
            'text': 'hello world',
            'duration': 4.0,
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'hello'},
                {'start': 2.0, 'end': 4.0, 'text': 'world'},
            ],
        }

        with self.app.app_context():
            job = repository.create_job(
                user_id=self.user_id,
                source_filename='clip.mp4',
                original_filename='clip.mp4',
                selected_style='meme',
                provider='fake-provider',
                language_outputs=[{'language_code': 'en', 'transcript': transcript}],
            )

            self.assertEqual(len(job.segments), 2)
            serialized = repository.serialize_job(job)
            self.assertEqual(serialized['segments'][0]['text'], 'hello')

            updated_job = repository.update_segments(
                job.id,
                [
                    {'start': 0.0, 'end': 1.5, 'duration': 1.5, 'text': 'updated hello'},
                ],
                user_id=self.user_id,
            )

            self.assertEqual(updated_job.status, 'reviewed')
            self.assertEqual(len(updated_job.segments), 1)
            rebuilt = repository.rebuild_transcript(updated_job)
            self.assertEqual(rebuilt['segments'][0]['text'], 'updated hello')

    def test_transcript_service_process_and_export_cleans_artifacts(self):
        transcript = {
            'text': 'hello world',
            'duration': 4.0,
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'hello world'},
                {'start': 2.0, 'end': 4.0, 'text': 'again'},
            ],
        }
        fake_provider = FakeTranscriptionProvider(transcript)
        fake_video_processor = FakeVideoProcessor(self.tempdir.name)
        transcript_repository = TranscriptRepository()
        processing_repository = ProcessingRepository()
        style_service = StyleService()
        export_service = FakeExportService(self.outputdir.name)
        service = TranscriptService(
            self.tempdir.name,
            api_key='test-key',
            output_folder=self.outputdir.name,
            video_processor=fake_video_processor,
            transcription_provider=fake_provider,
            style_service=style_service,
            export_service=export_service,
            transcript_repository=transcript_repository,
            processing_repository=processing_repository,
        )

        video_path = os.path.join(self.tempdir.name, 'clip.mp4')
        with open(video_path, 'w', encoding='utf-8') as handle:
            handle.write('video')

        user = SimpleNamespace(id=self.user_id, is_premium=False)

        with self.app.app_context():
            result = service.process_video(
                user=user,
                filename='clip.mp4',
                original_filename='clip.mp4',
                style='meme',
                languages=['en', 'hi'],
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['selected_style'], 'meme')
            self.assertEqual(result['selected_languages'], ['en', 'hi'])
            self.assertEqual(len(result['outputs']), 2)
            self.assertTrue(os.path.exists(video_path))
            self.assertFalse(os.path.exists(os.path.join(self.tempdir.name, 'clip.mp3')))
            self.assertEqual([call['language'] for call in fake_provider.calls], ['en', 'hi'])
            self.assertEqual(len(transcript_repository.get_jobs_for_user(self.user_id)), 1)
            self.assertEqual(transcript_repository.get_jobs_for_user(self.user_id)[0].provider, 'fake-provider')
            self.assertEqual(transcript_repository.serialize_job(transcript_repository.get_jobs_for_user(self.user_id)[0])['outputs'][0]['language_code'], 'en')

            export_result = service.export_transcript(user, result['transcript_job_id'], languages=['en', 'hi'])
            self.assertEqual(len(export_result['results']), 2)
            self.assertTrue(all(item.get('burned_video_filename') for item in export_result['results']))
            self.assertEqual(
                VideoProcessing.query.filter_by(user_id=self.user_id).count(),
                2,
            )
            self.assertTrue(os.path.exists(os.path.join(self.outputdir.name, 'clip_meme_en.srt')))
            self.assertTrue(os.path.exists(os.path.join(self.outputdir.name, 'clip_meme_hi.srt')))
            self.assertTrue(os.path.exists(os.path.join(self.outputdir.name, 'clip_meme_en_captions.mp4')))
            self.assertTrue(os.path.exists(os.path.join(self.outputdir.name, 'clip_meme_hi_captions.mp4')))

    def test_export_service_burns_video_with_subtitles_filter(self):
        source_video_path = os.path.join(self.tempdir.name, 'clip.mp4')
        srt_path = os.path.join(self.tempdir.name, 'clip_meme_en.srt')
        burned_video_path = os.path.join(self.tempdir.name, 'clip_meme_en_captions.mp4')

        with open(source_video_path, 'wb') as handle:
            handle.write(b'video')
        with open(srt_path, 'w', encoding='utf-8') as handle:
            handle.write('1\n00:00:00,000 --> 00:00:01,000\nHELLO\n')

        fake_clip = MagicMock()

        with patch('services.export_service.VideoFileClip', return_value=fake_clip) as video_file_clip, patch.object(
            ExportService,
            '_escape_subtitles_path',
            return_value='C:/tmp/clip_meme_en.srt',
        ):
            export_service = ExportService(self.outputdir.name)
            result = export_service.export_burned_video(
                source_video_path=source_video_path,
                srt_path=srt_path,
                source_filename='clip.mp4',
                style='meme',
                language='en',
            )

        video_file_clip.assert_called_once_with(source_video_path)
        fake_clip.write_videofile.assert_called_once()
        write_args, write_kwargs = fake_clip.write_videofile.call_args
        self.assertEqual(write_args[0], os.path.join(self.outputdir.name, 'clip_meme_en_captions.mp4'))
        self.assertEqual(write_kwargs['ffmpeg_params'], ['-vf', "subtitles='C:/tmp/clip_meme_en.srt'"])
        self.assertEqual(result['burned_video_filename'], 'clip_meme_en_captions.mp4')
        self.assertEqual(result['burned_video_path'], os.path.join(self.outputdir.name, 'clip_meme_en_captions.mp4'))
        fake_clip.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
