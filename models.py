import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    videos = db.relationship('VideoProcessing', backref='user', lazy=True, cascade='all, delete-orphan')
    transcript_jobs = db.relationship('TranscriptJob', backref='user', lazy=True, cascade='all, delete-orphan')
    payment_requests = db.relationship('PaymentRequest', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_video_count(self):
        """Get number of processed transcripts for usage limits"""
        return TranscriptJob.query.filter_by(user_id=self.id).count()

    def _get_latest_approved_payment_request(self):
        return (
            PaymentRequest.query.filter_by(user_id=self.id, status='approved')
            .order_by(PaymentRequest.approved_at.desc().nullslast(), PaymentRequest.created_at.desc())
            .first()
        )

    def get_usage_count(self):
        """Get the usage count for the current billing or free-usage window."""
        latest_approved_request = self._get_latest_approved_payment_request()
        if latest_approved_request is not None and latest_approved_request.approved_at is not None:
            return TranscriptJob.query.filter(
                TranscriptJob.user_id == self.id,
                TranscriptJob.processed_at >= latest_approved_request.approved_at,
            ).count()

        return self.get_video_count()

    def get_active_video_limit(self):
        """Return the current processing limit for the user."""
        if self.is_admin:
            return None

        latest_approved_request = self._get_latest_approved_payment_request()
        if latest_approved_request is not None:
            return latest_approved_request.approved_video_limit

        if self.is_premium:
            return None

        return Config.FREE_USER_VIDEO_LIMIT

    def get_remaining_video_count(self):
        """Return how many videos the user can still process."""
        limit = self.get_active_video_limit()
        if limit is None:
            return 'unlimited'
        return max(limit - self.get_usage_count(), 0)

    def get_plan_label(self):
        """Return a short label for the current account tier."""
        if self.is_admin:
            return 'Admin'

        latest_approved_request = self._get_latest_approved_payment_request()
        if latest_approved_request is not None:
            return f'Premium ({latest_approved_request.approved_video_limit} videos)'

        if self.is_premium:
            return 'Premium'

        return 'Free'
    
    def can_process_video(self):
        """Check if user can process more videos"""
        limit = self.get_active_video_limit()
        if limit is None:
            return True
        return self.get_usage_count() < limit
    
    def __repr__(self):
        return f'<User {self.username}>'


class VideoProcessing(db.Model):
    """Track video processing history"""
    __tablename__ = 'video_processing'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    srt_filename = db.Column(db.String(200))
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Float)
    status = db.Column(db.String(20), default='completed')
    
    def __repr__(self):
        return f'<VideoProcessing {self.filename}>'


class TranscriptJob(db.Model):
    """Persist a transcript and its parsed segments."""

    __tablename__ = 'transcript_jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    source_filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    provider = db.Column(db.String(50), default='gemini')
    transcript_text = db.Column(db.Text)
    transcript_payload = db.Column(db.Text)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    duration = db.Column(db.Float)
    status = db.Column(db.String(20), default='completed')

    segments = db.relationship(
        'TranscriptSegment',
        backref='job',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='TranscriptSegment.segment_index',
    )
    outputs = db.relationship(
        'TranscriptOutput',
        backref='job',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='TranscriptOutput.output_index',
    )

    def __repr__(self):
        return f'<TranscriptJob {self.source_filename}>'

    def _payload(self):
        if not self.transcript_payload:
            return {}
        try:
            return json.loads(self.transcript_payload)
        except json.JSONDecodeError:
            return {}

    @property
    def selected_style(self):
        return self._payload().get('selected_style', 'meme')

    @property
    def target_languages(self):
        payload = self._payload()
        languages = payload.get('languages')
        if isinstance(languages, list) and languages:
            return languages
        if self.language:
            return [self.language]
        return []

    @property
    def primary_language(self):
        payload = self._payload()
        return payload.get('primary_language', self.language)


class TranscriptOutput(db.Model):
    """Per-language transcript and export artifact for a job."""

    __tablename__ = 'transcript_outputs'

    id = db.Column(db.Integer, primary_key=True)
    transcript_job_id = db.Column(db.Integer, db.ForeignKey('transcript_jobs.id'), nullable=False, index=True)
    output_index = db.Column(db.Integer, nullable=False, default=0)
    language_code = db.Column(db.String(10), nullable=False)
    transcript_text = db.Column(db.Text)
    transcript_payload = db.Column(db.Text)
    duration = db.Column(db.Float)
    srt_filename = db.Column(db.String(200))
    burned_video_filename = db.Column(db.String(200))
    status = db.Column(db.String(20), default='completed')
    is_primary = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TranscriptOutput {self.transcript_job_id}:{self.language_code}>'


class TranscriptSegment(db.Model):
    """Structured transcript segment with timestamps."""

    __tablename__ = 'transcript_segments'

    id = db.Column(db.Integer, primary_key=True)
    transcript_job_id = db.Column(db.Integer, db.ForeignKey('transcript_jobs.id'), nullable=False, index=True)
    segment_index = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<TranscriptSegment {self.transcript_job_id}:{self.segment_index}>'


class PaymentRequest(db.Model):
    """Track premium purchase requests awaiting admin approval."""

    __tablename__ = 'payment_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False, default=499)
    currency = db.Column(db.String(10), nullable=False, default='INR')
    upi_id = db.Column(db.String(120), nullable=False)
    payee_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    payment_reference = db.Column(db.String(120))
    approved_video_limit = db.Column(db.Integer, nullable=False, default=50)
    admin_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<PaymentRequest {self.user_id}:{self.status}>'
