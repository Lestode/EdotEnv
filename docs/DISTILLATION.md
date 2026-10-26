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
Ray cluster, records runtime/topology evidence, and terminates its own Slurm steps.

[Smoke prompts](../configs/distillation/smoke.jsonl) are for execution checks only.
They are not a learning benchmark. For baseline and checkpoint evaluation,
[the separate evaluator](../distillation/evaluate.py) accepts an SGLang endpoint,
the served checkpoint path, and held-out JSONL with `prompt` and `answer` fields.
It uses greedy generation and Slime's math grader by default, preserving failures
and truncations. Select the task, decoding budget, and suitable scorer before
interpreting quality; use the same evaluation configuration for both models and
trained checkpoints. Training checkpoints need Slime's supported HF export before
serving them for evaluation.

## Evidence and remaining limits

Komondor job `14650670` passed ten CPU tests: teacher HTTP scoring and alignment,
policy-age validation, configuration consistency, tokenizer rejection, and the
actual pinned loss helper's gradient against an enumerated reverse-KL reference.
The loss-helper test isolates the function from Megatron; it is not a distributed
training test. Checkpoint metadata preflight, Ruff, and shell syntax checks passed.
Follow-up job `14650690` passed eleven tests, including the actual Slime serving
configuration parser. See the [journal](experiments/LOG.md) for runtime qualification and later runs.
Actual model execution, end-to-end async behavior, two-node communication, and
learning-quality comparisons remain unvalidated.
