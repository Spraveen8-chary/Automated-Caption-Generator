import os
import tempfile
import unittest
from types import SimpleNamespace

from flask import Flask

from models import db, User, VideoProcessing
from repositories.processing_repository import ProcessingRepository
from repositories.transcript_repository import TranscriptRepository
from services.export_service import ExportService
from services.upload_service import UploadService
from services.style_service import StyleService
from services.transcript_service import TranscriptService
from utils.caption_formatter import CaptionFormatter


class FakeTranscriptionProvider:
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


class CoreServiceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='test-secret',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            UPLOAD_FOLDER=self.tempdir.name,
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

        export_service = ExportService(self.tempdir.name, caption_formatter=formatter)
        export_data = export_service.export_srt(meme_captions, 'clip.mp4', 'meme')

        self.assertTrue(os.path.exists(export_data['srt_path']))
        self.assertEqual(export_data['srt_filename'], 'clip_meme.srt')

    def test_upload_service_saves_file_and_logs_without_reserved_keys(self):
        upload_service = UploadService(self.tempdir.name, {'mp4', 'mov', 'avi'})
        file_storage = FakeUploadFile('demo clip.mp4')

        result = upload_service.save_uploaded_file(file_storage)

        self.assertTrue(result['filename'].endswith('.mp4'))
        self.assertTrue(os.path.exists(result['filepath']))
        self.assertEqual(result['original_filename'], 'demo_clip.mp4')

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
                language='en',
                transcript=transcript,
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
        export_service = ExportService(self.tempdir.name)
        service = TranscriptService(
            self.tempdir.name,
            api_key='test-key',
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
                styles=['meme', 'formal'],
                language='en',
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['selected_styles'], ['meme', 'formal'])
            self.assertFalse(os.path.exists(video_path))
            self.assertFalse(os.path.exists(os.path.join(self.tempdir.name, 'clip.mp3')))
            self.assertEqual(fake_provider.calls[0]['language'], 'en')
            self.assertEqual(len(transcript_repository.get_jobs_for_user(self.user_id)), 1)

            export_result = service.export_transcript(user, result['transcript_job_id'], styles=['meme', 'formal'])
            self.assertEqual(len(export_result['results']), 2)
            self.assertEqual(
                VideoProcessing.query.filter_by(user_id=self.user_id).count(),
                2,
            )
            self.assertTrue(os.path.exists(os.path.join(self.tempdir.name, 'clip_meme.srt')))
            self.assertTrue(os.path.exists(os.path.join(self.tempdir.name, 'clip_formal.srt')))


if __name__ == '__main__':
    unittest.main()
