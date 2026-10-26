# Policy distillation experiment design

Status: protocol proposal, 2026-10-26. The immediate study compares synchronous
and asynchronous policy distillation from a more capable frozen teacher to a
student. The resource target is eight GPUs across two Komondor nodes. The
[project decisions](../../../AGENTS.md#confirmed-decisions) establish this
preliminary stage; the longer-term OPCD requirements remain in force for OPCD.

## Scientific question

Under which workload and learning regimes does asynchronous execution improve
the resource cost or elapsed time required to achieve a given student quality,
and where does it impair learning or stability?

The working hypotheses are that overlap can reduce waiting, that policy drift
and delayed data may change learning, and that the balance depends on the
workload and training stage. These are hypotheses to test. Treat synchronous
execution as the reference and asynchronous execution as a family of specified
schedules, rather than pooling all asynchronous runs into one condition.

## Model and objective controls

Select accessible teacher and student checkpoints with compatible token
semantics. Establish a useful teacher advantage on development tasks rather
than inferring it from parameter count. Pin checkpoints, tokenizers, chat
templates, precision, and scoring conventions. Keep the teacher frozen and use
the same task inputs for both models in the proposed classical distillation
study; teacher-only context is reserved for subsequent OPCD work.

Specify whether training uses student-generated or teacher-generated responses,
the direction and approximation of the distillation loss, its normalization,
and any clipping, correction, masking, or additional reward. Keep these fixed
within a scheduling comparison. Different estimators or correction mechanisms
are separate interventions. Slime's [existing OPD example](../../../slime/examples/on_policy_distillation/README.md)
provides a candidate path, but its sampled-token penalty must not be described
as the OPCD student-top-256 objective. The objective for this preliminary study
is still to be selected; this proposal does not change the OPCD requirement.

## Confounders and separate measurements

For each comparison, classify candidate explanatory factors as controlled,
deliberately varied, or measured. Scheduling may itself change queue age,
sample selection, and policy drift; these can be mechanisms of its effect.
Measure them before designing interventions to isolate their contributions.

| Factor | Control or separate measurement |
| --- | --- |
| Initialization and training progress | Match starting model/optimizer state and learning schedule; report effects by training stage using definitions fixed before confirmatory runs. |
| Prompts and evaluation | Freeze dataset versions and disjoint development/test splits; match prompt sampling rules and evaluation settings. Detect overlap where practical. |
| Sampling and response length | Match decoding rules, response limits, truncation, and loss masks; measure actual length distributions and completion-based selection. Matching seeds does not guarantee identical responses under different schedules. |
| Distillation implementation | Match teacher, score alignment, objective, reductions, and numerical settings; verify the same recorded batch gives equivalent loss and gradients across paths. |
| Freshness and policy drift | Record generating, serving, and training policy versions, time in queues, and responses spanning versions. Measure sampled-token log-probability differences on aligned prefixes; do not label those differences an exact distribution KL. |
| Queueing and workload balance | Measure generation, scoring, training, and weight-publication time separately, together with queue occupancy, backpressure, and discarded or retried work. |
| Hardware and placement | Match GPU roles, allocated node types, containers, transport, and storage. Record actual GPU/NIC affinity and network path, allocation identity, and run order. Block or counterbalance comparisons across allocations when possible. |
| Optimization and safeguards | Match batch/sequence weighting, optimizer updates, clipping, corrections, and stopping rules. Report effective training tokens after masking and rejection. |

Use small targeted ablations when observed effects remain entangled. For
example, controlled scoring delay can test sensitivity to a scoring bottleneck,
and delayed consumption of version-tagged batches can probe lag. Such
interventions also change queueing and potentially selection; state their
limits and compare against natural execution. A fixed recorded-batch replay
checks numerical and transport behavior but cannot establish learning quality.

## Fair comparisons and analysis

Separate three outcomes: systems efficiency, learning efficiency, and
instability. Report student quality against both effective training tokens and
elapsed time, with total allocated GPU-hours alongside them. Include the
initial student and frozen teacher as evaluation references. Report startup,
evaluation, scoring, synchronization, discarded generation, and recovery costs;
define which costs enter each timing metric before measurement.

Use matched training exposure to investigate learning differences and matched
resource budgets to assess operational benefit. Token count, update count,
and wall time cannot generally all be matched at once; state which comparison
supports each claim. Define time-to-quality targets from development evidence
before confirmatory runs, and retain runs that never reach them as censored or
failed outcomes under a specified analysis rule.

Choose primary endpoints, practical effect sizes or quality margins, run
budgets, and the analysis plan before confirmatory runs. Use independent
training seeds as experimental repetitions; checkpoints, batches, and tokens
from one run are not independent repetitions. Pair seeds and counterbalance
run order where practical. Choose the number of repetitions using pilot
variability and budget, report uncertainty and individual-run outcomes, and
distinguish exploratory regime comparisons from confirmatory claims. Held-out
test outcomes must not drive tuning or repeated model selection.

## Stability and regimes

Characterize regimes through response lengths, relative stage costs, actual
policy drift, queue age, and training progress. A one-update lag can correspond
to different drift at different stages. Define regime boundaries from pilots
before confirmatory comparisons; avoid selecting only favorable intervals
after seeing results. Test a narrow useful range first and investigate
interactions where evidence motivates them, rather than starting with a large
factorial sweep.

Before each comparison, specify numerical-failure stops, sustained degradation
criteria on development evaluation, queue/resource limits, and rules for
rejecting stale or incomplete data. Distinguish numerical divergence, quality
regression, resource exhaustion, and infrastructure failure. Queue bounds do
not by themselves establish a bound on policy lag, and policy version age
does not establish a bound on drift. Audit what the implementation enforces.
Keep failures in the results, record any recovery, and apply stopping rules
consistently. Additional safeguards or asymmetric tuning belong in separately
identified comparisons, with their tuning costs reported.

## Preparation and execution

Follow [experiment guidance](../../EXPERIMENTS.md) and the
[hardware validation sequence](../../HARDWARE.md#proposed-validation-sequence).
First verify scoring/loss correctness, teacher immutability, supported async
hooks, and two-node runtime/placement. Existing sync/async support does not
establish that every required safeguard is implemented or that distillation
is validated on Komondor.

Use exploratory pilots to select the model pair, objective, workload,
allocations, telemetry, and confirmatory design. Freeze those settings before
the main comparison. The eight-GPU target is not a GPU-hour budget or a launch
instruction; runtime, storage, datasets, and per-run limits remain to be
resolved before execution. Record every launched attempt in the
[experiment journal](../LOG.md), preserving unsuccessful attempts and private
data boundaries. Track preparation work in the [project TODO](../../TODO.md#preliminary-policy-distillation-study).
