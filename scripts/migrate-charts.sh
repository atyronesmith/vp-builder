#!/bin/bash
set -euo pipefail

# Generic Helm chart migration script for validated patterns
# Usage: ./migrate-charts.sh <source-repo-path> [chart1] [chart2] ...

if [ $# -lt 1 ]; then
    echo "Usage: $0 <source-repo-path> [chart-names...]"
    echo "Example: $0 /path/to/source-repo chart1 chart2"
    echo "If no chart names provided, will search for all Chart.yaml files"
    exit 1
fi

SOURCE_REPO="$1"
shift

# Validate source repo exists
if [ ! -d "${SOURCE_REPO}" ]; then
    echo "Error: Source repository not found: ${SOURCE_REPO}"
    exit 1
fi

# Create migrated-charts directory if it doesn't exist
mkdir -p migrated-charts

# Function to migrate a chart
migrate_chart() {
    local chart_path="$1"
    local chart_name
    chart_name=$(basename "$(dirname "${chart_path}")")

    echo "Migrating chart: ${chart_name}"

    # Create target directory
    mkdir -p "migrated-charts/${chart_name}"

    # Copy chart contents
    cp -r "$(dirname "${chart_path}")"/* "migrated-charts/${chart_name}/"

    echo "✓ Migrated ${chart_name} to migrated-charts/${chart_name}"
}

# If specific charts provided, migrate those
if [ $# -gt 0 ]; then
    for chart_name in "$@"; do
        # Find Chart.yaml for this chart
        chart_yaml=$(find "${SOURCE_REPO}" -name Chart.yaml -type f | grep "/${chart_name}/Chart.yaml" | head -1)

        if [ -n "${chart_yaml}" ]; then
            migrate_chart "${chart_yaml}"
        else
            echo "Warning: Chart '${chart_name}' not found in ${SOURCE_REPO}"
        fi
    done
else
    # No specific charts provided, find all charts
    echo "Searching for Helm charts in ${SOURCE_REPO}..."

    # Find all Chart.yaml files
    while IFS= read -r -d '' chart_yaml; do
        migrate_chart "${chart_yaml}"
    done < <(find "${SOURCE_REPO}" -name Chart.yaml -type f -print0)
fi

echo ""
echo "Chart migration complete!"
echo ""
echo "Migrated charts summary:"
ls -1 migrated-charts/ 2>/dev/null || echo "No charts migrated"
echo ""
echo "Next steps:"
echo "1. Review migrated charts in migrated-charts/"
echo "2. Create wrapper charts in charts/hub/ for each migrated chart"
echo "3. Update wrapper chart values to reference correct repositories"
echo "4. Configure ArgoCD applications with multiSourceConfig"