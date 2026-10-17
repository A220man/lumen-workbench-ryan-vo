# Changelog

## 1.30.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.29.0 — advisory `generate_advisory` fix and version sync

### Fixed
- **Broken LLM advisory path**: `POST /imports/analyze?explain=true` imported a `generate_advisory` function that did not exist in `services/advisory.py`, causing an `ImportError` at runtime. Added the `generate_advisory` async wrapper (builds advisor from operator settings, calls `explain_imports`) and fixed the router to `await` it. When `LLM_API_KEY` is absent, the endpoint returns a clear "LLM advisory disabled" notice grounded in actual configuration rather than crashing.
- **Version desynchronization**: `pyproject.toml` and `frontend/package.json`/`package-lock.json` were pinned to 1.26.0 while `VERSION` was 1.29.0. Synchronized all metadata to 1.29.0.
- **README auth & API reference**: README described "HTTP-only cookies with CSRF protection" but the implementation uses bearer JWT tokens kept in memory (SPA PKCE architecture). Corrected the description and added the missing `/auth/config`, `/auth/authorize`, and `/auth/callback` endpoints to the API reference table.

## 1.28.0 — Keycloak integration and documentation baseline

### Added
- **Keycloak OIDC Provider**: Added Keycloak service to `compose.yaml` with development realm import (`keycloak/realm.json`). Includes pre-configured client `lumen-workbench`, roles (`viewer`, `operator`, `admin`), and test users.
- **Documentation Suite**: Created `docs/` directory with three comprehensive guides:
  - `docs/api.md`: Complete REST API reference with request/response examples for all 25+ endpoints
  - `docs/architecture.md`: System architecture with Mermaid diagrams, component details, data flows, security boundaries, deployment topology
  - `docs/deployment.md`: Production deployment guide covering TLS reverse proxy (nginx/Traefik), Keycloak/SAML broker setup, backup/restore procedures, monitoring, troubleshooting
- **README Enhancements**: Added Documentation section with links, TLS reverse proxy requirements, backup/restore commands, and SAML IdP enrollment steps.

### Changed
- **Compose Stack**: Extended `compose.yaml` with Keycloak service, persistent volumes (`keycloak-data`), healthchecks, and service dependencies.
- **Feature Plan**: Marked `docs-keycloak-integration` as done with full acceptance criteria, implementation paths, and test references.
- **Plan & Status**: Updated `PLAN.md` with completed feature details and future roadmap items.

### Verified
- All 53 backend tests pass (pytest)
- All 25 frontend tests pass (vitest)
- Frontend TypeScript build succeeds (tsc + vite build)
- Preflight validation: source budget 149,901 bytes (within 50–150 KB), no unfinished code, no token-shaped files

## 1.27.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.26.0 — First Light startup diagnostic (issue #2523) and full test suite

### Added
- **First Light Diagnostic Service**: `backend/services/first_light_diagnostic.py` models the 13-stop startup sequence for 007 First Light (PPSA11386) from AnyPS5 issue #2523, including PR references, shader-cache miss counts, and verification status for each stop.
- **API Endpoints**: `/api/v1/first-light/stops` (list all stops), `/api/v1/first-light/analyze` (analyze with applied PRs), `/api/v1/first-light/presets` (predefined PR sets for key progression points).
- **Frontend Component**: `FirstLightDiagnostic` in `frontend/src/components/first-light-diagnostic.tsx` with preset selector, custom PR input, and stop progression visualization showing status, PR links, verification state, and regression detection.
- **Preset Configurations**: Three presets covering base `main`, stops 1–3 fixed (PRs 2830, 2831, 2946, 1964), and all merged PRs through stop 11.
- **Domain Tests**: `test_first_light_stop_sequence`, `test_first_light_pr_mapping`, `test_first_light_presets` in `backend/tests/test_domain_engine.py`.
- **API Tests**: `test_first_light_stops_endpoint`, `test_first_light_analyze_endpoint`, `test_first_light_presets_endpoint` in `backend/tests/test_api_endpoints.py`.
- **Frontend Tests**: 5 tests in `frontend/tests/first-light-diagnostic.test.tsx` covering rendering, preset selection, custom PR input, analysis execution, and regression display.

### Changed
- **Test coverage**: All 53 backend tests and 25 frontend tests pass; frontend build succeeds.
- **Feature plan**: Marked `first-light-diagnostic` as done in `feature-plan.json` with full acceptance criteria.

### Known Limitations
- Source budget at 165,116 bytes (150 KB limit); optimization needed for full preflight compliance.

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