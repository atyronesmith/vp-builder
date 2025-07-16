# Validated Pattern Conversion Process

## Overview
This document provides a step-by-step process for converting any project into a Red Hat Validated Pattern. Follow these steps in order to ensure a successful conversion.

## Pre-Conversion Checklist

- [ ] Access to source project repository
- [ ] Understanding of project architecture
- [ ] List of all components and dependencies
- [ ] OpenShift cluster for testing (optional but recommended)
- [ ] Git repository for the new pattern

## Step 1: Analyze Source Project

### 1.1 Inventory Components
```bash
# List all Helm charts
find . -name "Chart.yaml" -type f

# List all Kubernetes manifests
find . -name "*.yaml" -o -name "*.yml" | grep -E "(deployment|service|configmap|secret)"

# List container images
grep -r "image:" . | grep -v "^Binary" | sort -u
```

### 1.2 Document Dependencies
- Operators required
- External services
- Storage requirements
- Network policies
- Security constraints

### 1.3 Create Architecture Map
Document:
- Component relationships
- Communication flows
- Data persistence needs
- External integrations

## Step 2: Initialize Pattern Structure

### 2.1 Create Base Repository
```bash
# Create pattern directory
mkdir -p <pattern-name>
cd <pattern-name>

# Initialize git
git init
```

### 2.2 Create Directory Structure
```bash
# Create all required directories
mkdir -p ansible charts/{hub,region} common migrated-charts \
         overrides scripts tests/interop

# Create .gitkeep files to preserve empty directories
touch charts/region/.gitkeep overrides/.gitkeep tests/interop/.gitkeep
```

### 2.3 Generate Base Files
```bash
# Create ansible.cfg
cat > ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
interpreter_python = auto_silent
EOF

# Create Makefile
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

# Create .gitignore
cat > .gitignore << 'EOF'
common
values-secret.yaml
*.swp
*.bak
*~
EOF
```

## Step 3: Configure Pattern Metadata

### 3.1 Create pattern-metadata.yaml
```yaml
name: <pattern-name>
displayName: "<Human Readable Name>"
description: |
  <Multi-line description of what this pattern does>
gitOpsRepo: "https://github.com/<org>/<pattern-name>"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/<pattern-name>/"
architectureReadmeUrl: "https://github.com/<org>/<pattern-name>/blob/main/README.md"
organizations:
  - redhat
  - validatedpatterns
```

### 3.2 Create values-global.yaml
```yaml
global:
  pattern: <pattern-name>
  targetRevision: main
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: 0.9.0

  git:
    provider: github
    account: <your-github-org>
    email: <your-email>
    dev_revision: main

main:
  clusterGroupName: hub

clusterGroup:
  name: hub
  isHubCluster: true

  namespaces:
    - open-cluster-management
    - openshift-gitops
    - external-secrets
    - vault
    # Add your application namespaces here

  subscriptions:
    acm:
      namespace: open-cluster-management
      channel: release-2.10
      source: redhat-operators

    gitops:
      namespace: openshift-gitops
      channel: latest
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
```

## Step 4: Migrate Applications

### 4.1 Copy Original Charts
```bash
# Copy helm charts to migrated-charts
cp -r <source-repo>/deploy/helm/* migrated-charts/
```

### 4.2 Create Wrapper Charts
For each application, create a wrapper chart:

```bash
# Example for app named 'myapp'
mkdir -p charts/hub/myapp/templates

# Create Chart.yaml
cat > charts/hub/myapp/Chart.yaml << EOF
apiVersion: v2
name: myapp
description: Wrapper chart for myapp
version: 0.1.0
appVersion: "1.0"
EOF

# Create values.yaml
cat > charts/hub/myapp/values.yaml << EOF
clusterGroup:
  applications:
    myapp:
      enabled: true
      chart: myapp
      repoURL: https://charts.example.com
      targetRevision: 1.0.0
      valuesFile: values-hub-myapp.yaml
global:
  targetRepo: ""
  targetRevision: ""
  namespace: myapp-namespace
EOF
```

### 4.3 Create ArgoCD Application Template
```yaml
# charts/hub/myapp/templates/application.yaml
{{- if .Values.clusterGroup.applications.myapp.enabled }}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "300"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  sources:
    - repoURL: {{ .Values.global.targetRepo }}
      targetRevision: {{ .Values.global.targetRevision }}
      ref: patternref
    - chart: {{ .Values.clusterGroup.applications.myapp.chart }}
      repoURL: {{ .Values.clusterGroup.applications.myapp.repoURL }}
      targetRevision: {{ .Values.clusterGroup.applications.myapp.targetRevision }}
      helm:
        ignoreMissingValueFiles: true
        valueFiles:
          - $patternref/{{ .Values.clusterGroup.applications.myapp.valuesFile }}
  destination:
    server: https://kubernetes.default.svc
    namespace: {{ .Values.global.namespace }}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
{{- end }}
```

## Step 5: Configure Secrets

### 5.1 Create values-secret.yaml.template
```yaml
global:
  git:
    token: REPLACE_WITH_YOUR_GITHUB_TOKEN

secrets:
  - name: git-secret
    fields:
      - name: token
        value: REPLACE_WITH_YOUR_GITHUB_TOKEN

  - name: container-registry
    fields:
      - name: username
        value: REPLACE_WITH_USERNAME
      - name: password
        value: REPLACE_WITH_PASSWORD

externalSecrets:
  vault:
    server: https://vault.example.com:8200
    path: secret/data/hub
```

