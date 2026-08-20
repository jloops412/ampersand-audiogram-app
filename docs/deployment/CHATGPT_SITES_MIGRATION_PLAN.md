# Deferred ChatGPT Sites and Custom-Domain Release Note

**Status:** Deferred until Ampersand has a working publishable build  
**Last verified:** 2026-08-18  
**Authority:** [ADR-0007](../decisions/ADR-0007-BUILD-FIRST-HOSTING-DEFERRED.md)

## Owner intent

After the actual Ampersand product is working, publish its compatible web experience through ChatGPT Sites and connect the owner's existing domain.

This is a **release task**, not a current engineering epic, compatibility proof, Google-host audit, data-platform decision, or prerequisite for the engine and Studio.

## Portability requirements that remain relevant during the build

- keep the web UI separate from heavy media workers;
- keep configuration environment-based;
- never commit secrets;
- keep control APIs and domain schemas provider-neutral;
- upload large media directly/resumably where needed;
- do not use the browser as the authoritative long-form processor or renderer;
- tie release artifacts to reviewed Git commits.

## Later release checklist

Create a fresh GitHub issue when the first publishable build defined in `docs/build/IMPLEMENTATION_EXECUTION_PLAN.md` exists.

That issue should then:

1. publish the compatible web application to ChatGPT Sites;
2. configure required environment values and secrets;
3. run the completed product's smoke tests;
4. record the exact domain and DNS provider;
5. connect the domain using the records Sites provides;
6. preserve email-related DNS records;
7. retain the previous deployment as rollback until validation passes;
8. update the active-host documentation.

## Current prohibition

Agents must not spend current product-development time on:

- proving ChatGPT Sites compatibility;
- auditing the current Google host;
- evaluating Sites D1/R2 as canonical product infrastructure;
- DNS planning or changes;
- custom-domain cutover;
- retiring the current host.

Issues #16–#20 were closed because they represented that over-planning. The active work is issue #14 and the build issues it governs.