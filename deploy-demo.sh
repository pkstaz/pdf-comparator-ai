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
    
    # Check if we should build the image first
    if [ "${BUILD_IMAGE:-false}" = "true" ] || [ ! -z "${USE_LOCAL_BUILD}" ]; then
        print_info "Using locally built image..."
        IMAGE="${REGISTRY}/${DEMO_NAMESPACE}/pdf-comparator:latest"
    else
        # For demo, we'll create a simple deployment
        IMAGE="python:3.10-slim"
        print_warning "Using base Python image. Will create demo app inline."
    fi
    
    # First, create a ConfigMap with the demo application code
    print_info "Creating demo application code..."
    cat <<EOF | oc apply -f - -n ${DEMO_NAMESPACE}
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdf-comparator-app
  labels:
    app: pdf-comparator
data:
  main.py: |
    from fastapi import FastAPI, File, UploadFile, Form
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    import httpx
    import os
    import json
    
    app = FastAPI(title="PDF Comparator AI Demo")
    
    # Get configuration from environment
    GRANITE_ENDPOINT = os.getenv("VLLM_ENDPOINT", "http://granite-service:8000")
    GRANITE_MODEL = os.getenv("VLLM_MODEL_NAME", "granite-3.1-8b-instruct")
    API_KEY = os.getenv("VLLM_API_KEY", "demo-api-key")
    
    # HTML template for the web interface
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Comparator AI - Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1E3A8A;
                text-align: center;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }
            .upload-section {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }
            .upload-box {
                flex: 1;
                padding: 20px;
                border: 2px dashed #ddd;
                border-radius: 5px;
                text-align: center;
            }
            .btn {
                background-color: #1E3A8A;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                background-color: #2c5aa0;
            }
            .btn:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .info-box {
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .success-box {
                background-color: #c8e6c9;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .error-box {
                background-color: #ffcdd2;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .endpoint-info {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 3px;
                font-family: monospace;
                margin: 5px 0;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .status-connected {
                background-color: #4caf50;
            }
            .status-disconnected {
                background-color: #f44336;
            }
            #loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1E3A8A;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 PDF Comparator AI - Demo</h1>
            <p class="subtitle">Intelligent PDF comparison using Granite 3.1 model</p>
            
            <div class="info-box">
                <h3>ℹ️ Demo Information</h3>
                <p>This demo showcases PDF comparison capabilities using:</p>
                <ul>
                    <li>IBM Granite 3.1 model via vLLM</li>
                    <li>LangChain for AI orchestration</li>
                    <li>Multiple analysis types (Basic, Semantic, AI-powered)</li>
                </ul>
                <p><strong>Granite Endpoint:</strong> <span class="endpoint-info">""" + GRANITE_ENDPOINT + """</span></p>
                <p><strong>Model:</strong> <span class="endpoint-info">""" + GRANITE_MODEL + """</span></p>
                <p><strong>Status:</strong> <span id="connection-status"><span class="status-indicator status-disconnected"></span>Checking...</span></p>
            </div>
            
            <div class="upload-section">
                <div class="upload-box">
                    <h3>📄 Document 1</h3>
                    <input type="file" id="pdf1" accept=".pdf" onchange="handleFileSelect(1)">
                    <p id="file1-name">Select first PDF</p>
                </div>
                <div class="upload-box">
                    <h3>📄 Document 2</h3>
                    <input type="file" id="pdf2" accept=".pdf" onchange="handleFileSelect(2)">
                    <p id="file2-name">Select second PDF</p>
                </div>
            </div>
            
            <div style="text-align: center;">
                <button id="compareBtn" class="btn" onclick="comparePDFs()" disabled>🔍 Compare PDFs</button>
            </div>
            
            <div id="loading">
                <div class="spinner"></div>
                <p>Analyzing documents with Granite model...</p>
            </div>
            
            <div id="results" style="margin-top: 30px;"></div>
            
            <div class="info-box" style="margin-top: 30px;">
                <h3>🔗 API Endpoints</h3>
                <p>You can also use the REST API directly:</p>
                <div class="endpoint-info">GET /health - Health check</div>
                <div class="endpoint-info">GET /api/docs - Interactive API documentation</div>
                <div class="endpoint-info">POST /api/v1/compare - Compare two PDFs</div>
                <div class="endpoint-info">GET /test-granite - Test Granite connection</div>
            </div>
        </div>
        
        <script>
            let file1Selected = false;
            let file2Selected = false;
            
            // Check Granite connection on page load
            window.onload = function() {
                checkGraniteConnection();
            };
            
            function checkGraniteConnection() {
                fetch('/test-granite')
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('connection-status');
                        if (data.connected) {
                            statusEl.innerHTML = '<span class="status-indicator status-connected"></span>Connected';
                        } else {
                            statusEl.innerHTML = '<span class="status-indicator status-disconnected"></span>Not connected: ' + data.error;
                        }
                    })
                    .catch(error => {
                        document.getElementById('connection-status').innerHTML = 
                            '<span class="status-indicator status-disconnected"></span>Error checking connection';
                    });
            }
            
            function handleFileSelect(fileNum) {
                if (fileNum === 1) {
                    file1Selected = document.getElementById('pdf1').files.length > 0;
                    document.getElementById('file1-name').textContent = 
                        file1Selected ? document.getElementById('pdf1').files[0].name : 'Select first PDF';
                } else {
                    file2Selected = document.getElementById('pdf2').files.length > 0;
                    document.getElementById('file2-name').textContent = 
                        file2Selected ? document.getElementById('pdf2').files[0].name : 'Select second PDF';
                }
                
                // Enable button only if both files are selected
                document.getElementById('compareBtn').disabled = !(file1Selected && file2Selected);
            }
            
            async function comparePDFs() {
                const file1 = document.getElementById('pdf1').files[0];
                const file2 = document.getElementById('pdf2').files[0];
                
                if (!file1 || !file2) {
                    alert('Please select both PDF files');
                    return;
                }
                
                const formData = new FormData();
                formData.append('pdf1', file1);
                formData.append('pdf2', file2);
                
                const resultsDiv = document.getElementById('results');
                const loadingDiv = document.getElementById('loading');
                const compareBtn = document.getElementById('compareBtn');
                
                // Show loading, hide results
                loadingDiv.style.display = 'block';
                resultsDiv.innerHTML = '';
                compareBtn.disabled = true;
                
                try {
                    const response = await fetch('/api/v1/compare', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        resultsDiv.innerHTML = `
                            <h3>📊 Comparison Results</h3>
                            <div class="success-box">
                                <h4>Analysis Complete</h4>
                                <p><strong>Files compared:</strong> ${file1.name} vs ${file2.name}</p>
                                <p><strong>Processing time:</strong> ${data.processing_time || 'N/A'} seconds</p>
                            </div>
                            <div class="info-box">
                                <h4>Granite Model Response</h4>
                                <pre>${JSON.stringify(data.results, null, 2)}</pre>
                            </div>
                        `;
                    } else {
                        resultsDiv.innerHTML = `
                            <div class="error-box">
                                <h4>Error</h4>
                                <p>${data.message || 'An error occurred during comparison'}</p>
                                ${data.details ? '<p>Details: ' + data.details + '</p>' : ''}
                            </div>
                        `;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `
                        <div class="error-box">
                            <h4>Connection Error</h4>
                            <p>Failed to connect to the API: ${error.message}</p>
                        </div>
                    `;
                } finally {
                    loadingDiv.style.display = 'none';
                    compareBtn.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return html_template
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "pdf-comparator-demo"}
    
    @app.get("/ready")
    async def ready():
        return {"status": "ready"}
    
    @app.get("/test-granite")
    async def test_granite():
        """Test connection to Granite model"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
                response = await client.get(f"{GRANITE_ENDPOINT}/health", headers=headers)
                return {
                    "connected": response.status_code == 200,
                    "endpoint": GRANITE_ENDPOINT,
                    "model": GRANITE_MODEL,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "connected": False,
                "endpoint": GRANITE_ENDPOINT,
                "model": GRANITE_MODEL,
                "error": str(e)
            }
    
    @app.get("/api/docs")
    async def api_docs():
        return {
            "message": "API documentation",
            "endpoints": {
                "/health": "Health check",
                "/ready": "Readiness check",
                "/test-granite": "Test Granite connection",
                "/api/v1/compare": "Compare two PDFs"
            }
        }
    
    @app.post("/api/v1/compare")
    async def compare_pdfs(pdf1: UploadFile = File(...), pdf2: UploadFile = File(...)):
        """Compare two PDFs using Granite model"""
        try:
            # Read PDF content (simplified for demo)
            pdf1_content = await pdf1.read()
            pdf2_content = await pdf2.read()
            
            # Prepare request to Granite model
            prompt = f"""Compare these two documents and provide a detailed analysis:
            
            Document 1: {pdf1.filename} (Size: {len(pdf1_content)} bytes)
            Document 2: {pdf2.filename} (Size: {len(pdf2_content)} bytes)
            
            Please analyze:
            1. Main differences
            2. Similarities
            3. Key changes
            4. Recommendations
            """
            
            # Call Granite model
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
                
                payload = {
                    "model": GRANITE_MODEL,
                    "prompt": prompt,
                    "max_tokens": 500,
                    "temperature": 0.3
                }
                
                response = await client.post(
                    f"{GRANITE_ENDPOINT}/v1/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "message": "PDFs compared successfully",
                        "pdf1": pdf1.filename,
                        "pdf2": pdf2.filename,
                        "results": {
                            "granite_response": result.get("choices", [{}])[0].get("text", "No response"),
                            "model_used": GRANITE_MODEL,
                            "endpoint": GRANITE_ENDPOINT
                        },
                        "processing_time": result.get("processing_time", "N/A")
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Granite API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "Timeout connecting to Granite model",
                "details": f"Could not reach {GRANITE_ENDPOINT} within 30 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Error processing PDFs",
                "details": str(e),
                "endpoint": GRANITE_ENDPOINT,
                "model": GRANITE_MODEL
            }
    
    if __name__ == "__main__":
        print(f"Starting PDF Comparator Demo")
        print(f"Granite Endpoint: {GRANITE_ENDPOINT}")
        print(f"Model: {GRANITE_MODEL}")
        uvicorn.run(app, host="0.0.0.0", port=8000)
  
  requirements.txt: |
    fastapi==0.104.1
    uvicorn==0.24.0
    python-multipart==0.0.6
    httpx==0.25.2
EOF
    
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
      initContainers:
      - name: install-deps
        image: ${IMAGE}
        command: ['sh', '-c']
        args:
          - |
            pip install --no-cache-dir -r /app/requirements.txt
            cp -r /usr/local/lib/python3.10/site-packages/* /app-packages/
        volumeMounts:
        - name: app-code
          mountPath: /app
        - name: app-packages
          mountPath: /app-packages
      containers:
      - name: pdf-comparator
        image: ${IMAGE}
        imagePullPolicy: Always
        command: ["python", "/app/main.py"]
        env:
        - name: PYTHONPATH
          value: "/app-packages"
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        envFrom:
        - configMapRef:
            name: pdf-comparator-config
        - secretRef:
            name: pdf-comparator-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
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
          initialDelaySeconds: 20
          periodSeconds: 5
        volumeMounts:
        - name: app-code
          mountPath: /app
        - name: app-packages
          mountPath: /app-packages
        - name: temp
          mountPath: /tmp
      volumes:
      - name: app-code
        configMap:
          name: pdf-comparator-app
      - name: app-packages
        emptyDir: {}
      - name: temp
        emptyDir: {}
EOF
    
    # Wait for deployment to be created
    sleep 5
    
    # Check if deployment was created
    if oc get deployment pdf-comparator -n ${DEMO_NAMESPACE} &> /dev/null; then
        print_success "Deployment created successfully"
    else
        print_error "Failed to create deployment"
        print_info "Checking events for errors..."
        oc get events -n ${DEMO_NAMESPACE} --field-selector type=Warning
        exit 1
    fi
    
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
        print_warning "Dockerfile not found. Creating a simple one for demo..."
        
        # Create a simple Dockerfile for demo
        cat > Dockerfile.demo <<EOF
FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY . .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
        
        # Create a simple main.py for demo
        cat > main.py <<EOF
from fastapi import FastAPI

app = FastAPI(title="PDF Comparator Demo")

@app.get("/")
def read_root():
    return {"message": "PDF Comparator AI Demo", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    return {"status": "ready"}
EOF
    fi
    
    # Get internal registry
    INTERNAL_REGISTRY="image-registry.openshift-image-registry.svc:5000"
    
    # Create BuildConfig
    print_info "Creating BuildConfig..."
    oc new-build --binary --strategy=docker \
        --name=pdf-comparator \
        --docker-image=python:3.10-slim \
        -n ${DEMO_NAMESPACE} 2>/dev/null || true
    
    # Wait for builder service account
    sleep 5
    
    # Start build
    print_info "Starting build..."
    if [ -f "Dockerfile.demo" ]; then
        oc start-build pdf-comparator --from-dir=. --dockerfile=Dockerfile.demo --follow -n ${DEMO_NAMESPACE}
    else
        oc start-build pdf-comparator --from-dir=. --follow -n ${DEMO_NAMESPACE}
    fi
    
    # Update the deployment to use the built image
    oc set image deployment/pdf-comparator \
        pdf-comparator=${INTERNAL_REGISTRY}/${DEMO_NAMESPACE}/pdf-comparator:latest \
        -n ${DEMO_NAMESPACE}
    
    print_success "Image built and deployed successfully"
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
                # Don't create manual deployment when using ArgoCD
                print_info "Waiting for ArgoCD to create resources..."
                sleep 30
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
            create_configs
            deploy_application
            create_route
            build_image
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