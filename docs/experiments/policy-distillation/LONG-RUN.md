# 500-update MATH comparison

The user authorized 500 optimizer updates per condition after the ten-update
pilot. A/B/C start independently from the same pinned original 1.5B student,
with the frozen 7B teacher and existing MATH train/development/evaluation split.
This is a longer exploratory comparison; acceptable quality loss is not yet set.

Use eight GPUs across two nodes per condition, 64 GiB host RAM per node,
batch eight, microbatch one and the existing optimizer/sampling settings.
Each run has a 12-hour allocation cap; all three may run concurrently.
Raise response capacity to 8,192 tokens and total context to 12,288, leaving
4,096 prompt tokens. Apply the context consistently to serving and training.
This geometry needs runtime validation; do not claim the old memory evidence
certifies it. Stop affected jobs on a shared defect and retain failed attempts.

Save model-only checkpoints and HF exports every 50 updates and at completion,
so the 100-, 250- and 500-update milestones are available for evaluation.
Optimizer state remains absent: checkpoints cannot resume the exact Adam
trajectory. Record disk usage; both checkpoint formats consume storage.
Keep W&B capture on for every run and verify delivery. Online numeric relay
runs must remain active through queueing and execution; retain offline logs
if the relay loses connectivity. Do not restart user-cancelled notifications.

The completed pilot logged 14-18 seconds per update in trainer timer windows,
plus roughly ten minutes of unpartitioned startup/save/orchestration per job.
At the previous 2,048-token budget, a linear 500-update estimate is 2-3 hours
per condition. At 8,192 tokens, provisionally expect 8-12 hours; this is a
fourfold token-budget extrapolation, not a measured throughput result. Attention,
discarded work, response lengths and shared-host contention can change it.
Queue delay is additional and a 12-hour cap can still be reached before 500.

Use held-out development data for checkpoint evaluation and truncation checks;
retain the 468 reserved MATH-500 questions untouched. Compare accepted tokens,
updates, discarded work and quality, not just allocated time. Refer to the
[completed short-run report](reports/math-pilot-20261028/REPORT.md) for baseline
scores, failure history and the limits of this setup.
