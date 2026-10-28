#!/bin/bash
# Submit with --account=<authorized account> and exported paths described in docs.
#SBATCH --job-name=distillation-check
#SBATCH --partition=gpu,ai
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=00:30:00

set -euo pipefail
: "${PROJECT_ROOT:?Shared initialized checkout}"
export APPTAINER_MODULE=apptainer/1.4.4
exec bash "$PROJECT_ROOT/scripts/distillation-run.sh"
