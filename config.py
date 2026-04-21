import importlib.util
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///caption_generator.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage settings
    UPLOAD_FOLDER = os.getenv('TEMP_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'outputs')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 100)) * 1024 * 1024  # MB to bytes
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'mp4,mov,avi,mkv,webm').split(','))
    
    # API settings
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_MODEL_FALLBACKS = os.getenv('GEMINI_MODEL_FALLBACKS', 'gemini-2.0-flash')
    TRANSCRIPTION_PROVIDER = os.getenv('TRANSCRIPTION_PROVIDER', 'auto').strip().lower()
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')
    ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
    
    # Processing settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    FREE_USER_VIDEO_LIMIT = int(os.getenv('FREE_USER_VIDEO_LIMIT', 2))
    FREE_VIDEO_LIMIT = FREE_USER_VIDEO_LIMIT
    PREMIUM_MONTHLY_PRICE = int(os.getenv('PREMIUM_MONTHLY_PRICE', 499))
    PREMIUM_VIDEO_LIMIT = int(os.getenv('PREMIUM_VIDEO_LIMIT', 50))
    PAYMENT_UPI_ID = os.getenv('PAYMENT_UPI_ID', '9390425742@ybl')
    PAYMENT_PAYEE_NAME = os.getenv('PAYMENT_PAYEE_NAME', 'Caption Generator')
    MAX_TARGET_LANGUAGES_PER_JOB = int(os.getenv('MAX_TARGET_LANGUAGES_PER_JOB', 5))
    ENABLE_BURNED_VIDEO = os.getenv('ENABLE_BURNED_VIDEO', 'true').strip().lower() not in {
        '0',
        'false',
        'no',
        'off',
    }
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

    LANGUAGE_GROUPS = [
        {
            'label': 'Indian Languages',
            'options': [
                ('hi', 'Hindi (हिन्दी)'),
                ('bn', 'Bengali (বাংলা)'),
                ('te', 'Telugu (తెలుగు)'),
                ('mr', 'Marathi (मराठी)'),
                ('ta', 'Tamil (தமிழ்)'),
                ('ur', 'Urdu (اردو)'),
                ('gu', 'Gujarati (ગુજરાતી)'),
                ('kn', 'Kannada (ಕನ್ನಡ)'),
                ('ml', 'Malayalam (മലയാളം)'),
                ('pa', 'Punjabi (ਪੰਜਾਬੀ)'),
                ('or', 'Odia (ଓଡ଼ିଆ)'),
                ('as', 'Assamese (অসমীয়া)'),
                ('sa', 'Sanskrit (संस्कृतम्)'),
            ],
        },
        {
            'label': 'International Languages',
            'options': [
                ('en', 'English'),
                ('es', 'Spanish (Español)'),
                ('fr', 'French (Français)'),
                ('de', 'German (Deutsch)'),
                ('it', 'Italian (Italiano)'),
                ('pt', 'Portuguese (Português)'),
                ('ar', 'Arabic (العربية)'),
                ('ru', 'Russian (Русский)'),
                ('ja', 'Japanese (日本語)'),
                ('ko', 'Korean (한국어)'),
                ('zh', 'Chinese (中文)'),
                ('th', 'Thai (ไทย)'),
                ('vi', 'Vietnamese (Tiếng Việt)'),
                ('id', 'Indonesian (Bahasa Indonesia)'),
                ('tr', 'Turkish (Türkçe)'),
            ],
        },
    ]

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
    
    @classmethod
    def init_app(cls, app):
        """Initialize application configuration"""
        # Create storage folders if they don't exist
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)

    @classmethod
    def validate_app_config(cls):
        """Validate configuration values that gate startup."""
        if cls.FREE_USER_VIDEO_LIMIT < 1:
            raise ValueError('FREE_USER_VIDEO_LIMIT must be at least 1')

        if cls.PREMIUM_MONTHLY_PRICE < 1:
            raise ValueError('PREMIUM_MONTHLY_PRICE must be at least 1')

        if cls.PREMIUM_VIDEO_LIMIT < 1:
            raise ValueError('PREMIUM_VIDEO_LIMIT must be at least 1')

        if cls.MAX_TARGET_LANGUAGES_PER_JOB < 1:
            raise ValueError('MAX_TARGET_LANGUAGES_PER_JOB must be at least 1')

        provider = (cls.TRANSCRIPTION_PROVIDER or 'auto').strip().lower()
        valid_providers = {'auto', 'whisper', 'assemblyai', 'gemini'}
        if provider not in valid_providers:
            raise ValueError(
                f"Invalid TRANSCRIPTION_PROVIDER '{provider}'. "
                f"Expected one of: {sorted(valid_providers)}"
            )

        if provider == 'gemini':
            warnings.warn(
                'TRANSCRIPTION_PROVIDER=gemini is deprecated; using auto transcription with Gemini for styling only.',
                RuntimeWarning,
                stacklevel=2,
            )
            cls.TRANSCRIPTION_PROVIDER = 'auto'
            provider = 'auto'

        if provider == 'auto':
            return

        if provider == 'whisper':
            whisper_available = importlib.util.find_spec('whisper') is not None
            faster_whisper_available = importlib.util.find_spec('faster_whisper') is not None
            if not whisper_available and not faster_whisper_available:
                raise ValueError(
                    'TRANSCRIPTION_PROVIDER=whisper requires the whisper or faster-whisper package'
                )

        if provider == 'assemblyai' and not cls.ASSEMBLYAI_API_KEY:
            raise ValueError('ASSEMBLYAI_API_KEY is required when TRANSCRIPTION_PROVIDER=assemblyai')

        if provider == 'assemblyai' and importlib.util.find_spec('assemblyai') is None:
            raise ValueError('TRANSCRIPTION_PROVIDER=assemblyai requires the assemblyai package')
