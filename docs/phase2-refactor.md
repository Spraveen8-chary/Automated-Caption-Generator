# Phase 2 Refactor

## Purpose
Introduce a service/repository boundary without breaking the current Flask application flow.

## What changed
- Upload handling now lives in `services/upload_service.py`.
- Transcription is accessed through `services/transcription_provider.py`.
- The processing workflow is orchestrated in `services/transcript_service.py`.
- Caption styling and SRT export are wrapped in dedicated service classes.
- Transcript jobs and segments are persisted separately from export artifacts.
- Route handlers now delegate more work instead of owning the full pipeline.

## New module boundaries
- `services/transcription_provider.py`
- `services/transcript_service.py`
- `services/style_service.py`
- `services/export_service.py`
- `services/upload_service.py`
- `services/preview_service.py`
- `repositories/processing_repository.py`
- `repositories/transcript_repository.py`

## Transcript storage design
- `TranscriptJob` stores the transcript request metadata.
- `TranscriptSegment` stores timestamped transcript segments.
- `VideoProcessing` still stores export/history rows for backward compatibility.

## Verification notes
- The upload and process routes should still return the same JSON shape expected by the current frontend.
- SRT generation should still produce downloadable files in `uploads/`.
- Admin and history views should continue to load from the same logical data.

