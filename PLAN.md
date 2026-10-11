# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

system-telemetry-and-missing-library-resolution

## Roadmap

### complete-test-baseline-and-ci — Complete test baseline, Docker configuration, and CI workflow

Status: done

Acceptance:
- Preflight passes cleanly with zero missing files and source within budget
- CI workflow updated to run without pushing to external registries
- At least 12 backend pytest tests covering domain engine, auth, and API workflows
- At least 3 frontend vitest tests covering user-visible UI components

Implementation: `backend/Dockerfile`, `frontend/Dockerfile`, `.github/workflows/ci.yml`, `backend/tests/test_api_endpoints.py`, `backend/tests/test_auth.py`, `backend/tests/test_domain_engine.py`

Tests: `backend/tests/test_api_endpoints.py`, `backend/tests/test_auth.py`, `backend/tests/test_domain_engine.py`, `frontend/tests/dashboard.test.tsx`, `frontend/tests/profile.test.tsx`, `frontend/tests/evaluations.test.tsx`

### system-telemetry-and-missing-library-resolution — System telemetry, missing library blocker resolution, and UI wiring

Status: done

Acceptance:
- System telemetry endpoints (/stats and /analytics) return live aggregate metrics and per-library breakdown
- Missing system module libSceXml is recognized by domain engine as missing-module blocker (issue #2591)
- Access tokens kept strictly in memory without localStorage persistence per owned-app contract
- Frontend routing wires Dashboard, EvaluationTable, StatusPanel, AnalyticsPanel, and ProfilePanel with live API client
- All 22 backend pytest tests and 10 frontend vitest tests pass cleanly with zero deprecation warnings

Implementation: `backend/app/api/router.py`, `backend/services/export_db.py`, `backend/app/main.py`, `backend/core/db.py`, `frontend/src/api.ts`, `frontend/src/context.tsx`, `frontend/src/App.tsx`, `frontend/src/layout.tsx`

Tests: `backend/tests/test_api_endpoints.py`, `backend/tests/test_domain_engine.py`, `frontend/tests/status.test.tsx`, `frontend/tests/analytics.test.tsx`

### adversarial-dataset-expansion — Adversarial dataset generation and graphics driver module resolution

Status: planned

Acceptance:
- Expand adversarial generator with synthetic boundary imports for libSceAgcDriver and libSceVideoOut
- Report stress-test stability scores against host export boundaries

