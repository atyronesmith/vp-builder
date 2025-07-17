# Validated Pattern Converter

A modern Python tool for converting OpenShift/Kubernetes projects into [Red Hat Validated Patterns](https://validatedpatterns.io).

## Features

- 🔍 **Intelligent Analysis**: Automatically scans repositories for Helm charts, YAML configurations, and scripts
- 🏗️ **Complete Structure Generation**: Creates the full validated pattern directory hierarchy
- 📦 **Helm Chart Migration**: Migrates existing charts and creates ArgoCD wrapper charts
- ✅ **Built-in Validation**: Validates generated patterns for correctness
- 🎨 **Rich CLI Interface**: Beautiful terminal output with progress indicators
- 🔧 **Extensible Architecture**: Modular design for easy customization
- Generates comprehensive conversion reports
- Validates YAML syntax and Helm charts
- Creates reference pattern structure for comparison

## 🤖 Automatic Pattern-Specific Configuration

The converter now automatically detects architecture patterns in your projects and applies appropriate configurations:

### AI/ML Pipeline Pattern
When AI/ML patterns are detected (e.g., LLM services, vector databases, model serving):
- **Operators**: GPU Operator, Red Hat OpenShift AI
- **Namespaces**: ai-ml-serving, model-registry, gpu-operator, rhoai
- **Autoscaling**: GPU-aware HPA with nvidia.com/gpu metrics
- **Resources**: GPU node selectors, memory/CPU limits for model serving
- **Storage**: Fast SSD storage class for model caching

### Security Pattern
When security patterns are detected:
- **Operators**: Cert Manager, Compliance Operator, Red Hat Advanced Cluster Security
- **Namespaces**: vault, cert-manager, compliance-operator, stackrox
- **Policies**: Network policies (default deny, DNS allowed), Pod Security Standards
- **RBAC**: Least privilege, per-app service accounts
- **Security Contexts**: Non-root, read-only filesystem, no privilege escalation

### Scaling Pattern
When scaling patterns are detected:
- **Operators**: KEDA, Prometheus
- **Namespaces**: keda, prometheus, grafana
- **Autoscaling**: HPA defaults (2-20 replicas, 70% CPU), VPA configuration
- **Cluster Autoscaler**: Enabled with optimized timings
- **Policies**: Pod Disruption Budgets, Resource Quotas

### Data Processing Pipeline Pattern
When data processing patterns are detected:
- **Operators**: AMQ Streams (Kafka)
- **Namespaces**: kafka, data-pipeline, analytics
- **Configuration**: 3-replica Kafka, 100Gi persistent storage
- **Pipeline**: Parallelism and batch size optimization

The converter applies these configurations automatically during conversion, updating your `values-hub.yaml` and creating resource-specific YAML files in the `resources/` directory.

## 🔧 Configuration

Key configuration options in `vpconverter/config.py`:

- `PATTERN_DIRS`: Directory structure for validated patterns
- `SITE_PATTERNS`: Recognized site types (hub, region, etc.)
- `COMMON_NAMESPACES`: Default namespaces for patterns
- `DEFAULT_CHANNEL_CONFIG`: Default operator channels

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd validated-pattern-converter

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd validated-pattern-converter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

## Usage

### Basic Conversion

Convert a local project:
```bash
vp-convert convert my-pattern ./path/to/project
```

Convert from a Git repository:
```bash
vp-convert convert my-pattern https://github.com/user/repo.git
```

### Command Options

```bash
vp-convert convert [OPTIONS] PATTERN-NAME SOURCE

Options:
  --github-org TEXT        GitHub organization for the pattern
  -o, --output-dir PATH    Output directory (defaults to pattern-name-validated-pattern)
  --analyze-only           Only analyze the source repository without conversion
  --skip-validation        Skip validation after conversion
  --clone-reference        Clone reference pattern (multicloud-gitops)
  -v, --verbose           Enable verbose output
  --help                  Show this message and exit
```

### Other Commands

Analyze a repository without conversion:
```bash
vp-convert analyze ./path/to/project
```

Validate an existing pattern:
```bash
vp-convert validate ./my-pattern-validated-pattern
```

Validate a deployed pattern:
```bash
vp-convert validate-deployment ./my-pattern-validated-pattern
```

List available reference patterns:
```bash
vp-convert list-patterns
```

## Architecture

The converter follows a modular architecture:

```
vpconverter/
├── analyzer.py      # Repository analysis and pattern detection
├── generator.py     # Pattern structure and file generation
├── migrator.py      # Helm chart and script migration
├── validator.py     # Pattern validation
├── templates.py     # File templates
├── config.py        # Configuration constants
├── utils.py         # Utility functions
└── cli.py          # Command-line interface
```

### Conversion Process

1. **Analysis Phase**: Scans the source repository for:
   - Helm charts (Chart.yaml)
   - YAML configuration files
   - Shell scripts
   - Existing pattern structures

2. **Generation Phase**: Creates validated pattern structure:
   - Directory hierarchy
   - Base configuration files
   - Values files (global, hub, region)
   - GitOps manifests

3. **Migration Phase**: Migrates resources:
   - Copies Helm charts to `migrated-charts/`
   - Creates ArgoCD wrapper charts
   - Migrates useful scripts

4. **Validation Phase**: Ensures correctness:
   - YAML syntax validation
   - Helm chart validation
   - Structure verification

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=vpconverter

# Run specific test file
poetry run pytest tests/test_analyzer.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy vpconverter

# Linting
poetry run flake8
```

### Project Structure

```
validated-pattern-converter/
├── vpconverter/              # Main package
│   ├── __init__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── config.py
│   ├── generator.py
│   ├── migrator.py
│   ├── templates.py
│   ├── utils.py
│   └── validator.py
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_analyzer.py
│   └── test_generator.py
├── docs/                     # Documentation
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── .gitignore
```

## API Usage

The converter can also be used programmatically:

```python
from pathlib import Path
from vpconverter import PatternAnalyzer, PatternGenerator, HelmMigrator

# Analyze a repository
analyzer = PatternAnalyzer(Path("./my-project"))
result = analyzer.analyze()

# Generate pattern structure
generator = PatternGenerator("my-pattern", Path("./output"))
generator.generate(result)

# Migrate Helm charts
migrator = HelmMigrator(Path("./output"), generator)
migrator.migrate_all(result)
```

## Configuration

Key configuration options in `vpconverter/config.py`:

- `PATTERN_DIRS`: Directory structure for validated patterns
- `SITE_PATTERNS`: Recognized site types (hub, region, etc.)
- `COMMON_NAMESPACES`: Default namespaces for patterns
- `DEFAULT_CHANNEL_CONFIG`: Default operator channels

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed:
   ```bash
   poetry install
   ```

2. **Permission Errors**: The tool needs write permissions in the output directory

3. **Git Clone Failures**: Check network connectivity and Git credentials

4. **Validation Errors**: Review the validation output and fix identified issues

### Debug Mode

Run with verbose output for detailed information:
```bash
vp-convert --verbose convert my-pattern ./source
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure quality checks pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- [Red Hat Validated Patterns](https://validatedpatterns.io)
- [OpenShift GitOps](https://docs.openshift.com/container-platform/latest/cicd/gitops/understanding-openshift-gitops.html)
- [Helm](https://helm.sh)

## Support

For issues and questions:
- Open an issue on GitHub
- Visit [validatedpatterns.io](https://validatedpatterns.io)
- Join the community discussions