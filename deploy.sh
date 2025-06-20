#!/bin/bash
# PDF Comparator AI - Demo Deployment Script
# Author: Carlos Estay (cestay@redhat.com)
# Description: Deploys PDF Comparator AI demo without vLLM (assumes Granite model already deployed)

set -e

# Configuration
PROJECT_NAME="pdf-comparator"
DEMO_NAMESPACE="${PROJECT_NAME}-demo"
GRANITE_ENDPOINT="${GRANITE_ENDPOINT:-http://granite-service.vllm.svc.cluster.local:8000}"
GRANITE_MODEL_NAME="${GRANITE_MODEL_NAME:-granite-3.1-8b-instruct}"
GIT_REPO="https://github.com/pkstaz/pdf-comparator-ai.git"
GIT_BRANCH="${GIT_BRANCH:-master}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo -e "${GREEN}=================================================${NC}"
    echo -e "${GREEN}   PDF Comparator AI - Demo Deployment${NC}"
    echo -e "${GREEN}=================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if logged in to OpenShift
    if ! oc whoami &> /dev/null; then
        print_error "Not logged in to OpenShift"
        echo "Please run: oc login <cluster-url>"
        exit 1
    fi
    
    CURRENT_USER=$(oc whoami)
    CLUSTER_URL=$(oc whoami --show-server)
    print_info "Logged in as: ${GREEN}${CURRENT_USER}${NC}"
    print_info "Cluster: ${GREEN}${CLUSTER_URL}${NC}"
    
    # Check if ArgoCD is available
    if oc get namespace openshift-gitops &> /dev/null; then
        print_success "ArgoCD (OpenShift GitOps) is available"
        USE_ARGOCD=true
    else
        print_warning "ArgoCD not found. Will deploy using standard manifests"
        USE_ARGOCD=false
    fi
    
    # Check if the Granite model endpoint is accessible
    print_info "Checking Granite model endpoint: ${GRANITE_ENDPOINT}"
    if oc get svc -A | grep -q granite; then
        print_success "Granite service found in cluster"
    else
        print_warning "Granite service not found. Make sure to set GRANITE_ENDPOINT correctly"
    fi
    
    echo ""
}

