"""
Tests for the analyzer module.
"""

from pathlib import Path

import pytest

from vpconverter.analyzer import PatternAnalyzer, HelmChart


def test_pattern_analyzer_initialization(temp_dir: Path):
    """Test PatternAnalyzer initialization."""
    analyzer = PatternAnalyzer(temp_dir)
    assert analyzer.source_path == temp_dir
    assert analyzer.result.source_path == temp_dir
    assert len(analyzer.result.helm_charts) == 0


def test_analyze_helm_charts(sample_repository: Path):
    """Test analyzing Helm charts in a repository."""
    analyzer = PatternAnalyzer(sample_repository)
    result = analyzer.analyze(verbose=False)

    # Should find the test chart
    assert len(result.helm_charts) == 1
    chart = result.helm_charts[0]
    assert chart.name == "test-chart"
    assert chart.version == "0.1.0"
    assert chart.has_values is True
    assert chart.has_templates is True
    assert chart.template_count > 0


def test_analyze_yaml_files(sample_repository: Path):
    """Test analyzing YAML files in a repository."""
    analyzer = PatternAnalyzer(sample_repository)
    result = analyzer.analyze(verbose=False)

    # Should find at least the app-config.yaml
    assert len(result.yaml_files) >= 1
    yaml_file_names = [f.name for f in result.yaml_files]
    assert "app-config.yaml" in yaml_file_names


def test_analyze_scripts(sample_repository: Path):
    """Test analyzing scripts in a repository."""
    analyzer = PatternAnalyzer(sample_repository)
    result = analyzer.analyze(verbose=False)

    # Should find the deploy.sh script
    assert len(result.script_files) == 1
    assert result.script_files[0].name == "deploy.sh"


def test_helm_chart_structure_analysis(sample_helm_chart: Path):
    """Test detailed Helm chart structure analysis."""
    analyzer = PatternAnalyzer(sample_helm_chart.parent)
    result = analyzer.analyze(verbose=True)

    assert len(result.helm_charts) == 1
    chart = result.helm_charts[0]

    # Check chart properties
    assert chart.chart_type == "application"
    assert chart.uses_helm_templates is True
    assert "deployment.yaml" in chart.templates_found


def test_site_structure_detection(temp_dir: Path):
    """Test detection of site-based organization."""
    # Create site directories
    (temp_dir / "hub").mkdir()
    (temp_dir / "region").mkdir()

    analyzer = PatternAnalyzer(temp_dir)
    result = analyzer.analyze(verbose=False)

    assert "hub" in result.site_directories
    assert "region" in result.site_directories
    assert len(result.site_directories) == 2


def test_pattern_detection(temp_dir: Path):
    """Test detection of existing patterns."""
    # Create files that indicate GitOps pattern
    gitops_file = temp_dir / "gitops-config.yaml"
    gitops_file.write_text("gitops: true")

    argo_file = temp_dir / "argocd-app.yaml"
    argo_file.write_text("kind: Application")

    analyzer = PatternAnalyzer(temp_dir)
    result = analyzer.analyze(verbose=False)

    assert "gitops" in result.detected_patterns
    assert "argocd" in result.detected_patterns