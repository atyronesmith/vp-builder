# Red Hat Validated Patterns Tools

This repository contains tools and documentation for converting projects into Red Hat Validated Patterns.

## 🚀 Quick Start

Convert any OpenShift/Kubernetes project to a validated pattern:

```bash
./scripts/convert-to-validated-pattern.sh my-app ./my-app-repo myorg
```

## 📁 Repository Structure

```
.
├── scripts/                    # Conversion and deployment tools
│   ├── convert-to-validated-pattern.sh
│   ├── migrate-charts.sh
│   ├── validate-deployment.sh
│   └── deploy-models.sh
├── aiops-validated-pattern/    # Example converted pattern
├── docs/                       # Documentation (if created)
└── README-TOOLS.md            # This file
```

## 📚 Documentation

- [Scripts Documentation](scripts/README.md) - Detailed usage for all tools
- [Conversion Rules](CONVERSION-RULES.md) - Rules and requirements for patterns
- [Conversion Process](CONVERSION-PROCESS.md) - Step-by-step conversion guide
- [Pattern Templates](PATTERN-TEMPLATES.md) - Template files for patterns
- [Pattern Corrections](PATTERN-CORRECTIONS.md) - Common issues and fixes
- [Automated Conversion](AUTOMATED-CONVERSION.md) - Automation guide

## 🛠️ Tools Overview

### Pattern Conversion
- **convert-to-validated-pattern.sh** - Main conversion tool
- **migrate-charts.sh** - Helm chart migration utility

### Pattern Management
- **validate-deployment.sh** - Deployment validation
- **deploy-models.sh** - AI/ML model deployment

## 📋 Prerequisites

- OpenShift CLI (`oc`)
- Helm 3.x
- Git
- Make
- ShellCheck (recommended)

## 🔄 Typical Workflow

1. **Convert your project:**
   ```bash
   ./scripts/convert-to-validated-pattern.sh my-app ./source-repo myorg
   ```

2. **Navigate to pattern:**
   ```bash
   cd my-app-validated-pattern
   ```

3. **Setup framework:**
   ```bash
   git clone https://github.com/validatedpatterns-docs/common.git
   ln -s ./common/scripts/pattern-util.sh pattern.sh
   ```

4. **Configure and deploy:**
   ```bash
   cp values-secret.yaml.template values-secret.yaml
   # Edit values-secret.yaml
   make install
   ```

5. **Validate:**
   ```bash
   ../scripts/validate-deployment.sh
   ```

## 🌟 Features

- ✅ Automated pattern structure creation
- ✅ Helm chart migration
- ✅ GitOps configuration
- ✅ Multi-cluster support
- ✅ ShellCheck validated scripts
- ✅ Comprehensive documentation
- ✅ Platform-specific overrides

## 📖 Learn More

- [Validated Patterns](https://validatedpatterns.io)
- [MultiCloud GitOps](https://github.com/validatedpatterns/multicloud-gitops)
- [Pattern Framework](https://github.com/validatedpatterns-docs/common)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

Apache License 2.0

---

**Need help?** Check the [scripts documentation](scripts/README.md) or open an issue.