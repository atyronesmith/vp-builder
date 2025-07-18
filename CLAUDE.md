# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the AWS LLMD Validated Patterns repository - a comprehensive framework for converting OpenShift/Kubernetes projects into Red Hat Validated Patterns. It includes both reference implementations (AI Virtual Agent, RAG Blueprint) and sophisticated conversion tooling.

## Learning and Rules from Development Sessions

### Variable Expansion Implementation
- The validated pattern converter now includes a comprehensive GNU Make variable expansion engine
- When analyzing Makefiles, the converter expands variables to better understand deployment processes
- Key files: `vpconverter/variable_expander.py`, `vpconverter/makefile_analyzer.py`
- Handles: $(VAR), ${VAR}, automatic variables ($@, $<, etc.), functions (wildcard, shell, etc.)

### Code Quality and Validation
```bash
# Repository-wide validation
make validate-basic      # Quick validation (shellcheck + python syntax)
make validate-all        # Comprehensive validation
make shellcheck         # Check all bash scripts
make python-syntax      # Check Python syntax

# Converter-specific validation
cd scripts/validated-pattern-converter
make validate-basic     # Basic checks
make validate-all       # Full validation with Poetry
```

### Important Patterns and Conventions
1. **Makefile Analysis**: Extended parent directory search to 4 levels for better detection
2. **Variable Parsing**: Fixed to properly handle `:=` assignments and distinguish from targets
3. **Unexpanded Variables**: Some variables (like LLM, NAMESPACE) are intentionally undefined
4. **Function Detection**: Now detects shell, call, eval, and other GNU Make functions

### Documentation Structure
- `/claude/` directory contains comprehensive validated patterns documentation
- Key references:
  - `validated-patterns-reference.md` - Official docs summary
  - `converter-enhancement-plan.md` - Development roadmap
  - `variable-expansion-implementation-summary.md` - Technical details

### Development Workflow
1. Always run `make validate-basic` before committing
2. Use `--analyze-only` flag with converter to understand projects before conversion
3. Check `/claude/` directory for architectural decisions and patterns
4. Exclude generated directories (ai-virtual-agent/, rag-validated-pattern/) from commits

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
- Variable expansion engine: `scripts/validated-pattern-converter/vpconverter/variable_expander.py`
- Makefile analyzer: `scripts/validated-pattern-converter/vpconverter/makefile_analyzer.py`
- AI Virtual Agent API: `ai-virtual-agent/backend/backend/main.py`
- Frontend routing: `ai-virtual-agent/frontend/src/Routes.tsx`
- Deployment charts: `*/deploy/helm/`

## Session Learnings and Context

### Validated Patterns Framework
- Validated patterns use a hub-and-spoke architecture with GitOps (ArgoCD)
- ClusterGroup charts are the entry point - they're what get deployed first
- Values hierarchy: values-secret.yaml > values-*.yaml > values-global.yaml
- Common framework integration via git subtree is standard practice

### Converter Enhancement Priorities (from enhancement plan)
1. ✅ **Variable Expansion Engine** - COMPLETED
2. ClusterGroup Chart Generation - Next priority
3. Values Structure Alignment
4. Bootstrap Application Creation
5. Common Framework Integration
6. Product Version Tracking
7. Imperative Job Templates
8. Enhanced Validation

### Key Technical Decisions
- Use Jinja2 templating for consistency across generated files
- Preserve original Helm charts in migrated-charts/ directory
- Generate ArgoCD wrapper charts for GitOps deployment
- Implement rule-based pattern detection with confidence scoring
- Cache variable expansions for performance

### Testing and Validation Strategy
- Always test with real patterns (multicloud-gitops, ai-virtual-agent)
- Use --analyze-only flag for understanding before conversion
- Validate generated patterns deploy successfully to OpenShift
- Ensure backwards compatibility with existing patterns