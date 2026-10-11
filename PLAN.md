# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

version-synchronization-baseline-complete

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

Status: done

Acceptance:
- Expand adversarial generator with synthetic boundary imports for libSceAgcDriver and libSceVideoOut
- Report stress-test stability scores against host export boundaries

Implementation: `backend/services/adversarial.py`, `backend/services/export_db.py`, `backend/services/evaluator.py`, `backend/app/api/router.py`, `frontend/src/api.ts`, `frontend/src/components/analytics.tsx`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `frontend/tests/analytics.test.tsx`

### rdna2-ancillary-word-and-shader-analysis — Shader recompiler ancillary register tracking and RDNA2 packed pixel extraction

Status: done

Acceptance:
- Model RDNA2 packed pixel ancillary register bitfield extraction (render target and sample index) for UE4 shaders (issue #2548)
- Diagnostic reporting for live register reuse and unsupported bit range extraction

Implementation: `backend/services/shader_analyzer.py`, `backend/app/api/router.py`, `frontend/src/api.ts`, `frontend/src/components/shader-analyzer.tsx`, `frontend/src/App.tsx`, `frontend/src/layout.tsx`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `frontend/tests/shader-analyzer.test.tsx`

### structurizer-cfg-budget-diagnostics — Structurizer CFG shared merge splitting diagnostics and loop latch analysis

Status: done

Acceptance:
- Detect multi-latch loops with nested selection joins exceeding splitting budget (issue #2642)
- Compute CFG complexity metrics and identify synthetic merge block recursion limits

Implementation: `backend/services/structurizer.py`, `backend/app/api/router.py`, `frontend/src/api.ts`, `frontend/src/components/structurizer-panel.tsx`, `frontend/src/App.tsx`, `frontend/src/layout.tsx`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `frontend/tests/structurizer.test.tsx`

### storage-texture-writeback-diagnostics — Storage texture write-back cache conflict and 4 KiB page granularity diagnostics

Status: done

Acceptance:
- Model 64 KiB block vs 4 KiB page write-back conflict detection for unaligned GPU storage textures (issue #865, Silksong PPSA12544)
- Diagnose false-positive CPU stamp overwrites on edge blocks discarding GPU SDF font atlas results
- Simulate 4 KiB page-level granularity and APS5_EAGER_WRITEBACK policies preventing glyph box corruption

Implementation: `backend/services/storage_writeback.py`, `backend/app/api/router.py`, `frontend/src/api.ts`, `frontend/src/components/storage-writeback.tsx`, `frontend/src/App.tsx`, `frontend/src/layout.tsx`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `frontend/tests/storage-writeback.test.tsx`

### version-synchronization-baseline-complete — Version synchronization and product baseline completion

Status: done

Acceptance:
- All metadata files (VERSION, README.md, portfolio.json, pyproject.toml, frontend/package.json) show consistent version 1.10.0
- portfolio.json status updated from work-in-progress to active
- CHANGELOG.md documents 1.10.0 release with complete diagnostic suite summary
- All 45 backend tests and 17 frontend tests continue to pass
- Preflight validation passes with zero missing files and source within budget

Implementation: `README.md`, `portfolio.json`, `pyproject.toml`, `frontend/package.json`, `CHANGELOG.md`, `feature-plan.json`

Tests: `backend/tests/test_domain_engine.py`, `backend/tests/test_api_endpoints.py`, `backend/tests/test_auth.py`, `frontend/tests/`

