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

.PHONY: help
##@ Pattern Help

help: ## This help message
\t@make -f common/Makefile MAKEFILE_LIST="Makefile common/Makefile" help

%:
\t@if [ -f common/Makefile ]; then \\
\t\tmake -f common/Makefile $@; \\
\telse \\
\t\techo "No common/Makefile found. Please run:"; \\
\t\techo "  git clone https://github.com/validatedpatterns/common.git"; \\
\t\techo "or"; \\
\t\techo "  git submodule update --init"; \\
\t\techo ""; \\
\t\techo "For more information: https://validatedpatterns.io/patterns/"; \\
\t\texit 1; \\
\tfi

##@ Pattern Installation

.PHONY: install
install: operator-deploy post-install ## Install the pattern
\t@echo "Installed {{ pattern_name }} pattern successfully"

.PHONY: post-install
post-install: ## Post installation tasks
\t@make load-secrets
\t@echo "Post-install complete"

.PHONY: uninstall
uninstall: operator-destroy ## Uninstall the pattern
\t@echo "Uninstalled {{ pattern_name }} pattern"

##@ Pattern Testing and Validation

.PHONY: test
test: ## Run pattern tests
\t@make -f common/Makefile PATTERN_OPTS="-f values-global.yaml -f values-hub.yaml" test

.PHONY: validate-pattern
validate-pattern: ## Validate pattern structure
\t@make -f common/Makefile validate-pattern

##@ Local Development

.PHONY: predeploy
predeploy: ## Run pre-deployment checks
\t@./pattern.sh make show-secrets
\t@./pattern.sh make validate-origin

##@ Utility Targets

.PHONY: bootstrap
bootstrap: ## DEPRECATED: Use 'make install' instead
\t@echo "WARNING: 'make bootstrap' is deprecated. Use 'make install' instead."
\t@make install
"""

# pattern-metadata.yaml template
PATTERN_METADATA_TEMPLATE = """\
name: {{ pattern_name }}
displayName: "{{ pattern_display_name }}"
description: |
  {{ pattern_description }}
gitOpsRepo: "https://github.com/{{ github_org }}/{{ pattern_dir }}"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/{{ pattern_name }}/"
architectureReadmeUrl: "https://github.com/{{ github_org }}/{{ pattern_dir }}/blob/main/README.md"

# Pattern classification
tier: sandbox
supportLevel: community

# Organizations
organizations:
  - {{ github_org }}
  - validatedpatterns

# Categories this pattern belongs to
categories:
{%- for category in categories %}
  - {{ category }}
{%- endfor %}

# Programming languages used in this pattern
languages:
{%- for language in languages %}
  - {{ language }}
{%- endfor %}

# Industries this pattern applies to
industries:
{%- for industry in industries %}
  - {{ industry }}
{%- endfor %}

# Required products and their versions
products:
{%- for product in products %}
  - name: "{{ product.name }}"
    version: "{{ product.version }}"
    source: "{{ product.source }}"
    confidence: "{{ product.confidence }}"
{%- if product.operator_info %}
    operator:
      channel: "{{ product.operator_info.channel }}"
      source: "{{ product.operator_info.source }}"
{%- if product.operator_info.subscription %}
      subscription: "{{ product.operator_info.subscription }}"
{%- endif %}
{%- endif %}
{%- endfor %}

# Detected architecture patterns
patterns:
{%- for pattern in detected_patterns %}
  - name: {{ pattern }}
    confidence: high
{%- endfor %}

# Links to additional resources
links:
  - name: "Validated Patterns Documentation"
    url: "https://validatedpatterns.io/"
  - name: "Common Framework"
    url: "https://github.com/validatedpatterns/common"
  - name: "Pattern Development Guide"
    url: "https://validatedpatterns.io/learn/quickstart/"

