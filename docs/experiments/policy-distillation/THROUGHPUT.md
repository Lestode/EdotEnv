# Larger-model throughput and learning pilot

Komondor submissions may use either `gpu` or `ai`, with four allocated GPUs
per node even on eight-GPU AI hosts. Slurm chooses one partition per job;
this does not pool nodes across partitions. Retain actual placement in reports.
The site Apptainer 1.4.4 fails on AI hosts; the launcher selects 1.4.1 there,
validated for container startup on three AI nodes in diagnostic `14689539`.
GPU execution on AI remains unvalidated.

B/C pending jobs now request 64 GiB host RAM per node at the user’s direction;
A retains 128 GiB. This reduction is unvalidated through training/checkpointing
and must be disclosed in timing comparisons. GPU counts and workload are unchanged.

Status: corrected runtime-aware A/B/C jobs `14689575`/`14689576`/`14689577`
use immutable `source-ai-a1` (mount fix `4d791d5`, runtime selection `a9866fd`).
Earlier failures are retained in the journal. CPU model-access and all 20 tests
passed in `14689413`; larger-model training remains unvalidated. Teacher baseline:
29/32 versus original student 27/32.

The user authorized upgrading to a 7B student and frozen 32B teacher, measuring
pipeline waiting, GPU productivity by role, and quality versus tokens, time and
GPU-hours. Use pinned DeepSeek-R1-Distill-Qwen checkpoints; their tokenizer
metadata matches exactly. Reuse the completed 7B frozen baseline where its model,
data and decoding settings match. Run the 32B baseline concurrently with training
following the
[concurrency rule](../../EXPERIMENTS.md#run-independent-work-concurrently).
Baseline completion is required for quality interpretation, not training startup.

Start with 12 A100-40GB GPUs: four training (TP4), four student generation
(two TP2 engines), four teacher scoring (TP4). Generation admits up to 16
concurrent requests across engines; teacher requests are bounded to eight.
Global batch 64, microbatch one, full activation recomputation, 2048 response
tokens. Run separate A, B and C pilots from the same original student, each
targeting 20 updates with a 30-minute cap and HF checkpoints every ten updates.
Keep workload, seed, allocation and concurrency settings matched; record actual
placement and node sharing. On 27 October the user removed the prior 24-GPU
concurrency cap for this batch: submit all three independently and let Slurm
schedule them, allowing 36 training GPUs plus the four-GPU baseline concurrently.
Per-job limits remain unchanged. This round is a short smoke test; no further
optimization or longer learning runs before reviewing its results.
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

Allocation preference: request the required GPU total without requiring adjacent
nodes, consecutive GPU IDs, or a fixed count per node where the implementation
supports it. The launcher now accepts uniform allocations of one, two, or four GPUs per
node, preserving the model-role GPU totals and tensor-parallel sizes. For this
12-GPU profile, submit with matching Slurm overrides: `--nodes=12
--gpus-per-node=1`, `--nodes=6 --gpus-per-node=2`, or `--nodes=3
--gpus-per-node=4`. Ray and the collective probe use the requested per-node count;
the manifest records the layout. CPU and memory requests remain explicit.
Uneven counts per node still need a broader placement change. A new layout
requires its collective and runtime checks; CPU configuration tests alone do
not validate communication performance or GPU execution.

In results, distinguish the requested layout from the observed allocation.
Report available node/GPU identities, role placement and sharing evidence; mark
unmeasured topology or contention as unknown. If allocations differ, acknowledge
that communication and sharing may contribute to timing differences. Do not
attribute the full difference to A/B/C scheduling without supporting evidence.
