"""
Pattern-specific configuration generator.

This module automatically generates appropriate configurations based on detected patterns:
- AI/ML patterns: GPU resources, model storage, inference services
- Security patterns: Network policies, RBAC, secrets management
- Scaling patterns: HPA, resource limits, cluster autoscaling
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml

from .models import AnalysisResult
from .utils import log_info, console


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

        # Extract pattern names with high confidence (>= 0.6)
        if hasattr(analysis_result, 'enhanced_analysis') and analysis_result.enhanced_analysis:
            for chart_analysis in analysis_result.enhanced_analysis:
                for pattern in chart_analysis.patterns:
                    if pattern.confidence >= 0.6:
                        self.detected_patterns.append(pattern.name)

    def generate_configurations(self) -> Dict[str, PatternConfig]:
        """Generate configurations for all detected patterns."""
        configs = {}

        if "AI/ML Pipeline" in self.detected_patterns:
            configs["ai_ml"] = self._generate_ai_ml_config()

        if "Security Patterns" in self.detected_patterns:
            configs["security"] = self._generate_security_config()

        if "Scaling Patterns" in self.detected_patterns:
            configs["scaling"] = self._generate_scaling_config()

        if "Data Processing Pipeline" in self.detected_patterns:
            configs["data_processing"] = self._generate_data_processing_config()

        return configs

    def _generate_ai_ml_config(self) -> PatternConfig:
        """Generate AI/ML specific configuration."""
        log_info("Generating AI/ML pattern configuration...")

        return PatternConfig(
            namespaces=[
                "ai-ml-serving",
                "model-registry",
                "gpu-operator",
                "rhoai",  # Red Hat OpenShift AI
            ],
            subscriptions={
                "gpu-operator": {
                    "namespace": "gpu-operator",
                    "channel": "stable",
                    "source": "certified-operators",
                    "description": "NVIDIA GPU Operator for GPU workloads"
                },
                "rhoai": {
                    "namespace": "rhoai",
                    "channel": "stable",
                    "source": "redhat-operators",
                    "description": "Red Hat OpenShift AI for ML workflows"
                }
            },
            applications={
                "model-serving": {
                    "name": "model-serving",
                    "namespace": "ai-ml-serving",
                    "description": "Model inference service configuration",
                    "helm": {
                        "values": {
                            "autoscaling": {
                                "enabled": True,
                                "minReplicas": 1,
                                "maxReplicas": 10,
                                "metrics": [
                                    {
                                        "type": "Resource",
                                        "resource": {
                                            "name": "nvidia.com/gpu",
                                            "target": {
                                                "type": "Utilization",
                                                "averageUtilization": 80
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                "model-registry": {
                    "name": "model-registry",
                    "namespace": "model-registry",
                    "description": "ML model registry for model versioning"
                }
            },
            resources={
                "gpu_node_selector": {
                    "nvidia.com/gpu.present": "true"
                },
                "resource_limits": {
                    "nvidia.com/gpu": 1,
                    "memory": "16Gi",
                    "cpu": "4"
                },
                "storage": {
                    "model_cache": {
                        "size": "100Gi",
                        "storageClass": "fast-ssd"
                    }
                }
            },
            policies={
                "hpa": {
                    "enabled": True,
                    "description": "Horizontal Pod Autoscaler for GPU workloads",
                    "metrics": ["gpu_utilization", "inference_queue_size"]
                }
            }
        )

    def _generate_security_config(self) -> PatternConfig:
        """Generate security-specific configuration."""
        log_info("Generating security pattern configuration...")

        return PatternConfig(
            namespaces=[
                "vault",
                "cert-manager",
                "compliance-operator",
                "stackrox"
            ],
            subscriptions={
                "cert-manager": {
                    "namespace": "cert-manager",
                    "channel": "stable",
                    "source": "community-operators",
                    "description": "Certificate management for TLS"
                },
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
            },
            applications={
                "vault": {
                    "name": "vault",
                    "namespace": "vault",
                    "chart": "vault",
                    "repoURL": "https://charts.validatedpatterns.io",
                    "targetRevision": "0.1.0",
                    "description": "HashiCorp Vault for secrets management"
                }
            },
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
                },
                "rbac": {
                    "least_privilege": True,
                    "service_accounts_per_app": True
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
                },
                "image_scanning": {
                    "enabled": True,
                    "block_on_critical": True
                }
            }
        )

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
                }
            },
            resources={
                "hpa_defaults": {
                    "minReplicas": 2,
                    "maxReplicas": 20,
                    "targetCPUUtilizationPercentage": 70,
                    "targetMemoryUtilizationPercentage": 80,
                    "scaleDownStabilizationWindowSeconds": 300
                },
                "vpa_defaults": {
                    "updateMode": "Auto",
                    "resourcePolicy": {
                        "containerPolicies": [{
                            "minAllowed": {
                                "cpu": "100m",
                                "memory": "128Mi"
                            },
                            "maxAllowed": {
                                "cpu": "2",
                                "memory": "4Gi"
                            }
                        }]
                    }
                },
                "cluster_autoscaler": {
                    "enabled": True,
                    "scaleDownDelayAfterAdd": "10m",
                    "scaleDownUnneededTime": "10m",
                    "maxNodeProvisionTime": "15m"
                }
            },
            policies={
                "pod_disruption_budget": {
                    "minAvailable": "50%",
                    "description": "Ensure availability during scaling"
                },
                "resource_quotas": {
                    "enabled": True,
                    "defaults": {
                        "requests.cpu": "100",
                        "requests.memory": "200Gi",
                        "persistentvolumeclaims": "10"
                    }
                }
            }
        )

    def _generate_data_processing_config(self) -> PatternConfig:
        """Generate data processing pipeline configuration."""
        log_info("Generating data processing pattern configuration...")

        return PatternConfig(
            namespaces=[
                "kafka",
                "data-pipeline",
                "analytics"
            ],
            subscriptions={
                "amq-streams": {
                    "namespace": "kafka",
                    "channel": "stable",
                    "source": "redhat-operators",
                    "description": "Apache Kafka on OpenShift"
                }
            },
            applications={
                "kafka": {
                    "name": "kafka",
                    "namespace": "kafka",
                    "description": "Message streaming platform"
                }
            },
            resources={
                "kafka_config": {
                    "replicas": 3,
                    "storage": {
                        "type": "persistent-claim",
                        "size": "100Gi"
                    }
                },
                "pipeline_resources": {
                    "parallelism": 10,
                    "batch_size": 1000
                }
            },
            policies={
                "data_retention": {
                    "days": 7,
                    "compression": "snappy"
                }
            }
        )

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