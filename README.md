# VoiceResume AI

Voice memos to resume generation SaaS platform.

## Architecture

This is a monorepo with:
- **packages/** — Shared Python libraries (auth, database, models)
- **apps/voiceresumeapp/** — Main FastAPI application
- **apps/k8s-manifests/** — Kubernetes deployment files
- **.github/workflows/** — CI/CD pipelines

## Tech Stack

- **Language:** Python 3.12
- **Framework:** FastAPI
- **Database:** PostgreSQL (shared cluster, isolated DB per app)
- **Container:** Docker
- **Orchestration:** Kubernetes (K3s for dev, DOKS for production)
- **CI/CD:** GitHub Actions
- **Storage:** S3-compatible (Minio for dev, Wasabi for prod)
- **Speech-to-Text:** OpenAI Whisper API
- **Resume Generation:** OpenAI GPT-4
- **Package Registry:** GitHub Container Registry (GHCR)

## Local Development

### Prerequisites
- Python 3.12+
- Docker
- microk8s (single-node Kubernetes)
- kubectl (or use `microk8s kubectl`)

### Quick Start

```bash
# Start microk8s cluster with all services
make dev-up

# Watch logs
make dev-logs

# Run tests
make dev-test

# Stop cluster
make dev-down
```

The API will be available after you set up a host entry for `voiceresumeapp.local` pointing to the microk8s service IP.

## Project Structure

```
voiceresumeai/
├── packages/
│   ├── platform_auth/        # Shared authentication (signup, login, sessions)
│   └── platform_db/          # Shared database models and Alembic migrations
├── apps/
│   ├── voiceresumeapp/       # Main FastAPI application
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── requirements.txt
│   │   └── tests/
│   └── k8s-manifests/        # Kubernetes YAMLs
├── Dockerfile                 # Multi-stage Docker build
├── Makefile                   # Development commands
├── pyproject.toml            # Root Python project config
└── README.md                 # This file
```

## Features

### Phase 1: Foundation ✅
- Monorepo structure
- FastAPI app scaffolding
- Shared auth package
- Shared database models
- Docker container build
- Kubernetes manifests (K3s / DOKS)
- GitHub Actions CI/CD pipeline
- Local development setup (Makefile + k3d)

### Phase 2: Auth (In Progress)
- Sign up endpoint (email + password)
- Sign in endpoint (JWT sessions)
- Session management
- Password reset flow (email-based)

### Phase 3: Core Features (Planned)
- Voice memo upload (multipart/form-data)
- Automatic transcription (OpenAI Whisper)
- Resume generation (GPT-4)
- Memo history & listing

### Phase 4: Frontend (Planned)
- Web UI (React or Vue)
- Audio recording widget
- Resume editor and download

### Phase 5: Deployment (Planned)
- Production Kubernetes cluster (DOKS)
- S3 storage (Wasabi)
- TLS/HTTPS setup
- Monitoring and logging

## Deployment

### Local (K3s)
```bash
make dev-up
```

### Production (DigitalOcean DOKS)
```bash
# Set up cluster and secrets
kubectl create secret generic voiceresumeapp-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=JWT_SECRET=... \
  --from-literal=S3_ACCESS_KEY=... \
  --from-literal=S3_SECRET_KEY=... \
  -n production

# Apply manifests
kubectl apply -f apps/k8s-manifests/
```

See `apps/k8s-manifests/README.md` for detailed instructions.

## API Endpoints

### Auth
- `POST /auth/signup` — Create account
- `POST /auth/login` — Sign in
- `POST /auth/logout` — Sign out

### Health
- `GET /health` — Liveness check

### Voice Memos (Phase 3)
- `POST /api/v1/memos` — Upload voice memo
- `GET /api/v1/memos` — List user's memos
- `GET /api/v1/memos/:id` — Get memo details
- `DELETE /api/v1/memos/:id` — Delete memo

### Resumes (Phase 3)
- `POST /api/v1/resumes` — Generate resume from memo
- `GET /api/v1/resumes` — List user's resumes
- `GET /api/v1/resumes/:id` — Get resume
- `PATCH /api/v1/resumes/:id` — Update resume
- `GET /api/v1/resumes/:id/pdf` — Download as PDF
- `DELETE /api/v1/resumes/:id` — Delete resume

## Testing

```bash
# Run tests
make dev-test

# Or directly with pytest
pytest apps/voiceresumeapp/tests/ -v

# Lint code
make dev-lint
```

## Contributing

1. Create a feature branch
2. Make changes and test locally (`make dev-test`)
3. Commit with clear messages
4. Push and open a PR (GitHub Actions will lint, test, build, and deploy)

## Cost Estimate

Monthly costs (from architecture):
- DigitalOcean DOKS: $24/mo
- S3 storage (Wasabi): $5/mo
- OpenAI Whisper: ~$20/mo (100 audio hours)
- **Total:** ~$50/mo at launch

## Next Steps

1. Phase 2: Complete auth (signup, login, password reset)
2. Phase 3: Implement voice memo upload and resume generation
3. Phase 4: Build frontend UI
4. Phase 5: Deploy to production and harden

See [CREA-4](/CREA/issues/CREA-4) for current progress.
