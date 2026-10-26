#!/bin/bash
# Submit with --account=<authorized account> and exported paths described in docs.
#SBATCH --job-name=distillation-check
#SBATCH --partition=gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=00:30:00
#SBATCH --exclusive

set -euo pipefail
umask 077
: "${PROJECT_ROOT:?Shared checkout containing the initialized Slime submodule}"
: "${MODEL_ROOT:?Shared directory containing student and teacher snapshots}"
: "${TRAIN_DATA:?Training JSONL}"
: "${RUN_ROOT:?New shared attempt directory}"
: "${RUNTIME_IMAGE:?Validated A100 Slime Apptainer image}"
: "${SLURM_JOB_ID:?Submit through Slurm}"
MODE=${MODE:-synchronous}
module load apptainer/1.4.4
mkdir -m 700 "$RUN_ROOT"
export PROJECT_ROOT MODEL_ROOT TRAIN_DATA RUN_ROOT RUNTIME_IMAGE MODE
export RAY_PORT=16379
export RAY_ADDRESS
HEAD_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)
RAY_HEAD_IP=$(getent ahostsv4 "$HEAD_NODE" | awk 'NR==1 {print $1}')
export RAY_HEAD_IP
RAY_ADDRESS="$RAY_HEAD_IP:$RAY_PORT"
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/slime:${PYTHONPATH:-}"
export CUDA_DEVICE_MAX_CONNECTIONS=1

# Each Slurm step owns its processes; never stop another job's Ray instance.
pids=()
cleanup() {
    for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

srun --overlap --ntasks=2 --ntasks-per-node=1 --kill-on-bad-exit=1 \
    apptainer exec --nv --bind "$PROJECT_ROOT,$MODEL_ROOT,$RUN_ROOT,$(dirname "$TRAIN_DATA")" \
    "$RUNTIME_IMAGE" bash "$PROJECT_ROOT/scripts/distillation-node.sh" \
    > "$RUN_ROOT/ray.log" 2>&1 &
pids+=("$!")

# A bounded wait also verifies that both nodes expose their four allocated GPUs.
srun --overlap --nodes=1 --ntasks=1 --nodelist="$HEAD_NODE" \
    apptainer exec --nv --bind "$PROJECT_ROOT,$MODEL_ROOT,$RUN_ROOT,$(dirname "$TRAIN_DATA")" \
    "$RUNTIME_IMAGE" bash -c '
        cd "$PROJECT_ROOT"
        source scripts/distillation-runtime-env.sh
        python -m distillation.cluster_ready
        python -m distillation.launch --student "$MODEL_ROOT/student" --teacher "$MODEL_ROOT/teacher" \
            --data "$TRAIN_DATA" --output "$RUN_ROOT/train" --mode "$MODE" --execute
    ' > "$RUN_ROOT/driver.log" 2>&1
