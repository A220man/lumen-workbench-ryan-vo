# Lumen Workbench Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- Or: Python 3.12+, Node.js 24+, SQLite 3
- 2 GB RAM minimum (4 GB recommended for Keycloak)
- Ports 3000, 8000, 8080 available on localhost

## Quick Start (Docker Compose)

```bash
# Clone and navigate
cd lumen-workbench-ryan-vo

# Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your settings

# Start all services
docker compose up -d

# Access applications
# Frontend:  http://127.0.0.1:3000
# Backend:   http://127.0.0.1:8000
# Keycloak:  http://127.0.0.1:8080 (admin/changeme)
# API Docs:  http://127.0.0.1:8000/docs
```

## Local Development (Without Docker)

### Backend
```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
# Set required env vars or use demo mode
export LUMEN_DEMO_MODE=true
export OIDC_ENABLED=false
.venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Access at http://127.0.0.1:5173
```

## Configuration

All configuration via environment variables (see `.env.example`):

### Required for Production
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g., `postgresql://user:pass@db:5432/lumen`) |
| `LUMEN_SECRET_KEY` | Strong random string for JWT signing (32+ chars) |
| `OIDC_ENABLED` | `true` |
| `OIDC_PROVIDER_URL` | Keycloak realm URL (e.g., `https://auth.example.com/realms/lumen`) |
| `OIDC_CLIENT_ID` | Keycloak client ID |
| `OIDC_CLIENT_SECRET` | Keycloak client secret |
| `OIDC_REDIRECT_URI` | `https://your-domain.com/api/v1/auth/callback` |
| `HOST` | `0.0.0.0` (or your domain) |

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `LUMEN_DEMO_MODE` | `false` | Localhost-only demo login (refused in production) |
| `LLM_API_KEY` | - | Enable advisory explanations |
| `LLM_PROVIDER` | `openai-compatible` | `openai-compatible`, `anthropic`, `gemini`, `ollama` |
| `LLM_MODEL` | - | Model name (provider-dependent) |
| `LLM_BASE_URL` | - | Provider API base URL |
| `LUMEN_DEBUG` | `false` | Enable debug logging |
| `LUMEN_DATA_DIR` | `data` | Data directory for SQLite |

## TLS Reverse Proxy (Production)

**Required for production.** The application must run behind a TLS-terminating reverse proxy.

### nginx Example
```nginx
server {
    listen 443 ssl http2;
    server_name lumen.example.com;

    ssl_certificate /etc/letsencrypt/live/lumen.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lumen.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy strict-origin-when-cross-origin;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://api.openai.com https://api.anthropic.com https://generativelanguage.googleapis.com; frame-ancestors 'none';";

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Keycloak (if exposed)
    location /auth/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name lumen.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Traefik Example (Docker Labels)
```yaml
# Add to compose.yaml services
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.lumen-frontend.rule=Host(`lumen.example.com`)"
  - "traefik.http.routers.lumen-frontend.entrypoints=websecure"
  - "traefik.http.routers.lumen-frontend.tls.certresolver=letsencrypt"
  - "traefik.http.services.lumen-frontend.loadbalancer.server.port=80"
  - "traefik.http.routers.lumen-api.rule=Host(`lumen.example.com`) && PathPrefix(`/api`)"
  - "traefik.http.routers.lumen-api.entrypoints=websecure"
  - "traefik.http.routers.lumen-api.tls.certresolver=letsencrypt"
  - "traefik.http.services.lumen-api.loadbalancer.server.port=8000"
```

### Critical Proxy Headers
The backend relies on these headers for correct OIDC redirect URIs:
- `X-Forwarded-Proto` - Must be `https` in production
- `X-Forwarded-For` - Client IP for audit logs
- `Host` - Original host for redirect URI construction

## Keycloak Setup

### Via Docker Compose (Development)
The included `keycloak/realm.json` imports a pre-configured realm on startup:
- Realm: `lumen`
- Client: `lumen-workbench` (confidential, PKCE)
- Roles: `viewer`, `operator`, `admin`
- Users: `admin/admin`, `operator/operator`, `viewer/viewer`

### Manual Keycloak Configuration (Production)
1. Create realm `lumen`
2. Create client `lumen-workbench`:
   - Client authentication: On
   - Standard flow: On
   - Direct access grants: On
   - Valid redirect URIs: `https://your-domain.com/api/v1/auth/callback`
   - Web origins: `https://your-domain.com`
   - Client secret: Generate and save
3. Create realm roles: `viewer`, `operator`, `admin`
4. Create users and assign roles
5. Configure SAML Identity Provider (optional):
   - Identity Providers → SAML v2.0
   - Import IdP metadata or configure manually
   - Set up attribute mappers for email, name, roles
   - Link to Keycloak roles via role mappers

### SAML Brokering
Keycloak supports upstream SAML IdPs (Azure AD, Okta, Auth0, etc.) through identity brokering:
1. Add SAML Identity Provider in Keycloak
2. Configure IdP metadata (entity ID, SSO URL, certificates)
3. Map SAML attributes to Keycloak user attributes
4. Create role mappers to assign realm roles from SAML assertions
5. Test with `kc_saml_idp` test user

