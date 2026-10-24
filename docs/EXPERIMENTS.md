# Experiment guidance

## Validate before scaling

Before expensive or distributed experiments, run a small number of inexpensive,
targeted checks that establish meaningful correctness along the intended
execution path. Keep validation proportional to uncertainty and cost, reuse
applicable evidence, and avoid redundant checks. Investigate unexpected results
before scaling. When unsure whether further validation or a larger run is
warranted, ask the user.

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
