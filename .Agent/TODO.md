# TODO

## Phase 0 - Discovery and stabilization
- [ ] Review the previous codebase structure and confirm all existing routes, services, models, and UI pages.[file:19][file:23][file:28][file:32]
- [ ] Mark reusable modules versus replaceable modules.
- [ ] Identify hard dependencies on Gemini transcription.[file:28]
- [ ] Confirm current database schema and migration risk.[file:23]
- [ ] Document all external configuration variables from config and env files.[file:21][file:18]

## Phase 1 - Requirements and architecture
- [ ] Freeze the V1 target scope.
- [ ] Define actors, major use cases, and system boundaries from the previous product vision.[file:16][file:22]
- [ ] Decide target services: STT, LLM rewrite, video rendering, storage, auth.
- [ ] Define updated module structure.
- [ ] Define API contracts for upload, transcript retrieval, editing, export, and preview.

## Phase 2 - Backend refactor
- [ ] Replace old transcription service abstraction with a provider-based service layer.[file:28]
- [ ] Refactor processing pipeline in `app` flow into orchestration methods.[file:19]
- [ ] Introduce transcript segment persistence.
- [ ] Keep SRT generation isolated in formatter/export service.[file:25]
- [ ] Add preview-render pipeline hooks in video processor.[file:26]

## Phase 3 - Frontend editor flow
- [x] Convert preview-only result flow into transcript editor UI.[file:32]
- [x] Add editable segment timeline.
- [x] Add status indicators for transcript, styled captions, export, preview.
- [x] Keep existing upload and premium gating behavior unless intentionally changed.[file:32]

## Phase 4 - Integration and QA
- [x] Validate upload to transcript flow.
- [x] Validate transcript edit to SRT generation.
- [x] Validate preview rendering.
- [x] Validate history and dashboard compatibility.[file:29][file:31]
- [x] Validate error handling and rollback for failed processing.

## Phase 5 - Hardening
- [x] Add tests for core services.
- [x] Add structured logging.
- [x] Add migration notes and rollback notes.
- [x] Optimize file cleanup and job lifecycle management.[file:19][file:26]
- [x] Update README and delivery documents.[file:22]
