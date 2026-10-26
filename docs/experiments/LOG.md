# Experiment journal

Follow [experiment guidance](../EXPERIMENTS.md#maintain-experiment-continuity).
Keep one short entry per run, newest first, using a stable run ID that also
identifies its artifacts. Aim for 50–100 words per entry; link to detailed
configuration and evidence. Record each retry as a separate attempt linked to
the earlier entry so failures remain visible.

## Run entries

### 2026-10-26 · distillation-final-cpu-20261026 · completed

- Question: Does the final configuration retain passing checks with four GPUs per node and native-kernel probes?
- Setup: Final adapter checks as an overlapping CPU step within allocation `14650675`; the queued duplicate allocation `14650722` was cancelled before execution.
- Result: All twelve tests, Ruff, formatting, and shell syntax passed. GPU kernels are not exercised by these CPU tests.
- Evidence: Private `edotenv/distillation-check-20261026-a1/final-cpu-inline.log`.

### 2026-10-26 · distillation-weights-20261026 · running

- Question: Can the pinned teacher/student snapshots be staged and verified on shared project storage?
- Setup: The model lock and allocation-only downloader, `huggingface-hub==0.34.4` through uv; no inference.
- Resources: Slurm `14650718`, four requested CPUs, 16 GiB RAM, 15-minute limit; no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/model-staging.log` and `models/verification.json` when complete. Result pending.

### 2026-10-26 · distillation-review-fix2-20261026 · completed

- Question: Does an evaluator grading exception retain the generated answer and truncation evidence?
- Setup: Added the review-requested regression; first test attempt `14650706` failed because its mock intercepted another mock's module lookup. Corrected test setup and retried as `14650713`.
- Result: Twelve CPU tests, Ruff, formatting, and shell syntax passed; two seconds per attempt, three allocated CPUs and 8 GiB RAM, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/review-fix.log`, `review-fix2.log`, and `review-formatted.tar.gz`. No model execution.

### 2026-10-26 · distillation-collective-node-20261026 · completed

- Question: Does the intended node-level launcher permit eight-GPU communication after the per-GPU Slurm-task failure below?
- Setup: One Slurm task per node, each launching four torchrun workers; site `AI_env/v2`, PyTorch 2.6.0/CUDA 12.4/NCCL 2.21.5, BF16 all-reduce of known values.
- Result: All eight A100 workers passed across two nodes; Slurm `14650707`, nine seconds, exit `0:0`, approximately 0.020 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/collective-node.log`; reproducible probe in `distillation/collective_probe.py`. This validates the site collective, not Slime's separate runtime or learning.

### 2026-10-26 · distillation-collective-20261026 · failed

- Question: Can eight allocated A100s communicate correctly across two Komondor nodes?
- Setup: Site `AI_env/v2`, one Slurm task per GPU, BF16 NCCL all-reduce of known values; no models or Slime runtime.
- Resources: Slurm `14650698`, two nodes and eight GPUs, three-minute limit (at most 0.4 GPU-hours).
- Result: Failed during NCCL initialization (`nvmlDeviceGetHandleByPciBusId: Not Found`), before communication; 13 seconds, exit `1:0`, approximately 0.029 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/collective.log`. Retried with one Slurm task per node; this failure does not establish a network fault.

### 2026-10-26 · distillation-recheck-20261026 · completed

- Question: Does the updated adapter configuration parse through Slime's real serving parser while retaining a frozen teacher?
- Setup: Updated source archive in the same private validation directory; added serving-parser test, result normalization, and streaming weight hashes.
- Result: Eleven CPU tests passed; Ruff and shell syntax passed. No models or GPUs were used.
- Resources: Slurm `14650690`, 19 seconds, three allocated CPUs, 8 GiB RAM on `test`; exit `0:0`.
- Evidence: `edotenv/distillation-check-20261026-a1/update.tar.gz` and `recheck.log`. Distributed training and learning quality remain unvalidated.

### 2026-10-26 · distillation-runtime-20261026 · running

- Question: Can the documented Slime container provide the pinned training stack on Komondor?
- Setup: Apptainer pull of `slimerl/slime` digest `sha256:6379b872c6cc2535fb8c0e073a79bb1f41e365ca4859dd308e99ba14eb87936d`, then CPU import checks.
- Resources: Slurm `14650675`, planned eight CPUs, 64 GiB RAM, 30 minutes on `test`; no GPUs or model weights.
- Evidence: Private `edotenv/distillation-check-20261026-a1/runtime-preparation.log`; result pending. A100 kernels and distributed training remain separate checks.

### 2026-10-26 · distillation-check-20261026-a1 · completed

- Question: Do the classical-distillation adapters preserve token alignment, reject invalid policy ages, and agree with exact reverse-KL gradients in a tiny enumerated example?
- Setup: Project source snapshot on Komondor; pinned Slime `18868a79`; CPU tests and model-metadata preflight only.
- Result: All 10 tests passed; Ruff and shell syntax passed. Downloaded checkpoint metadata passed exact tokenizer-identity checks. The site AI environment lacks Ray, SGLang, Megatron, and Transformer Engine.
- Resources: Slurm `14650670`, `test`, 31 seconds, three allocated CPUs, 8 GiB RAM, zero GPUs; exit `0:0`.
- Evidence: Private project storage under `edotenv/distillation-check-20261026-a1`, including source snapshot, `validation.log`, and `preflight.json`.
- Limits: Numerical checks do not execute distributed Slime training or establish student quality.

Earlier execution records and
artifact locations are documented in the
[verifier context experiment](../../experiments/verifier-context/README.md#reading-the-results).
This journal is not yet a complete historical inventory.

## Entry template

Create the entry at launch with status `running`; fill in results when known.
Use `completed`, `failed`, or `cancelled` for the final status, and state any
partial results or uncertainty. Keep planned budgets separate from actual usage.

```markdown
### <UTC date/time> · <run ID> · <status>

- Question: What uncertainty does this run address?
- Setup: Code revision, model/checkpoint, saved config reference, and relevant changes.
- Result: Measured metrics and comparison; interpretation and limitations.
- Resources: Actual duration, GPU-hours or API cost, or unknown.
- Evidence: Durable locations of the saved configuration, logs, and outputs.
- Next: What the result suggests doing next, or pending.
```

Keep private data, prompts, logs, and credentials out of this public document.
Use non-sensitive artifact references to approved private storage where needed.
