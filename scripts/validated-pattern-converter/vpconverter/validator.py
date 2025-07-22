"""
Pattern validator for validated pattern converter.

This module validates the generated pattern structure and
configuration files to ensure they meet validated patterns standards.
"""

import os
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

    def validate_pattern_compliance(self, check_cluster: bool = False) -> ValidationResult:
        """Validate pattern compliance with validated patterns requirements."""
        log_info("Starting comprehensive pattern compliance validation...")

        with console.status("[bold green]Validating pattern compliance...") as status:
            # Validate ClusterGroup chart exists and is correct
            status.update("Validating ClusterGroup chart...")
            self._validate_clustergroup_chart()

            # Validate values structure compliance
            status.update("Validating values structure compliance...")
            self._validate_values_structure_compliance()

            # Validate bootstrap application
            status.update("Validating bootstrap application...")
            self._validate_bootstrap_application()

            # Validate common framework integration
            status.update("Validating common framework integration...")
            self._validate_common_framework()

            # Run standard validation as well
            status.update("Running standard validation checks...")
            self._validate_structure()
            self._validate_required_files()
            self._validate_yaml_files()
            self._validate_helm_charts()
            self._validate_values_files()
            self._validate_product_versions()
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

    def _validate_clustergroup_chart(self) -> None:
        """Validate ClusterGroup chart exists and is correct."""
        # Check for pattern-specific ClusterGroup chart
        pattern_name = self.pattern_dir.name
        clustergroup_path = self.pattern_dir / "charts" / "hub" / pattern_name
        
        if not clustergroup_path.exists():
            # Try alternative path with 'clustergroup' name
            clustergroup_path = self.pattern_dir / "charts" / "hub" / "clustergroup"
            if not clustergroup_path.exists():
                self.result.add_error(
                    f"CRITICAL: ClusterGroup chart missing. Expected at charts/hub/{pattern_name}/ or charts/hub/clustergroup/"
                )
                return
        
        # Validate Chart.yaml
        chart_yaml = clustergroup_path / "Chart.yaml"
        if not chart_yaml.exists():
            self.result.add_error(f"ClusterGroup Chart.yaml missing at {chart_yaml.relative_to(self.pattern_dir)}")
            return
        
        try:
            chart_content = read_yaml(chart_yaml)
            
            # Validate chart metadata
            if not chart_content:
                self.result.add_error("ClusterGroup Chart.yaml is empty")
                return
                
            if "name" not in chart_content:
                self.result.add_error("ClusterGroup Chart.yaml missing 'name'")
            elif chart_content["name"] != pattern_name and chart_content["name"] != "clustergroup":
                self.result.add_warning(f"ClusterGroup chart name '{chart_content['name']}' doesn't match pattern name '{pattern_name}'")
            
            # Check for clustergroup dependency
            dependencies = chart_content.get('dependencies', [])
            has_clustergroup_dep = any(
                dep.get('name') == 'clustergroup' 
                for dep in dependencies
            )
            
            if not has_clustergroup_dep:
                self.result.add_error("ClusterGroup chart missing 'clustergroup' dependency")
            else:
                # Validate dependency configuration
                for dep in dependencies:
                    if dep.get('name') == 'clustergroup':
                        if 'repository' not in dep:
                            self.result.add_error("ClusterGroup dependency missing 'repository'")
                        elif not dep['repository'].startswith(('https://', 'http://', 'file://')):
                            self.result.add_warning(f"ClusterGroup dependency repository may be invalid: {dep['repository']}")
                        
                        if 'version' not in dep:
                            self.result.add_error("ClusterGroup dependency missing 'version'")
        
        except Exception as e:
            self.result.add_error(f"Error validating ClusterGroup Chart.yaml: {e}")
        
        # Validate ClusterGroup values.yaml
        values_yaml = clustergroup_path / "values.yaml"
        if not values_yaml.exists():
            self.result.add_error(f"ClusterGroup values.yaml missing at {values_yaml.relative_to(self.pattern_dir)}")
        else:
            try:
                values_content = read_yaml(values_yaml)
                if values_content:
                    # ClusterGroup values.yaml should typically be empty or minimal
                    # as configuration comes from parent values files
                    self.result.add_info("ClusterGroup values.yaml exists and is valid")
                    
            except Exception as e:
                self.result.add_error(f"Error validating ClusterGroup values.yaml: {e}")
        
        # Check templates directory
        templates_dir = clustergroup_path / "templates"
        if templates_dir.exists() and any(templates_dir.iterdir()):
            # ClusterGroup charts typically shouldn't have templates
            # as they rely on the clustergroup dependency
            template_count = len(list(templates_dir.glob("*.yaml")))
            if template_count > 0:
                self.result.add_warning(
                    f"ClusterGroup chart has {template_count} templates. "
                    "ClusterGroup charts typically rely on the dependency and don't need custom templates."
                )
        
        self.result.add_info("ClusterGroup chart validation completed")

    def _validate_values_structure_compliance(self) -> None:
        """Validate values files structure matches validated patterns requirements."""
        # Validate values-global.yaml
        global_values = self.pattern_dir / "values-global.yaml"
        if not global_values.exists():
            self.result.add_error("CRITICAL: values-global.yaml missing")
            return
        
        try:
            global_data = read_yaml(global_values)
            if not global_data:
                self.result.add_error("values-global.yaml is empty")
                return
            
            # Required sections in values-global.yaml
            if "global" not in global_data:
                self.result.add_error("values-global.yaml missing required 'global' section")
            else:
                global_section = global_data["global"]
                
                # Check required global fields
                if "pattern" not in global_section:
                    self.result.add_error("values-global.yaml missing 'global.pattern'")
                
                if "options" not in global_section:
                    self.result.add_warning("values-global.yaml missing 'global.options' section")
                else:
                    options = global_section["options"]
                    # Check standard options
                    expected_options = ["useCSV", "syncPolicy", "installPlanApproval"]
                    for opt in expected_options:
                        if opt not in options:
                            self.result.add_info(f"Consider adding 'global.options.{opt}' for standard behavior")
            
            if "main" not in global_data:
                self.result.add_error("values-global.yaml missing required 'main' section")
            else:
                main_section = global_data["main"]
                if "clusterGroupName" not in main_section:
                    self.result.add_error("values-global.yaml missing 'main.clusterGroupName'")
                else:
                    # Validate clusterGroupName matches expected patterns
                    cluster_group_name = main_section["clusterGroupName"]
                    if cluster_group_name not in ["hub", "region", "edge"]:
                        self.result.add_warning(
                            f"Unusual clusterGroupName '{cluster_group_name}'. "
                            "Standard values are: hub, region, edge"
                        )
            
            # Check for gitOpsSpec (should NOT be in values-global per standard)
            if "gitOpsSpec" in global_data:
                self.result.add_warning(
                    "values-global.yaml contains 'gitOpsSpec' section. "
                    "This is typically handled by the common framework."
                )
                
        except Exception as e:
            self.result.add_error(f"Error parsing values-global.yaml: {e}")
        
        # Validate values-hub.yaml
        hub_values = self.pattern_dir / "values-hub.yaml"
        if not hub_values.exists():
            self.result.add_error("CRITICAL: values-hub.yaml missing")
            return
            
        try:
            hub_data = read_yaml(hub_values)
            if not hub_data:
                self.result.add_error("values-hub.yaml is empty")
                return
            
            if "clusterGroup" not in hub_data:
                self.result.add_error("values-hub.yaml missing required 'clusterGroup' section")
            else:
                cluster_group = hub_data["clusterGroup"]
                
                # Required ClusterGroup fields
                required_fields = {
                    "name": "hub",
                    "isHubCluster": True,
                }
                
                for field, expected in required_fields.items():
                    if field not in cluster_group:
                        self.result.add_error(f"values-hub.yaml missing 'clusterGroup.{field}'")
                    elif field == "name" and cluster_group[field] != expected:
                        self.result.add_warning(
                            f"values-hub.yaml clusterGroup.name is '{cluster_group[field]}', expected '{expected}'"
                        )
                    elif field == "isHubCluster" and cluster_group[field] != expected:
                        self.result.add_error(
                            f"values-hub.yaml clusterGroup.isHubCluster must be true for hub cluster"
                        )
                
                # Validate namespaces structure
                if "namespaces" not in cluster_group:
                    self.result.add_error("values-hub.yaml missing 'clusterGroup.namespaces'")
                else:
                    namespaces = cluster_group["namespaces"]
                    if not isinstance(namespaces, list):
                        self.result.add_error("clusterGroup.namespaces must be a list")
                    else:
                        # Check for required namespaces
                        required_namespaces = ["openshift-gitops", "vault", "golang-external-secrets"]
                        for ns in required_namespaces:
                            if ns not in namespaces:
                                self.result.add_warning(f"Missing recommended namespace: {ns}")
                
                # Validate subscriptions structure
                if "subscriptions" in cluster_group:
                    subscriptions = cluster_group["subscriptions"]
                    if not isinstance(subscriptions, list):
                        self.result.add_error("clusterGroup.subscriptions must be a list")
                    else:
                        for sub in subscriptions:
                            if isinstance(sub, dict):
                                required_sub_fields = ["name", "namespace"]
                                for field in required_sub_fields:
                                    if field not in sub:
                                        self.result.add_error(
                                            f"Subscription missing required field '{field}': {sub.get('name', 'unnamed')}"
                                        )
                
                # Validate applications structure
                if "applications" not in cluster_group:
                    self.result.add_error("values-hub.yaml missing 'clusterGroup.applications'")
                else:
                    apps = cluster_group["applications"]
                    if not isinstance(apps, dict):
                        self.result.add_error("clusterGroup.applications must be a dictionary")
                    else:
                        for app_name, app_config in apps.items():
                            if not isinstance(app_config, dict):
                                self.result.add_error(f"Application '{app_name}' configuration must be a dictionary")
                            else:
                                # Required fields for each application
                                required_app_fields = ["name", "namespace", "project", "path"]
                                for field in required_app_fields:
                                    if field not in app_config:
                                        self.result.add_error(
                                            f"Application '{app_name}' missing required field: {field}"
                                        )
                                
                                # Validate path structure
                                if "path" in app_config:
                                    path = app_config["path"]
                                    if not path.startswith(("charts/", "common/")):
                                        self.result.add_warning(
                                            f"Application '{app_name}' path '{path}' doesn't follow standard pattern. "
                                            "Expected to start with 'charts/' or 'common/'"
                                        )
                
                # Validate sharedValueFiles
                if "sharedValueFiles" in cluster_group:
                    shared_files = cluster_group["sharedValueFiles"]
                    if not isinstance(shared_files, list):
                        self.result.add_error("clusterGroup.sharedValueFiles must be a list")
                
        except Exception as e:
            self.result.add_error(f"Error parsing values-hub.yaml: {e}")
        
        # Check for values-region.yaml (optional but recommended)
        region_values = self.pattern_dir / "values-region.yaml"
        if region_values.exists():
            try:
                region_data = read_yaml(region_values)
                if region_data and "clusterGroup" in region_data:
                    cluster_group = region_data["clusterGroup"]
                    
                    # Region cluster should not be hub
                    if cluster_group.get("isHubCluster", False):
                        self.result.add_error("values-region.yaml should have isHubCluster: false")
                    
                    if cluster_group.get("name") != "region":
                        self.result.add_warning(
                            f"values-region.yaml has unexpected name '{cluster_group.get('name')}', expected 'region'"
                        )
                        
            except Exception as e:
                self.result.add_warning(f"Error parsing values-region.yaml: {e}")
        else:
            self.result.add_info("values-region.yaml not found (optional file)")
        
        # Check for platform-specific values files
        platform_files = ["values-aws.yaml", "values-azure.yaml", "values-gcp.yaml"]
        found_platform_files = []
        for platform_file in platform_files:
            if (self.pattern_dir / platform_file).exists():
                found_platform_files.append(platform_file)
        
        if found_platform_files:
            self.result.add_info(f"Found platform-specific values files: {', '.join(found_platform_files)}")
        
        self.result.add_info("Values structure compliance validation completed")

    def _validate_bootstrap_application(self) -> None:
        """Validate bootstrap application for pattern deployment."""
        bootstrap_dir = self.pattern_dir / "bootstrap"
        
        if not bootstrap_dir.exists():
            self.result.add_error("CRITICAL: bootstrap/ directory missing")
            return
        
        # Check for hub-bootstrap.yaml
        hub_bootstrap = bootstrap_dir / "hub-bootstrap.yaml"
        if not hub_bootstrap.exists():
            self.result.add_error("CRITICAL: bootstrap/hub-bootstrap.yaml missing")
            return
        
        try:
            bootstrap_data = read_yaml(hub_bootstrap)
            if not bootstrap_data:
                self.result.add_error("hub-bootstrap.yaml is empty")
                return
            
            # Validate it's an ArgoCD Application
            if bootstrap_data.get("apiVersion") != "argoproj.io/v1alpha1":
                self.result.add_error(f"hub-bootstrap.yaml has incorrect apiVersion: {bootstrap_data.get('apiVersion')}")
            
            if bootstrap_data.get("kind") != "Application":
                self.result.add_error(f"hub-bootstrap.yaml has incorrect kind: {bootstrap_data.get('kind')}")
            
            # Validate metadata
            metadata = bootstrap_data.get("metadata", {})
            if not metadata:
                self.result.add_error("hub-bootstrap.yaml missing metadata")
            else:
                if "name" not in metadata:
                    self.result.add_error("hub-bootstrap.yaml missing metadata.name")
                else:
                    # Name should match pattern
                    expected_name = f"{self.pattern_dir.name}-hub"
                    if metadata["name"] != expected_name:
                        self.result.add_warning(
                            f"Bootstrap application name '{metadata['name']}' doesn't match expected '{expected_name}'"
                        )
                
                if metadata.get("namespace") != "openshift-gitops":
                    self.result.add_error(
                        f"Bootstrap application namespace should be 'openshift-gitops', got '{metadata.get('namespace')}'"
                    )
                
                # Check for required labels
                labels = metadata.get("labels", {})
                if "app.kubernetes.io/instance" not in labels:
                    self.result.add_warning("Bootstrap application missing 'app.kubernetes.io/instance' label")
            
            # Validate spec
            spec = bootstrap_data.get("spec", {})
            if not spec:
                self.result.add_error("hub-bootstrap.yaml missing spec")
            else:
                # Validate destination
                destination = spec.get("destination", {})
                if not destination:
                    self.result.add_error("hub-bootstrap.yaml missing spec.destination")
                else:
                    if destination.get("server") != "https://kubernetes.default.svc":
                        self.result.add_warning(
                            "Bootstrap application destination.server should be 'https://kubernetes.default.svc'"
                        )
                    
                    if destination.get("namespace") != "openshift-gitops":
                        self.result.add_error(
                            "Bootstrap application destination.namespace should be 'openshift-gitops'"
                        )
                
                # Validate project
                if spec.get("project") != "default":
                    self.result.add_warning(
                        f"Bootstrap application project is '{spec.get('project')}', typically 'default'"
                    )
                
                # Validate source
                source = spec.get("source", {})
                if not source:
                    self.result.add_error("hub-bootstrap.yaml missing spec.source")
                else:
                    # Validate repoURL
                    if "repoURL" not in source:
                        self.result.add_error("hub-bootstrap.yaml missing spec.source.repoURL")
                    
                    # Validate targetRevision
                    if "targetRevision" not in source:
                        self.result.add_error("hub-bootstrap.yaml missing spec.source.targetRevision")
                    
                    # Validate path
                    if "path" not in source:
                        self.result.add_error("hub-bootstrap.yaml missing spec.source.path")
                    else:
                        expected_path = f"charts/hub/{self.pattern_dir.name}"
                        if source["path"] != expected_path:
                            # Check alternative path
                            alt_path = "charts/hub/clustergroup"
                            if source["path"] != alt_path:
                                self.result.add_warning(
                                    f"Bootstrap application path '{source['path']}' doesn't match "
                                    f"expected '{expected_path}' or '{alt_path}'"
                                )
                    
                    # Validate helm values files
                    helm = source.get("helm", {})
                    if helm:
                        value_files = helm.get("valueFiles", [])
                        expected_files = [
                            "/values-global.yaml",
                            "/values-hub.yaml"
                        ]
                        
                        for expected_file in expected_files:
                            if expected_file not in value_files:
                                self.result.add_warning(
                                    f"Bootstrap application missing helm value file: {expected_file}"
                                )
                
                # Validate syncPolicy
                sync_policy = spec.get("syncPolicy", {})
                if not sync_policy:
                    self.result.add_warning("Bootstrap application missing syncPolicy")
                else:
                    automated = sync_policy.get("automated", {})
                    if not automated:
                        self.result.add_info("Bootstrap application doesn't have automated sync")
                    else:
                        if not automated.get("prune", False):
                            self.result.add_info("Bootstrap application automated sync has prune disabled")
                        if not automated.get("selfHeal", False):
                            self.result.add_info("Bootstrap application automated sync has selfHeal disabled")
            
        except Exception as e:
            self.result.add_error(f"Error validating hub-bootstrap.yaml: {e}")
        
        # Check for other bootstrap files (region, edge)
        other_bootstrap_files = ["region-bootstrap.yaml", "edge-bootstrap.yaml"]
        for bootstrap_file in other_bootstrap_files:
            if (bootstrap_dir / bootstrap_file).exists():
                self.result.add_info(f"Found additional bootstrap file: {bootstrap_file}")
        
        self.result.add_info("Bootstrap application validation completed")

    def _validate_common_framework(self) -> None:
        """Validate common framework integration."""
        # Check for common/ directory
        common_dir = self.pattern_dir / "common"
        
        if not common_dir.exists():
            # Common framework might be symlinked
            if common_dir.is_symlink():
                self.result.add_info("common/ is a symlink (standard for validated patterns)")
                # Check if symlink is valid
                try:
                    common_dir.resolve()
                    self.result.add_info("common/ symlink is valid")
                except Exception:
                    self.result.add_error("common/ symlink is broken")
                    return
            else:
                self.result.add_warning(
                    "common/ directory missing. Run './pattern.sh make install' or create symlink to common framework"
                )
                return
        
        # Check for essential common framework files
        essential_files = [
            "common/Makefile",
            "common/common-Makefile",
            "common/scripts/pattern-util.sh"
        ]
        
        for file_path in essential_files:
            full_path = self.pattern_dir / file_path
            if not full_path.exists():
                self.result.add_error(f"Essential common framework file missing: {file_path}")
        
        # Check pattern.sh
        pattern_sh = self.pattern_dir / "pattern.sh"
        if not pattern_sh.exists():
            self.result.add_warning("pattern.sh missing (required for common framework operations)")
        else:
            # Check if it's executable
            if not pattern_sh.is_symlink() and not os.access(pattern_sh, os.X_OK):
                self.result.add_warning("pattern.sh is not executable")
            
            # Check if it's a symlink to common/pattern.sh
            if pattern_sh.is_symlink():
                try:
                    target = pattern_sh.readlink()
                    if str(target) == "common/pattern.sh":
                        self.result.add_info("pattern.sh correctly symlinked to common/pattern.sh")
                    else:
                        self.result.add_warning(f"pattern.sh symlinked to unexpected target: {target}")
                except Exception as e:
                    self.result.add_warning(f"Could not read pattern.sh symlink: {e}")
        
        # Check Makefile integration
        makefile = self.pattern_dir / "Makefile"
        if makefile.exists():
            try:
                makefile_content = makefile.read_text()
                
                # Check for common framework include
                if "include common/Makefile" not in makefile_content:
                    self.result.add_error("Makefile doesn't include common/Makefile")
                
                # Check for PATTERN_OPTS export
                if "export PATTERN_OPTS" not in makefile_content:
                    self.result.add_warning("Makefile doesn't export PATTERN_OPTS")
                
                # Check for essential targets
                essential_targets = ["install", "test", "validate-pattern"]
                makefile_lines = makefile_content.split('\n')
                
                for target in essential_targets:
                    # Look for target definition
                    target_found = any(
                        line.strip().startswith(f"{target}:") 
                        for line in makefile_lines
                    )
                    
                    if not target_found:
                        self.result.add_warning(f"Makefile missing recommended target: {target}")
                
            except Exception as e:
                self.result.add_error(f"Error reading Makefile: {e}")
        
        # Check for ansible.cfg
        ansible_cfg = self.pattern_dir / "ansible.cfg"
        if ansible_cfg.exists():
            try:
                cfg_content = ansible_cfg.read_text()
                
                # Check for common roles path
                if "common/ansible/roles" not in cfg_content:
                    self.result.add_warning("ansible.cfg doesn't include common/ansible/roles in roles_path")
                
                # Check for common plugins
                if "common/ansible/plugins" not in cfg_content:
                    self.result.add_info("Consider adding common/ansible/plugins to ansible.cfg for shared plugins")
                    
            except Exception as e:
                self.result.add_warning(f"Error reading ansible.cfg: {e}")
        
        # Check values-secret.yaml.template
        secret_template = self.pattern_dir / "values-secret.yaml.template"
        if not secret_template.exists():
            self.result.add_info(
                "values-secret.yaml.template not found. "
                "This file helps users understand required secrets"
            )
        
        # Check for setup.sh
        setup_sh = self.pattern_dir / "setup.sh"
        if setup_sh.exists():
            self.result.add_info("setup.sh found (good for initial pattern setup)")
            
            # Check if executable
            if not os.access(setup_sh, os.X_OK):
                self.result.add_warning("setup.sh is not executable")
        
        self.result.add_info("Common framework validation completed")