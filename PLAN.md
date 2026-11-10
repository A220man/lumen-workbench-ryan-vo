# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

import-analysis-list-endpoint

## Roadmap

### save-import-analysis-endpoint — Implement save import analysis endpoint

Status: done

Acceptance:
- POST /imports/analyze/save endpoint saves import analysis reports to database
- Frontend "Save Analysis" button works end-to-end
- All backend tests pass (57)
- All frontend tests pass (25)
- Frontend builds successfully

Implementation: `backend/app/api/router.py`, `backend/models/import_record.py`, `backend/schemas/import_analysis.py`, `backend/schemas/__init__.py`

Tests: `backend/tests/test_api_endpoints.py (23 tests)`, `backend/tests/test_auth.py (7 tests)`, `backend/tests/test_domain_engine.py (33 tests)`, `frontend/tests/import-analysis.test.tsx (3 tests)`

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- Run checks, fix failures, and implement the next planned feature

### import-analysis-list-endpoint — Implement list saved import analyses endpoint

Status: done

Acceptance:
- GET /imports/analyze/saved endpoint lists all saved import analysis records
- Frontend shows saved analyses in Import Analysis page
- Backend tests pass (58)
- Frontend tests pass (26)
- Frontend builds successfully

Implementation: `backend/app/api/router.py`, `backend/tests/test_api_endpoints.py`, `frontend/src/api.ts`, `frontend/src/components/import-analysis.tsx`, `frontend/tests/import-analysis.test.tsx`

Tests: `backend/tests/test_api_endpoints.py (24 tests)`, `backend/tests/test_auth.py (7 tests)`, `backend/tests/test_domain_engine.py (33 tests)`, `frontend/tests/import-analysis.test.tsx (4 tests)`

### import-analysis-delete-endpoint — Implement delete saved import analysis endpoint

Status: planned

Acceptance:
- DELETE /imports/analyze/saved/{id} endpoint deletes a saved import analysis record
- Frontend "Delete" button works for saved analyses
- Backend tests pass
- Frontend tests pass

