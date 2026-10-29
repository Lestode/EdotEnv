# A · Synchronous distillation

Recorded smoke result, 27 October 2026: corrected smoke test `14673098` completed successfully. All three optimizer steps (0–2) logged finite losses and nonzero finite gradient norms; the final checkpoint was saved. All 24 consumed responses had zero reported policy age and no mixed versions.

This preserves an earlier smoke checkpoint. Later attempts and the current
experimental direction are tracked in the [overview](../README.md#current-experimental-status)
and [journal](../../LOG.md).

Collect a batch, train, then publish weights. Each response must use one policy
version with zero lag. This is the learning reference if execution and subsequent
quality evaluation succeed.

Use `MODE=synchronous`. The [common protocol](../README.md#separate-execution-checks-and-measurements)
defines the initial model, workload and evidence requirements. Each attempt gets
a new output directory and manifest identifying condition A.

The successful retry took 8m26s on eight GPUs (about 1.124 GPU-hours, including startup and checkpointing). The previous failed attempt used about 1.689 GPU-hours. This establishes bounded execution and observed A invariants, not learning quality or numerical equivalence; half of the 24 responses reached the 512-token cap. Evidence: `A-a2/train/manifest.json`, `train.log`, rollouts and checkpoint under the private project run directory. See the [journal](../../LOG.md).
