# Changelog

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