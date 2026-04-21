# Automated Caption Generator

Flask app for turning uploaded videos into editable transcripts and styled SRT exports.

## What it does

- Upload a video and extract audio for transcription
- Review transcript segments before export
- Preview and export one caption style across multiple languages
- Download generated `.srt` files
- Track processing history for each user
- Provide an admin dashboard for usage visibility

## Current workflow

1. Upload a video.
2. Generate a transcript job from the uploaded source.
3. Edit transcript segments in the browser.
4. Preview the generated language outputs.
5. Export one SRT file per selected language.
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
FREE_USER_VIDEO_LIMIT=2
MAX_TARGET_LANGUAGES_PER_JOB=5
ENABLE_BURNED_VIDEO=true
TRANSCRIPTION_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODEL_FALLBACKS=gemini-2.0-flash
WHISPER_MODEL=base
ASSEMBLYAI_API_KEY=
```

`TRANSCRIPTION_PROVIDER` can be set to `gemini`, `whisper`, or `assemblyai`. If you switch to `whisper`, install either `whisper` or `faster-whisper`. If you switch to `assemblyai`, provide `ASSEMBLYAI_API_KEY` and install the AssemblyAI SDK.

If Gemini hits a quota limit, the app will try Whisper automatically when the local Whisper dependencies are installed.

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
- The current workflow uses one caption style and multiple target languages per job.

## Phase docs

- `docs/phase2-refactor.md`
- `docs/phase3-transcript-workflow.md`
- `docs/phase4-style-export.md`
- `docs/phase5-hardening.md`
