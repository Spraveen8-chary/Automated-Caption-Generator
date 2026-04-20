import os
import logging
import uuid

from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class UploadService:
    """Validate and persist uploaded video files."""

    def __init__(self, upload_folder, allowed_extensions, max_content_length=None):
        self.upload_folder = upload_folder
        self.allowed_extensions = {ext.lower().lstrip('.') for ext in allowed_extensions}
        self.max_content_length = max_content_length

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_uploaded_file(self, file_storage):
        if file_storage is None:
            raise ValueError('No video file provided')

        if file_storage.filename == '':
            raise ValueError('No file selected')

        if not self.allowed_file(file_storage.filename):
            raise ValueError('Invalid file type. Allowed: MP4, MOV, AVI, MKV, WebM')

        original_filename = secure_filename(file_storage.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{original_filename}"
        filepath = os.path.join(self.upload_folder, filename)
        file_storage.save(filepath)
        logger.info(
            "upload.saved",
            extra={
                'file_id': unique_id,
                'uploaded_filename': filename,
                'original_filename': original_filename,
            },
        )

        return {
            'success': True,
            'file_id': unique_id,
            'filename': filename,
            'original_filename': original_filename,
            'filepath': filepath,
            'message': 'Video uploaded successfully',
        }
