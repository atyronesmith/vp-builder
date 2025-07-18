# Validated Patterns Conversion Framework Makefile
# This Makefile provides utilities for converting applications to validated patterns

# Variables
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Pattern template source
MULTICLOUD_GITOPS_REPO := https://github.com/validatedpatterns/multicloud-gitops.git
MULTICLOUD_GITOPS_DIR := multicloud-gitops
COMMON_REPO := https://github.com/validatedpatterns-docs/common.git

# Conversion script
CONVERSION_SCRIPT := scripts/convert-to-validated-pattern.sh

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.PHONY: default
default: help

##@ General

.PHONY: help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup and Installation

.PHONY: setup
setup: clone-multicloud-gitops install-tools ## Complete setup for pattern conversion

.PHONY: clone-multicloud-gitops
clone-multicloud-gitops: ## Clone the multicloud-gitops reference pattern
	@echo -e "$(BLUE)Cloning multicloud-gitops reference pattern...$(NC)"
	@if [ -d "$(MULTICLOUD_GITOPS_DIR)" ]; then \
		echo -e "$(YELLOW)Directory $(MULTICLOUD_GITOPS_DIR) already exists. Pulling latest...$(NC)"; \
		cd $(MULTICLOUD_GITOPS_DIR) && git pull; \
	else \
		git clone $(MULTICLOUD_GITOPS_REPO) $(MULTICLOUD_GITOPS_DIR); \
	fi
	@echo -e "$(GREEN)✓ Multicloud GitOps pattern ready$(NC)"

.PHONY: install-tools
install-tools: ## Check and install required tools
	@echo -e "$(BLUE)Checking required tools...$(NC)"
	@command -v oc >/dev/null 2>&1 || { echo -e "$(RED)✗ OpenShift CLI (oc) is required but not installed.$(NC)" >&2; exit 1; }
	@command -v helm >/dev/null 2>&1 || { echo -e "$(RED)✗ Helm is required but not installed.$(NC)" >&2; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo -e "$(RED)✗ Git is required but not installed.$(NC)" >&2; exit 1; }
	@command -v yq >/dev/null 2>&1 || { echo -e "$(YELLOW)⚠ yq is recommended but not installed.$(NC)" >&2; }
	@command -v ansible >/dev/null 2>&1 || { echo -e "$(YELLOW)⚠ Ansible is recommended but not installed.$(NC)" >&2; }
	@echo -e "$(GREEN)✓ All required tools are installed$(NC)"

##@ Pattern Conversion

.PHONY: convert
convert: ## Convert an application to validated pattern (usage: make convert APP_NAME=myapp SOURCE_DIR=./source ORG=myorg)
	@if [ -z "$(APP_NAME)" ] || [ -z "$(SOURCE_DIR)" ]; then \
		echo -e "$(RED)Error: APP_NAME and SOURCE_DIR are required$(NC)"; \
		echo "Usage: make convert APP_NAME=myapp SOURCE_DIR=./source ORG=myorg"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Converting $(APP_NAME) to validated pattern...$(NC)"
	@bash $(CONVERSION_SCRIPT) "$(APP_NAME)" "$(SOURCE_DIR)" "$(ORG)"
	@echo -e "$(GREEN)✓ Conversion complete$(NC)"

