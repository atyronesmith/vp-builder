# Pattern Detection Rules for Validated Patterns Transformation

This document defines the rules and algorithms used by the pattern converter to automatically detect and classify project patterns. Based on analysis of the validated pattern converter and multicloud-gitops base pattern.

## Overview

The pattern detection system uses a rule-based approach with confidence scoring to identify architectural patterns in source projects. Each pattern type has specific detection rules that analyze:
- **File patterns** and presence indicators
- **Dependencies** and framework usage
- **Configuration patterns** and deployment structures
- **Documentation** and metadata indicators

## Pattern Types and Detection Rules

### 1. AI/ML Pipeline Pattern

**Confidence Threshold**: 0.7  
**Primary Indicators**:

#### File-based Detection (Weight: 0.3)
```yaml
file_patterns:
  - pattern: "*.ipynb"
    confidence_boost: 0.4
    description: "Jupyter notebooks indicate ML experimentation"
    
  - pattern: "**/models/**"
    confidence_boost: 0.3
    description: "Model directories suggest ML model management"
    
  - pattern: "**/data/**"
    confidence_boost: 0.2
    description: "Data directories suggest data processing"
    
  - pattern: "**/notebooks/**"
    confidence_boost: 0.3
    description: "Notebook directories indicate ML workflow"
    
  - pattern: "requirements.txt"
    confidence_boost: 0.1
    description: "Python requirements file"
    
  - pattern: "Pipfile"
    confidence_boost: 0.1
    description: "Pipenv configuration"
    
  - pattern: "pyproject.toml"
    confidence_boost: 0.1
    description: "Modern Python project configuration"
```

#### Dependency-based Detection (Weight: 0.4)
```yaml
python_dependencies:
  - package: "tensorflow"
    confidence_boost: 0.8
    description: "TensorFlow ML framework"
    
  - package: "torch"
    confidence_boost: 0.8
    description: "PyTorch ML framework"
    
  - package: "scikit-learn"
    confidence_boost: 0.7
    description: "Scikit-learn ML library"
    
  - package: "pandas"
    confidence_boost: 0.5
    description: "Data manipulation library"
    
  - package: "numpy"
    confidence_boost: 0.4
    description: "Numerical computing library"
    
  - package: "jupyter"
    confidence_boost: 0.6
    description: "Jupyter notebook environment"
    
  - package: "mlflow"
    confidence_boost: 0.8
    description: "ML experiment tracking"
    
  - package: "kubeflow"
    confidence_boost: 0.9
    description: "Kubernetes-native ML workflows"
    
  - package: "seldon-core"
    confidence_boost: 0.8
    description: "Model serving platform"
    
  - package: "feast"
    confidence_boost: 0.7
    description: "Feature store"
```

#### Configuration-based Detection (Weight: 0.3)
```yaml
kubernetes_resources:
  - kind: "Notebook"
    confidence_boost: 0.6
    description: "Jupyter notebook CRD"
    
  - kind: "Pipeline"
    confidence_boost: 0.7
    description: "Kubeflow pipeline"
    
  - kind: "Experiment"
    confidence_boost: 0.6
    description: "ML experiment tracking"
    
  - kind: "SeldonDeployment"
    confidence_boost: 0.8
    description: "Seldon model deployment"
    
  - kind: "InferenceService"
    confidence_boost: 0.8
    description: "KServe model serving"
    
docker_images:
  - pattern: "tensorflow/tensorflow"
    confidence_boost: 0.6
    description: "TensorFlow official image"
    
  - pattern: "pytorch/pytorch"
    confidence_boost: 0.6
    description: "PyTorch official image"
    
  - pattern: "jupyter/.*"
    confidence_boost: 0.5
    description: "Jupyter ecosystem images"
```

### 2. Security Pattern

**Confidence Threshold**: 0.6  
**Primary Indicators**:

