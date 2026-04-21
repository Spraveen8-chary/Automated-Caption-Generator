# Phase 1 Requirements Freeze

## Purpose
Freeze the v3 product scope, system boundaries, and data assumptions before implementation work starts.

This freeze follows the current-state analysis in [`docs/phase0-analysis.md`](phase0-analysis.md).

## Frozen Product Rules
- One run accepts one selected caption style.
- One run accepts multiple target languages.
- Free-user usage limits come from environment configuration.
- The transcription provider comes from environment configuration.
- Burned-in captioned video is a required output, not an optional add-on.
- The system should still remain usable without a mandatory paid API in the baseline path.

## In Scope
- User registration, login, logout, and session status.
- Supported video upload.
- Transcription using a configurable provider.
- Translation into multiple target languages per job.
- Caption styling for the selected style.
- SRT generation per target language.
- Burned-caption video generation per target language.
- Download of generated artifacts.
- Personal history.
- Admin visibility into users and processing activity.

## Out of Scope
- Multiple styles in the same run.
- Editable transcript timeline as the primary workflow.
- Real-time collaboration.
- Team workspaces.
- Major admin redesign.

## Actors
- Guest: can access auth pages only.
- Free user: can process up to the configured free limit.
- Premium user: can bypass the free limit.
- Admin: can view system-wide analytics and history.

## Core Use Cases
1. Register a new account.
2. Log in and resume a session.
3. Upload a supported video file.
4. Choose one caption style and multiple target languages.
5. Generate caption outputs for each target language.
6. Download SRT files and burned-caption video files.
7. Review personal history.
8. Review admin metrics and user activity.

## System Boundaries
### Presentation layer
- Flask templates in `templates/`.
- Client-side behavior in `static/js/`.
- Styling in `static/css/`.

### Application layer
- Route orchestration in `app.py`.
- Auth flow in `auth.py`.

### Domain and service layer
- Video and audio handling in `utils/video_processor.py`.
- Transcription in `utils/transcription.py`.
- Caption formatting in `utils/caption_formatter.py`.
- Provider selection and orchestration in service/repository helpers.

### Data layer
- SQLAlchemy models in `models.py`.
- SQLite database for local development.

### Infrastructure layer
- Environment config in `config.py` and `.env`.
- Upload storage in `uploads/`.
- Third-party transcription provider selected by env.

## Workflow States
- uploaded
- audio_extracted
- transcribed
- translated
- styled
- srt_generated
- video_burned
- completed
- failed

## API Boundary Definitions
### Auth
- `GET /auth/register`
- `POST /auth/register`
- `GET /auth/login`
- `POST /auth/login`
- `GET /auth/logout`
- `GET /auth/user/status`

### App
- `GET /`
- `POST /upload`
- `POST /process`
- `GET /download/<filename>`
- `DELETE /cleanup/<filename>`
- `GET /history`
- `GET /admin`

## Data Model Direction
- A root job should represent one uploaded video processing request.
- A child output record should represent each target language generated from the root job.
- Each language output should be able to point to both SRT and burned-video artifacts.

## Acceptance Criteria
- The v3 scope is explicit and frozen.
- The one-style, multi-language rule is documented.
- Free-user limits are documented as env-driven.
- Provider selection is documented as env-driven.
- Burned-caption video output is documented as required.
- Future refactors can proceed without re-deciding product scope.
