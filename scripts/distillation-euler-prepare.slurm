#!/bin/bash
# CPU-only staging. Training jobs depend on successful completion.
#SBATCH --job-name=edot-prepare
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH --time=02:00:00
#SBATCH --tmp=150G

set -euo pipefail
umask 077
: "${PROJECT_ROOT:?Shared initialized checkout}"
: "${RUNTIME_ROOT:?New shared runtime directory}"
: "${MODEL_ROOT:?New shared model directory}"
export APPTAINER_MODULE=
export UV_BIN=${UV_BIN:-$(command -v uv)}
export DISTILLATION_BUILD_JOBS=6
cd "$PROJECT_ROOT"
for script in scripts/distillation*.sh scripts/init-distillation*.sh scripts/distillation*.slurm; do
    bash -n "$script"
done
bash scripts/init-distillation-euler.sh
export RUNTIME_ENV="$RUNTIME_ROOT/venv"
export APPTAINER_BIND="$RUNTIME_ENV${APPTAINER_BIND:+,$APPTAINER_BIND}"
export APPTAINERENV_PREPEND_PATH="$RUNTIME_ENV/bin"
module load eth_proxy
mkdir -m 700 "$MODEL_ROOT"
export HF_HOME="$MODEL_ROOT/cache"
apptainer exec --bind "$PROJECT_ROOT,$MODEL_ROOT" "$RUNTIME_ROOT/base.sif" \
    python - <<'PY'
import json
import os
from pathlib import Path

from huggingface_hub import snapshot_download

root = Path(os.environ["PROJECT_ROOT"])
models = Path(os.environ["MODEL_ROOT"])
lock = json.loads((root / "configs/distillation/models.json").read_text())
for role, spec in lock.items():
    snapshot_download(
        repo_id=spec["repo"], revision=spec["revision"],
        local_dir=models / role,
        allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"],
    )
PY
apptainer exec --bind "$PROJECT_ROOT,$MODEL_ROOT" "$RUNTIME_ROOT/base.sif" \
    python -m distillation.preflight --student "$MODEL_ROOT/student" \
    --teacher "$MODEL_ROOT/teacher" > "$MODEL_ROOT/preflight.json"
touch "$RUNTIME_ROOT/preparation-completed"
