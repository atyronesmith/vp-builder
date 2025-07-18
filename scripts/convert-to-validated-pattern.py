#!/usr/bin/env python3
"""
Python wrapper for the validated pattern converter.
This script ensures proper virtual environment usage and handles imports correctly.
It automatically sets up the virtual environment and installs dependencies if needed.
"""

import sys
import os
import subprocess
from pathlib import Path

# Determine paths
script_path = Path(__file__).resolve()
scripts_dir = script_path.parent
converter_dir = scripts_dir / "validated-pattern-converter"
venv_dir = converter_dir / "venv"
venv_python = venv_dir / "bin" / "python"
requirements_file = converter_dir / "requirements.txt"

def setup_virtual_environment():
    """Create virtual environment and install dependencies."""
    print(f"Setting up virtual environment in {venv_dir}...")

    # Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Install dependencies
    print(f"Installing dependencies from {requirements_file}...")
    subprocess.run([
        str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)
    ], check=True)

    print("Setup complete!")

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        # Try importing the main module
        import vpconverter.cli
        return True
    except ImportError:
        return False

# If venv doesn't exist, create it
if not venv_python.exists():
    print("Virtual environment not found. Creating it now...")
    setup_virtual_environment()

# If venv exists and we're not already using it, restart with venv Python
if venv_python.exists() and sys.executable != str(venv_python):
    os.execv(str(venv_python), [str(venv_python), __file__] + sys.argv[1:])

# Add converter to Python path
sys.path.insert(0, str(converter_dir))

# Check if dependencies are installed
if not check_dependencies():
    print("Dependencies not found. Installing them now...")
    subprocess.run([
        str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)
    ], check=True)

    # Try importing again
    if not check_dependencies():
        print("Error: Failed to install dependencies properly.")
        sys.exit(1)

# Now import and run the CLI
try:
    from vpconverter.cli import cli

    if __name__ == "__main__":
        # Call the CLI directly
        cli()
except ImportError as e:
    print(f"Error: Failed to import converter modules: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current Python: {sys.executable}")
    print("\nTry running: rm -rf scripts/validated-pattern-converter/venv")
    print("Then run this script again to reinstall dependencies.")
    sys.exit(1)