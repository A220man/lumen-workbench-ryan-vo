# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

advisory-ui-integration

## Roadmap

### advisory-ui-integration — Integrate LLM advisory explanations into Import Analysis UI

Status: done

Acceptance:
- Add Generate advisory explanation checkbox to Import Analysis form
- Pass explain parameter to /imports/analyze endpoint
- Display advisory explanation in results when available
- All existing tests pass
- Frontend build succeeds

Implementation: `frontend/src/api.ts`, `frontend/src/components/import-analysis.tsx`

Tests: `frontend/tests/import-analysis.test.tsx`

### continue-implementation — Continue implementation and resolve known failures

Status: planned

Acceptance:
- Run checks, fix failures, and implement the next planned feature

