# Validated Patterns Conversion Tools

This directory contains tools for converting projects into Red Hat Validated Patterns and managing pattern deployments.

## 🆕 Python Converter (Recommended)

A modern Python implementation of the validated pattern converter with enhanced features:
- Rich terminal UI with progress indicators
- Better error handling and validation
- Modular, testable architecture
- Backward compatible with bash script

### Quick Start
```bash
cd scripts/validated-pattern-converter
./install.sh
vp-convert convert my-pattern ./source-repo
```

See [validated-pattern-converter/README.md](validated-pattern-converter/README.md) for full documentation.

## Scripts Overview

### 🔄 convert-to-validated-pattern.sh
Main conversion tool that transforms any OpenShift/Kubernetes project into a validated pattern structure.

**Usage:**
```bash
./scripts/convert-to-validated-pattern.sh <pattern-name> <source-repo-path-or-url> [github-org]

# Example: Convert a local project directory
./scripts/convert-to-validated-pattern.sh my-app ./my-app-repo myorg

# Example: Convert directly from a Git repository URL
./scripts/convert-to-validated-pattern.sh my-app https://github.com/user/repo.git myorg

# Example: Convert from GitLab or other Git hosting
./scripts/convert-to-validated-pattern.sh my-app https://gitlab.com/user/repo.git myorg
```

**Features:**
- Accepts both local directories and Git repository URLs
- Automatically clones remote repositories for conversion
- Creates complete validated pattern directory structure
- Migrates existing Helm charts
- Generates GitOps configuration files
- Sets up multi-cluster support
- Includes ShellCheck validation
- Provides conversion report with next steps
- Cleans up temporary files automatically
- **NEW**: Automatically detects patterns and applies specific configurations:
  - AI/ML patterns → GPU operators, model serving, GPU-aware autoscaling
  - Security patterns → Security operators, network policies, RBAC
  - Scaling patterns → KEDA, Prometheus, HPA/VPA configurations
  - Data processing → Kafka operators, pipeline optimizations

### 🐍 convert-to-validated-pattern.py
Python wrapper providing backward compatibility while using the new Python implementation.

**Usage:**
```bash
# Same interface as bash script
./scripts/convert-to-validated-pattern.py my-pattern ./source-repo myorg
```

### 📋 migrate-charts.sh
Migrates Helm charts from a source repository to the validated pattern structure.

**Usage:**
```bash
./scripts/migrate-charts.sh <source-repo-path> [chart-names...]

# Migrate all charts found in source repo
./scripts/migrate-charts.sh /path/to/source-repo

# Migrate specific charts only
./scripts/migrate-charts.sh /path/to/source-repo prometheus grafana

# The script will:
# - Search for Chart.yaml files in the source repo
# - Copy charts to migrated-charts/<chart-name>/
# - Preserve chart structure and dependencies
```

### ✅ validate-deployment.sh
Validates a deployed pattern to ensure all components are running correctly.

**Usage:**
```bash
# Run from within a pattern directory
./scripts/validate-deployment.sh

# Or specify the pattern directory
cd <pattern-dir> && ../scripts/validate-deployment.sh
```

**Checks:**
- Required operators installation
- Namespace creation
- Application deployment status
- Service availability
- Route accessibility

### 🚀 deploy-models.sh
Deploys AI/ML models to a pattern (specific to AI patterns).

**Usage:**
```bash
./scripts/deploy-models.sh [namespace]

# Default namespace: ai-llm-serving
./scripts/deploy-models.sh

# Custom namespace
./scripts/deploy-models.sh my-models-namespace
```

## Prerequisites

- OpenShift CLI (`oc`) installed and configured
- Helm 3.x
- Git
- Make
- ShellCheck (for script validation)
- Access to an OpenShift cluster (for deployment/validation)
- Python 3.9+ (for Python converter)

## Installation

1. Clone this repository:
```bash
git clone <this-repo>
cd <repo-name>
```

