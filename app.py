import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, VideoProcessing
from auth import auth as auth_blueprint
from repositories.processing_repository import ProcessingRepository
from services.transcript_service import TranscriptService
from services.upload_service import UploadService
from utils.logging_utils import configure_logging
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)
configure_logging(app)
logger = logging.getLogger(__name__)

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
upload_service = UploadService(
    app.config['UPLOAD_FOLDER'],
    app.config['ALLOWED_EXTENSIONS'],
    app.config['MAX_CONTENT_LENGTH'],
)
processing_repository = ProcessingRepository()
transcript_service = TranscriptService(
    app.config['UPLOAD_FOLDER'],
    app.config['GOOGLE_API_KEY'],
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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
        file = request.files.get('video')
        upload_data = upload_service.save_uploaded_file(file)
        logger.info(
            "upload.completed",
            extra={
                'user_id': current_user.id,
                'file_id': upload_data['file_id'],
                'uploaded_filename': upload_data['filename'],
            },
        )
        return jsonify({
            'success': True,
            'file_id': upload_data['file_id'],
            'filename': upload_data['filename'],
            'original_filename': upload_data['original_filename'],
            'message': upload_data['message']
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("upload.failed", extra={'user_id': current_user.id})
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
@login_required
def process_video():
    """Process video into a structured transcript."""
    filename = None
    try:
        data = request.get_json(silent=True) or {}
        filename = data.get('filename')
        original_filename = data.get('original_filename', filename)
        styles = data.get('styles')
        language = data.get('language', 'en')

        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        if not styles:
            styles = ['meme']

        logger.info(
            "process.requested",
            extra={
                'user_id': current_user.id,
                'source_filename': filename,
                'language': language,
                'styles': styles,
            },
        )
        result = transcript_service.process_video(
            user=current_user,
            filename=filename,
            original_filename=original_filename,
            styles=styles,
            language=language,
        )
        return jsonify(result), 200
    except PermissionError as e:
        return jsonify({'error': str(e), 'upgrade_required': True}), 403
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("process.failed", extra={'user_id': current_user.id, 'source_filename': filename})
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/transcripts/<int:job_id>', methods=['GET'])
@login_required
def get_transcript(job_id):
    """Fetch a saved transcript job and its segments."""
    try:
        transcript = transcript_service.get_transcript_job(current_user, job_id)
        logger.info("transcript.loaded", extra={'user_id': current_user.id, 'job_id': job_id})
        return jsonify({'success': True, 'transcript': transcript}), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.exception("transcript.fetch.failed", extra={'user_id': current_user.id, 'job_id': job_id})
        return jsonify({'error': f'Failed to load transcript: {str(e)}'}), 500


@app.route('/transcripts/<int:job_id>', methods=['PUT'])
@login_required
def update_transcript(job_id):
    """Update saved transcript segment text/timestamps."""
    try:
        data = request.get_json(silent=True) or {}
        segments = data.get('segments', [])
        transcript = transcript_service.update_transcript_job(current_user, job_id, segments)
        return jsonify({'success': True, 'transcript': transcript}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.exception("transcript.update.failed", extra={'user_id': current_user.id, 'job_id': job_id})
        return jsonify({'error': f'Failed to update transcript: {str(e)}'}), 500


@app.route('/transcripts/<int:job_id>/export', methods=['POST'])
@login_required
def export_transcript(job_id):
    """Export SRT files from the current saved transcript."""
    try:
        data = request.get_json(silent=True) or {}
        segments = data.get('segments')
        if segments:
            transcript_service.update_transcript_job(current_user, job_id, segments)
        styles = data.get('styles') or ['meme']
        result = transcript_service.export_transcript(current_user, job_id, styles=styles)
        logger.info(
            "transcript.exported",
            extra={'user_id': current_user.id, 'job_id': job_id, 'styles': styles},
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.exception("transcript.export.failed", extra={'user_id': current_user.id, 'job_id': job_id})
        return jsonify({'error': f'Failed to export transcript: {str(e)}'}), 500


@app.route('/transcripts/<int:job_id>/styles', methods=['POST'])
@login_required
def preview_styles(job_id):
    """Preview styled caption output for the saved transcript."""
    try:
        data = request.get_json(silent=True) or {}
        styles = data.get('styles') or ['meme']
        result = transcript_service.preview_styles(current_user, job_id, styles=styles)
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.exception("transcript.preview.failed", extra={'user_id': current_user.id, 'job_id': job_id})
        return jsonify({'error': f'Failed to preview styles: {str(e)}'}), 500

@app.route('/admin')
@login_required
def admin_dashboard():
    if not getattr(current_user, "is_admin", False):
        return "Unauthorized", 403

    users = processing_repository.get_all_users()
    all_videos = processing_repository.get_all_videos()
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

        logger.info("download.requested", extra={'user_id': current_user.id, 'download_filename': filename})
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/x-subrip'
        )

    except Exception as e:
        logger.exception("download.failed", extra={'user_id': current_user.id, 'download_filename': filename})
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@app.route('/cleanup/<filename>', methods=['DELETE'])
@login_required
def cleanup(filename):
    """Cleanup uploaded video file"""
    try:
        transcript_service.cleanup_uploaded_artifacts(secure_filename(filename))

        return jsonify({
            'success': True,
            'message': 'File cleaned up successfully'
        }), 200

    except Exception as e:
        logger.exception("cleanup.failed", extra={'user_id': current_user.id, 'cleanup_filename': filename})
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500


@app.route('/history')
@login_required
def history():
    """View processing history"""
    videos = processing_repository.get_user_history(current_user.id)
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
    logger.exception("internal.error")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
