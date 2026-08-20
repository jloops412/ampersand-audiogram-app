# Legacy prototype quarantine

The original React/Vite audiogram prototype remains at the repository root until issue #3 completes the permanent `legacy-audiogram-v0` tag and an explicitly reviewed structural move. `src/` and `backend/` are historical only.

V2 code must not import the legacy Auphonic proxy, Auphonic client, browser MediaRecorder renderer, or legacy React state model. CI enforces this boundary.