# Creation metadata
created: "{{ creation_date }}"
version: "1.0.0"
"""

# values-global.yaml template
VALUES_GLOBAL_TEMPLATE = """\
global:
  pattern: {{ pattern_name }}
  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic

  git:
    # This is only needed when using in-cluster-hub (Advanced)
    account: SOMEWHERE
    dev_revision: main
    email: SOMEWHERE@EXAMPLE.COM
    hostname: github.com

  hubClusterDomain: apps.hub.example.com
  localClusterDomain: apps.hub.example.com
  storageClass: gp3-csi
  clusterDomain: apps.hub.example.com
  clusterPlatform: aws
  clusterVersion: "4.12"
  targetRevision: main

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
    - golang-external-secrets
{%- for chart in helm_charts %}
    - {{ chart.name }}
{%- endfor %}

  subscriptions:
    acm:
      name: advanced-cluster-management
      namespace: open-cluster-management
      channel: release-2.11
      source: redhat-operators

  projects:
    - hub
{%- for chart in helm_charts %}
    - {{ chart.name }}
{%- endfor %}

  applications:
    acm:
      name: acm
      namespace: open-cluster-management
      project: hub
      path: common/acm
      chart: acm
      chartVersion: 0.1.*
      ignoreDifferences:
        - group: internal.open-cluster-management.io
          kind: ManagedClusterInfo
          jsonPointers:
            - /spec/loggingCA

    vault:
      name: vault
      namespace: vault
      project: hub
      path: common/hashicorp-vault
      chart: hashicorp-vault
      chartVersion: 0.1.*

    golang-external-secrets:
      name: golang-external-secrets
      namespace: golang-external-secrets
      project: hub
      path: common/golang-external-secrets
      chart: golang-external-secrets
      chartVersion: 0.1.*

{%- for chart in helm_charts %}
    {{ chart.name }}:
      name: {{ chart.name }}
      namespace: {{ chart.name }}
      project: {{ chart.name }}
      path: charts/all/{{ chart.name }}
{%- endfor %}

  managedClusterGroups: []

  imperative:
    # NOTE: We *must* use lists and not hashes. As hashes lose ordering once parsed by helm
    # The default schedule is every 10 minutes: imperative.schedule
    # Total timeout of all jobs is 1h: imperative.activeDeadlineSeconds
    # imagePullPolicy is set to always: imperative.imagePullPolicy
    # For additional overrides that apply to the jobs, please refer to:
    # https://hybrid-cloud-patterns.io/imperative-actions/#additional-job-customizations
    jobs: []
    #  - name: custom-job
    #    playbook: ansible/playbooks/custom-job.yaml
    #    image: registry.redhat.io/ansible-automation-platform-24/ee-supported-rhel8:latest

  sharedValueFiles:
    - '/overrides/values-{{ "{{" }} $.Values.global.clusterPlatform {{ "}}" }}.yaml'
"""

# values-region.yaml template
VALUES_REGION_TEMPLATE = """\
clusterGroup:
  name: region
  isHubCluster: false

  namespaces:
    - golang-external-secrets
{%- for chart in helm_charts %}
    - {{ chart.name }}
{%- endfor %}

  subscriptions: {}

  projects:
    - region
{%- for chart in helm_charts %}
    - {{ chart.name }}
{%- endfor %}

  applications:
    golang-external-secrets:
      name: golang-external-secrets
      namespace: golang-external-secrets
      project: region
      path: common/golang-external-secrets
      chart: golang-external-secrets
      chartVersion: 0.1.*

{%- for chart in helm_charts %}
    {{ chart.name }}:
      name: {{ chart.name }}
      namespace: {{ chart.name }}
      project: {{ chart.name }}
      path: charts/all/{{ chart.name }}
{%- endfor %}

  imperative:
    jobs: []
    cronJobs: []

  managedClusterGroups: []

  sharedValueFiles:
    - '/overrides/values-{{ "{{" }} $.Values.global.clusterPlatform {{ "}}" }}.yaml'
"""

# values-secret.yaml.template
VALUES_SECRET_TEMPLATE = """\
# NEVER COMMIT THIS FILE TO GIT
# A more formal description of this format can be found here:
# https://github.com/validatedpatterns/rhvp.cluster_utils/tree/main/roles/vault_utils#values-secret-file-format

version: "2.0"

