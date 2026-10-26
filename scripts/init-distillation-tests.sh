#!/bin/bash
# Initialize the isolated CPU test environment inside a compute allocation.
set -euo pipefail
: "${SLURM_JOB_ID:?Initialize manual test environments in a compute allocation}"
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
uv=${UV_BIN:-uv}
environment=${TEST_ENV:-$root/.venv-distillation}
"$uv" venv --python 3.12 --allow-existing "$environment"
# Fetch CPU torch from its explicit index; never resolve CUDA packages here.
"$uv" pip install --python "$environment/bin/python" \
    --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu'
"$uv" pip install --python "$environment/bin/python" \
    -r "$root/requirements-distillation-test.txt" ruff==0.14.7
"$uv" pip freeze --python "$environment/bin/python" > "$environment/requirements-resolved.txt"
