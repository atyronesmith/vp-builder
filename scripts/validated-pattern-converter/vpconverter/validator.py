"""
Pattern validator for validated pattern converter.

This module validates the generated pattern structure and
configuration files to ensure they meet validated patterns standards.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml

from .config import PATTERN_DIRS, COMMON_NAMESPACES
from .utils import (
    log_info, log_warn, log_success, log_error,
    read_yaml, check_command_exists, run_command,
    console, create_summary_table
)


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add an info message to the validation result."""
        self.info.append(message)

    def print_summary(self) -> None:
        """Print a summary of the validation results."""
        if self.passed:
            console.print("\n[bold green]✓ Validation PASSED[/bold green]")
        else:
            console.print("\n[bold red]✗ Validation FAILED[/bold red]")

        if self.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in self.errors:
                console.print(f"  ✗ {error}")

        if self.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in self.warnings:
                console.print(f"  ⚠ {warning}")

        if self.info:
            console.print("\n[bold blue]Info:[/bold blue]")
            for info in self.info:
                console.print(f"  ℹ {info}")


class PatternValidator:
    """Validates pattern structure and configuration."""

    def __init__(self, pattern_dir: Path):
        """Initialize validator with pattern directory."""
        self.pattern_dir = pattern_dir
        self.result = ValidationResult()

    def validate(self, check_cluster: bool = False) -> ValidationResult:
        """Perform complete validation of the pattern."""
        log_info("Starting pattern validation...")

        with console.status("[bold green]Validating pattern...") as status:
            # Validate directory structure
            status.update("Checking directory structure...")
            self._validate_structure()

            # Validate required files
            status.update("Checking required files...")
            self._validate_required_files()

            # Validate YAML syntax
            status.update("Validating YAML files...")
            self._validate_yaml_files()

            # Validate Helm charts
            status.update("Validating Helm charts...")
            self._validate_helm_charts()

            # Validate values files
            status.update("Validating values files...")
            self._validate_values_files()

            # Validate product versions
            status.update("Validating product versions...")
            self._validate_product_versions()

            # Validate scripts
            status.update("Validating shell scripts...")
            self._validate_scripts()

            # Optional: Check cluster connectivity
            if check_cluster:
                status.update("Checking cluster connectivity...")
                self._validate_cluster_access()

        self.result.print_summary()
        return self.result

    def _validate_structure(self) -> None:
        """Validate the directory structure."""
        for dir_path in PATTERN_DIRS:
            full_path = self.pattern_dir / dir_path
            if not full_path.exists():
                self.result.add_error(f"Missing required directory: {dir_path}")
            else:
                self.result.add_info(f"Directory exists: {dir_path}")

    def _validate_required_files(self) -> None:
        """Validate that all required files exist."""
        required_files = [
            "Makefile",
            "ansible.cfg",
            "ansible/site.yaml",
            "pattern-metadata.yaml",
            "values-global.yaml",
            "values-hub.yaml",
            ".gitignore",
            "charts/hub/clustergroup/Chart.yaml",  # Critical: ClusterGroup chart
            "charts/hub/clustergroup/values.yaml",
            "bootstrap/hub-bootstrap.yaml"  # Bootstrap application
        ]

        for file_path in required_files:
            full_path = self.pattern_dir / file_path
            if not full_path.exists():
                if "clustergroup" in file_path:
                    self.result.add_error(f"CRITICAL: Missing ClusterGroup chart file: {file_path}")
                else:
                    self.result.add_error(f"Missing required file: {file_path}")
            else:
                self.result.add_info(f"File exists: {file_path}")

    def _validate_yaml_files(self) -> None:
        """Validate YAML syntax for all YAML files."""
        yaml_files = list(self.pattern_dir.rglob("*.yaml")) + list(self.pattern_dir.rglob("*.yml"))

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                rel_path = yaml_file.relative_to(self.pattern_dir)
                self.result.add_error(f"Invalid YAML in {rel_path}: {e}")
            except Exception as e:
                rel_path = yaml_file.relative_to(self.pattern_dir)
                self.result.add_warning(f"Could not read {rel_path}: {e}")

    def _validate_helm_charts(self) -> None:
        """Validate Helm charts in the pattern."""
        # Check migrated charts
        migrated_charts_dir = self.pattern_dir / "migrated-charts"
        if migrated_charts_dir.exists():
            charts = list(migrated_charts_dir.glob("*/Chart.yaml"))
            if charts:
                self.result.add_info(f"Found {len(charts)} migrated Helm charts")

                # Validate each chart if helm is available
                if check_command_exists("helm"):
                    for chart_file in charts:
                        chart_dir = chart_file.parent
                        self._validate_single_helm_chart(chart_dir)
                else:
                    self.result.add_warning("Helm CLI not found, skipping chart validation")
            else:
                self.result.add_warning("No Helm charts found in migrated-charts/")

        # Check wrapper charts
        for site in ["hub", "region"]:
            site_charts_dir = self.pattern_dir / "charts" / site
            if site_charts_dir.exists():
                wrapper_charts = list(site_charts_dir.glob("*/Chart.yaml"))
                if wrapper_charts:
                    self.result.add_info(f"Found {len(wrapper_charts)} wrapper charts in {site}/")

    def _validate_single_helm_chart(self, chart_dir: Path) -> None:
        """Validate a single Helm chart."""
        try:
            result = run_command(
                ["helm", "lint", str(chart_dir)],
                capture_output=True,
                check=False
            )

            if result.returncode == 0:
                self.result.add_info(f"Helm chart valid: {chart_dir.name}")
            else:
                # Parse helm lint output for specific issues
                if "WARNING" in result.stdout:
                    self.result.add_warning(f"Helm chart has warnings: {chart_dir.name}")
                else:
                    self.result.add_error(f"Helm chart validation failed: {chart_dir.name}")

        except Exception as e:
            self.result.add_warning(f"Could not validate chart {chart_dir.name}: {e}")

    def _validate_values_files(self) -> None:
        """Validate the structure of values files."""
        # Check values-global.yaml
        global_values = self.pattern_dir / "values-global.yaml"
        if global_values.exists():
            try:
                data = read_yaml(global_values)

                # Check required sections
                if "global" not in data:
                    self.result.add_error("values-global.yaml missing 'global' section")
                else:
                    if "pattern" not in data["global"]:
                        self.result.add_error("values-global.yaml missing 'global.pattern'")

                if "main" not in data:
                    self.result.add_error("values-global.yaml missing 'main' section")
                else:
                    if "clusterGroupName" not in data["main"]:
                        self.result.add_error("values-global.yaml missing 'main.clusterGroupName'")

            except Exception as e:
                self.result.add_error(f"Could not parse values-global.yaml: {e}")

        # Check values-hub.yaml
        hub_values = self.pattern_dir / "values-hub.yaml"
        if hub_values.exists():
            try:
                data = read_yaml(hub_values)

                if "clusterGroup" not in data:
                    self.result.add_error("values-hub.yaml missing 'clusterGroup' section")
                else:
                    cluster_group = data["clusterGroup"]

                    # Check required cluster group fields
                    required_fields = ["name", "isHubCluster", "namespaces", "applications"]
                    for field in required_fields:
                        if field not in cluster_group:
                            self.result.add_warning(f"values-hub.yaml missing 'clusterGroup.{field}'")

                    # Validate namespaces
                    if "namespaces" in cluster_group:
                        namespaces = cluster_group["namespaces"]
                        for required_ns in COMMON_NAMESPACES:
                            if required_ns not in namespaces:
                                self.result.add_warning(f"Missing recommended namespace: {required_ns}")

                    # Validate applications structure
                    if "applications" in cluster_group:
                        apps = cluster_group["applications"]
                        for app_name, app_config in apps.items():
                            if not isinstance(app_config, dict):
                                self.result.add_error(f"Invalid application config for {app_name}")
                            else:
                                # Check required app fields
                                required_app_fields = ["name", "namespace", "project", "path"]
                                for field in required_app_fields:
                                    if field not in app_config:
                                        self.result.add_error(
                                            f"Application {app_name} missing required field: {field}"
                                        )

            except Exception as e:
                self.result.add_error(f"Could not parse values-hub.yaml: {e}")

        # Validate pattern-metadata.yaml for products
        metadata_file = self.pattern_dir / "pattern-metadata.yaml"
        if metadata_file.exists():
            try:
                data = read_yaml(metadata_file)
                if "products" not in data:
                    self.result.add_error("pattern-metadata.yaml missing 'products' list (requirement #3)")
                else:
                    if not isinstance(data["products"], list) or len(data["products"]) == 0:
                        self.result.add_error("pattern-metadata.yaml must list at least one product")
            except Exception as e:
                self.result.add_error(f"Could not parse pattern-metadata.yaml: {e}")

    def _validate_scripts(self) -> None:
        """Validate shell scripts."""
        scripts_dir = self.pattern_dir / "scripts"
        if not scripts_dir.exists():
            return

        scripts = list(scripts_dir.glob("*.sh"))
        if not scripts:
            return

        self.result.add_info(f"Found {len(scripts)} shell scripts")

        # Check if shellcheck is available
        if check_command_exists("shellcheck"):
            for script in scripts:
                try:
                    result = run_command(
                        ["shellcheck", str(script)],
                        capture_output=True,
                        check=False
                    )

                    if result.returncode == 0:
                        self.result.add_info(f"Script valid: {script.name}")
                    else:
                        self.result.add_warning(f"Script has issues: {script.name}")

                except Exception as e:
                    self.result.add_warning(f"Could not validate script {script.name}: {e}")
        else:
            self.result.add_info("ShellCheck not found, skipping script validation")

    def _validate_cluster_access(self) -> None:
        """Validate OpenShift cluster access."""
        if not check_command_exists("oc"):
            self.result.add_warning("OpenShift CLI (oc) not found")
            return

        try:
            # Check if logged in
            result = run_command(["oc", "whoami"], capture_output=True, check=False)

            if result.returncode == 0:
                user = result.stdout.strip()
                self.result.add_info(f"Logged in to cluster as: {user}")

                # Check cluster version
                version_result = run_command(
                    ["oc", "version", "--short"],
                    capture_output=True,
                    check=False
                )

                if version_result.returncode == 0:
                    self.result.add_info(f"Cluster version: {version_result.stdout.strip()}")

            else:
                self.result.add_warning("Not logged in to OpenShift cluster")

        except Exception as e:
            self.result.add_warning(f"Could not check cluster access: {e}")

    def _validate_product_versions(self) -> None:
        """Validate product versions in pattern metadata."""
        metadata_file = self.pattern_dir / "pattern-metadata.yaml"
        
        if not metadata_file.exists():
            self.result.add_warning("Pattern metadata file not found")
            return

        try:
            metadata = read_yaml(metadata_file)
            if not metadata:
                self.result.add_warning("Pattern metadata file is empty")
                return

            products = metadata.get('products', [])
            if not products:
                self.result.add_info("No products specified in pattern metadata")
                return

            # Validate each product entry
            for i, product in enumerate(products):
                if not isinstance(product, dict):
                    self.result.add_error(f"Product entry {i} is not a dictionary")
                    continue

                # Required fields
                name = product.get('name')
                version = product.get('version')
                
                if not name:
                    self.result.add_error(f"Product entry {i} missing 'name' field")
                elif not isinstance(name, str):
                    self.result.add_error(f"Product entry {i} 'name' must be a string")

                if not version:
                    self.result.add_error(f"Product entry {i} missing 'version' field")
                elif not isinstance(version, str):
                    self.result.add_error(f"Product entry {i} 'version' must be a string")

                # Optional fields validation
                source = product.get('source')
                confidence = product.get('confidence')
                operator_info = product.get('operator')

                if source and not isinstance(source, str):
                    self.result.add_warning(f"Product '{name}' source should be a string")

                if confidence and confidence not in ['high', 'medium', 'low']:
                    self.result.add_warning(f"Product '{name}' confidence should be 'high', 'medium', or 'low'")

                if operator_info:
                    if not isinstance(operator_info, dict):
                        self.result.add_warning(f"Product '{name}' operator info should be a dictionary")
                    else:
                        # Validate operator fields
                        channel = operator_info.get('channel')
                        operator_source = operator_info.get('source')
                        subscription = operator_info.get('subscription')

                        if channel and not isinstance(channel, str):
                            self.result.add_warning(f"Product '{name}' operator channel should be a string")
                        
                        if operator_source and not isinstance(operator_source, str):
                            self.result.add_warning(f"Product '{name}' operator source should be a string")
                        
                        if subscription and not isinstance(subscription, str):
                            self.result.add_warning(f"Product '{name}' operator subscription should be a string")

                # Validate version format for known patterns
                if version and version not in ['latest', 'stable', 'unknown']:
                    if not self._is_valid_version_format(version):
                        self.result.add_warning(f"Product '{name}' version '{version}' may not be a valid version format")

            self.result.add_info(f"Validated {len(products)} product entries")

        except Exception as e:
            self.result.add_error(f"Error validating product versions: {e}")

    def _is_valid_version_format(self, version: str) -> bool:
        """Check if version follows common version format patterns."""
        # Common version patterns:
        # - Semantic versioning: 1.2.3, 1.2.3-beta, 1.2.3+build
        # - Release versions: 4.14.x, 2.10.x
        # - Channel names: stable, alpha, beta
        # - Range indicators: 4.x, 2.10.x
        
        import re
        
        patterns = [
            r'^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?(\+[a-zA-Z0-9-]+)?$',  # Semantic versioning
            r'^\d+\.\d+\.x$',  # Release with .x
            r'^\d+\.x$',       # Major version with .x
            r'^(stable|alpha|beta|latest|release)-\d+\.\d+$',  # Channel with version
            r'^(stable|alpha|beta|latest)$',  # Simple channel names
        ]
        
        return any(re.match(pattern, version) for pattern in patterns)

    def validate_deployment(self) -> bool:
        """Validate a deployed pattern on the cluster."""
        if not check_command_exists("oc"):
            log_error("OpenShift CLI (oc) not found")
            return False

        log_info("Validating deployed pattern...")

        # Check required namespaces
        for namespace in COMMON_NAMESPACES:
            try:
                result = run_command(
                    ["oc", "get", "namespace", namespace],
                    capture_output=True,
                    check=False
                )

                if result.returncode == 0:
                    log_success(f"✓ Namespace exists: {namespace}")
                else:
                    log_error(f"✗ Namespace missing: {namespace}")

            except Exception as e:
                log_error(f"Error checking namespace {namespace}: {e}")

        # Check GitOps operator
        try:
            result = run_command(
                ["oc", "get", "csv", "-n", "openshift-operators"],
                capture_output=True,
                check=False
            )

            if result.returncode == 0 and "openshift-gitops" in result.stdout:
                log_success("✓ GitOps operator installed")
            else:
                log_error("✗ GitOps operator not found")

        except Exception as e:
            log_error(f"Error checking GitOps operator: {e}")

        return True