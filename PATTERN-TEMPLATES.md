# Validated Pattern Templates

## Overview
This document contains templates for all common files needed in a validated pattern. Copy and customize these templates for your specific pattern.

## Core Configuration Templates

### Chart.yaml (Application Wrapper)
```yaml
apiVersion: v2
name: <app-name>
description: <App description>
version: 0.1.0
appVersion: "1.0"
dependencies: []
```

### ArgoCD Application Template
```yaml
{{- if .Values.clusterGroup.applications.<app-name>.enabled }}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ .Values.clusterGroup.applications.<app-name>.name }}
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "{{ .Values.clusterGroup.applications.<app-name>.syncWave | default 300 }}"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  sources:
    - repoURL: {{ .Values.global.targetRepo }}
      targetRevision: {{ .Values.global.targetRevision }}
      ref: patternref
    - chart: {{ .Values.clusterGroup.applications.<app-name>.chart }}
      repoURL: {{ .Values.clusterGroup.applications.<app-name>.repoURL }}
      targetRevision: {{ .Values.clusterGroup.applications.<app-name>.targetRevision }}
      helm:
        ignoreMissingValueFiles: true
        valueFiles:
          - $patternref/{{ .Values.clusterGroup.applications.<app-name>.valuesFile }}
        {{- if .Values.clusterGroup.applications.<app-name>.extraValues }}
        values: |
          {{- .Values.clusterGroup.applications.<app-name>.extraValues | nindent 10 }}
        {{- end }}
  destination:
    server: https://kubernetes.default.svc
    namespace: {{ .Values.clusterGroup.applications.<app-name>.namespace }}
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
  {{- if .Values.clusterGroup.applications.<app-name>.ignoreDifferences }}
  ignoreDifferences:
    {{- toYaml .Values.clusterGroup.applications.<app-name>.ignoreDifferences | nindent 4 }}
  {{- end }}
{{- end }}
```

### Namespace Template
```yaml
{{- if .Values.clusterGroup.applications.<app-name>.enabled }}
apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.clusterGroup.applications.<app-name>.namespace }}
  labels:
    argocd.argoproj.io/managed-by: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "100"
{{- end }}
```

### Kustomization Template
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yaml
  - application.yaml
  {{- if .Values.clusterGroup.applications.<app-name>.serviceMonitor }}
  - servicemonitor.yaml
  {{- end }}
  {{- if .Values.clusterGroup.applications.<app-name>.route }}
  - route.yaml
  {{- end }}
```

### ServiceMonitor Template (Optional)
```yaml
{{- if .Values.clusterGroup.applications.<app-name>.serviceMonitor }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .Values.clusterGroup.applications.<app-name>.name }}
  namespace: {{ .Values.clusterGroup.applications.<app-name>.namespace }}
  labels:
    app: {{ .Values.clusterGroup.applications.<app-name>.name }}
spec:
  selector:
    matchLabels:
      app: {{ .Values.clusterGroup.applications.<app-name>.name }}
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
{{- end }}
```

## Operator Subscription Templates

### Subscription Template
```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: {{ .name }}
  namespace: {{ .namespace }}
  annotations:
    argocd.argoproj.io/sync-wave: "200"
spec:
  channel: {{ .channel }}
  installPlanApproval: {{ .installPlanApproval | default "Automatic" }}
  name: {{ .name }}
  source: {{ .source | default "redhat-operators" }}
  sourceNamespace: openshift-marketplace
  {{- if .config }}
  config:
    {{- toYaml .config | nindent 4 }}
  {{- end }}
```

### OperatorGroup Template
```yaml
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: {{ .namespace }}-operator-group
  namespace: {{ .namespace }}
  annotations:
    argocd.argoproj.io/sync-wave: "190"
spec:
  targetNamespaces:
    - {{ .namespace }}
```

## Values File Templates

### values-hub.yaml Template
```yaml
clusterGroup:
  name: hub
  isHubCluster: true

  managedClusterGroups:
    - name: region
      hostedArgoSites:
        - name: perth
          domain: perth.example.com
          bearerKeyPath: secret/data/hub/cluster_perth/bearerToken
          caKeyPath: secret/data/hub/cluster_perth/caCert
      helmOverrides:
        - name: clusterGroup.insecureEdgeTerminationPolicy
          value: Redirect
        - name: clusterServerAddress
          value: https://api.region.example.com:6443

  applications:
    <app-name>:
      name: <app-name>
      namespace: <app-namespace>
      enabled: true
      chart: <chart-name>
      repoURL: <chart-repo-url>
      targetRevision: <chart-version>
      valuesFile: values-hub-<app-name>.yaml
      syncWave: 300
