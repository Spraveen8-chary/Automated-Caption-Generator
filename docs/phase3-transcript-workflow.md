# Phase 3 Multi-Language Workflow

## Purpose
Move the app from a single-language transcript flow to a one-style, multi-language output model.

## What changed
- The `/process` route now creates one root transcript job and multiple language outputs.
- Each target language gets its own transcript payload and export artifact tracking row.
- Users can still review and edit the primary transcript before export.
- The history screen now groups generated outputs under each source job.

## Workflow
1. Upload the video.
2. Choose one caption style.
3. Choose multiple target languages.
4. Transcribe the audio for each requested language.
5. Review and edit the primary transcript.
6. Export SRT files for each selected language.

## Data separation
- `TranscriptJob` stores the root request metadata.
- `TranscriptOutput` stores one language-specific transcript and export state.
- `TranscriptSegment` remains the editable segment store for the primary language output.
- `VideoProcessing` remains the downloadable history/export record for compatibility.

## Acceptance criteria
- Users can choose multiple languages in a single run.
- One job can produce multiple language outputs.
- The saved job tracks the selected style once and languages many.
- History shows the grouped outputs for each job.
