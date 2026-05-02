.PHONY: help dev-up dev-down dev-logs dev-build dev-test dev-lint clean setup docker-up docker-down docker-logs docker-test

K8S_NAMESPACE ?= production
DOCKER_IMAGE ?= voiceresumeapp:latest
COMPOSE_FILE ?= docker-compose.local.yml

help:
	@echo "VoiceResume Local Development"
	@echo ""
	@echo "QUICK START (Docker Compose - Recommended):"
	@echo "  make setup        - Interactive setup (choose Docker Compose or K8s)"
	@echo "  make docker-up    - Start services with Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose services"
	@echo "  make docker-logs  - View Docker Compose logs"
	@echo "  make docker-test  - Run tests in Docker"
	@echo ""
	@echo "KUBERNETES (microk8s):"
	@echo "  make dev-up       - Start microk8s and apply manifests"
	@echo "  make dev-down     - Stop microk8s"
	@echo "  make dev-logs     - Tail K8s application logs"
	@echo ""
	@echo "UTILITIES:"
	@echo "  make dev-build    - Build Docker image locally"
	@echo "  make dev-lint     - Lint code"
	@echo "  make clean        - Clean up build artifacts"

setup:
	@bash scripts/setup-local-dev.sh

docker-up:
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "Services starting... waiting 5 seconds for health checks"
	@sleep 5
	@echo ""
	@echo "✓ Services are starting!"
	@echo "  API:     http://localhost:8000"
	@echo "  Swagger: http://localhost:8000/docs"
	@echo "  Minio:   http://localhost:9001"
	@echo "  PgAdmin: http://localhost:5050"
	@echo ""
	@echo "Run 'make docker-logs' to watch logs"

docker-down:
	docker compose -f $(COMPOSE_FILE) down

docker-logs:
	docker compose -f $(COMPOSE_FILE) logs -f voiceresumeapp

docker-test:
	docker compose -f $(COMPOSE_FILE) exec voiceresumeapp pytest tests/ -v

docker-shell:
	docker compose -f $(COMPOSE_FILE) exec voiceresumeapp bash

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
