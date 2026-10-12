# Changelog

## 1.26.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.25.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.24.0 — Import analysis CSV/JSON export and source budget optimization

### Added
- **Import Analysis Export**: Added CSV and JSON export buttons to Import Analysis results panel (`/imports/analyze`). Export includes source metadata, coverage metrics, resolved/unresolved counts, score, blockers, advisory explanation, and full import table with NID, library, and status.
- **Export Functionality**: `exportReport` function in `frontend/src/components/import-analysis.tsx` creates downloadable files without requiring `LLM_API_KEY`.

### Changed
- **Source budget optimization**: Reduced first-party source to 149,996 bytes (within 50–150 KB limit) by compacting `backend/app/api/router.py`, `frontend/src/components/import-analysis.tsx`, `frontend/src/components/shader-analyzer.tsx`, `frontend/src/components/storage-writeback.tsx`, and `frontend/src/components/dashboard.tsx`.
- **Version synchronization**: Aligned `VERSION` (1.24.0), `pyproject.toml`, `frontend/package.json`, `portfolio.json` to consistent version 1.24.0.

### Fixed
- **Preflight validation**: All required files present, source budget compliant (149 KB), no unfinished code markers, no token-shaped files.
- **Test suite**: All 47 backend tests and 20 frontend tests pass; frontend build succeeds.

### Added
- **Feature plan completion**: Marked `export-import-report` feature as done in `feature-plan.json` with full acceptance criteria, implementation paths, and test references.

## 1.23.0 — Title registry PS5 fields and portfolio.json compliance