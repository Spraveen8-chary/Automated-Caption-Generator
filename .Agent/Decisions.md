# Decisions Log

## Initial decisions
- The existing Flask-based project is the migration base, not a throwaway prototype.[file:19][file:22]
- The current Gemini-driven transcription service is considered a replaceable provider-specific implementation.[file:28]
- The future architecture should be transcript-first rather than direct style-first generation.[file:19][file:28][file:32]
- UI changes should extend the existing screens where possible instead of rebuilding the entire frontend immediately.[file:32]
- Admin and history modules are in scope for compatibility review, not immediate redesign.[file:29][file:31]

## Phase 1 decisions
- Date: 2026-04-20
- Decision: Freeze the V1 scope around auth, upload, transcription, caption styling, SRT export, history, and admin visibility.
- Why: The project needs a stable baseline before any deeper transcript editor or preview workflow is added.
- Impacted files: docs/phase1-baseline.md, .Agent/Progress.md
- Risk: Explicitly postponing preview rendering and transcript editing keeps the first delivery smaller, but those features remain planned later.
- Follow-up: Use the new phase 1 baseline as the reference point for phase 2 refactoring.

## Phase 2 decisions
- Date: 2026-04-20
- Decision: Add a service/repository layer now, but keep the current Flask app and JSON contract intact.
- Why: The app can be made more modular without forcing a frontend rewrite or breaking the current workflow.
- Impacted files: app.py, models.py, services/*, repositories/*
- Risk: Transcript jobs are stored separately from legacy export rows, so later normalization will still need a follow-up pass.
- Follow-up: Phase 3 can build on the new transcript storage without changing the route contract again.

## Phase 3 decisions
- Date: 2026-04-20
- Decision: Move caption generation to a transcript-first flow with separate save and export steps.
- Why: Users need to edit transcript text before SRT output is finalized.
- Impacted files: app.py, templates/index.html, static/js/main.js, static/css/style.css, repositories/transcript_repository.py, services/transcript_service.py
- Risk: History now reflects exported caption rows, while draft transcript jobs live separately until export.
- Follow-up: Phase 4 can focus on styling/export details using the saved transcript state.

## Phase 4 decisions
- Date: 2026-04-20
- Decision: Add an explicit style-preview step driven by the saved transcript state before export.
- Why: The user should be able to see the transformed captions before writing SRT files.
- Impacted files: app.py, services/style_service.py, services/export_service.py, services/transcript_service.py, templates/index.html, static/js/main.js, static/css/style.css
- Risk: The frontend now depends on the preview endpoint, so future style changes should keep the preview response stable.
- Follow-up: Phase 5 can reuse the same saved transcript data for preview rendering without changing the style/export contract.

## Decision template
Use this format for future entries:
- Date:
- Decision:
- Why:
- Impacted files:
- Risk:
- Follow-up:
