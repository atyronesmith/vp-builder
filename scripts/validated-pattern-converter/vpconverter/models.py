"""
Data models for validated pattern converter.

This module contains shared dataclasses used across the converter.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


@dataclass
class HelmChart:
    """Represents a Helm chart found in the repository."""
    name: str
    path: Path
    version: Optional[str] = None
    app_version: Optional[str] = None
    description: Optional[str] = None
    chart_type: str = "application"  # application or library
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    has_values: bool = False
    has_templates: bool = False
    template_count: int = 0
    uses_helm_templates: bool = False
    templates_found: List[str] = field(default_factory=list)
    enhanced_analysis: Optional[Any] = None  # Will be EnhancedChartAnalysis when available
    makefile_analysis: Optional[Any] = None  # Will be MakefileAnalysis when available


@dataclass
class ArchitecturePattern:
    """Represents a detected architecture pattern."""
    name: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ClusterGroupApplication:
    """Application definition for ClusterGroup"""
    name: str
    namespace: str
    project: str
    path: Optional[str] = None
    chart: Optional[str] = None
    chart_version: Optional[str] = None
    overrides: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ClusterGroupSubscription:
    """Subscription definition for ClusterGroup"""
    name: str
    namespace: str
    channel: str
    source: str = "redhat-operators"
    source_namespace: str = "openshift-marketplace"


@dataclass
class ManagedClusterGroup:
    """Managed cluster group definition"""
    name: str
    labels: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ClusterGroupData:
    """ClusterGroup configuration data"""
    name: str
    is_hub_cluster: bool
    namespaces: List[str]
    subscriptions: List[ClusterGroupSubscription]
    projects: List[str]
    applications: List[ClusterGroupApplication]
    managed_cluster_groups: List[ManagedClusterGroup] = field(default_factory=list)


@dataclass
class PatternData:
    """Complete pattern data for generation"""
    name: str
    description: str
    git_repo_url: str
    git_branch: str = "main"
    hub_cluster_domain: str = "apps.hub.example.com"
    local_cluster_domain: str = "apps.hub.example.com"
    namespaces: List[str] = field(default_factory=list)
    subscriptions: List[ClusterGroupSubscription] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    applications: List[ClusterGroupApplication] = field(default_factory=list)
    cluster_group_data: Optional[ClusterGroupData] = None


@dataclass
class AnalysisResult:
    """Results from repository analysis."""
    source_path: Path
    helm_charts: List[HelmChart] = field(default_factory=list)
    yaml_files: List[Path] = field(default_factory=list)
    script_files: List[Path] = field(default_factory=list)
    site_directories: List[str] = field(default_factory=list)
    has_kustomize: bool = False
    total_files: int = 0
    total_size: str = "0 B"
    detected_patterns: Set[str] = field(default_factory=set)
    enhanced_analysis: Optional[List[Any]] = None  # List of EnhancedChartAnalysis objects