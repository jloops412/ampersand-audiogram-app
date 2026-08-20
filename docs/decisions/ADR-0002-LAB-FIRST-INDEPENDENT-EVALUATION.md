# ADR-0002: Lab-First Development and Independent Evaluation

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owners:** Ampersand product, audio quality, and engineering

## Context

Ampersand's highest-risk promise is audio quality, not UI implementation. Open-source processors and recent models can be integrated quickly, but published demos and objective benchmark scores do not establish that they improve Ampersand's intended real-world recordings.

An earlier concept proposed comparing Ampersand outputs directly with Auphonic and characterizing Auphonic through controlled input/output experiments. Auphonic's current Terms of Service expressly restrict using its services, outputs, derivatives, evaluations, know-how, insights, or learnings to develop, train, evaluate, benchmark, or improve models/algorithms/systems or build a competing product. The terms also prohibit using outputs as reference material, ground truth, design input, or a quality target without a tailored arrangement.

## Decision

Build the **Ampersand Audio Lab before substantial Studio polish** and evaluate Ampersand independently.

The Lab will use:

- owned or rights-cleared clean references;
- deterministic synthetic degradations;
- consented real-world recordings;
- independent human-engineer reference masters where needed;
- open/permitted baselines;
- standards-based measurements;
- blinded human listening;
- clean-input preservation tests.

Auphonic services and outputs are excluded from Ampersand research, evaluation, training, tuning, model selection, and design input unless Ampersand first obtains written permission that specifically covers the activity.

## Consequences

### Positive

- tests the actual product promise before UI investment obscures risk;
- creates independent intellectual property and defensible quality evidence;
- avoids dependence on a competitor's service or output;
- supports repeatable model/recipe promotion and regression;
- exposes clean-audio damage and long-form artifacts early;
- creates a reusable quality asset for every future algorithm.

### Negative

- customer-facing visual progress begins more slowly;
- corpus rights, listening tests, and experiment infrastructure require real work;
- independent engineer references may cost money;
- results may reject exciting models or narrow the product scope;
- human listening is slower than relying on a metric leaderboard.

## Alternatives considered

### Build the Studio first and tune by user feedback

Rejected. Private user feedback without controlled versions, references, loudness matching, and artifact labels is too noisy to establish safe default processing.

### Select models by paper/README benchmark scores

Rejected. Metrics, data distributions, checkpoints, and target tasks differ. A strong published average may hide unacceptable artifacts on Ampersand material.

### Use Auphonic as the quality target

Rejected absent written permission. This conflicts with the current service terms and would also make Ampersand's engineering direction dependent on an opaque competitor.

### Use only objective metrics

Rejected. Objective metrics are diagnostic and often task-limited. Human listening remains the final gate.

## Required follow-up

- implement [Audio Quality Evaluation Plan](../research/AUDIO_QUALITY_EVALUATION_PLAN.md);
- enforce [Auphonic Capability and Research Boundary](../research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md);
- create rights and consent manifests before adding corpus media;
- separate Lab storage/identities from production;
- build loudness-matched blinded listening modes;
- create promotion reports and ADRs for every default processor/recipe;
- ensure production code cannot load unapproved Lab-only manifests.

## Review trigger

Review this ADR if:

- Auphonic grants a written tailored arrangement;
- the evaluation standard materially changes;
- Ampersand begins training models;
- a new user-data contribution program is proposed;
- human evaluation becomes impractical at intended scale.

Any change must preserve independent quality evidence and privacy/rights controls.