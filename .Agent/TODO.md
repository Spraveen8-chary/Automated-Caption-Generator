# TODO - v3 Features Included

## Phase 0 - Analyze current system
- [x] Audit where current code assumes one language only.[file:19][file:32]
- [x] Audit where current free-user limit is hardcoded.[file:19][file:23]
- [x] Audit current transcription engine coupling to Gemini.[file:28]
- [x] Audit current media output path for SRT-only vs video output.[file:25][file:26]

## Phase 1 - Freeze revised requirements
- [x] Confirm single-style, multi-language workflow.
- [x] Confirm env-based free-user limit.
- [x] Confirm env-based provider selection.
- [x] Confirm burned-caption video as mandatory output.

## Phase 2 - Configuration and provider refactor
- [x] Add env-driven provider config.
- [x] Add Whisper/faster-whisper provider.
- [x] Add AssemblyAI provider.
- [x] Remove direct dependency on Gemini-only transcription flow.[file:28]

## Phase 3 - Data and workflow changes
- [x] Support multiple target languages in one job.
- [x] Track style once, language many.
- [x] Add transcript/output records per language.
- [x] Make history reflect multi-output jobs.

## Phase 4 - Usage limit redesign
- [x] Replace hardcoded free limit with env config.[file:19][file:23]
- [x] Ensure UI banner reads configured limit.[file:32]
- [x] Ensure process checks match configured limit.

## Phase 5 - Captioned video output
- [x] Generate SRT for each target language.[file:25]
- [x] Burn selected SRT captions into the uploaded video.[file:26]
- [x] Save downloadable captioned video artifacts.
- [x] Preserve original and generated file relationships.

## Phase 6 - UI alignment
- [x] Change language selection from single select to multi-select.[file:32]
- [x] Restrict style selection to one chosen style per run if required by product rule.[file:32]
- [x] Add provider-selection or provider-display behavior if exposed in UI.
- [x] Add captioned-video download actions.

## Phase 7 - Hardening
- [x] Add tests for multi-language jobs.
- [x] Add tests for env-driven limits.
- [x] Add tests for provider switching.
- [x] Add tests for burned-video generation.
