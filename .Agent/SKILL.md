# Caption Generator Skill — v3

## Role
This agent plans and builds the caption generator as a configurable SaaS-like application with a free baseline and optional faster provider support.[file:19][file:22][file:24][file:28]

## Must-support features
- Single selected style with multiple target languages.[file:19][file:32]
- Free-user video usage control through environment configuration.[file:19][file:23]
- Provider selection through environment configuration.
- Burned-caption downloadable video output.[file:25][file:26]

## Engineering principles
- Requirements before implementation.
- Configuration over hardcoding.
- Provider abstraction.
- Reusable service boundaries.
- Deterministic baseline behavior.
- Backward-aware refactoring from existing Flask code.[file:19][file:23][file:28]
- Testability and observability.

## Product principles
- Default mode should stay free-system friendly.
- Paid provider usage must be optional.
- UI choices must map clearly to backend job behavior.
- Every generated artifact must be traceable in history/admin.

## Definition of done
A feature is done only if:
- UI supports it when applicable.
- Backend supports it.
- Database/history can represent it.
- Configuration is documented.
- Acceptance criteria are met.
