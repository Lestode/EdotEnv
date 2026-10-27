#!/bin/bash
# Check the staged runtime's two-node Ray startup before reserving GPUs.
#SBATCH --job-name=edot-ray-check
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=cpu
#SBATCH --time=00:05:00

set -euo pipefail
module load apptainer/1.4.4
umask 077
: "${PROJECT_ROOT:?Shared initialized checkout}"
: "${RUNTIME_IMAGE:?Prepared runtime}"
: "${RUN_ROOT:?New private output directory}"
mkdir -m 700 "$RUN_ROOT"
export RAY_AUTH_MODE=token
unset RAY_AUTH_TOKEN
export RAY_AUTH_TOKEN_PATH="$RUN_ROOT/ray-auth-token"
od -An -N32 -tx1 /dev/urandom | tr -d ' \n' > "$RAY_AUTH_TOKEN_PATH"
HEAD_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)
export RAY_HEAD_IP=$(getent ahostsv4 "$HEAD_NODE" | awk 'NR==1 {print $1}')
export RAY_ADDRESS="$RAY_HEAD_IP:6379"
export PROJECT_ROOT RUNTIME_IMAGE RUN_ROOT
cleanup() {
    timeout 20 srun --overlap --ntasks=2 --ntasks-per-node=1 bash -c '
        source_logs="/tmp/edot-ray-${SLURM_JOB_ID}/ray/session_latest/logs"
        if [ -d "$source_logs" ]; then
            cp -R "$source_logs" "$RUN_ROOT/logs-${SLURM_NODEID}"
        fi
    ' || true
    if [ -f "$RUN_ROOT/step-id" ]; then
        read -r step < "$RUN_ROOT/step-id"
        case "$step" in "$SLURM_JOB_ID".[0-9]*) scancel --signal=KILL "$step" || true ;; esac
    fi
    kill "$worker_pid" 2>/dev/null || true
    wait || true
}
trap cleanup EXIT
srun --overlap --ntasks=2 --ntasks-per-node=1 --kill-on-bad-exit=1 \
    apptainer exec --bind "$PROJECT_ROOT,$RUN_ROOT" "$RUNTIME_IMAGE" bash -c '
        set -euo pipefail
        source "$PROJECT_ROOT/scripts/distillation-runtime-env.sh"
        export TMPDIR="/tmp/edot-ray-${SLURM_JOB_ID}"
        mkdir -p "$TMPDIR"
        ip=$(getent ahostsv4 "$(hostname)" | awk "NR==1 {print \$1}")
        if [ "$SLURM_NODEID" = 0 ]; then
            printf "%s.%s\n" "$SLURM_JOB_ID" "$SLURM_STEP_ID" > "$RUN_ROOT/step-id"
            exec ray start --head --node-ip-address="$RAY_HEAD_IP" --port=6379 \
                --num-gpus=0 --num-cpus=4 --temp-dir="$TMPDIR/ray" --disable-usage-stats --block
        else
            for attempt in $(seq 1 60); do
                if (echo > "/dev/tcp/$RAY_HEAD_IP/6379") 2>/dev/null; then break; fi
                sleep 2
            done
            exec ray start --address="$RAY_ADDRESS" --node-ip-address="$ip" \
                --num-gpus=0 --num-cpus=4 --disable-usage-stats --block
        fi
    ' > "$RUN_ROOT/ray.log" 2>&1 &
worker_pid=$!
srun --overlap --nodes=1 --ntasks=1 --nodelist="$HEAD_NODE" \
    apptainer exec --bind "$PROJECT_ROOT,$RUN_ROOT" "$RUNTIME_IMAGE" bash -c '
        set -euo pipefail
        source "$PROJECT_ROOT/scripts/distillation-runtime-env.sh"
        timeout 180 python "$PROJECT_ROOT/distillation/ray_probe.py"
    ' > "$RUN_ROOT/driver.log" 2>&1
