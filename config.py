import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///caption_generator.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv('TEMP_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 100)) * 1024 * 1024  # MB to bytes
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'mp4,mov,avi,mkv,webm').split(','))
    
    # API settings
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Processing settings
        # Processing settings
    AUDIO_FORMAT = 'mp3'
    SUPPORTED_LANGUAGES = [
        # Indian Languages
        'hi', 'bn', 'te', 'mr', 'ta', 'ur', 'gu', 'kn', 'ml', 'pa', 'or', 'as', 
        'mai', 'sa', 'ks', 'sd',
        # International Languages
        'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'ja', 'ko', 'zh',
        'ar', 'th', 'vi', 'id', 'tr', 'he', 'fa', 'uk', 'ro', 'sv', 'no', 'da',
        'fi', 'cs', 'hu', 'el'
    ]

    # Usage limits
    FREE_VIDEO_LIMIT = 2
    
    # Caption styles
    CAPTION_STYLES = {
        'meme': {
            'name': 'Meme Style',
            'description': 'ALL CAPS, SHORT BURSTS, EMOJI-FRIENDLY'
        },
        'formal': {
            'name': 'Formal Style',
            'description': 'Professional, complete sentences'
        },
        'casual': {
            'name': 'Casual Style',
            'description': 'Natural, conversational tone'
        },
        'aesthetic': {
            'name': 'Aesthetic Style',
            'description': '✨ Decorative and artistic ✨'
        }
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
