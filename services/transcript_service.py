import os
import logging

from repositories.processing_repository import ProcessingRepository
from repositories.transcript_repository import TranscriptRepository
from services.export_service import ExportService
from services.preview_service import PreviewService
from services.style_service import StyleService
from services.transcription_provider import GeminiTranscriptionProvider
from utils.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class TranscriptService:
    """Orchestrate video processing, transcription, styling, and export."""

    def __init__(
        self,
        upload_folder,
        api_key,
        video_processor=None,
        transcription_provider=None,
        style_service=None,
        export_service=None,
        transcript_repository=None,
        processing_repository=None,
        preview_service=None,
    ):
        self.upload_folder = upload_folder
        self.video_processor = video_processor or VideoProcessor(upload_folder)
        self.transcription_provider = transcription_provider or GeminiTranscriptionProvider(api_key)
        self.style_service = style_service or StyleService()
        self.export_service = export_service or ExportService(upload_folder)
        self.transcript_repository = transcript_repository or TranscriptRepository()
        self.processing_repository = processing_repository or ProcessingRepository()
        self.preview_service = preview_service or PreviewService()

    def process_video(self, user, filename, original_filename=None, styles=None, language='en'):
        original_filename = original_filename or filename
        styles = styles or ['meme']

        video_path = os.path.join(self.upload_folder, filename)
        if not os.path.exists(video_path):
            raise FileNotFoundError('Video file not found')

        existing_usage = self.processing_repository.has_processing_record(user.id, filename, language)
        if not existing_usage and not user.is_premium and self.processing_repository.get_user_video_count(user.id) >= 2:
            raise PermissionError('You have reached your free limit (2 videos). Please upgrade to premium.')

        logger.info(
            "transcript.process.started",
            extra={
                'user_id': user.id,
                'source_filename': filename,
                'language': language,
                'styles': styles,
            },
        )

        audio_path = None
        cleanup_source_video = False
        try:
            audio_path = self.video_processor.extract_audio(video_path)
            transcript = self.transcription_provider.transcribe(audio_path, language)
            job = self.transcript_repository.create_job(
                user_id=user.id,
                source_filename=filename,
                original_filename=original_filename,
                language=language,
                transcript=transcript,
                provider='gemini',
            )

            style_previews = {}
            for style in styles:
                formatted_captions = self.style_service.format(transcript, style)
                style_previews[style] = formatted_captions[:5]

            videos_processed = self.processing_repository.get_user_video_count(user.id)
            videos_remaining = 'unlimited' if user.is_premium else max(2 - videos_processed, 0)
            cleanup_source_video = True

            logger.info(
                "transcript.process.completed",
                extra={
                    'user_id': user.id,
                    'job_id': job.id,
                    'source_filename': filename,
                    'language': language,
                    'styles': styles,
                },
            )

            return {
                'success': True,
                'transcript_job_id': job.id,
                'transcript': self.transcript_repository.serialize_job(job),
                'style_previews': style_previews,
                'selected_styles': styles,
                'videos_processed': videos_processed,
                'videos_remaining': videos_remaining,
                'message': 'Transcript generated successfully',
            }
        finally:
            self.video_processor.cleanup_processing_artifacts(video_path, cleanup_source=cleanup_source_video)

    def get_transcript_job(self, user, job_id):
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')
        return self.transcript_repository.serialize_job(job)

    def preview_styles(self, user, job_id, styles=None):
        styles = styles or ['meme']
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')

        transcript = self.transcript_repository.rebuild_transcript(job)
        logger.info(
            "transcript.styles.previewed",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'styles': styles,
            },
        )
        return {
            'success': True,
            'transcript_job_id': job.id,
            'styles': self.style_service.preview_styles(transcript, styles),
            'selected_styles': styles,
            'transcript': self.transcript_repository.serialize_job(job),
        }

    def update_transcript_job(self, user, job_id, segments):
        if not isinstance(segments, list) or not segments:
            raise ValueError('Segments are required')

        job = self.transcript_repository.update_segments(job_id, segments, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')
        logger.info(
            "transcript.job.updated",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'segment_count': len(segments),
            },
        )
        return self.transcript_repository.serialize_job(job)

    def export_transcript(self, user, job_id, styles=None):
        styles = styles or ['meme']
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')

        transcript = self.transcript_repository.rebuild_transcript(job)
        style_map = self.style_service.format_for_styles(transcript, styles)
        results = []

        logger.info(
            "transcript.export.started",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'styles': styles,
            },
        )

        for style, captions in style_map.items():
            export_data = self.export_service.export_srt(captions, job.source_filename, style)

            existing_record = self._find_processing_record(user.id, job.source_filename, style, job.language)
            if existing_record is None:
                self.processing_repository.create_record(
                    user_id=user.id,
                    filename=job.source_filename,
                    original_filename=job.original_filename,
                    style=style,
                    language=job.language,
                    srt_filename=export_data['srt_filename'],
                    duration=transcript.get('duration', 0),
                    status='completed',
                )
            else:
                existing_record.srt_filename = export_data['srt_filename']
                existing_record.status = 'completed'
                existing_record.duration = transcript.get('duration', 0)
                from models import db

                db.session.commit()

            results.append({
                'style': style,
                'srt_filename': export_data['srt_filename'],
                'captions': captions[:10],
                'total_captions': len(captions),
            })

        job.status = 'exported'
        from models import db

        db.session.commit()

        logger.info(
            "transcript.export.completed",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'styles': styles,
                'exports': len(results),
            },
        )

        videos_processed = self.processing_repository.get_user_video_count(user.id)
        videos_remaining = 'unlimited' if user.is_premium else max(2 - videos_processed, 0)
        return {
            'success': True,
            'results': results,
            'transcript_job_id': job.id,
            'transcript': self.transcript_repository.serialize_job(job),
            'videos_processed': videos_processed,
            'videos_remaining': videos_remaining,
            'message': f'Captions exported successfully for {len(results)} styles',
        }

    def _find_processing_record(self, user_id, filename, style, language):
        from models import VideoProcessing

        return VideoProcessing.query.filter_by(
            user_id=user_id,
            filename=filename,
            style=style,
            language=language,
        ).first()

    def cleanup_uploaded_artifacts(self, filename):
        """Remove source and temporary audio files for an uploaded video."""
        video_path = os.path.join(self.upload_folder, filename)
        self.video_processor.cleanup_processing_artifacts(video_path)
