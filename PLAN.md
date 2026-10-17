# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

fix-advisory-path

## Roadmap

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- Run checks, fix failures, and implement the next planned feature

### docs-keycloak-integration — Add Keycloak to compose.yaml and create documentation

Status: done

Acceptance:
- Keycloak service added to compose.yaml with realm import
- docs/api.md with complete endpoint reference
- docs/architecture.md with system design and data flows
- docs/deployment.md with TLS proxy, backup/restore, SAML setup
- README updated with documentation links and key deployment info
- All tests pass and preflight check passes

Implementation: `compose.yaml`, `keycloak/realm.json`, `docs/api.md`, `docs/architecture.md`, `docs/deployment.md`, `README.md`

Tests: `backend/tests/test_api_endpoints.py (53 tests)`, `backend/tests/test_auth.py (7 tests)`, `backend/tests/test_domain_engine.py (33 tests)`, `frontend/tests/ (25 tests across 10 files)`

### fix-advisory-path — Fix broken LLM advisory path and version/desync documentation

Status: done

Acceptance:
- POST /imports/analyze?explain=true does not crash with ImportError
- generate_advisory exists in advisory.py and is awaited in router
- Advisory field returned when LLM_API_KEY absent with disabled notice
- Version metadata synchronized: VERSION, pyproject.toml, package.json, package-lock.json all 1.29.0
- README auth description matches bearer-token architecture, API table includes OIDC endpoints
- All tests pass and preflight check passes

Implementation: `backend/services/advisory.py`, `backend/app/api/router.py`, `pyproject.toml`, `frontend/package.json`, `frontend/package-lock.json`, `README.md`

Tests: `backend/tests/test_api_endpoints.py::test_import_analysis_with_explain_disabled`, `backend/tests/test_domain_engine.py::test_generate_advisory_disabled_without_key`

