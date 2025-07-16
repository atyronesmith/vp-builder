#!/bin/bash
# convert-to-validated-pattern.sh
#
# A tool to convert any OpenShift/Kubernetes project into a Red Hat Validated Pattern
# This script creates the complete validated pattern structure following Red Hat's
# validated patterns framework (https://validatedpatterns.io)
#
# Usage: ./convert-to-validated-pattern.sh <pattern-name> <source-repo-path> [github-org]
# Example: ./convert-to-validated-pattern.sh my-app ./my-app-repo myorg

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <pattern-name> <source-repo-path> [github-org]"
    echo "Example: $0 my-pattern ./source-repo myorg"
    exit 1
fi

PATTERN_NAME="$1"
SOURCE_REPO="$2"
GITHUB_ORG="${3:-your-org}"
PATTERN_DIR="${PATTERN_NAME}-validated-pattern"

log_info "Starting conversion of ${SOURCE_REPO} to validated pattern: ${PATTERN_NAME}"

# Step 1: Create directory structure
log_info "Creating directory structure..."
mkdir -p "${PATTERN_DIR}"/{ansible,charts/{hub,region},common,migrated-charts,overrides,scripts,tests/interop}

cd "${PATTERN_DIR}"

# Step 2: Create base configuration files
log_info "Creating configuration files..."

# .gitignore
cat > .gitignore << 'EOF'
common
values-secret.yaml
*.swp
*.bak
*~
.DS_Store
EOF

# ansible.cfg
cat > ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
interpreter_python = auto_silent
EOF

# ansible/site.yaml
cat > ansible/site.yaml << 'EOF'
---
- hosts: localhost
  connection: local
  gather_facts: no
  vars:
    ansible_python_interpreter: "{{ ansible_playbook_python }}"

  tasks:
    - name: Check for rhvp.cluster_utils
      debug:
        msg: |
          This playbook requires rhvp.cluster_utils collection.
          Install with: ansible-galaxy collection install rhvp.cluster_utils
EOF

# Makefile
cat > Makefile << 'EOF'
.PHONY: default
default: help

%:
	@if [ -f common/Makefile ]; then \
		make -f common/Makefile $@; \
	else \
		echo "ERROR: common/Makefile not found. Clone from:"; \
		echo "https://github.com/validatedpatterns-docs/common.git"; \
		exit 1; \
	fi
EOF

# pattern-metadata.yaml
cat > pattern-metadata.yaml << EOF
name: ${PATTERN_NAME}
displayName: "${PATTERN_NAME} Pattern"
description: |
  TODO: Add description
gitOpsRepo: "https://github.com/${GITHUB_ORG}/${PATTERN_DIR}"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/${PATTERN_NAME}/"
architectureReadmeUrl: "https://github.com/${GITHUB_ORG}/${PATTERN_DIR}/blob/main/README.md"
organizations:
  - ${GITHUB_ORG}
  - validatedpatterns
EOF

# values-global.yaml
cat > values-global.yaml << EOF
global:
  pattern: ${PATTERN_NAME}
  namespace: pattern-namespace
  targetRevision: main
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: 0.9.0

  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic

  git:
    provider: github
    account: ${GITHUB_ORG}
    email: devops@${GITHUB_ORG}.com
    dev_revision: main

main:
  clusterGroupName: hub
  multiSourceConfig:
    enabled: true

clusterGroup:
  name: hub
  isHubCluster: true

  namespaces:
    - open-cluster-management
    - openshift-gitops
    - external-secrets
    - vault
    # TODO: Add application namespaces

  subscriptions:
    gitops:
      namespace: openshift-gitops
      channel: latest
      source: redhat-operators

    acm:
      namespace: open-cluster-management
      channel: release-2.10
      source: redhat-operators

  applications:
    acm:
      name: acm
      namespace: open-cluster-management
      chart: acm
      repoURL: https://charts.validatedpatterns.io
      targetRevision: 0.1.0
      valuesFile: values-hub.yaml
      enabled: true

    vault:
      name: vault
      namespace: vault
      chart: vault
      repoURL: https://charts.validatedpatterns.io
      targetRevision: 0.1.0
      valuesFile: values-hub-vault.yaml
      enabled: true
EOF

# values-hub.yaml
cat > values-hub.yaml << EOF
clusterGroup:
  name: hub
  isHubCluster: true

  managedClusterGroups:
    - name: region
      helmOverrides:
        - name: clusterGroup.insecureEdgeTerminationPolicy
          value: Redirect

  imperative:
    jobs:
      - name: deploy-models
        playbook: ansible/playbooks/deploy-models.yaml
        timeout: 3600
