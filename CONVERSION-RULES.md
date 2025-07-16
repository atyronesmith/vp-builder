# Red Hat Validated Pattern Conversion Rules

## Overview
This document defines the rules and requirements for converting any project into a Red Hat Validated Pattern. These rules are based on the multicloud-gitops reference pattern and validated patterns framework.

## Prerequisites

### Required Repositories
1. **Common Framework** (must be cloned separately)
   - Repository: `https://github.com/validatedpatterns-docs/common.git`
   - Purpose: Provides shared Makefile, scripts, and Ansible utilities
   - Required for: Pattern utilities, deployment automation

2. **Reference Pattern** (for structure guidance)
   - Repository: `https://github.com/validatedpatterns/multicloud-gitops.git`
   - Purpose: Reference implementation for directory structure and configuration

### Required Tools
- OpenShift CLI (oc)
- Helm 3.x
- Git
- Make
- Ansible (for site.yaml execution)
- Python 3.x with PyYAML
- ShellCheck (for shell script validation)

## Directory Structure Rules

### Mandatory Directories
```
pattern-name/
├── ansible/              # Ansible automation
│   └── site.yaml        # Main Ansible playbook
├── charts/              # Helm charts for applications
│   ├── hub/            # Hub cluster applications
│   └── region/         # Edge/region cluster applications
├── common/             # Symlink to common framework (post-clone)
├── migrated-charts/    # Original application charts
├── overrides/          # Platform-specific overrides
├── scripts/            # Pattern-specific scripts
├── tests/              # Test configurations
│   └── interop/        # Interoperability tests
└── values-*.yaml       # Configuration files
```

### Mandatory Files

#### 1. ansible/site.yaml
```yaml
- hosts: localhost
  connection: local
  gather_facts: no
  vars:
    ansible_python_interpreter: "{{ ansible_playbook_python }}"
  tasks:
    - name: Check for rhvp.cluster_utils
      debug:
        msg: |
          This playbook requires rhvp.cluster_utils role.
          Install with: ansible-galaxy collection install rhvp.cluster_utils
```

#### 2. ansible.cfg
```ini
[defaults]
host_key_checking = False
interpreter_python = auto_silent
```

#### 3. pattern.sh
- Must be symlink to: `./common/scripts/pattern-util.sh`
- Created after common framework is cloned

#### 4. Makefile
```makefile
.PHONY: default
default: help

%:
	@if [ -f common/Makefile ]; then \
	  make -f common/Makefile $@; \
	else \
	  echo "ERROR: common/Makefile not found. Please clone the common repo first."; \
	fi
```

#### 5. pattern-metadata.yaml
```yaml
name: pattern-name
displayName: "Human Readable Pattern Name"
description: |
  Brief description of the pattern
gitOpsRepo: "https://github.com/organization/pattern-name"
gitOpsBranch: main
patternDocumentationUrl: "https://validatedpatterns.io/patterns/pattern-name/"
architectureReadmeUrl: "https://github.com/organization/pattern-name/blob/main/README.md"
```

## Configuration File Rules

### values-global.yaml
Must include:
1. Pattern metadata
2. Cluster group definitions
3. Namespace configurations
4. Subscription defaults
5. Application definitions with multiSourceConfig

Required structure:
```yaml
global:
  pattern: pattern-name
  targetRevision: main
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: 0.9.0

main:
  clusterGroupName: hub

clusterGroup:
  name: hub
  namespaces: []
  subscriptions: []
  applications: {}
```

### values-hub.yaml
Must include:
1. Cluster-specific configurations
2. Managed cluster definitions
3. Application references

### values-secret.yaml.template
Must include templates for:
1. Git credentials
2. Container registry credentials
3. Cloud provider credentials
4. Application-specific secrets

## Application Migration Rules

### Chart Structure
Each application chart must have:
```
charts/hub/appname/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── namespace.yaml
    ├── application.yaml
    └── kustomization.yaml
```

### ArgoCD Application Template
Must use multiSourceConfig format:
```yaml
{{- if .Values.clusterGroup.applications.appname.enabled }}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: appname
  namespace: openshift-gitops
spec:
  sources:
    - repoURL: {{ .Values.global.targetRepo }}
      targetRevision: {{ .Values.global.targetRevision }}
      ref: patternref
    - chart: {{ .Values.clusterGroup.applications.appname.chart }}
      repoURL: {{ .Values.clusterGroup.applications.appname.repoURL }}
      targetRevision: {{ .Values.clusterGroup.applications.appname.targetRevision }}
      helm:
        valueFiles:
          - $patternref/{{ .Values.clusterGroup.applications.appname.valuesFile }}
```

