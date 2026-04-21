# Env Specification - v3

## Required baseline envs
- `FLASK_SECRET_KEY=`
- `DATABASE_URL=`
- `UPLOAD_FOLDER=`
- `MAX_CONTENT_LENGTH=`
- `ALLOWED_EXTENSIONS=`

## Product config envs
- `FREE_USER_VIDEO_LIMIT=2`
- `MAX_TARGET_LANGUAGES_PER_JOB=5`
- `ENABLE_BURNED_VIDEO=true`

## Provider envs
- `TRANSCRIPTION_PROVIDER=gemini`
- `WHISPER_MODEL=base`
- `ASSEMBLYAI_API_KEY=`
- `GOOGLE_API_KEY=`

## Rules
- If `TRANSCRIPTION_PROVIDER=whisper`, the app should not require `ASSEMBLYAI_API_KEY`.
- If `TRANSCRIPTION_PROVIDER=assemblyai`, the app must validate `ASSEMBLYAI_API_KEY` and the AssemblyAI SDK on startup.
- If `TRANSCRIPTION_PROVIDER=gemini`, the app must validate `GOOGLE_API_KEY` on startup.
- If provider config is invalid, fail with a clear startup error.
