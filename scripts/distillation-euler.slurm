#!/bin/bash
# Euler selects the account/partition through its submission filter.
#SBATCH --job-name=edot-distillation
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=nvidia_a100_80gb_pcie:4
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=8G
#SBATCH --time=00:30:00

set -euo pipefail
: "${RUNTIME_ENV:?Prepared external Euler virtual environment}"
test -f "$(dirname "$RUNTIME_ENV")/preparation-completed"
export APPTAINER_BIND="$RUNTIME_ENV${APPTAINER_BIND:+,$APPTAINER_BIND}"
export APPTAINERENV_PREPEND_PATH="$RUNTIME_ENV/bin"
: "${PROJECT_ROOT:?Shared initialized checkout}"
# Euler provides Apptainer directly; do not load Komondor's module.
export APPTAINER_MODULE=
exec bash "$PROJECT_ROOT/scripts/distillation-run.sh"