#### File-based Detection (Weight: 0.3)
```yaml
file_patterns:
  - pattern: "**/policies/**"
    confidence_boost: 0.5
    description: "Security policies directory"
    
  - pattern: "**/rbac/**"
    confidence_boost: 0.4
    description: "Role-based access control"
    
  - pattern: "**/*policy*.yaml"
    confidence_boost: 0.3
    description: "Policy configuration files"
    
  - pattern: "**/*security*.yaml"
    confidence_boost: 0.3
    description: "Security configuration files"
    
  - pattern: "**/.secrets/**"
    confidence_boost: 0.4
    description: "Secrets management"
    
  - pattern: "**/vault/**"
    confidence_boost: 0.5
    description: "Vault configuration"
```

#### Dependency-based Detection (Weight: 0.4)
```yaml
helm_charts:
  - chart: "hashicorp/vault"
    confidence_boost: 0.8
    description: "HashiCorp Vault"
    
  - chart: "external-secrets/external-secrets"
    confidence_boost: 0.7
    description: "External Secrets Operator"
    
  - chart: "falco/falco"
    confidence_boost: 0.8
    description: "Falco runtime security"
    
  - chart: "gatekeeper/gatekeeper"
    confidence_boost: 0.7
    description: "OPA Gatekeeper"
    
  - chart: "twistlock/twistlock"
    confidence_boost: 0.6
    description: "Twistlock security"
    
operators:
  - name: "compliance-operator"
    confidence_boost: 0.8
    description: "OpenShift compliance"
    
  - name: "rhacs-operator"
    confidence_boost: 0.7
    description: "Red Hat Advanced Cluster Security"
```

#### Configuration-based Detection (Weight: 0.3)
```yaml
kubernetes_resources:
  - kind: "NetworkPolicy"
    confidence_boost: 0.6
    description: "Network security policies"
    
  - kind: "PodSecurityPolicy"
    confidence_boost: 0.7
    description: "Pod security policies"
    
  - kind: "SecurityContextConstraints"
    confidence_boost: 0.6
    description: "OpenShift security contexts"
    
  - kind: "Role"
    confidence_boost: 0.4
    description: "RBAC roles"
    
  - kind: "ClusterRole"
    confidence_boost: 0.4
    description: "Cluster-level RBAC"
    
  - kind: "SecretStore"
    confidence_boost: 0.7
    description: "External secrets store"
    
  - kind: "ConstraintTemplate"
    confidence_boost: 0.8
    description: "OPA constraint templates"
```

### 3. Scaling Pattern

**Confidence Threshold**: 0.5  
**Primary Indicators**:

#### File-based Detection (Weight: 0.3)
```yaml
file_patterns:
  - pattern: "**/autoscaling/**"
    confidence_boost: 0.6
    description: "Autoscaling configurations"
    
  - pattern: "**/hpa/**"
    confidence_boost: 0.5
    description: "Horizontal Pod Autoscaler"
    
  - pattern: "**/cluster-autoscaler/**"
    confidence_boost: 0.7
    description: "Cluster autoscaler"
    
  - pattern: "**/regions/**"
    confidence_boost: 0.4
    description: "Multi-region configuration"
    
  - pattern: "**/zones/**"
    confidence_boost: 0.3
    description: "Multi-zone configuration"
```

#### Configuration-based Detection (Weight: 0.7)
```yaml
kubernetes_resources:
  - kind: "HorizontalPodAutoscaler"
    confidence_boost: 0.8
    description: "HPA for scaling"
    
  - kind: "VerticalPodAutoscaler"
    confidence_boost: 0.7
    description: "VPA for scaling"
    
  - kind: "PodDisruptionBudget"
    confidence_boost: 0.5
    description: "Availability during scaling"
    
  - kind: "Deployment"
    replicas_gt: 3
    confidence_boost: 0.4
    description: "High replica count"
    
  - kind: "StatefulSet"
    replicas_gt: 2
    confidence_boost: 0.4
    description: "Stateful scaling"
    
multi_cluster_indicators:
  - pattern: "managedClusterGroups"
    confidence_boost: 0.9
    description: "Multi-cluster management"
    
  - pattern: "clusterSelector"
    confidence_boost: 0.7
    description: "Cluster selection"
    
  - pattern: "placement"
    confidence_boost: 0.6
    description: "Workload placement"
```

### 4. Data Processing Pattern

**Confidence Threshold**: 0.6  
**Primary Indicators**:

