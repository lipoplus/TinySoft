# Kubernetes Manifests — Option 2: Production-Like Environment

Complete Kubernetes setup for VoiceResume with full infrastructure (API, PostgreSQL, Minio S3, Ingress).

## Files Overview

- **voiceresumeapp-configmap.yaml** — API environment configuration
- **voiceresumeapp-deployment.yaml** — API with init container for migrations
- **voiceresumeapp-service.yaml** — API service (ClusterIP)
- **voiceresumeapp-ingress.yaml** — HTTP ingress
- **postgres-deployment.yaml** — PostgreSQL with persistent volume (NEW)
- **minio-deployment.yaml** — Minio S3 storage with persistent volume (NEW)

## Local Development with microk8s (Recommended for Option 2)

### Prerequisites
```bash
# Install microk8s (Linux)
sudo snap install microk8s --classic
sudo snap install kubectl --classic

# Verify
microk8s status
```

### Automated Setup (Recommended)
```bash
# Use the Makefile target
make dev-up

# Watch logs
make dev-logs

# Stop cluster
make dev-down
```

### Manual Setup
```bash
# 1. Start and configure microk8s
microk8s start
microk8s enable dns storage ingress

# 2. Build local Podman image
podman build -t voiceresumeapp:latest .

# 3. Load image into microk8s
microk8s ctr image import <(podman save voiceresumeapp:latest)

# 4. Create namespace
microk8s kubectl create namespace production

# 5. Create secrets with your API key
microk8s kubectl create secret generic voiceresumeapp-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key-here \
  --from-literal=JWT_SECRET=dev-secret-key-change-in-prod \
  --from-literal=DB_PASSWORD=voiceresumeai \
  -n production

# 6. Apply all manifests (order matters)
microk8s kubectl apply -f postgres-deployment.yaml
microk8s kubectl apply -f minio-deployment.yaml
microk8s kubectl apply -f voiceresumeapp-configmap.yaml
microk8s kubectl apply -f voiceresumeapp-deployment.yaml
microk8s kubectl apply -f voiceresumeapp-service.yaml
microk8s kubectl apply -f voiceresumeapp-ingress.yaml

# 7. Wait for pods to be ready
microk8s kubectl get pods -n production -w

# 8. Get LoadBalancer IP and configure /etc/hosts
SERVICE_IP=$(microk8s kubectl get svc voiceresumeapp-svc -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$SERVICE_IP voiceresumeapp.local" | sudo tee -a /etc/hosts

# 9. Access the application
curl http://voiceresumeapp.local
```

## Checking Status

```bash
# List all resources
microk8s kubectl get all -n production

# Check pod status
microk8s kubectl get pods -n production

# Describe a specific pod
microk8s kubectl describe pod voiceresumeapp-xxx -n production

# View logs
microk8s kubectl logs -n production -l app=voiceresumeapp -f
microk8s kubectl logs -n production -l app=postgres -f
microk8s kubectl logs -n production -l app=minio -f

# Port-forward for direct access
microk8s kubectl port-forward -n production svc/minio-svc 9001:9001  # Minio console
```

## Testing the Setup

```bash
# Test API health
curl http://voiceresumeapp.local/health

# View API documentation
curl http://voiceresumeapp.local/docs

# Access Minio console (after port-forward)
# Visit http://localhost:9001 (minioadmin / minioadmin)

# Access database via psql
microk8s kubectl run -it --rm --image=postgres:16-alpine --restart=Never \
  -- psql -h postgres-svc -U voiceresumeai -d voiceresumeai -c "SELECT 1;"
```

## Scaling and Monitoring

```bash
# Scale the API
microk8s kubectl scale deployment voiceresumeapp --replicas=3 -n production

# Watch rollout progress
microk8s kubectl rollout status deployment/voiceresumeapp -n production

# View metrics (requires metrics-server)
microk8s enable metrics-server
microk8s kubectl top pods -n production
```

## Production Deployment (DigitalOcean DOKS)

### Setup DOKS Cluster
```bash
# Create cluster and configure context
doctl kubernetes cluster create voiceresumeai --region sfo3 --node-pool-name workers
doctl kubernetes cluster kubeconfig save voiceresumeai
```

### Deploy to Production
```bash
# 1. Create namespace
kubectl create namespace production

# 2. Create secrets with production values
kubectl create secret generic voiceresumeapp-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=JWT_SECRET=<strong-random-key> \
  --from-literal=DB_PASSWORD=<strong-random-password> \
  -n production

# 3. Push image to GHCR with Podman
podman tag voiceresumeapp:latest ghcr.io/voiceresumeai/voiceresumeapp:<version>
podman push ghcr.io/voiceresumeai/voiceresumeapp:<version>

# 4. Update deployment image reference in voiceresumeapp-deployment.yaml
# Change: imagePullPolicy: Never → Always
# Change: image: voiceresumeapp:latest → ghcr.io/voiceresumeai/voiceresumeapp:<version>

# 5. Apply manifests
kubectl apply -f postgres-deployment.yaml
kubectl apply -f minio-deployment.yaml
kubectl apply -f voiceresumeapp-configmap.yaml
kubectl apply -f voiceresumeapp-deployment.yaml
kubectl apply -f voiceresumeapp-service.yaml
kubectl apply -f voiceresumeapp-ingress.yaml

# 6. Verify deployment
kubectl get all -n production
```

## Troubleshooting

### Pods not starting
```bash
# Check pod events
microk8s kubectl describe pod <pod-name> -n production

# Check logs
microk8s kubectl logs <pod-name> -n production

# Check resource availability
microk8s kubectl top nodes
```

### Image pull failed
```bash
# For local dev: ensure image is loaded
podman build -t voiceresumeapp:latest .
microk8s ctr image import <(podman save voiceresumeapp:latest)

# For DOKS: ensure image is pushed to GHCR and imagePullPolicy is set
```

### Database connection failed
```bash
# Check postgres pod
microk8s kubectl logs -l app=postgres -n production

# Test connection from another pod
microk8s kubectl run -it --rm --image=postgres:16-alpine --restart=Never \
  -- psql -h postgres-svc -U voiceresumeai -d voiceresumeai
```

### Storage issues
```bash
# Check PVCs
microk8s kubectl get pvc -n production

# Check PV status
microk8s kubectl get pv
```

## Cleanup

```bash
# Stop microk8s (keeps data)
microk8s stop

# Remove namespace and all resources
microk8s kubectl delete namespace production

# Reset microk8s completely
microk8s reset
```
