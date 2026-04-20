# Phase 1 Baseline

## Purpose
Define the V1 product scope, system boundaries, and API contracts for the current Flask app before any larger refactor.

## V1 Scope
### In scope
- User registration, login, logout, and session status.
- Video upload for supported formats.
- Audio extraction from uploaded video.
- Gemini-based transcription and translation into a selected output language.
- Caption styling for `meme`, `formal`, `casual`, and `aesthetic`.
- SRT generation and download.
- User processing history.
- Admin visibility into users and processing activity.
- Free-user usage limits and premium bypass.

### Out of scope for V1
- Editable transcript timeline.
- Burned-in preview video rendering.
- Real-time collaboration.
- Team workspaces.
- Multi-provider transcription fallback.
- Major admin redesign.

## Actors
- Guest: can only reach auth pages.
- Free user: can upload and process up to 2 videos.
- Premium user: can process without the free limit.
- Admin: can view system-wide analytics and history.

## Core Use Cases
1. Register a new account.
2. Log in and resume a session.
3. Upload a supported video file.
4. Generate captions for one or more styles.
5. Download generated SRT files.
6. Review personal history.
7. Review admin metrics and user activity.

## System Boundaries
### Presentation layer
- Flask templates in `templates/`.
- Client-side behavior in `static/js/`.
- Styling in `static/css/`.

### Application layer
- Route orchestration in `app.py`.
- Auth flow in `auth.py`.

### Domain and service layer
- Video/audio handling in `utils/video_processor.py`.
- Transcription in `utils/transcription.py`.
- Caption formatting and SRT export in `utils/caption_formatter.py`.

### Data layer
- SQLAlchemy models in `models.py`.
- SQLite database in `instance/caption_generator.db` for local development.

### Infrastructure layer
- Environment config in `config.py` and `.env`.
- Upload storage in `uploads/`.
- Third-party transcription API via Google Gemini.

## Workflow States
- uploaded
- audio_extracted
- transcribed
- styled
- srt_generated
- completed
- failed

## API Boundary Definitions
### Auth
- `GET /auth/register`: render registration page.
- `POST /auth/register`: create a user.
- `GET /auth/login`: render login page.
- `POST /auth/login`: authenticate a user.
- `GET /auth/logout`: clear the session.
- `GET /auth/user/status`: return current user status.

### App
- `GET /`: main upload and caption generation page.
- `POST /upload`: save the uploaded video file.
- `POST /process`: extract audio, transcribe, style, and export captions.
- `GET /download/<filename>`: download an SRT file.
- `DELETE /cleanup/<filename>`: remove a stored video file.
- `GET /history`: show the current user's history.
- `GET /admin`: show admin analytics.

## Target Module Structure
The current monolith stays in place for V1, but the next refactor boundary should be:
- `services/transcription_provider.py`
- `services/transcript_service.py`
- `services/style_service.py`
- `services/export_service.py`
- `services/preview_service.py`
- `repositories/processing_repository.py`
- `repositories/transcript_repository.py`
- `routes/upload.py`
- `routes/process.py`
- `routes/history.py`
- `routes/admin.py`

## Acceptance Criteria
- The V1 scope is explicit and frozen.
- Every major route has a documented purpose and input/output shape.
- The current app can be mapped cleanly to future module boundaries.
- Future refactors can proceed without re-deciding basic product scope.
