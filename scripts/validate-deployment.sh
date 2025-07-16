#!/bin/bash
set -euo pipefail

# Generic deployment validation script for validated patterns
# This script checks common pattern components and can be extended

echo "=== Validated Pattern Deployment Validation ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Counter for errors
ERRORS=0

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    log_error "Not logged into OpenShift"
    echo "Please run: oc login <cluster-url>"
    exit 1
fi

CLUSTER=$(oc whoami --show-server)
log_success "Connected to cluster: ${CLUSTER}"

# Check core operators
echo -e "\nChecking core operators..."
for op in openshift-gitops-operator-redhat advanced-cluster-management; do
    if oc get csv -A 2>/dev/null | grep -q "${op}.*Succeeded"; then
        log_success "Operator ${op} is ready"
    else
        log_warn "Operator ${op} not found or not ready"
    fi
done

# Check core namespaces
echo -e "\nChecking core namespaces..."
for ns in openshift-gitops open-cluster-management; do
    if oc get namespace "${ns}" &> /dev/null; then
        log_success "Namespace ${ns} exists"
    else
        log_error "Namespace ${ns} missing"
        ((ERRORS++))
    fi
done

# Check GitOps applications
echo -e "\nChecking ArgoCD applications..."
if oc get applications -n openshift-gitops &> /dev/null; then
    APPS=$(oc get applications -n openshift-gitops -o name | wc -l)
    if [ "${APPS}" -gt 0 ]; then
        log_success "Found ${APPS} ArgoCD applications"

        # Show application status
        echo -e "\nApplication Status:"
        oc get applications -n openshift-gitops -o custom-columns='NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status' | column -t
    else
        log_warn "No ArgoCD applications found"
    fi
else
    log_error "Cannot access ArgoCD applications"
    ((ERRORS++))
fi

# Check External Secrets if available
echo -e "\nChecking External Secrets..."
if oc get crd externalsecrets.external-secrets.io &> /dev/null; then
    log_success "External Secrets CRD found"

    # Count external secrets
    ES_COUNT=$(oc get externalsecrets -A --no-headers 2>/dev/null | wc -l)
    if [ "${ES_COUNT}" -gt 0 ]; then
        log_success "Found ${ES_COUNT} external secrets"
    else
        log_warn "No external secrets configured"
    fi
else
    log_warn "External Secrets not installed"
fi

# Check Vault if available
echo -e "\nChecking Vault..."
if oc get namespace vault &> /dev/null; then
    if oc get pods -n vault -l app.kubernetes.io/name=vault --no-headers 2>/dev/null | grep -q Running; then
        log_success "Vault is running"
    else
        log_warn "Vault namespace exists but Vault is not running"
    fi
else
    log_warn "Vault not deployed"
fi

# Check pattern-specific namespaces
echo -e "\nChecking pattern namespaces..."
# Get namespaces with ArgoCD labels
PATTERN_NS=$(oc get namespaces -l argocd.argoproj.io/managed-by=openshift-gitops -o name 2>/dev/null | wc -l)
if [ "${PATTERN_NS}" -gt 0 ]; then
    log_success "Found ${PATTERN_NS} pattern-managed namespaces"
else
    log_warn "No pattern-managed namespaces found"
fi

# Check for common issues
echo -e "\nChecking for common issues..."

# Check if any pods are in error state
ERROR_PODS=$(oc get pods -A | grep -c -E 'Error|CrashLoopBackOff|ImagePullBackOff' || true)
if [ "${ERROR_PODS}" -gt 0 ]; then
    log_error "Found ${ERROR_PODS} pods in error state"
    echo "Run 'oc get pods -A | grep -v Running' to see details"
    ((ERRORS++))
else
    log_success "No pods in error state"
fi

# Summary
echo -e "\n=== Validation Summary ==="
if [ "${ERRORS}" -eq 0 ]; then
    echo -e "${GREEN}✓ Pattern deployment validation passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check application-specific components"
    echo "2. Verify application routes and endpoints"
    echo "3. Test application functionality"
else
    echo -e "${RED}✗ Found ${ERRORS} errors during validation${NC}"
    echo ""
    echo "Please check the errors above and:"
    echo "1. Ensure all operators are installed"
    echo "2. Check ArgoCD application sync status"
    echo "3. Review pod logs for failing components"
fi

# Optional: Show useful commands
echo -e "\nUseful commands:"
echo "- View all applications: oc get applications -n openshift-gitops"
echo "- Check sync status: oc get applications -n openshift-gitops -o yaml"
echo "- View all pods: oc get pods -A | grep -v Running"
echo "- Check operators: oc get csv -A"