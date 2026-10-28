# Experiment tracking

Follow the [experiment logging requirement](../../EXPERIMENTS.md#log-ml-experiments-in-wb).
Use one W&B run per attempt, keeping A/B/C and failed attempts distinct.
Enable native Slime logging via `WANDB_PROJECT` and `WANDB_ENTITY`; set
`WANDB_MODE=online` only with configured credentials and connectivity.
The implementation defaults to offline when tracking is enabled; explicitly
select online mode for live logging, or arrange a visible relay/sync. Confirm
that the intended run receives metrics after startup. Never put credentials in command
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

Cluster check `14700226` completed in 31 seconds: 19 distillation tests, one
numeric-export test, and shell syntax passed. These CPU checks do not establish
online authentication or delivery; verify those for the selected destination
and each launch environment. A periodic numeric relay is distinct from native
live logging and should be labelled accordingly.
