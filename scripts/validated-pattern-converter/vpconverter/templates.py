"""
File templates for validated pattern converter.

This module contains Jinja2 templates for generating various
configuration files required by the validated patterns framework.
"""

# .gitignore template
GITIGNORE_TEMPLATE = """\
common
values-secret.yaml
*.swp
*.bak
*~
.DS_Store
"""

# ansible.cfg template
ANSIBLE_CFG_TEMPLATE = """\
[defaults]
host_key_checking = False
interpreter_python = auto_silent
"""

# ansible/site.yaml template
ANSIBLE_SITE_TEMPLATE = """\
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
"""

# Makefile template
MAKEFILE_TEMPLATE = """\
.PHONY: default
default: help

%:
\t@if [ -f common/Makefile ]; then \\
\t\tmake -f common/Makefile $@; \\
\telse \\
\t\techo "ERROR: common/Makefile not found. Clone from:"; \\
\t\techo "https://github.com/validatedpatterns-docs/common.git"; \\
\t\texit 1; \\
\tfi
"""

# pattern-metadata.yaml template
PATTERN_METADATA_TEMPLATE = """\
name: {{ pattern_name }}
displayName: "{{ pattern_name }} Pattern"
description: |
  TODO: Add description
gitOpsRepo: "https://github.com/{{ github_org }}/{{ pattern_dir }}"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/{{ pattern_name }}/"
architectureReadmeUrl: "https://github.com/{{ github_org }}/{{ pattern_dir }}/blob/main/README.md"
organizations:
  - {{ github_org }}
  - validatedpatterns
"""

# values-global.yaml template
VALUES_GLOBAL_TEMPLATE = """\
global:
  pattern: {{ pattern_name }}
  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic

main:
  clusterGroupName: hub
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: "0.9.*"
"""

# values-hub.yaml template
VALUES_HUB_TEMPLATE = """\
clusterGroup:
  name: hub
  isHubCluster: true

  namespaces:
    - open-cluster-management
    - openshift-gitops
    - external-secrets
    - vault
    # TODO: Add application namespaces
{%- for chart in helm_charts %}
    - {{ chart.name }}
{%- endfor %}

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

{%- for chart in helm_charts %}

    {{ chart.name }}:
      name: {{ chart.name }}
      namespace: {{ chart.name }}
      chart: {{ chart.name }}
      repoURL: https://charts.example.com  # TODO: Update
      targetRevision: {{ chart.version or "1.0.0" }}
      valuesFile: values-hub-{{ chart.name }}.yaml
      enabled: true
{%- endfor %}

  managedClusterGroups:
    - name: region
      helmOverrides:
        - name: clusterGroup.insecureEdgeTerminationPolicy
          value: Redirect
"""

# values-region.yaml template
VALUES_REGION_TEMPLATE = """\
clusterGroup:
  name: region
  isHubCluster: false
  targetCluster: in-cluster

  applications: {}
"""

# values-secret.yaml.template
VALUES_SECRET_TEMPLATE = """\
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
"""

# README.md template
README_TEMPLATE = """\
# {{ pattern_name }} Validated Pattern

## Overview
TODO: Add pattern description

## Prerequisites
- OpenShift Container Platform 4.12+
- Helm 3.x
- Git
- Make

## Installation

### Quick Start
```bash
# Clone the pattern
git clone https://github.com/{{ github_org }}/{{ pattern_dir }}.git
cd {{ pattern_dir }}

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
```

## Components
{%- if helm_charts %}
### Helm Charts
{%- for chart in helm_charts %}
- **{{ chart.name }}**: {{ chart.description or "TODO: Add description" }}
{%- endfor %}
{%- endif %}

## Architecture
TODO: Add architecture diagram and description

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
Apache License 2.0
"""

# Wrapper Chart.yaml template for ArgoCD
WRAPPER_CHART_TEMPLATE = """\
apiVersion: v2
name: {{ chart_name }}
description: ArgoCD wrapper chart for {{ chart_name }} - enables GitOps deployment
type: application
version: 0.1.0
appVersion: "1.0"
# This wrapper chart is part of the validated pattern structure
# It creates an ArgoCD Application resource to deploy the actual chart
"""