#### File-based Detection (Weight: 0.3)
```yaml
file_patterns:
  - pattern: "**/etl/**"
    confidence_boost: 0.6
    description: "ETL pipeline"
    
  - pattern: "**/pipelines/**"
    confidence_boost: 0.5
    description: "Data pipelines"
    
  - pattern: "**/streaming/**"
    confidence_boost: 0.5
    description: "Stream processing"
    
  - pattern: "**/databases/**"
    confidence_boost: 0.4
    description: "Database configurations"
    
  - pattern: "**/*airflow*"
    confidence_boost: 0.7
    description: "Apache Airflow"
    
  - pattern: "**/*kafka*"
    confidence_boost: 0.6
    description: "Apache Kafka"
```

#### Dependency-based Detection (Weight: 0.4)
```yaml
helm_charts:
  - chart: "bitnami/postgresql"
    confidence_boost: 0.5
    description: "PostgreSQL database"
    
  - chart: "bitnami/mongodb"
    confidence_boost: 0.5
    description: "MongoDB database"
    
  - chart: "bitnami/redis"
    confidence_boost: 0.4
    description: "Redis cache"
    
  - chart: "confluentinc/cp-kafka"
    confidence_boost: 0.8
    description: "Apache Kafka"
    
  - chart: "elastic/elasticsearch"
    confidence_boost: 0.6
    description: "Elasticsearch"
    
  - chart: "apache/airflow"
    confidence_boost: 0.8
    description: "Apache Airflow"
    
  - chart: "apache/spark"
    confidence_boost: 0.7
    description: "Apache Spark"
```

#### Configuration-based Detection (Weight: 0.3)
```yaml
kubernetes_resources:
  - kind: "PersistentVolumeClaim"
    confidence_boost: 0.4
    description: "Persistent storage"
    
  - kind: "StatefulSet"
    confidence_boost: 0.6
    description: "Stateful applications"
    
  - kind: "CronJob"
    confidence_boost: 0.5
    description: "Scheduled data processing"
    
  - kind: "Job"
    confidence_boost: 0.4
    description: "Batch processing"
    
operators:
  - name: "postgresql-operator"
    confidence_boost: 0.7
    description: "PostgreSQL operator"
    
  - name: "mongodb-operator"
    confidence_boost: 0.7
    description: "MongoDB operator"
    
  - name: "strimzi-kafka-operator"
    confidence_boost: 0.8
    description: "Kafka operator"
```

### 5. MLOps Pattern

**Confidence Threshold**: 0.7  
**Primary Indicators**:

#### File-based Detection (Weight: 0.3)
```yaml
file_patterns:
  - pattern: "**/mlops/**"
    confidence_boost: 0.8
    description: "MLOps directory"
    
  - pattern: "**/experiments/**"
    confidence_boost: 0.6
    description: "ML experiments"
    
  - pattern: "**/model-registry/**"
    confidence_boost: 0.7
    description: "Model registry"
    
  - pattern: "**/.mlflow/**"
    confidence_boost: 0.7
    description: "MLflow tracking"
    
  - pattern: "**/workflows/**"
    confidence_boost: 0.5
    description: "ML workflows"
```

#### Dependency-based Detection (Weight: 0.4)
```yaml
python_dependencies:
  - package: "mlflow"
    confidence_boost: 0.9
    description: "MLflow platform"
    
  - package: "kubeflow"
    confidence_boost: 0.9
    description: "Kubeflow platform"
    
  - package: "dvc"
    confidence_boost: 0.8
    description: "Data Version Control"
    
  - package: "wandb"
    confidence_boost: 0.7
    description: "Weights & Biases"
    
  - package: "neptune"
    confidence_boost: 0.6
    description: "Neptune ML"
    
helm_charts:
  - chart: "kubeflow/kubeflow"
    confidence_boost: 0.9
    description: "Kubeflow platform"
    
  - chart: "mlflow/mlflow"
    confidence_boost: 0.8
    description: "MLflow server"
    
  - chart: "seldon/seldon-core"
    confidence_boost: 0.8
    description: "Seldon Core"
```

