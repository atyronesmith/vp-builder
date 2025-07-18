# Validated Patterns Implementation Guide

This comprehensive guide provides step-by-step instructions for implementing validated patterns transformations using the AWS LLMD repository tools and the multicloud-gitops base pattern.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Pattern Converter Usage](#pattern-converter-usage)
4. [Manual Transformation Process](#manual-transformation-process)
5. [Advanced Configuration](#advanced-configuration)
6. [Testing and Validation](#testing-and-validation)
7. [Deployment and Operations](#deployment-and-operations)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- **OpenShift CLI (oc)** - v4.12+
- **Helm** - v3.10+
- **Git** - v2.30+
- **Podman** - v4.3.0+
- **Python** - v3.9+
- **Poetry** - v1.4+
- **Make** - GNU Make 4.0+

### Required Access
- **OpenShift Cluster** - Cluster admin privileges
- **GitHub Account** - Repository creation and management
- **Container Registry** - Quay.io or equivalent
- **DNS Domain** - For application routes

### Cluster Requirements
- **OpenShift Container Platform** - v4.16-4.18
- **Minimum Resources**: 8 CPU cores, 16GB RAM
- **Storage**: Dynamic StorageClass configured
- **Network**: Access to external registries and GitHub

## Environment Setup

### 1. Clone the AWS LLMD Repository
```bash
git clone https://github.com/validatedpatterns/aws-llmd.git
cd aws-llmd
```

### 2. Setup Pattern Converter
```bash
cd scripts/validated-pattern-converter
poetry install
poetry shell
```

### 3. Verify Dependencies
```bash
# Check all required tools
make install-tools

# Verify OpenShift connection
oc cluster-info

# Test container runtime
podman --version
```

### 4. Configure Environment Variables
```bash
# Set required environment variables
export PATTERN_NAME="my-pattern"
export PATTERN_ORG="my-org"
export CLUSTER_DOMAIN="apps.cluster.example.com"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# Optional: For disconnected environments
export PATTERN_DISCONNECTED_HOME="registry.example.com/patterns"
```

## Pattern Converter Usage

### 1. Analyze Source Project
```bash
# Basic analysis
vp-convert analyze /path/to/source/project

# Detailed analysis with output
vp-convert analyze /path/to/source/project --detailed --output analysis.json

# Example output:
# Pattern Detection Results:
# - AI/ML Pipeline: 0.85 (High Confidence)
# - Security: 0.45 (Below Threshold)
# - Data Processing: 0.70 (High Confidence)
# - MLOps: 0.90 (High Confidence)
#
# Recommended Primary Pattern: MLOps (0.90)
# Files analyzed: 127
# Helm charts found: 3
# Kubernetes resources: 15
```

### 2. Generate Pattern Structure
```bash
# Convert project to validated pattern
vp-convert generate \
  --source /path/to/source/project \
  --target /path/to/target/pattern \
  --pattern-name my-pattern \
  --organization my-org \
  --primary-pattern mlops

# With additional options
vp-convert generate \
  --source /path/to/source/project \
  --target /path/to/target/pattern \
  --pattern-name my-pattern \
  --organization my-org \
  --primary-pattern mlops \
  --git-url https://github.com/my-org/my-pattern.git \
  --cluster-domain apps.cluster.example.com \
  --enable-vault \
  --enable-acm
```

### 3. Validate Generated Pattern
```bash
# Validate pattern structure
vp-convert validate /path/to/target/pattern

# Validate with specific checks
vp-convert validate /path/to/target/pattern \
  --check-helm-charts \
  --check-values-files \
  --check-secrets \
  --check-common-integration
```

## Manual Transformation Process

### 1. Initialize Pattern Repository
```bash
# Create pattern repository structure
mkdir -p my-pattern/{charts/{all,hub,region},common,overrides,tests}
cd my-pattern

# Initialize git repository
git init
git remote add origin https://github.com/my-org/my-pattern.git

# Add common framework
git subtree add --prefix=common \
  https://github.com/validatedpatterns/common.git main --squash
```

### 2. Create Core Configuration Files

#### Global Configuration (values-global.yaml)
```yaml
global:
  pattern: my-pattern
  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic
  git:
    provider: github
    account: my-org
    email: admin@example.com
  domain: example.com
  
main:
  clusterGroupName: hub
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: "0.9.*"
```

#### Hub Configuration (values-hub.yaml)
```yaml
clusterGroup:
  name: hub
  isHubCluster: true
  namespaces:
    - open-cluster-management
    - vault
    - golang-external-secrets
    - my-app
  subscriptions:
    acm:
      name: advanced-cluster-management
      namespace: open-cluster-management
      channel: release-2.11
  projects:
    - hub
    - my-app
  applications:
    acm:
      name: acm
      namespace: open-cluster-management
      project: hub
      chart: acm
      chartVersion: 0.1.*
    vault:
      name: vault
      namespace: vault
      project: hub
      chart: hashicorp-vault
      chartVersion: 0.1.*
    golang-external-secrets:
      name: golang-external-secrets
      namespace: golang-external-secrets
      project: hub
      chart: golang-external-secrets
      chartVersion: 0.1.*
    my-app:
      name: my-app
      namespace: my-app
      project: my-app
      path: charts/all/my-app
```

#### Pattern Metadata (pattern-metadata.yaml)
```yaml
apiVersion: gitops.hybrid-cloud-patterns.io/v1
kind: Pattern
metadata:
  name: my-pattern
spec:
  clusterGroupName: hub
  gitSpec:
    originRepo: https://github.com/my-org/my-pattern
    targetRevision: main
  multiSourceConfig:
    enabled: true
  tier: community
  supportLevel: community
  description: "My application converted to Validated Pattern"
  categories:
    - application
  industries:
    - general
```

### 3. Create Application Helm Charts

#### Application Chart Structure
```bash
mkdir -p charts/all/my-app/{templates,charts}
cd charts/all/my-app
```

#### Chart.yaml
```yaml
apiVersion: v2
name: my-app
description: My Application Helm Chart
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - pattern
  - my-app
```

#### Application Templates
Create templates for Deployment, Service, Route, ConfigMap, and Secrets:

**templates/deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  namespace: {{ .Values.global.pattern }}-{{ .Values.myapp.namespace }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.myapp.replicas }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.myapp.image.repository }}:{{ .Values.myapp.image.tag }}"
        ports:
        - containerPort: {{ .Values.myapp.service.port }}
        env:
        - name: CLUSTER_DOMAIN
          value: {{ .Values.global.localClusterDomain }}
        - name: PATTERN_NAME
          value: {{ .Values.global.pattern }}
        resources:
          {{- toYaml .Values.myapp.resources | nindent 12 }}
        livenessProbe:
          httpGet:
            path: /health
            port: {{ .Values.myapp.service.port }}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: {{ .Values.myapp.service.port }}
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. Configure Secret Management

#### Secret Template (values-secret.yaml.template)
```yaml
version: "2.0"
backingStore: vault

secrets:
  - name: my-app-database
    vaultPath: secret/data/hub/my-app-db
    fields:
      - name: username
        ini_file: ~/.config/my-app/db.ini
        ini_key: database.username
      - name: password
        ini_file: ~/.config/my-app/db.ini
        ini_key: database.password
        
  - name: my-app-api-key
    vaultPath: secret/data/hub/my-app-api
    fields:
      - name: api-key
        ini_file: ~/.config/my-app/api.ini
        ini_key: api.key
```

#### Create Local Secrets File
```bash
# Create local secrets file (never commit!)
cp values-secret.yaml.template ~/values-secret-my-pattern.yaml

# Edit with real values
vim ~/values-secret-my-pattern.yaml
```

### 5. Setup Build Automation

#### Makefile
```makefile
.PHONY: default
default: help

.PHONY: help
help:
	@make -f common/Makefile MAKEFILE_LIST="Makefile common/Makefile" help

%:
	make -f common/Makefile $*

.PHONY: install
install: operator-deploy post-install
	@echo "My Pattern installed successfully"

.PHONY: post-install
post-install:
	make load-secrets
	@echo "Post-install tasks completed"

.PHONY: test
test:
	@make -f common/Makefile PATTERN_OPTS="-f values-global.yaml -f values-hub.yaml" test

.PHONY: validate
validate:
	@make -f common/Makefile validate-pattern

.PHONY: clean
clean:
	@make -f common/Makefile clean
```

#### Copy Deployment Script
```bash
# Copy pattern.sh from multicloud-gitops
cp ../multicloud-gitops/pattern.sh .
chmod +x pattern.sh
```

## Advanced Configuration

### 1. Multi-Cluster Setup

#### Regional Configuration (values-region.yaml)
```yaml
clusterGroup:
  name: region
  isHubCluster: false
  namespaces:
    - my-app
    - golang-external-secrets
  projects:
    - my-app
    - eso
  applications:
    golang-external-secrets:
      name: golang-external-secrets
      namespace: golang-external-secrets
      project: eso
      chart: golang-external-secrets
      chartVersion: 0.1.*
    my-app:
      name: my-app
      namespace: my-app
      project: my-app
      path: charts/all/my-app
      overrides:
        - name: myapp.replicas
          value: 1
```

#### Update Hub Configuration for Managed Clusters
```yaml
# Add to values-hub.yaml
managedClusterGroups:
  region:
    name: region
    acmlabels:
      - name: clusterGroup
        value: region
    helmOverrides:
      - name: clusterGroup.isHubCluster
        value: false
```

### 2. Platform-Specific Overrides

#### AWS Override (overrides/values-aws.yaml)
```yaml
global:
  clusterPlatform: aws
  
myapp:
  storage:
    storageClass: gp2
  ingress:
    class: alb
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
```

#### Azure Override (overrides/values-azure.yaml)
```yaml
global:
  clusterPlatform: azure
  
myapp:
  storage:
    storageClass: managed-premium
  ingress:
    class: azure-application-gateway
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
```

### 3. Custom Operators Integration

#### Add Operator Subscription
```yaml
# Add to values-hub.yaml subscriptions section
subscriptions:
  my-operator:
    name: my-operator
    namespace: my-operator-system
    channel: stable
    source: community-operators
    sourceNamespace: openshift-marketplace
```

#### Create Operator Configuration
```yaml
# charts/hub/my-operator/templates/subscription.yaml
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: {{ .Values.subscription.name }}
  namespace: {{ .Values.subscription.namespace }}
spec:
  channel: {{ .Values.subscription.channel }}
  name: {{ .Values.subscription.name }}
  source: {{ .Values.subscription.source }}
  sourceNamespace: {{ .Values.subscription.sourceNamespace }}
```

## Testing and Validation

### 1. Pre-deployment Testing
```bash
# Validate pattern structure
make validate-pattern

# Test Helm charts
helm lint charts/all/*

# Validate values files
yamllint values-*.yaml

# Test template rendering
make show
```

### 2. Create Test Suite
```bash
mkdir -p tests/interop
cd tests/interop
```

#### Test Configuration (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short
markers =
    hub: marks tests as hub cluster tests
    edge: marks tests as edge cluster tests
    smoke: marks tests as smoke tests
```

#### Application Tests (test_my_app.py)
```python
import pytest
import subprocess
import time
import requests

def test_my_app_deployment():
    """Test that my-app deployment is successful"""
    result = subprocess.run([
        'oc', 'get', 'deployment', 'my-app', '-n', 'my-app',
        '-o', 'jsonpath={.status.readyReplicas}'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert int(result.stdout) > 0

def test_my_app_service():
    """Test that my-app service is accessible"""
    result = subprocess.run([
        'oc', 'get', 'service', 'my-app', '-n', 'my-app'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert 'my-app' in result.stdout

@pytest.mark.integration
def test_my_app_health():
    """Test application health endpoint"""
    result = subprocess.run([
        'oc', 'get', 'route', 'my-app', '-n', 'my-app',
        '-o', 'jsonpath={.spec.host}'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        host = result.stdout.strip()
        response = requests.get(f"https://{host}/health")
        assert response.status_code == 200

def test_secrets_loaded():
    """Test that secrets are properly loaded"""
    result = subprocess.run([
        'oc', 'get', 'secret', 'my-app-secret', '-n', 'my-app'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert 'my-app-secret' in result.stdout
```

### 3. Run Tests
```bash
# Run smoke tests
make test

# Run specific test suite
pytest tests/interop/test_my_app.py -v

# Run integration tests
pytest tests/interop/ -m integration
```

## Deployment and Operations

### 1. Initial Deployment
```bash
# Deploy pattern using operator
./pattern.sh make install

# Or deploy manually
make operator-deploy
make load-secrets
```

### 2. Monitor Deployment
```bash
# Check ArgoCD applications
oc get applications -n openshift-gitops

# Check application sync status
oc get applications -n openshift-gitops -o wide

# Check specific application
oc describe application my-app -n openshift-gitops
```

### 3. Access Applications
```bash
# Get application route
oc get route my-app -n my-app

# Test application
curl -k https://$(oc get route my-app -n my-app -o jsonpath='{.spec.host}')/health
```

### 4. Scaling Operations
```bash
# Scale application replicas
oc patch deployment my-app -n my-app -p '{"spec":{"replicas":5}}'

# Enable autoscaling
oc autoscale deployment my-app -n my-app --min=2 --max=10 --cpu-percent=70
```

### 5. Update Operations
```bash
# Update application image
oc set image deployment/my-app my-app=quay.io/my-org/my-app:v1.1.0 -n my-app

# Update pattern configuration
git add values-hub.yaml
git commit -m "Update configuration"
git push origin main
# ArgoCD will automatically sync changes
```

## Troubleshooting

### Common Issues and Solutions

#### 1. ArgoCD Application Not Syncing
```bash
# Check application status
oc get application my-app -n openshift-gitops -o yaml

# Force sync
oc patch application my-app -n openshift-gitops \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{"force":true}}}}}'

# Check ArgoCD logs
oc logs -f deployment/argocd-application-controller -n openshift-gitops
```

#### 2. Secret Loading Failures
```bash
# Check vault status
oc get pods -n vault

# Check external secrets operator
oc get pods -n golang-external-secrets

# Check secret synchronization
oc get externalsecrets -A
oc describe externalsecret my-app-secret -n my-app
```

#### 3. Helm Chart Issues
```bash
# Validate chart syntax
helm lint charts/all/my-app

# Test template rendering
helm template my-app charts/all/my-app \
  -f values-global.yaml \
  -f values-hub.yaml

# Check chart dependencies
helm dependency update charts/all/my-app
```

#### 4. Container Image Issues
```bash
# Check image pull secrets
oc get secret -n my-app | grep pull

# Check pod events
oc describe pod <pod-name> -n my-app

# Test image accessibility
podman pull quay.io/my-org/my-app:latest
```

#### 5. Network Issues
```bash
# Check network policies
oc get networkpolicy -n my-app

# Test service connectivity
oc exec -it <pod-name> -n my-app -- curl my-app:8080/health

# Check ingress/route configuration
oc get route my-app -n my-app -o yaml
```

### Debug Commands
```bash
# Pattern validation
make validate-pattern

# Show rendered templates
make show

# Check cluster health
make argo-healthcheck

# Run pattern tests
make test

# Check secret backend
make check-secret-backend

# Validate prerequisites
make validate-prereq
```

### Performance Optimization
```bash
# Monitor resource usage
oc top pods -n my-app
oc top nodes

# Check HPA status
oc get hpa -n my-app

# Review resource limits
oc describe deployment my-app -n my-app
```

This implementation guide provides comprehensive instructions for successfully transforming projects into validated patterns using the AWS LLMD repository tools and the multicloud-gitops base pattern framework.