## Conversion Process Rules

### Phase 1: Structure Creation
1. Create base directory structure
2. Generate mandatory configuration files
3. Set up git repository

### Phase 2: Configuration
1. Populate values-global.yaml with pattern metadata
2. Define cluster groups in values-hub.yaml
3. Create secret templates

### Phase 3: Application Migration
1. Analyze existing Helm charts
2. Create wrapper charts in charts/hub/
3. Preserve original charts in migrated-charts/
4. Update values files with application references

### Phase 4: Integration
1. Clone common framework
2. Create pattern.sh symlink
3. Test Makefile functionality
4. Validate ansible configuration

### Phase 5: Platform Overrides
1. Create platform-specific overrides (AWS, Azure, GCP)
2. Document platform requirements
3. Test deployment variations

## Validation Rules

### Must Pass Checks
1. All mandatory files exist
2. Directory structure matches specification
3. YAML syntax is valid
4. Helm charts are valid
5. ArgoCD applications use multiSourceConfig
6. Pattern metadata is complete
7. All shell scripts pass ShellCheck validation

### Shell Script Validation

All shell scripts in the pattern must pass ShellCheck validation to ensure:
- Proper syntax and best practices
- Portability across different shells
- Security and robustness
- Prevention of common scripting errors

#### ShellCheck Requirements

1. **Installation**:
   ```bash
   # macOS
   brew install shellcheck

   # Linux
   apt-get install shellcheck  # Debian/Ubuntu
   yum install ShellCheck      # RHEL/CentOS

   # Or download from https://github.com/koalaman/shellcheck
   ```

2. **Validation Process**:
   ```bash
   # Validate all shell scripts in the pattern
   find . -type f \( -name "*.sh" -o -name "*.bash" \) -exec shellcheck {} \;

   # Validate scripts without .sh extension but with shell shebang
   find . -type f -exec sh -c 'file "$1" | grep -q "shell script"' _ {} \; -exec shellcheck {} \;
   ```

3. **Required Fixes**:
   - Fix all errors (SC1xxx)
   - Fix all warnings (SC2xxx)
   - Consider info messages (SC3xxx)
   - Address style suggestions where appropriate

4. **Common Issues to Fix**:
   ```bash
   # Quoting issues
   # Bad:  rm $file
   # Good: rm "$file"

   # Array handling
   # Bad:  files="$@"
   # Good: files=("$@")

   # Command substitution
   # Bad:  var=`command`
   # Good: var=$(command)

   # Test commands
   # Bad:  [ $var == "value" ]
   # Good: [ "$var" = "value" ]
   ```

5. **Exceptions**:
   If specific ShellCheck warnings must be ignored:
   ```bash
   # Disable specific check for a line
   # shellcheck disable=SC2086
   echo $var_with_intentional_word_splitting

   # Document why the exception is needed
   ```

6. **CI/CD Integration**:
   Add to GitHub Actions workflow:
   ```yaml
   - name: Run ShellCheck
     run: |
       find . -type f -name "*.sh" -exec shellcheck {} \;
   ```

### Common Pitfalls
1. Missing multiSourceConfig in applications
2. Incorrect chart references in values files
3. Missing namespaces in clusterGroup definitions
4. Hardcoded values instead of templated references
5. Missing platform overrides
6. Shell scripts with syntax errors or security issues

## Secret Management Rules

### External Secrets Operator
- Must be configured in values-secret.yaml
- Vault paths must follow pattern: `secret/data/hub/`
- Backend must be defined (vault, aws, azure, etc.)

### Git Credentials
- Must support both token and SSH key authentication
- Should reference from secret management system

## Documentation Requirements

### README.md
Must include:
1. Pattern overview
2. Prerequisites
3. Installation instructions
4. Architecture diagram
5. Troubleshooting guide

### Additional Documentation
1. PATTERN-CORRECTIONS.md - Common fixes
2. MIGRATION-NOTES.md - Migration specifics
3. Architecture decision records (ADRs)

## Testing Requirements

### Interoperability Tests
Location: `tests/interop/`
Must test:
1. Pattern installation
2. Application deployment
3. Multi-cluster scenarios
4. Secret synchronization

## Version Compatibility

### Framework Versions
- Pattern framework: 0.9+
- ClusterGroup chart: 0.9.0+
- Helm: 3.x
- OpenShift: 4.12+

### Operator Versions
- OpenShift GitOps: 1.8+
- Red Hat Advanced Cluster Management: 2.8+
- External Secrets Operator: 0.8+