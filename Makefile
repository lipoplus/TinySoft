.PHONY: help dev-up dev-down dev-logs dev-build dev-test dev-lint clean

CLUSTER_NAME ?= voiceresumeai
K8S_NAMESPACE ?= production
DOCKER_IMAGE ?= voiceresumeapp:latest

help:
	@echo "VoiceResume Local Development"
	@echo ""
	@echo "Usage:"
	@echo "  make dev-up       - Start local K3s cluster and apply manifests"
	@echo "  make dev-down     - Stop and remove local K3s cluster"
	@echo "  make dev-logs     - Tail application logs"
	@echo "  make dev-build    - Build Docker image locally"
	@echo "  make dev-test     - Run tests"
	@echo "  make dev-lint     - Lint code"
	@echo "  make clean        - Clean up build artifacts"

dev-up:
	@echo "Starting K3s cluster..."
	k3d cluster create $(CLUSTER_NAME) --agents 1 --servers 1 -p "8080:80@loadbalancer" || true

	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

	@echo "Loading image into K3s..."
	k3d image import $(DOCKER_IMAGE) -c $(CLUSTER_NAME)

	@echo "Creating namespace..."
	kubectl create namespace $(K8S_NAMESPACE) || true

	@echo "Creating secrets (dev defaults)..."
	kubectl create secret generic voiceresumeapp-secrets \
	  --from-literal=OPENAI_API_KEY=sk-dev-key \
	  --from-literal=JWT_SECRET=dev-secret-key-change-in-production \
	  --from-literal=S3_ACCESS_KEY=dev-key \
	  --from-literal=S3_SECRET_KEY=dev-secret \
	  -n $(K8S_NAMESPACE) || true

	@echo "Applying manifests..."
	kubectl apply -f apps/k8s-manifests/voiceresumeapp-configmap.yaml
	kubectl apply -f apps/k8s-manifests/voiceresumeapp-deployment.yaml
	kubectl apply -f apps/k8s-manifests/voiceresumeapp-service.yaml
	kubectl apply -f apps/k8s-manifests/voiceresumeapp-ingress.yaml || true

	@echo "Waiting for deployment to be ready..."
	kubectl rollout status deployment/voiceresumeapp -n $(K8S_NAMESPACE) --timeout=2m || true

	@echo "Development environment ready!"
	@echo "App will be available at: http://localhost:8080"

dev-down:
	@echo "Removing K3s cluster..."
	k3d cluster delete $(CLUSTER_NAME) || true
	@echo "Cluster removed."

dev-logs:
	kubectl logs -n $(K8S_NAMESPACE) -l app=voiceresumeapp -f

dev-build:
	docker build -t $(DOCKER_IMAGE) .

dev-test:
	pip install -r apps/voiceresumeapp/requirements.txt
	pytest apps/voiceresumeapp/tests/ -v

dev-lint:
	pip install ruff
	ruff check apps/voiceresumeapp/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/
