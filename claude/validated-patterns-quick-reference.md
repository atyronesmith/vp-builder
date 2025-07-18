# Validated Patterns Quick Reference

## Essential Commands

### Pattern Deployment
```bash
# Quick deployment
./pattern.sh make install

# With custom values
./pattern.sh make install VALUES_FILE=values-custom.yaml

# Deploy specific component
./pattern.sh make deploy COMPONENT=vault
```

### Pattern Validation
```bash
# Validate entire pattern
make validate-pattern PATTERN_DIR=.

# Validate specific parts
make lint-yaml PATTERN_DIR=.
make lint-shell PATTERN_DIR=.
```

### ArgoCD Operations
```bash
# Check application status
oc get applications -n openshift-gitops

# Sync application
argocd app sync <app-name>

# Get application details
argocd app get <app-name>

# Force refresh
argocd app sync <app-name> --force
```

## Key File Structure

```
pattern-name/
├── values-global.yaml        # Global configuration
├── values-hub.yaml          # Hub cluster values
├── values-region.yaml       # Edge cluster values
├── values-secret.yaml.template  # Secret template
├── pattern.sh               # Deployment script
├── Makefile                # Build automation
├── charts/
│   ├── hub/                # Hub applications
│   ├── region/             # Edge applications
│   └── all/                # Common applications
├── common/                 # Framework subtree
└── scripts/                # Helper scripts
```

## Common Values File Patterns

### Basic Global Values
```yaml
global:
  pattern: my-pattern
  namespace: my-pattern-ns
  domain: example.com
  clusterDomain: cluster.local
  
  git:
    provider: github
    account: my-org
    email: admin@example.com
    
main:
  clusterGroupName: hub
  
clusterGroup:
  name: hub
  isHubCluster: true
```

### Application Definition
```yaml
applications:
  myapp:
    name: myapp
    namespace: myapp-ns
    project: default
    path: charts/hub/myapp
    repoURL: https://github.com/my-org/my-pattern
    targetRevision: main
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
```

### ClusterGroup with Managed Clusters
```yaml
clusterGroup:
  name: hub
  isHubCluster: true
  
  managedClusterGroups:
    - name: region
      helmOverrides:
        - name: clusterGroup.isHubCluster
          value: false
        - name: global.clusterDomain
          value: region.example.com
```

## Secret Management

### Vault Integration
```yaml
# values-secret.yaml (local only)
secrets:
  - name: database-secret
    vaultPath: secret/data/mypattern/database
    fields:
      - name: username
        value: "admin"
      - name: password
        value: "secure-password"
```

### External Secrets Operator
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-secret-store
    kind: SecretStore
  target:
    name: app-secret
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: secret/data/myapp
        property: password
```

## Common Troubleshooting

### Application Not Syncing
```bash
# Check status
oc get application myapp -n openshift-gitops -o yaml

# Common fixes
argocd app sync myapp --force
argocd app refresh myapp
```

### Values Override Issues
```bash
# Debug values resolution
helm template . -f values-global.yaml -f values-hub.yaml

# Check for YAML syntax errors
yamllint values-global.yaml
```

### Cluster Connection Issues
```bash
# Verify cluster registration
oc get managedclusters

# Check cluster status
oc get managedclusteraddons -A
```

## Pattern Types and Templates

### AI/ML Pattern
```yaml
global:
  pattern: ai-ml-pattern
  
applications:
  jupyter:
    name: jupyter-notebook
    namespace: jupyter
    
  model-serving:
    name: seldon-core
    namespace: seldon-system
    
  data-pipeline:
    name: kubeflow-pipelines
    namespace: kubeflow
```

### Security Pattern
```yaml
applications:
  compliance:
    name: compliance-operator
    namespace: openshift-compliance
    
  security-scanning:
    name: stackrox
    namespace: stackrox
```

### Multi-Cloud Pattern
```yaml
clusterGroup:
  name: hub
  isHubCluster: true
  
  managedClusterGroups:
    - name: aws-region
      provider: aws
    - name: azure-region
      provider: azure
    - name: gcp-region
      provider: gcp
```

## Operator Integration

### Subscription Configuration
```yaml
clusterGroup:
  subscriptions:
    acm:
      name: advanced-cluster-management
      namespace: open-cluster-management
      channel: release-2.9
      
    gitops:
      name: openshift-gitops-operator
      namespace: openshift-operators
```

### Custom Resource Definitions
```yaml
applications:
  custom-operator:
    name: my-operator
    namespace: my-operator-system
    extraResources:
      - apiVersion: example.com/v1
        kind: MyCustomResource
        metadata:
          name: my-resource
        spec:
          replicas: 3
```

## Performance Tuning

### Resource Limits
```yaml
applications:
  myapp:
    resources:
      limits:
        cpu: "2"
        memory: "4Gi"
      requests:
        cpu: "100m"
        memory: "256Mi"
```

### Scaling Configuration
```yaml
applications:
  myapp:
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
```

## Monitoring Integration

### ServiceMonitor
```yaml
applications:
  myapp:
    monitoring:
      enabled: true
      serviceMonitor:
        enabled: true
        path: /metrics
        port: metrics
```

### Grafana Dashboard
```yaml
applications:
  grafana:
    dashboards:
      - name: myapp-dashboard
        configMap: myapp-dashboard
        namespace: grafana
```

## Useful Environment Variables

```bash
# Pattern deployment
export PATTERN_NAME=my-pattern
export CLUSTER_DOMAIN=apps.cluster.example.com
export GIT_ACCOUNT=my-org

# Vault configuration
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=<vault-token>

# ArgoCD CLI
export ARGOCD_SERVER=openshift-gitops-server-openshift-gitops.apps.cluster.example.com
export ARGOCD_AUTH_TOKEN=<argocd-token>
```

## Quick Validation Checklist

- [ ] Pattern repository forked and cloned
- [ ] values-secret.yaml created (not committed)
- [ ] Git URLs updated to fork
- [ ] Cluster meets minimum requirements
- [ ] OpenShift GitOps operator installed
- [ ] Storage class configured
- [ ] Image registry operational
- [ ] Network access to required repositories
- [ ] Secrets properly configured
- [ ] Pattern validation passes