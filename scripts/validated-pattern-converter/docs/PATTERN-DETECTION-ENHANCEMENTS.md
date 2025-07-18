# Pattern Detection Enhancements

## Overview

The validated-pattern-converter has been enhanced with a sophisticated rule-based pattern detection engine inspired by the helm-analyzer project. This provides more flexible, maintainable, and accurate pattern detection capabilities.

## Key Enhancements

### 1. Rule-Based Pattern Detection Engine

#### Previous Approach
- Hard-coded pattern detection methods
- Simple keyword matching
- Binary detection (found/not found)
- Difficult to maintain and extend

#### New Approach
- Declarative rule definitions using dataclasses
- Multiple match modes (contains, equals, regex, any_of, greater_than)
- Confidence scoring with evidence collection
- Easy to add new patterns or modify existing ones

### 2. Core Components

#### DetectionRule Dataclass
```python
@dataclass
class DetectionRule:
    type: str  # Rule type: 'dependency', 'kind', 'image', etc.
    match_value: Union[str, List[str]]  # Value(s) to match
    match_mode: str = "contains"  # Matching strategy
    confidence_boost: float = 0.1  # Confidence contribution
    evidence_template: str = "Detected: {match}"  # Evidence format
    case_sensitive: bool = False
    description: str = ""  # Optional description
```

#### PatternDefinition Dataclass
```python
@dataclass
class PatternDefinition:
    name: str
    description: str
    rules: List[DetectionRule]
    min_confidence: float = 0.3  # Minimum confidence threshold
    category: str = "general"  # Pattern category
    recommendations: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
```

### 3. Enhanced Pattern Types

The system now detects and configures the following patterns:

1. **AI/ML Pipeline**
   - LLM services, vector databases, model serving
   - GPU resource detection and configuration
   - RAG architecture patterns
   - Data science tools (Jupyter, etc.)

2. **MLOps Operations** (New)
   - Model versioning and registry
   - A/B testing and canary deployments
   - Model monitoring and drift detection
   - Experiment tracking

3. **Model Context Protocol** (New)
   - MCP server detection
   - Tool integrations
   - API rate limiting
   - Circuit breaker patterns

4. **Security Patterns** (Enhanced)
   - Evidence-based component detection
   - Conditional operator installation
   - Enhanced RBAC configuration
   - Security scanning and compliance

5. **Scaling & Performance** (Enhanced)
   - KEDA event-driven autoscaling
   - Grafana dashboards
   - Resource quotas
   - Pod Disruption Budgets

6. **Data Processing Workflow** (Enhanced)
   - Component-specific operators (Kafka, Spark, Airflow)
   - Pipeline monitoring and SLAs
   - Data retention policies
   - Storage optimization

### 4. Evidence-Based Configuration

The new system uses detected evidence to make intelligent configuration decisions:

```python
# Example: AI/ML Configuration
evidence = self.pattern_evidence.get("AI/ML Pipeline", [])
has_gpu = any("GPU" in e for e in evidence)
has_vector_db = any("Vector database" in e for e in evidence)

# GPU-specific configuration only if GPU detected
if has_gpu:
    config.namespaces.append("gpu-operator")
    config.subscriptions["gpu-operator"] = {...}
```

### 5. Rule Types Supported

- **dependency**: Matches chart dependencies
- **kind**: Matches Kubernetes resource kinds
- **image**: Matches container images
- **content**: General content matching
- **api_version**: Matches API versions
- **annotation**: Matches annotations
- **port**: Matches service ports
- **service_count**: Checks number of services
- **chart_name**: Matches chart name
- **namespace**: Matches namespace names
- **resource**: Matches resource specifications

### 6. Match Modes

- **contains**: Substring matching
- **equals**: Exact matching
- **regex**: Regular expression matching
- **any_of**: Match any value in a list
- **greater_than**: Numeric comparison
- **less_than**: Numeric comparison
- **exists**: Check for presence

### 7. Benefits

1. **Maintainability**: Easy to add/modify patterns without changing code
2. **Flexibility**: Multiple rule types and match modes
3. **Transparency**: Evidence collection shows why patterns were detected
4. **Accuracy**: Confidence scoring prevents false positives
5. **Extensibility**: New rule types can be added easily
6. **Documentation**: Pattern definitions include descriptions and recommendations

## Usage Example

```python
# Define a new pattern
new_pattern = PatternDefinition(
    name="Edge Computing",
    description="Edge computing and IoT workloads",
    category="deployment",
    rules=[
        DetectionRule("content", ["edge", "iot", "mqtt"], "any_of", 0.3, "Edge keyword: {match}"),
        DetectionRule("dependency", ["mosquitto", "emqx"], "any_of", 0.4, "MQTT broker: {match}"),
        DetectionRule("port", [1883, 8883], "any_of", 0.2, "MQTT port: {match}"),
    ],
    recommendations=[
        "Configure edge node selectors",
        "Set up offline operation support",
        "Implement data synchronization"
    ]
)
```

## Integration Points

1. **Enhanced Analyzer**: Uses rule engine for pattern detection
2. **Pattern Configurator**: Generates configurations based on detected patterns
3. **Report Generator**: Includes pattern recommendations in reports
4. **CLI**: Shows detected patterns during analysis phase

## Future Enhancements

1. **Pattern Relationships**: Use related_patterns for complex scenarios
2. **Custom Rules**: Allow users to define custom patterns via YAML/JSON
3. **Pattern Composition**: Combine multiple patterns for complex architectures
4. **Machine Learning**: Use historical data to improve confidence scoring
5. **Pattern Templates**: Generate complete architectures from patterns