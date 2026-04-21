import os
import logging
import mimetypes
from urllib.parse import urlencode
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, VideoProcessing, PaymentRequest
from auth import auth as auth_blueprint
from services.admin_database_service import admin_database_bp
from repositories.processing_repository import ProcessingRepository
from repositories.transcript_repository import TranscriptRepository
from services.style_service import StyleService
from services.transcript_service import TranscriptService
from services.upload_service import UploadService
from utils.logging_utils import configure_logging
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)
Config.validate_app_config()
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
app.register_blueprint(admin_database_bp)

# Initialize services
upload_service = UploadService(
    app.config['UPLOAD_FOLDER'],
    app.config['ALLOWED_EXTENSIONS'],
    app.config['MAX_CONTENT_LENGTH'],
)
processing_repository = ProcessingRepository()
transcript_repository = TranscriptRepository()
transcript_service = TranscriptService(
    app.config['UPLOAD_FOLDER'],
    app.config['GOOGLE_API_KEY'],
    output_folder=app.config['OUTPUT_FOLDER'],
    style_service=StyleService(
        gemini_api_key=app.config['GOOGLE_API_KEY'],
        gemini_model=app.config.get('GEMINI_MODEL'),
    ),
    transcript_repository=transcript_repository,
    processing_repository=processing_repository,
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
    provider_labels = {
        'auto': 'Auto',
        'whisper': 'Whisper',
        'assemblyai': 'AssemblyAI',
    }
    transcription_provider = app.config['TRANSCRIPTION_PROVIDER']
    style_provider_display = 'Gemini' if app.config.get('GOOGLE_API_KEY') else 'Local'
    latest_payment_request = (
        PaymentRequest.query.filter_by(user_id=current_user.id)
        .order_by(PaymentRequest.created_at.desc())
        .first()
    )
    payment_request_payload = None
    if latest_payment_request is not None:
        payment_request_payload = {
            'id': latest_payment_request.id,
            'status': latest_payment_request.status,
            'amount': latest_payment_request.amount,
            'currency': latest_payment_request.currency,
            'upi_id': latest_payment_request.upi_id,
            'payee_name': latest_payment_request.payee_name,
            'payment_reference': latest_payment_request.payment_reference,
            'approved_video_limit': latest_payment_request.approved_video_limit,
            'admin_message': latest_payment_request.admin_message,
            'created_at': latest_payment_request.created_at.isoformat() if latest_payment_request.created_at else None,
            'approved_at': latest_payment_request.approved_at.isoformat() if latest_payment_request.approved_at else None,
        }
    payment_uri = "upi://pay?" + urlencode({
        'pa': app.config['PAYMENT_UPI_ID'],
        'pn': app.config['PAYMENT_PAYEE_NAME'],
        'am': str(app.config['PREMIUM_MONTHLY_PRICE']),
        'cu': 'INR',
        'tn': f"Premium plan for {current_user.username}",
    })
    return render_template(
        'index.html',
        styles=app.config['CAPTION_STYLES'],
        language_groups=app.config['LANGUAGE_GROUPS'],
        user=current_user,
        plan_label=current_user.get_plan_label(),
        active_video_limit=current_user.get_active_video_limit(),
        remaining_video_count=current_user.get_remaining_video_count(),
        videos_processed=current_user.get_usage_count(),
        can_process=current_user.can_process_video(),
        free_user_video_limit=app.config['FREE_USER_VIDEO_LIMIT'],
        premium_monthly_price=app.config['PREMIUM_MONTHLY_PRICE'],
        premium_video_limit=app.config['PREMIUM_VIDEO_LIMIT'],
        payment_upi_id=app.config['PAYMENT_UPI_ID'],
        payment_payee_name=app.config['PAYMENT_PAYEE_NAME'],
        payment_uri=payment_uri,
        payment_request=latest_payment_request,
        payment_request_payload=payment_request_payload,
        max_target_languages_per_job=app.config['MAX_TARGET_LANGUAGES_PER_JOB'],
        enable_burned_video=app.config['ENABLE_BURNED_VIDEO'],
        transcription_provider=transcription_provider,
        transcription_provider_display=provider_labels.get(transcription_provider, transcription_provider.title()),
        style_provider_display=style_provider_display,
    )


@app.route('/upload', methods=['POST'])
@login_required
def upload_video():
    """Handle video upload"""
    try:
        # Check usage limit
        if not current_user.can_process_video():
            return jsonify({
                'error': f"You have reached your free limit ({app.config['FREE_USER_VIDEO_LIMIT']} videos). Please upgrade to premium to continue.",
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
        style = data.get('style')
        styles = data.get('styles')
        languages = data.get('languages')
        language = data.get('language', 'en')

        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        if not style:
            if styles:
                style = styles[0]
            else:
                style = 'meme'

        if not languages:
            languages = [language] if language else ['en']

        logger.info(
            "process.requested",
            extra={
                'user_id': current_user.id,
                'source_filename': filename,
                'languages': languages,
                'style': style,
            },
        )
        result = transcript_service.process_video(
            user=current_user,
            filename=filename,
            original_filename=original_filename,
            style=style,
            styles=styles,
            languages=languages,
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
        language_code = data.get('language') or data.get('language_code')
        transcript = transcript_service.update_transcript_job(current_user, job_id, segments, language_code=language_code)
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
            language_code = data.get('language') or data.get('language_code')
            transcript_service.update_transcript_job(current_user, job_id, segments, language_code=language_code)
        languages = data.get('languages') or data.get('language')
        result = transcript_service.export_transcript(current_user, job_id, languages=languages)
        logger.info(
            "transcript.exported",
            extra={'user_id': current_user.id, 'job_id': job_id, 'languages': result.get('selected_languages', [])},
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
        result = transcript_service.preview_styles(current_user, job_id)
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
    payment_requests = PaymentRequest.query.order_by(PaymentRequest.created_at.desc()).all()
    pending_payment_requests = [payment_request for payment_request in payment_requests if payment_request.status == 'pending']
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
        user_history=user_history,
        payment_requests=payment_requests,
        pending_payment_requests=pending_payment_requests,
        pending_payment_count=len(pending_payment_requests),
        premium_video_limit=app.config['PREMIUM_VIDEO_LIMIT'],
        premium_monthly_price=app.config['PREMIUM_MONTHLY_PRICE']
    )


@app.route('/payments/request', methods=['POST'])
@login_required
def request_premium_payment():
    """Create a pending premium payment request for the current user."""
    try:
        data = request.get_json(silent=True) or {}
        payment_reference = (data.get('payment_reference') or '').strip()

        existing_pending = PaymentRequest.query.filter_by(user_id=current_user.id, status='pending').first()
        if existing_pending is not None:
            return jsonify({
                'success': True,
                'message': 'You already have a pending payment request.',
                'payment_request': {
                    'id': existing_pending.id,
                    'status': existing_pending.status,
                    'amount': existing_pending.amount,
                    'video_limit': existing_pending.approved_video_limit,
                },
            }), 200

        payment_request = PaymentRequest(
            user_id=current_user.id,
            amount=app.config['PREMIUM_MONTHLY_PRICE'],
            currency='INR',
            upi_id=app.config['PAYMENT_UPI_ID'],
            payee_name=app.config['PAYMENT_PAYEE_NAME'],
            status='pending',
            payment_reference=payment_reference or None,
            approved_video_limit=app.config['PREMIUM_VIDEO_LIMIT'],
            admin_message=f'Payment request submitted by {current_user.username}',
        )
        db.session.add(payment_request)
        db.session.commit()

        logger.info(
            "payment.request.created",
            extra={'user_id': current_user.id, 'payment_request_id': payment_request.id},
        )
        return jsonify({
            'success': True,
            'message': 'Payment request sent to admin for approval.',
            'payment_request': {
                'id': payment_request.id,
                'status': payment_request.status,
                'amount': payment_request.amount,
                'video_limit': payment_request.approved_video_limit,
            },
        }), 201
    except Exception as e:
        logger.exception("payment.request.failed", extra={'user_id': current_user.id})
        return jsonify({'error': f'Could not submit payment request: {str(e)}'}), 500


@app.route('/admin/payments/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_payment_request(request_id):
    """Approve a premium payment request and grant the premium video limit."""
    if not getattr(current_user, "is_admin", False):
        return jsonify({'error': 'Unauthorized'}), 403

    payment_request = db.session.get(PaymentRequest, request_id)
    if payment_request is None:
        return jsonify({'error': 'Payment request not found'}), 404

    payment_request.status = 'approved'
    payment_request.approved_at = datetime.utcnow()
    payment_request.admin_message = f'Approved by {current_user.username}'
    if payment_request.user is not None:
        payment_request.user.is_premium = True

    db.session.commit()
    logger.info(
        "payment.request.approved",
        extra={'admin_id': current_user.id, 'payment_request_id': request_id, 'user_id': payment_request.user_id},
    )
    return jsonify({
        'success': True,
        'message': 'Payment approved. Premium limit activated.',
        'user_id': payment_request.user_id,
        'video_limit': payment_request.approved_video_limit,
    }), 200


@app.route('/admin/payments/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_payment_request(request_id):
    """Reject a premium payment request."""
    if not getattr(current_user, "is_admin", False):
        return jsonify({'error': 'Unauthorized'}), 403

    payment_request = db.session.get(PaymentRequest, request_id)
    if payment_request is None:
        return jsonify({'error': 'Payment request not found'}), 404

    payment_request.status = 'rejected'
    payment_request.approved_at = None
    payment_request.admin_message = f'Rejected by {current_user.username}'
    db.session.commit()
    logger.info(
        "payment.request.rejected",
        extra={'admin_id': current_user.id, 'payment_request_id': request_id, 'user_id': payment_request.user_id},
    )
    return jsonify({
        'success': True,
        'message': 'Payment request rejected.',
        'user_id': payment_request.user_id,
    }), 200



@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download a generated caption artifact."""
    try:
        safe_filename = secure_filename(filename)
        search_paths = [app.config['OUTPUT_FOLDER'], app.config['UPLOAD_FOLDER']]
        filepath = None
        for base_path in search_paths:
            candidate_path = os.path.join(base_path, safe_filename)
            if os.path.exists(candidate_path):
                filepath = candidate_path
                break

        if filepath is None:
            return jsonify({'error': 'File not found'}), 404

        logger.info("download.requested", extra={'user_id': current_user.id, 'download_filename': filename})
        mimetype, _ = mimetypes.guess_type(filepath)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype or 'application/octet-stream'
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
    jobs = transcript_repository.get_jobs_for_user(current_user.id)
    return render_template('history.html', jobs=jobs, user=current_user)


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
