# Changelog

## 1.38.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.37.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.36.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.36.1 — edge case fix

### Fixed
- **Audit log email default**: `delete_saved_import_analysis` endpoint now uses `user.get('email', 'unknown')` instead of `user.get('email')` to prevent audit log entries from showing "None" when the user email is unexpectedly missing. This aligns with the existing pattern in `save_import_analysis` which already had the default.

## 1.35.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.34.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **List Saved Import Analyses Endpoint**: Implemented `GET /api/v1/imports/analyze/saved` endpoint to retrieve all saved import analysis records from the database, ordered by most recent first. The frontend Import Analysis page now displays a "Saved Analyses" table showing title name, status, analyzed by, date, and a Load button to reload any previous analysis.
- **Frontend Integration**: Added `listSavedImportAnalyses` API function in `frontend/src/api.ts`, updated `ImportAnalysis` component with saved analyses state, fetch-on-mount effect, and auto-refresh after saving new analyses.

### Tests
- Backend: 58 tests pass (added `test_import_analysis_list_endpoint` in `backend/tests/test_api_endpoints.py`)
- Frontend: 26 tests pass (added saved analyses rendering test in `frontend/tests/import-analysis.test.tsx`)
- Frontend TypeScript build succeeds (tsc + vite build)
## 1.33.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.33.1 — edge case fix

### Fixed
- **Audit log email default**: `delete_saved_import_analysis` endpoint now uses `user.get('email', 'unknown')` instead of `user.get('email')` to prevent audit log entries from showing "None" when the user email is unexpectedly missing. This aligns with the existing pattern in `save_import_analysis` which already had the default.

## 1.32.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.31.0 — work-in-progress checkpoint

### Added
- **Save Import Analysis Endpoint**: Implemented `POST /api/v1/imports/analyze/save` endpoint to persist import analysis reports to the database. The frontend "Save Analysis" button in the Import Analysis page now works end-to-end, storing the full resolution report (imports, coverage, blockers, advisory) as JSON in the `import_records` table.

### Tests
- All 55 backend tests pass
- All 25 frontend tests pass
- Frontend builds successfully
Partial code published for continued development. Known issues: STATUS.md.

## 1.30.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.29.0 — advisory `generate_advisory` fix and version sync

### Fixed
- **Broken LLM advisory path**: `POST /imports/analyze?explain=true` imported a `generate_advisory` function that did not exist in `services/advisory.py`, causing an `ImportError` at runtime. Added the `generate_advisory` async wrapper (builds advisor from operator settings, calls `explain_imports`) and fixed the router to `await` it. When `LLM_API_KEY` is absent, the endpoint returns a clear "LLM advisory disabled" notice grounded in actual configuration rather than crashing.
- **Version desynchronization**: `pyproject.toml` and `frontend/package.json`/`package-lock.json` were pinned to 1.26.0 while `VERSION` was 1.29.0. Synchronized all metadata to 1.29.0.
