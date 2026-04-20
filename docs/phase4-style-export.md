# Phase 4 Style and Export Flow

## Purpose
Make caption styling and export a controlled step on top of the saved transcript state.

## What changed
- Styled caption previews are generated from the saved transcript, not from raw upload output.
- Export writes SRT files from the same saved transcript state.
- Multiple selected styles are previewed and exported together.
- Styling logic stays isolated in the style service, while file writing stays in the export service.

## Workflow
1. Save transcript edits.
2. Preview the selected styles.
3. Export SRT files for the selected styles.
4. Download each exported file through the existing download route.

## Export contract
- Input: transcript job id, selected styles, and saved segment data.
- Output: generated SRT files plus preview metadata for each style.
- Compatibility: existing `/download/<filename>` route remains unchanged.

## Acceptance criteria
- Styled captions are generated from the current saved transcript state.
- SRT timestamps continue to match transcript segments.
- Multi-style export remains supported.
- The download flow still feels familiar to users.

