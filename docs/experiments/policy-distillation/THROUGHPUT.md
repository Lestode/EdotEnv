# Larger-model throughput and learning pilot

Status: preparation `14674318` and final-source CPU contract `14674338` queued;
teacher baseline `14674339` waits for both. No larger-model training submitted
yet. Source `f7b5aaa`, private run root `edotenv/throughput-7b32b-20261027`.

The user authorized upgrading to a 7B student and frozen 32B teacher, measuring
pipeline waiting, GPU productivity by role, and quality versus tokens, time and
GPU-hours. Use pinned DeepSeek-R1-Distill-Qwen checkpoints; their tokenizer
metadata matches exactly. Reuse the completed 7B frozen baseline where its model,
data and decoding settings match; establish the 32B baseline before training.

Start with 12 A100-40GB GPUs: four training (TP4), four student generation
(two TP2 engines), four teacher scoring (TP4). Generation admits up to 16
concurrent requests across engines; teacher requests are bounded to eight.
Global batch 64, microbatch one, full activation recomputation, 2048 response
tokens. Run separate A, B and C pilots from the same original student, each
targeting 20 updates with a 30-minute cap and HF checkpoints every ten updates.
Keep workload, seed, allocation and concurrency settings matched; record actual
placement and node sharing. At most two 12-GPU pilots may run concurrently,
including evaluation allocations within the 24-GPU total budget.
This is a capacity pilot; synthetic smoke prompts cannot support a general
learning claim. Evaluate saved checkpoints to detect changes on the fixed
development set, with uncertainty and truncation reported. Longer learning
comparisons require representative training data disjoint from evaluation.

Use existing stage timers, teacher request/queue durations, ready-queue counts
at batch boundaries, and GPU UUID/utilization/memory/power samples every two
seconds. Queue snapshots are not a continuous occupancy trace; concurrent
request durations are not additive wall time. GPU utilization is not peak
compute efficiency. Keep timestamped logs and placement evidence.

After the pilot, inspect memory, waiting and sample counts before tuning
concurrency or launching A/B/C learning runs, each capped at one hour and
evaluated at intermediate checkpoints. Do not infer quality from training loss.
Roofline profiling is a separate short diagnostic requiring FLOP and byte
counters, not a plot reconstructed from GPU-utilization percentages.

The public MATH training split is a candidate for subsequent learning runs:
`DigitalLearningGmbH/MATH-lighteval`, revision
`0530c78699ea5e8eb5530600900e1f328b48acad`, file
`data/train-00000-of-00001.parquet`. Prepare it separately, exclude exact
normalized problem overlap with all MATH-500 evaluation rows, and retain hashes.
Do not use the MATH test split for training. This does not rule out all semantic
overlap or model pretraining contamination.

## Consolidated report

The user requests a full report after all three pilots and checkpoint evaluations
finish. Deliver a shareable Markdown report and PDF with the exact model/data/code
revisions and configurations, per-condition outcomes, quality at baseline and
saved checkpoints, training tokens and elapsed/allocated GPU-hours, stage waiting,
queue snapshots, GPU telemetry by role, and measured throughput.
Include readable comparison tables and plots, retained failures, the limits of
single-seed/small-development-set evidence, and concrete optimization priorities.
Separate observed bottlenecks from hypotheses. Explicitly state whether C
produced mixed-version responses and whether its distinctive shortcut was tested.
Do not rank speed by total job time without separating startup and checkpointing.
Do not present GPU-utilization telemetry as a measured roofline.
