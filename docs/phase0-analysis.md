# Phase 0 Current-State Analysis

## Purpose
Document the current app behavior and the ways it conflicts with the v3 product direction before freezing requirements.

## What the current code does
- `app.py` still drives the main upload and processing flow directly.
- `templates/index.html` and `static/js/main.js` expose a single language selector and multiple caption-style checkboxes.
- `models.py` still treats `VideoProcessing` as the main history record and keeps the free-user limit logic attached to the user model.
- `utils/transcription.py` is still Gemini-specific, with the transcription model name coming from the current client implementation rather than provider abstraction.
- `download/<filename>` still serves SRT artifacts only.

## Conflicts with the v3 direction
- The current workflow is one selected language plus multiple styles, but v3 requires one style plus multiple target languages.
- The current free-user limit is hardcoded to 2 videos in `User.can_process_video()`.
- The current transcription path is tied to Gemini instead of an env-selected provider.
- The current output path is centered on SRT export, not burned-caption video artifacts.
- The current history model does not yet represent a root job plus per-language outputs.

## Files Reviewed
- [`app.py`](../app.py)
- [`models.py`](../models.py)
- [`templates/index.html`](../templates/index.html)
- [`static/js/main.js`](../static/js/main.js)
- [`utils/transcription.py`](../utils/transcription.py)
- [`docs/phase1-baseline.md`](phase1-baseline.md)

## Migration Notes
- Freeze the product contract before changing routes or database shape.
- Keep the current app usable while the new provider/config/data model is introduced.
- Treat the phase 1 freeze as the agreement that governs the later implementation phases.

## Acceptance Criteria
- The current-state gaps are explicitly listed.
- The phase 1 freeze has a clear basis.
- The migration path is easy to follow for later implementation work.
