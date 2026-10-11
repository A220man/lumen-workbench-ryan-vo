# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

continue-implementation

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

### continue-implementation — Complete product baseline: version sync, version metadata, and release readiness

Status: done

Acceptance:
- All version references synchronized to 1.20.0 across VERSION, pyproject.toml, package.json, portfolio.json, README
- Portfolio status updated to active with descriptive AI/ML workflow summary
- README work-in-progress banner removed
- All backend tests pass (47)
- All frontend tests pass (20)
- Frontend build succeeds

Implementation: `pyproject.toml`, `frontend/package.json`, `portfolio.json`, `README.md`, `VERSION`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `backend/tests/test_auth.py`, `frontend/tests/import-analysis.test.tsx`

