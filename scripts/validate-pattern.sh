#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

# Check if pattern directory is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <pattern-directory>"
    exit 1
fi

PATTERN_DIR="$1"
ERRORS=0
WARNINGS=0

echo "======================================"
echo "Validating pattern: ${PATTERN_DIR}"
echo "======================================"

# Check if pattern directory exists
if [ ! -d "${PATTERN_DIR}" ]; then
    log_error "Pattern directory not found: ${PATTERN_DIR}"
    exit 1
fi

cd "${PATTERN_DIR}"

# Function to check file exists
check_file() {
    local file="$1"
    local required="${2:-true}"

    if [ -f "${file}" ]; then
        log_success "${file} exists"
        return 0
    else
        if [ "${required}" = "true" ]; then
            log_error "${file} MISSING (required)"
            ((ERRORS++))
        else
            log_warn "${file} missing (optional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    local dir="$1"
    local required="${2:-true}"

    if [ -d "${dir}" ]; then
        log_success "${dir}/ exists"
        return 0
    else
        if [ "${required}" = "true" ]; then
            log_error "${dir}/ MISSING (required)"
            ((ERRORS++))
        else
            log_warn "${dir}/ missing (optional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Function to validate YAML syntax
check_yaml() {
    local file="$1"

    if [ -f "${file}" ]; then
        if command -v yamllint >/dev/null 2>&1; then
            if yamllint -d relaxed "${file}" >/dev/null 2>&1; then
                log_success "${file} - valid YAML"
                return 0
            else
                log_error "${file} - invalid YAML syntax"
                ((ERRORS++))
                return 1
            fi
        else
            # Fall back to python if yamllint not available
            if python3 -c "import yaml; yaml.safe_load(open('${file}'))" 2>/dev/null; then
                log_success "${file} - valid YAML"
                return 0
            else
                # If neither yamllint nor PyYAML available, skip validation
                log_warn "${file} - YAML validation skipped (install yamllint or python3-yaml)"
                ((WARNINGS++))
                return 0
            fi
        fi
    fi
}

# Function to check if file contains required content
check_content() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    if [ -f "${file}" ]; then
        if grep -q "${pattern}" "${file}" 2>/dev/null; then
            log_success "${file} contains ${description}"
            return 0
        else
            log_error "${file} missing ${description}"
            ((ERRORS++))
            return 1
        fi
    fi
}

echo ""
echo "Checking mandatory directories..."
echo "======================================"
check_dir "ansible"
check_dir "charts"
check_dir "charts/hub"
check_dir "migrated-charts"
check_dir "overrides"
check_dir "scripts"
check_dir "tests"

echo ""
echo "Checking mandatory files..."
echo "======================================"
check_file "ansible.cfg"
check_file "ansible/site.yaml"
check_file "Makefile"
check_file "pattern-metadata.yaml"
check_file "values-global.yaml"
check_file "values-hub.yaml"
check_file "values-secret.yaml.template"
check_file "README.md"

# Check for pattern.sh or common directory
echo ""
echo "Checking pattern framework integration..."
echo "======================================"
if [ -L "pattern.sh" ] || [ -f "pattern.sh" ]; then
    log_success "pattern.sh exists"
elif [ -d "common" ]; then
    log_warn "common/ exists but pattern.sh symlink missing"
    ((WARNINGS++))
else
    log_warn "Neither pattern.sh nor common/ found - clone common framework before deployment"
    ((WARNINGS++))
fi

echo ""
echo "Checking optional files..."
echo "======================================"
check_file "values-region.yaml" false
check_file "CONTRIBUTING.md" false
check_file ".gitignore" false

echo ""
echo "Validating YAML syntax..."
echo "======================================"
# Use find to avoid issues with glob patterns
for yaml_file in $(find . -maxdepth 1 -name "values-*.yaml" -o -name "pattern-metadata.yaml" 2>/dev/null) ansible/site.yaml; do
    if [ -f "${yaml_file}" ]; then
        check_yaml "${yaml_file}"
    fi
done

echo ""
echo "Validating pattern configuration..."
echo "======================================"

# Check ansible.cfg
if [ -f "ansible.cfg" ]; then
    check_content "ansible.cfg" "host_key_checking" "host_key_checking setting"
