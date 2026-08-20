# Historical ChatGPT Sites Migration Note

**Status:** Superseded; retained for history

**Last verified:** 2026-08-20
**Current authority:** [ADR-0009](../decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)

## Owner intent

The owner previously intended to publish Ampersand through ChatGPT Sites. On 2026-08-20 the owner chose to preserve the already deployed Google-hosted site instead.

Do not execute the former Sites migration. Use the [Google V1 beta publish guide](./GOOGLE_V1_BETA_PUBLISH.md) for the
fresh Cloud Run baseline and the [Google hosting plan](./GOOGLE_HOSTING_INTEGRATION_PLAN.md) for separately approved
legacy-resource cleanup under ADR-0011.

## Portability requirements that remain relevant during the build

- keep the web UI separate from heavy media workers;
- keep configuration environment-based;
- never commit secrets;
- keep control APIs and domain schemas provider-neutral;
- upload large media directly/resumably where needed;
- do not use the browser as the authoritative long-form processor or renderer;
- tie release artifacts to reviewed Git commits.

## Historical release checklist

The following checklist is preserved only to explain the superseded plan:

That issue should then:

1. publish the compatible web application to ChatGPT Sites;
2. configure required environment values and secrets;
3. run the completed product's smoke tests;
4. record the exact domain and DNS provider;
5. connect the domain using the records Sites provides;
6. preserve email-related DNS records;
7. retain the previous deployment as rollback until validation passes;
8. update the active-host documentation.

## Current rule

Agents must not:

- proving ChatGPT Sites compatibility;
- retire or mutate the current Google host;
- evaluating Sites D1/R2 as canonical product infrastructure;
- DNS planning or changes;
- custom-domain cutover;
- retiring the current host.

ADR-0009 and issue #31 govern the active direction.
