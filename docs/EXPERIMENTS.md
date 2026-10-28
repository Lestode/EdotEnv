# Experiment guidance

## Initial policy distillation pair

- Frozen teacher: `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`.
- Trainable student: `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`.

This is our initial pair. Exact tokenizer metadata compatibility passed on
Komondor for the [pinned revisions](../configs/distillation/models.json).
Both frozen-model development baselines completed before any training updates;
see the [results and limits](experiments/LOG.md). Baseline completion is not a
prerequisite for training. Teacher token alignment must pass before a generated
batch is used for training.

## Run independent work concurrently

Run independent baseline evaluations and training experiments concurrently within
the authorized resource budget. Wait only for genuine correctness or data
dependencies. Evaluate baselines from immutable original checkpoints; complete
and inspect the matched baselines before drawing learning-quality conclusions.
This replaces the baseline-before-training requirement by user decision on
27 October 2026.

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

The policy-distillation design records the
[candidate execution and weight-update policies](experiments/policy-distillation/README.md#candidate-execution-policies)
and the proposed first comparison.

## Log ML experiments in W&B

Log every ML experiment in Weights & Biases, including smoke tests and failed
attempts. Use a separate run for each condition and attempt. Record the model,
data and code revisions, configuration, resource allocation, available training
and evaluation metrics, and final outcome. Keep local evidence as well.

Set up tracking before launch and verify that metrics actually reach the intended
project. Prefer live logging; when cluster connectivity prevents it, use a
periodic relay or offline logging followed by sync, and make any delay visible.
Do not silently leave tracking disabled. Keep credentials and sensitive content
out of uploaded artifacts and the public repository. See the
[distillation tracking setup](experiments/policy-distillation/TRACKING.md).

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

## Share results and check in

Every experiment must have a concise, shareable report in its experiment
directory. Start with the question and current status; update it at meaningful
milestones with the setup, results, limitations, resources spent and next decision.
Write for a reader without the chat history. Link to detailed evidence instead
of reproducing logs or a long implementation plan. Provide a portable document
when requested; keep it consistent with the report in the repository.

Give the user a substantive checkpoint when repeated failures prolong debugging
or the time, cost or scope grows beyond the last agreed step. Pause further run
submissions for that checkpoint rather than continuing for hours through status
messages alone. Separate engineering validation from evidence of learning quality.
