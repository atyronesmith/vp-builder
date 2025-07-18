"""
Validated Pattern Converter

A tool to convert OpenShift/Kubernetes projects into Red Hat Validated Patterns.
"""

__version__ = "2.0.0"
__author__ = "Validated Patterns Team"
__email__ = "validated-patterns@redhat.com"

from .analyzer import PatternAnalyzer
from .generator import PatternGenerator
from .migrator import HelmMigrator
from .validator import PatternValidator
from .rules_engine import RuleEngine, DetectionRule, PatternDefinition

__all__ = [
    "PatternAnalyzer",
    "PatternGenerator",
    "HelmMigrator",
    "PatternValidator",
    "RuleEngine",
    "DetectionRule",
    "PatternDefinition",
]