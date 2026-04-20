# Requirements Baseline

## Functional requirements
- User can register and log in.[file:19][file:20][file:30][file:33]
- User can upload supported video files for processing.[file:19][file:32]
- System can extract audio from uploaded video.[file:19][file:26]
- System can produce timestamped transcript segments.[file:28]
- User can review and edit transcript segments.
- System can apply caption styles to transcript content.[file:25][file:32]
- System can generate SRT output.[file:19][file:25]
- System can generate preview video output with captions.[file:26][cite:5]
- User can access processing history.[file:19][file:31]
- Admin can view platform usage and activity.[file:19][file:29]

## Non-functional requirements
- Maintainability through modular services.
- Reliability through explicit workflow states.
- Usability through visible progress and error messaging.[file:32]
- Traceability from requirement to phase and file.
- Incremental migration without unnecessary rewrite.

## Out-of-scope until later
- Full real-time collaboration.
- Complex team workspaces.
- Deep analytics redesign.
- Full microservice split.
