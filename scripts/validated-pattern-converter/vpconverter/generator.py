"""
Pattern generator for validated pattern converter.

This module generates the validated pattern directory structure
and configuration files based on analysis results.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from jinja2 import Environment, BaseLoader
import yaml

from .analyzer import AnalysisResult, HelmChart
from .config import PATTERN_DIRS, VERSION, CLUSTERGROUP_VERSION, DEFAULT_PRODUCTS
from .pattern_configurator import PatternConfigurator
from .product_detector import ProductDetector
from .templates import (
    GITIGNORE_TEMPLATE,
    ANSIBLE_CFG_TEMPLATE,
    ANSIBLE_SITE_TEMPLATE,
    MAKEFILE_TEMPLATE,
    PATTERN_METADATA_TEMPLATE,
    VALUES_GLOBAL_TEMPLATE,
    VALUES_HUB_TEMPLATE,
    VALUES_REGION_TEMPLATE,
    VALUES_SECRET_TEMPLATE,
    README_TEMPLATE,
    WRAPPER_CHART_TEMPLATE,
    WRAPPER_VALUES_TEMPLATE,
    ARGOCD_APPLICATION_TEMPLATE,
    VALIDATION_SCRIPT_TEMPLATE,
    CONVERSION_REPORT_TEMPLATE,
    CLUSTERGROUP_CHART_TEMPLATE,
    CLUSTERGROUP_VALUES_TEMPLATE,
    BOOTSTRAP_APPLICATION_TEMPLATE,
    PATTERN_INSTALL_SCRIPT_TEMPLATE,
    MAKEFILE_BOOTSTRAP_TEMPLATE,
    IMPERATIVE_JOB_TEMPLATE
)
from .utils import (
    log_info, log_success, log_error, log_warn,
    ensure_directory, write_yaml, console
)


class PatternGenerator:
    """Generates validated pattern structure and files."""

    def __init__(self, pattern_name: str, pattern_dir: Path, github_org: str = "your-org", source_dir: Optional[Path] = None):
        """Initialize generator with pattern configuration."""
        self.pattern_name = pattern_name
        self.pattern_dir = pattern_dir
        self.github_org = github_org
        self.source_dir = source_dir
        self.env = Environment(loader=BaseLoader())

    def generate(self, analysis_result: AnalysisResult) -> None:
        """Generate complete validated pattern structure."""
        log_info("Starting validated pattern generation...")

        with console.status("[bold green]Generating pattern structure...") as status:
            # Create directory structure
            status.update("Creating directory hierarchy...")
            self._create_directories()

            # Generate base configuration files
            status.update("Generating configuration files...")
            self._generate_base_files(analysis_result)

            # Generate values files
            status.update("Generating values files...")
            self._generate_values_files(analysis_result)

            # Generate ClusterGroup chart (CRITICAL)
            status.update("Generating ClusterGroup chart...")
            self._generate_clustergroup_chart()

            # Generate bootstrap application
            status.update("Generating bootstrap mechanism...")
            self._generate_bootstrap_files()

            # Apply pattern-specific configurations
            status.update("Applying pattern-specific configurations...")
            self._apply_pattern_configurations(analysis_result)

            # Generate scripts
            status.update("Generating validation scripts...")
            self._generate_scripts(analysis_result)

            # Generate documentation
            status.update("Generating documentation...")
            self._generate_documentation(analysis_result)

            # Create empty placeholder files
            status.update("Creating placeholder files...")
            self._create_placeholders()

        log_success(f"Pattern structure generated in: {self.pattern_dir}")

    def _create_directories(self) -> None:
        """Create the validated pattern directory structure."""
        for dir_path in PATTERN_DIRS:
            full_path = self.pattern_dir / dir_path
            ensure_directory(full_path)
            log_info(f"  ✓ Created: {dir_path}/")

    def _generate_base_files(self, analysis_result: AnalysisResult) -> None:
        """Generate base configuration files."""
        # .gitignore
        self._write_file(".gitignore", GITIGNORE_TEMPLATE)

        # ansible.cfg
        self._write_file("ansible.cfg", ANSIBLE_CFG_TEMPLATE)

        # ansible/site.yaml
        self._write_file("ansible/site.yaml", ANSIBLE_SITE_TEMPLATE)

        # Makefile - use bootstrap-enabled version
        self._write_file("Makefile", MAKEFILE_BOOTSTRAP_TEMPLATE)

        # pattern-metadata.yaml with products
        products = list(DEFAULT_PRODUCTS)

        # Use product detector to find pattern-specific products
        detector = ProductDetector()
        detected_products = []

        # Detect from Helm charts
        for chart in analysis_result.helm_charts:
            # Use the chart path directly from analysis result
            if Path(chart.path).exists():
                detected = detector.detect_from_path(Path(chart.path))
                detected_products.extend(detected)

        # Detect from any other YAML files
        for yaml_file in analysis_result.yaml_files:
            if yaml_file.exists():
                detected = detector.detect_from_path(yaml_file)
                detected_products.extend(detected)

        # Merge detected products with defaults
        final_products = detector.merge_products(products, detected_products)

        # Log detected products
        if detected_products:
            log_info(f"  ✓ Detected {len(detected_products)} additional products")
            for product in detected_products:
                confidence_marker = "" if product.confidence == "high" else f" ({product.confidence} confidence)"
                log_info(f"    - {product.name}: {product.version}{confidence_marker}")

        context = {
            "pattern_name": self.pattern_name,
            "github_org": self.github_org,
            "pattern_dir": self.pattern_dir.name,
            "products": final_products
        }
        self._render_and_write("pattern-metadata.yaml", PATTERN_METADATA_TEMPLATE, context)

    def _generate_values_files(self, analysis_result: AnalysisResult) -> None:
        """Generate values-*.yaml files."""
        # values-global.yaml
        context = {"pattern_name": self.pattern_name}
        self._render_and_write("values-global.yaml", VALUES_GLOBAL_TEMPLATE, context)

        # values-hub.yaml
        context = {
            "helm_charts": analysis_result.helm_charts,
            "pattern_name": self.pattern_name
        }
        self._render_and_write("values-hub.yaml", VALUES_HUB_TEMPLATE, context)

        # values-region.yaml
        self._write_file("values-region.yaml", VALUES_REGION_TEMPLATE)

        # values-secret.yaml.template
        self._write_file("values-secret.yaml.template", VALUES_SECRET_TEMPLATE)

    def _apply_pattern_configurations(self, analysis_result: AnalysisResult) -> None:
        """Apply pattern-specific configurations to values files."""
        # Initialize pattern configurator
        configurator = PatternConfigurator(analysis_result)

        # Generate pattern-specific configurations
        pattern_configs = configurator.generate_configurations()

        if pattern_configs:
            log_info("Detected patterns requiring specific configurations:")
            for pattern_name in pattern_configs:
                log_info(f"  • {pattern_name}")

            # Apply configurations to values-hub.yaml
            hub_values_file = self.pattern_dir / "values-hub.yaml"
            configurator.apply_to_values(hub_values_file, pattern_configs)

            # Generate resource files for each pattern
            configurator.generate_resource_files(self.pattern_dir, pattern_configs)

            # Update conversion report with pattern configurations
            self._update_report_with_patterns(pattern_configs)
        else:
            log_info("No specific pattern configurations needed")

    def _update_report_with_patterns(self, pattern_configs: Dict[str, Any]) -> None:
        """Update conversion report with pattern-specific configurations."""
        report_file = self.pattern_dir / "CONVERSION-REPORT.md"
        if report_file.exists():
            with open(report_file, 'a') as f:
                f.write("\n\n## Pattern-Specific Configurations Applied\n\n")
                for pattern_name, config in pattern_configs.items():
                    f.write(f"### {pattern_name.replace('_', ' ').title()}\n")
                    f.write(f"- Namespaces: {', '.join(config.namespaces)}\n")
                    f.write(f"- Operators: {len(config.subscriptions)}\n")
                    f.write(f"- Applications: {len(config.applications)}\n")
                    if config.resources:
                        f.write(f"- Resource configurations: {len(config.resources)}\n")
                    if config.policies:
                        f.write(f"- Policies: {len(config.policies)}\n")
                    f.write("\n")

    def _generate_scripts(self, analysis_result: AnalysisResult) -> None:
        """Generate utility scripts."""
        # Generate validation script
        namespace_list = ""
        app_list = ""

        if analysis_result.helm_charts:
            namespaces = [f" {chart.name}" for chart in analysis_result.helm_charts]
            namespace_list = "".join(namespaces)

            apps = [f" {chart.name}" for chart in analysis_result.helm_charts]
            app_list = "".join(apps)

        context = {
            "namespace_list": namespace_list,
            "app_list": app_list
        }

        script_path = self.pattern_dir / "scripts" / "validate-deployment.sh"
        self._render_and_write(
            "scripts/validate-deployment.sh",
            VALIDATION_SCRIPT_TEMPLATE,
            context
        )

        # Make script executable
        os.chmod(script_path, 0o755)

    def _generate_documentation(self, analysis_result: AnalysisResult) -> None:
        """Generate documentation files."""
        # README.md
        context = {
            "pattern_name": self.pattern_name,
            "github_org": self.github_org,
            "pattern_dir": self.pattern_dir.name,
            "helm_charts": analysis_result.helm_charts
        }
        self._render_and_write("README.md", README_TEMPLATE, context)

        # CONVERSION-REPORT.md
        context = {
            "pattern_name": self.pattern_name,
            "source_repo": str(analysis_result.source_path),
            "conversion_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": VERSION,
            "helm_charts_count": len(analysis_result.helm_charts),
            "yaml_files_count": len(analysis_result.yaml_files),
            "scripts_count": len(analysis_result.script_files),
            "detected_patterns": list(analysis_result.detected_patterns)
        }
        self._render_and_write("CONVERSION-REPORT.md", CONVERSION_REPORT_TEMPLATE, context)

    def _create_placeholders(self) -> None:
        """Create placeholder files for empty directories."""
        placeholders = [
            "overrides/.gitkeep",
            "tests/interop/.gitkeep"
        ]

        for placeholder in placeholders:
            file_path = self.pattern_dir / placeholder
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()

    def generate_wrapper_chart(self, chart: HelmChart, site: str = "hub") -> None:
        """Generate ArgoCD wrapper chart for a Helm chart."""
        wrapper_dir = self.pattern_dir / "charts" / site / chart.name
        ensure_directory(wrapper_dir / "templates")

        # Generate Chart.yaml
        context = {
            "chart_name": chart.name,
            "chart_version": chart.version
        }
        self._render_and_write(
            f"charts/{site}/{chart.name}/Chart.yaml",
            WRAPPER_CHART_TEMPLATE,
            context
        )

        # Generate values.yaml
        self._render_and_write(
            f"charts/{site}/{chart.name}/values.yaml",
            WRAPPER_VALUES_TEMPLATE,
            context
        )

        # Generate namespace template instead of application
        namespace_template = f"""\