# By default the secretStore backend is `vault`
# These are the settings to connect to the vault server instance
secretStore:
  backend: vault
  vault:
    # Set this depending on your vault deployment
    # Set it to kubernetes if your vault server is running on the same cluster
    # Set it to https://vault.example.com:8200 if your vault server is running on a different cluster
    approle_secret: vault-secret
    base_url: kubernetes
    ca_cert: https_cert

secrets:
  - name: aws-creds
    vaultPrefixes:
      - global
    fields:
      - name: aws_access_key_id
        value: REPLACE_WITH_AWS_ACCESS_KEY
      - name: aws_secret_access_key
        value: REPLACE_WITH_AWS_SECRET_KEY

  - name: container-registry
    vaultPrefixes:
      - global
    fields:
      - name: username
        value: REPLACE_WITH_REGISTRY_USERNAME
      - name: password
        value: REPLACE_WITH_REGISTRY_PASSWORD

  - name: github-token
    vaultPrefixes:
      - global
    fields:
      - name: token
        value: REPLACE_WITH_GITHUB_TOKEN

  # Application-specific secrets can be added here
  # - name: app-secret
  #   vaultPrefixes:
  #     - hub
  #   fields:
  #     - name: api-key
  #       value: REPLACE_WITH_API_KEY
  #     - name: onMissingValue
  #       value: generate
"""

# README.md template
README_TEMPLATE = """\
# {{ pattern_name }} Validated Pattern

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

