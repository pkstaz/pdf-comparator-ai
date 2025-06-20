#!/bin/bash

# Log viewing script

ENV=${1:-dev}
COMPONENT=${2:-app}

case $COMPONENT in
    app)
        oc logs -f -n pdf-comparator-$ENV -l app=pdf-comparator --tail=100
        ;;
    vllm)
        oc logs -f -n vllm-$ENV -l app=vllm --tail=100
        ;;
    all)
        oc logs -f -n pdf-comparator-$ENV --all-containers=true --tail=100
        ;;
    *)
        echo "Usage: $0 [env] [app|vllm|all]"
        exit 1
        ;;
esac