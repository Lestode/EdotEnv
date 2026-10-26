# Experiment guidance

## Initial policy distillation pair

- Frozen teacher: `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`.
- Trainable student: `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`.

This is our initial pair. Exact tokenizer metadata compatibility passed on
Komondor for the [pinned revisions](../configs/distillation/models.json).
Both frozen-model development baselines completed before any training updates;
see the [results and limits](experiments/LOG.md). Preserve that prerequisite for
new model/task pairs, including execution checks that update weights. Teacher
token alignment must pass before a generated batch is used for training.

## Validate before scaling

Before expensive or distributed experiments, run a small number of inexpensive,
targeted checks that establish meaningful correctness along the intended
execution path. Keep validation proportional to uncertainty and cost, reuse
applicable evidence, and avoid redundant checks. Investigate unexpected results
before scaling. When unsure whether further validation or a larger run is
warranted, ask the user.

## Control confounders and distinguish regimes

Make comparisons informative: account for important confounders, measure
potentially distinct effects separately where useful, and investigate
interactions when they matter. A result in one workload or learning regime
need not generalize to another.

Agree on what would count as success before judging results. Keep exploration
distinct from validation, use credible comparisons and uncertainty, and retain
failures. Document the reasoning and consequential choices; add methodological
detail when a concrete experiment needs it.

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
