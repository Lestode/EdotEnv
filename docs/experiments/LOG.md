# Experiment journal

Follow [experiment guidance](../EXPERIMENTS.md#maintain-experiment-continuity).
Keep one short entry per run, newest first, using a stable run ID that also
identifies its artifacts. Aim for 50–100 words per entry; link to detailed
configuration and evidence. Record each retry as a separate attempt linked to
the earlier entry so failures remain visible.

## Run entries

### 2026-10-26 · distillation-student-baseline-20261026-a1 · running

- Question: What starting accuracy, truncation and evaluation cost does the student show under the fixed development protocol?
- Setup: Pinned student, frozen inference only, prepared 32-example MATH-500 development subset; greedy generation up to 8192 tokens, Slime math grader, BF16 SGLang Triton TP2 with CUDA graphs disabled. Evaluator timeout patch passed CPU checks before launch.
- Resources: Slurm `14651072`, two GPUs on one node, eight CPUs, 64 GiB RAM, 30-minute limit (at most one GPU-hour).
- Evidence: Private `edotenv/distillation-check-20261026-a1/baseline-student-14651072/` and `baseline-student-14651072.log`; pending. Teacher baseline and training remain outstanding.

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