### 5.2 Update .gitignore
Ensure values-secret.yaml is never committed.

## Step 6: Setup Ansible Automation

### 6.1 Create ansible/site.yaml
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: no
  vars:
    ansible_python_interpreter: "{{ ansible_playbook_python }}"

  tasks:
    - name: Check for required collections
      debug:
        msg: |
          This playbook requires the following collections:
          - kubernetes.core
          - rhvp.cluster_utils
          Install with: ansible-galaxy collection install <collection>

    - name: Deploy pattern pre-requisites
      when: ACTION is not defined or ACTION == "install"
      block:
        - name: Check if common exists
          stat:
            path: ../common
          register: common_dir

        - name: Fail if common not found
          fail:
            msg: "Common framework not found. Clone from validatedpatterns-docs/common"
          when: not common_dir.stat.exists
```

## Step 7: Platform-Specific Overrides

### 7.1 Create AWS Override
```yaml
# overrides/values-AWS.yaml
clusterGroup:
  provider: AWS
  storageClass: gp3-csi

platform:
  aws:
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1b
```

### 7.2 Create Azure Override
```yaml
# overrides/values-Azure.yaml
clusterGroup:
  provider: Azure
  storageClass: managed-csi

platform:
  azure:
    region: eastus
    resourceGroup: validated-patterns
```

## Step 8: Integration Steps

### 8.1 Clone Common Framework
```bash
git clone https://github.com/validatedpatterns-docs/common.git
```

### 8.2 Create pattern.sh Symlink
```bash
ln -s ./common/scripts/pattern-util.sh pattern.sh
chmod +x pattern.sh
```

### 8.3 Test Pattern Scripts
```bash
./pattern.sh make show
./pattern.sh make help
```

## Step 9: Documentation

### 9.1 Create README.md
Include:
- Pattern overview
- Architecture diagram
- Prerequisites
- Installation steps
- Configuration options
- Troubleshooting

### 9.2 Create Architecture Diagrams
Use draw.io or similar tools to create:
- Component architecture
- Deployment topology
- Data flow diagrams

## Step 10: Validation and Testing

### 10.1 Validate YAML Files
```bash
# Install yamllint
pip install yamllint

# Validate all YAML files
find . -name "*.yaml" -o -name "*.yml" | xargs yamllint
```

### 10.2 Validate Helm Charts
```bash
# For each chart
helm lint charts/hub/*/
helm template test charts/hub/*/ --values values-global.yaml
```

### 10.3 Validate Shell Scripts
```bash
# Install ShellCheck if not already installed
# macOS: brew install shellcheck
# Linux: apt-get install shellcheck or yum install ShellCheck

# Validate all shell scripts
find . -type f -name "*.sh" -exec shellcheck {} \;

# Fix any errors reported by ShellCheck
# Common fixes:
# - Quote all variables: "$var" instead of $var
# - Use $() instead of backticks for command substitution
# - Use [[ ]] for conditionals in bash scripts
```

### 10.4 Test Deployment
```bash
# Login to OpenShift
oc login <cluster-url>

# Deploy pattern
make install
```

## Post-Conversion Tasks

### 1. Repository Setup
- [ ] Push to Git repository
- [ ] Configure branch protection
- [ ] Setup CI/CD pipelines
- [ ] Add collaborators

### 2. Documentation
- [ ] Update README with screenshots
- [ ] Create video walkthrough
- [ ] Document known issues
- [ ] Create FAQ section

### 3. Community
- [ ] Submit to validatedpatterns.io
- [ ] Create blog post
- [ ] Share in forums
- [ ] Gather feedback

## Troubleshooting Common Issues

### Issue: Common Makefile not found
```bash
# Clone the common repository
git clone https://github.com/validatedpatterns-docs/common.git
```

### Issue: ArgoCD Application not syncing
- Check multiSourceConfig is enabled
- Verify chart repository is accessible
- Check values file path is correct

### Issue: Secrets not working
- Verify External Secrets Operator is installed
- Check Vault connectivity
- Validate secret paths

### Issue: Pattern won't install
- Check OpenShift version compatibility
- Verify all operators are available
- Review operator subscriptions

## Automation Script Template

Create `convert-to-pattern.sh`:
```bash
#!/bin/bash
set -euo pipefail

PATTERN_NAME=$1
SOURCE_REPO=$2

if [ -z "$PATTERN_NAME" ] || [ -z "$SOURCE_REPO" ]; then
    echo "Usage: $0 <pattern-name> <source-repo-path>"
    exit 1
fi

echo "Converting $SOURCE_REPO to validated pattern: $PATTERN_NAME"

# Create structure
mkdir -p "$PATTERN_NAME"
cd "$PATTERN_NAME"

# Initialize directories
mkdir -p ansible charts/{hub,region} migrated-charts overrides scripts tests/interop

# Copy this script's logic here...

# Validate shell scripts
echo "Validating shell scripts..."
if command -v shellcheck >/dev/null 2>&1; then
    find . -type f -name "*.sh" -exec shellcheck {} \;
else
    echo "Warning: ShellCheck not installed, skipping shell script validation"
fi

echo "Conversion complete! Next steps:"
echo "1. Clone common framework"
echo "2. Update values files with your specifics"
echo "3. Test deployment with 'make install'"
```

## Conclusion

Following this process ensures a systematic and complete conversion of any project into a validated pattern. The key is understanding the source project's architecture and carefully mapping it to the validated patterns framework.