2. Make scripts executable:
```bash
chmod +x scripts/*.sh
```

3. Install ShellCheck (optional but recommended):
```bash
# macOS
brew install shellcheck

# Linux
apt-get install shellcheck  # Debian/Ubuntu
yum install ShellCheck      # RHEL/CentOS
```

4. Install Python converter (recommended):
```bash
cd scripts/validated-pattern-converter
./install.sh
```

## Workflow Example

Complete workflow for converting and deploying a project:

```bash
# 1. Convert your project to a validated pattern
./scripts/convert-to-validated-pattern.sh my-app ./source-repo myorg

# 2. Navigate to the created pattern
cd my-app-validated-pattern

# 3. Clone the common framework
git clone https://github.com/validatedpatterns-docs/common.git

# 4. Create pattern.sh symlink
ln -s ./common/scripts/pattern-util.sh pattern.sh

# 5. Configure secrets
cp values-secret.yaml.template values-secret.yaml
# Edit values-secret.yaml with your credentials

# 6. Deploy the pattern
make install

# 7. Validate deployment
../scripts/validate-deployment.sh

# 8. Deploy models (if applicable)
../scripts/deploy-models.sh
```

## Pattern Structure Created

The conversion tool creates:
```
pattern-name/
├── ansible/              # Ansible automation
├── charts/              # Helm charts
│   ├── hub/            # Hub cluster apps
│   └── region/         # Edge cluster apps
├── common/             # Framework (cloned separately)
├── migrated-charts/    # Original charts
├── overrides/          # Platform overrides
├── scripts/            # Pattern scripts
├── tests/              # Test configurations
├── values-*.yaml       # Configuration files
├── Makefile            # Build automation
├── pattern.sh          # Pattern utilities
└── README.md           # Documentation
```

## Configuration Files

- `values-global.yaml` - Global pattern configuration
- `values-hub.yaml` - Hub cluster specific settings
- `values-region.yaml` - Edge cluster settings
- `values-secret.yaml.template` - Secret template
- `pattern-metadata.yaml` - Pattern metadata

## Troubleshooting

### Common Issues

1. **"common/Makefile not found"**
   - Clone the common framework: `git clone https://github.com/validatedpatterns-docs/common.git`

2. **ShellCheck warnings**
   - All scripts are ShellCheck compliant
   - Run `shellcheck scripts/*.sh` to verify

3. **Pattern won't deploy**
   - Check OpenShift login: `oc whoami`
   - Verify cluster version: `oc version`
   - Check operator availability

## ShellCheck Configuration

All shell scripts in this repository are validated with ShellCheck and follow best practices for bash scripting.

### Code Standards

All scripts have been updated to follow ShellCheck recommendations:
- Use `[[ ]]` instead of `[ ]` for tests (more robust in bash)
- Add `|| true` to commands in process substitution when return value isn't needed
- Use `${VAR}` syntax for all variable expansions
- Add `# shellcheck source=/dev/null` before sourcing dynamic files

### Configuration

We use a minimal `.shellcheckrc` file that:
- Sets shell to bash
- Enables all checks by default
- No disabled warnings - all code follows ShellCheck best practices

### Running ShellCheck

```bash
# Check all scripts
shellcheck scripts/*.sh

# Check all scripts recursively
find scripts -name "*.sh" -type f | xargs shellcheck

# Check with specific shell
shellcheck -s bash scripts/*.sh
```

All scripts pass ShellCheck with zero warnings or errors.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure ShellCheck passes
5. Submit a pull request

## Resources

- [Validated Patterns Documentation](https://validatedpatterns.io)
- [MultiCloud GitOps Pattern](https://github.com/validatedpatterns/multicloud-gitops)
- [Common Framework](https://github.com/validatedpatterns-docs/common)
- [ShellCheck](https://www.shellcheck.net)

## License

Apache License 2.0