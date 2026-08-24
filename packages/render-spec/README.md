# Audiogram render-spec boundary

`AudiogramSettings` is the provider-neutral, immutable render specification used by Studio templates, resolved
production settings, processing reports, and the FFmpeg renderer. `spec_version: "1.1"` is an additive extension of
the still-readable `1.0` contract and currently executes:

- 1:1, 4:5, 9:16, and 16:9 canvases at fixed delivery dimensions;
- solid color, animated linear/radial gradient, uploaded image, or silently looping uploaded video backgrounds;
- cover/contain fitting plus a deterministic contrast overlay;
- background blur and vignette treatments;
- line, mirrored, bar, point, frequency-spectrum, and dotted-frequency visualizers;
- linear, square-root, cube-root, and logarithmic amplitude display;
- waveform position, width, height, opacity, color, glow, and plate treatment;
- headline/subtitle copy with deterministic wrapping, sizes, alignment, placement, panel treatment, accent color, and
  bundled sans/serif/mono typography;
- six Studio-authored complete looks that resolve into the same executable fields rather than a separate opaque theme;
- 24, 30, or 60 fps and draft, standard, or high H.264 render tiers.

The browser preview consumes this same specification and is explicitly an animated layout preview; FFmpeg remains
authoritative for audio-reactive frames and encoded output. Source audio is never taken from background video. Timed
captions, clip selection, logos, workspace font assets, and exact preview/export frame parity require a later spec
version. See [Audiogram Visual System V1.1](../../docs/architecture/AUDIOGRAM_VISUAL_SYSTEM_V1_1.md).
