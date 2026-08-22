# Audiogram render-spec boundary

`AudiogramSettings` is the provider-neutral, immutable render specification used by Studio templates, resolved
production settings, processing reports, and the FFmpeg renderer. `spec_version: "1.0"` currently executes:

- 1:1, 4:5, 9:16, and 16:9 canvases at fixed delivery dimensions;
- solid color, uploaded image, or silently looping uploaded video backgrounds;
- cover/contain fitting plus a deterministic contrast overlay;
- line, mirrored, bar, and point waveform primitives;
- linear, square-root, cube-root, and logarithmic amplitude display;
- waveform position, width, height, opacity, and color;
- headline/subtitle copy, sizes, alignment, and color;
- 24, 30, or 60 fps and draft, standard, or high H.264 render tiers.

The browser preview consumes this same specification and is explicitly a layout preview; FFmpeg remains authoritative
for animated frames and encoded output. Source audio is never taken from background video. Captions, clip selection,
font assets, richer compositing/motion primitives, and exact preview/export frame parity require a later spec version.
