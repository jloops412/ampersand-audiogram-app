# Processing Router V0

**Status:** Implemented shadow planner; no production audio changes

**Issue:** #23

**Router algorithm:** `0.1.0`

**Media worker:** `0.5.0`

**Contract package:** `0.7.0`

**Runtime/cost:** local CPU, linear timeline memory, $0 external API cost

## Purpose

Processing Router V0 turns a versioned Semantic Audio Map and immutable recipe into an explicit regional
`ProcessingPlan`. It replaces the former one-region “protect everything pending router” placeholder with explainable
protection, bypass, deterministic-filter candidate, admitted-denoise candidate, and Leveler-eligibility decisions.

The router does not process samples. Every V0 region and decision carries `planning_only=true`; the report carries
`production_audio_changed=false`. The normal pipeline still renders only the separately approved two-pass final
loudness master. Proposed cleanup and Leveler stages remain shadow-only until their own listening and admission gates
pass.

## Inputs and artifacts

| Input/artifact | V0 role |
|---|---|
| `semantic-map-v0.json` | Full-coverage content, confidence, conflict, overlap, and defect probabilities |
| `recipe.json` | Immutable processing permissions, including whether neural processing is allowed |
| `router-settings.json` | Complete threshold, transition, processor-admission, and conservative filter snapshot |
| `ProcessingRouteOverride[]` | Optional immutable safe-only protect/bypass intervals |
| `processing-plan.json` | Ordered, contiguous, full-coverage downstream route contract |
| `processing-router-report.json` | Machine-readable decisions, reasons, fallbacks, warnings, hashes, and action counts |

The pipeline writes all four JSON artifacts beside the existing Semantic Map, Leveler, master, and report artifacts.
`processing-router-v0-shadow` is a distinct job step with its own deterministic input/output hashes and
`applied_to_audio=false` metric.

## Conservative policy

Router precedence is deterministic. A safe user override wins first; then conflicts and preservation rules; then
unsupported-damage guards; then bounded processor candidates.

| Evidence | V0 route |
|---|---|
| User protect/bypass override | Exact reversible no-op interval |
| Conflict, music, ambience, mixed, protected, or uncertain content | `protect` with `processor:no-op-v0` |
| Silence or explicit Semantic Map no-op | `bypass` with `processor:no-op-v0` |
| Eligible speech without region-level music evidence | `protect` and missing-evidence warning |
| Speech over music, excessive ambience, or overlap | `protect` |
| Clipping, strong reverb, or severe bandwidth-limit evidence | `bypass` and unsupported-path warning |
| Confident hum | bounded hum-notch candidate when deterministic filters are enabled |
| Confident rumble | 40–100 Hz/12 dB-octave high-pass candidate when deterministic filters are enabled |
| Eligible noisy speech | admitted denoiser only when settings name exact processor/model-manifest IDs and the recipe admits both neural processing and that model |
| Eligible clean speech or safe denoise fallback | separate Adaptive Leveler shadow candidate |

Only one regional action can be selected for a segment, so incompatible processor combinations cannot be hidden in a
V0 plan. Every non-no-op route declares `processor_id`, `fallback_processor_id`, `reason_code`, human reason,
confidence, parameters, warnings, transition duration, and source. Deterministic filter and denoise parameters are
proposals; no wet signal enters the production master.

## Missing evidence fails closed

The current local bootstrap VAD intentionally does not claim reliable music classification. Its pipeline Semantic Map
therefore has no region-level music probability, and Router V0 protects otherwise eligible speech instead of assuming
that speech has no music beneath it. Synthetic and future admitted-provider maps can exercise the richer branches, but
absence is never interpreted as a zero probability.

Hum/rumble/denoise routes likewise require normalized Semantic Map probabilities. Numeric features retained only in a
provider-native audit artifact do not silently become router authority.

## Settings and reusable templates

`ProcessingRouterSettings` is the resolved run snapshot, not a global mutable preference. It records:

- speech/content confidence and preservation thresholds;
- clipping, reverb, bandwidth, noise, hum, and rumble thresholds;
- transition duration;
- deterministic-filter enablement and bounded high-pass parameters;
- whether speech denoise is enabled, its exact admitted processor/model-manifest IDs, and conservative strength;
- the invariant that music evidence is required before processing.

These fields fit the Studio settings/template architecture: a user may select rich settings for one production or
reuse a versioned template, while the run retains its immutable resolved settings and hash. Changing a template later
cannot rewrite a historical route plan.

## Safe overrides

V0 accepts only `protect` and `bypass` user overrides. It deliberately cannot force an unadmitted processor or activate
neural/generative work. Overrides may start/end inside a Semantic Map region; the planner deterministically splits the
region at those half-open boundaries. Duplicate IDs, overlaps, and out-of-duration intervals fail validation. Removing
the override and rebuilding produces the original automatic plan without mutating the Semantic Map.

## Determinism and validation

Plan identity derives from canonical hashes of the Semantic Map, recipe, complete router settings, ordered overrides,
run ID, and algorithm version. Region/decision IDs derive from the plan and exact half-open segment. Same inputs produce
byte-identical plans and reports.

Contracts reject:

- empty, gapped, overlapping, out-of-order, duplicate-ID, or partial-coverage processing plans;
- overlapping/out-of-duration overrides;
- enabled speech denoise without admitted processor and model-manifest IDs;
- action counts that do not exactly match report decisions;
- unknown fields, invalid probabilities, invalid transitions, or non-finite numerics.

Planning is O(S + O) output memory for `S` emitted segments and `O` overrides. The automated one-hour control creates
3,600 contiguous route decisions twice and verifies deterministic full coverage without recorded media.

## Current evidence and open gates

Automated tests cover clean speech, silence, music, uncertain content, ordinary noise fallback, hum, rumble, clipping,
missing music evidence, neural recipe admission, safe override splitting/reversal, invalid configuration, overlapping
overrides, abrupt adjacent policy changes, deterministic pipeline artifacts, and one-hour planning.

Issue #23 remains open. Production routing still requires:

- admitted processor manifests and regional execution adapters from #7;
- rights-cleared listening for each filter/denoise use case and boundary crossfade;
- clean-input, protected music/ambience, pumping, timbre, and artifact evidence;
- calibrated hum/rumble classifiers and hum-frequency evidence before active filters;
- tested user-override persistence through the durable production workflow;
- representative long-form render/runtime/recovery evidence;
- an explicit promotion ADR for every active processor path.

Rollback is removal of the shadow-router step or selection of the all-protect plan. Current production master bytes do
not depend on a Router V0 regional candidate, and no Google-hosted Studio or deployment configuration changes in this
checkpoint.
