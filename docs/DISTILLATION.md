# Classical distillation implementation

The project adapters use the pinned Slime checkout without modifying it.
The initial DeepSeek pair and exact revisions are in
[the model lock](../configs/distillation/models.json). Their tokenizer,
tokenizer configuration, and generation configuration files are byte-identical.
The model vocabulary sizes differ (151936 student, 152064 teacher); teacher
scores are aligned by actual sampled token IDs, not by equating output shapes.

## Training behavior

[The launcher](../distillation/launch.py) uses Slime's sampled-token reverse-KL
advantage with its REINFORCE loss, recomputing current student log probabilities.
Task rewards, reward/advantage normalization, entropy bonuses, reference-model
penalties, and importance corrections are disabled. Sampling uses temperature
1 and the full vocabulary. This is an initial implementation baseline; its
learning quality remains to be established. The sampled log-probability
difference is not an exact distribution KL.

Sync and async share those settings. Async allows one publication of policy lag
by default; sync allows none. Unknown, future, or excessively old policy versions
abort the attempt rather than silently dropping examples. The bound is configurable
with `--max-policy-lag`. It does not eliminate off-policy bias or guarantee stability.
The wrappers rely on the pinned fresh-run driver's one weight publication per
rollout; resuming training is outside this launcher's current scope.

The initial eight-GPU configuration uses four trainer GPUs (TP2, DP2), two
student-generation GPUs (TP2), and two frozen-teacher GPUs (TP2). Both serving
models are managed through Slime's multi-model configuration; only the student
receives weight updates. Ray determines placement, which must be checked in the
logs alongside the captured GPU/network topology. Object-store transport is used
initially. The teacher hook rejects missing scores, token-ID mismatches, and
nonfinite probabilities; HTTP failures propagate instead of becoming zero rewards.

## Running

Run manual tests and workloads inside Komondor compute allocations. Local editing
and artifact preparation are permitted; greengoblin remains transit-only. Use uv
for project-managed Python setup. Keep the GPU runtime separate from
[CPU-test requirements](../requirements-distillation-test.txt).

For CPU adapter tests, run `bash scripts/init-distillation-tests.sh` in the
allocation, then run the adapter suite from the checkout:

```sh
.venv-distillation/bin/python -m unittest discover -s tests -p test_distillation.py -v
```

The initializer uses Python 3.12,
fetches CPU PyTorch from its own index, and records resolved versions. The
`distillation` package has an explicit `__init__.py`; run its modules from the
checkout, with the pinned Slime source on `PYTHONPATH` when using its hooks.

The candidate GPU runtime starts from Slime's OCI digest
`sha256:6379b872c6cc2535fb8c0e073a79bb1f41e365ca4859dd308e99ba14eb87936d`
(`slimerl/slime`, CUDA 13). It lacks FlashAttention-2. Inside an owned writable
copy, [the A100 initializer](../scripts/init-distillation-a100.sh) builds the
[pinned addition](../requirements-distillation-a100.txt) with uv against the
existing PyTorch. It removes unused FlashAttention-4, whose bundled CUTLASS API
breaks Transformer Engine's eager import on this runtime. Set `RUNTIME_BUILD_RECORD`
to a new directory; it retains setup, versions, build flags, and logs. The FA2
build, A100 kernel probe and frozen-model baseline inference passed; integrated
training remains unvalidated. Source
[the runtime environment](../scripts/distillation-runtime-env.sh) inside the
container to make PyTorch and Transformer Engine use the same cuDNN libraries;
the Slurm launcher does this for both driver and workers.

[The container initializer](../scripts/init-distillation-runtime.sh) assembles
those steps in a CPU allocation:

```sh
RUNTIME_ROOT=/approved/shared/new-runtime bash scripts/init-distillation-runtime.sh
```

It refuses an existing destination, keeps caches on that shared storage, and
builds a directory runtime at `$RUNTIME_ROOT/rootfs`. It defaults to six compiler
workers; allocate memory/CPUs accordingly or set `DISTILLATION_BUILD_JOBS`.
The combined initializer has not yet been exercised from a clean image download;
the current qualification uses the same pinned image's preserved extraction.

The launcher requires a compatible A100 Slime runtime, the initialized submodule,
and identical shared paths on both nodes. The upstream container is being qualified;
its presence or successful imports alone do not establish A100 kernel compatibility.
Stage pinned weights inside a compute allocation with the runtime's Python:

```sh
python -m distillation.download --output /approved/shared/models
```

`python -m distillation.launch --help` describes preparation and direct execution
on an existing Ray cluster. Preparation verifies metadata and records actual
weight hashes, arguments, source revisions, and dataset hash in a new private
output directory. Raw responses and training logs remain in that directory.

For the two-node allocation, export `PROJECT_ROOT`, `MODEL_ROOT` (containing
`student/` and `teacher/`), `TRAIN_DATA`, `RUN_ROOT` (a new directory), and
`RUNTIME_IMAGE`. Submit [distillation.slurm](../scripts/distillation.slurm) with
the authorized account. Set `MODE=synchronous` or `MODE=fully_async`. The current
script requests two four-GPU nodes for at most 30 minutes. It owns a dedicated
Ray cluster, first checks an eight-GPU collective in the candidate runtime,
records runtime/topology evidence, and terminates its own Slurm steps. Cleanup
kills the recorded Ray step so a server shutdown error cannot retain the allocation.

[Smoke prompts](../configs/distillation/smoke.jsonl) are for execution checks only.
They are not a learning benchmark. For baseline and checkpoint evaluation,
[the separate evaluator](../distillation/evaluate.py) accepts an SGLang endpoint,
the served checkpoint path, and held-out JSONL with `prompt` and `answer` fields.
It uses greedy generation and Slime's math grader by default, preserving failures
and truncations. `--request-timeout` accommodates longer reasoning responses;
the timeout is recorded alongside the decoding settings. Select the task, decoding budget, and suitable scorer before
interpreting quality. `--batch-size` bounds each request and is recorded in results;
response-count mismatches fail instead of silently misaligning examples. Use
the same evaluation configuration for both models and
trained checkpoints. Training checkpoints need Slime's supported HF export before
serving them for evaluation.

## Evidence and remaining limits

Komondor job `14650670` passed ten CPU tests: teacher HTTP scoring and alignment,
policy-age validation, configuration consistency, tokenizer rejection, and the
actual pinned loss helper's gradient against an enumerated reverse-KL reference.
The loss-helper test isolates the function from Megatron; it is not a distributed
training test. Checkpoint metadata preflight, Ruff, and shell syntax checks passed.
Follow-up job `14650690` passed eleven tests, including the actual Slime serving
configuration parser. Follow-up regressions bring this to fourteen passing tests,
including the real `Sample` reward accessor and custom-configuration statements.
A separate site-runtime NCCL probe passed across eight A100s on two nodes using
one Slurm launcher per node. The candidate Slime runtime now passes the A100
packed-attention/reference, backward, RMSNorm and Adam kernel probe.
See the [journal](experiments/LOG.md) for attempts
and coverage limits. Actual Slime model execution, end-to-end async behavior,
and learning-quality comparisons remain unvalidated.
