# Data Model Changes - v3

## Problem in current model
The current `VideoProcessing` model stores one record per processed result with fields for `style`, `language`, and `srt_filename`, which is not ideal for one-style multi-language jobs or multiple artifacts per output.[file:23]

## Recommended direction
### Root job
Represents one uploaded video and one selected style.

Suggested fields:
- `id`
- `user_id`
- `filename`
- `original_filename`
- `selected_style`
- `provider_used`
- `status`
- `created_at`

### Language output
Represents one target language derived from the root job.

Suggested fields:
- `id`
- `job_id`
- `language_code`
- `status`
- `duration`
- `transcript_text`
- `srt_filename`
- `burned_video_filename`
- `created_at`

## Migration note
If a full schema redesign is too large initially, add compatibility fields incrementally and migrate in phases.
