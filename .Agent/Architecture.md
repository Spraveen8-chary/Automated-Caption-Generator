# Architecture - v3

## Baseline from current project
The existing app is a Flask-based caption generator with auth, history, admin, SQLite persistence, multi-style processing, one selected language per run, and Gemini-based transcription.[file:19][file:23][file:28][file:32]

## Target workflow
1. User uploads one video.
2. User selects one style.
3. User selects multiple target languages.
4. System transcribes once using configured provider.
5. System creates per-language outputs.
6. System generates SRT per language.
7. System burns captions into video per language when enabled.
8. System stores artifacts and exposes them in history/admin.

## Key components
### Config layer
- App config
- Env validation
- Provider selection
- Usage-limit selection

### Application layer
- Upload controller
- Processing controller
- History controller
- Admin controller

### Service layer
- `transcription_provider`
- `provider_router`
- `language_output_service`
- `caption_style_service`
- `srt_export_service`
- `video_burn_service`
- `usage_policy_service`
- `artifact_cleanup_service`

### Data layer
- User
- Root processing job
- Per-language output record
- Generated artifact record

## Processing rule
A root job should represent one uploaded video processing request. Each target language should create a child output record tied to the same chosen style.
