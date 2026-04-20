# Phase 3 Transcript Workflow

## Purpose
Shift the app from one-shot caption generation to a transcript-first workflow where users can review and edit segments before exporting captions.

## What changed
- The `/process` route now creates a structured transcript job.
- Transcript jobs and segments are persisted separately.
- Users can fetch a transcript job with `GET /transcripts/<job_id>`.
- Users can save edits with `PUT /transcripts/<job_id>`.
- Users can export SRTs from the saved transcript with `POST /transcripts/<job_id>/export`.
- The main page now shows an editable transcript editor instead of only a static preview.

## Workflow
1. Upload the video.
2. Transcribe the audio into structured segments.
3. Review and edit the transcript blocks.
4. Save the transcript or export directly.
5. Generate SRTs from the saved transcript state.

## Data separation
- Raw transcript lives in `TranscriptJob.transcript_payload` and `TranscriptSegment`.
- Styled caption output is generated only at export time.
- Export rows remain in `VideoProcessing` for history and download compatibility.

## Acceptance criteria
- Users can view transcript segments with timestamps.
- Users can edit caption text before export.
- Changes persist in the database.
- Exported SRTs are generated from the saved transcript state.

