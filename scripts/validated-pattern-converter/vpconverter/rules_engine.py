"""
Rule-based pattern detection engine for validated patterns.

This module provides a flexible, maintainable system for detecting
architecture patterns in Helm charts and Kubernetes configurations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import re
from pathlib import Path

from .models import ArchitecturePattern


@dataclass
class DetectionRule:
    """A single detection rule that can match against various parts of a Helm chart"""
    type: str  # Rule type: 'dependency', 'kind', 'image', 'annotation', 'label', 'env', 'port', 'content', 'api_version', etc.
    match_value: Union[str, List[str]]  # Value(s) to match
    match_mode: str = "contains"  # 'contains', 'equals', 'regex', 'any_of', 'greater_than'
    confidence_boost: float = 0.1  # How much this rule boosts confidence
    evidence_template: str = "Detected: {match}"  # Evidence message template
    case_sensitive: bool = False
    description: str = ""  # Optional description of what this rule detects

    def __post_init__(self):
        """Validate rule configuration"""
        valid_types = ['dependency', 'kind', 'image', 'annotation', 'label', 'env',
                      'port', 'content', 'api_version', 'service_count', 'replicas',
                      'service_type', 'chart_name', 'namespace', 'resource']
        if self.type not in valid_types:
            raise ValueError(f"Invalid rule type: {self.type}. Must be one of {valid_types}")

        valid_modes = ['contains', 'equals', 'regex', 'any_of', 'greater_than', 'less_than', 'exists']
        if self.match_mode not in valid_modes:
            raise ValueError(f"Invalid match mode: {self.match_mode}. Must be one of {valid_modes}")


@dataclass
class PatternDefinition:
    """Defines a complete pattern with multiple detection rules"""
    name: str
    description: str
    rules: List[DetectionRule]
    min_confidence: float = 0.3  # Minimum confidence to report this pattern
    category: str = "general"  # Pattern category: 'ai_ml', 'security', 'scaling', 'data', 'deployment'
    recommendations: List[str] = field(default_factory=list)  # Recommended configurations
    related_patterns: List[str] = field(default_factory=list)  # Related pattern names

    def __post_init__(self):
        """Validate pattern definition"""
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError(f"min_confidence must be between 0.0 and 1.0, got {self.min_confidence}")


class RuleEngine:
    """Core rule matching engine"""

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive

    def match(self, text: str, match_values: Union[str, List[str]],
              match_mode: str, case_sensitive: Optional[bool] = None) -> List[str]:
        """Core matching logic that returns list of matches"""
        if case_sensitive is None:
            case_sensitive = self.case_sensitive

        if not case_sensitive:
            text = text.lower()
            if isinstance(match_values, str):
                match_values = match_values.lower()
            else:
                match_values = [v.lower() for v in match_values]

        matches = []

        if match_mode == "contains":
            if isinstance(match_values, str):
                if match_values in text:
                    matches.append(match_values)
            else:
                for value in match_values:
                    if value in text:
                        matches.append(value)

        elif match_mode == "equals":
            if isinstance(match_values, str):
                if text == match_values:
                    matches.append(match_values)
            else:
                for value in match_values:
                    if text == value:
                        matches.append(value)

        elif match_mode == "any_of":
            if isinstance(match_values, list):
                for value in match_values:
                    if value in text:
                        matches.append(value)

        elif match_mode == "regex":
            pattern = match_values if isinstance(match_values, str) else match_values[0]
            flags = 0 if case_sensitive else re.IGNORECASE
            if re.search(pattern, text, flags):
                matches.append(pattern)

        elif match_mode == "exists":
            # Just check if text is non-empty
            if text:
                matches.append("exists")

        return matches


# Default pattern definitions for validated patterns
DEFAULT_PATTERNS = [
    # AI/ML Pipeline Pattern
    PatternDefinition(
        name="AI/ML Pipeline",
        description="Machine learning pipeline with model training, serving, or inference capabilities",
        category="ai_ml",
        rules=[
            # Core AI/ML dependencies
            DetectionRule("dependency", ["llm", "llama", "gpt", "bert", "transformer", "huggingface",
                                       "pytorch", "tensorflow", "mlflow", "kubeflow", "kserve",
                                       "model", "inference", "ollama", "vllm", "triton"],
                         "any_of", 0.3, "AI/ML dependency: {match}"),

            # Vector databases - higher confidence as they're AI-specific
            DetectionRule("dependency", ["vector", "embedding", "faiss", "chroma", "pinecone",
                                       "weaviate", "qdrant", "pgvector", "milvus"],
                         "any_of", 0.4, "Vector database: {match}"),

            # AI-specific Kubernetes resources
            DetectionRule("kind", ["InferenceService", "ServingRuntime", "Notebook",
                                 "PipelineRun", "Pipeline"],
                         "any_of", 0.4, "ML service type: {match}"),

            # GPU resources
            DetectionRule("content", ["nvidia.com/gpu", "amd.com/gpu", "gpu-operator"],
                         "any_of", 0.3, "GPU resources configured"),

            # Model serving patterns
            DetectionRule("content", ["predictor", "inference", "serving", "endpoint",
                                    "llamastack", "model-server"],
                         "any_of", 0.2, "Model serving: {match}"),

            # RAG patterns
            DetectionRule("chart_name", "rag", "contains", 0.5, "RAG architecture in chart name"),
            DetectionRule("content", ["retrieval", "augmented", "generation", "embedding"],
                         "any_of", 0.2, "RAG component: {match}"),

            # UI for AI
            DetectionRule("content", ["streamlit", "gradio", "chainlit"],
                         "any_of", 0.2, "AI UI framework: {match}"),

            # Data science tools
            DetectionRule("content", ["jupyter", "notebook", "jupyterlab"],
                         "any_of", 0.2, "Data science tools: {match}"),
        ],
        recommendations=[
            "Configure GPU operators for accelerated computing",
            "Set up model registry for version control",
            "Implement model monitoring and drift detection",
            "Configure appropriate storage for model artifacts",
            "Set up autoscaling based on inference load"
        ],
        related_patterns=["MLOps Operations", "Kubeflow Data Science"]
    ),

    # Security Patterns
    PatternDefinition(
        name="Security Patterns",
        description="Security measures including authentication, authorization, encryption, and compliance",
        category="security",
        rules=[
            # Authentication methods
            DetectionRule("content", ["oauth", "oidc", "jwt", "saml", "ldap", "auth",
                                    "keycloak", "dex", "auth0"],
                         "any_of", 0.2, "Authentication: {match}"),

            # Encryption
            DetectionRule("content", ["tls", "ssl", "https", "certificate", "cert-manager"],
                         "any_of", 0.3, "Encryption: {match}"),

            # RBAC
            DetectionRule("kind", ["Role", "ClusterRole", "RoleBinding",
                                 "ClusterRoleBinding", "ServiceAccount"],
                         "any_of", 0.3, "RBAC configuration: {match}"),

            # Security contexts
            DetectionRule("content", ["securitycontext", "runasnonroot", "readonlyrootfilesystem"],
                         "any_of", 0.2, "Security contexts configured"),

            # Network policies
            DetectionRule("kind", "NetworkPolicy", "equals", 0.3, "Network policies defined"),

            # Security tools
            DetectionRule("content", ["vault", "sealed-secrets", "external-secrets", "sops"],
                         "any_of", 0.3, "Secrets management: {match}"),

            # Compliance and scanning
            DetectionRule("content", ["falco", "trivy", "snyk", "twistlock", "aqua", "stackrox"],
                         "any_of", 0.3, "Security scanning: {match}"),
        ],
        recommendations=[
            "Implement Pod Security Standards",
            "Configure network policies for namespace isolation",
            "Enable audit logging",
            "Set up vulnerability scanning in CI/CD",
            "Implement secrets rotation"
        ]
    ),

    # MLOps Operations Pattern
    PatternDefinition(
        name="MLOps Operations",
        description="Machine Learning Operations with model lifecycle management",
        category="ai_ml",
        min_confidence=0.4,
        rules=[
            # Model serving platforms
            DetectionRule("content", ["vllm", "kserve", "seldon", "mlflow", "model-registry",
                                    "bentoml", "ray-serve"],
                         "any_of", 0.3, "Model platform: {match}"),

            # KServe specific
            DetectionRule("api_version", "serving.kserve.io", "contains", 0.4, "KServe API"),
            DetectionRule("kind", ["ServingRuntime", "InferenceService", "Predictor"],
                         "any_of", 0.3, "KServe resource: {match}"),

            # Experimentation
            DetectionRule("content", ["experiment", "ab-test", "canary", "traffic-split",
                                    "shadow-deployment"],
                         "any_of", 0.2, "Experimentation: {match}"),

            # Monitoring
            DetectionRule("content", ["model-monitoring", "drift-detection", "feature-drift",
                                    "model-metrics", "prediction-metrics"],
                         "any_of", 0.2, "Model monitoring: {match}"),

            # Pipeline tools
            DetectionRule("content", ["mlflow", "wandb", "neptune", "comet", "clearml"],
                         "any_of", 0.2, "ML tracking: {match}"),
        ],
        recommendations=[
            "Implement A/B testing for model deployments",
            "Set up model performance monitoring",
            "Configure gradual rollout strategies",
            "Implement model versioning and rollback",
            "Set up feature stores for consistency"
        ],
        related_patterns=["AI/ML Pipeline"]
    ),

    # Data Processing Workflow
    PatternDefinition(
        name="Data Processing Workflow",
        description="Data pipeline with ETL/ELT, streaming, or batch processing capabilities",
        category="data",
        rules=[
            # Data processing frameworks
            DetectionRule("dependency", ["spark", "kafka", "flink", "beam", "airflow", "dagster",
                                       "prefect", "luigi", "argo", "tekton", "nifi"],
                         "any_of", 0.3, "Data framework: {match}"),

            # Kubeflow pipelines
            DetectionRule("api_version", ["kubeflow.org", "datasciencepipelinesapplications"],
                         "any_of", 0.4, "Pipeline platform: {match}"),

            # Batch processing
            DetectionRule("kind", ["Job", "CronJob"], "any_of", 0.2, "Batch processing: {match}"),

            # ETL patterns
            DetectionRule("content", ["etl", "elt", "extract", "transform", "load", "ingestion"],
                         "any_of", 0.3, "ETL/ELT pipeline"),

            # Streaming
            DetectionRule("content", ["stream", "real-time", "event-driven", "cdc"],
                         "any_of", 0.2, "Stream processing"),

            # Message queues
            DetectionRule("content", ["rabbitmq", "activemq", "pulsar", "nats"],
                         "any_of", 0.2, "Message queue: {match}"),
        ],
        recommendations=[
            "Configure appropriate resource limits for data jobs",
            "Implement data quality checks",
            "Set up monitoring for pipeline health",
            "Configure data retention policies",
            "Implement idempotent processing"
        ]
    ),

    # Scaling & Performance Pattern
    PatternDefinition(
        name="Scaling & Performance",
        description="Horizontal/vertical scaling, load balancing, and performance optimization",
        category="scaling",
        rules=[
            # Autoscaling
            DetectionRule("kind", "HorizontalPodAutoscaler", "equals", 0.4, "HPA configured"),
            DetectionRule("content", "verticalpodautoscaler", "contains", 0.3, "VPA configured"),
            DetectionRule("content", ["keda", "event-driven", "scaledobject"],
                         "any_of", 0.3, "KEDA autoscaling"),

            # High availability
            DetectionRule("replicas", 1, "greater_than", 0.2, "Multi-replica deployment"),
            DetectionRule("content", ["affinity", "anti-affinity", "topology"],
                         "any_of", 0.2, "Pod distribution: {match}"),

            # Load balancing
            DetectionRule("service_type", ["LoadBalancer", "NodePort"],
                         "any_of", 0.2, "External load balancing"),

            # Resource management
            DetectionRule("content", ["requests", "limits"], "any_of", 0.2, "Resource constraints"),

            # Caching
            DetectionRule("content", ["redis", "memcached", "hazelcast"],
                         "any_of", 0.2, "Caching layer: {match}"),

            # CDN/Edge
            DetectionRule("content", ["cloudflare", "akamai", "fastly", "cdn"],
                         "any_of", 0.2, "CDN integration: {match}"),
        ],
        recommendations=[
            "Configure PodDisruptionBudgets for availability",
            "Implement proper health checks",
            "Set up cluster autoscaling",
            "Configure appropriate QoS classes",
            "Implement caching strategies"
        ]
    ),

    # Model Context Protocol Pattern
    PatternDefinition(
        name="Model Context Protocol",
        description="MCP servers providing tool and API integrations for AI models",
        category="ai_ml",
        min_confidence=0.35,
        rules=[
            # MCP specific
            DetectionRule("content", ["mcp-server", "model-context-protocol", "mcp::", "fastmcp"],
                         "any_of", 0.4, "MCP component: {match}"),

            # MCP tools
            DetectionRule("content", ["mcp-weather", "mcp-search", "mcp-browser", "mcp-filesystem",
                                    "weather-tool", "search-tool"],
                         "any_of", 0.2, "MCP tool: {match}"),

            # SSE endpoints
            DetectionRule("content", ["sse", "server-sent-events", "event-stream"],
                         "any_of", 0.2, "SSE endpoints for streaming"),

            # Tool integration
            DetectionRule("content", ["tool-use", "function-calling", "tool-integration"],
                         "any_of", 0.2, "Tool integration pattern"),
        ],
        recommendations=[
            "Configure API key management for external tools",
            "Implement proper error handling for tool failures",
            "Set up monitoring for tool usage",
            "Configure rate limiting for external APIs"
        ],
        related_patterns=["AI/ML Pipeline"]
    ),
]


def load_patterns(pattern_file: Optional[Path] = None) -> List[PatternDefinition]:
    """Load pattern definitions from file or use defaults"""
    if pattern_file and pattern_file.exists():
        # TODO: Implement loading from YAML/JSON file
        pass
    return DEFAULT_PATTERNS