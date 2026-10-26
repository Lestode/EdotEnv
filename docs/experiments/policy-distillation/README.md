# Policy distillation experiment design

Status: protocol proposal, 2026-10-26. The immediate study concerns classical
policy distillation from a more capable frozen teacher to a student using
Slime. The initial validation setup is eight GPUs across two Komondor nodes.
This is provisional: resource sizing and topology may change as validation
and workload evidence develops. Record the actual setup for each comparison.
The longer-term OPCD scope stays in
[the project decisions](../../../AGENTS.md#confirmed-decisions).

## Main question

Does our implementation work, and do the shortcuts we take preserve
distillation quality within an acceptable loss?

Technical validity and retained student quality are the primary concerns.
Speed and resource cost are secondary measurements. A faster run is useful
only after we understand whether it learns correctly and how much quality its
shortcuts sacrifice. Synchronous versus asynchronous execution is one part of
this question, rather than the whole scientific objective.

## Reference and meaning of success

Establish a trustworthy reference for the chosen distillation method, with its
assumptions and approximations made explicit. Synchronous execution can serve
as the scheduling reference, but is not automatically a correctness reference
for other shortcuts. A shortcut shared by both paths needs separate validation.

Evaluate the initial student and frozen teacher as references. The teacher
should demonstrate a useful advantage on development tasks; model size alone
does not establish that advantage. Ask both whether distillation improves the
student and whether each shortcut retains the benefit achieved by the reference.

Before confirmatory comparisons, define the task, objective, primary quality
measure, acceptable degradation, and training exposure. Set tolerances using
the intended use and development evidence, not the observed test result.
Use a meaningful reference that has had enough training to learn; a weak or
undertrained reference cannot establish that a shortcut preserves quality.

## Shortcuts and attribution

Inventory the shortcuts actually used and the assumptions each changes.
Candidates to investigate, if present, include stale rollouts, responses
continued across policy versions, approximate probability support or losses,
cached scores, and numerical or transport optimizations. Distinguish existing
mechanisms from proposed ones and check what the implementation enforces.

Compare against the appropriate reference and isolate effects where practical.
Numerical agreement on recorded inputs can support a correctness claim;
learning quality still needs training and held-out evaluation. If several
shortcuts change together, use targeted ablations before attributing quality
loss to one mechanism. Check consequential interactions where single-factor
comparisons cannot explain the combined behavior.

The [existing Slime OPD example](../../../slime/examples/on_policy_distillation/README.md)
is a candidate implementation path. Its sampled-token penalty is not the OPCD
student-top-256 objective. The preliminary study's objective remains to be
selected; this does not change the longer-term OPCD requirement. The proposed
classical comparison gives teacher and student the same task inputs.

## Confounders and regimes

State which factors are controlled, varied, or measured. Relevant factors
include model and optimizer initialization, data and prompt selection,
decoding and response length, training exposure, objective normalization,
corrections or masking, precision, hardware placement, and run order.

Measure policy drift and freshness, queueing and stage costs, discarded work,
and failure behavior separately where they could explain a quality change.
Some are consequences of async rather than independent confounders; retain
that distinction when interpreting the overall effect. A queue bound or a
policy-version limit does not by itself establish small policy drift.

Treat workload and learning regimes as possible limits on the result. A
shortcut may behave differently during rapid policy change, with longer
responses, or when teacher scoring becomes the bottleneck. Investigate the
regimes supported by evidence without prescribing a broad parameter sweep or
pooling distinct behaviors into one sync/async result.

## Evidence and interpretation

Separate exploratory development from confirmatory evaluation. Choose
outcomes, quality margins, budgets, and failure/stopping rules before the main
comparison. Keep test data separate from tuning. Use independent training
repetitions and report uncertainty in quality differences; batches and
checkpoints from one run are not independent repetitions. A failure to detect
a difference is not sufficient evidence that quality loss is acceptable.

Match training exposure to study quality retention, and report allocated
GPU-hours and elapsed time alongside it. Resource-matched comparisons answer
a different operational question and should be identified as such. Retain
failed runs, discarded work, and recovery costs. Distinguish numerical
failure, quality regression, resource exhaustion, and infrastructure failure.
Limit conclusions to the shortcuts, workloads, and regimes actually tested.

## Current context

Models, objective, datasets, acceptable quality loss, and run budgets remain
open. Runtime, storage, placement, and two-node communication need validation
under the [hardware constraints](../../HARDWARE.md). Existing sync/async
support does not establish that the complete distillation path works there.

Follow [experiment guidance](../../EXPERIMENTS.md), preserve evidence and
unsuccessful attempts in the [experiment journal](../LOG.md), and use the
[project TODO](../../TODO.md#preliminary-policy-distillation-study) for a concise
handoff of outstanding work. This design does not launch a cluster run.
