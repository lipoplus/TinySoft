# VoiceResume Local Development Setup Guide

## Two Options for Local Development

### Option 1: Docker Compose (Recommended for Fast Iteration)
**Speed:** Fast (compose up in ~30s) | **Closest to prod:** ⭐⭐⭐ | **Overhead:** Docker only

Ideal for:
- Rapid feature development
- Testing API changes
- Running tests frequently
- Minimal infrastructure overhead

### Option 2: Kubernetes with microk8s (Recommended for Production-Like Testing)
**Speed:** Slower (~2-3 min) | **Closest to prod:** ⭐⭐⭐⭐⭐ | **Overhead:** Full K8s cluster

Ideal for:
- Testing deployment manifests
- Simulating production environment
- Testing scaling and load balancing
- Kubernetes-specific configurations

---

## Quick Start with Docker Compose (Recommended)

### Prerequisites
```bash
# Check Docker is installed and running
docker --version
docker compose version  # Should be v2.0+
```

### Setup
```bash
# 1. Clone and navigate to repo
cd /path/to/voiceresumeai

# 2. Copy environment template
cp .env.example .env.local

# 3. (Optional) Update OPENAI_API_KEY in .env.local
nano .env.local

# 4. Start all services
docker compose -f docker-compose.local.yml up -d

# 5. Wait for services to be ready (20-30 seconds)
docker compose -f docker-compose.local.yml logs -f

# 6. Apply database migrations
docker compose -f docker-compose.local.yml exec voiceresumeapp alembic upgrade head

# 7. Test the API
curl http://localhost:8000/health
```

### Available Services
- **API:** http://localhost:8000
- **Database:** localhost:5432 (voiceresumeai/voiceresumeai)
- **Minio (S3):** http://localhost:9001 (minioadmin/minioadmin)
- **PgAdmin:** http://localhost:5050 (admin@admin.com/admin)

### Common Commands
```bash
# View logs
docker compose -f docker-compose.local.yml logs voiceresumeapp -f

# Run tests
docker compose -f docker-compose.local.yml exec voiceresumeapp pytest tests/ -v

# Stop services
docker compose -f docker-compose.local.yml down

# Stop and remove data (clean slate)
docker compose -f docker-compose.local.yml down -v

# View database
docker compose -f docker-compose.local.yml exec postgres psql -U voiceresumeai -d voiceresumeai
```

### Developing with Hot Reload
```bash
# Edit code in your IDE, the app automatically reloads
# Located in: apps/voiceresumeapp/

# Test a specific endpoint
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

---

## Kubernetes Setup with microk8s

### Prerequisites
```bash
# Install microk8s (Linux)
sudo snap install microk8s --classic
microk8s status

# Install kubectl
sudo snap install kubectl --classic

# Verify installation
microk8s kubectl version
```

### Setup
```bash
# 1. Navigate to repo
cd /path/to/voiceresumeai

# 2. Copy environment template
cp .env.example .env.local

# 3. Start the environment
make dev-up

# 4. Get the service IP and add /etc/hosts entry
SERVICE_IP=$(microk8s kubectl get svc voiceresumeapp -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$SERVICE_IP voiceresumeapp.local" | sudo tee -a /etc/hosts

# 5. Access the app
curl http://voiceresumeapp.local/health
```

### Common Commands
```bash
# View logs
make dev-logs

# Restart services
microk8s kubectl rollout restart deployment/voiceresumeapp -n production

# Stop the cluster
make dev-down

# Clean up everything
make clean
```

---

## Troubleshooting

### Docker Compose Issues

**Issue:** `docker: command not found`
- **Solution:** Install Docker Desktop or Docker Engine: https://docs.docker.com/get-docker/

**Issue:** Port 8000 already in use
- **Solution:** Kill the process or change port in docker-compose.local.yml

**Issue:** Database connection refused
- **Solution:** Wait longer (databases take time to start). Check logs with `docker compose logs postgres`

### Kubernetes Issues

**Issue:** `microk8s: command not found`
- **Solution:** Install with `sudo snap install microk8s --classic`

**Issue:** Pods not starting
- **Solution:** Check `microk8s kubectl get pods -n production` and `microk8s kubectl describe pod <pod-name> -n production`

**Issue:** Image pull errors
- **Solution:** Ensure Docker image was built: `make dev-build`

---

## Development Workflow

### With Docker Compose
```bash
# Terminal 1: Watch logs
docker compose -f docker-compose.local.yml logs -f voiceresumeapp

# Terminal 2: Make changes, edit in apps/voiceresumeapp/
# Changes reload automatically

# Terminal 3: Test
curl http://localhost:8000/health
```

### Running Tests
```bash
# Docker Compose
docker compose -f docker-compose.local.yml exec voiceresumeapp pytest tests/ -v

# Or locally (requires Python 3.12+)
pip install -r apps/voiceresumeapp/requirements.txt
pytest apps/voiceresumeapp/tests/ -v
```

### Database Migrations
```bash
# Create a new migration
docker compose -f docker-compose.local.yml exec voiceresumeapp alembic revision --autogenerate -m "description"

# Apply migrations
docker compose -f docker-compose.local.yml exec voiceresumeapp alembic upgrade head

# Rollback
docker compose -f docker-compose.local.yml exec voiceresumeapp alembic downgrade -1
```

---

## System Requirements

### Docker Compose
- **OS:** macOS, Linux, or Windows (with WSL2)
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 5GB for images and volumes

### Kubernetes (microk8s)
- **OS:** Linux (Ubuntu 18.04+)
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 10GB for cluster and images

---

## Environment Variables

All services read from `.env.local`. Create this file:

```bash
cp .env.example .env.local
```

**Key variables:**
- `OPENAI_API_KEY` — Required for transcription and resume generation
- `DATABASE_URL` — Automatically set by docker-compose
- `S3_*` — Automatically set to Minio defaults

To use your own OpenAI key:
```bash
# Edit .env.local
OPENAI_API_KEY=sk-your-actual-key
```

---

## Next Steps

1. **Read the API docs:** http://localhost:8000/docs (Swagger UI, requires services running)
2. **Explore the codebase:** Start with `apps/voiceresumeapp/main.py`
3. **Run tests:** `make dev-test` or use docker-compose commands
4. **Create a feature branch** for your work

---

## Getting Help

- Check logs: `docker compose logs <service-name>`
- Database issues: Use PgAdmin at http://localhost:5050
- S3/Minio issues: Use console at http://localhost:9001
- API docs: http://localhost:8000/docs

---

## Summary

**For 90% of development:** Use Docker Compose (it's faster and easier).

**When you need:** Production simulation, K8s testing, or deployment validation → Use microk8s.

Both options let you develop fully locally without cloud access.
