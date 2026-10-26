#!/bin/bash
# Executed inside the immutable Slime image, with writable shared storage bound.
set -euo pipefail
: "${SLURM_JOB_ID:?Use a compute allocation}"
: "${RUNTIME_ENV:?New external virtual environment}"
: "${UV_BIN:?Host uv binary bound into the container}"
export UV_CACHE_DIR="$RUNTIME_ROOT/cache/uv"
export TMPDIR="$RUNTIME_ROOT/tmp"
"$UV_BIN" venv --python /opt/sglang/bin/python --system-site-packages "$RUNTIME_ENV"
export PATH="$RUNTIME_ENV/bin:$PATH"
python - <<'CHECK'
import sys
import torch
assert sys.version_info[:2] == (3, 12), sys.version
assert torch.__version__ == "2.13.0+cu130", torch.__version__
assert torch.version.cuda == "13.0", torch.version.cuda
CHECK
export CUDA_HOME=/usr/local/cuda
export FLASH_ATTENTION_FORCE_BUILD=TRUE FLASH_ATTN_CUDA_ARCHS=80 TORCH_CUDA_ARCH_LIST=8.0
export MAX_JOBS=${DISTILLATION_BUILD_JOBS:-6} NVCC_THREADS=2
"$UV_BIN" --version > "$RUNTIME_ROOT/uv.txt"
"$UV_BIN" pip install --python "$RUNTIME_ENV/bin/python" --no-build-isolation --no-deps \
    --no-cache --no-binary flash-attn --reinstall-package flash-attn \
    -r "$PROJECT_ROOT/requirements-distillation-a100.txt"
# Base-image console scripts have a base-interpreter shebang. Ray must use this venv.
printf '#!/bin/bash\nexec "%s/bin/python" -m ray.scripts.scripts "$@"\n' "$RUNTIME_ENV" > "$RUNTIME_ENV/bin/ray"
chmod 700 "$RUNTIME_ENV/bin/ray"
source "$PROJECT_ROOT/scripts/distillation-runtime-env.sh"
python - <<'CHECK'
import os
from pathlib import Path
import flash_attn
assert Path(flash_attn.__file__).is_relative_to(Path(os.environ["RUNTIME_ENV"])), flash_attn.__file__
from flash_attn import flash_attn_func, flash_attn_varlen_func
import transformer_engine.pytorch
import ray
print("External venv imports passed; GPU kernels remain unvalidated.")
CHECK
"$UV_BIN" pip freeze --python "$RUNTIME_ENV/bin/python" > "$RUNTIME_ROOT/environment.txt"
touch "$RUNTIME_ROOT/build-completed"
