from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_video_count(self):
        """Get number of videos processed by user"""
        return len(self.videos)
    
    def can_process_video(self):
        """Check if user can process more videos"""
        if self.is_premium:
            return True
        return self.get_video_count() < 2
    
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
