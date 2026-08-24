# Audiogram Visual System V1.1

**Status:** Implemented issue #27 checkpoint

**Date:** 2026-08-24

**Authority:** ADR-0012, `packages/render-spec/README.md`, and the immutable `AudiogramSettings` contract

## Product outcome

Audiogram Studio now starts with six complete looks instead of requiring users to assemble a design from raw controls.
Choosing a look writes ordinary versioned render fields; subsequent customization remains explicit, portable, and
reproducible. No browser-only theme identifier controls production output.

V1.1 adds:

- Ampersand Signature, Clean Editorial, Neon Pulse, Wedding Glow, Bold Social, and Midnight Broadcast looks;
- animated linear and radial color backgrounds plus existing solid, image, and looping-video modes;
- background blur, dim, and vignette treatments;
- classic waveform plus frequency-bar and frequency-dot visualizers;
- controllable glow and none/glass/outline/accent visualizer plates;
- sans, serif, and mono bundled typography;
- top/center/bottom text placement, deterministic multiline wrapping, and clean/shadow/glass/accent panels;
- an animated Studio preview driven by the same immutable fields as the server render.

## Deterministic renderer mapping

| Contract area | Authoritative FFmpeg execution |
|---|---|
| Solid/gradient background | `color` or `gradients` source |
| Image/video background | fixed cover/contain scale and crop/pad; video loops without contributing audio |
| Blur/dim/vignette | `gblur`, `drawbox`, and `vignette` |
| Waveforms | `showwaves` |
| Frequency visualizers | `showfreqs` with fixed window, averaging, and log frequency scale |
| Glow | alpha-preserving split, `gblur`, and deterministic overlay |
| Visualizer/text plates | fixed-coordinate `drawbox` layers |
| Type | installed DejaVu Sans, Serif, or Sans Mono; bold headline and regular subtitle |
| Text wrapping | normalized 160-character copy wrapped from canvas width and selected point size |
| Delivery | H.264/AAC MP4 with the selected dimensions, frame rate, and quality tier |

The renderer continues to use one FFmpeg process, one mastered WAV audio input, and no network or hosted visual service.
The CSS preview is compositionally representative; it does not claim frame-identical audio animation. Export remains
authoritative.

## Compatibility and migration

- The backend reads both `spec_version` `1.0` and `1.1`; V1.1 fields have deterministic defaults.
- Browser-local templates are additively migrated to V1.1 when loaded. Legacy cleanup settings retain their existing
  manual-mode migration.
- Built-in Studio templates advance to immutable version 3 because their resolved audiogram defaults changed.
- Historical production settings and hashes are not rewritten.
- Image/video validation and direct-upload privacy boundaries are unchanged. Gradient and solid backgrounds create no
  additional uploaded asset.

## Runtime and cost notes

Gradient sources, blur, glow, frequency analysis, higher resolutions, and 60 fps increase CPU work. Draft/standard/high
remain user-visible execution choices, and the private beta still serializes productions on its single worker. V1.1
adds no package, font download, model, external API, or license. The deployed `fonts-dejavu-core` package remains the
controlled typography source.

## Security and privacy impact

No new credential, network destination, public URL, or user-data class is introduced. Background media stays private,
object-scoped, and deletion-coupled to the production. FFmpeg receives only local/mounted source, master, background,
and temporary text files. Temporary text files are removed in the renderer's `finally` path.

## Rollback

Cloud Run may roll back to the immediately preceding reviewed revision. A pre-V1.1 revision cannot validate a newly
created V1.1 settings payload, so those productions should remain preserved and be retried after restoring V1.1; do not
rewrite their settings as V1.0. Source and completed artifacts remain immutable throughout rollback.

## Next visual slices

- timed word/cue captions and active-word highlighting;
- clip-range selection for short social outputs;
- separate logo/brand-mark assets and workspace brand kits;
- licensed workspace font assets;
- richer motion/layer composition through the planned render worker;
- closer automated preview/export frame comparison after the shared frame renderer is admitted.
