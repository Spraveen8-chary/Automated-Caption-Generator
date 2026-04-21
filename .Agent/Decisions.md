# Decisions Log - v3

## Initial decisions
- The project remains free-system by default, with Whisper/faster-whisper as the baseline option.[file:24]
- AssemblyAI is an optional provider for faster transcripts and should be selected through env config.
- The current hardcoded free-user limit of 2 should become an env-controlled value.[file:19][file:23]
- The product workflow changes from multiple styles + one language to one style + multiple languages.[file:19][file:32]
- Burned-caption video output is mandatory and should be treated as a first-class artifact.[file:25][file:26]
- The baseline should not require a paid provider for first-run functionality.
- Provider selection should be centralized and not spread across route handlers.
