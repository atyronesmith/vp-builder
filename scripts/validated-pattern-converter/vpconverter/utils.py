"""
Utility functions for the validated pattern converter.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

import git
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import COLORS, LOGGING_CONFIG


# Initialize Rich console for pretty output
console = Console()


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

    return logging.getLogger("vpconverter")


def log_info(message: str) -> None:
    """Log info message with green color."""
    console.print(f"[green][INFO][/green] {message}")


def log_warn(message: str) -> None:
    """Log warning message with yellow color."""
    console.print(f"[yellow][WARN][/yellow] {message}")


def log_error(message: str) -> None:
    """Log error message with red color."""
    console.print(f"[red][ERROR][/red] {message}")


def log_success(message: str) -> None:
    """Log success message with bold green color."""
    console.print(f"[bold green]✓[/bold green] {message}")


@contextmanager
def temporary_directory():
    """Context manager for creating and cleaning up temporary directories."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def clone_repository(url: str, target_dir: Path) -> git.Repo:
    """Clone a git repository to the specified directory."""
    log_info(f"Cloning repository: {url}")
    try:
        repo = git.Repo.clone_from(url, target_dir)
        log_success(f"Repository cloned successfully to {target_dir}")
        return repo
    except git.GitCommandError as e:
        log_error(f"Failed to clone repository: {e}")
        raise


def find_files(
    directory: Path,
    pattern: str = "*",
    extensions: Optional[List[str]] = None,
    recursive: bool = True
) -> List[Path]:
    """Find files in directory matching pattern and/or extensions."""
    files = []

    if recursive:
        search_pattern = f"**/{pattern}" if pattern != "*" else "**/*"
    else:
        search_pattern = pattern

    for file_path in directory.glob(search_pattern):
        if file_path.is_file():
            if extensions:
                if any(file_path.suffix == ext for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)

    return sorted(files)


def read_yaml(file_path: Path) -> Dict[str, Any]:
    """Read and parse a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        log_error(f"Error parsing YAML file {file_path}: {e}")
        raise
    except Exception as e:
        log_error(f"Error reading file {file_path}: {e}")
        raise


def write_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """Write data to a YAML file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        log_error(f"Error writing YAML file {file_path}: {e}")
        raise


def copy_tree(src: Path, dst: Path, ignore_patterns: Optional[List[str]] = None) -> None:
    """Copy directory tree from src to dst, ignoring specified patterns."""
    if ignore_patterns is None:
        ignore_patterns = []

    def ignore_function(directory, contents):
        ignored = []
        for pattern in ignore_patterns:
            for item in contents:
                if Path(item).match(pattern):
                    ignored.append(item)
        return ignored

    shutil.copytree(
        src, dst,
        ignore=ignore_function if ignore_patterns else None,
        dirs_exist_ok=True
    )


def run_command(
    command: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(command)}")
        log_error(f"Error: {e.stderr}")
        raise


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH."""
    return shutil.which(command) is not None


def create_progress_bar() -> Progress:
    """Create a Rich progress bar for long-running operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )


def create_summary_table(title: str, data: List[tuple]) -> Table:
    """Create a Rich table for displaying summary information."""
    table = Table(title=title, show_header=True, header_style="bold magenta")

    if data and len(data[0]) >= 2:
        table.add_column("Item", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for row in data:
            table.add_row(str(row[0]), str(row[1]))

    return table


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def relative_path(path: Path, base: Path) -> Path:
    """Get relative path from base, handling cases where path is not under base."""
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def validate_pattern_name(name: str) -> bool:
    """Validate that the pattern name follows naming conventions."""
    # Pattern name should be lowercase with hyphens
    import re
    pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
    return bool(re.match(pattern, name))


def get_file_size_human(path: Path) -> str:
    """Get human-readable file size."""
    size = path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def bytes_to_human(size: int) -> str:
    """Convert bytes to human-readable format."""
    size_float = float(size)  # Convert to float for division
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} TB"