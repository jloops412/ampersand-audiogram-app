# Studio web boundary

The active production destination is the owner's existing Google-hosted deployment. Until the owner connects the relevant Google account/project, this directory is the canonical future Studio source/client-adapter boundary and must not guess or mutate the live deployment. The OpenAI Sites checkpoint is a non-production reference artifact.

The Studio consumes versioned JSON Schemas from `packages/contracts/schema` and delegates native media work to independently deployable workers.

The Studio must render its Basic/Advanced settings from admitted control definitions, resolve every run to an immutable settings snapshot, and support reusable immutable-versioned workspace templates. Four intent cards may choose defaults but are not the entire configuration experience.
