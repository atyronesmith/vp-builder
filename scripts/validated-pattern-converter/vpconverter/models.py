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