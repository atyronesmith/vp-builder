# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the AWS LLMD Validated Patterns repository - a comprehensive framework for converting OpenShift/Kubernetes projects into Red Hat Validated Patterns. It includes both reference implementations (AI Virtual Agent, RAG Blueprint) and sophisticated conversion tooling.

## Common Development Commands

### Pattern Conversion
```bash
# Convert a project to validated pattern
make convert APP_NAME=myapp SOURCE_DIR=./source ORG=myorg

# Or use the CLI tool directly
./vp-convert <pattern-name> <source-repo>

# Create new pattern from template
make new-pattern NAME=my-pattern
```

### Build and Test
```bash
# Validate pattern structure
make validate-pattern PATTERN_DIR=./my-pattern

# Run all tests for a pattern
make test-pattern PATTERN_DIR=./my-pattern

# Lint YAML files
make lint-yaml PATTERN_DIR=./my-pattern

# Lint shell scripts
make lint-shell PATTERN_DIR=./my-pattern
```

### Python Development (Validated Pattern Converter)
```bash
cd scripts/validated-pattern-converter
make install-dev    # Install with dev dependencies
make test          # Run tests
make coverage      # Run tests with coverage
make lint          # Run linting (flake8 + mypy)
make format        # Format code (black + isort)
```

### Frontend Development (AI Virtual Agent)
```bash
cd ai-virtual-agent/frontend
npm install
npm run dev        # Start development server
npm run lint       # Run ESLint
npm run format     # Format with Prettier
npm run build      # Production build
```

### Deployment
```bash
# Deploy pattern to OpenShift
make deploy-pattern PATTERN_DIR=./my-pattern

# Deploy AI Virtual Agent
cd ai-virtual-agent/deploy/helm
make install NAMESPACE=my-namespace HF_TOKEN=<token>
```

## Architecture and Structure

### Pattern Converter Architecture
The `vp-convert` tool uses a modular architecture:
- **Analyzer**: Pattern detection using rule-based system with confidence scoring
- **Generator**: Creates validated pattern structure with GitOps integration
- **Validator**: Ensures pattern compliance and correctness
- **Templates**: Jinja2-based generation for consistency

Key patterns detected: AI/ML Pipeline, Security, Scaling, Data Processing, MLOps

### Project Structure
```
/
├── scripts/validated-pattern-converter/  # Modern Python-based converter
├── ai-virtual-agent/                    # Reference AI assistant implementation
├── RAG-Blueprint/                       # RAG reference architecture
├── multicloud-gitops/                   # Reference validated pattern
└── Makefile                            # Main build orchestration
```

### Validated Pattern Structure
Each pattern follows this structure:
```
pattern-name/
├── charts/
│   ├── hub/                # Hub cluster charts
│   └── region/             # Regional cluster charts
├── values-*.yaml           # Environment-specific values
├── Makefile               # Pattern-specific targets
└── common/                # Shared configuration
```

## Key Development Guidelines

1. **Pattern Detection**: The converter uses a rule-based system. When adding new patterns, update `vpconverter/rules_engine.py` with appropriate rules and confidence thresholds.

2. **Helm Chart Migration**: Original charts are preserved in `migrated-charts/` directory. ArgoCD wrapper charts are generated in the standard structure.

3. **Testing**: Always validate patterns after conversion using `make validate-pattern`. This checks YAML syntax, Helm chart structure, and pattern compliance.

4. **Frontend Development**: AI Virtual Agent uses React with TypeScript and PatternFly UI. Follow existing component patterns and maintain type safety.

5. **Python Standards**: Use Poetry for dependency management, maintain type hints, and follow black/isort formatting standards.

6. **Shell Scripts**: All scripts must pass ShellCheck validation. Use the provided Makefile targets for linting.

## Critical Paths

- Pattern conversion logic: `scripts/validated-pattern-converter/vpconverter/`
- Pattern templates: `scripts/validated-pattern-converter/vpconverter/templates.py`
- AI Virtual Agent API: `ai-virtual-agent/backend/backend/main.py`
- Frontend routing: `ai-virtual-agent/frontend/src/Routes.tsx`
- Deployment charts: `*/deploy/helm/`