```

### values-region.yaml Template
```yaml
clusterGroup:
  name: region
  isHubCluster: false

  targetCluster: in-cluster

  applications:
    <edge-app>:
      name: <edge-app>
      namespace: <edge-namespace>
      enabled: true
      chart: <chart-name>
      repoURL: <chart-repo-url>
      targetRevision: <chart-version>
      valuesFile: values-region-<edge-app>.yaml
```

### Application Values Override Template
```yaml
# values-hub-<app-name>.yaml
global:
  hubClusterDomain: hub.example.com
  localClusterDomain: hub.example.com
  storageClass: ocs-storagecluster-ceph-rbd

<app-name>:
  # App-specific configuration
  replicas: 2
  image:
    repository: quay.io/org/<app-name>
    tag: latest
    pullPolicy: Always

  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"

  persistence:
    enabled: true
    size: 10Gi
    storageClass: "{{ .Values.global.storageClass }}"
```

## Script Templates

### deploy-models.sh Template
```bash
#!/bin/bash
set -euo pipefail

NAMESPACE="${1:-ai-models}"

echo "Deploying models to namespace: $NAMESPACE"

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    echo "ERROR: Not logged into OpenShift"
    exit 1
fi

# Create namespace if it doesn't exist
oc create namespace "$NAMESPACE" --dry-run=client -o yaml | oc apply -f -

# Deploy model configurations
for model in models/*.yaml; do
    if [[ -f "$model" ]]; then
        echo "Deploying $model..."
        oc apply -f "$model" -n "$NAMESPACE"
    fi
done

echo "Model deployment complete"
```

### validate-deployment.sh Template
```bash
#!/bin/bash
set -euo pipefail

echo "Validating pattern deployment..."

# Function to check if namespace exists
check_namespace() {
    local ns=$1
    if oc get namespace "$ns" &> /dev/null; then
        echo "✓ Namespace $ns exists"
        return 0
    else
        echo "✗ Namespace $ns missing"
        return 1
    fi
}

# Function to check if operator is ready
check_operator() {
    local name=$1
    local namespace=$2

    if oc get csv -n "$namespace" 2>/dev/null | grep -q "$name.*Succeeded"; then
        echo "✓ Operator $name is ready"
        return 0
    else
        echo "✗ Operator $name is not ready"
        return 1
    fi
}

# Function to check ArgoCD applications
check_argocd_app() {
    local app=$1

    if oc get application "$app" -n openshift-gitops &> /dev/null; then
        local health
        local sync
        health=$(oc get application "$app" -n openshift-gitops -o jsonpath='{.status.health.status}')
        sync=$(oc get application "$app" -n openshift-gitops -o jsonpath='{.status.sync.status}')

        if [[ "$health" == "Healthy" && "$sync" == "Synced" ]]; then
            echo "✓ ArgoCD app $app is healthy and synced"
            return 0
        else
            echo "✗ ArgoCD app $app - Health: $health, Sync: $sync"
            return 1
        fi
    else
        echo "✗ ArgoCD app $app not found"
        return 1
    fi
}

# Validation checks
ERRORS=0

# Check critical namespaces
for ns in openshift-gitops open-cluster-management external-secrets vault; do
    check_namespace "$ns" || ((ERRORS++))
done

# Check operators
check_operator "openshift-gitops-operator" "openshift-operators" || ((ERRORS++))
check_operator "advanced-cluster-management" "open-cluster-management" || ((ERRORS++))

# Check ArgoCD applications
for app in hub-applications hub-operators; do
    check_argocd_app "$app" || ((ERRORS++))
done

# Summary
echo "========================="
if [[ $ERRORS -eq 0 ]]; then
    echo "✓ All validation checks passed!"
    exit 0
else
    echo "✗ $ERRORS validation checks failed"
    exit 1
fi
```

## Test Templates

### tests/interop/test-pattern.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pattern-tests
  namespace: default
data:
  test-hub-connectivity.sh: |
    #!/bin/bash
    echo "Testing hub cluster connectivity..."
    oc cluster-info

  test-gitops.sh: |
    #!/bin/bash
    echo "Testing GitOps functionality..."
    oc get applications -n openshift-gitops

  test-secrets.sh: |
    #!/bin/bash
    echo "Testing secret management..."
    oc get externalsecrets -A
```

## Documentation Templates

### README.md Template
```markdown
# <Pattern Name>

## Overview
Brief description of what this pattern does and its use cases.

## Architecture
![Architecture Diagram](docs/images/architecture.png)

Describe the key components and how they interact.

## Prerequisites
- OpenShift Container Platform 4.12+
- Helm 3.x
- Git
- Make

### Cluster Sizing
| Node Type | Count | CPU | Memory | Storage |
|-----------|-------|-----|--------|---------|
| Control   | 3     | 4   | 16 GB  | 120 GB  |
| Worker    | 3     | 8   | 32 GB  | 200 GB  |

## Installation

### Quick Start
```bash
# Clone the pattern
git clone https://github.com/<org>/<pattern-name>.git
cd <pattern-name>

# Clone the common framework
git clone https://github.com/validatedpatterns-docs/common.git

# Create pattern symlink
ln -s ./common/scripts/pattern-util.sh pattern.sh

# Copy secret template
cp values-secret.yaml.template values-secret.yaml

# Edit values-secret.yaml with your credentials
vi values-secret.yaml

# Deploy the pattern
make install
```

### Configuration
Key configuration files:
- `values-global.yaml` - Global pattern configuration
- `values-hub.yaml` - Hub cluster specific settings
- `values-secret.yaml` - Sensitive credentials (not in git)

## Components
- **Component 1**: Description and purpose
- **Component 2**: Description and purpose
- **Component 3**: Description and purpose

## Validation
```bash
# Run validation script
./scripts/validate-deployment.sh
```

## Troubleshooting

### Common Issues
1. **Pattern won't install**
   - Check OpenShift version
   - Verify operator availability

2. **Applications not syncing**
   - Check ArgoCD status
   - Verify git credentials

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
This pattern is licensed under the Apache License 2.0.
```

### CONTRIBUTING.md Template
```markdown
# Contributing to <Pattern Name>

## How to Contribute
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Development Setup
```bash
# Clone your fork
git clone https://github.com/<your-username>/<pattern-name>.git

# Add upstream remote
git remote add upstream https://github.com/<org>/<pattern-name>.git

# Create feature branch
git checkout -b feature/my-feature
```

## Testing
- Test on OpenShift 4.12+
- Run validation scripts
- Check all applications deploy

## Code Style
- Use consistent YAML formatting
- Follow Helm best practices
- Document all changes
```

## Common Makefile Targets

```makefile
# Additional targets for pattern Makefile
.PHONY: validate
validate:
	@echo "Running pattern validation..."
	@./scripts/validate-deployment.sh

.PHONY: test
test:
	@echo "Running pattern tests..."
	@helm lint charts/hub/*/
	@yamllint -c .yamllint values-*.yaml

