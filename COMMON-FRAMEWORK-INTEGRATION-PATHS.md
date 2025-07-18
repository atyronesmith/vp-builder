# Common Framework Integration Paths

## Executive Summary

The Common Framework is a critical component of validated patterns, providing Makefiles, scripts, and Ansible utilities. Currently, the converter requires users to manually clone it. This document explores multiple integration strategies, from simple to sophisticated, each with different trade-offs.

## Understanding the Common Framework

### What It Contains
- **Makefile**: Primary entry point for pattern operations
- **Scripts**: Utilities for pattern management
- **Ansible Components**: Now in separate repository (rhvp.cluster_utils)
- **No Helm Charts**: Charts moved to separate repositories (clustergroup-chart, etc.)

### Current Architecture
```
validated-pattern/
├── common/                    # Currently requires manual clone
│   ├── Makefile              # Main Makefile
│   ├── scripts/              # Utility scripts
│   └── requirements.yml      # Ansible requirements
├── Makefile                  # Delegates to common/Makefile
└── pattern.sh               # Symlink to common/scripts/pattern-util.sh
```

## Integration Paths

### Path 1: Git Submodule Integration (Traditional)

**Implementation:**
```bash
# In generator.py
def _add_git_submodule(self):
    """Add common as a git submodule."""
    subprocess.run([
        "git", "submodule", "add",
        "https://github.com/validatedpatterns-docs/common.git",
        "common"
    ], cwd=self.pattern_dir)

    # Create .gitmodules
    gitmodules_content = """[submodule "common"]
    path = common
    url = https://github.com/validatedpatterns-docs/common.git
    branch = main
"""
```

**Pros:**
- Standard Git approach
- Always up-to-date with upstream
- No duplication of code

**Cons:**
- Requires `git submodule update --init` on clone
- Can be confusing for users unfamiliar with submodules
- Breaks if upstream moves/changes

### Path 2: Lazy Download on First Use

**Implementation:**
```makefile
# In Makefile template
%:
    @if [ ! -d common ]; then \
        echo "Common framework not found. Downloading..."; \
        git clone https://github.com/validatedpatterns-docs/common.git common; \
    fi
    @make -f common/Makefile $@
```

**Pros:**
- Zero setup for users
- Works transparently
- No Git submodule complexity

**Cons:**
- First `make` command is slower
- No version pinning
- Requires internet on first use

### Path 3: Vendoring Critical Components

**Implementation:**
```python
# In generator.py
def _vendor_common_components(self):
    """Copy critical common components into the pattern."""
    common_files = {
        'Makefile': 'common/Makefile',
        'scripts/pattern-util.sh': 'scripts/pattern-util.sh',
        'scripts/ansible-setup.sh': 'scripts/ansible-setup.sh'
    }

    for src, dst in common_files.items():
        # Download and copy files
        self._download_and_copy(
            f"https://raw.githubusercontent.com/validatedpatterns-docs/common/main/{src}",
            self.pattern_dir / dst
        )
```

**Pros:**
- Self-contained patterns
- No external dependencies
- Version stability

**Cons:**
- Duplicated code
- Manual updates needed
- Larger repository size

### Path 4: Hybrid Approach (Bootstrap + Optional Full)

**Implementation:**
```python
# Create minimal bootstrap that can work standalone
def _create_hybrid_integration(self):
    # 1. Minimal Makefile that works without common
    makefile_content = """
.PHONY: install
install: bootstrap

.PHONY: bootstrap
bootstrap:
    @./scripts/pattern-bootstrap.sh

.PHONY: get-common
get-common:
    @if [ ! -d common ]; then \\
        git clone https://github.com/validatedpatterns-docs/common.git; \\
    fi

# If common exists, use it for everything else
ifneq (,$(wildcard common/Makefile))
%:
    @make -f common/Makefile $@
else
%:
    @echo "Run 'make get-common' for full functionality"
    @echo "Or use 'make bootstrap' for basic deployment"
endif
"""
```

**Pros:**
- Works without common for basic operations
- Full functionality available when needed
- Clear upgrade path

**Cons:**
- More complex Makefile
- Two different operation modes

### Path 5: Container-Based Common

**Implementation:**
```python
# Use container with common pre-installed
def _create_container_wrapper(self):
    script_content = """#!/bin/bash
# pattern.sh - Runs pattern operations in container

CONTAINER_IMAGE="quay.io/validatedpatterns/utility-container:latest"

podman run --rm -it \\
    -v $(pwd):/pattern:Z \\
    -w /pattern \\
    $CONTAINER_IMAGE \\
    make -f /opt/common/Makefile $@
"""
```

