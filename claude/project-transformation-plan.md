# Project Transformation Plan: Converting to Validated Patterns

Based on analysis of the multicloud-gitops base pattern and validated patterns documentation, this document provides a comprehensive plan for transforming projects into Red Hat Validated Patterns.

## Overview

This transformation plan converts existing projects into the multicloud-gitops validated pattern structure, enabling:
- **GitOps-based deployment** with ArgoCD
- **Multi-cluster management** with hub-and-spoke architecture
- **Automated secret management** with HashiCorp Vault
- **Standardized configuration** using hierarchical values files
- **Comprehensive testing** and validation frameworks

## Phase 1: Project Analysis and Pattern Detection

### 1.1 Analyze Source Project Structure
```bash
# Use the pattern converter to analyze project
./vp-convert analyze <project-path>

# Or run analysis manually
cd scripts/validated-pattern-converter
poetry run vp-convert analyze <project-path>
```

### 1.2 Pattern Detection Rules
The converter will automatically detect patterns based on:

#### AI/ML Patterns
- **Jupyter Notebooks**: `*.ipynb` files
- **ML Frameworks**: TensorFlow, PyTorch, Scikit-learn dependencies
- **Data Processing**: Spark, Kafka, Airflow configurations
- **Model Serving**: Seldon, KServe, MLflow deployments

#### Security Patterns
- **Compliance Tools**: OPA, Falco, Trivy configurations
- **Secret Management**: Vault, External Secrets Operator
- **RBAC**: Role-based access control configurations
- **Network Policies**: Kubernetes network security

#### Scaling Patterns
- **Horizontal Pod Autoscaling**: HPA configurations
- **Cluster Autoscaling**: Multi-region, multi-zone setups
- **Load Balancing**: Ingress controllers, service mesh

#### Data Processing Patterns
- **Databases**: PostgreSQL, MongoDB, Redis deployments
- **Streaming**: Kafka, Pulsar, NATS configurations
- **ETL Pipelines**: Apache Airflow, Prefect workflows

### 1.3 Confidence Scoring
Each pattern receives a confidence score (0.0-1.0) based on:
- **File presence** (0.3 weight)
- **Dependency analysis** (0.4 weight)
- **Configuration patterns** (0.3 weight)

## Phase 2: Repository Structure Transformation

### 2.1 Create Base Pattern Structure
```bash
# Create validated pattern structure
mkdir -p my-pattern/{charts/{all,hub,region},common,overrides,tests}
cd my-pattern

# Initialize git repository
git init
git remote add origin https://github.com/my-org/my-pattern.git
```

### 2.2 Directory Structure
```
my-pattern/
├── values-global.yaml           # Global pattern configuration
├── values-hub.yaml             # Hub cluster configuration
├── values-<cluster>.yaml       # Spoke cluster configurations
├── values-secret.yaml.template # Secret management template
├── pattern-metadata.yaml       # Pattern metadata
├── pattern.sh                  # Deployment script
├── Makefile                    # Build automation
├── ansible.cfg                 # Ansible configuration
├── charts/                     # Helm charts
│   ├── all/                    # Universal applications
│   ├── hub/                    # Hub-specific applications
│   └── region/                 # Regional applications
├── common/                     # Common framework (git subtree)
├── overrides/                  # Platform-specific overrides
├── tests/                      # Testing framework
└── docs/                       # Documentation
```

### 2.3 Add Common Framework
```bash
# Add common framework as git subtree
git subtree add --prefix=common \
  https://github.com/validatedpatterns/common.git main --squash
```

## Phase 3: Application Conversion

### 3.1 Convert Applications to Helm Charts
For each application component:

#### 3.1.1 Create Application Structure
```bash
# Create application directories
mkdir -p charts/all/myapp/{templates,charts}
cd charts/all/myapp
```

#### 3.1.2 Chart.yaml Template
```yaml
apiVersion: v2
name: myapp
description: My Application converted to Validated Pattern
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - pattern
  - myapp
```

