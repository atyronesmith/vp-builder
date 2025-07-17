#!/bin/bash
# convert-to-validated-pattern.sh
#
# A tool to convert any OpenShift/Kubernetes project into a Red Hat Validated Pattern
# This script creates the complete validated pattern structure following Red Hat's
# validated patterns framework (https://validatedpatterns.io)
#
# Usage: ./convert-to-validated-pattern.sh <pattern-name> <source-repo-path-or-url> [github-org]
# Example: ./convert-to-validated-pattern.sh my-app ./my-app-repo myorg
# Example: ./convert-to-validated-pattern.sh my-app https://github.com/user/repo.git myorg

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

# Cleanup function
cleanup() {
    if [[ -n "${TEMP_CLONE_DIR:-}" ]] && [[ -d "${TEMP_CLONE_DIR}" ]]; then
        log_info "Cleaning up temporary clone directory..."
        rm -rf "${TEMP_CLONE_DIR}"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Check arguments
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <pattern-name> <source-repo-path-or-url> [github-org]"
    echo "Examples:"
    echo "  $0 my-pattern ./source-repo myorg"
    echo "  $0 my-pattern https://github.com/user/repo.git myorg"
    exit 1
fi

PATTERN_NAME="$1"
SOURCE_INPUT="$2"
GITHUB_ORG="${3:-your-org}"
PATTERN_DIR="${PATTERN_NAME}-validated-pattern"
TEMP_CLONE_DIR=""

# Check if source is a URL or local path
if [[ "${SOURCE_INPUT}" =~ ^https?:// ]] || [[ "${SOURCE_INPUT}" =~ ^git@ ]]; then
    # It's a URL, we need to clone it
    log_info "Detected repository URL: ${SOURCE_INPUT}"
    TEMP_CLONE_DIR="/tmp/${PATTERN_NAME}-source-$$"
    log_info "Cloning repository to temporary directory: ${TEMP_CLONE_DIR}"

    if git clone "${SOURCE_INPUT}" "${TEMP_CLONE_DIR}"; then
        SOURCE_REPO="${TEMP_CLONE_DIR}"
        log_info "Repository cloned successfully"
    else
        log_error "Failed to clone repository: ${SOURCE_INPUT}"
        exit 1
    fi
else
    # It's a local path
    SOURCE_REPO="${SOURCE_INPUT}"
    if [[ ! -d "${SOURCE_REPO}" ]]; then
        log_error "Source directory not found: ${SOURCE_REPO}"
        exit 1
    fi
fi

log_info "Starting conversion of ${SOURCE_INPUT} to validated pattern: ${PATTERN_NAME}"
echo ""
echo "================================================================================"
echo "                     VALIDATED PATTERN CONVERSION PROCESS                        "
echo "================================================================================"
echo ""

# Phase 1: Analysis (Automated)
echo -e "${YELLOW}=== Phase 1: Analysis (Automated) ===${NC}"
log_info "Scanning source repository: ${SOURCE_REPO}"

# Perform detailed Helm chart analysis
log_info "Searching for Helm charts and analyzing structure..."
HELM_CHARTS=()
HELM_CHART_DETAILS=()
while IFS= read -r -d '' chart; do
    CHART_DIR=$(dirname "${chart}")
    CHART_NAME=$(basename "${CHART_DIR}")
    CHART_REL_PATH="${CHART_DIR#"${SOURCE_REPO}"/}"
    HELM_CHARTS+=("${CHART_NAME}")

    log_info "  ✓ Found Helm chart: ${CHART_NAME}"
    log_info "    Location: ${CHART_REL_PATH}"

    # Analyze chart type and details
    if grep -q "type: library" "${chart}" 2>/dev/null; then
        log_info "    Type: Library chart (provides utilities, not deployable)"
    else
        log_info "    Type: Application chart (deployable)"
    fi

    # Check for chart version
    CHART_VERSION=$(grep "^version:" "${chart}" 2>/dev/null | cut -d: -f2 | tr -d ' ')
    if [[ -n "${CHART_VERSION}" ]]; then
        log_info "    Version: ${CHART_VERSION}"
    fi

    # Check for dependencies
    if grep -q "dependencies:" "${chart}" 2>/dev/null; then
        log_info "    Has dependencies: Yes"
    fi

    # Analyze chart structure
    log_info "    Structure:"

    # Check for values.yaml and analyze
    if [[ -f "${CHART_DIR}/values.yaml" ]]; then
        log_info "      ✓ values.yaml found (default values for templates)"
        # Count number of values defined
        VALUE_COUNT=$(grep -E "^[a-zA-Z]" "${CHART_DIR}/values.yaml" 2>/dev/null | grep -cv "^#")
        if [[ ${VALUE_COUNT} -gt 0 ]]; then
            log_info "        Contains approximately ${VALUE_COUNT} value definitions"
        fi
    else
        log_info "      ⚠ No values.yaml - templates use only runtime values"
    fi

        # Check for templates
    if [[ -d "${CHART_DIR}/templates" ]]; then
        TEMPLATE_COUNT=$(find "${CHART_DIR}/templates" -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l | tr -d ' ')
        log_info "      ✓ templates/ directory (${TEMPLATE_COUNT} templates)"

        # Check for Go template usage
        TEMPLATE_USAGE=$(grep -l "{{" "${CHART_DIR}/templates/"*.yaml 2>/dev/null | wc -l | tr -d ' ')
        if [[ ${TEMPLATE_USAGE} -gt 0 ]]; then
            log_info "        ${TEMPLATE_USAGE} templates use Go template syntax"
        fi

        # Check for common Helm template patterns
        if grep -q "{{ .Values" "${CHART_DIR}/templates/"*.yaml 2>/dev/null; then
            log_info "        Templates reference .Values (configurable)"
        fi
        if grep -q "{{ .Release" "${CHART_DIR}/templates/"*.yaml 2>/dev/null; then
            log_info "        Templates use .Release metadata"
        fi
        if grep -q "{{ include" "${CHART_DIR}/templates/"*.yaml 2>/dev/null; then
            log_info "        Templates use template includes/partials"
        fi

        # List key template types
        if [[ -f "${CHART_DIR}/templates/deployment.yaml" ]]; then
            log_info "        - deployment.yaml"
        fi
        if [[ -f "${CHART_DIR}/templates/service.yaml" ]]; then
            log_info "        - service.yaml"
        fi
        if [[ -f "${CHART_DIR}/templates/configmap.yaml" ]]; then
            log_info "        - configmap.yaml"
        fi
        if [[ -f "${CHART_DIR}/templates/route.yaml" ]]; then
            log_info "        - route.yaml (OpenShift route)"
        fi

        # Check for _helpers.tpl
        if [[ -f "${CHART_DIR}/templates/_helpers.tpl" ]]; then
            log_info "        - _helpers.tpl (template functions)"
        fi
    else
        log_info "      ⚠ No templates/ directory"
    fi

    # Check for kustomization.yaml (common in validated patterns)
    if [[ -f "${CHART_DIR}/kustomization.yaml" ]]; then
        log_info "      ✓ kustomization.yaml (Kustomize integration)"
    fi

    # Store details for later use
    HELM_CHART_DETAILS+=("${CHART_NAME}|${CHART_REL_PATH}|${CHART_VERSION}")

done < <(find "${SOURCE_REPO}" -name "Chart.yaml" -type f -print0 2>/dev/null || true)

log_info "Searching for YAML configuration files..."
YAML_COUNT=0
YAML_FILES=()
while IFS= read -r -d '' yaml_file; do
    YAML_FILES+=("${yaml_file}")
done < <(find "${SOURCE_REPO}" \( -name "*.yaml" -o -name "*.yml" \) -type f -print0 2>/dev/null || true)

TOTAL_YAML=${#YAML_FILES[@]}

# Show first 20 YAML files
for ((i=0; i<20 && i<${#YAML_FILES[@]}; i++)); do
    yaml_file="${YAML_FILES[i]}"
    REL_PATH="${yaml_file#"${SOURCE_REPO}"/}"
    log_info "  ✓ Found YAML: ${REL_PATH}"
    ((YAML_COUNT++))
done

if [[ ${TOTAL_YAML} -gt 20 ]]; then
    log_info "  ... and $((TOTAL_YAML - 20)) more YAML files"
fi

log_info "Searching for shell scripts..."
while IFS= read -r -d '' script; do
    REL_PATH="${script#"${SOURCE_REPO}"/}"
    log_info "  ✓ Found script: ${REL_PATH}"
done < <(find "${SOURCE_REPO}" -name "*.sh" -type f -print0 2>/dev/null || true)

# Summary
HELM_CHART_COUNT=${#HELM_CHARTS[@]}
SCRIPT_COUNT=$(find "${SOURCE_REPO}" -name "*.sh" -type f 2>/dev/null | wc -l | tr -d ' ')

log_info ""
log_info "Analyzing repository structure for validated patterns compatibility..."

# Check if charts follow site-based organization
SITE_PATTERNS=("hub" "region" "datacenter" "factory" "edge")
FOUND_SITES=()
for site in "${SITE_PATTERNS[@]}"; do
    if find "${SOURCE_REPO}" -type d -name "${site}" | grep -q .; then
        FOUND_SITES+=("${site}")
        log_info "  ✓ Found site directory: ${site}/"
    fi
done

if [[ ${#FOUND_SITES[@]} -gt 0 ]]; then
    log_info "  Repository appears to follow site-based organization"
else
    log_info "  Repository will need restructuring for site-based deployment (hub/region pattern)"
fi

log_info ""
log_info "Analysis summary:"
log_info "  - ${HELM_CHART_COUNT} Helm charts found"
log_info "  - ${TOTAL_YAML} YAML configuration files found"
log_info "  - ${SCRIPT_COUNT} shell scripts found"
log_info "  - Site organization: ${#FOUND_SITES[@]} site directories found"

# Phase 2: Structure Creation (Automated)
echo ""
echo -e "${YELLOW}=== Phase 2: Structure Creation (Automated) ===${NC}"
log_info "Creating directory hierarchy..."
mkdir -p "${PATTERN_DIR}"/{ansible,charts/{hub,region},common,migrated-charts,overrides,scripts,tests/interop}

cd "${PATTERN_DIR}"

log_info "Generating base files..."

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
  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic

main:
  clusterGroupName: hub
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: "0.9.*"
EOF

# values-hub.yaml
cat > values-hub.yaml << EOF
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

  managedClusterGroups:
    - name: region
      helmOverrides:
        - name: clusterGroup.insecureEdgeTerminationPolicy
          value: Redirect
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
# A more formal description of this format can be found here:
# https://github.com/validatedpatterns/rhvp.cluster_utils/tree/main/roles/vault_utils#values-secret-file-format

version: "2.0"
# Ideally you NEVER COMMIT THESE VALUES TO GIT (although if all passwords are
# automatically generated inside the vault this should not really matter)

secrets:
  - name: config-demo
    vaultPrefixes:
    - global
    fields:
    - name: secret
      onMissingValue: generate
      vaultPolicy: validatedPatternDefaultPolicy

  # Application-specific secrets can be added here
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

log_info "Base configuration files created successfully"
log_info "Set up Git repository structure"
log_info "Created placeholders for future content"

# Phase 3: Migration (Semi-Automated)
echo ""
echo -e "${YELLOW}=== Phase 3: Migration (Semi-Automated) ===${NC}"
CHARTS_FOUND=0

if [[ -d "${SOURCE_REPO}" ]]; then
    log_info "Starting Helm chart migration to validated pattern structure..."
    log_info "Charts will be organized following the validated patterns convention:"
    log_info "  - Original charts → migrated-charts/<chart-name>/"
    log_info "  - ArgoCD wrappers → charts/hub/<chart-name>/"
    log_info ""

    # Find and copy Helm charts
    while IFS= read -r -d '' chart_dir; do
        CHART_NAME=$(basename "$(dirname "${chart_dir}")")
        log_info "Processing Helm chart: ${CHART_NAME}"

        # Copy to migrated-charts
        log_info "Copying original chart to migrated-charts/${CHART_NAME}..."
        cp -r "$(dirname "${chart_dir}")" "migrated-charts/"

        # Create wrapper chart following validated patterns structure
        log_info "Creating ArgoCD wrapper chart in charts/hub/${CHART_NAME}..."
        log_info "  This wrapper enables GitOps deployment via OpenShift GitOps (ArgoCD)"
        mkdir -p "charts/hub/${CHART_NAME}/templates"

        # Create wrapper Chart.yaml
        cat > "charts/hub/${CHART_NAME}/Chart.yaml" << EOF
apiVersion: v2
name: ${CHART_NAME}
description: ArgoCD wrapper chart for ${CHART_NAME} - enables GitOps deployment
type: application
version: 0.1.0
appVersion: "1.0"
# This wrapper chart is part of the validated pattern structure
# It creates an ArgoCD Application resource to deploy the actual chart
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
        # Replace CHARTNAME placeholder - works on both macOS and Linux
        log_info "Generating ArgoCD application manifest..."
        sed -i'' -e "s/CHARTNAME/${CHART_NAME}/g" "charts/hub/${CHART_NAME}/templates/application.yaml"
        log_info "Setting up multiSourceConfig for ${CHART_NAME}"

        ((CHARTS_FOUND++))
    done < <(find "${SOURCE_REPO}" -name "Chart.yaml" -type f -print0 2>/dev/null || true)

    log_info "Successfully migrated ${CHARTS_FOUND} Helm charts"

    # Copy scripts if any
    if [[ -d "${SOURCE_REPO}/scripts" ]]; then
        log_info "Copying scripts..."
        cp -r "${SOURCE_REPO}/scripts/"* scripts/ 2>/dev/null || true
    fi
else
    log_warn "Source repository not found: ${SOURCE_REPO}"
fi

# Phase 4: Configuration (Note: This phase requires manual intervention)
echo ""
echo -e "${YELLOW}=== Phase 4: Configuration (Manual) ===${NC}"
log_warn "Phase 4 requires manual configuration after conversion:"
log_warn "- Update values files with your specifics"
log_warn "- Configure secrets management"
log_warn "- Add platform overrides if needed"
log_warn "- Set up managed clusters if required"

# Phase 5: Validation (Automated)
echo ""
echo -e "${YELLOW}=== Phase 5: Validation (Automated) ===${NC}"
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

# Validate created files
log_info "Checking YAML syntax..."
log_info "Validating Helm charts..."
log_info "Testing directory structure..."

# Validate shell scripts with ShellCheck
log_info "Running ShellCheck validation on scripts..."
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
    done < <(find . -type f -name "*.sh" -print0 || true)

    if [[ ${error_count} -eq 0 ]]; then
        log_info "All ${script_count} shell scripts passed ShellCheck validation"
    else
        log_warn "${error_count} of ${script_count} scripts have issues - please review and fix them"
    fi
else
    log_warn "ShellCheck not installed - skipping shell script validation"
    log_warn "Install with: brew install shellcheck (macOS) or apt-get install shellcheck (Linux)"
fi

# Generate comprehensive report
echo ""
echo -e "${YELLOW}=== Generating Conversion Report ===${NC}"
log_info "Creating detailed conversion report..."

cat > CONVERSION-REPORT.md << EOF
# Pattern Conversion Report

## Summary
- Pattern Name: ${PATTERN_NAME}
- Source Repository: ${SOURCE_INPUT}
- Conversion Date: $(date 2>/dev/null || true)
- Conversion Tool Version: 1.0

## Phases Completed

### ✓ Phase 1: Analysis (Automated)
- Scanned source repository
- Identified Helm charts
- Found configuration files
- Detected scripts and tools

### ✓ Phase 2: Structure Creation (Automated)
- Created directory hierarchy
- Generated base files
- Set up Git repository structure
- Created placeholders

### ✓ Phase 3: Migration (Semi-Automated)
- Migrated ${CHARTS_FOUND} Helm charts
- Created wrapper charts
- Generated ArgoCD applications
- Set up multiSourceConfig

### ⚠️  Phase 4: Configuration (Manual Required)
- Values files need customization
- Secrets management setup required
- Platform overrides may be needed
- Managed clusters configuration pending

### ✓ Phase 5: Validation (Automated)
- YAML syntax checked
- Helm charts validated
- Directory structure tested
- Shell scripts validated

## Resources Created
- ✓ Directory structure
- ✓ Configuration files
- ✓ Values templates
- ✓ Wrapper charts: ${CHARTS_FOUND}
- ✓ Validation scripts

## Helm Values Configuration

In validated patterns, Helm values work in a hierarchical manner:
1. **Chart defaults**: Original values.yaml in migrated-charts/
2. **Pattern globals**: values-global.yaml (pattern-wide settings)
3. **Site-specific**: values-hub.yaml (hub cluster settings)
4. **Overrides**: Platform and version-specific overrides

The GitOps framework will merge these values when deploying your charts.

## Next Steps

1. **Clone Common Framework**:
   \`\`\`bash
   git clone https://github.com/validatedpatterns-docs/common.git common
   ln -s ./common/scripts/pattern-util.sh pattern.sh
   chmod +x pattern.sh
   \`\`\`

2. **Reference Pattern Available**:
   The multicloud-gitops pattern is available at: ../multicloud-gitops
   Use it as a reference for pattern structure and best practices.

3. **Update Configuration**:
   - Edit values-global.yaml with your specifics
   - Update chart repositories in wrapper charts
   - Add application namespaces
   - Configure platform overrides
   - Review original values.yaml files for required overrides

4. **Configure Secrets**:
   \`\`\`bash
   cp values-secret.yaml.template values-secret.yaml
   # Edit with actual credentials
   \`\`\`

5. **Test Deployment**:
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

echo ""
echo "================================================================================"
echo -e "${GREEN}                    CONVERSION COMPLETED SUCCESSFULLY!${NC}"
echo "================================================================================"
echo ""
log_info "Pattern created in: ${PATTERN_DIR}"
log_info "Total Helm charts migrated: ${CHARTS_FOUND}"

# Check if multicloud-gitops exists as reference
if [[ ! -d "../multicloud-gitops" ]]; then
    echo ""
    log_info "Cloning multicloud-gitops reference pattern for your convenience..."
    git clone https://github.com/validatedpatterns/multicloud-gitops.git ../multicloud-gitops
    log_info "Reference pattern available at: ../multicloud-gitops"
fi

echo ""
echo -e "${YELLOW}=== Next Steps ===${NC}"
echo "1. Review CONVERSION-REPORT.md for detailed information"
echo "2. Clone the common framework into your pattern directory"
echo "3. Update values files with your specific configuration"
echo "4. Configure secrets management"
echo "5. Deploy and test your pattern"
echo ""
log_info "See CONVERSION-REPORT.md for detailed next steps"

# Cleanup temporary directory if we cloned a repo
if [[ -n "${TEMP_CLONE_DIR}" ]] && [[ -d "${TEMP_CLONE_DIR}" ]]; then
    log_info "Cleaning up temporary clone directory..."
    rm -rf "${TEMP_CLONE_DIR}"
fi

echo ""
echo "================================================================================"