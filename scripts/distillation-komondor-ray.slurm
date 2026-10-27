#!/bin/bash
#SBATCH --job-name=edot-ray-check
#SBATCH --partition=cpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:05:00

set -euo pipefail
: "${PROJECT_ROOT:?Shared initialized checkout}"
module load apptainer/1.4.4
for script in "$PROJECT_ROOT"/scripts/distillation*.sh "$PROJECT_ROOT"/scripts/distillation*.slurm; do
    bash -n "$script"
done
exec bash "$PROJECT_ROOT/scripts/distillation-ray-check.sh"
