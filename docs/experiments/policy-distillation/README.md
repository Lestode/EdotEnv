# Policy distillation validation

## What we want to establish

Does our implementation work, and do its shortcuts preserve distillation
quality within an acceptable loss?

We focus on classical policy distillation from a more capable frozen
teacher to a student in Slime. Quality and technical validity come first;
speed and cost are secondary. Scope and rationale are recorded in
[AGENTS.md](../../../AGENTS.md#confirmed-decisions).

For now, retain existing logs and coarse elapsed-time measurements. Defer detailed
profiling and continuous monitoring until their performance impact is understood;
one-time startup topology snapshots can remain outside the measured training work.

## Proposed evaluation approach

Establish implementation correctness during development, before sustained
training. Compare teacher scores, the sampled-token loss, and student gradients
on fixed examples against an independent reference. Begin with inexpensive CPU
checks on allocated compute, then validate the actual model pair and backends during the first GPU
run. Establish agreement through the distributed path before comparing training
quality; distinguish numerical discrepancies from intentional async staleness.
Baseline task evaluations can proceed independently.

Measure the original student and frozen teacher on the same held-out tasks and
evaluation settings. [MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500)
is the proposed primary candidate, subject to a baseline check for useful teacher
advantage and manageable evaluation cost.
Keep development and final evaluation separate, and check for overlap with
training problems. A [fixed development pilot](../../../configs/distillation/baseline-pilot.json)
selects 32 problems before model evaluation, with a common 8192-token greedy
budget; the other 468 are reserved. This checks initial quality, truncation and
evaluation cost. The final study protocol and acceptable quality loss remain open.

Establish a validated synchronous reference that improves the student's held-out
answer accuracy. Then assess whether shortcuts, including async execution,
preserve that improvement. Compare at comparable training work, accounting for
updates and generated tokens; evaluate speed and cost separately. Distinguish
changes that could explain a quality difference, including workload, response
length, and learning stage, without prescribing an exhaustive test matrix.

Use average single-response correctness as the proposed primary quality metric,
with generation failures, answer-format failures, and truncation reported
alongside it. Fix a common generation and scoring protocol before comparison;
the reasoning budget must allow a meaningful assessment of these models.
Teacher disagreement and training diagnostics help explain results but do not
replace task accuracy or the independent correctness checks.

Agree on acceptable quality loss relative to the learning reference before
judging shortcuts. Size evaluations and repeated runs to distinguish that loss
from sampling and training variation; preserve inconclusive and failed results.
A successful short execution check establishes readiness for a learning study,
not that learning or quality preservation has already been demonstrated.

## Candidate execution policies

“Asynchronous” covers two separate choices: how far rollout generation runs
ahead of training, and when the serving student adopts new weights. The teacher
stays frozen throughout. These are candidate comparisons, not a commitment to
test every combination.

Support below means present in our pinned Slime revision `18868a79b0b08`,
not validated end to end on Komondor. It distinguishes Slime's built-in mechanisms
from our adapter and additional work needed for a particular experimental policy.

### Concrete comparisons

**Selected for execution validation: A, B and C, as separate experiments.**
Start with bounded smoke checks, then measure learning quality separately once
execution works. D–E remain deferred. None has produced training results;
the frozen-model baselines have completed. See the [checkpoint report](REPORT.md).

| Condition | Execution and permitted lag | Weights within one response | Question / comparison | Support and current status |
| --- | --- | --- | --- | --- |
| **A · Synchronous reference** | Collect → train → publish; no policy lag. Generation and scoring may run concurrently within collection. | One version throughout. | Does the reference implementation improve student quality? | Built-in Slime path. Smoke attempts stopped at startup, before training. |
| **B · Train while finishing answers** | Train on one batch while a separate student copy generates and the teacher scores upcoming answers. Those answers may come from the previous published student version. | Let unfinished answers finish before updating the generating copy. Never switch weights halfway through an answer. | **B vs A:** does training on answers from a slightly older student still work as well? | Uses Slime plus our “finish before updating” adapter. CPU checks passed; actual training remains untested. |
| **C · Mid-response update, rebuilt cache** | Same bounded-overlap and lag settings as B. | Pause, update, rebuild the prefix's KV cache, then continue; tokens can span versions. | **C vs B:** what changes when unfinished responses can switch policy? | Slime's built-in abort/flush/requeue path for flat responses. Selected; not run. |
| **D · Mid-response update, retained cache** | Same bounded-overlap and lag settings as C. | Pause, update, continue using KV state computed with older weights. | **D vs C:** is retaining old cache an acceptable additional shortcut? | Slime option, requiring compatible SGLang and separate serving/training GPUs. Not selected by our launcher; deferred. |
| **E · More work ahead** | Increase the queue capacity and permitted lag relative to B; values remain to be chosen. | Keep one version per response, as in B. | **E vs B:** is a more aggressive overlap regime still acceptable? | Slime has configurable prefetch; our launcher fixes its factor to 1. Needs configuration changes and B's response-boundary work; deferred. |

These comparisons assess the practical policy changes together with their
effects on queueing and sample selection. They do not isolate every causal
mechanism; separate factors only if a result warrants it. E deliberately changes
both queue capacity and allowed lag, so it cannot attribute a difference to either
alone.

**Asynchronous optimizer updates remain outside scope:** all conditions retain
coordinated training updates. The inspected Slime loop awaits its `async_train`
RPC each round; that name does not mean independently updating training workers.

Slime exposes queue capacity through `--fully-async-group-prefetch-factor` and
cache behavior through `--flush-cache-interval`: `1` aborts and flushes at every
publication; `0` retains cache after the initial publication; larger positive
values alternate retention with periodic flushing. Our `--max-policy-lag` checks
consumed samples and aborts on excessive lag; it does not prevent stale work from
being produced.

Source anchors: Slime's [training loop](../../../slime/train.py),
[async producer](../../../slime/slime/rollout/fully_async_rollout.py),
[publication pause](../../../slime/slime/ray/rollout.py),
[configuration](../../../slime/slime/utils/arguments.py), and
[weight-update transport](../../../slime/slime/backends/megatron_utils/update_weight/update_weight_from_distributed.py);
our [adapter](../../../distillation/hooks.py) and [launcher](../../../distillation/launch.py).

Updates to serving weights must happen at a safe inference boundary. Training a
separate student copy while generation continues does not itself change the
weights serving an unfinished response.

### Separate execution checks and measurements

Each condition has its own manifest, output directory, checkpoint and report:
[A](A/REPORT.md), [B](B/REPORT.md), and [C](C/REPORT.md). Start each from the same
original student checkpoint with matched prompts, seed, objective and training
budget. Do not train B from A's output or pool attempts across conditions.

The initial smoke check targets three updates and a saved checkpoint, with finite
scores, loss and gradients, and valid policy versions. A/B must reject mixed-version
responses; C records their count. A C run with none has not exercised mid-response
updates. Existing coarse timings and version counts suffice initially; no detailed
profiling is added. Smoke success is execution evidence, not learning quality.

All three use serving concurrency 2 per engine and prefetch factor 1 for this
validation, reduced from the earlier startup attempts to limit queued work under
the one-publication lag bound. Queue capacity is not itself a freshness guarantee:
the adapter still fails on excessive lag. B's drain operation and strict
single-version check need runtime validation; rebuilding the cache in C does not
remove its mixed-version token history.

## Current context

Eight GPUs across two Komondor nodes is the provisional initial validation
setup; resources and topology can evolve. Multi-node execution and the complete
distillation path still need validation under the [hardware constraints](../../HARDWARE.md).

The [initial model pair](../../EXPERIMENTS.md#initial-policy-distillation-pair)
is selected, with tokenizer metadata compatibility verified and both development
baselines completed; see the [results and limits](../LOG.md). The [implementation](../../DISTILLATION.md) supplies the selected
sampled-token objective and matched sync/async configuration. Dataset and acceptable
quality loss remain open. The first training validation is bounded at 30 minutes
on eight GPUs after runtime checks and both models' baseline evaluations; this
does not set the budget for later studies.
Slime's existing paths and the adapter CPU checks do not establish learning quality.

Use the [experiment guidance](../../EXPERIMENTS.md), [run records](../LOG.md),
and [current work](../../TODO.md#policy-distillation-validation) to
continue from here. Detailed methods should follow concrete experimental
choices and findings.
