# Experiment tracking

Use one W&B run per attempt, keeping A/B/C and failed attempts distinct.
Native Slime logging is opt-in via `WANDB_PROJECT` and `WANDB_ENTITY`; set
`WANDB_MODE=online` only with configured credentials and connectivity.
The default when enabling tracking is offline. Never put credentials in command
arguments, manifests, or the repository; use the SDK's authentication environment.
Existing submitted snapshots are unchanged by local integration edits.

Track loss, gradient norms, sampled teacher–student gap, timing and policy-age
metrics. Retain per-node GPU CSVs for utilization, memory and power; identify
roles from actual placement before aggregating them. Sampled gaps are not exact
KL, utilization is not a roofline measurement, and training loss is not quality.
Evaluation outcomes and complete checkpoint evidence remain separate gates.

`python -m distillation.tracking_export RUN_DIR --output metrics.json` extracts
numeric logged metrics and GPU samples. Add `--upload --entity TEAM --project
PROJECT` only after selecting the destination and configuring authentication.
These imports are explicitly historical, not live tracking; absent metrics stay
absent. No prompts, responses, raw logs, GPU UUIDs or model payloads are uploaded
by this exporter. Avoid importing an attempt twice; native live tracking and
historical imports must remain clearly distinguished.

Current integration is awaiting cluster checks and W&B login/destination; no
online dashboard has been verified yet.
