# Kubernetes Manifests

Manifests for deploying VoiceResume to Kubernetes.

## Local Development (K3s via k3d)

```bash
# Create cluster with K3d
k3d cluster create voiceresumeai --agents 1 --servers 1 -p "8080:80@loadbalancer"

# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f voiceresumeapp-configmap.yaml
kubectl apply -f voiceresumeapp-deployment.yaml
kubectl apply -f voiceresumeapp-service.yaml
kubectl apply -f voiceresumeapp-ingress.yaml

# Check status
kubectl get pods -n production
kubectl logs -n production -l app=voiceresumeapp -f
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
