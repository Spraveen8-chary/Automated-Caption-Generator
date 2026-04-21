# Phase 2 Refactor

## Purpose
Move transcription and usage settings out of hardcoded paths and into env-driven configuration.

## What changed
- Added env-backed limits for free users and target-language caps.
- Added `TRANSCRIPTION_PROVIDER` selection with a provider factory.
- Kept Gemini as a compatibility provider while adding Whisper and AssemblyAI adapters.
- Wired the Flask app to build the selected provider at startup.
- Exposed the configured usage limit to the UI and client script.

## New configuration
- `FREE_USER_VIDEO_LIMIT`
- `MAX_TARGET_LANGUAGES_PER_JOB`
- `ENABLE_BURNED_VIDEO`
- `TRANSCRIPTION_PROVIDER`
- `WHISPER_MODEL`
- `ASSEMBLYAI_API_KEY`

## Provider flow
- `gemini` uses the existing Gemini transcription implementation.
- `whisper` uses `whisper` or `faster-whisper` when installed.
- `assemblyai` uses the AssemblyAI SDK when installed.

## Verification notes
- Startup validation should fail fast if the selected provider is invalid or missing required credentials.
- The free-limit banner and API responses now use the configured limit instead of a magic number.
- Transcript jobs now store the selected provider name.
