#!/bin/bash
# ArgoCD CLI Examples for PDF Comparator AI
# Author: Carlos Estay (cestay@redhat.com)

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}ArgoCD CLI Examples - PDF Comparator AI${NC}\n"

# Login to ArgoCD
echo -e "${YELLOW}1. Login to ArgoCD:${NC}"
echo "argocd login openshift-gitops-server-openshift-gitops.apps.your-cluster.com"
echo ""

# List applications
echo -e "${YELLOW}2. List all PDF Comparator applications:${NC}"
echo "argocd app list | grep pdf-comparator"
echo ""

# Get current parameters
echo -e "${YELLOW}3. View current parameters for an environment:${NC}"
echo "argocd app get dev-pdf-comparator --show-params"
echo ""

# Basic parameter updates
echo -e "${BLUE}=== Basic Configuration ===${NC}"
echo -e "${YELLOW}4. Update replica count:${NC}"
echo "argocd app set dev-pdf-comparator -p app.replicaCount=3"
echo ""

echo -e "${YELLOW}5. Change log level:${NC}"
echo "argocd app set dev-pdf-comparator -p config.logLevel=DEBUG"
echo ""

# vLLM Configuration
echo -e "${BLUE}=== vLLM Configuration ===${NC}"
echo -e "${YELLOW}6. Update vLLM endpoint:${NC}"
echo "argocd app set dev-pdf-comparator -p vllm.endpoint=http://vllm-custom:8000"
echo ""

echo -e "${YELLOW}7. Configure model parameters:${NC}"
cat << 'EOF'
argocd app set dev-pdf-comparator \
  -p vllm.model.name=granite-3.1-8b-instruct \
  -p vllm.model.maxTokens=4096 \
  -p vllm.model.temperature=0.2 \
  -p vllm.model.topP=0.9
EOF
echo ""

# Feature flags
echo -e "${BLUE}=== Feature Flags ===${NC}"
echo -e "${YELLOW}8. Enable/disable features:${NC}"
cat << 'EOF'
argocd app set dev-pdf-comparator \
  -p config.features.enableDebugEndpoints=true \
  -p config.features.enableCaching=true \
  -p config.features.enableSemanticAnalysis=true
EOF
echo ""

# Resources
echo -e "${BLUE}=== Resource Configuration ===${NC}"
echo -e "${YELLOW}9. Update resource limits:${NC}"
cat << 'EOF'
argocd app set prod-pdf-comparator \
  -p app.resources.requests.memory=1Gi \
  -p app.resources.requests.cpu=500m \
  -p app.resources.limits.memory=4Gi \
  -p app.resources.limits.cpu=2000m
EOF
echo ""

# Autoscaling
echo -e "${BLUE}=== Autoscaling ===${NC}"
echo -e "${YELLOW}10. Enable autoscaling:${NC}"
cat << 'EOF'
argocd app set prod-pdf-comparator \
  -p autoscaling.enabled=true \
  -p autoscaling.minReplicas=4 \
  -p autoscaling.maxReplicas=20 \
  -p autoscaling.targetCPUUtilizationPercentage=75
EOF
echo ""

# Complete environment update
echo -e "${BLUE}=== Complete Environment Update ===${NC}"
echo -e "${YELLOW}11. Update multiple parameters at once:${NC}"
cat << 'EOF'
argocd app set staging-pdf-comparator \
  -p app.replicaCount=3 \
  -p app.image.tag=v2.0.0 \
  -p config.logLevel=INFO \
  -p vllm.model.temperature=0.3 \
  -p config.maxPdfSizeMb=100 \
  -p config.features.enableMetrics=true \
  -p monitoring.enabled=true \
  -p monitoring.interval=15s
EOF
echo ""

# Sync and wait
echo -e "${BLUE}=== Sync Operations ===${NC}"
echo -e "${YELLOW}12. Sync application after changes:${NC}"
echo "argocd app sync dev-pdf-comparator"
echo ""

echo -e "${YELLOW}13. Sync with prune:${NC}"
echo "argocd app sync dev-pdf-comparator --prune"
echo ""

echo -e "${YELLOW}14. Wait for sync to complete:${NC}"
echo "argocd app wait dev-pdf-comparator --sync"
echo ""

# Rollback
echo -e "${BLUE}=== Rollback ===${NC}"
echo -e "${YELLOW}15. View history:${NC}"
echo "argocd app history dev-pdf-comparator"
echo ""

echo -e "${YELLOW}16. Rollback to previous version:${NC}"
echo "argocd app rollback dev-pdf-comparator 1"
echo ""

# Diff
echo -e "${BLUE}=== Diff Operations ===${NC}"
echo -e "${YELLOW}17. View diff before sync:${NC}"
echo "argocd app diff dev-pdf-comparator"
echo ""

# Refresh
echo -e "${YELLOW}18. Hard refresh (force reconciliation):${NC}"
echo "argocd app get dev-pdf-comparator --hard-refresh"
echo ""

echo -e "${GREEN}For more information, visit: https://github.com/pkstaz/pdf-comparator-ai${NC}"