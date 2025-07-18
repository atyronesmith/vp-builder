"""
Configuration settings and constants for the validated pattern converter.
"""

from pathlib import Path
from typing import List, Dict, Any

# Version information
VERSION = "2.0.0"
DEFAULT_GITHUB_ORG = "your-org"

# Pattern structure directories
PATTERN_DIRS = [
    "ansible",
    "charts/hub",
    "charts/region",
    "charts/all",
    "common",
    "migrated-charts",
    "overrides",
    "scripts",
    "tests/interop",
    "bootstrap"
]

# Site patterns for detection
SITE_PATTERNS = ["hub", "region", "datacenter", "factory", "edge"]

# File patterns for searching
YAML_EXTENSIONS = [".yaml", ".yml"]
SCRIPT_EXTENSIONS = [".sh"]

# Chart analysis patterns
CHART_FILE = "Chart.yaml"
VALUES_FILE = "values.yaml"
TEMPLATES_DIR = "templates"
KUSTOMIZATION_FILE = "kustomization.yaml"

# Common Helm template files
COMMON_TEMPLATES = [
    "deployment.yaml",
    "service.yaml",
    "configmap.yaml",
    "route.yaml",
    "_helpers.tpl"
]

# GitOps sync wave annotations
SYNC_WAVES = {
    "operators": "200",
    "applications": "300",
    "configurations": "400"
}

# Default values for pattern configuration
DEFAULT_CHANNEL_CONFIG = {
    "gitops": {
        "namespace": "openshift-gitops",
        "channel": "latest",
        "source": "redhat-operators"
    },
    "acm": {
        "namespace": "open-cluster-management",
        "channel": "release-2.10",
        "source": "redhat-operators"
    }
}

# Common namespaces
COMMON_NAMESPACES = [
    "open-cluster-management",
    "openshift-gitops",
    "external-secrets",
    "vault"
]

# Pattern repository URLs
PATTERN_REPOS = {
    "common": "https://github.com/validatedpatterns-docs/common.git",
    "charts": "https://charts.validatedpatterns.io",
    "reference": "https://github.com/validatedpatterns/multicloud-gitops.git"
}

# Console output colors
COLORS = {
    "RED": "\033[0;31m",
    "GREEN": "\033[0;32m",
    "YELLOW": "\033[1;33m",
    "BLUE": "\033[0;34m",
    "NC": "\033[0m"  # No Color
}

# ClusterGroup and Pattern Install versions
CLUSTERGROUP_VERSION = "0.9.*"
PATTERN_INSTALL_VERSION = "0.0.*"

# Default products for validated patterns
DEFAULT_PRODUCTS = [
    {
        "name": "Red Hat OpenShift Container Platform",
        "version": "4.12+",
        "required": True
    },
    {
        "name": "Red Hat OpenShift GitOps",
        "version": "1.11.x",
        "operator": {
            "channel": "latest",
            "source": "redhat-operators"
        },
        "required": True
    },
    {
        "name": "Red Hat Advanced Cluster Management",
        "version": "2.10.x",
        "operator": {
            "channel": "release-2.10",
            "source": "redhat-operators"
        },
        "required": False
    }
]

# Logging configuration
LOGGING_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "level": "INFO"
}