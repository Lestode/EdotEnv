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
nvidia-smi topo -m > "$RUN_ROOT/topology-${SLURM_NODEID}.txt"
ip -brief address > "$RUN_ROOT/network-${SLURM_NODEID}.txt"
ip route get "$RAY_HEAD_IP" >> "$RUN_ROOT/network-${SLURM_NODEID}.txt"
if [ "$SLURM_NODEID" = 0 ]; then
    exec ray start --head --node-ip-address="$RAY_HEAD_IP" --port="$RAY_PORT" \
        --num-gpus=4 --num-cpus=16 --temp-dir="$TMPDIR/ray" --disable-usage-stats --block
else
    for attempt in $(seq 1 60); do
        if (echo > "/dev/tcp/$RAY_HEAD_IP/$RAY_PORT") 2>/dev/null; then break; fi
        sleep 2
    done
    exec ray start --address="$RAY_ADDRESS" --node-ip-address="$ip" \
        --num-gpus=4 --num-cpus=16 --disable-usage-stats --block
fi