.PHONY: clean
clean:
	@echo "Cleaning up pattern..."
	@rm -f values-secret.yaml
	@rm -f pattern.sh
	@rm -rf common/
```

## GitHub Actions Workflow Template

### .github/workflows/validate.yml
```yaml
name: Validate Pattern

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup tools
        run: |
          pip install yamllint
          curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
          sudo mv linux-amd64/helm /usr/local/bin/
          # Install ShellCheck
          sudo apt-get update
          sudo apt-get install -y shellcheck

      - name: Validate YAML
        run: yamllint -c .yamllint .

      - name: Validate Helm Charts
        run: |
          for chart in charts/hub/*/; do
            if [[ -d "$chart" ]]; then
              helm lint "$chart"
            fi
          done

      - name: Validate Shell Scripts
        run: |
          echo "Running ShellCheck on all shell scripts..."
          find . -type f -name "*.sh" -print0 | xargs -0 shellcheck

          # Also check scripts without .sh extension but with shell shebang
          find . -type f ! -name "*.sh" -exec sh -c '
            for file; do
              if head -n1 "$file" | grep -qE "^#!.*/(ba)?sh"; then
                echo "Checking $file"
                shellcheck "$file"
              fi
            done
          ' sh {} +
```

### .shellcheckrc Template
Create `.shellcheckrc` in the pattern root:
```bash
# ShellCheck configuration for validated patterns

# Set shell to bash by default
shell=bash

# Disable specific warnings if needed (with justification)
# disable=SC2034  # Example: Unused variables that are exported

# Enable optional checks
enable=quote-safe-variables
enable=require-variable-braces
```