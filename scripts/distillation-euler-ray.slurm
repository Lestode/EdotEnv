#!/bin/bash
# Check the staged runtime's two-node Ray startup before reserving GPUs.
#SBATCH --job-name=edot-ray-check
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --time=00:05:00

set -euo pipefail
: "${RUNTIME_ENV:?Prepared external Euler virtual environment}"
test -f "$(dirname "$RUNTIME_ENV")/preparation-completed"
export APPTAINER_BIND="$RUNTIME_ENV${APPTAINER_BIND:+,$APPTAINER_BIND}"
export APPTAINERENV_PREPEND_PATH="$RUNTIME_ENV/bin"
exec bash "$PROJECT_ROOT/scripts/distillation-ray-check.sh"