# Create namespace
create_namespace() {
    print_info "Creating namespace: ${DEMO_NAMESPACE}"
    
    if oc get namespace ${DEMO_NAMESPACE} &> /dev/null; then
        print_warning "Namespace ${DEMO_NAMESPACE} already exists"
    else
        oc new-project ${DEMO_NAMESPACE} \
            --display-name="PDF Comparator Demo" \
            --description="PDF Comparator AI Demo - Using Granite 3.1 Model"
        print_success "Namespace created"
    fi
    
    # Label namespace for ArgoCD if available
    if [ "$USE_ARGOCD" = true ]; then
        oc label namespace ${DEMO_NAMESPACE} \
            argocd.argoproj.io/managed-by=openshift-gitops \
            app=pdf-comparator \
            environment=demo \
            --overwrite
    fi
    
    # Add namespace to user's favorites in OpenShift Console
    print_info "Adding namespace to console favorites..."
    
    # Get current user
    CURRENT_USER=$(oc whoami)
    
    # Create or update the console user settings to add namespace as favorite
    # This uses the console.openshift.io/v1 API
    cat <<EOF | oc apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-settings-${CURRENT_USER//[^a-zA-Z0-9-]/-}
  namespace: openshift-console-user-settings
  labels:
    console.openshift.io/user-settings: "true"
    console.openshift.io/user: "${CURRENT_USER}"
data:
  favorite-namespaces: |
    - ${DEMO_NAMESPACE}
EOF
    
    # Alternative method using console preferences
    # This adds the namespace to the pinned resources
    oc annotate namespace ${DEMO_NAMESPACE} \
        openshift.io/display-name="PDF Comparator Demo ⭐" \
        --overwrite
    
    print_success "Namespace added to favorites"
}

# Create ConfigMaps and Secrets
create_configs() {
    print_info "Creating ConfigMaps and Secrets..."
    
    # Create main ConfigMap
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdf-comparator-config
  labels:
    app: pdf-comparator
data:
  APP_NAME: "pdf-comparator-demo"
  APP_ENV: "demo"
  LOG_LEVEL: "INFO"
  
  # vLLM Configuration (pointing to existing Granite deployment)
  VLLM_ENDPOINT: "${GRANITE_ENDPOINT}"
  VLLM_MODEL_NAME: "${GRANITE_MODEL_NAME}"
  VLLM_MAX_TOKENS: "2048"
  VLLM_TEMPERATURE: "0.3"
  VLLM_TOP_P: "0.95"
  
  # Redis Configuration (optional - will use in-memory if not available)
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  ENABLE_REDIS: "false"
  
  # Feature Flags
  ENABLE_CACHING: "true"
  ENABLE_METRICS: "true"
  ENABLE_SEMANTIC_ANALYSIS: "true"
  ENABLE_STRUCTURAL_ANALYSIS: "true"
  MAX_PDF_SIZE_MB: "50"
  SUPPORTED_LANGUAGES: "es,en,pt"
EOF
    
    # Create Secret for API keys (with dummy values for demo)
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: v1
kind: Secret
metadata:
  name: pdf-comparator-secrets
  labels:
    app: pdf-comparator
type: Opaque
stringData:
  VLLM_API_KEY: "${VLLM_API_KEY:-demo-api-key}"
EOF
    
    print_success "ConfigMaps and Secrets created"
}

# Deploy application
deploy_application() {
    print_info "Deploying PDF Comparator application..."
    
    # Create Deployment
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-comparator
  labels:
    app: pdf-comparator
    version: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pdf-comparator
  template:
    metadata:
      labels:
        app: pdf-comparator
        version: demo
    spec:
      containers:
      - name: pdf-comparator
        image: ghcr.io/pkstaz/pdf-comparator-ai:latest
        imagePullPolicy: Always
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        envFrom:
        - configMapRef:
            name: pdf-comparator-config
        - secretRef:
            name: pdf-comparator-secrets
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: temp
          mountPath: /app/temp
      volumes:
      - name: temp
        emptyDir: {}
EOF
    
    # Create Service
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: v1
kind: Service
metadata:
  name: pdf-comparator-service
  labels:
    app: pdf-comparator
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8000
    targetPort: http
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: metrics
    protocol: TCP
  selector:
    app: pdf-comparator
  sessionAffinity: ClientIP
EOF
    
    print_success "Application deployed"
}

# Create Route
create_route() {
    print_info "Creating Route for external access..."
    
    # Get cluster domain
    CLUSTER_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}')
    
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: pdf-comparator-route
  labels:
    app: pdf-comparator
  annotations:
    haproxy.router.openshift.io/timeout: 5m
spec:
  host: pdf-comparator-demo.${CLUSTER_DOMAIN}
  to:
    kind: Service
    name: pdf-comparator-service
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
EOF
    
    ROUTE_URL="https://pdf-comparator-demo.${CLUSTER_DOMAIN}"
    print_success "Route created: ${GREEN}${ROUTE_URL}${NC}"
}

# Deploy with ArgoCD
deploy_with_argocd() {
    print_info "Deploying with ArgoCD..."
    
    # Create ArgoCD Application
    cat <<EOF | oc apply -f - -n openshift-gitops
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: pdf-comparator-demo
  labels:
    app: pdf-comparator
spec:
  project: default
  source:
    repoURL: ${GIT_REPO}
    targetRevision: ${GIT_BRANCH}
    path: helm/pdf-comparator
    helm:
      parameters:
      - name: app.replicaCount
        value: "1"
      - name: vllm.enabled
        value: "false"
      - name: vllm.endpoint
        value: "${GRANITE_ENDPOINT}"
      - name: vllm.model.name
        value: "${GRANITE_MODEL_NAME}"
      - name: config.logLevel
        value: "INFO"
      - name: route.enabled
        value: "true"
      valueFiles:
      - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ${DEMO_NAMESPACE}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
    
    print_success "ArgoCD Application created"
    print_info "Waiting for ArgoCD to sync..."
    sleep 10
}

# Build and push image (optional)
build_image() {
    print_info "Building container image..."
    
    # Check if source code exists
    if [ ! -f "Dockerfile" ]; then
        print_warning "Dockerfile not found. Skipping build."
        print_info "Using pre-built image from registry"
        return
    fi
    
    # Get internal registry
    INTERNAL_REGISTRY=$(oc get route -n openshift-image-registry default-route -o jsonpath='{.spec.host}' 2>/dev/null)
    
    if [ -z "$INTERNAL_REGISTRY" ]; then
        print_warning "Internal registry not exposed. Using external image."
        return
    fi
    
    # Build using BuildConfig
    print_info "Creating BuildConfig..."
    oc new-build --binary --strategy=docker --name=pdf-comparator -n ${DEMO_NAMESPACE} || true
    
    print_info "Starting build..."
    oc start-build pdf-comparator --from-dir=. --follow -n ${DEMO_NAMESPACE}
    
    print_success "Image built successfully"
}

