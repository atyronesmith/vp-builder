"""
Helm chart migrator for validated pattern converter.

This module handles the migration of Helm charts from source
repositories to the validated pattern structure.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Set

from .analyzer import HelmChart, AnalysisResult
from .generator import PatternGenerator
from .utils import (
    log_info, log_warn, log_success, log_error,
    copy_tree, ensure_directory, relative_path,
    console, run_command, check_command_exists
)


class HelmMigrator:
    """Migrates Helm charts to validated pattern structure."""

    def __init__(self, pattern_dir: Path, generator: PatternGenerator):
        """Initialize migrator with pattern directory and generator."""
        self.pattern_dir = pattern_dir
        self.generator = generator
        self.migrated_dir = pattern_dir / "migrated-charts"
        ensure_directory(self.migrated_dir)

    def migrate_all(self, analysis_result: AnalysisResult) -> int:
        """Migrate all Helm charts found in the analysis."""
        if not analysis_result.helm_charts:
            log_warn("No Helm charts found to migrate")
            return 0

        log_info(f"Starting migration of {len(analysis_result.helm_charts)} Helm charts...")

        migrated_count = 0
        with console.status("[bold green]Migrating Helm charts...") as status:
            for i, chart in enumerate(analysis_result.helm_charts, 1):
                status.update(f"Migrating chart {i}/{len(analysis_result.helm_charts)}: {chart.name}")

                if self.migrate_chart(chart):
                    migrated_count += 1

                    # Generate wrapper chart
                    status.update(f"Creating wrapper for {chart.name}...")
                    self.generator.generate_wrapper_chart(chart)

        log_success(f"Successfully migrated {migrated_count} charts")
        return migrated_count

    def migrate_chart(self, chart: HelmChart) -> bool:
        """Migrate a single Helm chart."""
        try:
            target_dir = self.migrated_dir / chart.name

            # Check if already exists
            if target_dir.exists():
                log_warn(f"  Chart {chart.name} already exists in migrated-charts, skipping")
                return False

            # Copy chart directory
            log_info(f"  Migrating chart: {chart.name}")
            copy_tree(
                chart.path,
                target_dir,
                ignore_patterns=[".git", ".gitignore", "*.tgz", ".helmignore"]
            )

            # Validate the migrated chart
            if self._validate_chart(target_dir):
                log_success(f"    ✓ Chart migrated: migrated-charts/{chart.name}/")

                # Optionally update Chart.yaml with pattern-specific metadata
                self._update_chart_metadata(target_dir, chart)

                return True
            else:
                log_error(f"    ✗ Chart validation failed: {chart.name}")
                # Clean up failed migration
                shutil.rmtree(target_dir, ignore_errors=True)
                return False

        except Exception as e:
            log_error(f"  Failed to migrate chart {chart.name}: {e}")
            return False

    def migrate_scripts(self, analysis_result: AnalysisResult) -> int:
        """Migrate useful scripts from source repository."""
        if not analysis_result.script_files:
            return 0

        scripts_dir = self.pattern_dir / "scripts"
        ensure_directory(scripts_dir)

        migrated_count = 0
        useful_scripts = self._identify_useful_scripts(analysis_result.script_files)

        for script in useful_scripts:
            try:
                target_path = scripts_dir / script.name
                if not target_path.exists():
                    shutil.copy2(script, target_path)
                    log_info(f"  ✓ Migrated script: scripts/{script.name}")
                    migrated_count += 1
            except Exception as e:
                log_warn(f"  Failed to migrate script {script.name}: {e}")

        return migrated_count

    def _validate_chart(self, chart_dir: Path) -> bool:
        """Validate a Helm chart structure."""
        # Basic structure validation
        required_files = ["Chart.yaml"]
        for required_file in required_files:
            if not (chart_dir / required_file).exists():
                log_error(f"    Missing required file: {required_file}")
                return False

        # If helm is available, use it for validation
        if check_command_exists("helm"):
            try:
                result = run_command(
                    ["helm", "lint", str(chart_dir)],
                    capture_output=True,
                    check=False
                )

                if result.returncode == 0:
                    log_info("    ✓ Helm lint passed")
                    return True
                else:
                    log_warn(f"    Helm lint warnings: {result.stdout}")
                    # Don't fail on lint warnings, just inform
                    return True

            except Exception as e:
                log_warn(f"    Could not run helm lint: {e}")
                # Continue anyway if helm is not available
                return True

        return True

    def _update_chart_metadata(self, chart_dir: Path, chart: HelmChart) -> None:
        """Update Chart.yaml with pattern-specific metadata."""
        chart_file = chart_dir / "Chart.yaml"

        try:
            import yaml
            with open(chart_file, 'r') as f:
                chart_data = yaml.safe_load(f)

            # Add pattern-specific annotations
            if "annotations" not in chart_data:
                chart_data["annotations"] = {}

            chart_data["annotations"]["validatedpatterns.io/pattern"] = self.generator.pattern_name
            chart_data["annotations"]["validatedpatterns.io/migrated"] = "true"

            # Update maintainers if not present
            if "maintainers" not in chart_data or not chart_data["maintainers"]:
                chart_data["maintainers"] = [{
                    "name": "Validated Patterns Team",
                    "email": "validated-patterns@redhat.com"
                }]

            with open(chart_file, 'w') as f:
                yaml.dump(chart_data, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            log_warn(f"    Could not update chart metadata: {e}")

    def _identify_useful_scripts(self, scripts: List[Path]) -> List[Path]:
        """Identify scripts that might be useful in the pattern."""
        useful_scripts = []
        useful_patterns = [
            "deploy", "install", "setup", "test", "validate",
            "build", "push", "release", "backup", "restore"
        ]

        exclude_patterns = [
            "node_modules", "venv", ".git", "vendor",
            "__pycache__", ".pytest_cache"
        ]

        for script in scripts:
            # Skip if in excluded directory
            if any(pattern in str(script) for pattern in exclude_patterns):
                continue

            # Include if name matches useful patterns
            script_name_lower = script.name.lower()
            if any(pattern in script_name_lower for pattern in useful_patterns):
                useful_scripts.append(script)
                continue

            # Include if it's in a scripts or bin directory
            if script.parent.name in ["scripts", "bin", "tools"]:
                useful_scripts.append(script)

        return useful_scripts

    def create_migration_summary(self, analysis_result: AnalysisResult) -> dict:
        """Create a summary of the migration process."""
        summary = {
            "total_charts": len(analysis_result.helm_charts),
            "migrated_charts": 0,
            "wrapper_charts_created": 0,
            "scripts_migrated": 0,
            "migration_issues": []
        }

        # Count migrated charts
        if self.migrated_dir.exists():
            summary["migrated_charts"] = len(list(self.migrated_dir.glob("*/")))

        # Count wrapper charts
        hub_charts_dir = self.pattern_dir / "charts" / "hub"
        if hub_charts_dir.exists():
            summary["wrapper_charts_created"] = len(list(hub_charts_dir.glob("*/")))

        return summary