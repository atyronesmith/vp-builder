"""
Product detection module for extracting product information from Helm charts and manifests.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from .models import ProductVersion, AnalysisResult

@dataclass
class DetectedProduct:
    """Represents a detected product with its metadata."""
    name: str
    version: str
    operator: Optional[Dict[str, str]] = None
    source: str = "detected"  # Where it was detected from
    confidence: str = "high"  # high, medium, low

class ProductDetector:
    """Detects products and their versions from Helm charts and Kubernetes manifests."""

    # Known operator mappings to official product names
    OPERATOR_PRODUCT_MAP = {
        # Red Hat Operators
        "openshift-gitops-operator": {
            "name": "Red Hat OpenShift GitOps",
            "default_channel": "latest"
        },
        "advanced-cluster-management": {
            "name": "Red Hat Advanced Cluster Management",
            "default_channel": "release-2.10"
        },
        "odf-operator": {
            "name": "Red Hat OpenShift Data Foundation",
            "default_channel": "stable-4.14"
        },
        "kubevirt-hyperconverged": {
            "name": "Red Hat OpenShift Virtualization",
            "default_channel": "stable"
        },
        "amq-streams": {
            "name": "Red Hat AMQ Streams",
            "default_channel": "stable"
        },
        "ansible-automation-platform-operator": {
            "name": "Red Hat Ansible Automation Platform",
            "default_channel": "stable-2.4"
        },
        "rhacs-operator": {
            "name": "Red Hat Advanced Cluster Security",
            "default_channel": "stable"
        },
        "elasticsearch-operator": {
            "name": "Red Hat OpenShift Elasticsearch Operator",
            "default_channel": "stable"
        },
        "cluster-logging": {
            "name": "Red Hat OpenShift Logging",
            "default_channel": "stable"
        },
        "serverless-operator": {
            "name": "Red Hat OpenShift Serverless",
            "default_channel": "stable"
        },
        "service-mesh": {
            "name": "Red Hat OpenShift Service Mesh",
            "default_channel": "stable"
        },
        "jaeger-product": {
            "name": "Red Hat OpenShift distributed tracing platform",
            "default_channel": "stable"
        },
        "kiali-ossm": {
            "name": "Red Hat OpenShift Service Mesh - Kiali",
            "default_channel": "stable"
        },
        # AI/ML and GPU Operators
        "nfd": {
            "name": "Node Feature Discovery",
            "default_channel": "stable"
        },
        "gpu-operator-certified": {
            "name": "NVIDIA GPU Operator",
            "default_channel": "stable"
        },
        "rhods-operator": {
            "name": "Red Hat OpenShift AI",
            "default_channel": "stable"
        },
        "cloud-native-postgresql": {
            "name": "EDB PostgreSQL Operator",
            "default_channel": "stable"
        },
        "elasticsearch-eck-operator-certified": {
            "name": "Elastic Cloud on Kubernetes",
            "default_channel": "stable"
        },
        "servicemeshoperator": {
            "name": "Red Hat OpenShift Service Mesh",
            "default_channel": "stable"
        },
        "ray-operator": {
            "name": "Ray Operator for ML",
            "default_channel": "alpha"
        },
        "kubeflow-operator": {
            "name": "Kubeflow Operator",
            "default_channel": "stable"
        },
        "seldon-operator": {
            "name": "Seldon Core Operator",
            "default_channel": "stable"
        },
        "nvidia-network-operator": {
            "name": "NVIDIA Network Operator",
            "default_channel": "stable"
        },
        "gpu-feature-discovery": {
            "name": "GPU Feature Discovery",
            "default_channel": "stable"
        },
        # Community Operators
        "argocd-operator": {
            "name": "Argo CD (Community)",
            "default_channel": "alpha"
        },
        "grafana-operator": {
            "name": "Grafana Operator (Community)",
            "default_channel": "v4"
        },
        "prometheus": {
            "name": "Prometheus Operator (Community)",
            "default_channel": "beta"
        },
        "cert-manager": {
            "name": "cert-manager",
            "default_channel": "stable"
        },
        "vault": {
            "name": "HashiCorp Vault",
            "default_channel": "stable"
        }
    }

    # Version extraction patterns
    VERSION_PATTERNS = {
        "channel": re.compile(r'(release-|stable-|v)?(\d+\.?\d*\.?\d*)', re.IGNORECASE),
        "csv": re.compile(r'\.v?(\d+\.\d+\.\d+)'),
        "image": re.compile(r':v?(\d+\.\d+(?:\.\d+)?)')
    }

    def __init__(self):
        self.detected_products: Dict[str, DetectedProduct] = {}

    def detect_from_path(self, path: Path) -> List[DetectedProduct]:
        """Detect products from a given path (file or directory)."""
        if path.is_file():
            return self._detect_from_file(path)
        elif path.is_dir():
            products = []
            for yaml_file in path.rglob("*.yaml"):
                products.extend(self._detect_from_file(yaml_file))
            for yml_file in path.rglob("*.yml"):
                products.extend(self._detect_from_file(yml_file))
            return products
        return []

    def _detect_from_file(self, file_path: Path) -> List[DetectedProduct]:
        """Detect products from a single YAML file."""
        products = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Handle multi-document YAML
            for doc in yaml.safe_load_all(content):
                if not doc:
                    continue

                # Check for Subscription resources
                if doc.get('kind') == 'Subscription':
                    product = self._extract_from_subscription(doc, str(file_path))
                    if product:
                        products.append(product)

                # Check for CSV references
                elif doc.get('kind') == 'ClusterServiceVersion':
                    product = self._extract_from_csv(doc, str(file_path))
                    if product:
                        products.append(product)

                # Check for known images
                elif 'spec' in doc and 'containers' in doc.get('spec', {}).get('template', {}).get('spec', {}):
                    detected = self._extract_from_containers(
                        doc['spec']['template']['spec']['containers'],
                        str(file_path)
                    )
                    products.extend(detected)

        except Exception as e:
            # Silently skip files that can't be parsed
            pass

        return products

    def _extract_from_subscription(self, subscription: Dict, source: str) -> Optional[DetectedProduct]:
        """Extract product information from a Subscription resource."""
        spec = subscription.get('spec', {})
        name = spec.get('name', '')
        channel = spec.get('channel', '')
        source_name = spec.get('source', 'redhat-operators')
        starting_csv = spec.get('startingCSV', '')

        # Look up in our known operators
        if name in self.OPERATOR_PRODUCT_MAP:
            product_info = self.OPERATOR_PRODUCT_MAP[name]
            version = self._extract_version_from_channel(channel) or "latest"

            return DetectedProduct(
                name=product_info['name'],
                version=version,
                operator={
                    'channel': channel or product_info['default_channel'],
                    'source': source_name,
                    'subscription': name
                },
                source=f"subscription:{source}",
                confidence="high"
            )
        else:
            # Unknown operator - make best guess
            version = self._extract_version_from_channel(channel) or \
                     self._extract_version_from_csv(starting_csv) or \
                     "unknown"

            # Clean up the name for display
            display_name = name.replace('-operator', '').replace('-', ' ').title()

            return DetectedProduct(
                name=f"{display_name} (Operator)",
                version=version,
                operator={
                    'channel': channel,
                    'source': source_name,
                    'subscription': name
                },
                source=f"subscription:{source}",
                confidence="low"
            )

    def _extract_from_csv(self, csv: Dict, source: str) -> Optional[DetectedProduct]:
        """Extract product information from a ClusterServiceVersion."""
        metadata = csv.get('metadata', {})
        spec = csv.get('spec', {})

        name = spec.get('displayName', metadata.get('name', ''))
        version = spec.get('version', '')

        if not version:
            # Try to extract from metadata name
            version = self._extract_version_from_csv(metadata.get('name', ''))

        if name and version:
            return DetectedProduct(
                name=name,
                version=version or "unknown",
                source=f"csv:{source}",
                confidence="medium"
            )
        return None

    def _extract_from_containers(self, containers: List[Dict], source: str) -> List[DetectedProduct]:
        """Extract products from container images."""
        products = []

        # Known image patterns to product mapping
        image_patterns = {
            # OpenShift Core Components
            'registry.redhat.io/openshift4/ose-oauth-proxy': ('OAuth Proxy', 'OpenShift Component'),
            'registry.redhat.io/rhel8/postgresql': ('PostgreSQL', 'Database'),
            'registry.redhat.io/rhel8/redis': ('Redis', 'Cache'),
            'registry.redhat.io/amq7/amq-broker': ('Red Hat AMQ Broker', 'Messaging'),
            'registry.redhat.io/rh-sso-7/sso': ('Red Hat Single Sign-On', 'Authentication'),
            
            # AI/ML and Inference Services
            'quay.io/vllm/vllm-openai': ('vLLM OpenAI Server', 'AI/ML Inference'),
            'ghcr.io/huggingface/text-generation-inference': ('Hugging Face TGI', 'AI/ML Inference'),
            'nvcr.io/nvidia/tritonserver': ('NVIDIA Triton', 'AI/ML Inference'),
            'quay.io/modh/odh-notebook': ('OpenShift AI Notebook', 'AI/ML Development'),
            'quay.io/opendatahub/kubeflow': ('Kubeflow', 'ML Pipeline'),
            'quay.io/ray/ray': ('Ray Distributed Computing', 'ML Framework'),
            'nvcr.io/nvidia/pytorch': ('PyTorch NVIDIA', 'ML Framework'),
            'nvcr.io/nvidia/tensorflow': ('TensorFlow NVIDIA', 'ML Framework'),
            'quay.io/seldon/seldon-core': ('Seldon Core', 'ML Serving'),
            
            # Vector Databases and ML Storage
            'docker.io/pgvector/pgvector': ('pgvector PostgreSQL', 'Vector Database'),
            'redis/redis-stack-server': ('Redis Stack', 'Vector Database'),
            'docker.elastic.co/elasticsearch/elasticsearch': ('Elasticsearch', 'Vector Database'),
            'quay.io/minio/minio': ('MinIO', 'Object Storage'),
            
            # GPU and Hardware Acceleration
            'nvcr.io/nvidia/k8s-device-plugin': ('NVIDIA Device Plugin', 'GPU Management'),
            'nvcr.io/nvidia/gpu-feature-discovery': ('GPU Feature Discovery', 'GPU Management'),
            'nvcr.io/nvidia/driver': ('NVIDIA Driver', 'GPU Driver'),
            
            # Monitoring and Observability for AI/ML
            'quay.io/prometheus/prometheus': ('Prometheus', 'Monitoring'),
            'grafana/grafana': ('Grafana', 'Visualization'),
            'quay.io/jaegertracing/jaeger': ('Jaeger', 'Distributed Tracing'),
            
            # Authentication and Security
            'quay.io/keycloak/keycloak': ('Keycloak', 'Authentication'),
            'docker.io/bitnami/postgresql': ('PostgreSQL', 'Database'),
            'docker.io/bitnami/redis': ('Redis', 'Cache'),
        }

        for container in containers:
            image = container.get('image', '')
            for pattern, (product_name, category) in image_patterns.items():
                if pattern in image:
                    version_match = self.VERSION_PATTERNS['image'].search(image)
                    version = version_match.group(1) if version_match else "latest"

                    products.append(DetectedProduct(
                        name=f"{product_name} ({category})",
                        version=version,
                        source=f"image:{source}",
                        confidence="medium"
                    ))
                    break

        return products

    def _extract_version_from_channel(self, channel: str) -> Optional[str]:
        """Extract version from channel name."""
        if not channel:
            return None

        # Direct version channels
        if channel in ['latest', 'stable', 'alpha', 'beta']:
            return channel

        # Versioned channels like "release-2.10" or "stable-4.14"
        match = self.VERSION_PATTERNS['channel'].search(channel)
        if match:
            return match.group(2) + ".x"

        return None

    def _extract_version_from_csv(self, csv_name: str) -> Optional[str]:
        """Extract version from CSV name."""
        if not csv_name:
            return None

        match = self.VERSION_PATTERNS['csv'].search(csv_name)
        if match:
            return match.group(1)

        return None

    def merge_products(self, default_products: List[Dict], detected_products: List[DetectedProduct]) -> List[Dict]:
        """Merge detected products with defaults, avoiding duplicates."""
        # Convert defaults to a dict by name for easy lookup
        products_by_name: Dict[str, Dict] = {p['name']: p for p in default_products}

        # Add detected products
        for detected in detected_products:
            product_name = detected.name  # Ensure it's a string
            if product_name not in products_by_name:
                # New product
                product_dict = {
                    'name': detected.name,
                    'version': detected.version
                }
                if detected.operator:
                    product_dict['operator'] = detected.operator

                # Add confidence marker for low confidence detections
                if detected.confidence == "low":
                    product_dict['name'] = f"{detected.name} # TODO: Verify product name"
                    product_dict['version'] = f"{detected.version} # TODO: Verify version"

                products_by_name[product_name] = product_dict
            else:
                # Update version if we have better information
                if detected.confidence == "high" and detected.version != "unknown":
                    products_by_name[product_name]['version'] = detected.version
                    if detected.operator:
                        products_by_name[product_name]['operator'] = detected.operator

        # Convert back to list and sort
        final_products = list(products_by_name.values())

        # Sort: Required products first, then alphabetically
        def sort_key(p):
            # OpenShift and GitOps always first
            if "OpenShift Container Platform" in p['name']:
                return (0, p['name'])
            elif "OpenShift GitOps" in p['name']:
                return (1, p['name'])
            else:
                return (2, p['name'])

        final_products.sort(key=sort_key)

        return final_products

    def detect_product_versions(self, analysis_result: AnalysisResult) -> List[ProductVersion]:
        """Detect product versions from analysis result."""
        products = []
        
        # OpenShift version detection
        ocp_version = self._detect_openshift_version(analysis_result)
        if ocp_version:
            products.append(ProductVersion(
                name="OpenShift Container Platform",
                version=ocp_version,
                source="cluster_analysis",
                confidence="high"
            ))
        
        # Operator version detection from manifests
        operator_versions = self._detect_operator_versions(analysis_result)
        products.extend(operator_versions)
        
        # Helm chart version detection
        chart_versions = self._detect_chart_versions(analysis_result)
        products.extend(chart_versions)
        
        # Detect from files in source path
        if hasattr(analysis_result, 'source_path'):
            detected_products = self.detect_from_path(analysis_result.source_path)
            for dp in detected_products:
                # Convert DetectedProduct to ProductVersion
                pv = ProductVersion(
                    name=dp.name,
                    version=dp.version,
                    source=dp.source,
                    confidence=dp.confidence,
                    operator_info=dp.operator
                )
                products.append(pv)
        
        # Remove duplicates and consolidate
        return self._consolidate_product_versions(products)

    def _detect_openshift_version(self, analysis_result: AnalysisResult) -> Optional[str]:
        """Detect OpenShift version from various sources."""
        
        # Check for version in cluster info if available
        if hasattr(analysis_result, 'cluster_info') and analysis_result.cluster_info:
            cluster_version = analysis_result.cluster_info.get('version')
            if cluster_version:
                return cluster_version
        
        # Check for version in Kubernetes manifests
        if hasattr(analysis_result, 'kubernetes_manifests'):
            for manifest in analysis_result.kubernetes_manifests:
                if manifest.get('apiVersion') == 'config.openshift.io/v1':
                    if manifest.get('kind') == 'ClusterVersion':
                        spec = manifest.get('spec', {})
                        desired_update = spec.get('desiredUpdate', {})
                        version = desired_update.get('version')
                        if version:
                            return version
                
                # Check for OpenShift-specific API versions to infer version range
                api_version = manifest.get('apiVersion', '')
                if 'openshift.io' in api_version:
                    # Basic heuristic - if we see OpenShift APIs, assume 4.x
                    return "4.x"
        
        # Check for OpenShift-specific configuration in Helm charts
        for chart in analysis_result.helm_charts:
            if self._chart_suggests_openshift_version(chart):
                return "4.x"  # Default assumption for modern charts
        
        return None

    def _detect_operator_versions(self, analysis_result: AnalysisResult) -> List[ProductVersion]:
        """Detect operator versions from subscriptions and CSVs."""
        products = []
        
        # Check YAML files for Subscription and CSV resources
        for yaml_file in analysis_result.yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    content = f.read()
                
                for doc in yaml.safe_load_all(content):
                    if not doc:
                        continue
                    
                    if doc.get('kind') == 'Subscription':
                        product = self._extract_product_from_subscription(doc, str(yaml_file))
                        if product:
                            products.append(product)
                    
                    elif doc.get('kind') == 'ClusterServiceVersion':
                        product = self._extract_product_from_csv(doc, str(yaml_file))
                        if product:
                            products.append(product)
            
            except Exception:
                # Skip files that can't be parsed
                continue
        
        # Check for ClusterGroup subscription configurations in values files
        clustergroup_products = self._detect_clustergroup_subscriptions(analysis_result)
        products.extend(clustergroup_products)
        
        return products

    def _detect_chart_versions(self, analysis_result: AnalysisResult) -> List[ProductVersion]:
        """Detect versions from Helm charts."""
        products = []
        
        for chart in analysis_result.helm_charts:
            # Chart itself as a product
            if chart.version:
                products.append(ProductVersion(
                    name=f"{chart.name} (Helm Chart)",
                    version=chart.version,
                    source=f"chart:{chart.path}",
                    confidence="high"
                ))
            
            # App version if different from chart version
            if chart.app_version and chart.app_version != chart.version:
                products.append(ProductVersion(
                    name=f"{chart.name} Application",
                    version=chart.app_version,
                    source=f"chart:{chart.path}",
                    confidence="medium"
                ))
            
            # Dependencies
            for dep in chart.dependencies:
                if dep.get('version'):
                    products.append(ProductVersion(
                        name=f"{dep.get('name', 'Unknown')} (Dependency)",
                        version=dep['version'],
                        source=f"chart_dependency:{chart.path}",
                        confidence="medium"
                    ))
        
        return products

    def _extract_product_from_subscription(self, subscription: Dict, source: str) -> Optional[ProductVersion]:
        """Extract ProductVersion from a Subscription resource."""
        spec = subscription.get('spec', {})
        name = spec.get('name', '')
        channel = spec.get('channel', '')
        source_name = spec.get('source', 'redhat-operators')
        starting_csv = spec.get('startingCSV', '')

        # Look up in our known operators
        if name in self.OPERATOR_PRODUCT_MAP:
            product_info = self.OPERATOR_PRODUCT_MAP[name]
            version = self._extract_version_from_channel(channel) or "latest"

            return ProductVersion(
                name=product_info['name'],
                version=version,
                source=f"subscription:{source}",
                confidence="high",
                operator_info={
                    'channel': channel or product_info['default_channel'],
                    'source': source_name,
                    'subscription': name
                }
            )
        else:
            # Unknown operator - make best guess
            version = self._extract_version_from_channel(channel) or \
                     self._extract_version_from_csv(starting_csv) or \
                     "unknown"

            # Clean up the name for display
            display_name = name.replace('-operator', '').replace('-', ' ').title()

            return ProductVersion(
                name=f"{display_name} (Operator)",
                version=version,
                source=f"subscription:{source}",
                confidence="low",
                operator_info={
                    'channel': channel,
                    'source': source_name,
                    'subscription': name
                }
            )

    def _extract_product_from_csv(self, csv: Dict, source: str) -> Optional[ProductVersion]:
        """Extract ProductVersion from a ClusterServiceVersion."""
        metadata = csv.get('metadata', {})
        spec = csv.get('spec', {})

        name = spec.get('displayName', metadata.get('name', ''))
        version = spec.get('version', '')

        if not version:
            # Try to extract from metadata name
            version = self._extract_version_from_csv(metadata.get('name', ''))

        if name and version:
            return ProductVersion(
                name=name,
                version=version or "unknown",
                source=f"csv:{source}",
                confidence="medium"
            )
        return None

    def _chart_suggests_openshift_version(self, chart) -> bool:
        """Check if a chart suggests a specific OpenShift version."""
        # Check chart metadata and templates for OpenShift-specific features
        if hasattr(chart, 'templates_found'):
            openshift_resources = [
                'Route', 'DeploymentConfig', 'BuildConfig', 'ImageStream',
                'SecurityContextConstraints', 'Project'
            ]
            for template in chart.templates_found:
                if any(resource in template for resource in openshift_resources):
                    return True
        
        return False

    def _consolidate_product_versions(self, products: List[ProductVersion]) -> List[ProductVersion]:
        """Remove duplicates and consolidate product versions."""
        # Use a dict to track unique products by name
        consolidated: Dict[str, ProductVersion] = {}
        
        for product in products:
            existing = consolidated.get(product.name)
            if not existing:
                consolidated[product.name] = product
            else:
                # Keep the one with higher confidence
                if (product.confidence == "high" and existing.confidence != "high") or \
                   (product.confidence == "medium" and existing.confidence == "low"):
                    consolidated[product.name] = product
                elif product.confidence == existing.confidence and product.version != "unknown":
                    # Same confidence, prefer non-unknown version
                    if existing.version == "unknown":
                        consolidated[product.name] = product
        
        # Convert back to list and sort
        result = list(consolidated.values())
        result.sort(key=lambda p: (0 if "OpenShift" in p.name else 1, p.name))
        
        return result

    def _detect_clustergroup_subscriptions(self, analysis_result: AnalysisResult) -> List[ProductVersion]:
        """Detect operator subscriptions from ClusterGroup values files."""
        products = []
        
        # Look for values files that might contain ClusterGroup configurations
        values_files = [
            'values-hub.yaml',
            'values-global.yaml', 
            'values-region.yaml'
        ]
        
        for values_filename in values_files:
            values_path = analysis_result.source_path / values_filename
            if values_path.exists():
                try:
                    with open(values_path, 'r') as f:
                        values_content = yaml.safe_load(f)
                    
                    if not values_content:
                        continue
                    
                    # Look for clusterGroup.subscriptions
                    cluster_group = values_content.get('clusterGroup', {})
                    subscriptions = cluster_group.get('subscriptions', {})
                    
                    for sub_key, sub_config in subscriptions.items():
                        if isinstance(sub_config, dict):
                            operator_name = sub_config.get('name', sub_key)
                            namespace = sub_config.get('namespace', 'openshift-operators')
                            channel = sub_config.get('channel', 'stable')
                            source = sub_config.get('source', 'redhat-operators')
                            
                            # Create mock subscription for extraction
                            mock_subscription = {
                                'kind': 'Subscription',
                                'spec': {
                                    'name': operator_name,
                                    'channel': channel,
                                    'source': source,
                                    'namespace': namespace
                                }
                            }
                            
                            product = self._extract_product_from_subscription(
                                mock_subscription, 
                                f"clustergroup:{values_filename}"
                            )
                            if product:
                                # Mark as ClusterGroup source for better identification
                                product.source = f"clustergroup:{values_filename}"
                                products.append(product)
                
                except Exception as e:
                    # Skip files that can't be parsed
                    continue
        
        return products