# Wait for deployment
wait_for_deployment() {
    print_info "Waiting for deployment to be ready..."
    
    oc wait deployment pdf-comparator \
        -n ${DEMO_NAMESPACE} \
        --for=condition=Available \
        --timeout=300s
    
    print_success "Deployment is ready"
}

# Display access information
display_info() {
    echo ""
    echo -e "${GREEN}=================================================${NC}"
    echo -e "${GREEN}   Deployment Completed Successfully! 🎉${NC}"
    echo -e "${GREEN}=================================================${NC}"
    echo ""
    
    # Get route URL
    ROUTE_URL=$(oc get route pdf-comparator-route -n ${DEMO_NAMESPACE} -o jsonpath='{.status.ingress[0].host}')
    
    echo -e "${YELLOW}Access Information:${NC}"
    echo -e "  Web UI: ${GREEN}https://${ROUTE_URL}${NC}"
    echo -e "  API Docs: ${GREEN}https://${ROUTE_URL}/api/docs${NC}"
    echo -e "  Health Check: ${GREEN}https://${ROUTE_URL}/health${NC}"
    echo ""
    
    echo -e "${YELLOW}Granite Model Configuration:${NC}"
    echo -e "  Endpoint: ${GREEN}${GRANITE_ENDPOINT}${NC}"
    echo -e "  Model: ${GREEN}${GRANITE_MODEL_NAME}${NC}"
    echo ""
    
    echo -e "${YELLOW}Quick Test:${NC}"
    echo -e "  ${BLUE}curl https://${ROUTE_URL}/health${NC}"
    echo ""
    
    echo -e "${YELLOW}View Logs:${NC}"
    echo -e "  ${BLUE}oc logs -f deployment/pdf-comparator -n ${DEMO_NAMESPACE}${NC}"
    echo ""
    
    echo -e "${YELLOW}Port Forward (for local testing):${NC}"
    echo -e "  ${BLUE}oc port-forward -n ${DEMO_NAMESPACE} svc/pdf-comparator-service 8000:8000${NC}"
    echo ""
    
    if [ "$USE_ARGOCD" = true ]; then
        ARGOCD_URL=$(oc get route -n openshift-gitops openshift-gitops-server -o jsonpath='{.spec.host}')
        echo -e "${YELLOW}ArgoCD Dashboard:${NC}"
        echo -e "  ${GREEN}https://${ARGOCD_URL}${NC}"
        echo ""
    fi
}

# Cleanup function
cleanup() {
    print_warning "Cleaning up demo deployment..."
    
    if [ "$USE_ARGOCD" = true ]; then
        oc delete application pdf-comparator-demo -n openshift-gitops --ignore-not-found
    fi
    
    oc delete project ${DEMO_NAMESPACE} --ignore-not-found
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    print_header
    
    # Parse arguments
    case "${1:-deploy}" in
        deploy)
            check_prerequisites
            create_namespace
            
            if [ "$USE_ARGOCD" = true ] && [ "${DEPLOY_METHOD:-argocd}" = "argocd" ]; then
                deploy_with_argocd
            else
                create_configs
                deploy_application
                create_route
            fi
            
            wait_for_deployment
            display_info
            ;;
        
        build-deploy)
            check_prerequisites
            create_namespace
            build_image
            create_configs
            deploy_application
            create_route
            wait_for_deployment
            display_info
            ;;
        
        cleanup|delete)
            cleanup
            ;;
        
        info)
            display_info
            ;;
        
        logs)
            oc logs -f deployment/pdf-comparator -n ${DEMO_NAMESPACE}
            ;;
        
        *)
            echo "Usage: $0 [deploy|build-deploy|cleanup|info|logs]"
            echo ""
            echo "Commands:"
            echo "  deploy       - Deploy using pre-built image (default)"
            echo "  build-deploy - Build image and deploy"
            echo "  cleanup      - Remove demo deployment"
            echo "  info         - Display access information"
            echo "  logs         - View application logs"
            echo ""
            echo "Environment Variables:"
            echo "  GRANITE_ENDPOINT - Granite model endpoint (default: http://granite-service.vllm.svc.cluster.local:8000)"
            echo "  GRANITE_MODEL_NAME - Model name (default: granite-3.1-8b-instruct)"
            echo "  VLLM_API_KEY - API key for vLLM (default: demo-api-key)"
            echo "  DEPLOY_METHOD - Deployment method: argocd or manual (default: argocd if available)"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"