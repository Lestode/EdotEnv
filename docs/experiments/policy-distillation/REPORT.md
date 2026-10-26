# Policy distillation validation update

26 October 2026 · Komondor · Engineering validation checkpoint

**Both frozen-model baselines completed. End-to-end training remains blocked at
distributed startup.** No optimizer updates have run, neither sync nor async
training has passed, and no full run has started. At this checkpoint submissions
were paused and no jobs for this experiment remained running or queued.

The user subsequently authorized separate A/B/C execution checks. Their current
records are [A](A/REPORT.md), [B](B/REPORT.md), and [C](C/REPORT.md); the measured
results below remain unchanged. B's response-boundary enforcement now passes
[CPU regressions](B/REPORT.md), with cluster authentication pending before
diagnosing Ray startup on allocated CPUs. No new GPU attempts have been submitted.

## Question and setup

Does the implementation work, and do its shortcuts preserve student quality
within an acceptable loss? The immediate objective is to pass short synchronous
and asynchronous execution checks before a learning study.

The frozen teacher is DeepSeek-R1-Distill-Qwen-7B; the student is
DeepSeek-R1-Distill-Qwen-1.5B. Slime provides generation, teacher scoring and
training. Eight A100 GPUs across two Komondor nodes is the provisional training
setup: four trainer GPUs, two student-serving GPUs and two teacher-serving GPUs.
Detailed profiling is deferred; existing stage timings and startup snapshots remain.

## Frozen model baseline results

Both models used the same fixed 32-question MATH-500 development subset, greedy
decoding, an 8192-token response limit, batches of eight, and the Slime math
grader. These evaluations preceded all attempted training. The other 468
questions remain reserved for later evaluation.

| Measurement | Student | Teacher |
| --- | ---: | ---: |
| Correct answers | 22 / 32 | 27 / 32 |
| Accuracy | 68.75% | 84.375% |
| Responses reaching the token limit | 10 / 32 | 5 / 32 |
| Request or grading errors | 0 | 0 |
| Evaluation elapsed time | 811.85 s | 832.97 s |
| Allocation elapsed time including startup and cleanup | 14m59s | 16m02s |

The observed teacher advantage is five answers, or 15.625 percentage points.
This supports continuing a development pilot, but 32 questions and substantial
truncation do not establish a reliable effect size. These starting-checkpoint
baselines do not establish successful distillation or acceptable shortcut loss.
The final study protocol and acceptable quality loss remain open.

## Engineering results and current blocker

Fourteen CPU adapter tests passed. Native A100 checks passed for attention
against a reference, backward computation, RMSNorm and an Adam update. An
eight-GPU, two-node BF16 collective passed in the candidate training runtime.
Both sync and async configurations passed argument validation; that checks
configuration acceptance, not execution.

Four subsequent synchronous smoke attempts stopped before model loading or
optimizer updates:

| Job | Duration | Outcome |
| --- | --- | --- |
| 14651375 | 2m13s | Ray inspected inaccessible Slurm ancestors. Disabled unnecessary environment detection and fixed readiness failure handling. |
| 14651432 | 2m20s | Optional network capture required an absent utility. Made the snapshot best effort. |
| 14651465 | 1m55s | Head port overlapped Ray's worker range. Corrected the port and checked CLI startup on CPU. |
| 14651539 | 1m48s | Authenticated head started, then its client service timed out waiting for node registration. Unresolved. |

CPU checks passed for Ray remote tasks, missing network tools and explicit
authentication. Reliable two-node startup remains unvalidated. The last attempt
exited automatically; the earlier three were stopped promptly.

## Resource use and next decision

The two completed baselines used approximately **1.034 GPU-hours**. The four
subsequent smoke attempts used **1.102 GPU-hours**, for **2.136 GPU-hours** combined.
This is allocated GPU count multiplied by allocation duration, including startup
and cleanup. It excludes earlier setup, failed baseline attempts and CPU-only
checks; it is not a complete project cost or a monetary bill.

The proposed next step is one bounded investigation of Ray startup, preserving
its node-local failure logs and reproducing it on CPU resources where possible.
Resume the three-update sync test only after that startup check passes; attempt
async after sync succeeds. No sustained training is proposed at this checkpoint.

## Evidence

The [run journal](../LOG.md), [model lock](../../../configs/distillation/models.json)
and [pilot protocol](../../../configs/distillation/baseline-pilot.json) preserve
the evidence and configuration. Latest executed revision: `d2bd5dc`.
[PR 15](https://github.com/Lestode/EdotEnv/pull/15) remains open; implementation
review is incomplete because the reviewer cannot inspect the pinned Slime
interfaces. Raw responses, logs and credentials remain private.