EOF

# values-region.yaml
cat > values-region.yaml << 'EOF'
clusterGroup:
  name: region
  isHubCluster: false
  targetCluster: in-cluster

  applications: {}
EOF

# values-secret.yaml.template
cat > values-secret.yaml.template << 'EOF'
global:
  git:
    token: REPLACE_WITH_YOUR_GITHUB_TOKEN

secrets:
  - name: git-secret
    vaultPrefixes:
      - global
    fields:
      - name: token
        value: REPLACE_WITH_YOUR_GITHUB_TOKEN

  - name: container-registry
    vaultPrefixes:
      - global
    fields:
      - name: username
        value: REPLACE_WITH_USERNAME
      - name: password
        value: REPLACE_WITH_PASSWORD

# Application-specific secrets
# - name: app-secret
#   vaultPrefixes:
#     - hub
#   fields:
#     - name: api-key
#       value: REPLACE_WITH_API_KEY
EOF

# README.md
cat > README.md << EOF
# ${PATTERN_NAME} Validated Pattern

## Overview
TODO: Add pattern description

## Prerequisites
- OpenShift Container Platform 4.12+
- Helm 3.x
- Git
- Make

## Installation

### Quick Start
\`\`\`bash
# Clone the pattern
git clone https://github.com/${GITHUB_ORG}/${PATTERN_DIR}.git
cd ${PATTERN_DIR}

# Clone the common framework
git clone https://github.com/validatedpatterns-docs/common.git

# Create pattern symlink
ln -s ./common/scripts/pattern-util.sh pattern.sh
chmod +x pattern.sh

# Copy and edit secrets
cp values-secret.yaml.template values-secret.yaml
vi values-secret.yaml

# Deploy the pattern
make install
\`\`\`

## Components
TODO: List pattern components

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
Apache License 2.0
EOF

log_info "Base files created successfully"

# Step 3: Analyze and migrate source repository
if [ -d "${SOURCE_REPO}" ]; then
    log_info "Analyzing source repository..."

    # Find and copy Helm charts
    CHARTS_FOUND=0
    while IFS= read -r -d '' chart_dir; do
        CHART_NAME=$(basename "$(dirname "${chart_dir}")")
        log_info "Found chart: ${CHART_NAME}"

        # Copy to migrated-charts
        cp -r "$(dirname "${chart_dir}")" "migrated-charts/"

        # Create wrapper chart
        mkdir -p "charts/hub/${CHART_NAME}/templates"

        # Create wrapper Chart.yaml
        cat > "charts/hub/${CHART_NAME}/Chart.yaml" << EOF
apiVersion: v2
name: ${CHART_NAME}
description: Wrapper chart for ${CHART_NAME}
version: 0.1.0
appVersion: "1.0"
EOF

        # Create wrapper values.yaml
        cat > "charts/hub/${CHART_NAME}/values.yaml" << EOF
clusterGroup:
  applications:
    ${CHART_NAME}:
      enabled: true
      chart: ${CHART_NAME}
      repoURL: https://charts.example.com  # TODO: Update
      targetRevision: 1.0.0  # TODO: Update
      valuesFile: values-hub-${CHART_NAME}.yaml

global:
  targetRepo: ""
  targetRevision: ""
  namespace: ${CHART_NAME}
EOF

        # Create application template
        cat > "charts/hub/${CHART_NAME}/templates/application.yaml" << 'EOF'
{{- if .Values.clusterGroup.applications.CHARTNAME.enabled }}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ .Values.clusterGroup.applications.CHARTNAME.name }}
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "300"
spec:
  project: default
  sources:
    - repoURL: {{ .Values.global.targetRepo }}
      targetRevision: {{ .Values.global.targetRevision }}
      ref: patternref
    - chart: {{ .Values.clusterGroup.applications.CHARTNAME.chart }}
      repoURL: {{ .Values.clusterGroup.applications.CHARTNAME.repoURL }}
      targetRevision: {{ .Values.clusterGroup.applications.CHARTNAME.targetRevision }}
      helm:
        ignoreMissingValueFiles: true
        valueFiles:
          - ${patternref}/{{ .Values.clusterGroup.applications.CHARTNAME.valuesFile }}
  destination:
    server: https://kubernetes.default.svc
    namespace: {{ .Values.global.namespace }}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
{{- end }}
EOF
        # Replace CHARTNAME placeholder
        sed -i "s/CHARTNAME/${CHART_NAME}/g" "charts/hub/${CHART_NAME}/templates/application.yaml"

        ((CHARTS_FOUND++))
    done < <(find "${SOURCE_REPO}" -name "Chart.yaml" -type f -print0 2>/dev/null)

    log_info "Migrated ${CHARTS_FOUND} charts"

    # Copy scripts if any
    if [ -d "${SOURCE_REPO}/scripts" ]; then
        log_info "Copying scripts..."
        cp -r "${SOURCE_REPO}/scripts/"* scripts/ 2>/dev/null || true
    fi
else
    log_warn "Source repository not found: ${SOURCE_REPO}"
fi

# Step 4: Create validation script
log_info "Creating validation script..."
cat > scripts/validate-deployment.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "Validating pattern deployment..."

# Check namespaces
for ns in openshift-gitops open-cluster-management external-secrets vault; do
    if oc get namespace "${ns}" &> /dev/null; then
        echo "✓ Namespace ${ns} exists"
    else
        echo "✗ Namespace ${ns} missing"
    fi
done

# Check operators
if oc get csv -n openshift-operators 2>/dev/null | grep -q "openshift-gitops.*Succeeded"; then
    echo "✓ GitOps operator ready"
else
    echo "✗ GitOps operator not ready"
fi

# Check ArgoCD apps
for app in hub-applications hub-operators; do
    if oc get application "${app}" -n openshift-gitops &> /dev/null; then
        echo "✓ ArgoCD app ${app} exists"
    else
        echo "✗ ArgoCD app ${app} missing"
    fi
done

echo "Validation complete!"
EOF
chmod +x scripts/validate-deployment.sh

# Step 5: Create placeholders
touch overrides/.gitkeep tests/interop/.gitkeep

# Step 5.1: Validate shell scripts with ShellCheck
log_info "Running ShellCheck validation..."
if command -v shellcheck >/dev/null 2>&1; then
    # Find and validate all shell scripts
    script_count=0
    error_count=0

    while IFS= read -r -d '' script; do
        ((script_count++))
        if shellcheck "${script}"; then
            log_info "✓ ${script} passed ShellCheck"
        else
            log_warn "✗ ${script} has ShellCheck warnings/errors"
            ((error_count++))
        fi
    done < <(find . -type f -name "*.sh" -print0)

    if [[ ${error_count} -eq 0 ]]; then
        log_info "All ${script_count} shell scripts passed ShellCheck validation"
    else
        log_warn "${error_count} of ${script_count} scripts have issues - please fix them"
    fi
else
    log_warn "ShellCheck not installed - skipping shell script validation"
    log_warn "Install with: brew install shellcheck (macOS) or apt-get install shellcheck (Linux)"
fi

# Step 6: Create pattern conversion report
cat > CONVERSION-REPORT.md << EOF
# Pattern Conversion Report

## Summary
- Pattern Name: ${PATTERN_NAME}
- Source Repository: ${SOURCE_REPO}
- Conversion Date: $(date)

## Structure Created
- ✓ Directory structure
- ✓ Configuration files
- ✓ Values files
- ✓ Wrapper charts: ${CHARTS_FOUND}

## Next Steps

1. **Clone Common Framework**:
   \`\`\`bash
   git clone https://github.com/validatedpatterns-docs/common.git common
   ln -s ./common/scripts/pattern-util.sh pattern.sh
   chmod +x pattern.sh
   \`\`\`

2. **Update Configuration**:
   - Edit values-global.yaml with your specifics
   - Update chart repositories in wrapper charts
   - Add application namespaces
   - Configure platform overrides

3. **Configure Secrets**:
   \`\`\`bash
   cp values-secret.yaml.template values-secret.yaml
   # Edit with actual credentials
   \`\`\`

4. **Test Deployment**:
   \`\`\`bash
   make install
   ./scripts/validate-deployment.sh
   \`\`\`

## Manual Tasks Required
- Update pattern-metadata.yaml description
- Add architecture diagram
- Update README.md
- Configure managed clusters (if needed)
- Add platform-specific overrides
- Test on OpenShift cluster
EOF

log_info "Conversion complete!"
log_info "Pattern created in: ${PATTERN_DIR}"
log_info "See CONVERSION-REPORT.md for next steps"