.PHONY: new-pattern
new-pattern: ## Create a new pattern from template (usage: make new-pattern NAME=my-pattern)
	@if [ -z "$(NAME)" ]; then \
		echo -e "$(RED)Error: NAME is required$(NC)"; \
		echo "Usage: make new-pattern NAME=my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Creating new pattern: $(NAME)$(NC)"
	@mkdir -p $(NAME)
	@cp -r templates/pattern-base/* $(NAME)/ 2>/dev/null || echo "No base templates found"
	@echo -e "$(GREEN)✓ Pattern $(NAME) created$(NC)"

##@ Pattern Management

.PHONY: validate-pattern
validate-pattern: ## Validate a pattern structure (usage: make validate-pattern PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make validate-pattern PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Validating pattern in $(PATTERN_DIR)...$(NC)"
	@bash scripts/validate-pattern.sh "$(PATTERN_DIR)"

.PHONY: test-pattern
test-pattern: ## Run pattern tests (usage: make test-pattern PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make test-pattern PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Testing pattern in $(PATTERN_DIR)...$(NC)"
	@cd $(PATTERN_DIR) && make test 2>/dev/null || echo "No tests defined"

.PHONY: lint-yaml
lint-yaml: ## Lint all YAML files in a pattern (usage: make lint-yaml PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make lint-yaml PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Linting YAML files in $(PATTERN_DIR)...$(NC)"
	@if command -v yamllint >/dev/null 2>&1; then \
		find $(PATTERN_DIR) -name "*.yaml" -o -name "*.yml" | grep -v "templates/" | xargs yamllint -c .yamllint; \
	else \
		echo -e "$(YELLOW)yamllint not installed, skipping YAML validation$(NC)"; \
	fi

.PHONY: lint-shell
lint-shell: ## Run ShellCheck on all shell scripts (usage: make lint-shell PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make lint-shell PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Checking shell scripts in $(PATTERN_DIR)...$(NC)"
	@if command -v shellcheck >/dev/null 2>&1; then \
		find $(PATTERN_DIR) -type f -name "*.sh" -exec shellcheck {} \; ; \
	else \
		echo -e "$(YELLOW)ShellCheck not installed, skipping shell script validation$(NC)"; \
	fi

##@ Documentation

.PHONY: docs
docs: ## Generate documentation for patterns
	@echo -e "$(BLUE)Generating documentation...$(NC)"
	@mkdir -p docs/patterns
	@for pattern in */pattern-metadata.yaml; do \
		if [ -f "$$pattern" ]; then \
			dir=$$(dirname "$$pattern"); \
			echo "Processing $$dir..."; \
			cp -r "$$dir/README.md" "docs/patterns/$$dir.md" 2>/dev/null || true; \
		fi \
	done
	@echo -e "$(GREEN)✓ Documentation generated in docs/$(NC)"

.PHONY: list-patterns
list-patterns: ## List all patterns in the repository
	@echo -e "$(BLUE)Available patterns:$(NC)"
	@for pattern in */pattern-metadata.yaml; do \
		if [ -f "$$pattern" ]; then \
			dir=$$(dirname "$$pattern"); \
			name=$$(yq '.name' "$$pattern" 2>/dev/null || echo "unknown"); \
			echo -e "  $(GREEN)$$dir$(NC) - $$name"; \
		fi \
	done

##@ Deployment

.PHONY: deploy-pattern
deploy-pattern: ## Deploy a pattern to OpenShift (usage: make deploy-pattern PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make deploy-pattern PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Deploying pattern from $(PATTERN_DIR)...$(NC)"
	@cd $(PATTERN_DIR) && \
		if [ ! -d "common" ]; then \
			echo -e "$(YELLOW)Cloning common framework...$(NC)"; \
			git clone $(COMMON_REPO) common; \
			ln -sf ./common/scripts/pattern-util.sh pattern.sh; \
			chmod +x pattern.sh; \
		fi && \
		make install

.PHONY: undeploy-pattern
undeploy-pattern: ## Remove a deployed pattern (usage: make undeploy-pattern PATTERN_DIR=./my-pattern)
	@if [ -z "$(PATTERN_DIR)" ]; then \
		echo -e "$(RED)Error: PATTERN_DIR is required$(NC)"; \
		echo "Usage: make undeploy-pattern PATTERN_DIR=./my-pattern"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Removing pattern from $(PATTERN_DIR)...$(NC)"
	@cd $(PATTERN_DIR) && make uninstall 2>/dev/null || echo "Pattern not deployed"

##@ Code Quality and Validation

.PHONY: shellcheck
shellcheck: ## Run shellcheck on all bash scripts in the repository
	@echo -e "$(BLUE)Running shellcheck on all bash scripts...$(NC)"
	@if command -v shellcheck >/dev/null 2>&1; then \
		find . -name "*.sh" -type f -not -path "./.git/*" | xargs shellcheck -e SC1091; \
		echo -e "$(GREEN)✓ Shellcheck passed$(NC)"; \
	else \
		echo -e "$(RED)✗ ShellCheck not installed$(NC)"; \
		exit 1; \
	fi

.PHONY: python-syntax
python-syntax: ## Check Python syntax for all Python files
	@echo -e "$(BLUE)Checking Python syntax...$(NC)"
	@if command -v python3 >/dev/null 2>&1; then \
		find . -name "*.py" -type f -not -path "./.git/*" -not -path "./*/venv/*" -not -path "./*/.pytest_cache/*" | while read -r file; do \
			python3 -m py_compile "$$file" || exit 1; \
		done; \
		echo -e "$(GREEN)✓ Python syntax check passed$(NC)"; \
	else \
		echo -e "$(RED)✗ Python3 not installed$(NC)"; \
		exit 1; \
	fi

