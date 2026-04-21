# .Agent v3 — Free-System + Configurable Provider Plan

This `.Agent-v3` package is the revised planning and execution workspace for building the Automated Caption Generator with a complete free-system baseline and the newly required product features: multi-language output with a single selected style, SaaS-style free-user usage limits, environment-driven transcription provider selection, and saved captioned video output with visible subtitles.[file:19][file:22][file:23][file:24][file:25][file:26][file:28][file:32]

## Mandatory feature commitments
- A user can select one caption style and generate outputs for multiple target languages in one run.[file:19][file:32]
- The free-user video limit must be configurable by environment variable rather than hardcoded to `2`, even though the current project logic already uses a 2-video free-user limit.[file:19][file:23][file:32]
- The transcription engine must be configurable through environment variables so the system can switch between local Whisper/faster-whisper and AssemblyAI, depending on speed, cost, and runtime preference.[file:24][file:28]
- The system must save a downloadable video with visible subtitles burned into the video, not only standalone SRT output.[file:25][file:26]

## Free-system baseline
The default baseline should still work without mandatory paid APIs by using Whisper/faster-whisper locally. AssemblyAI remains an optional provider that can be enabled when an API key is present and faster transcription is preferred.[file:24][file:28]

## Recommended env design
- `TRANSCRIPTION_PROVIDER=whisper` or `assemblyai`
- `USE_WHISPER=true|false`
- `ASSEMBLYAI_API_KEY=`
- `WHISPER_MODEL=base|small|medium`
- `FREE_USER_VIDEO_LIMIT=2`
- `ENABLE_BURNED_VIDEO=true`
- `MAX_TARGET_LANGUAGES_PER_JOB=`

## Package contents
- `SKILL.md`
- `TODO.md`
- `Implementation.md`
- `Architecture.md`
- `Requirements.md`
- `Standards.md`
- `Decisions.md`
- `Progress.md`
- `File-Map.md`
- `Env-Spec.md`
- `Data-Model-Changes.md`
- `Prompts/`
- `Templates/`
