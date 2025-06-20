# PDF Comparator AI - Project Structure

## Directory Layout

```
pdf-comparator-ai/
│
├── src/                    # Source code
│   ├── core/              # Core functionality
│   ├── chatbot/           # Chatbot logic
│   ├── interfaces/        # UI/API interfaces
│   └── utils/             # Utilities
│
├── k8s/                   # Kubernetes manifests
│   ├── base/              # Base configurations
│   ├── overlays/          # Environment-specific configs
│   └── argocd/            # ArgoCD applications
│
├── helm/                  # Helm charts
│   ├── pdf-comparator/    # Main application chart
│   └── vllm/              # vLLM service chart
│
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
│
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── development/       # Development guides
│
├── scripts/               # Utility scripts
├── configs/               # Configuration files
└── .github/               # GitHub specific files
```

## Key Files

- `main.py` - Application entry point
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Local development setup
- `deploy.sh` - OpenShift deployment script
- `setup-repo.sh` - Git repository initialization
- `Makefile` - Common development tasks

## Helm Values

- `helm/pdf-comparator/values.yaml` - Default values
- `helm/pdf-comparator/values-dev.yaml` - Development overrides
- `helm/pdf-comparator/values-staging.yaml` - Staging overrides
- `helm/pdf-comparator/values-prod.yaml` - Production overrides

## ArgoCD Configuration

- `k8s/argocd/applicationset.yaml` - Multi-environment deployment
- `k8s/argocd/parameter-catalog.yaml` - All configurable parameters
- `k8s/argocd/argocd-cli-examples.sh` - CLI usage examples
