#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}VoiceResume K8s Environment Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper function to print check results
check_command() {
    local name=$1
    local command=$2

    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $name"
        ((CHECKS_FAILED++))
    fi
}

# Helper function to check service
check_service() {
    local name=$1
    local label=$2

    if kubectl get pods -n production -l app=$label 2>/dev/null | grep -q Running; then
        echo -e "${GREEN}✓${NC} $name is running"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $name is not running"
        ((CHECKS_FAILED++))
    fi
}

echo -e "${YELLOW}Prerequisites:${NC}"
check_command "microk8s installed" "which microk8s"
check_command "kubectl installed" "which kubectl"
check_command "docker installed" "which docker"

echo ""
echo -e "${YELLOW}microk8s Status:${NC}"
if microk8s status &>/dev/null; then
    echo -e "${GREEN}✓${NC} microk8s is running"
    ((CHECKS_PASSED++))

    echo ""
    echo -e "${YELLOW}K8s Services:${NC}"

    # Check if production namespace exists
    if kubectl get namespace production &>/dev/null; then
        echo -e "${GREEN}✓${NC} production namespace exists"
        ((CHECKS_PASSED++))

        # Check services
        echo ""
        echo -e "${YELLOW}Deployment Status:${NC}"
        check_service "PostgreSQL" "postgres"
        check_service "Minio" "minio"
        check_service "VoiceResume API" "voiceresumeapp"

        # Check secrets
        echo ""
        echo -e "${YELLOW}Configuration:${NC}"
        if kubectl get secret voiceresumeapp-secrets -n production &>/dev/null; then
            echo -e "${GREEN}✓${NC} secrets are configured"
            ((CHECKS_PASSED++))
        else
            echo -e "${YELLOW}!${NC} secrets not yet configured (will be created by make dev-up)"
        fi

        if kubectl get configmap voiceresumeapp-config -n production &>/dev/null; then
            echo -e "${GREEN}✓${NC} configmap is configured"
            ((CHECKS_PASSED++))
        else
            echo -e "${YELLOW}!${NC} configmap not yet deployed"
        fi

        # Check PVCs
        echo ""
        echo -e "${YELLOW}Storage:${NC}"
        if kubectl get pvc -n production 2>/dev/null | grep -q postgres-pvc; then
            echo -e "${GREEN}✓${NC} PostgreSQL persistent volume exists"
            ((CHECKS_PASSED++))
        else
            echo -e "${YELLOW}!${NC} PostgreSQL persistent volume not yet created"
        fi

        if kubectl get pvc -n production 2>/dev/null | grep -q minio-pvc; then
            echo -e "${GREEN}✓${NC} Minio persistent volume exists"
            ((CHECKS_PASSED++))
        else
            echo -e "${YELLOW}!${NC} Minio persistent volume not yet created"
        fi

    else
        echo -e "${YELLOW}!${NC} production namespace not created (will be created by make dev-up)"
    fi
else
    echo -e "${RED}✗${NC} microk8s is not running"
    echo ""
    echo "To start microk8s:"
    echo "  microk8s start"
    ((CHECKS_FAILED++))
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your K8s environment is ready. Try:"
    echo "  microk8s kubectl get all -n production"
    echo "  microk8s kubectl logs -f -n production -l app=voiceresumeapp"
    exit 0
else
    if microk8s status &>/dev/null; then
        echo -e "${YELLOW}Note:${NC} Some services may still be starting. Run 'make dev-logs' to watch progress."
    else
        echo -e "${RED}Note:${NC} To set up K8s environment, run: make dev-up"
    fi
    exit 1
fi
