import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, VideoProcessing
from auth import auth as auth_blueprint
from utils.video_processor import VideoProcessor
from utils.transcription import TranscriptionService
from utils.caption_formatter import CaptionFormatter
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Register auth blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Initialize services
video_processor = VideoProcessor(app.config['UPLOAD_FOLDER'])
transcription_service = TranscriptionService(app.config['GOOGLE_API_KEY'])
caption_formatter = CaptionFormatter()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create database tables
with app.app_context():
    db.create_all()
    # Admin bootstrap
    admin_email = "admin@caption.generator.com"
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        user = User(email=admin_email, username="admin", is_admin=True, is_premium=True)
        user.set_password("Praveen8")
        db.session.add(user)
        db.session.commit()



def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
@login_required
def index():
    """Render main page"""
    return render_template(
        'index.html',
        styles=app.config['CAPTION_STYLES'],
        user=current_user,
        videos_processed=current_user.get_video_count(),
        can_process=current_user.can_process_video()
    )


@app.route('/upload', methods=['POST'])
@login_required
def upload_video():
    """Handle video upload"""
    try:
        # Check usage limit
        if not current_user.can_process_video():
            return jsonify({
                'error': 'You have reached your free limit (2 videos). Please upgrade to premium to continue.',
                'upgrade_required': True
            }), 403
        
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: MP4, MOV, AVI, MKV, WebM'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{original_filename}"
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'file_id': unique_id,
            'filename': filename,
            'original_filename': original_filename,
            'message': 'Video uploaded successfully'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
@login_required
def process_video():
    """Process video and generate captions for one/multiple styles at once."""
    try:
        # Check usage limit: only increment if this is a new (video, language) pair
        data = request.get_json()
        filename = data.get('filename')
        original_filename = data.get('original_filename', filename)
        styles = data.get('styles')   # List of styles
        language = data.get('language', 'en')

        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        if not styles:
            styles = ['meme']  # Default fallback
        
        # For free users, check if user already processed this video+language
        existing_usage = VideoProcessing.query.filter_by(
            user_id=current_user.id,
            filename=filename,
            language=language
        ).first()

        if not existing_usage and not current_user.is_premium and current_user.get_video_count() >= 2:
            return jsonify({
                'error': 'You have reached your free limit (2 videos). Please upgrade to premium.',
                'upgrade_required': True
            }), 403

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404

        # Extract audio only once
        app.logger.info(f"Extracting audio from {filename}")
        audio_path = video_processor.extract_audio(video_path)

        # Only transcribe once per (video, language)
        app.logger.info(f"Transcribing audio with language: {language}")
        transcript = transcription_service.transcribe(audio_path, language)

        results = []
        for style in styles:
            # Format captions for this style
            formatted_captions = caption_formatter.format(transcript, style)
            srt_filename = f"{filename.rsplit('.', 1)[0]}_{style}.srt"
            srt_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_filename)
            caption_formatter.generate_srt(formatted_captions, srt_path)

            # Add a usage DB record if needed (one for first style, track all styles)
            video_record = VideoProcessing(
                user_id=current_user.id,
                filename=filename,
                original_filename=original_filename,
                style=style,
                language=language,
                srt_filename=srt_filename,
                duration=transcript.get('duration', 0),
                status='completed'
            )
            db.session.add(video_record)
            db.session.commit()

            results.append({
                'style': style,
                'srt_filename': srt_filename,
                'captions': formatted_captions[:10],  # First 10 for preview
                'total_captions': len(formatted_captions)
            })

        # Cleanup audio file
        video_processor.cleanup_file(audio_path)

        return jsonify({
            'success': True,
            'results': results,
            'videos_processed': current_user.get_video_count(),
            'videos_remaining': 2 - current_user.get_video_count() if not current_user.is_premium else 'unlimited',
            'message': f'Captions generated successfully for {len(results)} styles'
        }), 200

    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/admin')
@login_required
def admin_dashboard():
    if not getattr(current_user, "is_admin", False):
        return "Unauthorized", 403

    users = User.query.order_by(User.created_at.desc()).all()
    all_videos = VideoProcessing.query.order_by(VideoProcessing.processed_at.desc()).all()
    total_videos = len(all_videos)
    total_users = len(users)

    # Monthly analytics
    now = datetime.utcnow()
    this_month = now.month
    this_year = now.year
    month_videos = [v for v in all_videos if v.processed_at.month == this_month and v.processed_at.year == this_year]
    month_users = [u for u in users if u.created_at.month == this_month and u.created_at.year == this_year]

    # Build user-video history mapping
    user_history = {user.id: [] for user in users}
    for video in all_videos:
        user_history[video.user_id].append(video)

    return render_template(
        "admin_dashboard.html",
        users=users,
        videos=all_videos,
        month_videos=month_videos,
        month_users=month_users,
        total_users=total_users,
        total_videos=total_videos,
        month_video_count=len(month_videos),
        month_new_users=len(month_users),
        user_history=user_history
    )



@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download generated SRT file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/x-subrip'
        )
        
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@app.route('/cleanup/<filename>', methods=['DELETE'])
@login_required
def cleanup(filename):
    """Cleanup uploaded video file"""
    try:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        video_processor.cleanup_file(video_path)
        
        return jsonify({
            'success': True,
            'message': 'File cleaned up successfully'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500


@app.route('/history')
@login_required
def history():
    """View processing history"""
    videos = VideoProcessing.query.filter_by(user_id=current_user.id).order_by(VideoProcessing.processed_at.desc()).all()
    return render_template('history.html', videos=videos, user=current_user)


@app.errorhandler(413)
def file_too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': f'File too large. Maximum size: {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
    }), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    app.logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
