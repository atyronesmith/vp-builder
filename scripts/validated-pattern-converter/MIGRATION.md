# Migration Guide: Bash to Python Converter

This guide helps you transition from the bash script (`convert-to-validated-pattern.sh`) to the new Python implementation.

## Key Improvements

The Python version provides:
- ✨ Better error handling and recovery
- 🎨 Rich terminal UI with progress indicators
- 🧩 Modular architecture for easier maintenance
- 🧪 Comprehensive test suite
- 📚 Better documentation and help
- 🔧 Extensible plugin architecture

## Installation

### Quick Start

```bash
cd scripts/validated-pattern-converter
./install.sh
```

### Manual Installation

With Poetry:
```bash
cd scripts/validated-pattern-converter
poetry install
poetry shell
```

With pip:
```bash
cd scripts/validated-pattern-converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage Comparison

### Basic Conversion

**Bash script:**
```bash
./scripts/convert-to-validated-pattern.sh my-pattern ./source-repo myorg
```

**Python (compatible mode):**
```bash
./scripts/convert-to-validated-pattern.py my-pattern ./source-repo myorg
```

**Python (new CLI):**
```bash
vp-convert convert my-pattern ./source-repo --github-org myorg
```

### From Git URL

**Bash script:**
```bash
./scripts/convert-to-validated-pattern.sh my-pattern https://github.com/user/repo.git
```

**Python:**
```bash
vp-convert convert my-pattern https://github.com/user/repo.git
```

## New Features

### Analysis Only
```bash
# Analyze without converting
vp-convert convert my-pattern ./source --analyze-only

# Or use the dedicated analyze command
vp-convert analyze ./source
```

### Validation
```bash
# Validate pattern structure
vp-convert validate ./my-pattern-validated-pattern

# Validate deployed pattern
vp-convert validate-deployment ./my-pattern-validated-pattern
```

### Custom Output Directory
```bash
vp-convert convert my-pattern ./source -o /custom/output/path
```

### Reference Pattern
```bash
# Clone reference pattern for comparison
vp-convert convert my-pattern ./source --clone-reference
```

### List Available Patterns
```bash
vp-convert list-patterns
```

## Feature Mapping

| Bash Script Feature | Python Equivalent |
|-------------------|------------------|
| Repository analysis | ✅ Enhanced with pattern detection |
| Helm chart migration | ✅ Improved with validation |
| Structure creation | ✅ Same functionality |
| Script migration | ✅ Smart filtering of useful scripts |
| YAML validation | ✅ Comprehensive validation |
| Git URL support | ✅ Same functionality |
| Progress display | ✅ Rich progress bars |
| Color output | ✅ Enhanced with Rich library |
| Error handling | ✅ Much improved |

## Environment Variables

The Python version respects the same environment variables:
- `GITHUB_ORG`: Default GitHub organization
- `NO_COLOR`: Disable colored output

## Backward Compatibility

The `convert-to-validated-pattern.py` wrapper script provides full backward compatibility:

```bash
# These are equivalent:
./scripts/convert-to-validated-pattern.sh my-pattern ./source myorg
./scripts/convert-to-validated-pattern.py my-pattern ./source myorg
```

## Troubleshooting

### Import Errors
If you see import errors, ensure you've installed dependencies:
```bash
cd scripts/validated-pattern-converter
poetry install  # or pip install -r requirements.txt
```

### Command Not Found
If `vp-convert` is not found:
1. Ensure you've activated the virtual environment
2. Or use `poetry run vp-convert`

### Permission Denied
Make scripts executable:
```bash
chmod +x scripts/convert-to-validated-pattern.py
chmod +x scripts/validated-pattern-converter/install.sh
```

## Advanced Usage

### Programmatic API
```python
from pathlib import Path
from vpconverter import PatternAnalyzer, PatternGenerator

# Analyze
analyzer = PatternAnalyzer(Path("./source"))
result = analyzer.analyze()

# Generate
generator = PatternGenerator("my-pattern", Path("./output"))
generator.generate(result)
```

### Custom Templates
You can modify templates in `vpconverter/templates.py` to customize generated files.

## Getting Help

```bash
# General help
vp-convert --help

# Command-specific help
vp-convert convert --help
vp-convert validate --help
```

## Reporting Issues

Please report issues with:
1. Python version (`python3 --version`)
2. Error message and traceback
3. Command that caused the error
4. Operating system