# Experiment journal

Follow [experiment guidance](../EXPERIMENTS.md#maintain-experiment-continuity).
Keep one short entry per run, newest first, using a stable run ID that also
identifies its artifacts. Aim for 50–100 words per entry; link to detailed
configuration and evidence. Record each retry as a separate attempt linked to
the earlier entry so failures remain visible.

## Run entries

### 2026-10-29 · MATH A/B/C and matched evaluations · completed

A/B/C `14702480`/`14702481`/`14702486` completed ten finite updates and saved
model/HF checkpoints in 13m42s/11m47s/11m44s. Accepted lag stayed at zero/one/one;
C had 38 mixed-version responses, B none. B/C discarded seven/nineteen stale
groups. Training used 4.962 GPU-hours; 67-68/80 responses per run were truncated.
Matched TP4 evaluations `14728534`/`14728535`/`14728536` scored 20/32, 20/32,
24/32; original-student evaluation `14728542` scored 24/32. All completed without
request/grading failures. Evaluations used 5.294 GPU-hours. Numeric results are
synced to W&B. See the [report](policy-distillation/reports/math-pilot-20261028/REPORT.md)
for paired outcomes, plots, exact revisions, limitations and evidence paths.

### 2026-10-28 · MATH A/B/C pilots · submitted

The user cancelled remaining smoke work and selected MATH training prompts.
A/B/C `14702480`/`14702481`/`14702486` are independently queued: eight GPUs
across two nodes, 64 GiB/node, ten updates, batch eight, 2,048 response tokens,
30-minute caps, model-only saves and HF exports. Immutable `source-a1` in
`edotenv/math-pilot-20261028` has `856cbdd` overlays. Async sampling now drops
and replaces over-age groups through Slime's filter hook, retaining lag one;
report discard counts and selection effects. W&B offline capture plus an online
numeric relay is configured and the three relay runs were created successfully.
Validation `14702479` passed 19 checks but an old command-equality expectation
failed; corrected-test check `14702490` also exercises the actual filter/parser.

### 2026-10-28 · smoke outcomes and MATH data · retained

Smoke A `14700907` completed ten updates in 12m05s and saved distributed model
weights and a seven-shard HF export. B `14700908` and C `14700909` each stopped
after two updates when queued responses exceeded the one-publication lag bound;
B had 15 ready responses for an eight-response batch. A's smoke evaluation
`14701466` was cancelled at the user's request; preserve partial results without
claiming a completed evaluation. MATH prep `14702438` completed in one minute:
3,000 train, 256 development and 4,239 reserve rows. Four references could not be
extracted and one duplicate/overlap row was excluded; manifests retain hashes.

### 2026-10-28 · MATH data preparation · submitted

CPU-only job `14702438` prepares the selected MATH training source with code
`e649014` (four cores, 8 GiB, ten-minute cap). Planned outputs are 3,000
prompt-only training rows, separate references and 256 held-out development
rows, with subject/difficulty strata, normalized overlap exclusion against all
500 MATH-500 questions, and source/output hashes. Output is under the small-model
base's `math-data-a1`; results remain pending. This is data preparation, not a
learning run. The existing 32-question MATH-500 development selection and 468
reserved final-evaluation questions remain distinct from training.

### 2026-10-28 · small-model A/B/C · concurrent release

The user removed the save-first gate and explicitly authorized stopping affected
runs if a shared bug appears, then applying the correction across A/B/C.
Dependencies were cleared for `14700907`/`14700908`/`14700909`; the redundant
pending save-only job `14700906` was cancelled. All three retain the same
small-model snapshot and model-only/HF export settings. Diagnostic `14700905`
passed 19 CPU tests but failed on its missing prepared `hooks.json`;
independent retry `14700921` uses the production launcher to prepare all files.
Runtime validation, saving and evaluation remain unproven for this configuration.

### 2026-10-28 · return to small-model validation · submitted

The user chose the initial 1.5B student / 7B teacher pair to reduce scheduling
and memory pressure. Reuse eight GPUs across two nodes, with 64 GiB RAM/node,
model-only saves, no replay dumps, HF exports and lightweight telemetry.
The large-model optimizer-offload settings do not apply to this profile.
Retain the successful Ray/container/mount fixes and existing model baselines.
Replace the pending larger-model save and A/B/C jobs, keeping their records.
Full-argument/CPU gate `14700905` precedes save test `14700906`; A/B/C
`14700907`/`14700908`/`14700909` each wait for the save test. Pilots request
ten updates and 512 response tokens, with 30-minute caps. Pending larger jobs
`14700459`/`14700460`/`14700462`/`14700463` were cancelled before replacement.
Artifacts: `/project/nk_meshapplied/edotenv/small-validation-20261028`, immutable
`source-a1` with `ac72126` launch/test overlays. Checkpoint evaluation and the
consolidated report remain required.

### 2026-10-28 · model-only without replay dumps · authorized

The user approved disabling replay/debug batch dumps for model-only pilots.
The launcher now omits `--save-debug-rollout-data` only in that mode, avoiding
Slime's implicit trainer-recovery requirement for optimizer state. Full saves
retain their existing replay behavior. Metrics, GPU CSVs and model exports
remain enabled; exact replay and optimizer-state recovery are unavailable.
Validate this configuration through the full installed parser before the
one-update save test and the dependent A/B/C pilots.

### 2026-10-28 · tracking-check-14700226 · passed; pilots blocked

The W&B integration snapshot corresponding to `01f47fb` passed 19 distillation
checks, one numeric-export check and shell syntax in 31 seconds (one AI GPU
allocated for runtime access, no training). Cloud authentication/upload remain
unvalidated. Model-only preflight `14700178` separately failed because replay
batch dumps activate trainer recovery, which requires optimizer state. Awaiting
user decision on disabling those dumps; save test `14699990` and new A/B/C
`14700179`/`14700180`/`14700181` remain dependency-blocked. Old C `14697823`
also hit host OOM at full checkpoint saving. Logs remain in the throughput base.

### 2026-10-28 · model-only-save validation · preparing

A `14697224` and B `14697822` exceeded 128 GiB host RAM while saving
their first full checkpoint; neither has a confirmed evaluation export. The
user selected a one-update model-only save test at 128 GiB/node instead of the
queued 256 GiB full-save probe `14698989`. `CHECKPOINT_MODE=model-only` passes
Slime’s `--no-save-optim`; full saving remains the default. This preserves model
weights for evaluation but not optimizer state for exact training continuation.
Validate full runtime arguments, then the actual distributed save and HF export.


### 2026-10-28 · throughput-7b32b-A/B/C-offload-a2 · running / queued

- Current jobs: A `14697224` running; B `14697822` and C `14697823` queued,
  concurrently authorized by the user. Old held C `14692971` was cancelled.
- Source: immutable `source-offload-a2`, launch/tests overlays `01dc547`;
  separate `A/B/C-capacity-offload-a2` outputs and saved submission commands.
- Budget: Each 12 GPUs, three nodes, 30 minutes, 20 updates, 128 GiB/node.
  B/C now match A because A's reported maximum task RSS reached approximately
  123 GiB; offloading makes the previous 64 GiB request unsuitable.
- Partial result at 11:53 UTC: A completed three finite updates; publication
  after the first two succeeded, with roughly 11 GiB GPU memory free afterward.
  No update-10 HF export exists yet. Full completion and quality remain pending.

### 2026-10-28 · offload-args-14696291 · completed

- Full Slime/Megatron argument validation passed in 3m32s after adding required
  `--use-precision-aware-optimizer`. Main parameters, gradients and both Adam
  moments explicitly retain FP32. Half of optimizer state remains on CPU.
- Evidence: `throughput-7b32b-20261027/offload-args-14696291.log`;
  `offload-full-args.py` validates the failed run's recorded command with the
  correction. One AI GPU allocated; no model training (0.0589 GPU-hours).
- Prior attempt A `14695736` failed in 6m24s before training because this flag
  was missing. The tiny optimizer test bypassed full argument validation and
  did not cover that requirement. Preserve `A-capacity-offload-a1` evidence.
- Next: A-only full-model retry; optimizer offloading and HF export remain
  unvalidated end to end. B/C remain stopped/held.

### 2026-10-28 · offload-check-14695604 · completed

- Candidate: The 7B/32B profile uses Megatron optimizer CPU offload fraction 0.5,
  preserving model layout, batch size, optimizer hyperparameters and precision.
- Result: 19 CPU regressions passed; the installed hybrid optimizer completed
  three tiny GPU updates with finite changed parameters and saved/reloaded its
  optimizer state. This does not establish full distributed checkpoint export.
- Resources: One AI GPU, four CPUs, 16 GiB; 1m37s, 0.0269 GPU-hours.
- Evidence: `throughput-7b32b-20261027/offload-check-14695604.log` and
  `offload-probe.py`. Retry A alone with its existing 128 GiB/node allocation;
  verify repeated publication, checkpoints and host-memory pressure before B/C.

### 2026-10-28 · throughput-7b32b-A-ray-a2 · failed after first update

- A `14692928` ran 16m10s on 12 GPUs (3.23 allocated GPU-hours). Ray attachment,
  serving and the first training update succeeded: 64 responses, mean length
  575.98 tokens, loss -0.11430, gradient norm 0.94442, policy age zero.
- Failure: CUDA OOM in Slime's TP parameter all-gather during weight publication
  after step 0. A 1.02 GiB allocation failed with about 1005 MiB free on a
  39.52 GiB GPU. No update-10 export exists for evaluation.
- B `14692929` was cancelled during startup to avoid the shared publication
  failure; C `14692971` is held. This is GPU memory, not host RAM or Ray startup.
- Evidence: `A-capacity-ray-a2/train/train.log`, rollout `0.pt`, and GPU telemetry.
  Investigate publication peak memory and supported memory controls before retry.

### 2026-10-28 · throughput-7b32b-A/B/C-ray-a2 · submitted

- Jobs: A `14692928`, B `14692929`, C `14692971`, separate fresh outputs
  `A/B/C-capacity-ray-a2`; launcher fix `a77325a`, staged `source-ray-a2`.
- Budget: Each 12 GPUs on three nodes, 30 minutes, 20 updates, batch 64,
  2048 response tokens, HF exports at 10/20; concurrent execution authorized.
  A retains 128 GiB/node, B/C 64 GiB/node. Sharing is permitted.
- Gate: Two-node Ray driver/task check and 20 CPU tests passed in `14692340`.
- Evidence: Saved submission commands and `submissions.txt` under the existing
  `throughput-7b32b-20261027` artifact root. Old held C `14689577` is replaced.
- Pending: Actual updates, condition-specific invariants, checkpoint evaluation
  and the consolidated report; no longer run is started by this submission.

### 2026-10-28 · ray-multinode-14692340 · completed

- Result: Driver attachment in the head container and CPU tasks on both `cn01`
  and `cn02` passed. Launcher shell syntax and 20 CPU regressions passed.
- Resources: Two AI nodes, one GPU allocated per node, four CPUs and 16 GiB
  per node; 2m11s (0.0728 GPU-hours). Ray used CPU tasks only.
- Evidence: `throughput-7b32b-20261027/ray-multinode-14692340`, staged
  `source-ray-a1` with the prepared launcher changes.
- Limit: Validates the placement pattern; full model training remains untested
  with the new launcher. Proceed to fresh bounded A/B/C pilots.

### 2026-10-28 · ray-visibility-14691685 · completed

- Question: Does driver placement explain AI Ray attachment failure?
- Result: Same-container driver discovered the local Ray node and connected;
  a separate Slurm/container step failed local node discovery. This supports
  keeping the driver with the head; exact site isolation mechanism is unconfirmed.
- Resources: One GPU allocated, four CPUs, 16 GiB, 1m39s (0.0275 GPU-hours);
  Ray advertised zero GPUs and no model ran.
- Evidence: `throughput-7b32b-20261027/ray-visibility-14691685` logs/results.
- Next: Validate the prepared launcher correction across nodes before training.

### 2026-10-28 · ray-visibility-14691557 · cancelled

- Diagnostic defect: selected head port 16379 overlaps Ray's default worker
  range. Ray never started; subsequent connection failures are uninterpretable.
- Stopped the lingering allocation; retained logs. Retry `14691685` uses 26379
  and fails immediately when head startup exits. No training ran.

### 2026-10-28 · throughput-7b32b-A/B-ai-a1 · failed

- A `14689575` failed after 11m43s; B `14689576` after 11m25s, both before
  training at Ray driver readiness. A passed model access and 12-rank collective;
  its Ray head registered all three nodes. C `14689577` remains held.
- A used 128 GiB/node; B used 64 GiB. Neither establishes training memory needs.
- Evidence: retained `A-capacity-ai-a1` / `B-capacity-ai-a1` logs under the
  `throughput-7b32b-20261027` artifact root. No checkpoints to evaluate.

### 2026-10-28 · throughput-7b32b-B/C-ai-a1 · reduced host memory

- User authorized reducing pending B `14689576` and C `14689577` to 64 GiB host RAM per node. Updated in place and verified: `MinMemoryNode=64G`, effective `MinCPUsNode=17` (previously 33). GPU counts, workload and time caps unchanged; A remains at 128 GiB/node.
- A's startup cgroup peaks were about 7.1–7.7 GiB/node; training and checkpoint peaks were not yet measured. The reduced limit is not yet validated, and the difference must be recorded in comparisons.
- AI snapshot after update: free GPUs 1/0/6/2 on cn01–04. Only cn03 meets four GPUs plus the reduced CPU/RAM request; neither three-node job fits yet.


### 2026-10-28 · throughput-7b32b-A/B/C-ai-a1 · runtime-aware retries submitted

- Diagnostic `14689539` completed in 15 seconds: Apptainer 1.4.4 failed on all three tested AI nodes, while 1.4.1 started the existing container successfully on each. This checks container startup, not GPU execution.
- Fix `a9866fd` selects 1.4.1 on allocated AI nodes and retains 1.4.4 on GPU nodes. New immutable `source-ai-a1` builds on the mount-corrected snapshot.
- Jobs A `14689575`, B `14689576`, C `14689577` are eligible for `gpu,ai`, each three nodes/four GPUs per node/30 minutes, unchanged workload. Pending B/C a3 attempts were cancelled before held replacements were released; no duplicates. Per-node model access, GPU runtime, collective and Ray readiness remain mandatory before training.


### 2026-10-28 · throughput-7b32b-A-3x4-a3 · AI runtime failed

- A `14689447` immediately scheduled on AI nodes `cn01`, `cn02`, `cn04`, then failed after one second, exit 127. The site Apptainer 1.4.4 executable could not load `libsubid.so.3`; no container or training started.
- Pending B `14689448` and C `14689449` returned in place to `gpu` to avoid repeating this defect. AI eligibility alone does not establish AI runtime support.
- Diagnostic `14689539` tests both site runtimes (1.4.4 and 1.4.1) on three AI nodes, one GPU each, two-minute cap. An initial CPU-only submission was rejected by partition policy. Inspect actual command outcomes before another pilot.


### 2026-10-28 · throughput-7b32b-A/B/C-3x4-a3 · AI eligibility enabled

- User requested AI-node support. Existing jobs `14689447`/`14689448`/`14689449` were updated in place to `Partition=gpu,ai`; Slurm confirmed eligibility. No duplicate submissions or resource increases.
- Four allocated GPUs per node remain advertised to Ray; pinned Slime resolves physical serving IDs within the inherited visible-device list. AI runtime execution remains unvalidated; per-node access, native-kernel, collective and Ray-resource checks precede training.
- The Komondor launcher now defaults to both partitions. Each job stays within a single partition; record placement and topology rather than assuming identical performance.

### 2026-10-28 · throughput-7b32b-A/B/C-3x4-a3 · submitted after mount validation

- CPU gate `14689413` passed real-container access to both pinned models, one new shard-access regression and all 19 existing distillation tests. No GPU allocation for this gate.
- Fresh retries: A `14689447`, B `14689448`, C `14689449`, each 12 GPUs/three nodes/30 minutes on `gpu`, same workload as a2. Every node now checks model access before Ray and collectives.
- Source: private `source-mount-a1`, copied from `source-layout-a2` with the three implementation/test files from `4d791d5`. Separate a3 outputs; prior failures preserved. GPU training and evaluations remain pending.


### 2026-10-28 · throughput-7b32b-A/B/C-3x4-a2 · failed before training

- A `14676512` failed after 5m58s; B `14676513` and C `14676514` after 1m08s each. All passed the 12-rank BF16 collective, but no training started and no checkpoints were produced.
- Shared cause: the reused 7B student symlink points outside the mounted model root. Metadata exists on the host but was invisible inside the training containers. Driver logs retain the missing config exception; Ray startup waits also appear.
- Correction: bind resolved student/teacher directories in workers and driver, and check pinned metadata plus shard readability on every node before startup. Preserve these attempts; validate the corrected mounts before fresh retries.

### 2026-10-27 · throughput-7b32b-A/B/C-3x4-a2 · submitted

- Decision: User requested returning to four GPUs per node. Pending 12×1 jobs `14676046`/`14676047`/`14676048` were cancelled before replacements were released; no GPU time was used. Exactly one active submission per condition.
- Jobs: A `14676512`, B `14676513`, C `14676514`, independent with no baseline dependencies. Source `b3aed46`, unchanged role totals and smoke workload.
- Resources: Each 12 GPUs across three nodes, requested 16 CPUs/128 GiB per node, 30-minute cap, sharing allowed. Twenty updates, batch 64, 2048 response tokens, checkpoints at 10 and 20.
- Evidence: Private `throughput-7b32b-20261027/submissions.txt` and separate `A-capacity-3x4-a2`, `B-capacity-3x4-a2`, `C-capacity-3x4-a2` outputs. Earlier attempts and allocation decisions remain recorded.

### 2026-10-27 · throughput-7b32b-A/B/C-12x1-a1 · submitted

- Decision: User explicitly selected one 12×1 job per A/B/C despite the provisional later scheduler estimates. This is three experiments, not repeated trials. Original queued jobs `14675577`/`14675578`/`14675579` were cancelled before their replacements were released; zero GPU use on originals.
- Jobs: A `14676046`, B `14676047`, C `14676048`, independent with no baseline dependency. Source `b3aed46` in private `source-layout-a2`; Slime pin unchanged. CPU layout contract passed all19 tests; cross-node tensor-parallel GPU execution remains to be checked by these bounded runs.
- Resources: Each12 GPUs on12 nodes, requested4 CPUs/64GiB per node, 30-minute cap, node sharing allowed. Same20 updates, model roles, batch64 and2048 response-token cap as before.
- Evidence: `throughput-7b32b-20261027/submissions.txt` and separate `A-capacity-12x1-a1`, `B-capacity-12x1-a1`, `C-capacity-12x1-a1` outputs. Record topology and network effects; these timings cannot be assumed equivalent to3×4.

### 2026-10-27 · throughput-7b32b-teacher-baseline · completed across attempts

- Result: Continuation `14675573` completed in 11m25s, all eight answers correct, one truncated. Combined with retained first-attempt results: 29/32 correct, four truncated, zero request failures. Original indices cover 0–31 exactly once; data hashes, model path, decoding, tokenizer, batch size and grader match.
- Comparison: The immutable 7B baseline scored 27/32 with five truncated responses on the same questions/settings. A two-question difference on this small development set is not a definitive capability advantage.
- Resources: Both teacher attempts together about 2.769 allocated GPU-hours. A/B/C remain independently queued.
- Evidence: Private `edotenv/throughput-7b32b-20261027/baseline-teacher-combined/summary.json`, original responses and `baseline-continuation.json`; failed first attempt preserved.


### 2026-10-27 · fragmented-allocation-contract · completed

- Change: Source `b3aed46` adds uniform 1/2/4-GPU-per-node layouts across Ray readiness, collective probing and model placement, retaining role totals. Uneven allocations remain unsupported. Pinned uv/Ruff lint and formatting passed.
- Validation: CPU contract `14675861` passed all 19 tests and shell syntax checks, exit0 in43s, four CPUs/16GiB, zero GPUs. Source snapshot at private `throughput-7b32b-20261027/source-layout-a1` contains the pre-format equivalent changes and regression tests; no GPU validation claimed.
- Scheduling: Slurm test-only queries predicted 29 October for 12×1 and 6×2 with four CPUs/64GiB per node, versus 28 October for the existing 3×4 jobs. These estimates are provisional, not a controlled performance comparison. No alternate GPU jobs were submitted; preserve A/B/C queue positions.
- Evidence: `layout-contract-14675861.log`, `submissions.txt`; the main monitor tracks this gate alongside the existing A/B/C jobs.

### 2026-10-27 · throughput-7b32b-A/B/C-capacity-a1 · submitted concurrently

- Decision: User removed baseline-before-training gating and the prior 24-GPU concurrency cap for this short smoke batch. Slurm schedules the independent jobs; baseline continuation runs separately.
- Jobs: A `14675577`, B `14675578`, C `14675579`, submitted without dependencies after verifying preparation and CPU contract success and checking for existing submissions.
- Setup: Source `f7b5aaa`, profile `7b32b`, 20 updates, batch64, 2048 response tokens, checkpoints at10/20; same original student per condition.
- Resources: Each12 GPUs across three nodes, 30-minute cap, no exclusivity; up to36 training GPUs plus4 baseline GPUs concurrently.
- Evidence: Private `edotenv/throughput-7b32b-20261027/submissions.txt` and separate `A-capacity-a1`, `B-capacity-a1`, `C-capacity-a1` outputs. Synthetic prompts limit quality interpretation. No longer run authorized in this batch.

### 2026-10-27 · throughput-7b32b-teacher-baseline · partial; continuation submitted

- Result: Teacher baseline `14674339` hit its 30-minute limit (accounting: 30m07s). It retained 24/32 answers: 21 correct, three truncated, zero request failures. This is not a completed 32-question baseline. The interrupted summary still says running; scheduler accounting is authoritative.
- Diagnosis: Startup plus sequential batches waiting for long responses exhausted the cap; logs show tail decode around 18 tokens/s with one request left. No model-loading or scoring exception was observed.
- Continuation: `14675573` evaluates only original indices 24–31, same model/decoding/grader. Original data hash and retained indices were verified; separate subset hash and index mapping are in `baseline-continuation.json`. Merge only after all eight finish, checking model/settings and disjoint coverage.
- Resources: First attempt about 2.008 allocated GPU-hours; continuation four GPUs, 30-minute cap. A/B/C training remains gated.
- Evidence: Private `edotenv/throughput-7b32b-20261027/baseline-teacher-a1`, `baseline-teacher-a2`, scheduler logs and submissions.


### 2026-10-27 · throughput-7b32b-preparation · staging

- Question: Can the upgraded pair run with four training, four generation and four teacher GPUs, and produce useful capacity and checkpoint-quality measurements?
- Setup: Pinned 7B/32B tokenizer metadata matches. Reuse existing runtime and 7B weights; preparation `14674318` stages the 32B snapshot after CPU tests. Final-source contract check `14674338` includes the named HF checkpoint-export template. Source `f7b5aaa` is staged in `source-a2`.
- Result: Final-source contract job `14674338` passed all 18 tests in 47 seconds (exit `0:0`). Preparation `14674318` also passed 18 tests and is downloading the 32B snapshot. On the user's request to improve scheduling, their eligible partitions were widened in place to `cpu,cpu-short,test`; job IDs, CPU/memory limits and downstream dependencies are unchanged. No GPUs were added. Four-GPU teacher baseline `14674339` depends on both passing; no larger-model training submitted yet. Existing frozen 7B baseline is retained.
- Resources: Preparation eight CPUs/32 GiB/45 minutes; contract four CPUs/16 GiB/five minutes; baseline four GPUs/30 minutes.
- Evidence: Private `edotenv/throughput-7b32b-20261027/submissions.txt` and per-job logs; [pilot protocol](policy-distillation/THROUGHPUT.md).


### 2026-10-27 · komondor-C-a3 · completed

- Result: Job `14673436` completed three finite updates and saved its checkpoint; 16 of 24 consumed responses were one publication stale, none mixed versions. Execution passed; the mid-response shortcut was not exercised.
- Resources: Eight GPUs, sharing permitted, 6m55s (about 0.922 GPU-hours).
- Limits: All A/B/C runs used only three batches of eight responses and a 512-token cap. No post-training evaluation. Warm steps 1–2 report about 1.2s training and 6.1–6.3s waiting across conditions; overlapping timers must not be summed. Startup/checkpointing preclude a total-runtime speed ranking. Generation, scoring and coordination contributions still need separation.
- Evidence: [C report](policy-distillation/C/REPORT.md), private `edotenv/abc-komondor-20261027/C-a3/train/`.

### 2026-10-27 · komondor-B-a2 · completed

- Result: Job `14673099` completed three updates with finite losses and nonzero finite gradients, saved its checkpoint, and logged producer draining. Of 24 consumed responses, 16 were one publication stale; none mixed versions. Observed B invariants passed, not learning quality.
- Resources: Eight GPUs, 9m15s, about 1.233 GPU-hours; exclusive allocation. C-a3 `14673436` has started with sharing permitted.
- Limitations: Post-warmup `freeze_gc` connection errors were retained; serving and training subsequently succeeded. Startup and checkpointing dominate this short run, so elapsed time is not a throughput comparison.
- Evidence: [B report](policy-distillation/B/REPORT.md), private `edotenv/abc-komondor-20261027/B-a2/train/`.

### 2026-10-27 · komondor-C-a3 · submitted

- Question: Can C obtain an allocation without unnecessary whole-node exclusivity?
- Setup: User requested shared-node scheduling. Slurm denied updating pending C-a2 in place; it was cancelled before allocation, consuming no GPU time. Replacement C-a3 `14673436` uses the same `04f7283` training source and workload, with only the submission's exclusive directive removed.
- Result: Submitted; Slurm confirms `OverSubscribe=OK`. B-a2 remains running. A's completed result used exclusive nodes; this difference must be retained in timing comparisons.
- Resources: Eight GPUs across two nodes, 30-minute cap; no extra concurrent test.
- Evidence: Private run directory `edotenv/abc-komondor-20261027/C-a3`, saved `C-a3-submission.slurm`, and `submissions.txt`.

### 2026-10-27 · komondor-A-a2 / komondor-B-a2 / komondor-C-a2 · A completed; B running; C queued

- Question: Do the three execution policies complete training after correcting the shared reward contract?
- Setup: Source `04f7283`, existing runtime/models, fresh separate outputs; the two-node CPU Ray gate and all 17 targeted CPU regressions passed.
- Result: A `14673098` completed in 8m26s (about 1.124 GPU-hours): three finite optimizer-step metrics, checkpoint saved, 24 responses with zero reported lag and no mixed versions. B `14673099` is running; C `14673100` was subsequently cancelled while pending and replaced by non-exclusive C-a3. No learning-quality claim. See [A report](policy-distillation/A/REPORT.md).
- Resources: Each job has eight GPUs across two nodes and a 30-minute cap; up to 24 GPUs concurrently.
- Evidence: Private project `edotenv/abc-komondor-20261027/`, outputs `A-a2`, `B-a2`, `C-a2`, and `submissions.txt`. Previous failures are retained.

### 2026-10-27 · komondor-reward-contract · completed

- Question: Does the adapter expose the scalar expected by Slime logging while preserving teacher token scores and zero task reward?
- Setup: Source `04f7283`, actual pinned Slime sample accessor and zero-variance metric tested before postprocessing; teacher scores remain in the structured payload. The launcher selects `task_reward=0` using Slime's reward-key setting.
- Result: CPU regression job `14673025` passed all 17 targeted tests; elapsed 40 seconds, exit `0:0`. This validates the reward contract, not GPU training.
- Resources: Four CPUs, 16 GiB RAM, five-minute cap; no GPUs.
- Evidence: Private `edotenv/abc-komondor-20261027/reward-check-14673025.log`; corrected source in `source-a2`.

### 2026-10-27 · komondor-B-a1 / komondor-C-a1 · cancelled

- Question: Do bounded complete-response overlap (B) and abort/flush/resume overlap (C) execute their three-update smoke workloads?
- Setup: Same source `bf6125d`, runtime, models and batch settings as A. The user explicitly authorized concurrent A/B/C execution, superseding the sequential launch plan. Results remain separate.
- Result: Cancelled after A exposed a shared scalar-reward logging defect. B `14672807` had reached serving startup (4m46s, about 0.636 GPU-hours); C `14672808` was still pending (zero allocation). Neither reached a validated update.
- Resources: Eight GPUs and a 30-minute cap per job; with A, up to 24 GPUs concurrently and 12 GPU-hours total if all reach their caps.
- Evidence: Private project `edotenv/abc-komondor-20261027/B-a1`, `C-a1` and `submissions.txt`.

### 2026-10-27 · komondor-A-a1 · failed

- Question: Does synchronous distillation complete its three-update smoke workload after the two-node CPU Ray gate passed?
- Setup: Source `bf6125d`, pinned Slime and existing validated Komondor runtime/models; fresh output under `edotenv/abc-komondor-20261027/A-a1`. Ray startup logs are retained before cleanup.
- Result: Job `14672502` passed collectives and Ray readiness, initialized model services, and reached rollout processing. Slime logging then tried to round the teacher-score dictionary as a scalar reward; no optimizer update completed. Failed after 12m40s, about 1.689 GPU-hours. B/C were stopped to avoid repeating this shared defect.
- Resources: Eight A100 GPUs across two nodes, 30-minute cap (at most four GPU-hours).
- Evidence: Private project `edotenv/abc-komondor-20261027/`, including `submissions.txt`, per-stage logs and eventual manifest.

### 2026-10-27 · komondor-ray-20261027-a1 · completed

- Question: Does the existing Komondor runtime start an authenticated Ray cluster across two nodes?
- Setup: Source `79cc198`; existing `runtime-sandbox`, two CPU nodes, four CPUs and 16 GiB RAM per node, five-minute cap.
- Result: Job `14672379` completed in 1m25s, exit `0:0`. The driver reported success with remote tasks on two distinct hosts. The server step was explicitly killed by owned-step cleanup after success.
- Resources: Eight CPUs; zero GPUs.
- Evidence: Private project `edotenv/komondor-ray-20261027-a1/result/driver.log` and retained Ray logs. This validates CPU startup, not GPU model initialization or training.

### 2026-10-27 · euler-preparation-a4 · submitted

- Question: Does a writable compiler cache resolve the observed FlashAttention build failure?
- Setup: Source `930c270`, new `runtime-a4`/`models-a4`; reuse the completed a3 SIF after provenance/inspection checks, with compiler cache and temporary files on node-local storage.
- Result: Targeted CPU job `18546450` submitted. No runtime, model, Ray or GPU success claimed.
- Resources: Eight CPUs, 64 GiB RAM, 50 GB local scratch, one-hour cap; zero GPUs requested.
- Evidence: Private Euler scratch `edotenv/abc-20261026/prepare-a4-18546450.log` and `submissions.txt`.

### 2026-10-27 · euler-preparation-a3 · failed

- Question: Does node-local extraction allow runtime preparation to complete?
- Setup: Source `6ccf09b`, new `runtime-a3`/`models-a3`; 150 GB Slurm-managed local scratch for extraction and compilation, same pinned public image and uv environment.
- Result: Job `18541043` produced the 13 GB SIF, then FlashAttention compilation failed because ccache attempted to write to the read-only image. Runtime imports, models, Ray and GPU paths remain unvalidated.
- Resources: Eight CPUs, 64 GiB RAM, elapsed 22m16s, exit `1:0`; zero GPUs.
- Evidence: Private Euler scratch `edotenv/abc-20261026/prepare-a3-18541043.log` and `submissions.txt`. No further long blind retry if this attempt fails.

### 2026-10-27 · euler-preparation-a2 · failed

- Question: Does the corrected Euler proxy and external uv environment permit runtime/model staging?
- Setup: Source `bda1fc6`; new `runtime-a2` and `models-a2` under private Euler scratch `edotenv/abc-20261026`. Container-access group membership is now present; the preceding CPU shell check passed.
- Result: After the queues reopened, Slurm `18523280` reached its one-hour limit during container extraction on shared scratch. No SIF, dependency build, models or training results were produced.
- Resources: Eight CPUs, 64 GiB RAM; elapsed 1h00m29s; zero GPU usage.
- Evidence: `prepare-a2-18523280.log` and scheduler accounting. Retry uses Slurm node-local scratch for extraction/builds, following Euler storage guidance, with a two-hour CPU cap; GPU gates remain unchanged.

### 2026-10-26 · euler-preparation-a1 · failed

- Question: Can Euler stage the runtime before A/B/C smoke checks?
- Setup: Revision `da5e7dc`, CPU preparation followed by dependency-gated Ray and A/B/C jobs.
- Result: Preparation `18476549` failed reaching Docker Hub after seven seconds. Ray `18476572` and A/B/C `18476616`, `18476617`, `18476620` were cancelled on failed dependencies before allocation. No training ran.
- Resources: Eight allocated CPUs for seven seconds; zero GPU allocation time.
- Evidence: Private Euler scratch `edotenv/abc-20261026/prepare-18476549.log` and Slurm accounting. Proxy, runtime preparation and container-access gaps are tracked in the [Euler report](policy-distillation/EULER.md).

### 2026-10-26 · euler-inventory · unavailable

- Question: Can Euler immediately allocate eight GPUs across two nodes?
- Setup: Read-only SSH/scheduler/runtime inspection, then a bounded two-minute inventory request. Per-node memory and an explicit GPU account were rejected before allocation; per-CPU memory and default account selection were accepted.
- Result: Slurm `18475970` could not obtain the requested nodes immediately and was cancelled without running. No GPU execution or training evidence.
- Resources: zero allocation time; no GPU-hours consumed. Runtime and selected model caches still need staging.
- Evidence: Scheduler accounting reports `CANCELLED`, elapsed `00:00:00`; cluster context and next steps are in the [Euler report](policy-distillation/EULER.md).

### 2026-10-26 · distillation-sync-smoke-20261026-a5 · failed

- Question: Does the distributed synchronous path work with validated Ray startup settings?
- Setup: Revision `d2bd5dc`, same three-update smoke workload, pinned models and runtime. Ray uses head port 6379 and explicit per-attempt token authentication. Earlier frozen baselines are unchanged.
- Result: Head startup reached an authenticated Ray cluster, but its client service timed out waiting for node registration. The head shut down and the readiness driver failed before model loading or updates. The precise startup delay remains unresolved; no further jobs are submitted pending the user's checkpoint.
- Resources: Slurm `14651539`, eight GPUs across two nodes, failed after 1m48s, exit `1:0`; approximately 0.240 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/sync-smoke-20261026-a5/` and corresponding log. Attempted collection of node-local Ray logs after exit was rejected because the allocation had expired.

### 2026-10-26 · distillation-ray-cli2-20261026 · completed

- Question: Does explicit token authentication allow the CLI head and API driver to communicate?
- Setup: Same CPU CLI check, setting `RAY_AUTH_MODE=token` for both processes. Dependencies and model runtime unchanged.
- Result: CLI head startup, driver connection, remote task and cleanup passed. The training launcher now uses explicit token mode and a private per-attempt token file shared by its head, workers and driver.
- Resources: Slurm `14651528`, two CPUs, 8 GiB RAM; 13 seconds, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/ray-cli-check2.sh` and `ray-cli-check2.log`.

### 2026-10-26 · distillation-ray-cli-20261026 · cancelled

- Question: Does the actual Ray CLI start and accept remote work using a nonconflicting head port?
- Setup: Same container and environment; head port 6379 is outside Ray's worker range. CPU-only head, connecting driver, remote task and owned-process cleanup.
- Result: Port accepted, but CLI head enabled token authentication automatically while the explicitly addressed API driver did not. Connection rejected; stopped for an explicit shared-authentication retry.
- Resources: Slurm `14651470`, two CPUs, 8 GiB RAM, cancelled after 51 seconds; no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/ray-cli-check.sh` and `ray-cli-check.log`.

### 2026-10-26 · distillation-sync-smoke-20261026-a4 · cancelled

- Question: Does the full synchronous path execute after both launcher startup fixes?
- Setup: Revision `ee18621`, unchanged pinned models, runtime and three-update smoke configuration. Optional topology snapshots are best effort; existing stage timers remain the only performance instrumentation.
- Result: Native checks passed, but Ray rejected head port 16379 because it overlaps its default worker range 10002–19999. No model initialization or training updates ran. Retry uses head port 6379 after a CLI check.
- Resources: Slurm `14651465`, eight GPUs across two nodes, cancelled after 1m55s; approximately 0.256 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/sync-smoke-20261026-a4/` and corresponding log.

### 2026-10-26 · distillation-node-startup-20261026 · completed

- Question: Does the node launcher reach Ray startup when optional network tools are absent?
- Setup: Actual container and node script, with native-probe and Ray executables replaced by fixtures; the real GPU probe and Ray task have separate passing evidence. Network capture falls back to kernel routes and cannot abort training.
- Result: Node script reached the Ray-start fixture with missing network tools; shell syntax passed.
- Resources: Slurm `14651434`, one CPU, 2 GiB RAM; one second, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/node-startup-fix.tar.gz`, `node-startup-check.sh`, `node-startup-check.log` and `node-check-14651434/`.

### 2026-10-26 · distillation-sync-smoke-20261026-a3 · cancelled

- Question: Does synchronous training initialize and complete after the Ray startup fix?
- Setup: Revision `b619222`, same pinned models, runtime, prompts and three-update configuration as the cancelled attempt. Disable Ray's unnecessary environment autodetection and abort immediately if readiness fails.
- Result: Eight-GPU collective and native probes passed. Both node launchers then failed because the optional network snapshot invoked the absent `ip` utility; Ray never started and no updates ran. Stopped the attempt and made snapshots best effort.
- Resources: Slurm `14651432`, eight GPUs across two nodes, cancelled after 2m20s; approximately 0.311 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/sync-smoke-20261026-a3/` and corresponding log.

### 2026-10-26 · distillation-ray-startup-20261026 · completed

- Question: Can Ray initialize and execute a remote task without inspecting inaccessible Slurm ancestors?
- Setup: Disable Ray's automatic `uv run` environment detection; dependencies remain installed with uv in the prepared container. Check updated launcher shell syntax and real Ray startup/task/shutdown inside a CPU allocation.
- Result: Launcher shell syntax, Ray initialization, remote task and shutdown passed. Ray still warns that it cannot inspect dashboard descendants; this did not prevent the task. Slurm remains responsible for allocation containment.
- Resources: Slurm `14651431`, two CPUs, 8 GiB RAM; 38 seconds, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/ray-startup-fix.tar.gz`, `ray-startup-check.sh` and `ray-startup-check.log`.

### 2026-10-26 · distillation-sync-smoke-20261026-a2 · cancelled

- Question: Does the complete synchronous path execute three updates and save a checkpoint?
- Setup: Revision `7093564`, pinned models/runtime, eight synthetic smoke prompts, three batches of eight with a 512-token response cap. Both frozen-model baseline evaluations completed before submission. Existing stage timers only; detailed profiling is deferred.
- Result: Candidate-runtime BF16 all-reduce passed on all eight GPUs (PyTorch 2.13.0/CUDA 13/NCCL 2.29.7). Ray readiness failed when automatic `uv run` detection inspected an inaccessible Slurm ancestor. The inner driver shell incorrectly continued after that failure; stopped the job before model initialization or updates. The retry disables that detection and makes inner shells fail immediately.
- Resources: Slurm `14651375`, eight GPUs across two nodes, cancelled after 2m13s; approximately 0.296 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/sync-smoke-20261026-a2/` and corresponding log. Import errors also appeared during cancellation; their relation to teardown remains unverified. No full run.

### 2026-10-26 · distillation-step-cleanup-20261026 · completed

- Question: Does the training launcher's cleanup terminate only its recorded Slurm worker step and return promptly?
- Setup: Real CPU Slurm step running a sleep fixture; invoke the launcher's cleanup function against that step. Shell syntax checked for the updated launcher and node script.
- Result: Step killed and reaped while its parent allocation remained alive; Slurm `14651228`, one second, exit `0:0`, one CPU, 1 GiB RAM, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/smoke-launcher.tar.gz`, `step-cleanup-check.sh`, `step-cleanup-check.log` and `step-cleanup-14651228/`.

### 2026-10-26 · distillation-baseline-batched-20261026 · completed

- Question: Can bounded batches complete both frozen-model baselines within the pilot budget?
- Setup: Same 32 examples, checkpoints, greedy decoding and 8192-token limit; batch size eight for both models. This changes scheduling and may change numerical generation behavior; cancelled sequential attempts are not pooled with this pilot. The batched evaluator passed fourteen CPU tests and the real-tokenizer/HTTP/grader fixture.
- Result: Student 22/32 correct (68.75%), ten truncated; teacher 27/32 (84.375%), five truncated. No request or grading errors. Evaluation elapsed time was 811.85s and 832.97s respectively. This small development pilot suggests a teacher advantage; truncation and sample size limit quality conclusions.
- Resources: Slurm `14651195` (student) and `14651196` (teacher), each two GPUs, eight CPUs and 64 GiB RAM. Completed in 14m59s and 16m02s respectively, both exit `0:0`; approximately 1.034 GPU-hours combined, including startup and cleanup.
- Evidence: Private `edotenv/distillation-check-20261026-a1/baseline-{student,teacher}-<job-id>/` and corresponding logs. Two dependency-based submissions were rejected before allocation because the earlier completed jobs were no longer accepted as dependencies.

### 2026-10-26 · distillation-evaluator-batch-20261026 · completed

- Question: Does batching preserve example alignment, final partial batches and failure evidence?
- Setup: Updated evaluator, mismatch rejection and grading-failure regression; actual checkpoint tokenizer and Slime grader with a two-response fixture HTTP server.
- Result: Slurm `14651186`, fourteen CPU tests, Ruff, formatting, shell checks and real-runtime fixture passed; 20 seconds, two requested CPUs, 8 GiB RAM, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/evaluator-batch.tar.gz`, `evaluator-batch.log` and `eval-batch-formatted.tar.gz`. Fixture correctness is not model accuracy.

### 2026-10-26 · distillation-arguments-gpu2-20261026 · completed

- Question: Does full argument validation pass with the production launcher's environment?
- Setup: Same parser-only probe with `CUDA_DEVICE_MAX_CONNECTIONS=1`, already set by the real launcher; no training.
- Result: Full Slime/Megatron/SGLang argument validation passed for both synchronous and fully asynchronous modes, including BF16, sampled-token objective and policy-lag configuration. No training ran.
- Resources: Slurm `14651194`, one GPU, two CPUs, 8 GiB RAM; 1m50s, exit `0:0`, approximately 0.031 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/argument-probe-gpu2.log`.

### 2026-10-26 · distillation-arguments-gpu-20261026 · failed

- Question: Can the full parser run with the CUDA driver available?
- Setup: Same parser-only probe inside an A100 allocation, adding Apptainer GPU passthrough.
- Result: Reached Megatron validation, which rejected the probe's missing `CUDA_DEVICE_MAX_CONNECTIONS=1`. The production launcher already sets it; this was a probe setup error.
- Resources: Slurm `14651173`, one GPU, two CPUs, 8 GiB RAM; 4m18s, exit `1:0`, approximately 0.072 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/argument-probe-gpu.log`.

### 2026-10-26 · distillation-arguments-20261026 · failed

- Question: Does the complete runtime argument parser accept both launch modes and preserve the intended objective and hook settings?
- Setup: Actual pinned Slime, Megatron and SGLang parsers; generated serving/hooks configuration and project training arguments; no model loading or optimizer updates.
- Result: Transformer Engine import requires `libcuda.so.1`, unavailable in the CPU allocation; full parsing did not complete.
- Resources: Slurm `14651163`, two requested CPUs, 8 GiB RAM; 32 seconds, exit `1:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/argument-probe.py`, `argument-probe.sh` and `argument-probe.log`.

### 2026-10-26 · distillation-baseline-retry-20261026 · cancelled

- Question: Can both frozen models complete the fixed development evaluation after the tokenizer and cleanup fixes?
- Setup: Same pinned models and 32-example protocol as the failed student attempt. Explicit token-ID output passed the real-runtime CPU contract check; cleanup passed its failure fixture. Student and teacher run independently with identical settings and no weight updates.
- Result: Student generation worked at about 42 tokens/second, but the first long response showed sequential evaluation would not reliably fit the budget. Both attempts were cancelled to use matched batching; no complete quality result. Teacher was still loading.
- Resources: Slurm `14651158` (student) and `14651159` (teacher), each two GPUs, eight CPUs, 64 GiB RAM; each cancelled at 4m28s, approximately 0.298 GPU-hours combined.
- Evidence: Private `edotenv/distillation-check-20261026-a1/baseline-{student,teacher}-<job-id>/` and corresponding job logs.

### 2026-10-26 · distillation-cleanup-20261026 · completed

- Question: Does baseline cleanup terminate a server that ignores SIGTERM without retaining its allocation?
- Setup: Bounded five-second grace period followed by SIGKILL to the owned process group; CPU fixture deliberately ignores SIGTERM.
- Result: The SIGTERM-resistant fixture was killed and reaped within the bound; baseline shell syntax passed.
- Resources: Slurm `14651153`, one CPU, 1 GiB RAM; five seconds, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/cleanup-check.sh`, `baseline-cleanup.sh` and `cleanup-check.log`.

### 2026-10-26 · distillation-evaluator-contract-20261026 · completed

- Question: Does explicit token-ID output fix evaluation with the actual runtime tokenizer and grader?
- Setup: Updated evaluator and regression test; CPU container check uses the pinned student tokenizer, a local fixture HTTP server and the real Slime math grader. This tests JSON transport without generating model answers.
- Result: Actual tokenizer, JSON transport and grader passed; thirteen adapter tests, Ruff and shell checks also passed. The response was a fixture, not model inference.
- Resources: Slurm `14651151`, two requested CPUs, 8 GiB RAM; 44 seconds, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/evaluator-fix.tar.gz`, `evaluator-check.log` and `edot-evaluation-probe.py`.

### 2026-10-26 · distillation-student-baseline-20261026-a1 · failed

- Question: What starting accuracy, truncation and evaluation cost does the student show under the fixed development protocol?
- Setup: Pinned student, frozen inference only, prepared 32-example MATH-500 development subset; greedy generation up to 8192 tokens, Slime math grader, BF16 SGLang Triton TP2 with CUDA graphs disabled. Evaluator timeout patch passed CPU checks before launch.
- Result: Model serving became healthy, but all 32 requests failed before generation: the runtime tokenizer defaults to `BatchEncoding`, which the evaluator cannot serialize as token IDs. No quality result was obtained. Server shutdown then stalled on `psutil.AccessDenied`; the allocation was cancelled manually.
- Resources: Slurm `14651072`, two GPUs on one node, eight CPUs, 64 GiB RAM; 17m10s including stalled cleanup, approximately 0.572 GPU-hours; scheduler status cancelled.
- Evidence: Private `edotenv/distillation-check-20261026-a1/baseline-student-14651072/` and `baseline-student-14651072.log`. Teacher baseline and training remain outstanding. Retry requires explicit token-ID output and bounded cleanup.

### 2026-10-26 · distillation-baseline-prep-20261026 · completed

- Question: Can the fixed development pilot be prepared reproducibly before either model is evaluated?
- Setup: [Pilot protocol](../../configs/distillation/baseline-pilot.json), pinned MATH-500 source, first 32 rows by SHA256 of `unique_id`; remaining 468 reserved. No model execution.
- Result: Slurm `14651063`, data prepared with source/evaluation hashes and selected/reserved IDs; thirteen CPU tests, Ruff and shell checks passed, including configurable generation-request timeout. Two seconds, two requested CPUs, 8 GiB RAM, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/baseline-prep.tar.gz`, `baseline-prep.log`, `prepare-edot-baseline.py` and `baseline-data/manifest.json`.

### 2026-10-26 · distillation-flash2-native2-20261026 · completed

- Question: Can the native A100 probe execute after the unused FA4 import conflict is removed?
- Setup: Same probe and runtime as `14650838`, with FA4 uninstalled by `14650955`; no other package changes.
- Result: BF16 matrix multiplication, packed GQA forward/reference agreement and backward, RMSNormLinear forward/backward, and the Megatron Adam update all passed on A100. This does not exercise model inference or training.
- Resources: Slurm `14651045`, one GPU, four CPUs, 16 GiB RAM; 3m07s, exit `0:0`, approximately 0.052 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/flash2-native2.log`. An earlier submission was rejected by the shared per-user job-count limit before allocation.

### 2026-10-26 · distillation-contract2-20261026 · completed

- Question: Does the new contract regression pass with the complete pinned Slime Python package available?
- Setup: Retry after replacing the incomplete staged dependency source with the package from the verified checkout. No test-code change.
- Result: Slurm `14651044`, all thirteen CPU tests, Ruff and shell checks passed; two seconds, two requested CPUs, 8 GiB RAM, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/contract-check2.log`. The bounded contract check does not execute Slime's full GPU argument parser.

### 2026-10-26 · distillation-contract-20261026 · failed

- Question: Do the pinned Slime reward accessor and custom-configuration statements satisfy the adapter's entry contracts?
- Setup: New CPU regression against the actual submodule source, with numpy/httpx added to the uv test environment; remaining adapter tests, Ruff and shell checks included.
- Result: Twelve tests passed; the new test could not read `arguments.py` because the earlier staged dependency archive was incomplete. Ruff and shell checks passed.
- Resources: Slurm `14650958`, two requested CPUs, 8 GiB RAM; six seconds, exit `1:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/contract-update.tar.gz` and `contract-check.log`.

### 2026-10-26 · distillation-flash4-removal-20261026 · completed

- Question: Does removing unused FlashAttention-4 resolve the native probe's eager-import conflict while preserving FlashAttention-2?
- Setup: uv uninstall in the owned writable runtime; before/after package lists and FA2 import check retained. No upstream source edits or PyTorch replacement.
- Result: Only `flash-attn-4==4.0.0b19` was removed; FA2 imports passed.
- Resources: Slurm `14650955`, two requested CPUs, 8 GiB RAM; three seconds, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/flash4-removal.log` and `flash4-removal/`. GPU qualification remains separate.

### 2026-10-26 · distillation-async-smoke-20261026-a1 · cancelled

- Question: Can the frozen-teacher distillation path complete a bounded fully asynchronous run without violating score or policy-age checks?
- Setup: Revision `2deac06`, selected pinned DeepSeek models, eight arithmetic execution prompts, three rollouts; queued after synchronous job `14650897`.
- Result: Held and cancelled before execution to preserve the agreed baseline-before-training prerequisite; no runtime logs or training artifacts were produced.
- Resources: Slurm `14650899`, planned eight GPUs/two nodes and 30 minutes; actual elapsed time and GPU-hours zero.

### 2026-10-26 · distillation-sync-smoke-20261026-a1 · cancelled

- Question: Can the initial distributed Slime path generate, score, train, and save a student checkpoint?
- Setup: Revision `2deac06`, selected pinned DeepSeek models, eight arithmetic execution prompts, three rollouts; queued after native-kernel probe `14650838`.
- Result: Held and cancelled before execution because this would update weights before both models' task baselines were established. Implementation review `071c98e7224f` F1 identified the ordering error; the original prerequisite is retained.
- Resources: Slurm `14650897`, planned eight GPUs/two nodes and 30 minutes; actual elapsed time and GPU-hours zero. No training artifacts were produced.

### 2026-10-26 · distillation-flash2-native-20261026 · failed

- Question: Does the rebuilt runtime execute the student's packed GQA and RMSNorm kernels on A100?
- Setup: Feature-branch probe with explicit flash backend and consistent cuDNN path, following successful build `14650836`.
- Result: Failed while importing Transformer Engine: bundled FlashAttention-4 expects `cutlass.cute.core.ThrMma`, absent from the installed CUTLASS API. The intended packed-attention, RMSNorm and Adam checks did not execute.
- Resources: Slurm `14650838`, one GPU, four CPUs, 16 GiB RAM; 2m32s, exit `1:0`, approximately 0.042 GPU-hours.
- Evidence: Private `edotenv/distillation-check-20261026-a1/flash2-native.log`. No model training.

### 2026-10-26 · distillation-flash2-build2-20261026 · completed

- Question: Can the A100 extension build complete with an explicit resource budget?
- Setup: Retry of `14650807` with six compiler workers and two NVCC threads each, overriding the image's inherited build settings. Existing CUDA/PyTorch retained.
- Result: FlashAttention-2 2.8.3 built for sm80, installed through uv and imported successfully. Compilation/import alone does not qualify GPU execution.
- Resources: Slurm `14650836`, thirteen CPUs, 48 GiB RAM; 30m40s, exit `0:0`, no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/flash2-build2.log` and `flash2-build2/`, including versions, exact flags and completion marker.

### 2026-10-26 · distillation-uv-check2-20261026 · completed

- Question: Does the reusable uv CPU initializer preserve passing adapter checks?
- Setup: Python 3.12, explicit CPU PyTorch index, pinned requirements; corrected the lint annotation from the previous attempt.
- Result: Slurm `14650816`, all twelve tests, Ruff, and shell syntax passed. The kernel probe was formatted but not executed on CPU. Runtime compilation remains separate.
- Evidence: Private `edotenv/distillation-check-20261026-a1/uv-cpu-check2.log`, `.venv/requirements-resolved.txt`, and `uv-formatted.tar.gz`.

### 2026-10-26 · distillation-uv-check-20261026 · failed

- Question: Does the new uv setup and expanded native probe pass CPU checks?
- Setup: Same environment initializer and pinned dependencies; Slurm `14650812`, two requested CPUs, 8 GiB RAM, no GPUs.
- Result: Environment setup succeeded; Ruff rejected an incorrectly written unused-import annotation after one second. Tests did not execute. The follow-up records the corrected probe's implementation module instead.
- Evidence: Private `edotenv/distillation-check-20261026-a1/uv-cpu-check.log`.

### 2026-10-26 · distillation-flash2-build-20261026 · cancelled

- Question: Can FlashAttention-2 be built for A100 against the selected Slime runtime?
- Setup: Owned writable runtime sandbox from the recorded OCI digest; uv, FlashAttention 2.8.3 source, sm80 only, existing PyTorch/CUDA retained. Reusable project initializer records provenance.
- Resources: Slurm `14650807`, initially eight requested CPUs and 64 GiB RAM; reduced while queued to thirteen allocated CPUs and 48 GiB RAM to fit available capacity. 45-minute limit; no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/flash2-build.log` and `flash2-build/`. Stopped after 1m15s when provenance showed the base image had supplied `MAX_JOBS=16`. Retry sets its own six-worker build budget; no GPU kernels ran.

### 2026-10-26 · distillation-fused-coherent-20261026 · failed

- Question: Does a single cuDNN version make packed GQA fused attention available on A100?
- Setup: Same candidate probe, now setting both `CUDNN_HOME` and `LD_LIBRARY_PATH` to PyTorch's libraries. Debug output confirmed cuDNN 9.20.
- Result: Slurm `14650796`, one GPU, 24 seconds, exit `1:0`; no supported fused backend for this configuration. No model training. Retain the planned FlashAttention-2 training path.
- Evidence: Private `edotenv/distillation-check-20261026-a1/fused-coherent.log`.

### 2026-10-26 · distillation-fused-debug-20261026 · failed

- Question: Which libraries and attention backend did the earlier retry actually select?
- Setup: Repeat with Transformer Engine debug logging, no package changes.
- Result: Slurm `14650789`, one GPU, 35 seconds, exit `1:0`; TE still selected system cuDNN 9.14 despite the library-path prefix, and found no backend.
- Evidence: Private `edotenv/distillation-check-20261026-a1/fused-debug.log`. Motivated setting TE's documented `CUDNN_HOME` as well.

### 2026-10-26 · distillation-fused-cudnn-20261026 · failed

- Question: Does a consistent cuDNN library path resolve the candidate backend's import failure?
- Setup: Repeat the same fused-attention/reference and RMSNormLinear probe, placing the image's PyTorch cuDNN 9.20 library directory first in `LD_LIBRARY_PATH`. No package or container-source changes.
- Resources: Slurm `14650787`, one GPU, four requested CPUs, 16 GiB RAM, eight-minute limit.
- Evidence: Private `edotenv/distillation-check-20261026-a1/fused-cudnn.log`; failed after 1m47s, exit `1:0`, with no available fused backend. A debug follow-up checked the actual cuDNN selection.

### 2026-10-26 · distillation-fused-20261026 · failed

- Question: Does the image's cuDNN fused-attention route support A100 without adding FlashAttention-2?
- Setup: Forced fused attention, BF16 packed GQA forward compared with an explicit causal-softmax reference, backward finiteness, and RMSNormLinear forward/backward. This tests a candidate backend before changing training settings.
- Resources: Slurm `14650783`, one GPU, four requested CPUs, 16 GiB RAM, eight-minute limit.
- Result: Fourteen seconds, exit `1:0`; cuDNN 9.14 system libraries conflicted with PyTorch's cuDNN 9.20 while importing Transformer Engine. This did not test the fused kernels.
- Evidence: Private `edotenv/distillation-check-20261026-a1/fused-probe.py` and `fused-probe.log`.

### 2026-10-26 · distillation-gpu-sandbox-20261026 · failed

- Question: Can the fully extracted runtime execute on A100 without completing SIF compression?
- Setup: Apptainer's directory runtime using the original complete extracted filesystem from `14650675`, moved after that job ended; same native-kernel probe. The partial preservation copy is unused.
- Resources: Slurm `14650736`, one GPU, four requested CPUs, 16 GiB RAM, five-minute limit.
- Result: Failed after 3m07s, exit `1:0`: the image contains FlashAttention-3/4 but no FlashAttention-2 API. The independent CPU import step passed (PyTorch 2.13.0/CUDA 13.0, Ray, SGLang, Megatron, Transformer Engine). No model training ran.
- Evidence: Private `edotenv/distillation-check-20261026-a1/gpu-runtime-sandbox.log` and `sandbox-import.log`.

### 2026-10-26 · distillation-gpu-runtime-20261026 · failed

- Question: Does the prepared Slime image execute its native kernels on A100?
- Setup: Runtime imports, BF16 matrix multiplication, FlashAttention and Transformer Engine forward/backward probes; dependent on image preparation. No models or training data.
- Resources: Slurm `14650730`, one GPU, four requested CPUs, 16 GiB RAM, five-minute limit (at most 0.083 GPU-hours).
- Result: Two seconds, exit `1:0`; the prerequisite SIF image was absent after preparation timed out. No native kernels ran.
- Evidence: Private `edotenv/distillation-check-20261026-a1/gpu-runtime.log`.

### 2026-10-26 · distillation-final-cpu-20261026 · completed

- Question: Does the final configuration retain passing checks with four GPUs per node and native-kernel probes?
- Setup: Final adapter checks as an overlapping CPU step within allocation `14650675`; the queued duplicate allocation `14650722` was cancelled before execution.
- Result: All twelve tests, Ruff, formatting, and shell syntax passed. GPU kernels are not exercised by these CPU tests.
- Evidence: Private `edotenv/distillation-check-20261026-a1/final-cpu-inline.log`.

### 2026-10-26 · distillation-weights-20261026 · completed

- Question: Can the pinned teacher/student snapshots be staged and verified on shared project storage?
- Setup: The model lock and allocation-only downloader, `huggingface-hub==0.34.4` through uv; no inference.
- Resources: Slurm `14650718`, four requested CPUs, 16 GiB RAM, 15-minute limit; no GPUs.
- Evidence: Private `edotenv/distillation-check-20261026-a1/model-staging.log` and `models/verification.json`. Both snapshots downloaded and metadata/weight hashes verified; completed in 3m41s, exit `0:0`.

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

### 2026-10-26 · distillation-runtime-20261026 · failed

- Question: Can the documented Slime container provide the pinned training stack on Komondor?
- Setup: Apptainer pull of `slimerl/slime` digest `sha256:6379b872c6cc2535fb8c0e073a79bb1f41e365ca4859dd308e99ba14eb87936d`, then CPU import checks.
- Resources: Slurm `14650675`, planned eight CPUs, 64 GiB RAM, 30 minutes on `test`; no GPUs or model weights.
- Result: Timed out after 30m03s during SIF compression, after extraction and Apptainer configuration completed. The scheduler denied extending the running job. The complete extracted filesystem survived and was moved to `runtime-sandbox` for a directory-runtime retry; an interrupted hardlink preservation attempt is not used.
- Evidence: Private `edotenv/distillation-check-20261026-a1/runtime-preparation.log`. No import or GPU validation completed in this attempt.

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