This is a validated pattern that follows the [Validated Patterns](https://validatedpatterns.io/) framework for GitOps-based deployments on OpenShift.

## Prerequisites

- OpenShift Container Platform 4.12+
- Git
- Make
- An OpenShift cluster with cluster-admin privileges

## Quick Start

### 1. Clone and Setup

```bash
# Clone the pattern repository
git clone https://github.com/{{ github_org }}/{{ pattern_dir }}.git
cd {{ pattern_dir }}

# Run the setup script to configure common framework
./scripts/setup.sh
```

### 2. Configure Secrets

```bash
# Edit the secrets file with your actual values
cp values-secret.yaml.template values-secret.yaml
# Edit values-secret.yaml with your environment-specific secrets
```

### 3. Deploy the Pattern

```bash
# Deploy the complete pattern
make install
```

### 4. Verify Deployment

```bash
# Check pattern status
make test

# Validate pattern deployment
make validate-pattern
```

## Alternative Setup (Manual)

If you prefer manual setup:

```bash
# Clone the common framework
git clone https://github.com/validatedpatterns/common.git

# Create pattern.sh symlink
ln -sf common/scripts/pattern-util.sh pattern.sh

# Configure secrets
cp values-secret.yaml.template values-secret.yaml
# Edit values-secret.yaml with your secrets

# Deploy
make install
```

## Architecture

This pattern deploys the following components:

### Hub Cluster Components
- **Advanced Cluster Management (ACM)**: Multi-cluster management
- **HashiCorp Vault**: Secret management
- **External Secrets Operator**: Secret synchronization

{%- if helm_charts %}
### Application Components
{%- for chart in helm_charts %}
- **{{ chart.name }}**: {{ chart.description or "Application component" }}
{%- endfor %}
{%- endif %}

## Pattern Structure

```
{{ pattern_dir }}/
├── charts/                    # Helm charts
│   ├── all/                  # Charts that can run anywhere
│   ├── hub/                  # Hub-specific charts
│   └── region/               # Regional charts
├── common/                   # Common framework (git submodule/clone)
├── overrides/               # Platform-specific overrides
├── scripts/                 # Utility scripts
├── values-global.yaml       # Global configuration
├── values-hub.yaml         # Hub cluster configuration
├── values-region.yaml      # Regional cluster configuration
├── values-secret.yaml.template # Secret template
└── Makefile                # Main deployment interface
```

## Configuration

### Values Files

- **values-global.yaml**: Global pattern configuration
- **values-hub.yaml**: Hub cluster specific configuration  
- **values-region.yaml**: Regional cluster configuration
- **values-secret.yaml**: Sensitive configuration (not committed)

### Platform Overrides

The pattern supports platform-specific overrides in the `overrides/` directory:

- `values-AWS.yaml` - AWS-specific configurations
- `values-Azure.yaml` - Azure-specific configurations
- `values-GCP.yaml` - GCP-specific configurations

## Common Operations

### View Pattern Status
```bash
make show-secrets
```

### Update Pattern
```bash
git pull
make upgrade
```

### Uninstall Pattern
```bash
make uninstall
```

### Test Pattern
```bash
make test
```

## Troubleshooting

### Common Issues

1. **Pattern fails to deploy**: Check that you're logged into the correct OpenShift cluster
2. **Missing secrets**: Ensure values-secret.yaml is properly configured
3. **Common framework missing**: Run `./scripts/setup.sh` to set up the common framework

### Getting Help

- Check the [Validated Patterns documentation](https://validatedpatterns.io/)
- Review the [common framework](https://github.com/validatedpatterns/common) documentation
- Open an issue in this repository

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## More Information

- [Validated Patterns Hub](https://validatedpatterns.io/)
- [Pattern Development Guide](https://validatedpatterns.io/learn/quickstart/)
- [Common Framework Documentation](https://github.com/validatedpatterns/common)
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
# ArgoCD Applications are now managed by the ClusterGroup chart
# This file is kept as a placeholder for backward compatibility
#
# Applications are defined in values-hub.yaml under clusterGroup.applications
# The ClusterGroup chart will create the ArgoCD Application resources
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

## Manual Tasks Required
- Update pattern-metadata.yaml description
- Add architecture diagram
- Update README.md
- Configure managed clusters (if needed)
- Add platform-specific overrides
- Test on OpenShift cluster
"""

# ClusterGroup Chart.yaml template
CLUSTERGROUP_CHART_TEMPLATE = """\
apiVersion: v2
name: {{ pattern_name }}
description: {{ description }}
type: application
version: 0.1.0
appVersion: "1.0"
dependencies:
  - name: clustergroup
    version: "~{{ clustergroup_version }}"
    repository: https://charts.validatedpatterns.io
"""

# ClusterGroup values.yaml template
CLUSTERGROUP_VALUES_TEMPLATE = """\
global:
  pattern: {{ pattern_name }}
  repoURL: {{ git_repo_url }}
  targetRevision: {{ git_branch }}
  namespace: {{ pattern_name }}
  hubClusterDomain: {{ hub_cluster_domain }}
  localClusterDomain: {{ local_cluster_domain }}

clusterGroup:
  name: hub
  isHubCluster: true
  
  namespaces:
{%- for namespace in namespaces %}
    - {{ namespace }}
{%- endfor %}
  
  subscriptions:
{%- for subscription in subscriptions %}
    {{ subscription.name }}:
      name: {{ subscription.name }}
      namespace: {{ subscription.namespace }}
      channel: {{ subscription.channel }}
{%- endfor %}
  
  projects:
{%- for project in projects %}
    - {{ project }}
{%- endfor %}
  
  applications:
{%- for app in applications %}
    {{ app.name }}:
      name: {{ app.name }}
      namespace: {{ app.namespace }}
      project: {{ app.project }}
      path: {{ app.path }}
{%- endfor %}
"""

# Bootstrap application template
BOOTSTRAP_APPLICATION_TEMPLATE = """\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ pattern_name }}-hub
  namespace: openshift-gitops
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: {{ git_repo }}
    targetRevision: {{ target_revision }}
    path: charts/hub/clustergroup
    helm:
      valueFiles:
        - "../../../values-global.yaml"
        - "../../../values-hub.yaml"
  destination:
    server: https://kubernetes.default.svc
    namespace: openshift-gitops
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    retry:
      limit: 10
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 5m
"""

# Pattern install bootstrap script
PATTERN_INSTALL_SCRIPT_TEMPLATE = """\
#!/bin/bash
set -euo pipefail

# Pattern Bootstrap Script
# This script bootstraps the validated pattern deployment

PATTERN_NAME="{{ pattern_name }}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PATTERN_DIR="${SCRIPT_DIR}/.."

echo "Bootstrapping ${PATTERN_NAME} pattern..."

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    echo "ERROR: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

# Check if OpenShift GitOps is installed
if ! oc get subscription -n openshift-operators openshift-gitops-operator &> /dev/null; then
    echo "ERROR: OpenShift GitOps operator is not installed."
    echo "Please install it from the OperatorHub or run 'make operator-deploy-openshift-gitops'"
    exit 1
fi

# Wait for GitOps to be ready
echo "Waiting for OpenShift GitOps to be ready..."
oc wait --for=condition=Ready --timeout=300s -n openshift-gitops pod -l app.kubernetes.io/name=openshift-gitops-server

# Apply the bootstrap application
echo "Applying bootstrap application..."
oc apply -f "${PATTERN_DIR}/bootstrap/hub-bootstrap.yaml"

echo "Bootstrap complete! The pattern will now be deployed by ArgoCD."
echo "You can monitor the progress in the OpenShift GitOps console."
"""

# Updated Makefile template with bootstrap support
MAKEFILE_BOOTSTRAP_TEMPLATE = """\
.PHONY: default
default: help

.PHONY: help
help:
\t@echo "Validated Pattern Makefile Targets:"
\t@echo "  install           - Deploy the pattern (requires common framework)"
\t@echo "  bootstrap         - Bootstrap the pattern using ArgoCD directly"
\t@echo "  upgrade           - Upgrade the pattern"
\t@echo "  uninstall         - Uninstall the pattern"
\t@echo "  validate          - Validate the pattern deployment"
\t@echo ""
\t@echo "First time setup:"
\t@echo "  1. git clone https://github.com/validatedpatterns-docs/common.git"
\t@echo "  2. make install"
\t@echo ""
\t@echo "Alternative (without common):"
\t@echo "  make bootstrap"

.PHONY: bootstrap
bootstrap:
\t@echo "Bootstrapping pattern without common framework..."
\t@if [ ! -f bootstrap/hub-bootstrap.yaml ]; then \\
\t\techo "ERROR: bootstrap/hub-bootstrap.yaml not found"; \\
\t\texit 1; \\
\tfi
\t@./scripts/pattern-bootstrap.sh

.PHONY: validate
validate:
\t@echo "Validating pattern deployment..."
\t@./scripts/validate-deployment.sh

# Common framework targets
%:
\t@if [ -f common/Makefile ]; then \\
\t\tmake -f common/Makefile $@; \\
\telse \\
\t\techo "ERROR: common/Makefile not found. Clone from:"; \\
\t\techo "https://github.com/validatedpatterns-docs/common.git"; \\
\t\techo ""; \\
\t\techo "Or use 'make bootstrap' to deploy without common framework"; \\
\t\texit 1; \\
\tfi
"""

# Imperative Job template for idempotent tasks
IMPERATIVE_JOB_TEMPLATE = """\
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ job_name }}
  namespace: {{ namespace }}
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  template:
    metadata:
      name: {{ job_name }}
    spec:
      serviceAccountName: {{ service_account | default("default") }}
      restartPolicy: OnFailure
      containers:
        - name: ansible-runner
          image: quay.io/ansible/ansible-runner:latest
          env:
            - name: ANSIBLE_HOST_KEY_CHECKING
              value: "False"
          command:
            - /bin/bash
            - -c
            - |
              #!/bin/bash
              set -euo pipefail

              echo "Running idempotent job: {{ job_name }}"

              # Check if job has already completed successfully
              if [ -f /tmp/job-complete ]; then
                echo "Job already completed successfully"
                exit 0
              fi

              # Run ansible playbook or other idempotent tasks
              ansible-playbook -i localhost, /ansible/{{ playbook_name }}.yaml

              # Mark job as complete
              touch /tmp/job-complete
              echo "Job completed successfully"
          volumeMounts:
            - name: ansible-playbooks
              mountPath: /ansible
              readOnly: true
      volumes:
        - name: ansible-playbooks
          configMap:
            name: {{ job_name }}-playbooks
            defaultMode: 0755
"""