# Policy distillation validation

## What we want to establish

Does our implementation work, and do its shortcuts preserve distillation
quality within an acceptable loss?

We focus on classical policy distillation from a more capable frozen
teacher to a student in Slime. Quality and technical validity come first;
speed and cost are secondary. Scope and rationale are recorded in
[AGENTS.md](../../../AGENTS.md#confirmed-decisions).

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
training problems. The benchmark and evaluation protocol are not yet fixed.

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

## Current context

Eight GPUs across two Komondor nodes is the provisional initial validation
setup; resources and topology can evolve. Multi-node execution and the complete
distillation path still need validation under the [hardware constraints](../../HARDWARE.md).

The [initial model pair](../../EXPERIMENTS.md#initial-policy-distillation-pair)
is selected, with tokenizer metadata compatibility verified and baseline quality
still to establish. The [implementation](../../DISTILLATION.md) supplies the selected
sampled-token objective and matched sync/async configuration. Dataset and acceptable
quality loss remain open. The first training validation is bounded at 30 minutes
on eight GPUs after runtime checks and both models' baseline evaluations; this
does not set the budget for later studies.
Slime's existing paths and the adapter CPU checks do not establish learning quality.

Use the [experiment guidance](../../EXPERIMENTS.md), [run records](../LOG.md),
and [current work](../../TODO.md#policy-distillation-validation) to
continue from here. Detailed methods should follow concrete experimental
choices and findings.
