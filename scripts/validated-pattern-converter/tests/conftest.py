"""
Pytest configuration and fixtures for validated pattern converter tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_chart_yaml() -> dict:
    """Sample Chart.yaml content."""
    return {
        "apiVersion": "v2",
        "name": "test-chart",
        "description": "A test Helm chart",
        "type": "application",
        "version": "0.1.0",
        "appVersion": "1.16.0"
    }


@pytest.fixture
def sample_values_yaml() -> dict:
    """Sample values.yaml content."""
    return {
        "replicaCount": 1,
        "image": {
            "repository": "nginx",
            "pullPolicy": "IfNotPresent",
            "tag": ""
        },
        "service": {
            "type": "ClusterIP",
            "port": 80
        }
    }


@pytest.fixture
def sample_helm_chart(temp_dir: Path, sample_chart_yaml: dict, sample_values_yaml: dict) -> Path:
    """Create a sample Helm chart structure."""
    chart_dir = temp_dir / "test-chart"
    chart_dir.mkdir()

    # Create Chart.yaml
    with open(chart_dir / "Chart.yaml", "w") as f:
        yaml.dump(sample_chart_yaml, f)

    # Create values.yaml
    with open(chart_dir / "values.yaml", "w") as f:
        yaml.dump(sample_values_yaml, f)

    # Create templates directory
    templates_dir = chart_dir / "templates"
    templates_dir.mkdir()

    # Create a sample deployment template
    deployment_template = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "test-chart.fullname" . }}
  labels:
    {{- include "test-chart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "test-chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "test-chart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
"""

    with open(templates_dir / "deployment.yaml", "w") as f:
        f.write(deployment_template)

    return chart_dir


@pytest.fixture
def sample_repository(temp_dir: Path, sample_helm_chart: Path) -> Path:
    """Create a sample repository with Helm charts."""
    repo_dir = temp_dir / "sample-repo"
    repo_dir.mkdir()

    # Create helm directory
    helm_dir = repo_dir / "helm"
    helm_dir.mkdir()

    # Copy sample chart to helm directory
    import shutil
    shutil.copytree(sample_helm_chart, helm_dir / "test-chart")

    # Create some YAML files
    config_dir = repo_dir / "config"
    config_dir.mkdir()

    with open(config_dir / "app-config.yaml", "w") as f:
        yaml.dump({"app": {"name": "test-app", "version": "1.0.0"}}, f)

    # Create a script
    scripts_dir = repo_dir / "scripts"
    scripts_dir.mkdir()

    with open(scripts_dir / "deploy.sh", "w") as f:
        f.write("#!/bin/bash\necho 'Deploying application...'\n")

    return repo_dir