#!/bin/bash

# Cleanup script for PDF Comparator AI

echo "WARNING: This will delete all PDF Comparator resources!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Delete ArgoCD applications
oc delete application -n openshift-gitops -l app.kubernetes.io/part-of=pdf-comparator

# Delete projects
for env in dev staging prod; do
    oc delete project pdf-comparator-$env --wait=false
    oc delete project vllm-$env --wait=false
done

echo "Cleanup initiated. Projects will be deleted in the background."