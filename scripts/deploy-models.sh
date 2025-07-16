#!/bin/bash
set -euo pipefail

# Generic deployment helper script for validated patterns
# Can be used to deploy additional resources after pattern installation

# Usage: ./deploy-models.sh [namespace] [resource-dir]

NAMESPACE="${1:-default}"
RESOURCE_DIR="${2:-resources}"

echo "=== Pattern Resource Deployment ==="
echo "Namespace: ${NAMESPACE}"
echo "Resource directory: ${RESOURCE_DIR}"

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    echo "ERROR: Not logged into OpenShift"
    echo "Please run: oc login <cluster-url>"
    exit 1
fi

# Create namespace if it doesn't exist
if ! oc get namespace "${NAMESPACE}" &> /dev/null; then
    echo "Creating namespace ${NAMESPACE}..."
    oc create namespace "${NAMESPACE}"
else
    echo "Using existing namespace ${NAMESPACE}"
fi

# Deploy resources if directory exists
if [ -d "${RESOURCE_DIR}" ]; then
    echo "Deploying resources from ${RESOURCE_DIR}..."

    # Count YAML files
    YAML_COUNT=$(find "${RESOURCE_DIR}" -name "*.yaml" -o -name "*.yml" | wc -l)

    if [ "${YAML_COUNT}" -gt 0 ]; then
        echo "Found ${YAML_COUNT} YAML files to deploy"

        # Deploy each YAML file
        for yaml_file in "${RESOURCE_DIR}"/*.yaml "${RESOURCE_DIR}"/*.yml; do
            if [ -f "${yaml_file}" ]; then
                echo "Deploying $(basename "${yaml_file}")..."
                oc apply -f "${yaml_file}" -n "${NAMESPACE}"
            fi
        done

        echo "✓ Resource deployment complete"
    else
        echo "No YAML files found in ${RESOURCE_DIR}"
    fi
else
    echo "Resource directory not found: ${RESOURCE_DIR}"
    echo ""
    echo "Usage: $0 [namespace] [resource-dir]"
    echo ""
    echo "This script deploys YAML resources to a specified namespace."
    echo "Place your YAML files in the resource directory before running."
    exit 1
fi

# Check deployment status
echo ""
echo "Checking deployment status..."
oc get all -n "${NAMESPACE}"

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Verify resources are running: oc get pods -n ${NAMESPACE}"
echo "2. Check logs if needed: oc logs -n ${NAMESPACE} <pod-name>"
echo "3. Expose services if required: oc expose svc/<service> -n ${NAMESPACE}"