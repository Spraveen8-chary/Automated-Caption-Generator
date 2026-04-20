# Caption Generator Agent Skill

## Purpose
This `.Agent` workspace defines how to plan, build, review, and evolve the Automated Caption Generator project using an agent-driven workflow. The project is being upgraded from an earlier Flask-based version into a more modular, phase-wise system with cleaner services, editable transcript workflows, and stronger software engineering discipline.[file:19][file:22][file:28][file:32]

## Product goal
Build an AI-powered caption generator for short-form videos that supports timed transcription, caption style transformation, multilingual output, SRT export, preview rendering, user history, and admin monitoring.[file:16][file:22][file:32]

## Existing baseline
The current codebase already includes:
- Flask application structure and route orchestration.[file:19]
- Authentication and premium/free-user gating.[file:19][file:22]
- Video upload and processing workflow.[file:19][file:32]
- Caption styling and SRT generation utilities.[file:19][file:25]
- Gemini-based transcription service that should be replaced or refactored.[file:28]
- Admin dashboard, history screen, and user-facing UI pages.[file:19][file:29][file:31][file:32]

## Agent mission
The agent system should help with:
- Requirement clarification.
- Phase-wise planning.
- Architecture decisions.
- File-by-file implementation.
- Refactoring decisions.
- QA validation.
- Documentation and delivery discipline.

## Working principles
Every phase should follow core software engineering principles:
- Separation of concerns.
- Modular design.
- Low coupling and high cohesion.
- Incremental delivery.
- Testability.
- Traceability from requirement to implementation.
- Documentation-first planning.
- Backward-aware migration from the existing codebase.[file:19][file:22][file:28]

## Project constraints
- Reuse the previous version where practical instead of rebuilding blindly.[file:19][file:22]
- Preserve current working user flows before introducing risky changes.[file:19][file:32]
- Move from single-shot caption generation to transcript-first processing and editing.[file:19][file:28][file:32]
- Keep the system demo-friendly and student-project manageable while improving engineering quality.

## Recommended agent behavior
When implementing any task, the agent should:
1. Read the relevant phase from `Implementation.md`.
2. Check pending work in `TODO.md`.
3. Read architecture boundaries in `Architecture.md`.
4. Review coding standards in `Standards.md`.
5. Update progress in `Progress.md` after each completed task.
6. Record decisions and deviations in `Decisions.md`.

## Deliverable expectations
For each implementation step, produce:
- Scope.
- Files to modify.
- Acceptance criteria.
- Risks.
- Verification steps.

## Definition of done
A task is complete only when:
- Code is implemented.
- Old behavior is not broken unless intentionally replaced.
- Output is testable.
- Documentation is updated.
- Known limitations are explicitly written down.
