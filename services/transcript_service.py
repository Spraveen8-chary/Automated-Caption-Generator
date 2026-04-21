import os
import logging

from config import Config
from repositories.processing_repository import ProcessingRepository
from repositories.transcript_repository import TranscriptRepository
from services.export_service import ExportService
from services.preview_service import PreviewService
from services.style_service import StyleService
from services.transcription_provider import ProviderConfigurationError, build_transcription_provider
from utils.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class TranscriptService:
    """Orchestrate video processing, transcription, styling, and export."""

    def __init__(
        self,
        upload_folder,
        api_key,
        output_folder=None,
        video_processor=None,
        transcription_provider=None,
        style_service=None,
        export_service=None,
        transcript_repository=None,
        processing_repository=None,
        preview_service=None,
    ):
        self.upload_folder = upload_folder
        self.output_folder = output_folder or upload_folder
        self.video_processor = video_processor or VideoProcessor(upload_folder)
        self.transcription_provider = transcription_provider
        self.transcription_provider_name = 'auto' if Config.TRANSCRIPTION_PROVIDER == 'gemini' else Config.TRANSCRIPTION_PROVIDER
        self.transcription_provider_api_key = api_key
        self.transcription_provider_whisper_model = Config.WHISPER_MODEL
        self.transcription_provider_assemblyai_api_key = Config.ASSEMBLYAI_API_KEY
        self._whisper_fallback_provider = None
        self.style_service = style_service or StyleService(gemini_api_key=Config.GOOGLE_API_KEY)
        self.export_service = export_service or ExportService(self.output_folder)
        self.transcript_repository = transcript_repository or TranscriptRepository()
        self.processing_repository = processing_repository or ProcessingRepository()
        self.preview_service = preview_service or PreviewService()
        self.free_user_video_limit = Config.FREE_USER_VIDEO_LIMIT
        self.max_target_languages_per_job = Config.MAX_TARGET_LANGUAGES_PER_JOB

    def _get_transcription_provider(self):
        if self.transcription_provider is None:
            self.transcription_provider = build_transcription_provider(
                provider_name=self.transcription_provider_name,
                google_api_key=self.transcription_provider_api_key,
                whisper_model=self.transcription_provider_whisper_model,
                assemblyai_api_key=self.transcription_provider_assemblyai_api_key,
            )
        return self.transcription_provider

    def _get_whisper_fallback_provider(self):
        if self._whisper_fallback_provider is None:
            self._whisper_fallback_provider = build_transcription_provider(
                provider_name='whisper',
                google_api_key=self.transcription_provider_api_key,
                whisper_model=self.transcription_provider_whisper_model,
                assemblyai_api_key=self.transcription_provider_assemblyai_api_key,
            )
        return self._whisper_fallback_provider

    def process_video(self, user, filename, original_filename=None, style=None, styles=None, languages=None, language='en'):
        original_filename = original_filename or filename
        selected_style = style or (styles[0] if styles else 'meme')
        target_languages = languages or ([language] if language else ['en'])
        if isinstance(target_languages, str):
            target_languages = [target_languages]
        deduped_languages = []
        seen_languages = set()
        for lang in target_languages:
            if not lang or lang in seen_languages:
                continue
            seen_languages.add(lang)
            deduped_languages.append(lang)
        target_languages = deduped_languages
        if not target_languages:
            target_languages = ['en']

        if len(target_languages) > self.max_target_languages_per_job:
            raise ValueError(
                f'You can select at most {self.max_target_languages_per_job} target languages per job.'
            )

        video_path = os.path.join(self.upload_folder, filename)
        if not os.path.exists(video_path):
            raise FileNotFoundError('Video file not found')

        existing_usage = self.processing_repository.has_processing_record(user.id, filename, language)
        if not existing_usage:
            if hasattr(user, 'can_process_video'):
                can_process = user.can_process_video()
            else:
                current_count = self.processing_repository.get_user_video_count(user.id)
                can_process = getattr(user, 'is_premium', False) or current_count < self.free_user_video_limit

            if not can_process:
                active_limit_getter = getattr(user, 'get_active_video_limit', None)
                active_limit = active_limit_getter() if callable(active_limit_getter) else self.free_user_video_limit
                active_limit = active_limit or self.free_user_video_limit
                raise PermissionError(
                    f'You have reached your processing limit ({active_limit} videos). Please upgrade or renew premium access.'
                )

        logger.info(
            "transcript.process.started",
            extra={
                'user_id': user.id,
                'source_filename': filename,
                'languages': target_languages,
                'style': selected_style,
            },
        )

        audio_path = None
        try:
            audio_path = self.video_processor.extract_audio(video_path)
            provider = self._get_transcription_provider()
            provider_name = getattr(provider, 'provider_name', 'whisper')

            if provider_name in {'whisper', 'assemblyai'}:
                processing_note = None
                if len(target_languages) > 1:
                    processing_note = (
                        f'{provider_name.title()} transcribes one detected-language output; '
                        'extra selected languages were ignored.'
                    )
                    logger.warning(
                        "transcript.multilanguage.not_supported",
                        extra={
                            'provider': provider_name,
                            'requested_languages': target_languages,
                            'user_id': user.id,
                            'source_filename': filename,
                        },
                    )

                transcript, provider_used = self._transcribe_language(audio_path, None, provider)
                detected_language = transcript.get('language') or target_languages[0] or 'en'
                target_languages = [detected_language]
                language_outputs = [{
                    'language_code': detected_language,
                    'transcript': transcript,
                    'provider_used': provider_used,
                }]
            else:
                language_outputs = []
                for target_language in target_languages:
                    transcript, provider_used = self._transcribe_language(audio_path, target_language, provider)
                    language_outputs.append({
                        'language_code': target_language,
                        'transcript': transcript,
                        'provider_used': provider_used,
                    })

            job_provider = self._summarize_job_provider(language_outputs, provider_name)

            job = self.transcript_repository.create_job(
                user_id=user.id,
                source_filename=filename,
                original_filename=original_filename,
                selected_style=selected_style,
                provider=job_provider,
                language_outputs=language_outputs,
            )

            serialized_job = self.transcript_repository.serialize_job(job)
            output_previews = []
            for output in serialized_job['outputs']:
                transcript = self.transcript_repository.rebuild_transcript(job, output['language_code'])
                formatted_captions = self.style_service.format(transcript, selected_style)
                output_previews.append({
                    'language_code': output['language_code'],
                    'language': output['language_code'],
                    'captions': formatted_captions[:5],
                    'total_captions': len(formatted_captions),
                })

            usage_count_getter = getattr(user, 'get_usage_count', None)
            remaining_count_getter = getattr(user, 'get_remaining_video_count', None)
            videos_processed = usage_count_getter() if callable(usage_count_getter) else self.processing_repository.get_user_video_count(user.id)
            videos_remaining = (
                remaining_count_getter()
                if callable(remaining_count_getter)
                else ('unlimited' if getattr(user, 'is_premium', False) else max(self.free_user_video_limit - videos_processed, 0))
            )
            cleanup_source_video = True

            logger.info(
                "transcript.process.completed",
                extra={
                    'user_id': user.id,
                    'job_id': job.id,
                    'source_filename': filename,
                    'languages': target_languages,
                    'style': selected_style,
                    'provider': job_provider,
                },
            )

            active_limit_getter = getattr(user, 'get_active_video_limit', None)
            plan_label_getter = getattr(user, 'get_plan_label', None)
            return {
                'success': True,
                'transcript_job_id': job.id,
                'transcript': self.transcript_repository.serialize_job(job),
                'outputs': serialized_job['outputs'],
                'style_previews': output_previews,
                'selected_style': selected_style,
                'selected_languages': target_languages,
                'primary_language': serialized_job['primary_language'],
                'videos_processed': videos_processed,
                'videos_remaining': videos_remaining,
                'active_video_limit': active_limit_getter() if callable(active_limit_getter) else (None if getattr(user, 'is_premium', False) else self.free_user_video_limit),
                'plan_label': plan_label_getter() if callable(plan_label_getter) else ('Premium' if getattr(user, 'is_premium', False) else 'Free'),
                'free_user_video_limit': self.free_user_video_limit,
                'transcription_provider': job_provider,
                'message': (
                    processing_note + ' '
                    if provider_name in {'whisper', 'assemblyai'} and len(deduped_languages) > 1
                    else ''
                ) + 'Transcript generated successfully',
            }
        finally:
            # Keep the uploaded source video available for caption burning and downloadable history.
            self.video_processor.cleanup_processing_artifacts(video_path, cleanup_source=False)

    def _transcribe_language(self, audio_path, language, provider=None):
        """Transcribe audio with the selected transcription backend."""
        active_provider = provider or self._get_transcription_provider()
        provider_name = getattr(active_provider, 'provider_name', 'whisper')

        try:
            transcript = active_provider.transcribe(audio_path, language)
            return transcript, provider_name
        except ProviderConfigurationError as error:
            if provider_name == 'whisper':
                raise

            logger.warning(
                "transcript.provider.fallback",
                extra={
                    'provider': provider_name,
                    'language': language,
                    'error': str(error),
                },
            )

            fallback_provider = self._get_whisper_fallback_provider()
            transcript = fallback_provider.transcribe(audio_path, language)
            return transcript, getattr(fallback_provider, 'provider_name', 'whisper')

    @staticmethod
    def _summarize_job_provider(language_outputs, default_provider):
        providers = [output.get('provider_used') for output in language_outputs if output.get('provider_used')]
        unique_providers = list(dict.fromkeys(providers))
        if len(unique_providers) == 1:
            return unique_providers[0]
        if len(unique_providers) > 1:
            return 'mixed'
        return default_provider

    def get_transcript_job(self, user, job_id):
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')
        return self.transcript_repository.serialize_job(job)

    def preview_styles(self, user, job_id, styles=None):
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')

        previews = []
        for output in job.outputs:
            transcript = self.transcript_repository.rebuild_transcript(job, output.language_code)
            formatted_captions = self.style_service.format(transcript, job.selected_style)
            previews.append({
                'language_code': output.language_code,
                'language': output.language_code,
                'captions': formatted_captions[:5],
                'total_captions': len(formatted_captions),
            })

        logger.info(
            "transcript.styles.previewed",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'style': job.selected_style,
                'languages': job.target_languages,
            },
        )
        return {
            'success': True,
            'transcript_job_id': job.id,
            'styles': previews,
            'selected_style': job.selected_style,
            'selected_languages': job.target_languages,
            'transcript': self.transcript_repository.serialize_job(job),
        }

    def update_transcript_job(self, user, job_id, segments, language_code=None):
        if not isinstance(segments, list) or not segments:
            raise ValueError('Segments are required')

        job = self.transcript_repository.update_segments(job_id, segments, user_id=user.id, language_code=language_code)
        if job is None:
            raise FileNotFoundError('Transcript not found')
        logger.info(
            "transcript.job.updated",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'language_code': language_code or job.primary_language,
                'segment_count': len(segments),
            },
        )
        return self.transcript_repository.serialize_job(job)

    def export_transcript(self, user, job_id, languages=None):
        job = self.transcript_repository.get_job(job_id, user_id=user.id)
        if job is None:
            raise FileNotFoundError('Transcript not found')

        selected_languages = languages or job.target_languages
        if isinstance(selected_languages, str):
            selected_languages = [selected_languages]
        selected_languages = [language for language in selected_languages if language]
        if not selected_languages:
            selected_languages = job.target_languages

        results = []

        logger.info(
            "transcript.export.started",
            extra={
                'user_id': user.id,
                'job_id': job.id,
                'style': job.selected_style,
                'languages': selected_languages,
            },
        )

        for language_code in selected_languages:
            transcript = self.transcript_repository.rebuild_transcript(job, language_code)
            captions = self.style_service.format(transcript, job.selected_style)
            export_data = self.export_service.export_srt(captions, job.source_filename, job.selected_style, language=language_code)
            burned_export = None
            if Config.ENABLE_BURNED_VIDEO:
                source_video_path = os.path.join(self.upload_folder, job.source_filename)
                burned_export = self.export_service.export_burned_video(
                    source_video_path=source_video_path,
                    srt_path=export_data['srt_path'],
                    source_filename=job.source_filename,
                    style=job.selected_style,
                    language=language_code,
                )
            output_record = self.transcript_repository.get_output(job.id, language_code=language_code, user_id=user.id)
            if output_record is not None:
                output_record.srt_filename = export_data['srt_filename']
                if burned_export is not None:
                    output_record.burned_video_filename = burned_export['burned_video_filename']
                output_record.status = 'exported'
                output_record.duration = transcript.get('duration', 0)

            existing_record = self._find_processing_record(user.id, job.source_filename, job.selected_style, language_code)
            if existing_record is None:
                self.processing_repository.create_record(
                    user_id=user.id,
                    filename=job.source_filename,
                    original_filename=job.original_filename,
                    style=job.selected_style,
                    language=language_code,
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
                'style': job.selected_style,
                'language': language_code,
                'srt_filename': export_data['srt_filename'],
                'burned_video_filename': burned_export['burned_video_filename'] if burned_export else None,
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
                'style': job.selected_style,
                'languages': selected_languages,
                'exports': len(results),
            },
        )

        usage_count_getter = getattr(user, 'get_usage_count', None)
        remaining_count_getter = getattr(user, 'get_remaining_video_count', None)
        videos_processed = usage_count_getter() if callable(usage_count_getter) else self.processing_repository.get_user_video_count(user.id)
        videos_remaining = (
            remaining_count_getter()
            if callable(remaining_count_getter)
            else ('unlimited' if getattr(user, 'is_premium', False) else max(self.free_user_video_limit - videos_processed, 0))
        )
        active_limit_getter = getattr(user, 'get_active_video_limit', None)
        plan_label_getter = getattr(user, 'get_plan_label', None)
        return {
            'success': True,
            'results': results,
            'transcript_job_id': job.id,
            'transcript': self.transcript_repository.serialize_job(job),
            'videos_processed': videos_processed,
            'videos_remaining': videos_remaining,
            'active_video_limit': active_limit_getter() if callable(active_limit_getter) else (None if getattr(user, 'is_premium', False) else self.free_user_video_limit),
            'plan_label': plan_label_getter() if callable(plan_label_getter) else ('Premium' if getattr(user, 'is_premium', False) else 'Free'),
            'free_user_video_limit': self.free_user_video_limit,
            'selected_style': job.selected_style,
            'selected_languages': selected_languages,
            'message': f'Captions exported successfully for {len(results)} languages',
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
