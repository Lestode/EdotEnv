# Larger-model throughput and learning pilot

Status: preparing; no larger-model training result yet.

The user authorized upgrading to a 7B student and frozen 32B teacher, measuring
pipeline waiting, GPU productivity by role, and quality versus tokens, time and
GPU-hours. Use pinned DeepSeek-R1-Distill-Qwen checkpoints; their tokenizer
metadata matches exactly. Reuse the completed 7B frozen baseline where its model,
data and decoding settings match; establish the 32B baseline before training.

Start with 12 A100-40GB GPUs: four training (TP4), four student generation
(two TP2 engines), four teacher scoring (TP4). Generation admits up to 16
concurrent requests across engines; teacher requests are bounded to eight.
Global batch 64, microbatch one, full activation recomputation, 2048 response
tokens. First run B for 20 updates with a 30-minute cap, saving HF checkpoints
every ten updates for separate evaluation. This is a capacity pilot; synthetic
smoke prompts cannot support a learning claim. Longer learning comparisons
require representative training data disjoint from evaluation.

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
