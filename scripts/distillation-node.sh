#!/bin/bash
set -euo pipefail
source "$PROJECT_ROOT/scripts/distillation-runtime-env.sh"
if [ "$SLURM_NODEID" = 0 ]; then
    printf '%s.%s\n' "$SLURM_JOB_ID" "$SLURM_STEP_ID" > "$RUN_ROOT/ray-step-id"
fi
ip=$(getent ahostsv4 "$(hostname)" | awk 'NR==1 {print $1}')
if [ "$SLURM_NODEID" = 0 ]; then ip="$RAY_HEAD_IP"; fi
export SLIME_HOST_IP="$ip"
export TMPDIR="/tmp/edot-${SLURM_JOB_ID}"
mkdir -p "$TMPDIR"
python -m distillation.runtime_probe > "$RUN_ROOT/runtime-${SLURM_NODEID}.json"
nvidia-smi topo -m > "$RUN_ROOT/topology-${SLURM_NODEID}.txt" 2>&1 || true
{
    if command -v ip >/dev/null; then
        ip -brief address
        ip route get "$RAY_HEAD_IP"
    else
        echo 'ip utility unavailable; recording kernel routes instead.'
        cat /proc/net/route
    fi
} > "$RUN_ROOT/network-${SLURM_NODEID}.txt" 2>&1 || true
sampler_pid=""
if [ "${GPU_SAMPLE_SECONDS:-0}" != 0 ]; then
    nvidia-smi --query-gpu=timestamp,uuid,index,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,clocks.sm,clocks.mem \
        --format=csv --loop="${GPU_SAMPLE_SECONDS}" > "$RUN_ROOT/gpu-${SLURM_NODEID}.csv" 2> "$RUN_ROOT/gpu-${SLURM_NODEID}.err" &
    sampler_pid=$!
fi
cleanup_sampler() {
    if [ -n "$sampler_pid" ]; then kill "$sampler_pid" 2>/dev/null || true; fi
}
trap cleanup_sampler EXIT
if [ "$SLURM_NODEID" = 0 ]; then
    ray start --head --node-ip-address="$RAY_HEAD_IP" --port="$RAY_PORT" \
        --num-gpus="$DISTILLATION_GPUS_PER_NODE" --num-cpus="${SLURM_CPUS_PER_TASK:-16}" --temp-dir="$TMPDIR/ray" --disable-usage-stats --block
else
    for attempt in $(seq 1 60); do
        if (echo > "/dev/tcp/$RAY_HEAD_IP/$RAY_PORT") 2>/dev/null; then break; fi
        sleep 2
    done
    ray start --address="$RAY_ADDRESS" --node-ip-address="$ip" \
        --num-gpus="$DISTILLATION_GPUS_PER_NODE" --num-cpus="${SLURM_CPUS_PER_TASK:-16}" --disable-usage-stats --block
fi
