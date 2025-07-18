# AWS LLMD - Validated Patterns Repository

This repository contains validated patterns and tools for converting projects into Red Hat Validated Patterns.

## 🚀 Quick Start - Pattern Converter

We now have a simple top-level script to convert projects to validated patterns:

```bash
# Show help and examples
./vp-convert

# Convert a local project
./vp-convert my-pattern ./ai-virtual-agent

# Convert from GitHub
./vp-convert my-pattern https://github.com/user/repo.git

# Analyze only (no conversion)
./vp-convert my-pattern ./RAG-Blueprint --analyze-only
```

The converter will automatically:
- ✅ Check for dependencies and offer to install them
- ✅ Analyze your project structure
- ✅ Migrate Helm charts
- ✅ Generate validated pattern structure
- ✅ Validate the output

See [scripts/validated-pattern-converter/README.md](scripts/validated-pattern-converter/README.md) for full documentation.

## Scripts Overview

### 🔄 convert-to-validated-pattern.sh
Main conversion tool that transforms any OpenShift/Kubernetes project into a validated pattern structure.

**New Feature**: The converter now automatically detects architecture patterns and applies appropriate configurations:
- **AI/ML patterns** → GPU operators, model serving namespaces, GPU-aware autoscaling
- **Security patterns** → Security operators, network policies, RBAC configurations
- **Scaling patterns** → KEDA, Prometheus, HPA/VPA configurations
- **Data processing** → Kafka operators, pipeline optimizations

See [validated-pattern-converter/README.md](scripts/validated-pattern-converter/README.md#-automatic-pattern-specific-configuration) for details.

**Usage:**

## 📂 Repository Structure

```
aws-llmd/
├── vp-convert                    # 🆕 Easy pattern converter script
├── ai-virtual-agent/            # AI Virtual Agent project
├── RAG-Blueprint/               # RAG Blueprint project
├── multicloud-gitops/           # Reference pattern
├── scripts/                     # Conversion and utility scripts
│   ├── validated-pattern-converter/  # Python converter (v2.0)
│   ├── convert-to-validated-pattern.sh  # Original bash script
│   └── README.md               # Scripts documentation
└── README.md                   # This file
```

## 🛠️ Available Projects

### AI Virtual Agent
An AI-powered virtual assistant with:
- Admin interface
- Backend API
- Frontend application
- MCP servers

### RAG Blueprint
Reference Architecture Guide (RAG) implementation with:
- Data ingestion pipeline
- Frontend UI
- Jupyter notebooks
- Deployment configurations

### Multicloud GitOps
Reference implementation for validated patterns demonstrating:
- GitOps workflows
- Multi-cluster management
- Pattern structure best practices

## 🔧 Conversion Tools

### Python Converter (Recommended) - v2.0
Modern Python implementation with:
- Rich CLI interface
- Better error handling
- Comprehensive validation
- Modular architecture

### Bash Script (Legacy)
Original conversion script - still functional but consider using the Python version.

## 📚 Documentation

- [Validated Patterns Documentation](https://validatedpatterns.io)
- [Scripts Documentation](scripts/README.md)
- [Converter Documentation](scripts/validated-pattern-converter/README.md)

## 💻 Requirements

- Python 3.9+
- Git
- OpenShift CLI (`oc`) - for deployment
- Helm 3.x - for chart operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Apache License 2.0