## Database

### SQLite (Default, Development)
- File: `data/lumen.db` (persisted in Docker volume `lumen-data`)
- No configuration needed
- Suitable for single-instance, low-concurrency workloads

### PostgreSQL (Production)
```bash
# In .env
DATABASE_URL=postgresql://lumen:secure_password@db:5432/lumen
```

Add PostgreSQL service to `compose.yaml`:
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: lumen
      POSTGRES_USER: lumen
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lumen"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
    driver: local
```

Update backend `depends_on` to include `db`.

### Migrations
SQLAlchemy creates tables on startup via `create_all()`. For production schema changes, use Alembic:
```bash
.venv/bin/pip install alembic
.venv/bin/alembic init backend/alembic
# Configure backend/alembic/env.py with target_metadata
.venv/bin/alembic revision --autogenerate -m "initial"
.venv/bin/alembic upgrade head
```

## Backup & Restore

### SQLite Backup
```bash
# Hot backup (requires sqlite3)
docker exec lumen-backend sqlite3 /data/lumen.db ".backup /data/lumen-backup-$(date +%F).db"

# Or copy volume
docker run --rm -v lumen-workbench-ryan-vo_lumen-data:/data -v $(pwd)/backups:/backup alpine \
  cp /data/lumen.db /backup/lumen-backup-$(date +%F).db
```

### PostgreSQL Backup
```bash
docker exec lumen-db pg_dump -U lumen lumen > lumen-backup-$(date +%F).sql
```

### Restore
```bash
# SQLite
docker run --rm -v lumen-workbench-ryan-vo_lumen-data:/data -v $(pwd)/backups:/backup alpine \
  cp /backup/lumen-backup-2026-10-13.db /data/lumen.db

# PostgreSQL
docker exec -i lumen-db psql -U lumen lumen < lumen-backup-2026-10-13.sql
```

### Keycloak Backup
```bash
# Export realm
docker exec lumen-keycloak /opt/keycloak/bin/kc.sh export --dir /opt/keycloak/data/export --realm lumen --users realm_file

# Or use Keycloak admin console: Realm Settings → Export
```

## Health Checks & Monitoring

| Service | Endpoint | Expected |
|---------|----------|----------|
| Backend | `GET /health` | `{"status": "healthy"}` |
| Frontend | `GET /` | HTTP 200, HTML |
| Keycloak | `GET /health/ready` | HTTP 200 |

### Prometheus Metrics (Optional)
Add `prometheus-fastapi-instrumentator` to backend:
```python
# In main.py
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

## Scaling & High Availability

### Horizontal Scaling
- Backend: Stateless, run multiple replicas behind load balancer
- Frontend: Static assets, serve via CDN or multiple nginx replicas
- Keycloak: Use external managed service or clustered Keycloak
- Database: PostgreSQL with replication

### Session Affinity
Not required - JWT tokens are stateless. All instances share `LUMEN_SECRET_KEY`.

## Troubleshooting

### Demo Mode Refused
```
RuntimeError: LUMEN_DEMO_MODE=true is only allowed when HOST is 127.0.0.1/localhost
```
→ Set `HOST=127.0.0.1` or disable demo mode and configure OIDC.

### OIDC Callback Fails
- Verify `OIDC_REDIRECT_URI` matches Keycloak client exactly
- Check `X-Forwarded-Proto` header is `https` behind proxy
- Ensure Keycloak `KC_HOSTNAME` matches public URL

### Database Locked
- SQLite doesn't handle concurrent writes well
- Migrate to PostgreSQL for multi-user production

### Keycloak Import Fails
- Check realm.json syntax
- Verify volume mount: `./keycloak/realm.json:/opt/keycloak/data/import/realm.json`
- Keycloak 26+ uses `--import-realm` flag

## Security Checklist (Production)

- [ ] `LUMEN_DEMO_MODE=false`
- [ ] `OIDC_ENABLED=true` with valid provider
- [ ] Strong `LUMEN_SECRET_KEY` (32+ random chars)
- [ ] TLS termination at reverse proxy
- [ ] Secure `OIDC_CLIENT_SECRET` and `KEYCLOAK_ADMIN_PASSWORD`
- [ ] Database credentials not in repo
- [ ] `LLM_API_KEY` restricted to minimal permissions
- [ ] Regular backup schedule configured
- [ ] Security headers in reverse proxy
- [ ] Rate limiting on auth endpoints
- [ ] Audit log retention policy

## Upgrading

```bash
# Pull latest images
docker compose pull

# Rebuild custom images
docker compose build --no-cache

# Restart with new versions
docker compose up -d

# Run database migrations if using Alembic
docker exec lumen-backend .venv/bin/alembic upgrade head
```

## Support

- Issues: https://github.com/A220man/lumen-workbench-ryan-vo/issues
- Author: Ryan Vo (ryandtvo@gmail.com)