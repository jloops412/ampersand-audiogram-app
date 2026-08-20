# Studio web boundary

This directory is the active Studio source for the new GitHub-to-Cloud Run baseline in Google Cloud project `gen-lang-client-0564514768`. Older deployments are deprecated and the OpenAI Sites checkpoint is reference-only. Legacy resource deletion remains a separate, explicit cleanup operation after the new service is verified.

The Studio consumes versioned JSON Schemas from `packages/contracts/schema` and delegates native media work to independently deployable workers.

The Studio must render its Basic/Advanced settings from admitted control definitions, resolve every run to an immutable settings snapshot, and support reusable immutable-versioned workspace templates. Four intent cards may choose defaults but are not the entire configuration experience.
