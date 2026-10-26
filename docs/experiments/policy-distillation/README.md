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

### Scheduling

| Strategy | What happens | Slime support | Proposed scope |
| --- | --- | --- | --- |
| Round-synchronous | Collect a batch, train on it, publish weights, then collect the next batch. Generation and scoring can still run concurrently within a round. | Built-in default rollout and training loop. | Learning reference. |
| Bounded pipeline overlap | Generate and score future responses while training the current batch; allow at most one publication of policy lag. | Built-in async producer and bounded queues. Our adapter adds the strict lag check; the queue bound alone is insufficient. | First async comparison. |
| Deeper asynchronous queue | Let more work run ahead, allowing greater policy lag. | Built-in configurable prefetch pool; our launcher currently fixes its factor to 1. Queue depth and permitted lag need separate configuration. | Possible later comparison. |
| Asynchronous optimizer updates | Training workers apply updates without the usual coordination. | Not provided by the inspected training path; its `async_train` RPC is awaited each round. | Outside this experiment. |

### Updating the serving student during a response

| Weight-update policy | What a response uses | Slime support | What it lets us test |
| --- | --- | --- | --- |
| Finish with original weights | One student version for the entire response; publish at a suitable boundary or retain the original serving snapshot. | Available for completed responses in the default synchronous path. Async workers have a drain primitive, but the publication path uses a non-draining pause; enforcing this during overlap needs integration and validation. | Pipeline overlap and stale responses without changing weights mid-response. |
| Pause, update, rebuild cache, continue | Earlier tokens come from the old version; later tokens use new weights after rebuilding the prefix's KV cache. | Built-in async abort/flush/requeue path for flat token responses, with the default cache-flush setting. | The additional effect of mixing policy versions within a response. |
| Pause, update, retain cache, continue | New weights continue from KV state computed with older weights. | Built-in in-place pause and cache-retention option; requires compatible SGLang and separate training/serving GPUs. Not selected by our launcher. | An additional cache-reuse shortcut; defer initially. |

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
separate student copy while generation continues is compatible with all three
policies; it does not itself change the weights serving an unfinished response.

The proposed starting comparison is **round-synchronous versus bounded overlap,
with one student version per response in both**. First ask whether student quality
is preserved; investigate individual mechanisms only if results warrant it.

**Implementation gap:** the current one-publication lag check does not enforce
one version per response. The pinned async path can retain interrupted partial
responses and resume them after a weight update. That boundary must be enforced
and validated before treating the proposed first comparison as implemented.
Rebuilding the cache alone does not remove the mixed-version token history.

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
