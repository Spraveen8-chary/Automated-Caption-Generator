from models import TranscriptJob, User, VideoProcessing, db


class ProcessingRepository:
    """Database access for processing history."""

    def create_record(
        self,
        user_id,
        filename,
        original_filename,
        style,
        language,
        srt_filename=None,
        duration=0,
        status='completed',
    ):
        record = VideoProcessing(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            style=style,
            language=language,
            srt_filename=srt_filename,
            duration=duration,
            status=status,
        )
        db.session.add(record)
        db.session.commit()
        return record

    def has_processing_record(self, user_id, filename, language):
        return TranscriptJob.query.filter_by(
            user_id=user_id,
            source_filename=filename,
        ).first() is not None

    def get_user_history(self, user_id):
        return VideoProcessing.query.filter_by(user_id=user_id).order_by(VideoProcessing.processed_at.desc()).all()

    def get_all_users(self):
        return User.query.order_by(User.created_at.desc()).all()

    def get_all_videos(self):
        return VideoProcessing.query.order_by(VideoProcessing.processed_at.desc()).all()

    def get_user_video_count(self, user_id):
        return TranscriptJob.query.filter_by(user_id=user_id).count()
