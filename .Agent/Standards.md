# Standards — v3

## Configuration rules
- Business limits must not be hardcoded when they are product settings.
- Provider selection must be centralized.
- Optional providers must fail clearly when misconfigured.

## Data rules
- Separate root jobs from per-language outputs.
- Do not duplicate original video metadata across child outputs unnecessarily.
- Track artifact paths explicitly.

## Service rules
- Route handlers should not know provider internals.
- One service should own usage-policy checks.
- One service should own burned-video generation.

## UI rules
- UI control type must reflect actual business rule; use single-select for style if only one style is allowed, and multi-select for languages.[file:32]
- Result cards should clearly distinguish each language output.

## Testing rules
- Test free-limit env behavior.
- Test provider switch behavior.
- Test one-style multi-language workflow.
- Test SRT and burned-video artifact creation.[file:25][file:26]
