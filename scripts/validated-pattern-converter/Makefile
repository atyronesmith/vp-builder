.PHONY: help install install-dev test coverage format lint type-check shellcheck python-syntax validate-basic validate-all clean build

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install the package using Poetry
	poetry install

install-dev:  ## Install with development dependencies
	poetry install --with dev
	poetry run pre-commit install

test:  ## Run tests
	poetry run pytest

coverage:  ## Run tests with coverage report
	poetry run pytest --cov=vpconverter --cov-report=html --cov-report=term

format:  ## Format code using black and isort
	poetry run black .
	poetry run isort .

lint:  ## Run linting checks
	poetry run flake8 vpconverter tests
	poetry run mypy vpconverter

type-check:  ## Run type checking
	poetry run mypy vpconverter

shellcheck:  ## Run shellcheck on all bash scripts
	@echo "Running shellcheck on bash scripts..."
	@find . -name "*.sh" -type f | xargs shellcheck -e SC1091

python-syntax:  ## Check Python syntax without Poetry
	@echo "Checking Python syntax..."
	@python3 -m py_compile vpconverter/*.py
	@python3 -m py_compile tests/*.py
	@echo "Python syntax check passed! ✓"

validate-basic:  ## Run basic validation checks (python-syntax, shellcheck)
	@echo "Running basic validation..."
	@echo "1. Python syntax check..."
	@$(MAKE) python-syntax
	@echo "2. Shellcheck..."
	@$(MAKE) shellcheck
	@echo "Basic validation checks passed! ✓"

validate-all:  ## Run all validation checks (lint, type-check, shellcheck, tests)
	@echo "Running comprehensive validation..."
	@echo "1. Formatting check..."
	poetry run black --check .
	poetry run isort --check-only .
	@echo "2. Linting..."
	poetry run flake8 vpconverter tests
	@echo "3. Type checking..."
	poetry run mypy vpconverter
	@echo "4. Shellcheck..."
	@find . -name "*.sh" -type f | xargs shellcheck -e SC1091
	@echo "5. Running tests..."
	poetry run pytest
	@echo "All validation checks passed! ✓"

clean:  ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

build:  ## Build the package
	poetry build

run-example:  ## Run an example conversion
	poetry run vp-convert convert test-pattern ../ai-virtual-agent --verbose

shell:  ## Start a poetry shell
	poetry shell