#### 3.1.3 Values.yaml Template
```yaml
# Application-specific values
myapp:
  name: myapp
  namespace: myapp
  replicas: 2
  image:
    repository: quay.io/myorg/myapp
    tag: latest
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 8080
    
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 100m
      memory: 256Mi
      
  autoscaling:
    enabled: false
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

#### 3.1.4 Template Conversion
Convert existing Kubernetes manifests to Helm templates:

**Deployment Template**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  namespace: {{ .Values.myapp.namespace }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.myapp.replicas }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.myapp.image.repository }}:{{ .Values.myapp.image.tag }}"
        ports:
        - containerPort: {{ .Values.myapp.service.port }}
        resources:
          {{- toYaml .Values.myapp.resources | nindent 12 }}
        env:
        - name: CLUSTER_DOMAIN
          value: {{ .Values.global.localClusterDomain }}
        - name: PATTERN_NAME
          value: {{ .Values.global.pattern }}
```

**Service Template**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "myapp.fullname" . }}
  namespace: {{ .Values.myapp.namespace }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  type: {{ .Values.myapp.service.type }}
  ports:
  - port: {{ .Values.myapp.service.port }}
    targetPort: {{ .Values.myapp.service.port }}
    protocol: TCP
  selector:
    {{- include "myapp.selectorLabels" . | nindent 4 }}
```

**Route Template** (OpenShift):
```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: {{ include "myapp.fullname" . }}
  namespace: {{ .Values.myapp.namespace }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  host: myapp.{{ .Values.global.localClusterDomain }}
  to:
    kind: Service
    name: {{ include "myapp.fullname" . }}
  port:
    targetPort: {{ .Values.myapp.service.port }}
```

### 3.2 Helper Templates
Create `templates/_helpers.tpl`:
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "myapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "myapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "myapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "myapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Chart name and version
*/}}
{{- define "myapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}
```

## Phase 4: Configuration Setup

### 4.1 Global Configuration (values-global.yaml)
```yaml
global:
  pattern: my-pattern
  options:
    useCSV: false
    syncPolicy: Automatic
    installPlanApproval: Automatic
  
  # Git configuration
  git:
    provider: github
    account: my-org
    email: admin@example.com
    
  # Cluster configuration
  domain: example.com
  
main:
  clusterGroupName: hub
  multiSourceConfig:
    enabled: true
    clusterGroupChartVersion: "0.9.*"
```

### 4.2 Hub Configuration (values-hub.yaml)
```yaml
clusterGroup:
  name: hub
  isHubCluster: true
  
  namespaces:
    - open-cluster-management
    - vault
    - golang-external-secrets
    - myapp
    
  subscriptions:
    acm:
      name: advanced-cluster-management
      namespace: open-cluster-management
      channel: release-2.11
      
  projects:
    - hub
    - myapp
    
  applications:
    # Core infrastructure
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
      
    # Application
    myapp:
      name: myapp
      namespace: myapp
      project: myapp
      path: charts/all/myapp
      
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

### 4.3 Regional Configuration (values-region.yaml)
```yaml
clusterGroup:
  name: region
  isHubCluster: false
  
  namespaces:
    - myapp
    - golang-external-secrets
    
  projects:
    - myapp
    - eso
    
  applications:
    golang-external-secrets:
      name: golang-external-secrets
      namespace: golang-external-secrets
      project: eso
      chart: golang-external-secrets
      chartVersion: 0.1.*
      
    myapp:
      name: myapp
      namespace: myapp
      project: myapp
      path: charts/all/myapp
      overrides:
        - name: myapp.replicas
          value: 1  # Fewer replicas on spoke clusters
```

### 4.4 Pattern Metadata (pattern-metadata.yaml)
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
  languages:
    - yaml
    - helm
  industries:
    - general
```

## Phase 5: Secret Management

### 5.1 Secret Template (values-secret.yaml.template)
```yaml
version: "2.0"
backingStore: vault
# Uncomment one of the following lines to set a backend
# backingStore: vault 
# backingStore: kubernetes
# backingStore: none

secrets:
  - name: myapp-database
    vaultPath: secret/data/hub/myapp-db
    fields:
      - name: username
        ini_file: ~/.config/myapp/db.ini
        ini_key: database.username
      - name: password
        ini_file: ~/.config/myapp/db.ini
        ini_key: database.password
        
  - name: myapp-api-key
    vaultPath: secret/data/hub/myapp-api
    fields:
      - name: api-key
        ini_file: ~/.config/myapp/api.ini
        ini_key: api.key
        
  - name: myapp-tls
    vaultPath: secret/data/hub/myapp-tls
    fields:
      - name: tls.crt
        path: ~/.config/myapp/tls.crt
      - name: tls.key
        path: ~/.config/myapp/tls.key
```

### 5.2 External Secret Integration
Add to application templates:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-secret
  namespace: {{ .Values.myapp.namespace }}
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: myapp-secret
    creationPolicy: Owner
  data:
    - secretKey: database-username
      remoteRef:
        key: secret/data/hub/myapp-db
        property: username
    - secretKey: database-password
      remoteRef:
        key: secret/data/hub/myapp-db
        property: password
```

## Phase 6: Build and Deployment Automation

### 6.1 Makefile
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
```

### 6.2 Pattern Deployment Script
The `pattern.sh` script is copied from multicloud-gitops and provides:
- Containerized deployment using utility container
- Automatic podman version detection
- SSL certificate and kubeconfig mounting
- Environment variable propagation
- Disconnected environment support

## Phase 7: Testing and Validation

### 7.1 Test Structure
```bash
mkdir -p tests/interop
cd tests/interop
```

### 7.2 Test Configuration (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short
markers =
    hub: marks tests as hub cluster tests
    edge: marks tests as edge cluster tests
    smoke: marks tests as smoke tests
    integration: marks tests as integration tests
```

### 7.3 Test Cases (test_myapp.py)
```python
import pytest
import subprocess
import time

def test_myapp_deployment():
    """Test that myapp deployment is successful"""
    result = subprocess.run([
        'oc', 'get', 'deployment', 'myapp', '-n', 'myapp', 
        '-o', 'jsonpath={.status.readyReplicas}'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert int(result.stdout) > 0

def test_myapp_service():
    """Test that myapp service is accessible"""
    result = subprocess.run([
        'oc', 'get', 'service', 'myapp', '-n', 'myapp'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert 'myapp' in result.stdout

def test_myapp_route():
    """Test that myapp route is accessible"""
    result = subprocess.run([
        'oc', 'get', 'route', 'myapp', '-n', 'myapp', 
        '-o', 'jsonpath={.spec.host}'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert result.stdout.endswith('.com')

@pytest.mark.integration
def test_myapp_health_check():
    """Test application health endpoint"""
    # Get route host
    result = subprocess.run([
        'oc', 'get', 'route', 'myapp', '-n', 'myapp', 
        '-o', 'jsonpath={.spec.host}'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        host = result.stdout.strip()
        import requests
        response = requests.get(f"https://{host}/health")
        assert response.status_code == 200
```

## Phase 8: Documentation and Finalization

### 8.1 Pattern Documentation
Create comprehensive documentation:
- `README.md`: Installation and usage guide
- `docs/DEPLOYMENT.md`: Deployment procedures
- `docs/CUSTOMIZATION.md`: Customization options
- `docs/TROUBLESHOOTING.md`: Common issues and solutions

### 8.2 CI/CD Integration
Add GitHub Actions workflow:
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
      
      - name: Validate Helm Charts
        run: |
          helm lint charts/all/*
          
      - name: Validate Values Files
        run: |
          yamllint values-*.yaml
          
      - name: Test Pattern Structure
        run: |
          make validate-pattern
```

## Summary

This transformation plan provides a comprehensive approach to converting projects into Red Hat Validated Patterns following the multicloud-gitops base pattern. The plan covers:

1. **Project Analysis**: Automated pattern detection and confidence scoring
2. **Structure Transformation**: Converting to standard validated pattern layout
3. **Application Conversion**: Helm chart creation and templating
4. **Configuration Management**: Hierarchical values files and secret management
5. **Automation**: Build and deployment automation
6. **Testing**: Comprehensive validation and testing framework
7. **Documentation**: Complete pattern documentation

The resulting pattern will provide enterprise-grade deployment capabilities with GitOps automation, multi-cluster support, and integrated secret management.