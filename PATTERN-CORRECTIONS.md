# Validated Pattern Corrections Guide

## Overview
This document captures common issues encountered during pattern conversion and their solutions. These corrections were discovered while converting projects to the validated patterns framework.

## Critical Missing Components

### 1. Ansible Configuration (MANDATORY)
**Issue**: Pattern missing ansible/site.yaml and ansible.cfg
**Impact**: Pattern framework cannot execute imperative tasks
**Solution**:
```bash
# Create ansible directory
mkdir -p ansible

# Create ansible.cfg
cat > ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
interpreter_python = auto_silent
EOF

# Create ansible/site.yaml with rhvp.cluster_utils check
```

### 2. Common Framework Integration
**Issue**: Missing pattern.sh symlink and common framework reference
**Impact**: Make commands fail, pattern utilities unavailable
**Solution**:
```bash
# Clone common framework
git clone https://github.com/validatedpatterns-docs/common.git

# Create symlink
ln -s ./common/scripts/pattern-util.sh pattern.sh
chmod +x pattern.sh
```

### 3. MultiSourceConfig for ArgoCD Applications
**Issue**: Applications using old single-source format
**Impact**: Pattern framework 0.9+ requires multiSourceConfig
**Solution**:
```yaml
# In values-global.yaml
global:
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: 0.9.0

# In application templates - use sources (plural) not source
spec:
  sources:
    - repoURL: {{ .Values.global.targetRepo }}
      targetRevision: {{ .Values.global.targetRevision }}
      ref: patternref
    - chart: {{ chart }}
      repoURL: {{ repoURL }}
      helm:
        valueFiles:
          - $patternref/{{ valuesFile }}
```

## Common Configuration Errors

### 1. Incorrect Makefile
**Issue**: Makefile contains actual targets instead of delegating to common
**Impact**: Pattern utilities not available, inconsistent behavior
**Correct Makefile**:
```makefile
.PHONY: default
default: help

%:
	@if [ -f common/Makefile ]; then \
		make -f common/Makefile $@; \
	else \
		echo "ERROR: common/Makefile not found."; \
		exit 1; \
	fi
```

### 2. Missing Overrides Directory
**Issue**: No platform-specific overrides
**Impact**: Cannot deploy to different cloud providers
**Solution**:
```bash
mkdir -p overrides
# Create platform files: values-AWS.yaml, values-Azure.yaml, values-GCP.yaml
```

### 3. Incorrect Pattern Metadata Structure
**Issue**: Using descriptive format instead of validated patterns format
**Impact**: Pattern not recognized by validatedpatterns.io
**Correct Format**:
```yaml
name: pattern-name
displayName: "Human Readable Name"
description: |
  Multi-line description
gitOpsRepo: "https://github.com/org/pattern"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/pattern/"
architectureReadmeUrl: "https://github.com/org/pattern/blob/main/README.md"
organizations:
  - redhat
  - validatedpatterns
```

## Application Migration Pitfalls

### 1. Direct Chart References
**Issue**: Referencing original charts directly in values files
**Impact**: No GitOps control, missing pattern integration
**Solution**: Create wrapper charts in charts/hub/ that deploy via ArgoCD

### 2. Missing Namespace Definitions
**Issue**: Applications reference namespaces not defined in clusterGroup
**Impact**: Namespaces not created, applications fail to deploy
**Solution**:
```yaml
clusterGroup:
  namespaces:
    - application-namespace
    - another-namespace
```

### 3. Hardcoded Values
**Issue**: Hardcoded cluster URLs, image registries, etc.
**Impact**: Pattern not portable across environments
**Solution**: Use templated values from global and clusterGroup sections

## Secret Management Issues

### 1. Secrets in Git
**Issue**: Actual secrets committed to repository
**Impact**: Security vulnerability
**Solution**:
- Use values-secret.yaml.template
- Add values-secret.yaml to .gitignore
- Use External Secrets Operator

### 2. Incorrect Vault Paths
**Issue**: Vault paths don't follow pattern convention
**Impact**: Secrets not found
**Correct Path Format**:
```yaml
vaultPaths:
  - name: hub
    path: secret/data/hub  # Note: data/ is required for KV v2
```

## Operator Subscription Problems

### 1. Missing OperatorGroup
**Issue**: Subscription created without OperatorGroup
**Impact**: Operator installation fails
**Solution**: Always create OperatorGroup before Subscription

