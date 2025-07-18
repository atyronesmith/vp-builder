"""
Product detection module for extracting product information from Helm charts and manifests.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

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
            'registry.redhat.io/openshift4/ose-oauth-proxy': ('OAuth Proxy', 'OpenShift Component'),
            'registry.redhat.io/rhel8/postgresql': ('PostgreSQL', 'Database'),
            'registry.redhat.io/rhel8/redis': ('Redis', 'Cache'),
            'registry.redhat.io/amq7/amq-broker': ('Red Hat AMQ Broker', 'Messaging'),
            'registry.redhat.io/rh-sso-7/sso': ('Red Hat Single Sign-On', 'Authentication'),
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