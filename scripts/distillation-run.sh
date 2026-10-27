#!/bin/bash
# Shared execution body; submit a cluster-specific Slurm entry point.
set -euo pipefail
umask 077
: "${PROJECT_ROOT:?Shared checkout containing the initialized Slime submodule}"
: "${MODEL_ROOT:?Shared directory containing student and teacher snapshots}"
: "${TRAIN_DATA:?Training JSONL}"
: "${RUN_ROOT:?New shared attempt directory}"
: "${RUNTIME_IMAGE:?Validated A100 Slime Apptainer image}"
: "${SLURM_JOB_ID:?Submit through Slurm}"
MODE=${MODE:-synchronous}
DISTILLATION_NODES=${SLURM_JOB_NUM_NODES:-2}
export DISTILLATION_NODES
export DISTILLATION_PROFILE=${DISTILLATION_PROFILE:-smoke}
export ROLLOUTS=${ROLLOUTS:-3}
export RESPONSE_TOKENS=${RESPONSE_TOKENS:-512}
# Slurm's per-node request may be numeric or a typed GPU resource (Euler).
# A uniform allocation is required by pinned Slime's serving placement.
: "${SLURM_GPUS_PER_NODE:?Submit with --gpus-per-node=1,2,or4}"
export DISTILLATION_GPUS_PER_NODE="${SLURM_GPUS_PER_NODE##*:}"
case "$DISTILLATION_GPUS_PER_NODE" in
    1|2|4) ;;
    *) echo "Unsupported uniform GPU request: $SLURM_GPUS_PER_NODE" >&2; exit 2 ;;
esac
expected_total=8
if [ "$DISTILLATION_PROFILE" = 7b32b ]; then expected_total=12; fi
if [ "$((DISTILLATION_NODES * DISTILLATION_GPUS_PER_NODE))" -ne "$expected_total" ]; then
    echo "Allocation must total $expected_total GPUs for $DISTILLATION_PROFILE" >&2
    exit 2
fi
if [ -n "${APPTAINER_MODULE:-}" ]; then module load "$APPTAINER_MODULE"; fi
command -v apptainer >/dev/null
mkdir -m 700 "$RUN_ROOT"
export PROJECT_ROOT MODEL_ROOT TRAIN_DATA RUN_ROOT RUNTIME_IMAGE MODE
# Explicitly share one private token between head, workers and driver. The
# runtime otherwise enables authentication differently for CLI and API clients.
export RAY_AUTH_MODE=token
unset RAY_AUTH_TOKEN
export RAY_AUTH_TOKEN_PATH="$RUN_ROOT/ray-auth-token"
od -An -N32 -tx1 /dev/urandom | tr -d ' \n' > "$RAY_AUTH_TOKEN_PATH"
chmod 600 "$RAY_AUTH_TOKEN_PATH"
# Keep the head outside Ray's default worker range (10002--19999).
export RAY_PORT=6379
export RAY_ADDRESS
HEAD_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)
RAY_HEAD_IP=$(getent ahostsv4 "$HEAD_NODE" | awk 'NR==1 {print $1}')
export RAY_HEAD_IP
RAY_ADDRESS="$RAY_HEAD_IP:$RAY_PORT"
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/slime:${PYTHONPATH:-}"
export CUDA_DEVICE_MAX_CONNECTIONS=1

# Exercise the actual candidate runtime's inter-node collective before training.
srun --ntasks="$DISTILLATION_NODES" --ntasks-per-node=1 --kill-on-bad-exit=1 \
    apptainer exec --nv --bind "$PROJECT_ROOT,$RUN_ROOT" "$RUNTIME_IMAGE" \
    bash -c '
        set -euo pipefail
        cd "$PROJECT_ROOT"
        source scripts/distillation-runtime-env.sh
        python -m torch.distributed.run --nnodes="$DISTILLATION_NODES" --nproc-per-node="$DISTILLATION_GPUS_PER_NODE" \
            --node-rank="$SLURM_NODEID" --master-addr="$RAY_HEAD_IP" --master-port=16400 \
            -m distillation.collective_probe
    ' > "$RUN_ROOT/collective.log" 2>&1

# Each Slurm step owns its processes; never stop another job's Ray instance.
pids=()
cleanup() {
    timeout 20 srun --overlap --ntasks="$DISTILLATION_NODES" --ntasks-per-node=1 bash -c '
        source_logs="/tmp/edot-${SLURM_JOB_ID}/ray/session_latest/logs"
        if [ -d "$source_logs" ]; then
            cp -R "$source_logs" "$RUN_ROOT/ray-logs-${SLURM_NODEID}"
        fi
    ' || true
    if [ -f "$RUN_ROOT/ray-step-id" ]; then
        read -r ray_step < "$RUN_ROOT/ray-step-id"
        case "$ray_step" in
            "$SLURM_JOB_ID".[0-9]*) scancel --signal=KILL "$ray_step" 2>/dev/null || true ;;
        esac
    fi
    for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

srun --overlap --ntasks="$DISTILLATION_NODES" --ntasks-per-node=1 --kill-on-bad-exit=1 \
    apptainer exec --nv --bind "$PROJECT_ROOT,$MODEL_ROOT,$RUN_ROOT,$(dirname "$TRAIN_DATA")" \
    "$RUNTIME_IMAGE" bash "$PROJECT_ROOT/scripts/distillation-node.sh" \
    > "$RUN_ROOT/ray.log" 2>&1 &
pids+=("$!")

# Verify every requested node exposes exactly its allocated GPU count.
srun --overlap --nodes=1 --ntasks=1 --nodelist="$HEAD_NODE" \
    apptainer exec --nv --bind "$PROJECT_ROOT,$MODEL_ROOT,$RUN_ROOT,$(dirname "$TRAIN_DATA")" \
    "$RUNTIME_IMAGE" bash -c '
        set -euo pipefail
        cd "$PROJECT_ROOT"
        source scripts/distillation-runtime-env.sh
        python -m distillation.cluster_ready
        python -m distillation.launch --student "$MODEL_ROOT/student" --teacher "$MODEL_ROOT/teacher" \
            --data "$TRAIN_DATA" --output "$RUN_ROOT/train" --mode "$MODE" \
            --profile "$DISTILLATION_PROFILE" --rollouts "$ROLLOUTS" \
            --gpus-per-node "$DISTILLATION_GPUS_PER_NODE" \
            --response-tokens "$RESPONSE_TOKENS" --execute
    ' > "$RUN_ROOT/driver.log" 2>&1
