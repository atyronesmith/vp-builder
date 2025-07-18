"""
Tests for the generator module.
"""

from pathlib import Path

import pytest

from vpconverter.generator import PatternGenerator
from vpconverter.analyzer import AnalysisResult, HelmChart
from vpconverter.models import PatternData, ClusterGroupApplication, ClusterGroupSubscription


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
    assert (wrapper_dir / "templates" / "namespace.yaml").exists()

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


def test_generate_clustergroup_chart(temp_dir: Path):
    """Test generation of ClusterGroup chart."""
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
    
    # Check ClusterGroup chart files
    clustergroup_dir = pattern_dir / "charts" / "hub" / "clustergroup"
    assert (clustergroup_dir / "Chart.yaml").exists()
    assert (clustergroup_dir / "values.yaml").exists()
    assert (clustergroup_dir / "templates" / ".gitkeep").exists()
    
    # Verify Chart.yaml content
    import yaml
    with open(clustergroup_dir / "Chart.yaml", "r") as f:
        chart_data = yaml.safe_load(f)
    
    assert chart_data["name"] == "test-pattern"
    assert "ClusterGroup chart" in chart_data["description"]
    assert len(chart_data["dependencies"]) == 1
    assert chart_data["dependencies"][0]["name"] == "clustergroup"
    assert chart_data["dependencies"][0]["repository"] == "https://charts.validatedpatterns.io"
    
    # Verify values.yaml content
    with open(clustergroup_dir / "values.yaml", "r") as f:
        values_data = yaml.safe_load(f)
    
    assert values_data["global"]["pattern"] == "test-pattern"
    assert values_data["clusterGroup"]["name"] == "hub"
    assert values_data["clusterGroup"]["isHubCluster"] is True
    
    # Check that sample-app namespace and application are included
    assert "sample-app" in values_data["clusterGroup"]["namespaces"]
    
    # Check that sample-app application is included
    sample_app_found = False
    for app in values_data["clusterGroup"]["applications"]:
        if app["name"] == "sample-app":
            sample_app_found = True
            assert app["namespace"] == "sample-app"
            assert app["project"] == "hub"
            assert app["path"] == "charts/hub/sample-app"
            break
    assert sample_app_found, "sample-app application not found in ClusterGroup applications"


def test_create_pattern_data(temp_dir: Path):
    """Test creation of PatternData from analysis result."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")
    
    # Create analysis result with multiple charts
    analysis_result = AnalysisResult(source_path=temp_dir)
    
    charts = [
        HelmChart(name="app1", path=temp_dir / "app1", version="1.0.0"),
        HelmChart(name="app2", path=temp_dir / "app2", version="2.0.0"),
    ]
    analysis_result.helm_charts = charts
    
    # Create pattern data
    pattern_data = generator._create_pattern_data(analysis_result)
    
    # Verify basic pattern data
    assert pattern_data.name == "test-pattern"
    assert pattern_data.git_repo_url == "https://github.com/test-org/test-pattern"
    assert pattern_data.git_branch == "main"
    
    # Verify default namespaces are included
    assert "open-cluster-management" in pattern_data.namespaces
    assert "openshift-gitops" in pattern_data.namespaces
    assert "external-secrets" in pattern_data.namespaces
    assert "vault" in pattern_data.namespaces
    
    # Verify chart namespaces are added
    assert "app1" in pattern_data.namespaces
    assert "app2" in pattern_data.namespaces
    
    # Verify default subscriptions
    assert len(pattern_data.subscriptions) >= 2
    gitops_sub = next((s for s in pattern_data.subscriptions if s.name == "openshift-gitops-operator"), None)
    assert gitops_sub is not None
    assert gitops_sub.namespace == "openshift-operators"
    assert gitops_sub.channel == "latest"
    
    acm_sub = next((s for s in pattern_data.subscriptions if s.name == "advanced-cluster-management"), None)
    assert acm_sub is not None
    assert acm_sub.namespace == "open-cluster-management"
    assert acm_sub.channel == "release-2.10"
    
    # Verify default and chart applications
    assert len(pattern_data.applications) >= 5  # 3 default + 2 from charts
    
    # Check chart applications
    app1_found = False
    app2_found = False
    for app in pattern_data.applications:
        if app.name == "app1":
            app1_found = True
            assert app.namespace == "app1"
            assert app.project == "hub"
            assert app.path == "charts/hub/app1"
        elif app.name == "app2":
            app2_found = True
            assert app.namespace == "app2"
            assert app.project == "hub"
            assert app.path == "charts/hub/app2"
    
    assert app1_found, "app1 application not found"
    assert app2_found, "app2 application not found"
    
    # Check default applications
    acm_app = next((a for a in pattern_data.applications if a.name == "acm"), None)
    assert acm_app is not None
    assert acm_app.path == "common/acm"
    
    vault_app = next((a for a in pattern_data.applications if a.name == "vault"), None)
    assert vault_app is not None
    assert vault_app.path == "common/hashicorp-vault"


def test_create_pattern_data_no_charts(temp_dir: Path):
    """Test creation of PatternData with no charts."""
    pattern_dir = temp_dir / "test-pattern"
    generator = PatternGenerator("test-pattern", pattern_dir, "test-org")
    
    # Create empty analysis result
    analysis_result = AnalysisResult(source_path=temp_dir)
    
    # Create pattern data
    pattern_data = generator._create_pattern_data(analysis_result)
    
    # Verify only default namespaces are included
    expected_namespaces = ["open-cluster-management", "openshift-gitops", "external-secrets", "vault"]
    assert pattern_data.namespaces == expected_namespaces
    
    # Verify only default applications are included
    default_app_names = ["acm", "vault", "golang-external-secrets"]
    actual_app_names = [app.name for app in pattern_data.applications]
    for default_name in default_app_names:
        assert default_name in actual_app_names