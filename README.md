# Automated Caption Generator

Flask app for turning uploaded videos into editable transcripts and styled SRT exports.

## What it does

- Upload a video and extract audio for transcription
- Review transcript segments before export
- Preview and export multiple caption styles
- Download generated `.srt` files
- Track processing history for each user
- Provide an admin dashboard for usage visibility

## Current workflow

1. Upload a video.
2. Generate a transcript job from the uploaded source.
3. Edit transcript segments in the browser.
4. Preview the selected caption styles.
5. Export one or more SRT files.
6. Download the exported captions from the same app.

## Project layout

- `app.py` - Flask routes and app bootstrap
- `models.py` - SQLAlchemy models
- `services/` - upload, transcript, style, export, and preview orchestration
- `repositories/` - persistence helpers
- `utils/` - caption formatting, transcription, video processing, logging
- `templates/` - HTML views
- `static/` - client-side JavaScript and styles
- `docs/` - phase-by-phase delivery notes

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with at least:

```env
FLASK_SECRET_KEY=your-secret
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=sqlite:///caption_generator.db
TEMP_FOLDER=uploads
MAX_UPLOAD_SIZE=100
ALLOWED_EXTENSIONS=mp4,mov,avi,mkv,webm
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODEL_FALLBACKS=gemini-2.0-flash
```

## Run locally

```bash
python app.py
```

Then open `http://localhost:5000`.

## Hardening notes

- Uploaded source videos and extracted audio are cleaned up after a successful transcript job.
- Exported SRT files remain in `uploads/` so the download route stays stable.
- Structured JSON logging is enabled through the application logger.
- Core service coverage lives in `tests/test_core_services.py`.

## Phase docs

- `docs/phase2-refactor.md`
- `docs/phase3-transcript-workflow.md`
- `docs/phase4-style-export.md`
- `docs/phase5-hardening.md`