**Pros:**
- No local common needed
- Consistent environment
- All tools included

**Cons:**
- Requires container runtime
- Slower than native execution
- May have permission issues

### Path 6: Smart Pattern Installer

**Implementation:**
```python
def _create_pattern_installer(self):
    """Create an installer script that sets up everything."""
    installer_content = """#!/bin/bash
# install-pattern.sh - One-click pattern setup

echo "Setting up validated pattern..."

# Check for common
if [ ! -d common ]; then
    echo "Downloading common framework..."
    git clone https://github.com/validatedpatterns-docs/common.git common
fi

# Create symlink
if [ ! -L pattern.sh ]; then
    ln -s ./common/scripts/pattern-util.sh pattern.sh
    chmod +x pattern.sh
fi

# Check for dependencies
for cmd in oc helm ansible; do
    if ! command -v $cmd &> /dev/null; then
        echo "WARNING: $cmd not found"
    fi
done

echo "Pattern ready! Run 'make install' to deploy"
"""
```

**Pros:**
- Single command setup
- Checks dependencies
- User-friendly

**Cons:**
- Another script to maintain
- Platform-specific checks

### Path 7: Multi-Source Makefile

**Implementation:**
```makefile
# Advanced Makefile that tries multiple sources
COMMON_SOURCES := \\
    https://github.com/validatedpatterns-docs/common.git \\
    https://gitlab.com/validatedpatterns/common.git \\
    https://github.com/hybrid-cloud-patterns/common.git

.PHONY: get-common
get-common:
    @for repo in $(COMMON_SOURCES); do \\
        if git clone $$repo common 2>/dev/null; then \\
            echo "Successfully cloned from $$repo"; \\
            break; \\
        fi; \\
    done
```

**Pros:**
- Resilient to repository moves
- Multiple fallback options
- Future-proof

**Cons:**
- More complex
- May get outdated versions

### Path 8: Framework-as-a-Service

**Implementation:**
Create a web service that provides common functionality:

```python
def _create_api_integration(self):
    """Use common framework via API."""
    api_script = """#!/usr/bin/env python3
import requests

API_BASE = "https://api.validatedpatterns.io/v1"

def run_make_target(target, pattern_data):
    response = requests.post(f"{API_BASE}/make/{target}",
                           json=pattern_data)
    return response.json()
"""
```

**Pros:**
- No local dependencies
- Always latest version
- Central management

**Cons:**
- Requires internet
- Dependency on service
- Privacy concerns

## Recommended Approach

Based on the analysis, I recommend a **Progressive Enhancement Strategy**:

### Phase 1: Lazy Download (Immediate)
Implement Path 2 - automatic download on first use. This provides immediate improvement with minimal complexity.

### Phase 2: Hybrid Integration (Short-term)
Implement Path 4 - provide both bootstrap and full common support. This gives users flexibility.

### Phase 3: Smart Installer (Medium-term)
Add Path 6 - create an intelligent installer that handles all setup tasks.

### Phase 4: Container Option (Long-term)
Offer Path 5 as an alternative for users who prefer containerized environments.

## Implementation Priority

1. **Update Makefile Template** (1 day)
   ```makefile
   # Auto-download common if missing
   common/Makefile:
       @echo "Downloading common framework..."
       @git clone https://github.com/validatedpatterns-docs/common.git common

   %: common/Makefile
       @make -f common/Makefile $@
   ```

2. **Add Setup Script** (1 day)
   - Create `scripts/setup-pattern.sh`
   - Check and install common
   - Verify dependencies
   - Create symlinks

3. **Update Documentation** (0.5 day)
   - Explain auto-download behavior
   - Document manual options
   - Add troubleshooting guide

4. **Add Container Wrapper** (1 day)
   - Create `pattern-container.sh`
   - Test with utility container
   - Document usage

## Conclusion

The common framework integration doesn't have to be all-or-nothing. By implementing a progressive enhancement strategy, we can provide:

1. **Zero-friction experience** for new users (auto-download)
2. **Flexibility** for advanced users (multiple options)
3. **Reliability** for production use (vendoring/containers)
4. **Future-proofing** for framework evolution

The key is to start simple (lazy download) and progressively add more sophisticated options based on user needs and feedback.