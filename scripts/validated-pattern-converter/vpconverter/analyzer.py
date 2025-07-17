"""
Repository analyzer for validated pattern converter.

This module scans source repositories to identify Helm charts,
configuration files, and existing pattern structures.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING

import yaml

from .config import (
    CHART_FILE, VALUES_FILE, TEMPLATES_DIR, KUSTOMIZATION_FILE,
    YAML_EXTENSIONS, SCRIPT_EXTENSIONS, SITE_PATTERNS, COMMON_TEMPLATES
)
from .models import HelmChart, AnalysisResult
from .enhanced_analyzer import EnhancedHelmAnalyzer
from .utils import (
    setup_logging, log_info, log_warn, log_error, log_success, console,
    relative_path, create_summary_table,
    get_file_size_human, bytes_to_human, find_files, read_yaml
)

# Import enhanced analyzer if deep analysis is needed
try:
    from .enhanced_analyzer import EnhancedHelmAnalyzer, EnhancedChartAnalysis
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False
    if TYPE_CHECKING:
        from .enhanced_analyzer import EnhancedChartAnalysis


class PatternAnalyzer:
    """Analyzes source repositories for validated pattern conversion."""

    def __init__(self, source_path: Path):
        """Initialize analyzer with source repository path."""
        self.source_path = source_path
        self.result = AnalysisResult(source_path=source_path)

    def analyze(self, verbose: bool = False) -> AnalysisResult:
        """Perform complete analysis of the source repository."""
        log_info(f"Starting analysis of repository: {self.source_path}")

        with console.status("[bold green]Analyzing repository...") as status:
            # Scan for Helm charts
            status.update("Scanning for Helm charts...")
            self._analyze_helm_charts(verbose)

            # Scan for YAML files
            status.update("Scanning for YAML configuration files...")
            self._analyze_yaml_files(verbose)

            # Scan for scripts
            status.update("Scanning for shell scripts...")
            self._analyze_scripts(verbose)

            # Check for site-based organization
            status.update("Checking for site-based organization...")
            self._analyze_site_structure()

            # Detect existing patterns
            status.update("Detecting existing patterns...")
            self._detect_patterns()

            # Calculate statistics
            status.update("Calculating statistics...")
            self._calculate_stats()

            # Run enhanced analysis if charts were found
            if self.result.helm_charts:
                status.update("Running enhanced pattern analysis...")
                self._run_enhanced_analysis(verbose)

        log_success("Repository analysis completed")
        return self.result

    def _analyze_helm_charts(self, verbose: bool = False) -> None:
        """Find and analyze all Helm charts in the repository."""
        chart_files = find_files(self.source_path, CHART_FILE)

        for chart_file in chart_files:
            chart_dir = chart_file.parent
            chart_name = chart_dir.name

            log_info(f"  ✓ Found Helm chart: {chart_name}")

            # Load Chart.yaml
            chart_data = read_yaml(chart_file)

            # Create HelmChart object
            chart = HelmChart(
                name=chart_name,
                path=chart_dir,
                version=chart_data.get('version'),
                app_version=chart_data.get('appVersion'),
                description=chart_data.get('description'),
                chart_type=chart_data.get('type', 'application'),
                dependencies=chart_data.get('dependencies', [])
            )

            # Check for values.yaml
            values_file = chart_dir / VALUES_FILE
            if values_file.exists():
                chart.has_values = True
                # Count top-level values keys
                values_data = read_yaml(values_file)
                if isinstance(values_data, dict):
                    key_count = len(values_data.keys())
                    log_info(f"    Values: {key_count} top-level keys")

            # Analyze templates
            templates_dir = chart_dir / TEMPLATES_DIR
            if templates_dir.exists():
                chart.has_templates = True
                template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
                chart.template_count = len([f for f in template_files if not f.name.startswith('_')])
                log_info(f"    Templates: {chart.template_count} files")

                # Check for common template patterns
                for template_file in template_files:
                    template_name = template_file.stem
                    if template_name in COMMON_TEMPLATES:
                        chart.templates_found.append(f"{template_name}.yaml")

                    # Check if templates use Helm templating
                    try:
                        with open(template_file, 'r') as f:
                            content = f.read()
                            if '{{' in content:
                                chart.uses_helm_templates = True
                    except Exception:
                        pass

                if chart.templates_found:
                    log_info(f"    Common templates: {', '.join(chart.templates_found)}")

            # Perform enhanced analysis if available and verbose
            if ENHANCED_ANALYSIS_AVAILABLE and verbose:
                try:
                    enhanced_analyzer = EnhancedHelmAnalyzer(chart_dir)
                    enhanced_results = enhanced_analyzer.analyze()

                    # Add enhanced information to chart
                    chart.enhanced_analysis = enhanced_results

                    # Log patterns if found
                    if enhanced_results.patterns:
                        log_info("    Detected patterns:")
                        for pattern in enhanced_results.patterns:
                            log_info(f"      - {pattern.name} (confidence: {pattern.confidence:.0%})")

                    # Log security features
                    if enhanced_results.security_features:
                        log_info(f"    Security features: {', '.join(enhanced_results.security_features)}")

                except Exception as e:
                    log_warn(f"    Enhanced analysis failed: {e}")

            self.result.helm_charts.append(chart)

    def _analyze_chart_structure(self, chart: HelmChart, verbose: bool) -> None:
        """Analyze the structure of a Helm chart."""
        # Check for values.yaml
        values_file = chart.path / VALUES_FILE
        if values_file.exists():
            chart.has_values = True
            if verbose:
                try:
                    values_data = read_yaml(values_file)
                    value_count = self._count_yaml_keys(values_data)
                    log_info(f"    Values: {value_count} top-level keys")
                except Exception:
                    pass

        # Check for templates
        templates_dir = chart.path / TEMPLATES_DIR
        if templates_dir.exists() and templates_dir.is_dir():
            chart.has_templates = True
            template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
            chart.template_count = len(template_files)

            # Check for Helm templating
            for template_file in template_files:
                try:
                    with open(template_file, 'r') as f:
                        content = f.read()
                        if "{{" in content:
                            chart.uses_helm_templates = True
                            break
                except Exception:
                    pass

            # Check for common templates
            for common_template in COMMON_TEMPLATES:
                if (templates_dir / common_template).exists():
                    chart.templates_found.append(common_template)

            if verbose:
                log_info(f"    Templates: {chart.template_count} files")
                if chart.templates_found:
                    log_info(f"    Common templates: {', '.join(chart.templates_found)}")

    def _analyze_yaml_files(self, verbose: bool) -> None:
        """Find all YAML files in the repository."""
        yaml_files = find_files(self.source_path, extensions=YAML_EXTENSIONS)

        # Exclude Chart.yaml files already analyzed
        chart_paths = {chart.path for chart in self.result.helm_charts}

        for yaml_file in yaml_files:
            # Skip if it's part of a Helm chart
            if any(chart_path in yaml_file.parents for chart_path in chart_paths):
                continue

            self.result.yaml_files.append(yaml_file)

            # Check for Kustomization files
            if yaml_file.name == KUSTOMIZATION_FILE:
                self.result.has_kustomize = True

        if verbose and self.result.yaml_files:
            log_info(f"  Found {len(self.result.yaml_files)} YAML files")
            # Show first 10 files
            for i, yaml_file in enumerate(self.result.yaml_files[:10]):
                rel_path = relative_path(yaml_file, self.source_path)
                log_info(f"    - {rel_path}")
            if len(self.result.yaml_files) > 10:
                log_info(f"    ... and {len(self.result.yaml_files) - 10} more")

    def _analyze_scripts(self, verbose: bool) -> None:
        """Find all shell scripts in the repository."""
        script_files = find_files(self.source_path, extensions=SCRIPT_EXTENSIONS)
        self.result.script_files = script_files

        if verbose and script_files:
            log_info(f"  Found {len(script_files)} shell scripts")
            for script in script_files[:5]:
                rel_path = relative_path(script, self.source_path)
                log_info(f"    - {rel_path}")
            if len(script_files) > 5:
                log_info(f"    ... and {len(script_files) - 5} more")

    def _analyze_site_structure(self) -> None:
        """Check if repository follows site-based organization."""
        for site in SITE_PATTERNS:
            site_dir = self.source_path / site
            if site_dir.exists() and site_dir.is_dir():
                self.result.site_directories.append(site)
                log_info(f"  ✓ Found site directory: {site}/")

    def _detect_patterns(self) -> None:
        """Detect existing patterns in the repository."""
        # Check for GitOps patterns
        if any("gitops" in str(f).lower() for f in self.result.yaml_files):
            self.result.detected_patterns.add("gitops")

        # Check for ArgoCD
        if any("argo" in str(f).lower() for f in self.result.yaml_files):
            self.result.detected_patterns.add("argocd")

        # Check for ACM (Advanced Cluster Management)
        if any("acm" in str(f).lower() or "cluster-management" in str(f).lower()
               for f in self.result.yaml_files):
            self.result.detected_patterns.add("acm")

        # Check for Kustomize
        if self.result.has_kustomize:
            self.result.detected_patterns.add("kustomize")

    def _calculate_stats(self) -> None:
        """Calculate repository statistics."""
        total_size = 0
        total_files = 0

        for file_path in self.source_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        self.result.total_files = total_files
        self.result.total_size = bytes_to_human(total_size)

    def _run_enhanced_analysis(self, verbose: bool) -> None:
        """Run enhanced analysis on discovered Helm charts."""
        enhanced_analyses = []

        for chart in self.result.helm_charts:
            log_info(f"  Running enhanced analysis on chart: {chart.name}")
            enhanced_analyzer = EnhancedHelmAnalyzer(chart.path)
            enhanced_result = enhanced_analyzer.analyze()
            enhanced_analyses.append(enhanced_result)

            # Extract detected patterns
            for pattern in enhanced_result.patterns:
                if pattern.confidence >= 0.6:  # Only add high-confidence patterns
                    self.result.detected_patterns.add(pattern.name)
                    if verbose:
                        log_info(f"    Detected: {pattern.name} ({pattern.confidence*100:.0f}% confidence)")

        # Store enhanced analysis results
        self.result.enhanced_analysis = enhanced_analyses

    def _count_yaml_keys(self, data: Any, depth: int = 0) -> int:
        """Count top-level keys in YAML data."""
        if depth > 0 or not isinstance(data, dict):
            return 0
        return len(data.keys())

    def print_summary(self) -> None:
        """Print a formatted summary of the analysis results."""
        console.print("\n[bold cyan]═══ Analysis Summary ═══[/bold cyan]\n")

        # Repository info
        summary_data = [
            ("Repository", str(self.source_path)),
            ("Total Files", str(self.result.total_files)),
            ("Total Size", self.result.total_size),
            ("Helm Charts", str(len(self.result.helm_charts))),
            ("YAML Files", str(len(self.result.yaml_files))),
            ("Shell Scripts", str(len(self.result.script_files))),
            ("Site Directories", ", ".join(self.result.site_directories) or "None"),
            ("Detected Patterns", ", ".join(self.result.detected_patterns) or "None"),
        ]

        table = create_summary_table("Repository Analysis", summary_data)
        console.print(table)

        # Helm chart details
        if self.result.helm_charts:
            console.print("\n[bold cyan]Helm Charts Found:[/bold cyan]")
            for chart in self.result.helm_charts:
                console.print(f"\n  [green]• {chart.name}[/green]")
                console.print(f"    Path: {relative_path(chart.path, self.source_path)}")
                console.print(f"    Type: {chart.chart_type}")
                if chart.version:
                    console.print(f"    Version: {chart.version}")
                if chart.has_templates:
                    console.print(f"    Templates: {chart.template_count} files")
                if chart.dependencies:
                    console.print(f"    Dependencies: {len(chart.dependencies)}")

                # Show enhanced analysis if available
                if hasattr(chart, 'enhanced_analysis') and chart.enhanced_analysis:
                    enhanced = chart.enhanced_analysis

                    # Show detected patterns
                    if enhanced.patterns:
                        console.print("\n    [yellow]Detected Patterns:[/yellow]")
                        for pattern in sorted(enhanced.patterns, key=lambda p: p.confidence, reverse=True):
                            confidence_color = "green" if pattern.confidence > 0.7 else "yellow" if pattern.confidence > 0.4 else "dim"
                            console.print(f"      [{confidence_color}]• {pattern.name} ({pattern.confidence:.0%} confidence)[/{confidence_color}]")
                            if pattern.evidence:
                                for evidence in pattern.evidence[:2]:  # Show first 2 pieces of evidence
                                    console.print(f"        - {evidence}")

                    # Show security features
                    if enhanced.security_features:
                        console.print("\n    [cyan]Security Features:[/cyan]")
                        for feature in enhanced.security_features[:3]:  # Show first 3
                            console.print(f"      • {feature}")

                    # Show components summary
                    if enhanced.components:
                        container_count = sum(1 for c in enhanced.components if c.type == 'container')
                        dep_count = sum(1 for c in enhanced.components if c.type.startswith('dependency'))
                        console.print(f"\n    [blue]Components:[/blue] {container_count} containers, {dep_count} dependencies")

                        # Group dependencies by type
                        dep_types = {}
                        for comp in enhanced.components:
                            if comp.type.startswith('dependency-'):
                                dep_type = comp.type.split('-', 1)[1]
                                if dep_type not in dep_types:
                                    dep_types[dep_type] = []
                                dep_types[dep_type].append(comp.name)

                        if dep_types:
                            console.print("      Dependencies by type:")
                            for dep_type, deps in sorted(dep_types.items()):
                                console.print(f"        • {dep_type}: {', '.join(deps)}")