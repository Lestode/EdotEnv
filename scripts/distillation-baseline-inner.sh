#!/bin/bash
set -euo pipefail
cd "$PROJECT_ROOT"
source scripts/distillation-runtime-env.sh
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/slime:${PYTHONPATH:-}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$RUN_ROOT/cache" TRITON_CACHE_DIR="$RUN_ROOT/triton-cache"
mkdir -p "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR"
setsid python -m sglang.launch_server --model-path "$BASELINE_MODEL" --host 127.0.0.1 \
    --port 30571 --tp-size 4 --dtype bfloat16 --attention-backend triton \
    --mem-fraction-static 0.65 --context-length 12288 --disable-cuda-graph \
    > "$RUN_ROOT/server.log" 2>&1 &
server_pid=$!
cleanup() {
    kill -TERM -- "-$server_pid" 2>/dev/null || true
    for attempt in $(seq 1 10); do
        if ! kill -0 "$server_pid" 2>/dev/null; then break; fi
        sleep 1
    done
    kill -KILL -- "-$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
export BASELINE_SERVER_PID="$server_pid"
python - <<'PY'
import os, time, urllib.request
deadline = time.monotonic() + 600
while time.monotonic() < deadline:
    os.kill(int(os.environ["BASELINE_SERVER_PID"]), 0)
    try:
        with urllib.request.urlopen("http://127.0.0.1:30571/health", timeout=5) as response:
            if response.status == 200:
                break
    except OSError:
        time.sleep(2)
else:
    raise TimeoutError("Baseline server startup exceeded 600 seconds")
PY
python -m distillation.evaluate --endpoint http://127.0.0.1:30571 \
    --model "$BASELINE_MODEL" --data "$BASELINE_DATA" --output "$RUN_ROOT/evaluation" \
    --max-tokens 8192 --request-timeout 600 --batch-size 8
