#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}VoiceResume Local Development Setup${NC}"
echo "======================================"
echo ""

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}❌ Podman is not installed${NC}"
    echo "Please install Podman: https://podman.io/getting-started/installation/"
    exit 1
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo -e "${RED}❌ podman-compose is not installed${NC}"
    echo "Please install podman-compose: https://github.com/containers/podman-compose"
    exit 1
fi

# Check if Podman socket is accessible (for rootless mode)
if ! podman ps &> /dev/null; then
    echo -e "${RED}❌ Podman socket is not accessible${NC}"
    echo "Please check your Podman installation and socket permissions"
    exit 1
fi

echo -e "${GREEN}✓ Podman and podman-compose are installed${NC}"
echo ""

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local from template...${NC}"
    cp .env.example .env.local
    echo -e "${GREEN}✓ Created .env.local${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Remember to add your OPENAI_API_KEY to .env.local if you have one${NC}"
    echo "   Otherwise, transcription and resume generation will fail"
    echo ""
fi

# Ask user which setup option they want
echo -e "${YELLOW}Select development environment:${NC}"
echo "1) Docker Compose (fast, recommended for development)"
echo "2) Kubernetes with microk8s (production-like, slower)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Starting Docker Compose environment...${NC}"
        docker compose -f docker-compose.local.yml up -d

        echo ""
        echo -e "${YELLOW}Waiting for services to be ready...${NC}"
        sleep 5

        # Check if services are healthy
        if docker compose -f docker-compose.local.yml ps | grep -q "healthy\|running"; then
            echo -e "${GREEN}✓ Services are starting${NC}"
            echo ""
            echo -e "${YELLOW}Applying database migrations...${NC}"
            docker compose -f docker-compose.local.yml exec -T voiceresumeapp alembic upgrade head || true
            echo ""
            echo -e "${GREEN}✓ Setup complete!${NC}"
            echo ""
            echo "Services running:"
            echo "  📱 API:        http://localhost:8000"
            echo "  📊 Swagger:    http://localhost:8000/docs"
            echo "  🗄️  Database:   localhost:5432"
            echo "  💾 Minio:      http://localhost:9001 (minioadmin/minioadmin)"
            echo "  🖥️  PgAdmin:    http://localhost:5050 (admin@admin.com/admin)"
            echo ""
            echo "Next steps:"
            echo "  1. View logs:  docker compose -f docker-compose.local.yml logs -f"
            echo "  2. Run tests:  docker compose -f docker-compose.local.yml exec voiceresumeapp pytest tests/ -v"
            echo "  3. Stop:       docker compose -f docker-compose.local.yml down"
        else
            echo -e "${RED}✗ Services failed to start${NC}"
            echo "Check logs: docker compose -f docker-compose.local.yml logs"
            exit 1
        fi
        ;;
    2)
        echo ""
        echo -e "${YELLOW}Checking for microk8s...${NC}"

        if ! command -v microk8s &> /dev/null; then
            echo -e "${RED}❌ microk8s is not installed${NC}"
            echo "Install with: sudo snap install microk8s --classic"
            exit 1
        fi

        if ! command -v kubectl &> /dev/null; then
            echo -e "${RED}❌ kubectl is not installed${NC}"
            echo "Install with: sudo snap install kubectl --classic"
            exit 1
        fi

        echo -e "${GREEN}✓ microk8s and kubectl are installed${NC}"
        echo ""
        echo -e "${YELLOW}Starting Kubernetes environment with make dev-up...${NC}"
        make dev-up

        echo ""
        echo -e "${GREEN}✓ Kubernetes environment is running!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Get service IP:  microk8s kubectl get svc -n production"
        echo "  2. View logs:       make dev-logs"
        echo "  3. Stop:            make dev-down"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}For more details, see SETUP.md${NC}"
