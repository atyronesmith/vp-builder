"""
Pattern-specific configuration generator.

This module automatically generates appropriate configurations based on detected patterns:
- AI/ML patterns: GPU resources, model storage, inference services
- Security patterns: Network policies, RBAC, secrets management
- Scaling patterns: HPA, resource limits, cluster autoscaling
- MLOps patterns: Model versioning, A/B testing, monitoring
- Data Processing: Pipeline orchestration, storage optimization
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml

from .models import AnalysisResult
from .utils import log_info, console
from .rules_engine import PatternDefinition, load_patterns


@dataclass
class PatternConfig:
    """Configuration for a specific pattern type."""
    namespaces: List[str]
    subscriptions: Dict[str, Dict[str, Any]]
    applications: Dict[str, Dict[str, Any]]
    resources: Dict[str, Any]
    policies: Dict[str, Any]


class PatternConfigurator:
    """Generates pattern-specific configurations."""

    def __init__(self, analysis_result: AnalysisResult):
        self.analysis = analysis_result
        self.detected_patterns = []
        self.pattern_definitions = load_patterns()
        self.pattern_evidence = {}  # Store evidence for each detected pattern

        # Extract pattern names with high confidence (>= 0.6)
        if hasattr(analysis_result, 'enhanced_analysis') and analysis_result.enhanced_analysis:
            for chart_analysis in analysis_result.enhanced_analysis:
                for pattern in chart_analysis.patterns:
                    if pattern.confidence >= 0.6:
                        self.detected_patterns.append(pattern.name)
                        self.pattern_evidence[pattern.name] = pattern.evidence

    def generate_configurations(self) -> Dict[str, PatternConfig]:
        """Generate configurations for all detected patterns."""
        configs = {}

        # Map pattern names to configuration generators
        pattern_config_map = {
            "AI/ML Pipeline": self._generate_ai_ml_config,
            "Security Patterns": self._generate_security_config,
            "Scaling & Performance": self._generate_scaling_config,
            "Data Processing Workflow": self._generate_data_processing_config,
            "MLOps Operations": self._generate_mlops_config,
            "Model Context Protocol": self._generate_mcp_config,
        }

        for pattern_name in self.detected_patterns:
            config_generator = pattern_config_map.get(pattern_name)
            if config_generator:
                config_key = pattern_name.lower().replace(" ", "_").replace("&", "and")
                configs[config_key] = config_generator()

                # Add recommendations from pattern definition
                pattern_def = next((p for p in self.pattern_definitions if p.name == pattern_name), None)
                if pattern_def and pattern_def.recommendations:
                    log_info(f"  Recommendations for {pattern_name}:")
                    for rec in pattern_def.recommendations:
                        log_info(f"    • {rec}")

        return configs

    def _generate_ai_ml_config(self) -> PatternConfig:
        """Generate AI/ML specific configuration."""
        log_info("Generating AI/ML pattern configuration...")

        # Check evidence for specific AI/ML components
        evidence = self.pattern_evidence.get("AI/ML Pipeline", [])
        has_gpu = any("GPU" in e for e in evidence)
        has_vector_db = any("Vector database" in e for e in evidence)
        has_rag = any("RAG" in e for e in evidence)
        has_llm = any("llm" in e.lower() or "model" in e.lower() for e in evidence)

        config = PatternConfig(
            namespaces=[
                "ai-ml-serving",
                "model-registry",
            ],
            subscriptions={},
            applications={},
            resources={},
            policies={}
        )

        # Add GPU operator if GPU resources detected
        if has_gpu:
            config.namespaces.append("gpu-operator")
            config.subscriptions["gpu-operator"] = {
                "namespace": "gpu-operator",
                "channel": "stable",
                "source": "certified-operators",
                "description": "NVIDIA GPU Operator for GPU workloads"
            }
            config.resources["gpu_node_selector"] = {
                "nvidia.com/gpu.present": "true"
            }
            config.resources["resource_limits"] = {
                "nvidia.com/gpu": 1,
                "memory": "16Gi",
                "cpu": "4"
            }

        # Add Red Hat OpenShift AI for comprehensive ML workflows
        if has_llm or has_rag:
            config.namespaces.append("rhoai")
            config.subscriptions["rhoai"] = {
                "namespace": "rhoai",
                "channel": "stable",
                "source": "redhat-operators",
                "description": "Red Hat OpenShift AI for ML workflows"
            }

        # Model serving configuration
        config.applications["model-serving"] = {
            "name": "model-serving",
            "namespace": "ai-ml-serving",
            "description": "Model inference service configuration",
            "helm": {
                "values": {
                    "autoscaling": {
                        "enabled": True,
                        "minReplicas": 1,
                        "maxReplicas": 10,
                        "metrics": self._get_ai_ml_metrics(has_gpu)
                    },
                    "resources": self._get_ai_ml_resources(has_gpu)
                }
            }
        }

        # Vector database specific configuration
        if has_vector_db:
            config.resources["vector_db_storage"] = {
                "size": "200Gi",
                "storageClass": "fast-ssd",
                "description": "High-performance storage for vector embeddings"
            }

        # Model storage
        config.resources["storage"] = {
            "model_cache": {
                "size": "100Gi",
                "storageClass": "fast-ssd" if has_llm else "standard"
            }
        }

        # AI/ML specific HPA configuration
        config.policies["hpa"] = {
            "enabled": True,
            "description": "Horizontal Pod Autoscaler for AI workloads",
            "metrics": ["gpu_utilization", "inference_queue_size"] if has_gpu else ["cpu", "memory"]
        }

        return config

    def _generate_mlops_config(self) -> PatternConfig:
        """Generate MLOps specific configuration."""
        log_info("Generating MLOps pattern configuration...")

        return PatternConfig(
            namespaces=[
                "mlflow",
                "kserve",
                "model-experiments"
            ],
            subscriptions={
                "kserve": {
                    "namespace": "kserve",
                    "channel": "stable",
                    "source": "community-operators",
                    "description": "Model serving and inference"
                }
            },
            applications={
                "mlflow": {
                    "name": "mlflow",
                    "namespace": "mlflow",
                    "description": "Model lifecycle management",
                    "helm": {
                        "values": {
                            "backend": {
                                "store": "postgres",
                                "artifactStore": "s3"
                            }
                        }
                    }
                },
                "model-registry": {
                    "name": "model-registry",
                    "namespace": "model-experiments",
                    "description": "Central model registry"
                }
            },
            resources={
                "experiment_tracking": {
                    "enabled": True,
                    "storage": "100Gi"
                },
                "model_versioning": {
                    "enabled": True,
                    "retention": "30d"
                },
                "ab_testing": {
                    "enabled": True,
                    "traffic_split": {
                        "canary": 10,
                        "stable": 90
                    }
                }
            },
            policies={
                "deployment_strategy": {
                    "type": "canary",
                    "rollback_on_failure": True,
                    "metrics_analysis": True
                }
            }
        )

    def _generate_mcp_config(self) -> PatternConfig:
        """Generate Model Context Protocol specific configuration."""
        log_info("Generating MCP pattern configuration...")

        return PatternConfig(
            namespaces=[
                "mcp-servers",
                "tool-registry"
            ],
            subscriptions={},
            applications={
                "mcp-server": {
                    "name": "mcp-server",
                    "namespace": "mcp-servers",
                    "description": "Model Context Protocol server",
                    "helm": {
                        "values": {
                            "tools": {
                                "enabled": True,
                                "registry": "tool-registry"
                            },
                            "api": {
                                "rateLimit": {
                                    "enabled": True,
                                    "requests_per_minute": 100
                                }
                            }
                        }
                    }
                }
            },
            resources={
                "api_keys": {
                    "vault_path": "/secret/mcp/api-keys",
                    "rotation": "30d"
                },
                "tool_permissions": {
                    "default": "read",
                    "admin": ["read", "write", "execute"]
                }
            },
            policies={
                "circuit_breaker": {
                    "enabled": True,
                    "failure_threshold": 5,
                    "timeout": "30s"
                }
            }
        )

    def _generate_security_config(self) -> PatternConfig:
        """Generate security-specific configuration."""
        log_info("Generating security pattern configuration...")

        # Check evidence for specific security components
        evidence = self.pattern_evidence.get("Security Patterns", [])
        has_vault = any("vault" in e.lower() for e in evidence)
        has_cert_manager = any("cert" in e.lower() for e in evidence)
        has_rbac = any("rbac" in e.lower() for e in evidence)

        config = PatternConfig(
            namespaces=[],
            subscriptions={},
            applications={},
            resources={
                "network_policies": {
                    "default_deny": True,
                    "allow_dns": True,
                    "namespace_isolation": True
                },
                "pod_security_standards": {
                    "enforce": "restricted",
                    "audit": "restricted",
                    "warn": "restricted"
                }
            },
            policies={
                "security_context": {
                    "runAsNonRoot": True,
                    "readOnlyRootFilesystem": True,
                    "allowPrivilegeEscalation": False,
                    "capabilities": {
                        "drop": ["ALL"]
                    }
                }
            }
        )

        # Add Vault if secrets management detected
        if has_vault:
            config.namespaces.append("vault")
            config.applications["vault"] = {
                "name": "vault",
                "namespace": "vault",
                "chart": "vault",
                "repoURL": "https://charts.validatedpatterns.io",
                "targetRevision": "0.1.0",
                "description": "HashiCorp Vault for secrets management"
            }

        # Add cert-manager if TLS/certificates detected
        if has_cert_manager:
            config.namespaces.append("cert-manager")
            config.subscriptions["cert-manager"] = {
                "namespace": "cert-manager",
                "channel": "stable",
                "source": "community-operators",
                "description": "Certificate management for TLS"
            }

        # Enhanced RBAC if detected
        if has_rbac:
            config.resources["rbac"] = {
                "least_privilege": True,
                "service_accounts_per_app": True,
                "audit_logging": True
            }

        # Always include security operators for patterns
        config.namespaces.extend(["compliance-operator", "stackrox"])
        config.subscriptions.update({
            "compliance-operator": {
                "namespace": "compliance-operator",
                "channel": "stable",
                "source": "redhat-operators",
                "description": "Security compliance scanning"
            },
            "rhacs": {
                "namespace": "stackrox",
                "channel": "stable",
                "source": "redhat-operators",
                "description": "Red Hat Advanced Cluster Security"
            }
        })

        config.policies["image_scanning"] = {
            "enabled": True,
            "block_on_critical": True,
            "scan_frequency": "daily"
        }

        return config

    def _generate_scaling_config(self) -> PatternConfig:
        """Generate scaling-specific configuration."""
        log_info("Generating scaling pattern configuration...")

        return PatternConfig(
            namespaces=[
                "keda",
                "prometheus",
                "grafana"
            ],
            subscriptions={
                "keda": {
                    "namespace": "keda",
                    "channel": "stable",
                    "source": "community-operators",
                    "description": "Kubernetes Event-driven Autoscaling"
                },
                "prometheus": {
                    "namespace": "prometheus",
                    "channel": "stable",
                    "source": "community-operators",
                    "description": "Metrics collection for autoscaling"
                }
            },
            applications={
                "keda": {
                    "name": "keda",
                    "namespace": "keda",
                    "description": "Event-driven autoscaler"
                },
                "prometheus": {
                    "name": "prometheus",
                    "namespace": "prometheus",
                    "description": "Metrics server"
                },
                "grafana": {
                    "name": "grafana",
                    "namespace": "grafana",
                    "description": "Metrics visualization",
                    "helm": {
                        "values": {
                            "dashboards": {
                                "default": {
                                    "cluster-autoscaler": True,
                                    "hpa-metrics": True,
                                    "resource-usage": True
                                }
                            }
                        }
                    }
                }
            },
            resources={
                "cluster_autoscaler": {
                    "enabled": True,
                    "min_nodes": 3,
                    "max_nodes": 100,
                    "scale_down_delay": "10m"
                },
                "resource_quotas": {
                    "enabled": True,
                    "per_namespace": True
                }
            },
            policies={
                "hpa": {
                    "cpu_threshold": 70,
                    "memory_threshold": 80,
                    "scale_up_rate": "100%",
                    "scale_down_rate": "10%"
                },
                "vpa": {
                    "enabled": True,
                    "update_mode": "Auto"
                },
                "pdb": {
                    "min_available": "50%",
                    "description": "Pod Disruption Budget for HA"
                }
            }
        )

    def _generate_data_processing_config(self) -> PatternConfig:
        """Generate data processing specific configuration."""
        log_info("Generating data processing pattern configuration...")

        # Check evidence for specific data processing components
        evidence = self.pattern_evidence.get("Data Processing Workflow", [])
        has_kafka = any("kafka" in e.lower() for e in evidence)
        has_spark = any("spark" in e.lower() for e in evidence)
        has_airflow = any("airflow" in e.lower() for e in evidence)

        config = PatternConfig(
            namespaces=[
                "data-pipeline",
                "streaming"
            ],
            subscriptions={},
            applications={},
            resources={
                "pipeline_storage": {
                    "staging": {
                        "size": "500Gi",
                        "storageClass": "standard"
                    },
                    "processed": {
                        "size": "1Ti",
                        "storageClass": "standard"
                    }
                },
                "job_resources": {
                    "batch_jobs": {
                        "memory": "8Gi",
                        "cpu": "4",
                        "parallelism": 10
                    }
                }
            },
            policies={
                "data_retention": {
                    "raw_data": "30d",
                    "processed_data": "90d",
                    "archived_data": "1y"
                },
                "pipeline_monitoring": {
                    "enabled": True,
                    "alert_on_failure": True,
                    "sla_monitoring": True
                }
            }
        )

        # Add Kafka operator if streaming detected
        if has_kafka:
            config.namespaces.append("kafka")
            config.subscriptions["strimzi-kafka-operator"] = {
                "namespace": "kafka",
                "channel": "stable",
                "source": "community-operators",
                "description": "Apache Kafka on Kubernetes"
            }
            config.applications["kafka"] = {
                "name": "kafka-cluster",
                "namespace": "kafka",
                "description": "Streaming data platform"
            }

        # Add Spark operator if Spark detected
        if has_spark:
            config.namespaces.append("spark")
            config.subscriptions["spark-operator"] = {
                "namespace": "spark",
                "channel": "stable",
                "source": "community-operators",
                "description": "Apache Spark on Kubernetes"
            }

        # Add Airflow if workflow orchestration detected
        if has_airflow:
            config.applications["airflow"] = {
                "name": "airflow",
                "namespace": "data-pipeline",
                "description": "Workflow orchestration",
                "helm": {
                    "values": {
                        "executor": "KubernetesExecutor",
                        "workers": {
                            "replicas": 3
                        }
                    }
                }
            }

        return config

    def _get_ai_ml_metrics(self, has_gpu: bool) -> List[Dict[str, Any]]:
        """Get appropriate metrics for AI/ML autoscaling."""
        metrics = []

        if has_gpu:
            metrics.append({
                "type": "Resource",
                "resource": {
                    "name": "nvidia.com/gpu",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": 80
                    }
                }
            })

        # Always include CPU and memory metrics
        metrics.extend([
            {
                "type": "Resource",
                "resource": {
                    "name": "cpu",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": 70
                    }
                }
            },
            {
                "type": "Resource",
                "resource": {
                    "name": "memory",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": 80
                    }
                }
            }
        ])

        return metrics

    def _get_ai_ml_resources(self, has_gpu: bool) -> Dict[str, Any]:
        """Get appropriate resource limits for AI/ML workloads."""
        resources = {
            "requests": {
                "memory": "4Gi",
                "cpu": "2"
            },
            "limits": {
                "memory": "16Gi",
                "cpu": "4"
            }
        }

        if has_gpu:
            resources["limits"]["nvidia.com/gpu"] = "1"
            resources["requests"]["nvidia.com/gpu"] = "1"

        return resources

    def apply_to_values(self, values_file: Path, pattern_configs: Dict[str, PatternConfig]) -> None:
        """Apply pattern configurations to values file."""
        log_info(f"Applying pattern configurations to {values_file}")

        # Load existing values
        values = {}
        if values_file.exists():
            with open(values_file, 'r') as f:
                values = yaml.safe_load(f) or {}

        # Apply configurations
        for pattern_name, config in pattern_configs.items():
            log_info(f"  Applying {pattern_name} configuration...")

            # Add namespaces
            if 'clusterGroup' not in values:
                values['clusterGroup'] = {}
            if 'namespaces' not in values['clusterGroup']:
                values['clusterGroup']['namespaces'] = []

            for ns in config.namespaces:
                if ns not in values['clusterGroup']['namespaces']:
                    values['clusterGroup']['namespaces'].append(ns)

            # Add subscriptions
            if 'subscriptions' not in values['clusterGroup']:
                values['clusterGroup']['subscriptions'] = {}

            values['clusterGroup']['subscriptions'].update(config.subscriptions)

            # Add applications
            if 'applications' not in values['clusterGroup']:
                values['clusterGroup']['applications'] = {}

            values['clusterGroup']['applications'].update(config.applications)

        # Write updated values
        with open(values_file, 'w') as f:
            yaml.dump(values, f, default_flow_style=False, sort_keys=False)

        log_info(f"  Updated {values_file} with pattern-specific configurations")

    def generate_resource_files(self, output_dir: Path, pattern_configs: Dict[str, PatternConfig]) -> None:
        """Generate resource-specific YAML files for each pattern."""
        resources_dir = output_dir / "resources"
        resources_dir.mkdir(exist_ok=True)

        for pattern_name, config in pattern_configs.items():
            pattern_dir = resources_dir / pattern_name
            pattern_dir.mkdir(exist_ok=True)

            # Generate HPA configurations for AI/ML and scaling patterns
            if pattern_name in ["ai_ml", "scaling"] and "hpa" in config.policies:
                self._generate_hpa_config(pattern_dir, config)

            # Generate NetworkPolicy for security patterns
            if pattern_name == "security" and "network_policies" in config.resources:
                self._generate_network_policies(pattern_dir, config)

            # Generate resource quotas for scaling patterns
            if pattern_name == "scaling" and "resource_quotas" in config.policies:
                self._generate_resource_quotas(pattern_dir, config)

    def _generate_hpa_config(self, output_dir: Path, config: PatternConfig) -> None:
        """Generate HorizontalPodAutoscaler configurations."""
        hpa_file = output_dir / "hpa-config.yaml"

        hpa_config = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "ai-workload-hpa",
                "namespace": "ai-ml-serving"
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "model-server"
                },
                "minReplicas": 1,
                "maxReplicas": 10,
                "metrics": []
            }
        }

        # Add GPU metrics for AI/ML
        if "gpu_utilization" in config.policies.get("hpa", {}).get("metrics", []):
            hpa_config["spec"]["metrics"].append({
                "type": "Resource",
                "resource": {
                    "name": "nvidia.com/gpu",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": 80
                    }
                }
            })

        with open(hpa_file, 'w') as f:
            yaml.dump(hpa_config, f, default_flow_style=False)

        log_info(f"    Generated HPA configuration: {hpa_file}")

    def _generate_network_policies(self, output_dir: Path, config: PatternConfig) -> None:
        """Generate NetworkPolicy configurations."""
        np_file = output_dir / "network-policies.yaml"

        policies = []

        if config.resources.get("network_policies", {}).get("default_deny"):
            policies.append({
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "default-deny-all",
                    "namespace": "default"
                },
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress", "Egress"]
                }
            })

        if config.resources.get("network_policies", {}).get("allow_dns"):
            policies.append({
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "allow-dns",
                    "namespace": "default"
                },
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Egress"],
                    "egress": [{
                        "to": [{
                            "namespaceSelector": {
                                "matchLabels": {
                                    "name": "openshift-dns"
                                }
                            }
                        }],
                        "ports": [{
                            "protocol": "UDP",
                            "port": 53
                        }]
                    }]
                }
            })

        with open(np_file, 'w') as f:
            yaml.dump_all(policies, f, default_flow_style=False)

        log_info(f"    Generated network policies: {np_file}")

    def _generate_resource_quotas(self, output_dir: Path, config: PatternConfig) -> None:
        """Generate ResourceQuota configurations."""
        rq_file = output_dir / "resource-quotas.yaml"

        quota_config = {
            "apiVersion": "v1",
            "kind": "ResourceQuota",
            "metadata": {
                "name": "compute-quota",
                "namespace": "default"
            },
            "spec": {
                "hard": config.policies.get("resource_quotas", {}).get("defaults", {})
            }
        }

        with open(rq_file, 'w') as f:
            yaml.dump(quota_config, f, default_flow_style=False)

        log_info(f"    Generated resource quota: {rq_file}")

    def _update_report_with_patterns(self, pattern_configs: Dict[str, Any]) -> None:
        """Update conversion report with pattern-specific information."""
        # Implementation remains the same
        pass