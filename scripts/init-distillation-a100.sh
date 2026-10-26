#!/bin/bash
# Run inside an owned, writable copy of the Slime runtime, on a compute node.
set -euo pipefail
: "${SLURM_JOB_ID:?Build the runtime in a compute allocation}"
: "${RUNTIME_BUILD_RECORD:?New directory for build provenance}"
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
uv=${UV_BIN:-uv}
python=${RUNTIME_PYTHON:-/opt/sglang/bin/python}
umask 077
mkdir "$RUNTIME_BUILD_RECORD"
"$python" - <<'PY'
import sys
import torch

assert sys.version_info[:2] == (3, 12), sys.version
assert torch.__version__ == "2.13.0+cu130", torch.__version__
assert torch.version.cuda == "13.0", torch.version.cuda
PY
export CUDA_HOME=/usr/local/cuda
export FLASH_ATTENTION_FORCE_BUILD=TRUE
export FLASH_ATTN_CUDA_ARCHS=80
export TORCH_CUDA_ARCH_LIST=8.0
# The base image exports MAX_JOBS=16; do not inherit its build resource budget.
export MAX_JOBS=${DISTILLATION_BUILD_JOBS:-6}
export NVCC_THREADS=2
"$uv" --version > "$RUNTIME_BUILD_RECORD/uv.txt"
"$uv" pip freeze --python "$python" > "$RUNTIME_BUILD_RECORD/before.txt"
cp "$root/requirements-distillation-a100.txt" "$RUNTIME_BUILD_RECORD/requirements.txt"
cp "${BASH_SOURCE[0]}" "$RUNTIME_BUILD_RECORD/setup.sh"
env | LC_ALL=C sort | sed -n '/^\(CUDA_HOME\|FLASH_ATTENTION_FORCE_BUILD\|FLASH_ATTN_CUDA_ARCHS\|TORCH_CUDA_ARCH_LIST\|MAX_JOBS\|NVCC_THREADS\)=/p' \
    > "$RUNTIME_BUILD_RECORD/build-environment.txt"
"$uv" pip install --python "$python" --no-build-isolation --no-deps \
    --no-cache --no-binary flash-attn --reinstall-package flash-attn \
    -r "$root/requirements-distillation-a100.txt" \
    2>&1 | tee "$RUNTIME_BUILD_RECORD/install.log"
"$uv" pip freeze --python "$python" > "$RUNTIME_BUILD_RECORD/after.txt"
"$python" -c 'from flash_attn import flash_attn_func, flash_attn_varlen_func'
# Successful compilation/import still requires the separate GPU runtime probe.
touch "$RUNTIME_BUILD_RECORD/build-completed"
