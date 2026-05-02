# Kubernetes Manifests

Manifests for deploying VoiceResume to Kubernetes.

## Local Development (microk8s)

```bash
# Start microk8s
microk8s start

# Enable required services
microk8s enable dns storage ingress

# Apply manifests
microk8s kubectl apply -f voiceresumeapp-configmap.yaml
microk8s kubectl apply -f voiceresumeapp-deployment.yaml
microk8s kubectl apply -f voiceresumeapp-service.yaml
microk8s kubectl apply -f voiceresumeapp-ingress.yaml

# Check status
microk8s kubectl get pods -n production
microk8s kubectl logs -n production -l app=voiceresumeapp -f

# Get service IP and add to /etc/hosts
microk8s kubectl get svc -n production
# Then add: <IP> voiceresumeapp.local
```

Or simply use the Makefile:
```bash
make dev-up      # Start microk8s and deploy
make dev-logs    # Watch logs
make dev-down    # Stop microk8s
```

## Production (DigitalOcean DOKS)

1. Create DOKS cluster via DigitalOcean dashboard
2. Configure kubectl context: `doctl kubernetes cluster kubeconfig save <cluster-id>`
3. Create secrets: `kubectl create secret generic voiceresumeapp-secrets -n production --from-env-file=.env.prod`
4. Apply manifests as above

## Secrets

Create secrets via:

```bash
kubectl create secret generic voiceresumeapp-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=JWT_SECRET=<generated-secret> \
  --from-literal=S3_ACCESS_KEY=... \
  --from-literal=S3_SECRET_KEY=... \
  -n production
```

## Updating Images

Push new images to GHCR:

```bash
docker tag voiceresumeapp:latest ghcr.io/voiceresumeai/voiceresumeapp:<commit-sha>
docker push ghcr.io/voiceresumeai/voiceresumeapp:<commit-sha>
```

Then update the Deployment:

```bash
kubectl set image deployment/voiceresumeapp voiceresumeapp=ghcr.io/voiceresumeai/voiceresumeapp:<commit-sha> -n production
```

Or use GitOps (Flux/ArgoCD) for automated rollouts.
