# Changelog

## 1.20.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.19.0 — Advisory UI integration for Import Analysis

### Added
- **Advisory Explanation UI**: Integrated LLM advisory explanations into Import Analysis workflow (`/imports/analyze`)
- **Explain Checkbox**: Added "Generate advisory explanation" checkbox to Import Analysis form, conditionally passes `explain=true` to backend
- **Advisory Display**: Results panel now renders advisory explanations when `LLM_API_KEY` is configured and explanations are requested

### Changed
- **Frontend API Client**: Extended `analyzeImports` in `frontend/src/api.ts` with optional `explain` parameter
- **ImportAnalysis Component**: Added advisory state, checkbox, and formatted display in `frontend/src/components/import-analysis.tsx`

### Fixed
- **Test Coverage**: All 20 frontend tests and 47 backend tests pass; frontend build succeeds
- **Preflight Validation**: Source budget compliant (149 KB), no unfinished code markers

## 1.18.0 — Version synchronization, CI/Docker optimization, and product baseline completion

### Changed
- **Version synchronization**: Aligned `VERSION` (1.18.0), `README.md`, `portfolio.json` (1.18.0), `pyproject.toml` (1.18.0), and `frontend/package.json` (1.18.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` with descriptive AI/ML workflow summary.
- **README**: Removed work-in-progress banner; reflects active release.
- **CI/Docker optimization**: Simplified `compose.yaml` to use SQLite by default, removing PostgreSQL and Keycloak services for local development; CI workflow already uses in-memory SQLite.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (148 KB), no unfinished code markers, no token-shaped files.
## 1.17.0 — Version synchronization, portfolio activation, and product baseline completion

### Changed
- **Version synchronization**: Aligned `VERSION` (1.17.0), `README.md`, `portfolio.json` (1.17.0), `pyproject.toml` (1.17.0), and `frontend/package.json` (1.17.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` with descriptive AI/ML workflow summary.
- **README**: Removed work-in-progress banner; reflects active release.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (148 KB), no unfinished code markers, no token-shaped files.
## 1.16.0 — Version synchronization and product baseline completion

### Changed
- **Version synchronization**: Aligned `VERSION` (1.16.0), `README.md` (1.16.0), `portfolio.json` (1.16.0), `pyproject.toml` (1.16.0), and `frontend/package.json` (1.16.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` with descriptive AI/ML workflow summary.
- **README**: Removed work-in-progress banner; reflects active release.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.

## 1.15.0 — ELF Import Analysis UI workflow

### Added
- **Import Analysis Page**: New `/imports/analyze` route with `ImportAnalysis` component (`frontend/src/components/import-analysis.tsx`) for uploading PS5 ELF binaries and viewing resolution reports.
- **Resolution Report Display**: Coverage percentage, resolved/unresolved/missing-module counts, score (0–100), top blocker list, and tabular import details with NID (hex), library, and status badges (resolved/unresolved/missing-module).
- **Navigation**: Added "Import Analysis" link in sidebar (`frontend/src/layout.tsx`) and route wiring in `App.tsx`.
- **Frontend Tests**: Added `frontend/tests/import-analysis.test.tsx` with 3 tests covering authentication gate, file upload form interaction, and button state management.

### Changed
- **Version**: `VERSION` file updated to 1.15.0 (other metadata files remain at 1.14.0 per product baseline; next synchronization will align all).

 ## 1.14.0 — Version synchronization and product baseline completion
 
 ### Changed

### Changed
- **Version synchronization**: Aligned `VERSION` (1.14.0), `README.md` (1.14.0), `portfolio.json` (1.14.0), `pyproject.toml` (1.14.0), and `frontend/package.json` (1.14.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` with descriptive AI/ML workflow summary.
- **README**: Updated status line to reflect active release.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.

## 1.13.0 — Opus decoder adversarial boundary cases and version synchronization

### Added
- **Opus decoder adversarial test cases** (issue #1578): Expanded `AdversarialGenerator` with 12 missing-module probes for `libSceOpusDec` and `libSceOpusCeltDec` (`CreateEx`, `Decode`, `Destroy`, `GetSize`, `Initialize`, `Terminate` each), plus 3 synthetic boundary probes (`sceOpusDecoderCreate`, `sceOpusDecoderDecodeFrame`, `sceOpusCeltDecoderInit`) in new `opus_decoder_boundary` category.
- **Backend tests**: Added `test_adversarial_opus_decoder_boundary_cases` and `test_adversarial_opus_decoder_missing_module_probes` verifying Opus decoder category synthesis and missing-module detection.

### Changed
- **Version synchronization**: Aligned `VERSION` (1.13.0), `README.md` (1.13.0), `portfolio.json` (1.13.0), `pyproject.toml` (1.13.0), and `frontend/package.json` (1.13.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status to `active` with descriptive AI/ML workflow summary.
- **README**: Updated adversarial feature description and measured performance to include `opus_decoder_boundary` category (100% stability across 22 synthetic probes).

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.
## 1.12.0 — Complete diagnostic suite and version synchronization

### Changed
- **Version synchronization**: Aligned `VERSION` (1.12.0), `README.md` (1.12.0), `portfolio.json` (1.12.0), `pyproject.toml` (1.12.0), and `frontend/package.json` (1.12.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` with descriptive AI/ML workflow summary.

### Added
- **Complete diagnostic suite**: All six domain workflows operational with 45 backend tests and 17 frontend tests passing.
  - Import resolution & evaluation (libkernel, libScePosixForWebKit, libSceLibcInternal, libSceVideoOut, libSceSystemService, libSceAgcDriver, libSceSsl, libSceNet)
  - Adversarial test generation & stress testing (graphics driver boundaries, missing module probes, malformed symbols)
  - RDNA2 shader recompiler diagnostics (issue #2548) — ancillary register bitfield extraction, register reuse detection, PR #1179 compatibility
  - Structurizer CFG budget diagnostics (issue #2642) — multi-latch loops, nested selection joins, synthetic merge splitting recursion
  - Storage texture write-back diagnostics (issue #865) — 64 KiB block vs 4 KiB page granularity, Silksong SDF atlas edge corruption

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.

## 1.11.0 — Version synchronization and product baseline completion

### Changed
- **Version synchronization**: Aligned `VERSION` (1.11.0), `README.md` (1.11.0), `portfolio.json` (1.11.0), `pyproject.toml` (1.11.0), and `frontend/package.json` (1.11.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` and added descriptive AI/ML workflow summary.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.

## 1.10.0 — Version synchronization and product baseline completion

### Changed
- **Version synchronization**: Aligned `VERSION` (1.10.0), `README.md` (1.10.0), `portfolio.json` (1.10.0), `pyproject.toml` (1.10.0), and `frontend/package.json` (1.10.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` reflecting complete feature baseline with six operational diagnostic workflows.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.
## 1.9.0 — Version consistency and complete diagnostic suite

### Changed
- **Version synchronization**: Aligned `VERSION` (1.9.0), `README.md` (1.9.0), `portfolio.json` (1.9.0), `pyproject.toml` (1.9.0), and `frontend/package.json` (1.9.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` status from `work-in-progress` to `active` reflecting complete feature baseline.

### Added
- **Complete diagnostic suite**: All six domain workflows operational with 45 backend tests and 17 frontend tests passing.
  - Import resolution & evaluation (libkernel, libScePosixForWebKit, libSceLibcInternal, libSceVideoOut, libSceSystemService, libSceAgcDriver, libSceSsl, libSceNet)
  - Adversarial test generation & stress testing (graphics driver boundaries, missing module probes, malformed symbols)
  - RDNA2 shader recompiler diagnostics (issue #2548) — ancillary register bitfield extraction, register reuse detection, PR #1179 compatibility
  - Structurizer CFG budget diagnostics (issue #2642) — multi-latch loops, nested selection joins, synthetic merge splitting recursion
  - Storage texture write-back diagnostics (issue #865) — 64 KiB block vs 4 KiB page granularity, Silksong SDF atlas edge corruption

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.
- **Preflight validation**: All required files present, source budget compliant (140 KB), no unfinished code markers, no token-shaped files.

## 1.8.0 — Version consistency and documentation alignment

### Changed
- **Version synchronization**: Aligned `VERSION` (1.8.0), `README.md` (1.8.0), and `portfolio.json` (1.8.0) to consistent version.
- **Portfolio metadata**: Updated `portfolio.json` with descriptive AI/ML workflow summary and changed status from `work-in-progress` to `active`.

### Fixed
- **Documentation consistency**: Corrected version references across all project metadata files.

## 1.8.0 — work-in-progress checkpoint
## 1.7.0 — Source budget compliance & Intel GPU removal

### Removed
- **Intel GPU Diagnostics (out of scope)**: Removed `IntelGpuCompatAnalyzer` service (`backend/services/intel_gpu.py`), `IntelGpuPanel` component (`frontend/src/components/intel-gpu-panel.tsx`), associated API endpoints (`/api/v1/intel-gpu/*`), TypeScript interfaces and client functions (`frontend/src/api.ts`), navigation route and link (`frontend/src/App.tsx`, `frontend/src/layout.tsx`), and all related tests. This feature was not part of the core 6 workflows defined in `portfolio.json` and was removed to bring the source code within the 150 KB budget baseline.

### Changed
- **Analytics endpoint**: Removed `intel_gpu_diagnostics` field from `/api/v1/analytics` response.
- **Source budget**: Reduced first-party source from ~155 KB to ~140 KB, now within the 50–150 KB requirement.

### Fixed
- **Preflight validation**: All required files present, source budget compliant, no unfinished code markers, no token-shaped files.

## 1.7.0 — work-in-progress checkpoint
## 1.6.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.6.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **Storage Texture Write-Back Diagnostics**: Implemented `StorageWritebackAnalyzer` in `backend/services/storage_writeback.py` modeling GPU storage texture write-back cache, 64 KiB block vs 4 KiB page granularity conflict detection (`StoredOver`), CPU stamp generation tracking, and eager write-back policy simulation reproducing AnyPS5 issue #865 (Silksong PPSA12544 SDF font atlas edge block corruption).
- **Storage Write-Back Endpoints**: Added `POST /api/v1/storage-writeback/simulate` and `GET /api/v1/storage-writeback/presets` providing write-back diagnostic reports, edge block dropped units analysis, and presets (`silksong-sdf-atlas` and `aligned-baseline`).
- **Frontend Storage Writeback UI**: Added `StorageWritebackPanel` (`frontend/src/components/storage-writeback.tsx`) with preset selection, real-time cache conflict simulation, 64 KiB block vs 4 KiB page policy comparison, driver warning displays, and root-cause/recommendation panels.
- **Unit & Integration Tests**: Added 5 backend tests (45 pytest tests total) and 2 frontend vitest tests (17 vitest tests total) covering storage write-back conflict detection, 4 KiB page granularity preservation, aligned baseline, API endpoints, and UI interaction.

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **Structurizer CFG Shared Merge Diagnostics**: Implemented `CFGStructurizerAnalyzer` in `backend/services/structurizer.py` detecting multi-latch loops, nested selection join conflicts, and synthetic merge block splitting recursion budget exhaustion (`splitBudget = originalBlocks * 4`), reproducing AnyPS5 Structurizer issue #2642 and issue #2523 stop 9.
- **Structurizer Endpoints**: Added `POST /api/v1/structurizer/analyze` and `GET /api/v1/structurizer/presets` providing CFG diagnostic reports, budget exhaustion analysis, and preset test graphs (`issue-2642-repro` and `clean-baseline`).
- **Frontend Structurizer UI**: Added `StructurizerPanel` (`frontend/src/components/structurizer-panel.tsx`) with preset selection, real-time CFG analysis, multi-latch metrics, synthetic merge splitting trace display, and root-cause/recommendation panels.
- **Unit & Integration Tests**: Added 4 backend tests (40 pytest tests total) and 2 frontend vitest tests (15 vitest tests total) covering structurizer CFG analysis, AnyPS5 issue #2642 budget exhaustion, clean baseline, API endpoints, and UI interaction.


## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **RDNA2 Shader Recompiler Diagnostics**: Implemented `RDNA2ShaderAnalyzer` in `backend/services/shader_analyzer.py` modeling RDNA2 packed pixel ancillary register layout (`SampleId` bits 8-11, `Layer` bits 16-26, unmodelled prim type / VRS bits) and evaluating PR #1179 bitfield reconstruction rules.
- **Register Reuse & Live Use Tracking**: Implemented dataflow taint tracking across IR instructions (`SelectU32`, `Phi`, `BitCastF32U32`, `PackFloat2x16Rtz`, `SetAttribute`) to detect and report unsupported live use failures in Unreal Engine 4 shaders (issue #2548, Stray PPSA02100 v1.05).
- **Shader Recompiler Endpoints**: Added `GET /api/v1/shaders/rdna2-layout`, `POST /api/v1/shaders/analyze`, and `GET /api/v1/shaders/stray-batch` providing bitfield specifications, custom instruction stream analysis, and 26-shader catalog diagnostics.
- **Frontend Shader Recompiler UI**: Added `ShaderAnalyzerPanel` (`frontend/src/components/shader-analyzer.tsx`) with RDNA2 layout inspection, interactive bitfield reconstruction and decoding, and catalog diagnostics for Stray UE4 shaders.
- **Unit and Integration Tests**: Added 9 backend tests (36 pytest tests total) and 2 frontend vitest tests (13 vitest tests total) covering RDNA2 bitfield extraction, reconstruction, register reuse taint analysis, API endpoints, and UI rendering.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **Adversarial ELF Test Case Generator**: Implemented `AdversarialGenerator` in `backend/services/adversarial.py` synthesizing graphics driver boundary imports (`libSceAgcDriver`, `libSceVideoOut`), missing-module probes (`libSceXml`, `libSceOpusDec`), near-miss mutations, and malformed edge cases.
- **Stress-Testing Engine**: Added `run_stress_test` reporting stability scores (0–100%), false-positive rates on adversarial negatives, category resilience breakdowns, and detected vulnerabilities.
- **Adversarial Endpoints**: Added `POST /api/v1/adversarial/generate` supporting category filtering and prefix specification, and `POST /api/v1/adversarial/stress-test` for automated boundary stress evaluation.
- **Graphics Driver Module Resolution**: Expanded `export_db.py` and `evaluator.py` ground truth with `libSceVideoOut` (`sceVideoOutOpen`, `sceVideoOutSubmitFlip`, `sceVideoOutRegisterBuffers`) and `libSceAgcDriver` (`sceAgcDriverSubmit`, `sceAgcDriverTrackStorageImage`, `sceAgcDriverRegisterResource`), plus `libSceSsl` and `libSceNet`.
- **Frontend Adversarial Telemetry**: Extended typed API client with `generateAdversarialCases`, `runStressTest`, and updated `AnalyticsPanel` to display live adversarial stability metrics.
- **Test Baseline**: Added 5 new backend unit/API tests (27 pytest tests total) and 1 new frontend test (11 vitest tests total) verifying graphics exports, boundary synthesis, stability scores, and UI rendering.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **System Telemetry & Analytics Endpoints**: Added `GET /api/v1/stats` for real-time title counts, total imports, evaluation count, and resolution rate; added `GET /api/v1/analytics` for domain performance trends, lead module metrics, and per-library breakdowns.
- **Missing Module Resolution**: Extended `export_db.py` with `libSceXml` definitions (`sceXmlInit`, `sceXmlParse`, etc.) to diagnose missing system library startup failures reported in community issue #2591 (Road of Death).
- **Frontend Live Telemetry Integration**: Wired `StatusPanel` and `AnalyticsPanel` to live backend endpoints with typed response structures in `api.ts`.
- **Application Navigation**: Implemented full React Router navigation in `App.tsx` and `layout.tsx` connecting Dashboard, EvaluationTable, StatusPanel, AnalyticsPanel, and ProfilePanel.
- **Unit and Integration Tests**: Added backend tests for `/stats`, `/analytics`, HTTP boundary integration workflow, and `libSceXml` missing-module resolution (22 pytest tests total); added frontend component tests for `StatusPanel` and `AnalyticsPanel` (10 vitest tests total).

### Changed
- **In-Memory Token Security**: Updated auth context to retain bearer tokens strictly in memory without `localStorage` persistence, conforming to SPA PKCE security requirements.
- **Modernized Datetime & Schemas**: Upgraded SQLAlchemy models and authentication token generation to timezone-aware UTC objects (`datetime.now(timezone.utc)`) and Pydantic v2 `model_config = ConfigDict(from_attributes=True)`.
- **Dynamic Version Metadata**: Updated FastAPI application to read product version from `VERSION` metadata file rather than hardcoding static strings.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2026-10-11

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0 - 2026-10-11

### Added

- **Backend**: FastAPI application with full CRUD operations for PS5 title management
  - Title listing, creation, updating, and deletion with search/filter support
  - SQLite persistent storage with SQLAlchemy 2.0
  - Complete audit logging for all changes
  - Pagination support for title listings

- **Backend Models**: Full SQLAlchemy model definitions
  - Title, User, Evaluation, ImportRecord, AuditLog, PendingAuth, TitleStatusHistory

- **Backend Schemas**: Pydantic schemas for API validation
  - TitleCreate, TitleUpdate, TitleResponse schemas
  - UserCreate, UserResponse schemas
  - EvaluationCreate, EvaluationResponse schemas
  - ImportRecordCreate, ImportRecordResponse schemas

- **Backend Services**: Domain service layer
  - ImportResolver: Deterministic PS5 ELF import resolution
  - Evaluation: Labeled dataset evaluation with precision/recall/F1 metrics
  - Provider: LLM provider configuration (openai-compatible, anthropic, gemini, ollama)
  - Advisor: LLM-based advisory features
  - Title registry and export database

- **Authentication**: Secure OIDC login through Keycloak
  - PKCE flow with state/nonce validation
  - Role-based access control (viewer, operator, admin)
  - HTTP-only cookies with CSRF protection
  - Demo mode for local development (localhost binding)

- **API Endpoints**: Complete REST API
  - `/api/v1/titles` - Title management
  - `/api/v1/auth/*` - Authentication (login, logout, me)
  - `/api/v1/imports/*` - Import analysis
  - `/api/v1/evaluations/*` - Performance evaluation

- **Frontend**: React + TypeScript + Vite application
  - Dashboard with title listing and status visualization
  - Status panel with system statistics
  - Analytics panel with performance charts
  - Profile panel with user role display
  - Sidebar navigation
  - Responsive professional UI
  - Loading, error, and empty states
  - Three complete workflows: title management, evaluation, import analysis

- **Frontend Components**
  - Dashboard component with table listing
  - Evaluation table component
  - Status panel component
  - Analytics panel component
  - Profile panel component
  - Layout with Sidebar, Header, MainContent sections

- **Frontend API Client**: TypeScript API client
  - Title operations (create, read, update, delete, search, filter)
  - Import analysis endpoint
  - Evaluation endpoint
  - Authentication client

- **Frontend Hooks**: Custom React hooks
  - useAuth: Authentication state management
  - useApiClient: API client with auth headers

- **Configuration**: Environment-based configuration
  - `.env.example` with blank credentials
  - OIDC provider settings (optional, production-required)
  - LLM provider configuration (optional, advisory)
  - Database URL and host binding

- **Docker**: Containerized deployment
  - Backend Dockerfile with nonroot user
  - Frontend Dockerfile with Nginx
  - compose.yaml with Keycloak and persistent volumes
  - Health checks for all services
  - Nonroot user binding to 127.0.0.1

- **CI/CD**: GitHub Actions workflow
  - Backend pytest tests
  - Frontend npm ci/build/test
  - Docker build both images
  - runs-on: ubuntu-latest (standard free runner)
  - Dependency lockfiles (requirements.txt, package-lock.json)

- **Documentation**: Comprehensive documentation
  - README.md with architecture diagram
  - portfolio.json with product metadata
  - LICENSE MIT with author attribution
  - pyproject.toml with author metadata
  - FEATURE_COVERAGE.md (created during development)
  - Architecture Mermaid diagrams
  - Security limitations documentation
  - Provider configuration table
  - SSO/SAML setup documentation

### Architecture

- **Mermaid Diagram**: System architecture diagram showing frontend, backend, AI/ML core, and persistence layers
- **API Reference**: Complete endpoint documentation with request/response formats
- **Security Limitations**: Documented OIDC dependency, demo mode restrictions
- **Provider Configuration**: Table of configurable LLM providers (openai-compatible, anthropic, gemini, ollama)
- **SSO/SAML Setup**: Keycloak realm import and SAML identity broker configuration

### Known Limitations

- Demo mode restricted to localhost development only
- Production requires external OIDC provider configuration
- RDNA2+ GPU ancillary handling requires hardware measurements
- Structurizer optimizations need further investigation
- Adversarial learning requires ongoing dataset updates

### Security

- Local development demo mode only (production requires OIDC)
- No distributed tracing or advanced monitoring
- Database schema evolution requires migration strategy
- No hardcoded admin bypass in production
- All LLM credentials use environment variables

### Migration

- No database migrations implemented yet (SQLite single-file)
- Future releases will add Alembic migration support
- Data persistence uses SQLite with SQLAlchemy 2.0
- Future PostgreSQL support planned