#### Configuration-based Detection (Weight: 0.3)
```yaml
kubernetes_resources:
  - kind: "Pipeline"
    confidence_boost: 0.8
    description: "Kubeflow pipeline"
    
  - kind: "Experiment"
    confidence_boost: 0.7
    description: "ML experiment"
    
  - kind: "Run"
    confidence_boost: 0.6
    description: "Pipeline run"
    
  - kind: "Model"
    confidence_boost: 0.7
    description: "ML model CRD"
    
  - kind: "ModelVersion"
    confidence_boost: 0.6
    description: "Model versioning"
```

## Detection Algorithm

### 1. Rule Processing
```python
def detect_pattern(project_path, pattern_type):
    confidence = 0.0
    
    # File-based detection
    file_score = analyze_file_patterns(project_path, pattern_type)
    confidence += file_score * 0.3
    
    # Dependency-based detection
    dep_score = analyze_dependencies(project_path, pattern_type)
    confidence += dep_score * 0.4
    
    # Configuration-based detection
    config_score = analyze_configurations(project_path, pattern_type)
    confidence += config_score * 0.3
    
    return min(confidence, 1.0)
```

### 2. Confidence Scoring
```python
def calculate_confidence(matches, total_rules):
    """Calculate confidence score based on rule matches"""
    if total_rules == 0:
        return 0.0
    
    # Weighted sum of matched rules
    weighted_score = sum(match.confidence_boost for match in matches)
    
    # Normalize by total possible score
    max_possible_score = sum(rule.confidence_boost for rule in total_rules)
    
    return min(weighted_score / max_possible_score, 1.0)
```

### 3. Pattern Ranking
```python
def rank_patterns(project_path):
    """Rank all patterns by confidence score"""
    pattern_scores = {}
    
    for pattern_type in PATTERN_TYPES:
        score = detect_pattern(project_path, pattern_type)
        if score >= pattern_type.threshold:
            pattern_scores[pattern_type.name] = score
    
    # Sort by confidence score (descending)
    return sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
```

## Usage in Pattern Converter

### 1. Analysis Command
```bash
# Analyze project patterns
vp-convert analyze /path/to/project

# Output example:
# Pattern Detection Results:
# - AI/ML Pipeline: 0.85 (High Confidence)
# - Security: 0.45 (Below Threshold)
# - Scaling: 0.60 (Medium Confidence)
# - Data Processing: 0.70 (High Confidence)
# - MLOps: 0.90 (High Confidence)
#
# Recommended Primary Pattern: MLOps (0.90)
# Recommended Secondary Pattern: AI/ML Pipeline (0.85)
```

### 2. Conversion Integration
```python
def convert_project(source_path, target_path):
    # Detect patterns
    patterns = rank_patterns(source_path)
    
    if not patterns:
        raise ValueError("No patterns detected with sufficient confidence")
    
    primary_pattern = patterns[0][0]
    
    # Apply pattern-specific transformations
    transformer = get_transformer(primary_pattern)
    transformer.transform(source_path, target_path)
    
    # Apply secondary pattern enhancements
    for pattern_name, confidence in patterns[1:]:
        if confidence > 0.6:
            enhancer = get_enhancer(pattern_name)
            enhancer.enhance(target_path)
```

## Customization and Extension

### 1. Adding New Pattern Types
```yaml
# custom-pattern.yaml
pattern_type: "custom-pattern"
confidence_threshold: 0.6
detection_rules:
  file_patterns:
    - pattern: "**/custom/**"
      confidence_boost: 0.5
      description: "Custom application directory"
  
  dependencies:
    - package: "custom-framework"
      confidence_boost: 0.8
      description: "Custom framework dependency"
  
  kubernetes_resources:
    - kind: "CustomResource"
      confidence_boost: 0.7
      description: "Custom resource definition"
```

### 2. Modifying Existing Rules
```yaml
# rule-overrides.yaml
pattern_modifications:
  ai_ml_pipeline:
    file_patterns:
      - pattern: "**/*.py"
        confidence_boost: 0.1
        description: "Python files (custom boost)"
    
    dependencies:
      - package: "tensorflow"
        confidence_boost: 0.9  # Increased from 0.8
        description: "TensorFlow (high priority)"
```

This pattern detection system provides a robust foundation for automatically identifying and classifying project patterns, enabling intelligent transformation to validated patterns with appropriate confidence levels and pattern-specific optimizations.