apiVersion: v1
kind: Namespace
metadata:
  name: {chart.name}
  labels:
    argocd.argoproj.io/managed-by: openshift-gitops
  annotations:
    argocd.argoproj.io/sync-wave: "100"
"""
        self._write_file(
            f"charts/{site}/{chart.name}/templates/namespace.yaml",
            namespace_template
        )

        log_info(f"  ✓ Created wrapper chart: charts/{site}/{chart.name}/")

    def _generate_clustergroup_chart(self) -> None:
        """Generate the ClusterGroup chart that serves as the pattern entry point."""
        chart_dir = self.pattern_dir / "charts" / "hub" / "clustergroup"
        ensure_directory(chart_dir)
        ensure_directory(chart_dir / "templates")

        # Generate Chart.yaml
        context = {
            "pattern_name": self.pattern_name,
            "clustergroup_version": CLUSTERGROUP_VERSION
        }
        self._render_and_write(
            "charts/hub/clustergroup/Chart.yaml",
            CLUSTERGROUP_CHART_TEMPLATE,
            context
        )

        # Generate values.yaml
        context = {
            "pattern_name": self.pattern_name,
            "git_repo": f"https://github.com/{self.github_org}/{self.pattern_dir.name}",
            "target_revision": "main"
        }
        self._render_and_write(
            "charts/hub/clustergroup/values.yaml",
            CLUSTERGROUP_VALUES_TEMPLATE,
            context
        )

        # Create .gitkeep in templates directory
        (chart_dir / "templates" / ".gitkeep").touch()

        log_info("  ✓ Created ClusterGroup chart: charts/hub/clustergroup/")

    def _generate_bootstrap_files(self) -> None:
        """Generate bootstrap application and scripts."""
        # Create bootstrap directory
        bootstrap_dir = self.pattern_dir / "bootstrap"
        ensure_directory(bootstrap_dir)

        # Generate bootstrap application
        context = {
            "pattern_name": self.pattern_name,
            "git_repo": f"https://github.com/{self.github_org}/{self.pattern_dir.name}",
            "target_revision": "main"
        }
        self._render_and_write(
            "bootstrap/hub-bootstrap.yaml",
            BOOTSTRAP_APPLICATION_TEMPLATE,
            context
        )

        # Generate bootstrap script
        context = {
            "pattern_name": self.pattern_name
        }
        script_path = self.pattern_dir / "scripts" / "pattern-bootstrap.sh"
        self._render_and_write(
            "scripts/pattern-bootstrap.sh",
            PATTERN_INSTALL_SCRIPT_TEMPLATE,
            context
        )
        # Make script executable
        os.chmod(script_path, 0o755)

        log_info("  ✓ Created bootstrap mechanism")

    def _write_file(self, relative_path: str, content: str) -> None:
        """Write content to a file."""
        file_path = self.pattern_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(content)

        log_info(f"  ✓ Generated: {relative_path}")

    def _render_and_write(self, relative_path: str, template: str, context: Dict[str, Any]) -> None:
        """Render a Jinja2 template and write to file."""
        try:
            jinja_template = self.env.from_string(template)
            rendered = jinja_template.render(**context)
            self._write_file(relative_path, rendered)
        except Exception as e:
            log_error(f"Failed to render template for {relative_path}: {e}")
            raise

    def add_custom_values(self, values_file: str, custom_values: Dict[str, Any]) -> None:
        """Add custom values to a values file."""
        file_path = self.pattern_dir / values_file

        if file_path.exists():
            existing_values = yaml.safe_load(file_path.read_text()) or {}
            # Deep merge custom values
            merged_values = self._deep_merge(existing_values, custom_values)
            write_yaml(merged_values, file_path)
            log_info(f"  ✓ Updated {values_file} with custom values")
        else:
            log_warn(f"Values file not found: {values_file}")

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result