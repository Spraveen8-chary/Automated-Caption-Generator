# File Map — v3

## Current files affected
- `app-4.py` — process flow, usage checks, request schema, downloads.[file:19]
- `models-8.py` — user limit logic and processing records.[file:23]
- `transcription-12.py` — current Gemini-only provider implementation.[file:28]
- `caption_formatter-11.py` — SRT generation path.[file:25]
- `video_processor-13.py` — media extraction/rendering utilities.[file:26]
- `index-16.html` — current single-language, multi-style UI.[file:32]
- `history-15.html` — output visibility.[file:31]
- `admin_dashboard-14.html` — output/admin reporting.[file:29]

## Recommended new files
- `services/provider_router.py`
- `services/whisper_provider.py`
- `services/assemblyai_provider.py`
- `services/usage_policy_service.py`
- `services/language_output_service.py`
- `services/video_burn_service.py`
- `models/output_artifact.py` or equivalent extension
