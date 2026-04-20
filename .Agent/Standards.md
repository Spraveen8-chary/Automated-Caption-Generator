# Engineering Standards

## Coding standards
- Prefer small, single-responsibility modules.
- Avoid large route handlers with mixed responsibilities.[file:19]
- Keep provider-specific code isolated from domain logic.[file:28]
- Use descriptive names for services, states, and artifacts.
- Keep reusable formatting logic independent from UI logic.[file:25][file:32]

## Documentation standards
Every new feature should define:
- Purpose.
- Inputs.
- Outputs.
- Dependencies.
- Failure cases.
- Acceptance criteria.

## Refactoring standards
- Preserve working behavior before optimization.
- Refactor one dependency boundary at a time.
- Document any intentional breaking change.
- Maintain migration notes for database changes.[file:23]

## Testing standards
- Unit test service methods where possible.
- Smoke test end-to-end upload to export path.
- Validate edge cases: unsupported file, failed transcription, empty transcript, rendering failure.[file:19][file:28]

## UI standards
- Keep upload flow simple.
- Make processing states visible to users.[file:32]
- Show clear recovery messages on failure.[file:32]
- Avoid hiding critical workflow state transitions.

## Project management standards
- Work in small phases.
- Complete one acceptance-criteria set before opening the next phase.
- Update `Progress.md` and `Decisions.md` continuously.