fi

# Check ansible/site.yaml
if [ -f "ansible/site.yaml" ]; then
    check_content "ansible/site.yaml" "rhvp.cluster_utils" "rhvp.cluster_utils reference"
fi

# Check Makefile
if [ -f "Makefile" ]; then
    if grep -q "common/Makefile" "Makefile" 2>/dev/null; then
        log_success "Makefile delegates to common framework"
    else
        log_error "Makefile does not delegate to common framework"
        ((ERRORS++))
    fi
fi

# Check values-global.yaml
if [ -f "values-global.yaml" ]; then
    check_content "values-global.yaml" "multiSourceConfig:" "multiSourceConfig setting"
    check_content "values-global.yaml" "pattern:" "pattern name"
    check_content "values-global.yaml" "clusterGroup:" "clusterGroup definition"
fi

# Check for Helm charts
echo ""
echo "Checking Helm charts..."
echo "======================================"
CHART_COUNT=0
for chart in charts/hub/*/Chart.yaml; do
    if [ -f "${chart}" ]; then
        ((CHART_COUNT++))
        CHART_DIR=$(dirname "${chart}")
        CHART_NAME=$(basename "${CHART_DIR}")

        # Check for application template
        if [ -f "${CHART_DIR}/templates/application.yaml" ]; then
            log_success "${CHART_NAME} has application.yaml"

            # Check for multiSourceConfig
            if grep -q "sources:" "${CHART_DIR}/templates/application.yaml" 2>/dev/null; then
                log_success "${CHART_NAME} uses multiSourceConfig (sources)"
            else
                log_error "${CHART_NAME} missing multiSourceConfig - uses old 'source' format"
                ((ERRORS++))
            fi
        else
            log_error "${CHART_NAME} missing templates/application.yaml"
            ((ERRORS++))
        fi
    fi
done

if [ "${CHART_COUNT}" -eq 0 ]; then
    log_warn "No Helm charts found in charts/hub/"
    ((WARNINGS++))
else
    log_info "Found ${CHART_COUNT} Helm charts"
fi

# Check for platform overrides
echo ""
echo "Checking platform overrides..."
echo "======================================"
for platform in AWS Azure GCP; do
    if [ -f "overrides/values-${platform}.yaml" ]; then
        log_success "values-${platform}.yaml exists"
    else
        log_warn "values-${platform}.yaml missing"
        ((WARNINGS++))
    fi
done

# Check for validation/deployment scripts
echo ""
echo "Checking scripts..."
echo "======================================"
if [ -d "scripts" ]; then
    SCRIPT_COUNT=$(find scripts -name "*.sh" -type f 2>/dev/null | wc -l)
    if [ "${SCRIPT_COUNT}" -gt 0 ]; then
        log_info "Found ${SCRIPT_COUNT} scripts"

        # Run ShellCheck if available
        if command -v shellcheck >/dev/null 2>&1; then
            echo ""
            echo "Running ShellCheck on scripts..."
            echo "======================================"

            for script in scripts/*.sh; do
                if [ -f "${script}" ]; then
                    if shellcheck "${script}" >/dev/null 2>&1; then
                        log_success "$(basename "${script}") - passes ShellCheck"
                    else
                        log_error "$(basename "${script}") - ShellCheck errors"
                        ((ERRORS++))
                    fi
                fi
            done
        else
            log_warn "ShellCheck not installed - skipping shell script validation"
            ((WARNINGS++))
        fi
    else
        log_warn "No scripts found in scripts/"
        ((WARNINGS++))
    fi
fi

# Summary
echo ""
echo "======================================"
echo "Validation Summary"
echo "======================================"

if [ "${ERRORS}" -eq 0 ]; then
    if [ "${WARNINGS}" -eq 0 ]; then
        echo -e "${GREEN}✓ Pattern validation passed with no issues!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Pattern validation passed with ${WARNINGS} warnings${NC}"
        echo ""
        echo "Warnings are non-critical issues that should be addressed before production use."
        exit 0
    fi
else
    echo -e "${RED}✗ Pattern validation failed with ${ERRORS} errors and ${WARNINGS} warnings${NC}"
    echo ""
    echo "Please fix the errors before proceeding with pattern deployment."
    exit 1
fi