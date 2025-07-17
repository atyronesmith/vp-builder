#!/bin/bash
# Installation script for Validated Pattern Converter

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Validated Pattern Converter Installation${NC}"
echo -e "${GREEN}================================================${NC}"
echo

# Check Python version
echo -n "Checking Python version... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

    if [[ ${PYTHON_MAJOR} -ge 3 ]] && [[ ${PYTHON_MINOR} -ge 9 ]]; then
        echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION}"
    else
        echo -e "${RED}✗${NC} Python ${PYTHON_VERSION} (requires 3.9+)"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Python3 not found"
    exit 1
fi

# Check for Poetry
echo -n "Checking for Poetry... "
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
    echo -e "${GREEN}✓${NC} Poetry ${POETRY_VERSION}"
    USE_POETRY=true
else
    echo -e "${YELLOW}⚠${NC} Poetry not found"
    echo "  Poetry is recommended for installation."
    echo "  Install with: curl -sSL https://install.python-poetry.org | python3 -"
    echo
    read -p "Continue with pip instead? (y/N) " -n 1 -r
    echo
    if [[ ! ${REPLY} =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_POETRY=false
fi

# Check for Git (required for gitpython)
echo -n "Checking for Git... "
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo -e "${GREEN}✓${NC} Git ${GIT_VERSION}"
else
    echo -e "${RED}✗${NC} Git not found (required for repository cloning)"
    exit 1
fi

# Installation directory
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${INSTALL_DIR}"

echo
echo "Installing Validated Pattern Converter..."
echo "Installation directory: ${INSTALL_DIR}"
echo

if [[ "${USE_POETRY}" = true ]]; then
    # Install with Poetry
    echo "Installing with Poetry..."
    poetry install

    echo
    echo -e "${GREEN}Installation complete!${NC}"
    echo
    echo "To use the converter:"
    echo "  1. Activate the virtual environment:"
    echo "     poetry shell"
    echo
    echo "  2. Run the converter:"
    echo "     vp-convert convert <pattern-name> <source>"
    echo
    echo "Or run directly with:"
    echo "  poetry run vp-convert convert <pattern-name> <source>"

else
    # Install with pip
    echo "Creating virtual environment..."
    python3 -m venv venv

    echo "Activating virtual environment..."
    # shellcheck source=/dev/null
    source venv/bin/activate

    echo "Upgrading pip..."
    pip install --upgrade pip

    echo "Installing dependencies..."
    pip install -r requirements.txt

    echo "Installing package..."
    pip install -e .

    echo
    echo -e "${GREEN}Installation complete!${NC}"
    echo
    echo "To use the converter:"
    echo "  1. Activate the virtual environment:"
    echo "     source venv/bin/activate"
    echo
    echo "  2. Run the converter:"
    echo "     vp-convert convert <pattern-name> <source>"
fi

echo
echo "For backward compatibility with the bash script:"
echo "  ../convert-to-validated-pattern.py <pattern-name> <source> [github-org]"
echo
echo "See README.md for full documentation."