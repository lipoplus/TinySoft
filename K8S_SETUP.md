# Option 2: Kubernetes Setup Guide

This guide covers setting up VoiceResume using Kubernetes (microk8s) for a production-like development environment.

## When to Use Option 2

Use Kubernetes when you need to:
- Test deployment configurations and manifests
- Simulate production-like environment locally
- Test scaling, load balancing, and orchestration
- Validate Kubernetes-specific features
- Practice production deployment procedures

**Speed**: ~2-3 minutes startup (vs 30 seconds for Docker Compose)

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 18.04+) or WSL2 on Windows
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 10GB for cluster, images, and data
- **CPU**: 2+ cores

### Required Software
```bash
# Install microk8s
sudo snap install microk8s --classic

# Install kubectl (standalone)
sudo snap install kubectl --classic

# Verify installation
microk8s status
microk8s version
kubectl version
```

## Quick Start

### Option A: Automated Setup (Recommended)
```bash
# Run interactive setup
make setup

# Choose "2" for Kubernetes when prompted
```

The setup will:
1. Build Docker image
2. Start microk8s cluster
3. Enable required services (DNS, storage, ingress)
4. Create namespace and secrets
5. Deploy PostgreSQL, Minio, and API
6. Wait for all services to be ready

### Option B: Manual Setup
```bash
# Start K8s cluster
make dev-up

# This does everything above automatically
```

## Services Deployed

### 1. PostgreSQL (postgres-svc:5432)
- Database for application data
- Persistent volume: 5GB
- User: `voiceresumeai` / password: `voiceresumeai`

### 2. Minio (minio-svc:9000, 9001)
- S3-compatible object storage
- API: `minio-svc:9000`
- Console: `http://localhost:9001` (after port-forward)
- Credentials: `minioadmin` / `minioadmin`
- Persistent volume: 10GB

### 3. VoiceResume API (voiceresumeapp-svc:8000)
- FastAPI application
- Automatic database migrations (init container)
- Health checks (liveness & readiness probes)
- Resource limits: 500m CPU / 512MB RAM

## Common Commands

### Viewing Status
```bash
# Check all resources
microk8s kubectl get all -n production

# Watch deployment rollout
microk8s kubectl rollout status deployment/voiceresumeapp -n production

# View pod status
microk8s kubectl get pods -n production
```

### Viewing Logs
```bash
# API logs
make dev-logs

# All service logs
make dev-logs-all

# Specific pod logs
microk8s kubectl logs -n production pod/voiceresumeapp-xxx -f
```

### Accessing Services
```bash
# API health check
curl http://voiceresumeapp.local/health

# API documentation
curl http://voiceresumeapp.local/docs

# Port-forward to Minio console
microk8s kubectl port-forward -n production svc/minio-svc 9001:9001
# Then visit http://localhost:9001

# Connect to database
make dev-psql
```

### Database Operations
```bash
# Run database migrations
microk8s kubectl delete pod -l app=voiceresumeapp -n production
# (Pod will restart and run migrations)

# Backup database
microk8s kubectl exec -n production \
  postgres-xxx -- pg_dump -U voiceresumeai voiceresumeai > backup.sql

# Restore database
cat backup.sql | microk8s kubectl exec -i -n production \
  postgres-xxx -- psql -U voiceresumeai voiceresumeai
```

### Scaling
```bash
# Scale API to 3 replicas
microk8s kubectl scale deployment/voiceresumeapp --replicas=3 -n production

# Watch scaling progress
microk8s kubectl rollout status deployment/voiceresumeapp -n production

# View metrics
microk8s kubectl top pods -n production
```

## Troubleshooting

### Services Won't Start

**Problem**: Pods stuck in `Pending` or `CrashLoopBackOff`

```bash
# Describe the pod to see what's wrong
microk8s kubectl describe pod <pod-name> -n production

# Check logs
microk8s kubectl logs <pod-name> -n production

# Check events
microk8s kubectl get events -n production --sort-by='.lastTimestamp'
```

### Storage Issues

**Problem**: PVC stuck in `Pending`

```bash
# Check available storage
microk8s kubectl get pv
microk8s kubectl get pvc -n production

# Verify storage add-on is enabled
microk8s status | grep storage

# If disabled, enable it:
microk8s enable storage
```

### Database Connection Failed

**Problem**: API can't connect to PostgreSQL

```bash
# Check postgres is running
microk8s kubectl get pods -n production -l app=postgres

# Check postgres logs
microk8s kubectl logs -n production -l app=postgres -f

# Test connection manually
make dev-psql
```

### Image Pull Issues

**Problem**: `ImagePullBackOff` error

```bash
# For local dev images:
# Ensure you're using imagePullPolicy: Never
# (This is set in the deployment manifests)

# Rebuild and reload image
docker build -t voiceresumeapp:latest .
microk8s ctr image import <(docker save voiceresumeapp:latest)

# Restart pods to pick up new image
microk8s kubectl delete pods -n production -l app=voiceresumeapp
```

### Stuck Resources

**Problem**: Pods won't delete or get stuck

```bash
# Force delete a pod
microk8s kubectl delete pod <pod-name> -n production --grace-period=0 --force

# Delete namespace completely (will delete all resources)
microk8s kubectl delete namespace production

# Reset everything
make dev-reset
```

## Validation

```bash
# Check K8s setup status
make dev-validate

# This checks:
# - microk8s running
# - All required services deployed
# - Persistent volumes created
# - Secrets configured
```

## Advanced Topics

### Custom Configuration

Edit `apps/k8s-manifests/voiceresumeapp-configmap.yaml` to change:
- Environment variables
- Log levels
- Database connection strings
- S3 endpoints

Apply changes:
```bash
microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-configmap.yaml
microk8s kubectl rollout restart deployment/voiceresumeapp -n production
```

### Resource Limits

Edit `apps/k8s-manifests/voiceresumeapp-deployment.yaml` to adjust:
- CPU requests/limits
- Memory requests/limits

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Persistence

All data is stored in persistent volumes:
- PostgreSQL: `/data/postgres-pvc` (5GB)
- Minio: `/data/minio-pvc` (10GB)

Data survives `microk8s stop` but not `microk8s reset`.

## Cleanup

### Stop Services (Keep Data)
```bash
make dev-down
```

### Delete Resources
```bash
microk8s kubectl delete namespace production
```

### Full Reset (Delete Everything)
```bash
make dev-reset
```

This will:
- Stop the cluster
- Reset microk8s completely
- Delete all data, volumes, and configuration
- Require reinstalling microk8s

## Moving to Production (DOKS)

When ready to deploy to DigitalOcean DOKS:

1. Create DOKS cluster:
   ```bash
   doctl kubernetes cluster create voiceresumeai --region sfo3
   ```

2. Update manifests for production:
   - Change image from `voiceresumeapp:latest` to `ghcr.io/voiceresumeai/voiceresumeapp:v1.0.0`
   - Change `imagePullPolicy: Never` to `Always`
   - Increase resource requests/limits
   - Add PersistentVolumeClaims with cloud storage

3. Deploy:
   ```bash
   kubectl apply -f apps/k8s-manifests/
   ```

4. Configure ingress for your domain

See `apps/k8s-manifests/README.md` for detailed production instructions.

## Further Reading

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [microk8s Documentation](https://microk8s.io/docs)
- [VoiceResume README](./README.md)
- [K8s Manifests README](./apps/k8s-manifests/README.md)
