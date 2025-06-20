# ArgoCD Parameter Configuration Guide

This guide explains how to configure PDF Comparator AI using ArgoCD parameters.

## Overview

All application settings can be modified through ArgoCD without changing code or redeploying. This provides:

- Dynamic configuration management
- Environment-specific settings
- Real-time updates
- GitOps compliance

## Accessing ArgoCD

1. Get ArgoCD URL:
```bash
oc get route -n openshift-gitops openshift-gitops-server -o jsonpath='{.spec.host}'
```

2. Login with OpenShift credentials:
```bash
argocd login <argocd-url> --sso
```

## Common Parameter Updates

### Via UI

1. Navigate to your application
2. Click "App Details" → "Parameters"
3. Modify values
4. Save and sync

### Via CLI

#### Basic Configuration
```bash
# Change replica count
argocd app set prod-pdf-comparator -p app.replicaCount=5

# Update log level
argocd app set dev-pdf-comparator -p config.logLevel=DEBUG
```

#### vLLM Configuration
```bash
# Change model endpoint
argocd app set prod-pdf-comparator \
  -p vllm.endpoint=http://vllm-custom:8000

# Update model parameters
argocd app set prod-pdf-comparator \
  -p vllm.model.temperature=0.2 \
  -p vllm.model.maxTokens=4096
```

#### Feature Flags
```bash
# Enable/disable features
argocd app set prod-pdf-comparator \
  -p config.features.enableCaching=false \
  -p config.features.enableDebugEndpoints=false
```

## Parameter Categories

### Application Parameters
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `app.replicaCount` | Number of pods | integer | 2 |
| `app.image.tag` | Container image tag | string | latest |
| `config.logLevel` | Logging level | string | INFO |

### vLLM Parameters
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `vllm.endpoint` | vLLM service URL | string | http://vllm-service:8000 |
| `vllm.model.name` | Model identifier | string | granite-3.1-8b-instruct |
| `vllm.model.temperature` | Generation temperature | float | 0.3 |
| `vllm.model.maxTokens` | Max tokens per response | integer | 2048 |

### Resource Parameters
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `app.resources.requests.memory` | Memory request | string | 512Mi |
| `app.resources.limits.memory` | Memory limit | string | 2Gi |
| `app.resources.requests.cpu` | CPU request | string | 250m |
| `app.resources.limits.cpu` | CPU limit | string | 1000m |

### Feature Flags
| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `config.features.enableCaching` | Enable Redis caching | boolean | true |
| `config.features.enableMetrics` | Enable Prometheus metrics | boolean | true |
| `config.features.enableSemanticAnalysis` | Enable semantic comparison | boolean | true |

## Environment-Specific Configurations

### Development
```bash
argocd app set dev-pdf-comparator \
  -p app.replicaCount=1 \
  -p config.logLevel=DEBUG \
  -p config.features.enableDebugEndpoints=true
```

### Staging
```bash
argocd app set staging-pdf-comparator \
  -p app.replicaCount=2 \
  -p config.logLevel=INFO \
  -p autoscaling.enabled=true
```

### Production
```bash
argocd app set prod-pdf-comparator \
  -p app.replicaCount=4 \
  -p config.logLevel=WARNING \
  -p autoscaling.enabled=true \
  -p autoscaling.maxReplicas=20
```

## Advanced Configurations

### Enable Autoscaling
```bash
argocd app set prod-pdf-comparator \
  -p autoscaling.enabled=true \
  -p autoscaling.minReplicas=4 \
  -p autoscaling.maxReplicas=20 \
  -p autoscaling.targetCPUUtilizationPercentage=70
```

### Configure Monitoring
```bash
argocd app set prod-pdf-comparator \
  -p monitoring.enabled=true \
  -p monitoring.interval=15s
```

### Update vLLM Resources
```bash
argocd app set vllm-granite \
  -p resources.requests.memory=24Gi \
  -p resources.requests.gpu=1 \
  -p deployment.gpuMemoryUtilization=0.95
```

## Best Practices

1. **Test in Dev First**: Always test parameter changes in development before applying to production
2. **Document Changes**: Keep a record of parameter modifications
3. **Use Git for Major Changes**: For significant configuration updates, commit to Git
4. **Monitor After Changes**: Watch application metrics after parameter updates
5. **Backup Current Config**: Export current parameters before major changes

## Troubleshooting

### View Current Parameters
```bash
argocd app get <app-name> --show-params
```

### Check Sync Status
```bash
argocd app get <app-name>
```

### Force Sync
```bash
argocd app sync <app-name> --force
```

### Rollback Changes
```bash
argocd app rollback <app-name> <revision>
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/pkstaz/pdf-comparator-ai/issues
- Email: cestay@redhat.com
```

## docker-compose.yml (for local development)
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - VLLM_ENDPOINT=http://vllm:8000
      - REDIS_HOST=redis
      - MINIO_ENDPOINT=minio:9000
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src
    depends_on:
      - redis
      - minio

  vllm:
    image: vllm/vllm-openai:latest
    command: >
      --model ibm-granite/granite-3.1-8b-instruct
      --dtype auto
      --api-key token-abc123
    ports:
      - "8001:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    command: server /data --console-address ":9001"

volumes:
  minio_data:
```