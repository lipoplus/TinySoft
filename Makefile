.PHONY: help dev-up dev-down dev-logs dev-build dev-test dev-lint clean

K8S_NAMESPACE ?= production
DOCKER_IMAGE ?= voiceresumeapp:latest

help:
	@echo "VoiceResume Local Development (microk8s)"
	@echo ""
	@echo "Usage:"
	@echo "  make dev-up       - Start microk8s and apply manifests"
	@echo "  make dev-down     - Stop microk8s"
	@echo "  make dev-logs     - Tail application logs"
	@echo "  make dev-build    - Build Docker image locally"
	@echo "  make dev-test     - Run tests"
	@echo "  make dev-lint     - Lint code"
	@echo "  make clean        - Clean up build artifacts"

dev-up:
	@echo "Starting microk8s..."
	microk8s start || true

	@echo "Waiting for microk8s to be ready..."
	@until microk8s status --wait-ready; do sleep 2; done

	@echo "Enabling required services..."
	microk8s enable dns storage ingress || true

	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

	@echo "Pushing image to microk8s registry..."
	docker tag $(DOCKER_IMAGE) localhost:32000/$(DOCKER_IMAGE)
	docker push localhost:32000/$(DOCKER_IMAGE) || true

	@echo "Creating namespace..."
	microk8s kubectl create namespace $(K8S_NAMESPACE) || true

	@echo "Creating secrets (dev defaults)..."
	microk8s kubectl create secret generic voiceresumeapp-secrets \
	  --from-literal=OPENAI_API_KEY=sk-dev-key \
	  --from-literal=JWT_SECRET=dev-secret-key-change-in-production \
	  --from-literal=S3_ACCESS_KEY=dev-key \
	  --from-literal=S3_SECRET_KEY=dev-secret \
	  -n $(K8S_NAMESPACE) || true

	@echo "Applying manifests..."
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-configmap.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-deployment.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-service.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-ingress.yaml || true

	@echo "Waiting for deployment to be ready..."
	microk8s kubectl rollout status deployment/voiceresumeapp -n $(K8S_NAMESPACE) --timeout=2m || true

	@echo "Development environment ready!"
	@echo "To access the app:"
	@echo "  1. Get the service IP: microk8s kubectl get svc -n $(K8S_NAMESPACE)"
	@echo "  2. Add /etc/hosts entry: <IP> voiceresumeapp.local"
	@echo "  3. Visit: http://voiceresumeapp.local"

dev-down:
	@echo "Stopping microk8s..."
	microk8s stop || true
	@echo "microk8s stopped."

dev-logs:
	microk8s kubectl logs -n $(K8S_NAMESPACE) -l app=voiceresumeapp -f

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
