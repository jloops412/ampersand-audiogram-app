# ADR-0009: Keep Google Hosting and Make Studio Settings/Template-Driven

- **Status:** Template/settings direction accepted; deployment-preservation direction superseded by ADR-0011
- **Date:** 2026-08-20
- **Decision owners:** Ampersand product and engineering
- **Tracks:** GitHub issue #31

## Context

Ampersand already has a deployed Google-hosted web surface. The owner has decided to continue using that infrastructure instead of moving production hosting to OpenAI Sites. The exact Google product, project, deployment workflow, storage boundary, secrets, and operational setup have not yet been inspected in this implementation workspace.

The current Studio shell also presents four production intents. They are useful shortcuts, but they do not satisfy the product goal: users need rich supported settings for each production and reusable templates that preserve repeatability.

## Decision

### Deployment destination

The existing Google deployment remains Ampersand's production web destination.

- Do not retire, replace, publish to, or otherwise mutate it until the owner connects the relevant Google account/project at the integration stage.
- Do not infer whether it uses Firebase Hosting, App Hosting, Cloud Run, Google AI Studio, or another Google service from old source files or naming alone.
- Preserve the OpenAI Sites checkpoint as a non-production design/reference artifact.
- Keep GitHub as the durable implementation and planning authority.
- Keep the Studio/control API and media/render workers separated by versioned Ampersand contracts so the heavy engine remains independently deployable and hosting-provider-neutral.

The later Google integration begins with read-only discovery of the existing deployment, then a documented staging/publish/rollback path. Custom-domain work remains deferred until the product is release-ready.

### Studio configuration

The four intent choices may select recommended defaults, but they are not the complete product surface. The Studio must provide:

- a template choice or blank/default starting point;
- safe, outcome-oriented settings for every supported processing stage;
- a discoverable advanced/expert view;
- per-production overrides before a run begins;
- a review of the exact resolved settings that will run;
- an immutable resolved-settings snapshot attached to every run;
- plain-language descriptions, units, ranges, warnings, availability, and contraindications derived from contract metadata;
- no control that lacks an admitted engine/recipe field.

### Template and run semantics

Ampersand distinguishes four concepts:

1. **RecipeVersion** — immutable, engine-admitted processing graph and safety policy.
2. **StudioTemplate** — mutable workspace catalog identity such as “Joshua's wedding dialogue.”
3. **StudioTemplateVersion** — immutable reference to a recipe version plus validated settings/render/export choices.
4. **ResolvedProductionSettings** — fully expanded immutable snapshot created from recipe defaults, template version, and per-run overrides.

Editing a template creates a new template version. It never changes an existing run. A production may override a template without changing it; “save as template” is an explicit action. Built-in templates are versioned and copied before user customization.

## Consequences

### Positive

- deployment work builds on the owner's existing investment;
- the engine remains portable and independently operable;
- users can choose simple recommended defaults or precise supported settings;
- template reuse does not sacrifice run reproducibility;
- settings become traceable inputs to caching, reports, quality evaluation, and rollback.

### Costs and risks

- exact deployment mechanics remain unknown until the Google connection stage;
- the Studio needs schema-driven control metadata and settings migrations;
- template lifecycle, validation, authorization, archive/restore, and import/export require durable contracts;
- more options increase misuse risk, so recipe safety ranges and clear defaults remain authoritative.

## Integration gate

When the owner says the product is ready for Google integration and connects the relevant account/project:

1. identify the exact deployment target, source branch, build command, runtime, storage, identity, and region;
2. inventory environment variables and secret names without exposing values;
3. map the existing web/upload/control behavior to Ampersand contracts;
4. establish a staging or preview publish from a reviewed Git commit;
5. add smoke checks, logs/alerts, rollback, and deletion/retention verification;
6. publish production only with an explicit rollback target;
7. connect the custom domain only after release-readiness checks pass.

## Supersession

ADR-0008 remains historical evidence for the web/worker separation and the Sites checkpoint. This ADR supersedes its selection of OpenAI Sites as the active production host. ADR-0006 and ADR-0007 are also historical where they name ChatGPT/OpenAI Sites as the intended destination.

On 2026-08-20, the owner selected the new GitHub-to-Cloud Run build as a fresh baseline and deprecated the older
deployments. ADR-0011 supersedes this ADR's requirement to preserve and integrate the pre-existing Google deployment;
the rich settings, immutable resolved runs, and reusable template decisions remain accepted.