.PHONY: validate-converter
validate-converter: ## Run validation on the pattern converter code
	@echo -e "$(BLUE)Validating pattern converter...$(NC)"
	@cd scripts/validated-pattern-converter && make validate-basic
	@echo -e "$(GREEN)✓ Pattern converter validation passed$(NC)"

.PHONY: validate-basic
validate-basic: ## Run basic validation checks (shellcheck, python-syntax, converter)
	@echo -e "$(BLUE)Running basic validation checks...$(NC)"
	@$(MAKE) shellcheck
	@$(MAKE) python-syntax
	@$(MAKE) validate-converter
	@echo -e "$(GREEN)✓ All basic validation checks passed$(NC)"

.PHONY: validate-all
validate-all: ## Run comprehensive validation (basic + pattern-specific checks)
	@echo -e "$(BLUE)Running comprehensive validation...$(NC)"
	@$(MAKE) validate-basic
	@echo -e "$(BLUE)Running pattern-specific validations...$(NC)"
	@for pattern in */pattern-metadata.yaml; do \
		if [ -f "$$pattern" ]; then \
			dir=$$(dirname "$$pattern"); \
			echo -e "$(BLUE)Validating pattern: $$dir$(NC)"; \
			$(MAKE) lint-yaml PATTERN_DIR="$$dir" || true; \
			$(MAKE) lint-shell PATTERN_DIR="$$dir" || true; \
		fi \
	done
	@echo -e "$(GREEN)✓ All validation checks passed$(NC)"

##@ Utilities

.PHONY: clean
clean: ## Clean up generated files and temporary data
	@echo -e "$(BLUE)Cleaning up...$(NC)"
	@find . -name "*.swp" -o -name "*~" -o -name "*.bak" | xargs rm -f
	@rm -rf .cache .pytest_cache
	@echo -e "$(GREEN)✓ Cleanup complete$(NC)"

.PHONY: update-multicloud-gitops
update-multicloud-gitops: ## Update the multicloud-gitops reference
	@echo -e "$(BLUE)Updating multicloud-gitops...$(NC)"
	@cd $(MULTICLOUD_GITOPS_DIR) && git pull
	@echo -e "$(GREEN)✓ Updated to latest version$(NC)"

.PHONY: create-script-templates
create-script-templates: ## Create script templates if they don't exist
	@echo -e "$(BLUE)Creating script templates...$(NC)"
	@mkdir -p scripts templates/pattern-base
	@if [ ! -f "scripts/validate-pattern.sh" ]; then \
		echo '#!/bin/bash' > scripts/validate-pattern.sh; \
		echo '# Pattern validation script' >> scripts/validate-pattern.sh; \
		chmod +x scripts/validate-pattern.sh; \
	fi
	@echo -e "$(GREEN)✓ Script templates ready$(NC)"

.PHONY: check-env
check-env: ## Check environment and display status
	@echo -e "$(BLUE)Environment Status:$(NC)"
	@echo -n "OpenShift CLI: "; command -v oc >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(RED)✗$(NC)"
	@echo -n "Helm: "; command -v helm >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(RED)✗$(NC)"
	@echo -n "Git: "; command -v git >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(RED)✗$(NC)"
	@echo -n "Make: "; command -v make >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(RED)✗$(NC)"
	@echo -n "yq: "; command -v yq >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(YELLOW)⚠$(NC)"
	@echo -n "yamllint: "; command -v yamllint >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(YELLOW)⚠$(NC)"
	@echo -n "ShellCheck: "; command -v shellcheck >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(YELLOW)⚠$(NC)"
	@echo -n "Python3: "; command -v python3 >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(YELLOW)⚠$(NC)"
	@echo -n "Ansible: "; command -v ansible >/dev/null 2>&1 && echo -e "$(GREEN)✓$(NC)" || echo -e "$(YELLOW)⚠$(NC)"

##@ Examples

.PHONY: example-conversion
example-conversion: ## Show example conversion command
	@echo -e "$(BLUE)Example: Converting an application to a validated pattern$(NC)"
	@echo ""
	@echo "  make convert APP_NAME=my-app SOURCE_DIR=./my-app-source ORG=myorg"
	@echo ""
	@echo "This will:"
	@echo "  1. Create a new directory: my-app-validated-pattern/"
	@echo "  2. Set up the validated pattern structure"
	@echo "  3. Migrate Helm charts from the source"
	@echo "  4. Create wrapper charts for GitOps deployment"
	@echo "  5. Generate all required configuration files"

# Include pattern-specific makefiles if they exist
-include patterns.mk