# Wrapper values.yaml template
WRAPPER_VALUES_TEMPLATE = """\
clusterGroup:
  applications:
    {{ chart_name }}:
      enabled: true
      chart: {{ chart_name }}
      repoURL: https://charts.example.com  # TODO: Update
      targetRevision: {{ chart_version or "1.0.0" }}  # TODO: Update
      valuesFile: values-hub-{{ chart_name }}.yaml

global:
  targetRepo: ""
  targetRevision: ""
  namespace: {{ chart_name }}
"""

# ArgoCD Application template
ARGOCD_APPLICATION_TEMPLATE = """\
{{- if .Values.clusterGroup.applications.{{ chart_name }}.enabled }}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ "{{ .Values.clusterGroup.applications." }}{{ chart_name }}{{ ".name }}" }}
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "300"
spec:
  project: default
  sources:
    - repoURL: {{ "{{ .Values.global.targetRepo }}" }}
      targetRevision: {{ "{{ .Values.global.targetRevision }}" }}
      ref: patternref
    - chart: {{ "{{ .Values.clusterGroup.applications." }}{{ chart_name }}{{ ".chart }}" }}
      repoURL: {{ "{{ .Values.clusterGroup.applications." }}{{ chart_name }}{{ ".repoURL }}" }}
      targetRevision: {{ "{{ .Values.clusterGroup.applications." }}{{ chart_name }}{{ ".targetRevision }}" }}
      helm:
        ignoreMissingValueFiles: true
        valueFiles:
          - ${'${patternref}/'}{{ "{{ .Values.clusterGroup.applications." }}{{ chart_name }}{{ ".valuesFile }}" }}
  destination:
    server: https://kubernetes.default.svc
    namespace: {{ "{{ .Values.global.namespace }}" }}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
{{- end }}
"""

# Validation script template
VALIDATION_SCRIPT_TEMPLATE = """\
#!/bin/bash
set -euo pipefail

echo "Validating pattern deployment..."

# Check namespaces
for ns in openshift-gitops open-cluster-management external-secrets vault{{ namespace_list }}; do
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
for app in hub-applications hub-operators{{ app_list }}; do
    if oc get application "${app}" -n openshift-gitops &> /dev/null; then
        echo "✓ ArgoCD app ${app} exists"
    else
        echo "✗ ArgoCD app ${app} missing"
    fi
done

echo "Validation complete!"
"""

# Conversion report template
CONVERSION_REPORT_TEMPLATE = """\
# Pattern Conversion Report

## Summary
- Pattern Name: {{ pattern_name }}
- Source Repository: {{ source_repo }}
- Conversion Date: {{ conversion_date }}
- Conversion Tool Version: {{ version }}

## Phases Completed

### ✓ Phase 1: Analysis (Automated)
- Scanned source repository
- Identified {{ helm_charts_count }} Helm charts
- Found {{ yaml_files_count }} configuration files
- Detected {{ scripts_count }} scripts

### ✓ Phase 2: Structure Creation (Automated)
- Created directory hierarchy
- Generated base files
- Set up Git repository structure
- Created placeholders

### ✓ Phase 3: Migration (Semi-Automated)
- Migrated {{ helm_charts_count }} Helm charts
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
- ✓ Wrapper charts: {{ helm_charts_count }}
- ✓ Validation scripts

## Detected Patterns
{%- if detected_patterns %}
{%- for pattern in detected_patterns %}
- {{ pattern }}
{%- endfor %}
{%- else %}
- None detected
{%- endif %}

## Next Steps

1. **Clone Common Framework**:
   ```bash
   git clone https://github.com/validatedpatterns-docs/common.git common
   ln -s ./common/scripts/pattern-util.sh pattern.sh
   chmod +x pattern.sh
   ```

2. **Update Configuration**:
   - Edit values-global.yaml with your specifics
   - Update chart repositories in wrapper charts
   - Add application namespaces
   - Configure platform overrides

3. **Configure Secrets**:
   ```bash
   cp values-secret.yaml.template values-secret.yaml
   # Edit with actual credentials
   ```

4. **Test Deployment**:
   ```bash
   make install
   ./scripts/validate-deployment.sh
   ```
"""