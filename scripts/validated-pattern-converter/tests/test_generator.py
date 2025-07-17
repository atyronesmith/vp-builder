"""
Tests for the generator module.
"""

from pathlib import Path

import pytest

from vpconverter.generator import PatternGenerator
from vpconverter.analyzer import AnalysisResult, HelmChart


def test_pattern_generator_initialization(temp_dir: Path):
    """Test PatternGenerator initialization."""
    generator = PatternGenerator("test-pattern", temp_dir, "test-org")
    assert generator.pattern_name == "test-pattern"
    assert generator.pattern_dir == temp_dir
    assert generator.github_org == "test-org"


def test_create_directories(temp_dir: Path):
    """Test directory structure creation."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")

    # Create empty analysis result
    analysis_result = AnalysisResult(source_path=temp_dir)

    # Generate pattern structure
    generator.generate(analysis_result)

    # Check key directories exist
    assert (pattern_dir / "ansible").exists()
    assert (pattern_dir / "charts" / "hub").exists()
    assert (pattern_dir / "charts" / "region").exists()
    assert (pattern_dir / "migrated-charts").exists()
    assert (pattern_dir / "scripts").exists()
    assert (pattern_dir / "tests" / "interop").exists()


def test_generate_base_files(temp_dir: Path):
    """Test generation of base configuration files."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")

    analysis_result = AnalysisResult(source_path=temp_dir)
    generator.generate(analysis_result)

    # Check required files exist
    assert (pattern_dir / ".gitignore").exists()
    assert (pattern_dir / "ansible.cfg").exists()
    assert (pattern_dir / "ansible" / "site.yaml").exists()
    assert (pattern_dir / "Makefile").exists()
    assert (pattern_dir / "pattern-metadata.yaml").exists()


def test_generate_values_files(temp_dir: Path):
    """Test generation of values files."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")

    # Create analysis result with a sample chart
    analysis_result = AnalysisResult(source_path=temp_dir)
    chart = HelmChart(
        name="sample-app",
        path=temp_dir / "sample-app",
        version="1.0.0"
    )
    analysis_result.helm_charts.append(chart)

    generator.generate(analysis_result)

    # Check values files exist
    assert (pattern_dir / "values-global.yaml").exists()
    assert (pattern_dir / "values-hub.yaml").exists()
    assert (pattern_dir / "values-region.yaml").exists()
    assert (pattern_dir / "values-secret.yaml.template").exists()

    # Check that helm chart is included in values-hub.yaml
    import yaml
    with open(pattern_dir / "values-hub.yaml", "r") as f:
        hub_values = yaml.safe_load(f)

    # Should have the sample-app namespace
    assert "sample-app" in hub_values["clusterGroup"]["namespaces"]


def test_generate_wrapper_chart(temp_dir: Path):
    """Test generation of ArgoCD wrapper charts."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")

    # Create pattern directory structure
    (pattern_dir / "charts" / "hub").mkdir(parents=True)

    # Create a sample chart
    chart = HelmChart(
        name="test-app",
        path=temp_dir / "test-app",
        version="2.0.0"
    )

    # Generate wrapper chart
    generator.generate_wrapper_chart(chart)

    # Check wrapper chart files
    wrapper_dir = pattern_dir / "charts" / "hub" / "test-app"
    assert (wrapper_dir / "Chart.yaml").exists()
    assert (wrapper_dir / "values.yaml").exists()
    assert (wrapper_dir / "templates" / "application.yaml").exists()

    # Verify Chart.yaml content
    import yaml
    with open(wrapper_dir / "Chart.yaml", "r") as f:
        chart_data = yaml.safe_load(f)

    assert chart_data["name"] == "test-app"
    assert "ArgoCD wrapper" in chart_data["description"]


def test_generate_documentation(temp_dir: Path):
    """Test generation of documentation files."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")

    analysis_result = AnalysisResult(source_path=temp_dir)
    generator.generate(analysis_result)

    # Check documentation files exist
    assert (pattern_dir / "README.md").exists()
    assert (pattern_dir / "CONVERSION-REPORT.md").exists()

    # Verify README content
    readme_content = (pattern_dir / "README.md").read_text()
    assert "test-pattern" in readme_content
    assert "test-org" in readme_content


def test_deep_merge(temp_dir: Path):
    """Test deep merge functionality."""
    generator = PatternGenerator("test", temp_dir)

    base = {
        "a": 1,
        "b": {"c": 2, "d": 3},
        "e": [1, 2, 3]
    }

    update = {
        "a": 10,
        "b": {"c": 20, "f": 4},
        "g": 5
    }

    result = generator._deep_merge(base, update)

    assert result["a"] == 10
    assert result["b"]["c"] == 20
    assert result["b"]["d"] == 3
    assert result["b"]["f"] == 4
    assert result["e"] == [1, 2, 3]
    assert result["g"] == 5