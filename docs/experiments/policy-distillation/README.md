# Policy distillation validation

## What we want to establish

Does our implementation work, and do its shortcuts preserve distillation
quality within an acceptable loss?

For now, we focus on classical policy distillation from a more capable frozen
teacher to a student in Slime. Quality and technical validity come first;
speed and cost are secondary. The longer-term OPCD goal remains in
[AGENTS.md](../../../AGENTS.md#confirmed-decisions).

## How we should reason about it

Compare against a trustworthy reference that demonstrably learns. Check both
whether distillation improves the student and whether our shortcuts preserve
that benefit. Agreement between two implementations is not enough if they
share the same problematic shortcut.

Account for confounders and measure potentially distinct effects separately
where useful, so we can understand why quality changes. Keep this proportionate
to the actual experiment rather than prescribing an exhaustive test matrix.

Sync versus async is one comparison. We are particularly concerned that async
can become unstable, and that its behavior may differ across workloads and
learning stages. Avoid drawing a universal conclusion from one regime.

Agree on acceptable quality loss before judging the comparison, and gather
enough evidence to distinguish it from noise. Preserve failures and remaining
uncertainty as well as successful results.

## Current context

Eight GPUs across two Komondor nodes is the provisional initial validation
setup; resources and topology can evolve. Multi-node execution and the complete
distillation path still need validation under the [hardware constraints](../../HARDWARE.md).

The model pair, distillation objective, dataset, acceptable quality loss, and
run budgets remain open. Slime already has sync/async and OPD paths; that does
not establish their correctness for this study or the later OPCD objective.

Use the [experiment guidance](../../EXPERIMENTS.md), [run records](../LOG.md),
and [current work](../../TODO.md#preliminary-policy-distillation-study) to
continue from here. Detailed methods should follow concrete experimental
choices and findings.
