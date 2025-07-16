# Red Hat Validated Patterns Tools and Documentation

## 🎯 Project Overview

This repository provides comprehensive tools and documentation for converting any OpenShift/Kubernetes project into a Red Hat Validated Pattern. It includes automated conversion scripts, validation tools, templates, and best practices documentation.

## 🚀 Quick Start

Convert any project to a validated pattern in minutes:

```bash
./scripts/convert-to-validated-pattern.sh my-pattern ./source-repo myorg
```

## 📚 What's Included

### 🛠️ Tools
- **Conversion Script** - Automated pattern structure creation
- **Chart Migration** - Helm chart migration utility
- **Pattern Validation** - Comprehensive validation tool
- **Deployment Scripts** - Pattern deployment helpers

### 📖 Documentation
- **[Conversion Rules](CONVERSION-RULES.md)** - Requirements and specifications
- **[Conversion Process](CONVERSION-PROCESS.md)** - Step-by-step guide
- **[Pattern Templates](PATTERN-TEMPLATES.md)** - Ready-to-use templates
- **[Pattern Corrections](PATTERN-CORRECTIONS.md)** - Common issues and fixes
- **[Automated Conversion](AUTOMATED-CONVERSION.md)** - Automation guide
- **[Scripts Documentation](scripts/README.md)** - Tool usage guide

## 🏗️ Pattern Structure

The tools create a standard validated pattern structure:

```
pattern-name/
├── ansible/              # Ansible automation
│   └── site.yaml        # Main playbook
├── charts/              # Helm charts
│   ├── hub/            # Hub cluster apps
│   └── region/         # Edge cluster apps
├── common/             # Framework (cloned separately)
├── migrated-charts/    # Original application charts
├── overrides/          # Platform-specific values
├── scripts/            # Pattern-specific scripts
├── tests/              # Test configurations
├── values-*.yaml       # Configuration files
├── Makefile            # Build automation
└── README.md           # Documentation
```

## 🔧 Key Features

### ✅ Automated Conversion
- Complete directory structure creation
- Helm chart migration and wrapping
- GitOps configuration with ArgoCD
- Multi-cluster support setup
- Platform override templates

### ✅ Validation & Compliance
- Pattern structure validation
- YAML syntax checking
- Helm chart validation
- ShellCheck for scripts
- Operator dependency checking

### ✅ GitOps Integration
- ArgoCD application templates
- MultiSourceConfig support
- Automated sync policies
- Wave-based deployments

### ✅ Multi-Platform Support
- AWS, Azure, GCP overrides
- Storage class configuration
- Platform-specific settings

## 📋 Prerequisites

- OpenShift Container Platform 4.12+
- Helm 3.x
- Git
- Make
- ShellCheck (recommended)
- Python with PyYAML (optional)

## 🚦 Getting Started

### 1. Convert Your Project

```bash
# Basic conversion
./scripts/convert-to-validated-pattern.sh my-app ./my-app-repo myorg

# The script will:
# - Create pattern directory structure
# - Generate configuration files
# - Migrate Helm charts
# - Set up GitOps integration
# - Clone multicloud-gitops reference (if needed)
```

### 2. Complete Setup

```bash
cd my-app-validated-pattern

# Clone common framework
git clone https://github.com/validatedpatterns-docs/common.git

# Create pattern symlink
ln -s ./common/scripts/pattern-util.sh pattern.sh

# Configure secrets
cp values-secret.yaml.template values-secret.yaml
vi values-secret.yaml
```

### 3. Validate Pattern

```bash
# Run validation
make validate-pattern PATTERN_DIR=.

# Or use the script directly
../scripts/validate-pattern.sh .
```

### 4. Deploy

```bash
# Deploy to OpenShift
make install

# Validate deployment
./scripts/validate-deployment.sh
```

## 📊 Validation Features

The pattern validation tool checks:
- ✓ Directory structure compliance
- ✓ Required files presence
- ✓ YAML syntax validity
- ✓ Helm chart structure
- ✓ ArgoCD multiSourceConfig
- ✓ Shell script quality (ShellCheck)
- ✓ Platform overrides
- ✓ Pattern metadata

## 🔄 Workflow Example

Complete validated pattern workflow:

```bash
# 1. Convert project
./scripts/convert-to-validated-pattern.sh retail-app ./retail-repo acme-corp

# 2. Navigate to pattern
cd retail-app-validated-pattern

# 3. Setup framework
git clone https://github.com/validatedpatterns-docs/common.git
ln -s ./common/scripts/pattern-util.sh pattern.sh

# 4. Customize values
vi values-global.yaml  # Update pattern specifics
vi values-hub.yaml     # Configure hub settings

# 5. Validate structure
make validate-pattern PATTERN_DIR=.

# 6. Deploy pattern
make install

# 7. Check deployment
./scripts/validate-deployment.sh
```

## 📝 Configuration Files

### Core Files
- `values-global.yaml` - Pattern-wide settings
- `values-hub.yaml` - Hub cluster configuration
- `values-secret.yaml` - Sensitive credentials (from template)
- `pattern-metadata.yaml` - Pattern information

### Platform Overrides
- `overrides/values-AWS.yaml` - AWS-specific settings
- `overrides/values-Azure.yaml` - Azure-specific settings
- `overrides/values-GCP.yaml` - GCP-specific settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Ensure validation passes
5. Submit a pull request

## 📚 Resources

- [Validated Patterns Documentation](https://validatedpatterns.io)
- [MultiCloud GitOps Pattern](https://github.com/validatedpatterns/multicloud-gitops) - **The reference pattern**
- [Common Framework](https://github.com/validatedpatterns-docs/common)
- [Red Hat OpenShift](https://www.openshift.com)

## 📌 Important Note

The **multicloud-gitops** repository is the reference implementation for all validated patterns. When creating a new pattern:
1. The conversion script will automatically clone it if not present
2. Use it as a reference for structure and best practices
3. Compare your pattern against it for compliance

## 📄 License

Apache License 2.0