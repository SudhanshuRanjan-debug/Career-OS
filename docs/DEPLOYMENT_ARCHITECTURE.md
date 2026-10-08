# Deployment & Cloud Architecture
## Career & Job Application Management Platform — Cloud Architecture

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture
**Cloud Target:** Microsoft Azure

---

## 1. Environment Strategy

| Environment | Host Infrastructure | Database | File Storage | Secrets & Config |
|:------------|:-------------------|:---------|:-------------|:-----------------|
| **Local** | Docker Compose (FastAPI, Vite, Postgres, Nginx) | PostgreSQL 16 Container | Local Filesystem (`/storage/private`) | `.env` file |
| **Staging** | Azure Container Apps | Azure Database for PostgreSQL (Flexible Server) | Azure Blob Storage (Private Container) | Azure Key Vault / App Secrets |
| **Production** | Azure Container Apps + Azure Front Door | Azure Database for PostgreSQL (Flexible Server with HA) | Azure Blob Storage (Zone-Redundant Private Container) | Azure Key Vault |

---

## 2. Local Docker Compose Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE (LOCAL)                          │
│                                                                        │
│   ┌──────────────┐         ┌──────────────┐                            │
│   │   frontend   │         │   backend    │                            │
│   │ (Vite Dev)   │         │  (FastAPI)   │                            │
│   │ Port: 5173   │         │ Port: 8000   │                            │
│   └──────┬───────┘         └──────┬───────┘                            │
│          │                        │                                    │
│          └───────────┬────────────┘                                    │
│                      │                                                 │
│             ┌────────▼────────┐                                        │
│             │      Nginx      │                                        │
│             │    Port: 80     │                                        │
│             │  (Reverse Proxy)│                                        │
│             └─────────────────┘                                        │
│                                                                        │
│   ┌──────────────┐         ┌──────────────┐                            │
│   │  PostgreSQL  │         │ Local Storage│                            │
│   │   Port: 5432 │         │  Directory   │                            │
│   └──────────────┘         └──────────────┘                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Production Cloud Architecture (Microsoft Azure)

```
Internet Clients (Web / Mobile Browsers)
                  │
                  ▼ HTTPS (TLS 1.3 Termination, WAF, DDoS Protection)
┌────────────────────────────────────────────────────────────────────────┐
│                        AZURE FRONT DOOR                                │
│                                                                        │
│   Route: /api/*  ──→ Azure Container Apps (FastAPI Backend)            │
│   Route: /*      ──→ Azure Container Apps (Nginx + React SPA)          │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌───────────────────────────────────────┐ ┌──────────────────────────────┐
│       AZURE CONTAINER APPS            │ │    AZURE CONTAINER APPS      │
│                                       │ │                              │
│  Backend Service (FastAPI)            │ │  Frontend Web (Nginx + React)│
│  - Python 3.12 / 3.13 Runtime         │ │  - Static bundle hosting     │
│  - Auto-scaling (1 to 10 replicas)    │ │  - Gzip / Brotli compression │
│  - Private Virtual Network (VNet)     │ │  - Client-side SPA routing   │
└──────────────────┬────────────────────┘ └──────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌───────────────────────┐ ┌──────────────────────────────────────────────┐
│ AZURE POSTGRESQL      │ │ AZURE BLOB STORAGE                           │
│ (Flexible Server)     │ │                                              │
│ - PostgreSQL 16       │ │ - Private Container for Resumes & Docs       │
│ - Private Endpoint    │ │ - No public read access                      │
│ - Automated Backups   │ │ - Authenticated streaming via backend        │
│ - High Availability   │ │ - Optional SAS URLs for large direct streams │
└───────────────────────┘ └──────────────────────────────────────────────┘
       │
       ▼
┌───────────────────────────────────────┐
│ AZURE MONITOR & APPLICATION INSIGHTS  │
│                                       │
│ - Structured JSON log aggregation     │
│ - API response time & health telemetry│
│ - Automated anomaly & alert rules     │
└───────────────────────────────────────┘
```

---

## 4. Container Configurations

### 4.1 Backend Dockerfile (`infrastructure/docker/backend.Dockerfile`)
```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY backend/ .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Frontend Dockerfile (`infrastructure/docker/frontend.Dockerfile`)
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY infrastructure/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 Nginx Reverse Proxy (`infrastructure/nginx/nginx.conf`)
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 15M;
    }

    # Backend health check proxy
    location /health {
        proxy_pass http://backend:8000/health;
        proxy_set_header Host $host;
    }

    # SPA client-side fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 5. CI/CD Pipeline Strategy (GitHub Actions)

1. **Pull Request & Commit Gate**:
   - Backend: linting with `ruff`, type checks, model validation, and unit/integration tests with `pytest`.
   - Frontend: linting with `eslint`, type validation with `tsc`, and production bundling verification with `vite build`.
2. **Staging Continuous Deployment**:
   - Auto-deploys `develop` branch to Azure Staging Environment.
   - Executes database migrations via Alembic.
   - Runs post-deployment synthetic health checks.
3. **Production Release Gate**:
   - Manual approval gate triggered from tagged releases (`v*.*.*`) on `main`.
   - Zero-downtime rolling update via Azure Container Apps revisions.
