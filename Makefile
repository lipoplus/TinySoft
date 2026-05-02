.PHONY: help setup dev-up dev-down dev-reset dev-logs dev-logs-all dev-validate dev-shell dev-psql dev-build dev-test dev-lint clean docker-up docker-down docker-logs docker-test docker-shell

K8S_NAMESPACE ?= production
DOCKER_IMAGE ?= voiceresumeapp:latest
COMPOSE_FILE ?= docker-compose.local.yml

help:
	@echo "VoiceResume Local Development"
	@echo ""
	@echo "QUICK START (Docker Compose - Recommended):"
	@echo "  make setup           - Interactive setup (choose Docker Compose or K8s)"
	@echo "  make docker-up       - Start services with Docker Compose"
	@echo "  make docker-down     - Stop Docker Compose services"
	@echo "  make docker-logs     - View Docker Compose logs"
	@echo "  make docker-test     - Run tests in Docker"
	@echo ""
	@echo "KUBERNETES (microk8s - Option 2):"
	@echo "  make dev-up          - Start K8s cluster with all services"
	@echo "  make dev-down        - Stop microk8s (preserves data)"
	@echo "  make dev-reset       - Reset microk8s completely (deletes all data)"
	@echo "  make dev-logs        - Tail API logs"
	@echo "  make dev-logs-all    - Tail all service logs"
	@echo "  make dev-validate    - Check K8s setup status"
	@echo "  make dev-shell       - Open shell in API container"
	@echo "  make dev-psql        - Connect to PostgreSQL"
	@echo ""
	@echo "UTILITIES:"
	@echo "  make dev-build       - Build Docker image locally"
	@echo "  make dev-test        - Run tests"
	@echo "  make dev-lint        - Lint code"
	@echo "  make clean           - Clean up build artifacts"

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
	docker build -t $(DOCKER_IMAGE) -t $(DOCKER_IMAGE):dev .

	@echo "Loading image into microk8s..."
	microk8s ctr image import <(docker save $(DOCKER_IMAGE)) || true

	@echo "Creating namespace..."
	microk8s kubectl create namespace $(K8S_NAMESPACE) || true

	@echo "Creating secrets (dev defaults)..."
	microk8s kubectl create secret generic voiceresumeapp-secrets \
	  --from-literal=OPENAI_API_KEY=sk-dev-key \
	  --from-literal=JWT_SECRET=dev-secret-key-change-in-production \
	  --from-literal=DB_PASSWORD=voiceresumeai \
	  -n $(K8S_NAMESPACE) || true

	@echo "Applying manifests (order matters)..."
	microk8s kubectl apply -f apps/k8s-manifests/postgres-deployment.yaml
	microk8s kubectl apply -f apps/k8s-manifests/minio-deployment.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-configmap.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-deployment.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-service.yaml
	microk8s kubectl apply -f apps/k8s-manifests/voiceresumeapp-ingress.yaml || true

	@echo ""
	@echo "Waiting for services to be ready (this may take 1-2 minutes)..."
	@echo "PostgreSQL starting..."
	@until microk8s kubectl get pods -n $(K8S_NAMESPACE) -l app=postgres | grep -q Running; do sleep 2; done
	@echo "✓ PostgreSQL ready"

	@echo "Minio starting..."
	@until microk8s kubectl get pods -n $(K8S_NAMESPACE) -l app=minio | grep -q Running; do sleep 2; done
	@echo "✓ Minio ready"

	@echo "API starting..."
	@until microk8s kubectl get pods -n $(K8S_NAMESPACE) -l app=voiceresumeapp | grep -q Running; do sleep 2; done
	@echo "✓ API ready"

	@echo ""
	@echo "Waiting for deployment rollout..."
	microk8s kubectl rollout status deployment/voiceresumeapp -n $(K8S_NAMESPACE) --timeout=3m || true

	@echo ""
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Services running:"
	@echo "  📱 API:        http://voiceresumeapp.local:8000"
	@echo "  📊 Swagger:    http://voiceresumeapp.local:8000/docs"
	@echo "  💾 Minio:      kubectl port-forward -n $(K8S_NAMESPACE) svc/minio-svc 9001:9001"
	@echo "  🗄️  Database:   postgresql://voiceresumeai@postgres-svc:5432/voiceresumeai"
	@echo ""
	@echo "Next steps:"
	@echo "  1. View logs:     make dev-logs"
	@echo "  2. Validate:      bash scripts/validate-k8s.sh"
	@echo "  3. Get service IP and add to /etc/hosts:"
	@echo "     SERVICE_IP=$$(microk8s kubectl get svc voiceresumeapp-svc -n $(K8S_NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
	@echo "     echo \"$$SERVICE_IP voiceresumeapp.local\" | sudo tee -a /etc/hosts"

dev-down:
	@echo "Stopping microk8s..."
	microk8s stop || true
	@echo "✓ microk8s stopped. Data preserved."

dev-reset:
	@echo "Resetting microk8s completely (deletes all data)..."
	microk8s reset || true
	@echo "✓ microk8s reset complete."

dev-logs:
	microk8s kubectl logs -n $(K8S_NAMESPACE) -l app=voiceresumeapp -f

dev-logs-all:
	microk8s kubectl logs -n $(K8S_NAMESPACE) -f --tail=50 \
	  -l 'app in (voiceresumeapp,postgres,minio)'

dev-validate:
	@bash scripts/validate-k8s.sh

dev-shell:
	microk8s kubectl exec -it -n $(K8S_NAMESPACE) deployment/voiceresumeapp -- /bin/bash

dev-psql:
	microk8s kubectl run -it --rm --image=postgres:16-alpine --restart=Never \
	  -- psql -h postgres-svc -U voiceresumeai -d voiceresumeai

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
