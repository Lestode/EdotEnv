# Experiment guidance

## Validate before scaling

Before expensive or distributed experiments, run a small number of inexpensive,
targeted checks that establish meaningful correctness along the intended
execution path. Keep validation proportional to uncertainty and cost, reuse
applicable evidence, and avoid redundant checks. Investigate unexpected results
before scaling. When unsure whether further validation or a larger run is
warranted, ask the user.

## Control confounders and distinguish regimes

Define the scientific question and intended comparison before choosing a run
matrix. Identify factors that could explain the outcome, including differences
introduced by scheduling, sampling, resource placement, and training progress.
Specify which factors are controlled, varied, or measured. Measure potentially
distinct mechanisms separately where practical; use targeted ablations when
several factors change together. Record residual confounding and interactions
rather than attributing every difference to the named treatment.

Compare learning quality, stability, elapsed time, and resource use under
explicit budgets. Separate exploratory pilots and tuning from confirmatory
comparisons, define outcomes and stopping rules in advance, and retain failures.
Support conclusions with independent repetitions and uncertainty appropriate to
the experimental unit. Limit conclusions to the workloads and training regimes
actually tested. Study-specific controls belong in the experiment protocol.

## Maintain experiment continuity

Read recent experiment records before planning further runs. Create a journal
entry when launching an experiment and update it when the run completes, fails,
or is cancelled. Record the outcome, limitations, resource use, and durable
evidence locations. Preserve unsuccessful attempts and distinguish measured
results from interpretations. Keep sensitive inputs and outputs in approved
private storage.

Use the [experiment journal](experiments/LOG.md) for concise run entries, newest
first. Link to saved configurations and detailed results rather than copying
them into the journal. Mark unavailable measurements as unknown.
