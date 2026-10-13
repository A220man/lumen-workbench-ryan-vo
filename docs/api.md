# Lumen Workbench API Reference

Base URL: `http://127.0.0.1:8000/api/v1`

All endpoints require authentication via Bearer token (JWT) unless noted otherwise.

## Authentication

### POST `/auth/login`
Demo mode only. Authenticate with username/password.

**Request:**
```json
{"username": "admin", "password": "admin"}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_at": "2026-10-13T01:00:00Z",
  "role": "admin",
  "user": {"sub": "admin", "email": "admin@localhost", "name": "Admin User", "role": "admin"}
}
```

### GET `/auth/authorize`
Initiate OIDC PKCE authorization code flow.

**Query Parameters:**
- `redirect_uri` (optional): Override default redirect URI

**Response:**
```json
{"authorization_url": "https://keycloak...", "state": "abc123"}
```

### POST `/auth/callback`
Complete OIDC PKCE flow with authorization code.

**Request:**
```json
{"code": "auth_code_from_provider", "state": "state_from_authorize"}
```

### POST `/auth/logout`
Log out current session.

### GET `/auth/me`
Get current authenticated user profile.

**Response:**
```json
{"sub": "user-1", "email": "user@test.local", "name": "Test User", "role": "operator", "iss": "lumen", "aud": "lumen", "iat": 1697245200, "exp": 1697274000}
```

### GET `/auth/config`
Get authentication configuration (public endpoint).

## Titles

### GET `/titles`
List titles with pagination and filtering.

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20, max: 100)
- `status` (optional): Filter by status
- `search` (optional): Search by name

**Response:**
```json
[{"id": 1, "name": "007 First Light", "ppsa_id": "PPSA11386", "status": "active", "description": "...", "created_at": "2026-10-13T00:00:00Z", "updated_at": "2026-10-13T00:00:00Z"}]
```

### GET `/titles/ppsa/{ppsa_id}`
Get title by PPSA ID.

### GET `/titles/{title_id}`
Get title by internal ID.

### POST `/titles`
Create new title (requires `operator` or `admin` role).

**Request:**
```json
{"name": "Title Name", "ppsa_id": "PPSA12345", "status": "active", "description": "Optional description"}
```

### PUT `/titles/{title_id}`
Update title (requires `operator` or `admin` role).

### DELETE `/titles/{title_id}`
Delete title (requires `admin` role).

### GET `/titles/{title_id}/history`
Get title status change history.

## Import Analysis

### POST `/imports/analyze`
Upload and analyze PS5 ELF binary imports.

**Request:** Multipart form data
- `file`: ELF binary file (.elf, .bin, .so)
- `explain` (optional): Generate LLM advisory explanation (requires `LLM_API_KEY`)

**Response:**
```json
{
  "source_name": "app.elf",
  "needed_libraries": ["libkernel", "libSceVideoOut"],
  "coverage": 0.969,
  "resolved_count": 156,
  "unresolved_count": 5,
  "missing_module_count": 1,
  "score": 97,
  "blockers": ["sceVideoOutGetResolutionStatus (libSceVideoOut)"],
  "advisory": "[ADVISORY] This title has high import coverage...",
  "imports": [
    {"name": "sceKernelCreateThread", "nid": 0x12345678, "library": "libkernel", "status": "resolved"},
    {"name": "sceVideoOutGetResolutionStatus", "nid": 0xABCDEF01, "library": "libSceVideoOut", "status": "missing-module"}
  ]
}
```

## Evaluations

### GET `/evaluations`
List historical evaluation records.

### POST `/evaluations/run`
Run evaluation benchmark against labeled dataset.

**Response:**
```json
{"status": "success", "precision": 1.0, "recall": 0.969, "f1": 0.984, "coverage": 0.969, "total": 1578, "resolved": 1529, "unresolved": 49}
```

## Adversarial Testing

### POST `/adversarial/generate`
Generate synthetic boundary test cases.

**Request:**
```json
{"category": "graphics_driver_boundary", "count": 100}
```

**Categories:** `graphics_driver_boundary`, `video_out_boundary`, `missing_module_probe`, `opus_decoder_boundary`, `malformed_symbol`

### POST `/adversarial/stress-test`
Run adversarial stress test.

**Request:**
```json
{"categories": ["graphics_driver_boundary", "video_out_boundary"], "iterations": 10}
```

**Response:**
```json
{"status": "success", "overall_stability": 100.0, "total_cases": 220, "passed": 220, "failed": 0, "category_scores": {"graphics_driver_boundary": 100.0, "video_out_boundary": 100.0}}
```

## System Statistics & Analytics

### GET `/stats`
System telemetry and runtime statistics.

### GET `/analytics`
Domain performance metrics and stability scores.

## RDNA2 Shader Diagnostics

### GET `/shaders/rdna2-layout`
Get RDNA2 packed pixel ancillary VGPR layout specification.

### POST `/shaders/analyze`
Analyze shader instruction stream for ancillary word handling.

**Request:**
```json
{"shader_address": "0x200e370000", "title_id": "PPSA02100", "ancillary_vgpr": "v4", "instructions": [...], "raw_word": 0x12345678}
```

### GET `/shaders/stray-batch`
Batch analysis for Stray (PPSA02100) UE4 shaders (issue #2548).

## Structurizer CFG Diagnostics

### GET `/structurizer/presets`
Get CFG test shape presets including issue #2642 reproduction.

### POST `/structurizer/analyze`
Analyze control-flow graph for shared merge splitting budget exhaustion.

**Request:**
```json
{"name": "custom_cfg", "adjacency": [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []], "split_budget": 36}
```

## Storage Write-Back Diagnostics

### GET `/storage-writeback/presets`
Get storage writeback simulation presets (issue #865).

### POST `/storage-writeback/simulate`
Simulate storage writeback conflict for Silksong issue #865.

**Request:**
```json
{"title_id": "PPSA12544", "title_name": "Hollow Knight: Silksong", "texture_address": 2559197184, "texture_size": 262144, "block_size": 65536, "page_size": 4096, "gpu_dispatch_generation": 87617, "cpu_writes": [{"address": 2559197184, "size_bytes": 65536, "generation": 87617, "description": "CPU fill"}]}
```

## First Light Diagnostic

### GET `/first-light/stops`
Get all startup stops for 007 First Light (issue #2523).

### GET `/first-light/presets`
Get diagnostic presets for key progression points.

### POST `/first-light/analyze`
Analyze First Light sequence with applied PRs.

**Request:**
```json
{"applied_prs": [2830, 2831, 2946, 1964]}
```

**Response:**
```json
{
  "title_id": "PPSA11386",
  "title_name": "007 First Light",
  "version": "v01.018.000",
  "stops": [...],
  "current_stop": 4,
  "passed_stops": 3,
  "failed_stops": 10,
  "status": "stopped_at_4",
  "regression_detected": false,
  "regression_details": []
}
```

## Health

### GET `/health`
Health check endpoint (public).

**Response:**
```json
{"status": "healthy", "service": "lumen-workbench"}
```

## Error Responses

All endpoints may return standard HTTP error codes:
- `400` - Bad Request
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient role)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (OIDC not configured)

Error format:
```json
{"detail": "Error description"}
```