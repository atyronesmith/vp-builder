"""
Command-line interface for validated pattern converter.

This module provides the CLI interface using Click framework
to convert projects into validated patterns.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .analyzer import PatternAnalyzer
from .config import DEFAULT_GITHUB_ORG, PATTERN_REPOS
from .generator import PatternGenerator
from .migrator import HelmMigrator
from .validator import PatternValidator
from .utils import (
    setup_logging, log_info, log_error, log_success, log_warn,
    clone_repository, temporary_directory, validate_pattern_name,
    console
)


@click.group()
@click.version_option(version=__version__, prog_name="validated-pattern-converter")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Convert OpenShift/Kubernetes projects into Red Hat Validated Patterns."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)

    # Display banner
    banner = Panel.fit(
        Text("Validated Pattern Converter", style="bold cyan", justify="center"),
        subtitle=f"v{__version__}",
        border_style="cyan"
    )
    console.print(banner)


@cli.command()
@click.argument("pattern-name")
@click.argument("source", type=click.Path())
@click.option(
    "--github-org",
    default=DEFAULT_GITHUB_ORG,
    help="GitHub organization for the pattern"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory (defaults to pattern-name-validated-pattern)"
)
@click.option(
    "--analyze-only",
    is_flag=True,
    help="Only analyze the source repository without conversion"
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip validation after conversion"
)
@click.option(
    "--clone-reference",
    is_flag=True,
    help="Clone reference pattern (multicloud-gitops) for comparison"
)
@click.pass_context
def convert(
    ctx: click.Context,
    pattern_name: str,
    source: str,
    github_org: str,
    output_dir: Optional[str],
    analyze_only: bool,
    skip_validation: bool,
    clone_reference: bool
) -> None:
    """Convert a source repository into a validated pattern.

    PATTERN-NAME: Name for the validated pattern (lowercase with hyphens)
    SOURCE: Path to source repository or Git URL
    """
    verbose = ctx.obj["verbose"]

    # Validate pattern name
    if not validate_pattern_name(pattern_name):
        log_error("Pattern name must be lowercase with hyphens (e.g., my-pattern)")
        sys.exit(1)

    # Determine output directory
    if output_dir:
        pattern_dir = Path(output_dir)
    else:
        pattern_dir = Path(f"{pattern_name}-validated-pattern")

    # Handle source input (URL or local path)
    source_path = Path(source)
    temp_dir_context = None

    try:
        # Check if source is a URL
        if source.startswith(("http://", "https://", "git@")):
            log_info(f"Detected repository URL: {source}")
            temp_dir_context = temporary_directory()
            temp_dir = temp_dir_context.__enter__()
            clone_repository(source, temp_dir / "source")
            source_path = temp_dir / "source"
        elif not source_path.exists():
            log_error(f"Source path not found: {source}")
            sys.exit(1)

        # Phase 1: Analysis
        console.print("\n[bold yellow]=== Phase 1: Analysis ===[/bold yellow]")
        analyzer = PatternAnalyzer(source_path)
        analysis_result = analyzer.analyze(verbose)
        analyzer.print_summary()

        if analyze_only:
            log_info("Analysis complete (--analyze-only specified)")
            return

        # Check if pattern directory already exists
        if pattern_dir.exists():
            if not click.confirm(f"\nDirectory {pattern_dir} already exists. Overwrite?"):
                log_info("Conversion cancelled")
                return
            import shutil
            shutil.rmtree(pattern_dir)

        # Phase 2: Structure Creation
        console.print("\n[bold yellow]=== Phase 2: Structure Creation ===[/bold yellow]")
        generator = PatternGenerator(pattern_name, pattern_dir, github_org, source_dir=source_path)
        generator.generate(analysis_result)

        # Phase 3: Migration
        console.print("\n[bold yellow]=== Phase 3: Migration ===[/bold yellow]")
        migrator = HelmMigrator(pattern_dir, generator)
        charts_migrated = migrator.migrate_all(analysis_result)
        scripts_migrated = migrator.migrate_scripts(analysis_result)

        log_info(f"Migrated {charts_migrated} Helm charts and {scripts_migrated} scripts")

        # Phase 4: Configuration (Manual)
        console.print("\n[bold yellow]=== Phase 4: Configuration ===[/bold yellow]")
        console.print("[yellow]This phase requires manual configuration:[/yellow]")
        console.print("  • Update values files with your specifics")
        console.print("  • Configure secrets management")
        console.print("  • Add platform overrides if needed")
        console.print("  • Set up managed clusters if required")

        # Phase 5: Validation
        if not skip_validation:
            console.print("\n[bold yellow]=== Phase 5: Validation ===[/bold yellow]")
            validator = PatternValidator(pattern_dir)
            validation_result = validator.validate(check_cluster=False)

            if not validation_result.passed:
                log_warn("Pattern validation found issues - please review and fix")

        # Clone reference pattern if requested
        if clone_reference:
            ref_dir = Path("multicloud-gitops")
            if not ref_dir.exists():
                log_info("\nCloning reference pattern for comparison...")
                clone_repository(PATTERN_REPOS["reference"], ref_dir)
                log_info(f"Reference pattern available at: {ref_dir}")

        # Success summary
        console.print("\n[bold green]═══ Conversion Complete! ═══[/bold green]\n")
        console.print(f"✅ Pattern created in: [cyan]{pattern_dir}[/cyan]")
        console.print(f"📊 Helm charts migrated: [cyan]{charts_migrated}[/cyan]")
        console.print(f"📄 Scripts migrated: [cyan]{scripts_migrated}[/cyan]")

        console.print("\n[bold]Next Steps:[/bold]")
        console.print(f"1. cd {pattern_dir}")
        console.print("2. git clone https://github.com/validatedpatterns-docs/common.git")
        console.print("3. cp values-secret.yaml.template values-secret.yaml")
        console.print("4. Edit values files as needed")
        console.print("5. make install")

    except Exception as e:
        log_error(f"Conversion failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        if temp_dir_context:
            temp_dir_context.__exit__(None, None, None)


@cli.command()
@click.argument("pattern-dir", type=click.Path(exists=True))
@click.option("--check-cluster", is_flag=True, help="Also check cluster connectivity")
@click.pass_context
def validate(ctx: click.Context, pattern_dir: str, check_cluster: bool) -> None:
    """Validate a validated pattern structure."""
    pattern_path = Path(pattern_dir)

    log_info(f"Validating pattern: {pattern_path}")

    validator = PatternValidator(pattern_path)
    result = validator.validate(check_cluster=check_cluster)

    if not result.passed:
        sys.exit(1)


@cli.command()
@click.argument("pattern-dir", type=click.Path(exists=True))
@click.pass_context
def validate_deployment(ctx: click.Context, pattern_dir: str) -> None:
    """Validate a deployed pattern on the cluster."""
    pattern_path = Path(pattern_dir)

    validator = PatternValidator(pattern_path)
    if not validator.validate_deployment():
        sys.exit(1)


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.pass_context
def analyze(ctx: click.Context, source: str) -> None:
    """Analyze a source repository without conversion."""
    source_path = Path(source)
    verbose = ctx.obj["verbose"]

    analyzer = PatternAnalyzer(source_path)
    analysis_result = analyzer.analyze(verbose)
    analyzer.print_summary()


@cli.command()
def list_patterns() -> None:
    """List available reference patterns."""
    console.print("\n[bold]Available Reference Patterns:[/bold]\n")

    patterns = [
        ("multicloud-gitops", "Core GitOps pattern with ACM"),
        ("industrial-edge", "Edge computing for industrial IoT"),
        ("medical-diagnosis", "AI/ML for medical imaging"),
        ("retail", "Retail application modernization"),
    ]

    for name, description in patterns:
        console.print(f"  • [cyan]{name}[/cyan]: {description}")

    console.print("\n[dim]Visit https://validatedpatterns.io for more patterns[/dim]")


def main() -> None:
    """Main entry point for the CLI."""
    cli()