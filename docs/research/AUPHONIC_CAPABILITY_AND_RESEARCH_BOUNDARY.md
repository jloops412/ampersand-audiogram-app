# Auphonic Capability and Research Boundary

**Status:** Accepted governance rule  
**Last verified:** 2026-08-18  
**Owner:** Ampersand program governance

## Purpose

Auphonic is a valuable source of public product and workflow research because its documentation describes a mature automatic audio-production system. It is also a commercial service with explicit contractual restrictions on how its services, outputs, derivatives, and learnings may be used.

This document defines the boundary between legitimate public capability research and prohibited competitive benchmarking or reverse engineering.

This is an engineering governance document, not legal advice. A qualified attorney should review the terms before commercial launch or any proposed use near the boundary.

## Hard boundary from Auphonic's current terms

Auphonic's current Terms of Service state that users must not use Auphonic services, outputs, derivatives, data, labels, evaluations, know-how, insights, or learnings derived from them to develop, train, evaluate, benchmark, or improve a model, algorithm, or system; reverse engineer underlying algorithms or models; or build a competing product. The terms further state that outputs or derivatives may not be used as reference material, ground truth, evaluation material, design input, or a quality target, whether through machine learning, human analysis, or manual tuning.

Official source:

- [Auphonic Terms of Service](https://us.auphonic.com/terms_of_service)

The terms invite parties with a potentially covered use case to contact Auphonic support for a tailored arrangement.

## Ampersand rule

Unless Ampersand has a written agreement from Auphonic that expressly permits the intended activity:

### Do not

- process test material through Auphonic for Ampersand research;
- compare Auphonic output with Ampersand output;
- run blind Auphonic-versus-Ampersand tests;
- infer leveler gain curves, attack/release behavior, denoise thresholds, filters, model routing, or other internal behavior from Auphonic outputs;
- use Auphonic output as a reference, gold master, quality target, regression target, training example, preference example, label, metric input, or design input;
- manually tune Ampersand toward an Auphonic output;
- retain an Auphonic-derived engineering corpus;
- use Auphonic API output in the Ampersand Audio Lab;
- describe Ampersand as reproducing, reverse engineering, or cloning Auphonic algorithms;
- allow contributors or automated agents to bypass this restriction through personal accounts or untracked experiments.

### Permitted planning inputs under this project policy

- publicly accessible Auphonic product pages, help documentation, API schemas, changelog entries, and technical articles;
- independent audio standards and research papers;
- open-source projects and models used under their applicable licenses and terms;
- independently created test signals;
- owned or rights-cleared recordings;
- independently commissioned human-engineer reference mixes;
- user research about desired workflows that does not expose or analyze Auphonic outputs;
- general audio-engineering knowledge.

Reading public documentation does not authorize copying proprietary implementations, product expression, trade dress, text, or protected material. Ampersand should use public information only to understand broad capabilities, terminology, user needs, and interoperability expectations, then design an independent system.

## Treatment of the current legacy integration

The existing application proxies user uploads to Auphonic and then feeds returned audio into the browser audiogram workflow.

For V2:

- the legacy Auphonic provider must be isolated from the Audio Lab;
- no legacy output may be added to evaluation data or used to tune Ampersand;
- credentials and historical output must not be migrated into the V2 research environment;
- a future customer-facing Auphonic connector is **not approved** merely because the legacy prototype contains one;
- keeping, removing, or offering any connector requires a separate legal/product decision and, preferably, written clarification from Auphonic;
- V2 architecture must not depend on Auphonic availability.

## Publicly documented capability map

Auphonic's public documentation is useful as a market capability inventory. It currently describes two broad processing modes:

- **Singletrack:** one mono or stereo mixed source;
- **Multitrack:** multiple parallel inputs with joint analysis and automatic mixing behavior.

Auphonic states that both modes analyze content and classify it into small meaningful segments such as speech, music, silence, and different speakers, then apply matching processing. Publicly described capability areas include:

### Analysis and content understanding

- content segmentation;
- speaker and speech/music awareness;
- loudness and peak analysis;
- speech recognition;
- chapters, summaries, shownotes, and metadata generation.

### Singletrack processing

- adaptive leveling;
- short-term dynamics compression;
- loudness normalization;
- true-peak limiting;
- several noise-reduction modes;
- reverb and breath reduction controls;
- adaptive high-pass filtering;
- speaker-aware AutoEQ;
- bandwidth extension;
- Studio Voice beta restoration;
- segment-level processing overrides;
- automatic detection/cutting of silence, fillers, coughs/respiratory sounds, and foreground music.

### Multitrack processing

- cross-track analysis;
- automatic track and speaker leveling;
- dynamics control;
- adaptive gating;
- mic-bleed/crosstalk removal;
- foreground/background classification;
- ducking;
- per-track gain and pan;
- loop/trim behavior;
- master loudness constraints.

### Workflow and output surface

- presets;
- batch processing;
- watch folders and API workflows;
- metadata and chapter handling;
- multiple audio/video output formats;
- transcript, chapter, cut-list, waveform, and production-description outputs;
- external file transfer and publishing targets;
- audiogram and burned-caption styling.

Primary public source:

- [Auphonic Audio Algorithms](https://us.auphonic.com/help/algorithms/index.html)
- [Auphonic Singletrack Algorithms](https://us.auphonic.com/help/algorithms/singletrack.html)
- [Auphonic Multitrack Algorithms](https://us.auphonic.com/help/algorithms/multitrack.html)
- [Auphonic API algorithm schema](https://auphonic.com/api/info/algorithms.json)
- [Auphonic output-file schema](https://auphonic.com/api/info/output_files.json)

## What public documentation does not establish

Public documentation generally does not establish the exact:

- model architectures;
- training data;
- feature representations;
- loss functions;
- classifier thresholds;
- gain-control laws;
- filter coefficients;
- limiter curves;
- model-routing policies;
- processor ordering in every case;
- inference windows or smoothing constants;
- internal quality models.

Ampersand must not fill these gaps by experimentation against Auphonic outputs. It should solve them independently through standards, open research, owned data, original engineering, and documented listening tests.

## Independent evaluation replacement

The earlier concept of using Auphonic as a benchmark is superseded.

Ampersand quality evaluation will instead use:

1. clean, rights-cleared speech references;
2. deterministic synthetic degradations with known ground truth;
3. real-world rights-cleared recordings with documented consent;
4. independent human-engineer masters when a realistic reference is needed;
5. standards-based measurements;
6. human listening protocols;
7. open-source and deterministic baselines whose licenses allow the evaluation;
8. clean-input preservation tests;
9. artifact-specific tests for noise, coloration, discontinuity, reverb, clipping, loudness, and intelligibility.

See [Audio Quality Evaluation Plan](./AUDIO_QUALITY_EVALUATION_PLAN.md).

## Permission path

Auphonic's terms state that potentially covered parties may contact support to discuss a tailored arrangement.

Ampersand may later seek written permission for a narrowly defined evaluation or interoperability purpose. Until such permission is obtained and archived:

- the hard boundary in this document remains in force;
- verbal discussions or informal assumptions are insufficient;
- any permission must identify allowed materials, uses, retention, publication, and derivative learnings;
- the agreement must be reviewed before experiments begin.

## Contributor checklist

Before any experiment involving Auphonic, answer all of the following:

- Does this use an Auphonic service, API, output, derivative, evaluation, label, or learning?
- Could the result influence Ampersand design, tuning, model selection, quality thresholds, or marketing?
- Is there written permission specifically covering the activity?
- Is that permission stored with the project governance records?

If the first or second answer is yes and the third is no, the experiment must not proceed.

## Change control

This boundary must be re-verified against Auphonic's current Terms of Service:

- before any commercial launch;
- before adding or retaining an Auphonic connector;
- before any proposed comparative claim;
- after notice of an Auphonic terms change;
- at least once per major release cycle.

A change to this policy requires a superseding ADR and documented legal review.