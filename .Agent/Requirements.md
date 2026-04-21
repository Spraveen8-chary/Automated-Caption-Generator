# Requirements - v3

## Functional requirements
- User can upload a supported video.[file:19][file:32]
- User can choose one caption style per run.[file:32]
- User can choose multiple target languages per run.[file:19][file:32]
- System selects transcription provider from environment configuration.[file:24][file:28]
- System supports local Whisper/faster-whisper as the free baseline.
- System supports AssemblyAI as an optional provider.
- System enforces free-user video limits using environment configuration.[file:19][file:23]
- System generates SRT per target language.[file:25]
- System generates downloadable captioned video with visible subtitles burned into the video.[file:26]
- User can access all generated outputs in history.[file:31]
- Admin can inspect processing activity.[file:29]

## Non-functional requirements
- No mandatory paid API for baseline operation.
- Provider choice should not require route rewrites.
- Configuration must be documented.
- File artifacts must be traceable and recoverable.
- Existing Flask foundation should be reused when practical.[file:19]

## Product rules
- Single style, multiple languages.
- Free limit from env.
- Provider from env.
- Burned-caption video is a core deliverable.
