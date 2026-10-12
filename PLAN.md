# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

first-light-diagnostic

## Roadmap

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- All backend tests pass (47/47)
- All frontend tests pass (20/20)
- Frontend build succeeds
- Preflight validation passes (source budget, no unfinished code, no token-shaped files)
- Portfolio.json updated to contract specification with domain, workflows, auth, llm_providers
- Title model extended with PS5-specific fields (ppsa_id, version)
- TitleService integrated with new endpoints: list, get by ID, get by PPSSA ID, create, update, delete, history

Implementation: `backend/models/title.py`, `backend/schemas/title.py`, `backend/services/title_registry.py`, `backend/app/api/router.py`, `portfolio.json`

Tests: `backend/tests/test_api_endpoints.py::test_titles_crud_lifecycle`, `backend/tests/test_api_endpoints.py::test_adversarial_generation_endpoint`, `backend/tests/test_api_endpoints.py::test_system_analytics_endpoint`, `backend/tests/test_api_endpoints.py::test_integration_workflow_http_boundary`, `backend/tests/test_api_endpoints.py::test_storage_writeback_simulate_endpoint`

### export-import-report — Add CSV/JSON export for import analysis reports

Status: done

Acceptance:
- Add Export Report button to Import Analysis results panel
- Support CSV and JSON export formats
- Exported file includes all import details, coverage, blockers, and advisory explanation
- Export works without LLM_API_KEY configured
- All existing tests pass
- Frontend build succeeds

Implementation: `frontend/src/components/import-analysis.tsx`

Tests: `frontend/tests/import-analysis.test.tsx`

### first-light-diagnostic — Add 007 First Light startup sequence diagnostic (issue #2523)

Status: in_progress

Acceptance:
- Add FirstLightDiagnostic service modeling the 13-stop startup sequence from issue #2523
- Add API endpoints: /first-light/stops, /first-light/analyze, /first-light/presets
- Add frontend FirstLightDiagnostic component with stop progression visualization
- Include PR references and verification status for each stop
- All backend tests pass
- All frontend tests pass
- Frontend build succeeds

Implementation: `backend/services/first_light_diagnostic.py`, `backend/app/api/router.py`, `frontend/src/components/first-light-diagnostic.tsx`, `frontend/src/api.ts`

Tests: `backend/tests/test_domain_engine.py::test_first_light_stop_sequence`, `backend/tests/test_domain_engine.py::test_first_light_pr_mapping`, `backend/tests/test_api_endpoints.py::test_first_light_stops_endpoint`, `backend/tests/test_api_endpoints.py::test_first_light_analyze_endpoint`, `frontend/tests/first-light-diagnostic.test.tsx`

