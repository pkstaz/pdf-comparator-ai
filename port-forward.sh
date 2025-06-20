#!/bin/bash

# Port forwarding script for local development

ENV=${1:-dev}
SERVICE=${2:-api}

case $SERVICE in
    api)
        oc port-forward -n pdf-comparator-$ENV svc/pdf-comparator-service 8000:8000
        ;;
    vllm)
        oc port-forward -n vllm-$ENV svc/vllm-service 8001:8000
        ;;
    redis)
        oc port-forward -n pdf-comparator-$ENV svc/redis-service 6379:6379
        ;;
    *)
        echo "Usage: $0 [env] [api|vllm|redis]"
        exit 1
        ;;
esac