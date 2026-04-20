# Phase 5 Hardening

## Purpose
Stabilize the transcript-first workflow with test coverage, structured logging, and safer file cleanup.

## What changed

- Added core service tests for caption formatting, transcript persistence, and export flows.
- Added structured JSON logging for upload, process, preview, export, download, and cleanup events.
- Cleaned up temporary source and audio files after a successful transcript job.
- Kept exported SRT files available for the existing download route.

## Operational behavior

- Source videos are deleted only after transcript generation succeeds.
- Extracted audio is always removed after processing attempts.
- SRT files stay in the upload folder so users can download them later.

## Migration notes

- Existing SQLite databases do not need a destructive reset.
- The new `transcript_jobs` and `transcript_segments` tables are created on startup through `db.create_all()`.
- Existing `video_processing` rows remain valid and continue to support history and download compatibility.

## Rollback notes

- To roll back, remove the new cleanup call in `TranscriptService.process_video` and restore the previous route logging if needed.
- The schema additions are additive, so a rollback can keep the tables in place without breaking the older app flow.
- If you need to fully revert the schema, drop the new transcript tables after backing up the database.

## Verification

- Run `python -m unittest discover -s tests` to validate the core service path.
- Confirm upload, transcript edit, preview, export, and download still work end to end.
