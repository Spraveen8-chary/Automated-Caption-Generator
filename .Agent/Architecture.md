# Architecture

## Current baseline architecture
The current system is a Flask web application with authentication, upload handling, transcription, caption formatting, SRT generation, history tracking, and admin dashboards.[file:19][file:22][file:29][file:31][file:32]

## Target architecture
The target architecture should separate the application into the following layers:
- Presentation layer: HTML, CSS, JS screens for upload, transcript editing, history, auth, and admin.[file:29][file:30][file:31][file:32]
- Application layer: route handlers and workflow orchestration.[file:19]
- Domain/service layer: transcription provider, transcript manager, style engine, caption formatter, video renderer.[file:25][file:26][file:28]
- Data layer: users, processing jobs, transcript segments, generated assets.[file:23]
- Infrastructure layer: config, env variables, file storage, third-party APIs.[file:21][file:18]

## Recommended modules
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

## Core design rules
- Routes should orchestrate, not own business logic.
- Services should be independently testable.
- Formatting should not know about HTTP concerns.
- Rendering should not know about auth concerns.
- Data models should reflect workflow state explicitly.

## Workflow states
Recommended states:
- uploaded
- audio_extracted
- transcribed
- transcript_reviewed
- styled
- srt_generated
- preview_generated
- failed

## Key architectural decision
Keep backward compatibility with the existing Flask foundation while introducing modular boundaries incrementally instead of replacing everything at once.[file:19]