### 2. Incorrect Sync Waves
**Issue**: Applications deploying before operators ready
**Impact**: Application failures
**Correct Order**:
```yaml
# Namespaces: wave 100
# OperatorGroups: wave 190
# Subscriptions: wave 200
# Applications: wave 300+
```

## Values File Mistakes

### 1. Missing Global Section
**Issue**: No global configuration section
**Impact**: Pattern framework cannot function
**Required Global Fields**:
```yaml
global:
  pattern: pattern-name
  targetRevision: main
  options:
    useCSV: false
    syncPolicy: Automatic
```

### 2. Incomplete Application Definitions
**Issue**: Missing required fields in application definitions
**Impact**: ArgoCD cannot deploy applications
**Required Fields**:
```yaml
applications:
  appname:
    name: appname
    namespace: target-namespace
    enabled: true
    chart: chart-name
    repoURL: https://charts.example.com
    targetRevision: 1.0.0
    valuesFile: values-hub-appname.yaml
```

## Testing and Validation Errors

### 1. No Validation Scripts
**Issue**: No way to verify deployment success
**Impact**: Silent failures, debugging difficulties
**Solution**: Create scripts/validate-deployment.sh

### 2. Missing Test Configurations
**Issue**: Empty tests/interop directory
**Impact**: Cannot run pattern tests
**Solution**: Add test configurations and scripts

## Documentation Gaps

### 1. No Architecture Diagram
**Issue**: Missing visual representation
**Impact**: Difficult to understand pattern
**Solution**: Create architecture diagram in docs/images/

### 2. Incomplete README
**Issue**: Missing installation steps, prerequisites
**Impact**: Users cannot deploy pattern
**Required Sections**:
- Overview
- Prerequisites
- Architecture
- Installation
- Configuration
- Troubleshooting

## Troubleshooting Techniques

### Check Pattern Structure
```bash
# Verify all required files exist
for file in ansible/site.yaml ansible.cfg pattern.sh Makefile \
            pattern-metadata.yaml values-global.yaml values-hub.yaml; do
    [ -f "$file" ] && echo "✓ $file" || echo "✗ $file MISSING"
done
```

### Validate YAML Syntax
```bash
# Install yamllint
pip install yamllint

# Check all YAML files
find . -name "*.yaml" -o -name "*.yml" | xargs yamllint
```

### Test Helm Charts
```bash
# Lint all charts
for chart in charts/hub/*/; do
    helm lint "$chart"
done

# Dry run render
helm template test charts/hub/*/ --values values-global.yaml
```

### Debug ArgoCD Applications
```bash
# Check application status
oc get applications -n openshift-gitops

# Get sync status
oc get application <app-name> -n openshift-gitops -o yaml

# Check events
oc describe application <app-name> -n openshift-gitops
```

## Prevention Checklist

Before considering pattern complete:
- [ ] All mandatory files present
- [ ] Common framework integrated
- [ ] MultiSourceConfig enabled
- [ ] All applications have wrapper charts
- [ ] Platform overrides created
- [ ] Secrets template provided
- [ ] Validation scripts working
- [ ] Documentation complete
- [ ] YAML syntax valid
- [ ] Helm charts lint clean
- [ ] Shell scripts pass ShellCheck

## Common Error Messages and Solutions

### "common/Makefile not found"
Clone the common framework repository

### "Application is OutOfSync"
Check multiSourceConfig is enabled and chart paths are correct

### "Namespace not found"
Add namespace to clusterGroup.namespaces in values file

### "CSV not found"
Check operator subscription channel and source

### "Secret not found"
Verify External Secrets Operator is installed and vault path is correct

### ShellCheck Errors

Common ShellCheck errors and fixes:

#### SC2086: Double quote to prevent globbing
```bash
# Bad
echo $var

# Good
echo "$var"
```

#### SC2046: Quote to prevent word splitting
```bash
# Bad
rm $(find . -name "*.tmp")

# Good
find . -name "*.tmp" -exec rm {} \;
# Or
rm "$(find . -name "*.tmp")"
```

#### SC1091: Not following sourced file
```bash
# Add directive if source is dynamic
# shellcheck source=/dev/null
source "$CONFIG_FILE"
```

#### SC2181: Check exit code directly
```bash
# Bad
command
if [ $? -eq 0 ]; then

# Good
if command; then
```

## References
- [Validated Patterns Documentation](https://validatedpatterns.io)
- [MultiCloud GitOps Pattern](https://github.com/validatedpatterns/multicloud-gitops)
- [Common Framework](https://github.com/validatedpatterns-docs/common)
- [ShellCheck Wiki](https://www.shellcheck.net/wiki/)