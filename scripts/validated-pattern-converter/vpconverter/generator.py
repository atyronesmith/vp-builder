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
from .models import PatternData, ClusterGroupData, ClusterGroupApplication, ClusterGroupSubscription
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
            self._generate_clustergroup_chart(analysis_result)

            # Generate wrapper charts for discovered Helm charts
            status.update("Generating wrapper charts...")
            for chart in analysis_result.helm_charts:
                self.generate_wrapper_chart(chart, site="all")

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

            # Generate platform overrides
            status.update("Generating platform overrides...")
            self._generate_platform_overrides()

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

        # Makefile with pattern name context
        context = {"pattern_name": self.pattern_name}
        self._render_and_write("Makefile", MAKEFILE_TEMPLATE, context)

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

        # Create enhanced pattern metadata context
        context = {
            "pattern_name": self.pattern_name,
            "pattern_display_name": self.pattern_name.replace('-', ' ').title() + " Pattern",
            "pattern_description": f"Validated pattern for {self.pattern_name.replace('-', ' ')} deployment on OpenShift using GitOps",
            "github_org": self.github_org,
            "pattern_dir": self.pattern_dir.name,
            "products": final_products,
            "categories": self._detect_categories(analysis_result),
            "languages": self._detect_languages(analysis_result),
            "industries": self._detect_industries(analysis_result),
            "detected_patterns": list(analysis_result.detected_patterns) if hasattr(analysis_result, 'detected_patterns') else [],
            "creation_date": datetime.now().isoformat()
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
        context = {
            "helm_charts": analysis_result.helm_charts,
            "pattern_name": self.pattern_name
        }
        self._render_and_write("values-region.yaml", VALUES_REGION_TEMPLATE, context)

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

    def generate_wrapper_chart(self, chart: HelmChart, site: str = "all") -> None:
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

    def _generate_clustergroup_chart(self, analysis_result: Optional[AnalysisResult] = None) -> None:
        """Generate the ClusterGroup chart that serves as the pattern entry point."""
        chart_dir = self.pattern_dir / "charts" / "hub" / "clustergroup"
        ensure_directory(chart_dir)
        ensure_directory(chart_dir / "templates")

        # Create pattern data from analysis result
        pattern_data = self._create_pattern_data(analysis_result)

        # Generate Chart.yaml
        context = {
            "pattern_name": self.pattern_name,
            "description": f"ClusterGroup chart for {self.pattern_name} pattern",
            "clustergroup_version": CLUSTERGROUP_VERSION
        }
        self._render_and_write(
            "charts/hub/clustergroup/Chart.yaml",
            CLUSTERGROUP_CHART_TEMPLATE,
            context
        )

        # Generate values.yaml with full pattern data
        context = {
            "pattern_name": pattern_data.name,
            "git_repo_url": pattern_data.git_repo_url,
            "git_branch": pattern_data.git_branch,
            "hub_cluster_domain": pattern_data.hub_cluster_domain,
            "local_cluster_domain": pattern_data.local_cluster_domain,
            "namespaces": pattern_data.namespaces,
            "subscriptions": pattern_data.subscriptions,
            "projects": pattern_data.projects,
            "applications": pattern_data.applications
        }
        self._render_and_write(
            "charts/hub/clustergroup/values.yaml",
            CLUSTERGROUP_VALUES_TEMPLATE,
            context
        )

        # Create .gitkeep in templates directory
        (chart_dir / "templates" / ".gitkeep").touch()

        log_info("  ✓ Created ClusterGroup chart: charts/hub/clustergroup/")

    def _create_pattern_data(self, analysis_result: Optional[AnalysisResult] = None) -> PatternData:
        """Create PatternData from analysis result and pattern configuration."""
        # Base pattern data
        pattern_data = PatternData(
            name=self.pattern_name,
            description=f"Validated pattern for {self.pattern_name}",
            git_repo_url=f"https://github.com/{self.github_org}/{self.pattern_dir.name}",
            git_branch="main",
            hub_cluster_domain="apps.hub.example.com",
            local_cluster_domain="apps.hub.example.com"
        )

        # Add default namespaces
        pattern_data.namespaces = [
            "open-cluster-management",
            "openshift-gitops",
            "external-secrets",
            "vault",
            "golang-external-secrets"
        ]

        # Add default subscriptions
        pattern_data.subscriptions = [
            ClusterGroupSubscription(
                name="openshift-gitops-operator",
                namespace="openshift-operators",
                channel="latest"
            ),
            ClusterGroupSubscription(
                name="advanced-cluster-management",
                namespace="open-cluster-management",
                channel="release-2.10"
            )
        ]

        # Add default projects
        pattern_data.projects = ["hub"]

        # Add default applications
        pattern_data.applications = [
            ClusterGroupApplication(
                name="acm",
                namespace="open-cluster-management",
                project="hub",
                path="common/acm"
            ),
            ClusterGroupApplication(
                name="vault",
                namespace="vault",
                project="hub",
                path="common/hashicorp-vault"
            ),
            ClusterGroupApplication(
                name="golang-external-secrets",
                namespace="golang-external-secrets",
                project="hub",
                path="common/golang-external-secrets"
            )
        ]

        # Add applications from analysis result
        if analysis_result:
            for chart in analysis_result.helm_charts:
                # Add namespace for each chart
                pattern_data.namespaces.append(chart.name)
                
                # Add project for each chart
                pattern_data.projects.append(chart.name)
                
                # Add application for each chart
                pattern_data.applications.append(
                    ClusterGroupApplication(
                        name=chart.name,
                        namespace=chart.name,
                        project=chart.name,
                        path=f"charts/all/{chart.name}"
                    )
                )
            
            # Detect product versions
            product_detector = ProductDetector()
            detected_products = product_detector.detect_product_versions(analysis_result)
            pattern_data.products = detected_products

        return pattern_data

    def _generate_bootstrap_files(self) -> None:
        """Generate bootstrap application and common framework integration."""
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

        # Generate pattern.sh symlink target
        pattern_sh_content = """\
#!/bin/bash
# This file should be a symlink to common/scripts/pattern-util.sh
# If you see this message, the common framework is not set up correctly.

echo "ERROR: pattern.sh is not properly linked to common framework"
echo ""
echo "To fix this, run:"
echo "  git clone https://github.com/validatedpatterns/common.git"
echo "  ln -sf common/scripts/pattern-util.sh pattern.sh"
echo ""
echo "For more information: https://validatedpatterns.io/patterns/"
exit 1
"""
        pattern_sh_path = self.pattern_dir / "pattern.sh"
        self._write_file("pattern.sh", pattern_sh_content)
        os.chmod(pattern_sh_path, 0o755)

        # Generate setup script for common framework
        setup_script = f"""\
#!/bin/bash
set -euo pipefail

# Setup script for {self.pattern_name} pattern
echo "Setting up {self.pattern_name} pattern..."

# Check if common directory exists
if [ ! -d "common" ]; then
    echo "Cloning common framework..."
    git clone https://github.com/validatedpatterns/common.git
else
    echo "Common framework already exists"
fi

# Create pattern.sh symlink
if [ ! -L "pattern.sh" ]; then
    echo "Creating pattern.sh symlink..."
    ln -sf common/scripts/pattern-util.sh pattern.sh
    chmod +x pattern.sh
else
    echo "pattern.sh symlink already exists"
fi

# Check if values-secret.yaml exists
if [ ! -f "values-secret.yaml" ]; then
    if [ -f "values-secret.yaml.template" ]; then
        echo "Creating values-secret.yaml from template..."
        cp values-secret.yaml.template values-secret.yaml
        echo "Please edit values-secret.yaml with your actual secrets"
    else
        echo "WARNING: No values-secret.yaml.template found"
    fi
else
    echo "values-secret.yaml already exists"
fi

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit values-secret.yaml with your actual secrets"
echo "2. Run: make install"
echo ""
echo "For more information: https://validatedpatterns.io/patterns/"
"""
        setup_script_path = self.pattern_dir / "scripts" / "setup.sh"
        self._write_file("scripts/setup.sh", setup_script)
        os.chmod(setup_script_path, 0o755)

        log_info("  ✓ Created bootstrap mechanism and common framework integration")

    def _detect_categories(self, analysis_result: AnalysisResult) -> List[str]:
        """Detect pattern categories based on analysis."""
        categories = ["gitops", "kubernetes"]
        
        # Add categories based on detected patterns
        if hasattr(analysis_result, 'detected_patterns'):
            pattern_set = analysis_result.detected_patterns
            if "AI/ML Pipeline" in pattern_set:
                categories.extend(["ai", "machine-learning", "data"])
            if "Security" in pattern_set:
                categories.append("security")
            if "Scaling" in pattern_set:
                categories.append("scalability")
            if "Data Processing" in pattern_set:
                categories.extend(["data", "analytics"])
            if "MLOps" in pattern_set:
                categories.extend(["mlops", "devops"])
        
        # Add categories based on chart names
        for chart in analysis_result.helm_charts:
            chart_name = chart.name.lower()
            if any(keyword in chart_name for keyword in ["web", "ui", "frontend"]):
                categories.append("web")
            if any(keyword in chart_name for keyword in ["api", "service", "backend"]):
                categories.append("microservices")
            if any(keyword in chart_name for keyword in ["data", "analytics", "metrics"]):
                categories.append("data")
        
        return list(set(categories))  # Remove duplicates

    def _detect_languages(self, analysis_result: AnalysisResult) -> List[str]:
        """Detect programming languages used in the pattern."""
        languages = ["yaml", "helm"]
        
        # Check for common language patterns in chart names
        for chart in analysis_result.helm_charts:
            chart_name = chart.name.lower()
            if any(keyword in chart_name for keyword in ["python", "py", "flask", "django"]):
                languages.append("python")
            if any(keyword in chart_name for keyword in ["node", "js", "express", "react", "angular"]):
                languages.extend(["javascript", "nodejs"])
            if any(keyword in chart_name for keyword in ["java", "spring", "tomcat"]):
                languages.append("java")
            if any(keyword in chart_name for keyword in ["go", "golang"]):
                languages.append("go")
            if any(keyword in chart_name for keyword in ["rust", "rs"]):
                languages.append("rust")
        
        return list(set(languages))  # Remove duplicates

    def _detect_industries(self, analysis_result: AnalysisResult) -> List[str]:
        """Detect industries this pattern applies to."""
        industries = ["technology", "cloud-computing"]
        
        # Add industries based on detected patterns
        if hasattr(analysis_result, 'detected_patterns'):
            pattern_set = analysis_result.detected_patterns
            if "AI/ML Pipeline" in pattern_set or "MLOps" in pattern_set:
                industries.extend(["artificial-intelligence", "data-science"])
            if "Security" in pattern_set:
                industries.extend(["cybersecurity", "compliance"])
            if "Data Processing" in pattern_set:
                industries.extend(["data-analytics", "business-intelligence"])
        
        # Add industries based on chart names and functionality
        for chart in analysis_result.helm_charts:
            chart_name = chart.name.lower()
            if any(keyword in chart_name for keyword in ["finance", "banking", "payment"]):
                industries.append("financial-services")
            if any(keyword in chart_name for keyword in ["health", "medical", "patient"]):
                industries.append("healthcare")
            if any(keyword in chart_name for keyword in ["retail", "ecommerce", "shop"]):
                industries.append("retail")
            if any(keyword in chart_name for keyword in ["manufacturing", "iot", "sensor"]):
                industries.append("manufacturing")
        
        return list(set(industries))  # Remove duplicates

    def _generate_platform_overrides(self) -> None:
        """Generate platform-specific override files."""
        # Create platform override files for common platforms
        platforms = ["AWS", "Azure", "GCP", "IBMCloud", "OpenStack"]
        
        for platform in platforms:
            platform_overrides = f"""\
# Platform-specific overrides for {platform}
# Add platform-specific configurations here

global:
  clusterPlatform: {platform.lower()}
  
# Example platform-specific configurations:
# storageClass: {platform.lower()}-storage
# domainSuffix: {platform.lower()}.example.com
"""
            self._write_file(f"overrides/values-{platform}.yaml", platform_overrides)
            log_info(f"  ✓ Created platform override: overrides/values-{platform}.yaml")

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