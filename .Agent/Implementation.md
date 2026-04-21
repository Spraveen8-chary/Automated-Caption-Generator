# Implementation - v3 Phased Plan

## Phase 0 - Current-state analysis
### Goal
Identify exactly where the current project conflicts with the new required features.

### Findings to document
- Current `/process` route assumes one `language` and multiple `styles`, which is the reverse of the new requirement.[file:19]
- Current UI exposes one language selector and multi-style checkboxes.[file:32]
- Current free-user limit is implemented as `2` in model and route logic.[file:19][file:23]
- Current transcription service is Gemini-specific.[file:28]
- Current visible workflow is mainly SRT generation, not guaranteed final captioned-video delivery.[file:19][file:25][file:26]

### Acceptance criteria
- All incompatibilities are listed.
- Migration notes are ready.

## Phase 1 - Requirement freeze
### Goal
Freeze the exact revised product behavior.

### Frozen rules
- One run accepts one chosen style and multiple target languages.
- A transcript source should be produced once, then transformed/exported per target language when possible.
- Free-user usage limit must come from env.
- Transcription provider must come from env.
- Captioned video output is mandatory.

### Engineering principle
Clear requirement freeze prevents UI/backend/data mismatches.

### Acceptance criteria
- A single frozen scope statement exists in the repo.
- Env-driven limit/provider behavior is explicitly documented.
- The one-style, multi-language rule is explicit.
- Burned-caption video is recorded as a required output.

## Phase 2 - Config-first architecture
### Goal
Replace hardcoded business and provider assumptions with configuration.

### Work
- Add `TRANSCRIPTION_PROVIDER` strategy.
- Add `FREE_USER_VIDEO_LIMIT` strategy.
- Add optional provider-specific config validation.
- Preserve a free default path using Whisper.

### Acceptance criteria
- System can boot with Whisper only.
- System can boot with AssemblyAI when key is present.
- Limit is no longer hardcoded.

## Phase 3 - Provider abstraction
### Goal
Support multiple STT providers through a single service contract.

### Work
- Define provider interface.
- Implement Whisper/faster-whisper provider.
- Implement AssemblyAI provider.
- Keep provider selection centralized.

### Engineering principle
Open/closed design: add providers without rewriting routes.

### Acceptance criteria
- Route/service orchestration is provider-agnostic.
- Failures are provider-specific but normalized.

## Phase 4 - Multi-language single-style workflow
### Goal
Reshape the product workflow to support one style and multiple target languages.

### Work
- Change request schema from `language` to `languages[]`.[file:19]
- Keep style singular, not a list, if product rule is one style per run.[file:32]
- Create one job, many language outputs.
- Avoid duplicate transcription work when possible.

### Engineering principle
Avoid repeated expensive work by separating source transcript generation from per-language output generation.

### Acceptance criteria
- A single upload can produce multiple language outputs.
- All outputs remain associated with one root job.

## Phase 5 - Usage-limit redesign
### Goal
Make SaaS limits configurable and maintainable.

### Work
- Add `FREE_USER_VIDEO_LIMIT` env support.
- Replace hardcoded `2` checks in model and route layers.[file:19][file:23]
- Reflect configured limit in UI banner and API responses.[file:32]

### Acceptance criteria
- Changing env value changes allowed free usage without code edits.

## Phase 6 - Captioned video artifact pipeline
### Goal
Make captioned video output a first-class deliverable.

### Work
- Generate SRT per language.[file:25]
- Burn subtitle track into video per requested output language.[file:26]
- Save and expose downloadable captioned video file.
- Track relation between original video, SRT, and output video.

### Engineering principle
Artifacts should be explicit and recoverable.

### Acceptance criteria
- User can download a subtitle-burned video file.
- History/admin can reference generated video outputs.

## Phase 7 - UI and tracking alignment
### Goal
Synchronize frontend and admin/history with the new data model.

### Work
- Convert language selector to multi-select or checkbox group.[file:32]
- Convert style UI to single-select if required by product rule.[file:32]
- Add output cards for each language result.
- Add SRT + video download actions.
- Update history/admin summaries.

### Acceptance criteria
- UI behavior matches backend workflow.
- Users can clearly see all outputs.

## Phase 8 - Hardening
### Goal
Stabilize the revised system.

### Work
- Add tests for multi-language jobs, provider switching, free-limit env, and burned-video output.
- Add logs for provider and render failures.
- Update docs and migration notes.

### Acceptance criteria
- Core v3 features are verifiable and documented.
