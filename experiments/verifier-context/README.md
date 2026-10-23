# Verifier context experiment

Status: high-level proposal. The first guidance text is agreed; the experiment
setup and agent runs await user validation.

## Goal

Determine whether additional Markdown guidelines improve the final hidden
weighted Pearson correlation on this specific task,
`autoresearch-feature-volume`. Compare the baseline with the selected guidance
under the same conditions.

The task uses the local `data/autoresearch-feature-volume` package:
agents research features, train an Elastic Net model to forecast next-minute
volume changes, and submit it for evaluation on hidden market data. The package
contains reference baselines, but no completed agent trial results.

## Proposed comparison

| Condition | What the agent receives |
| --- | --- |
| A: baseline | The existing task instructions, public data, tools, and existing task documentation. |
| B: additional research guidance | Everything in A, plus the [research guidance](research-guidance.md). |

The proposed baseline keeps the documentation already supplied with the task.
The comparison measures the value of additional guidance; it does not remove
the existing research or evaluation guides. Validate this interpretation before
preparing either condition.

Use the same model, agent execution loop, tools, data split, verifier, and
resource limits in both conditions. Start each rollout with a fresh environment
and conversation. Repeat both conditions so that one lucky or failed run does
not determine the conclusion.

The first treatment covers how to validate research findings. It adds research
advice to the existing task documentation, so any improvement would measure the
value of that advice. It would not isolate the benefit of explaining verifier
mechanics. Hidden labels and the reference solution remain outside both agents'
contexts. Freeze the Markdown before comparison runs; do not tune it against
hidden evaluation results.

## What to measure

The primary outcome is the final model's official hidden weighted Pearson
correlation (`weighted_pearson_ic`). Compare this metric across repeated runs
with and without the selected guidance.

Report rejected or missing submissions alongside the scores for accepted
models, so failed runs remain visible. Their penalty is not a measured
forecasting correlation. Keep the submitted models and verifier outcomes so
that reported results can be checked.

The current experiment asks whether the guidelines improve the final metric.
Detailed analysis of the agents' research process is potential future work.

## Potential future work

If the guidelines improve the final metric, future work could inspect which
agent decisions changed and whether those changes explain the improvement.
It could also test whether an agent can learn the useful behavior through OPCD
without receiving the extra Markdown at deployment.

These follow-ups are outside the current experiment. Any later OPCD work must
follow the teacher-only context separation required by the project scope.
A score improvement here would not by itself establish that the behavior can
be distilled or that the guidelines help on other tasks.

## Decisions before implementation and runs

1. Validate the baseline and how the agreed research guidance is supplied to
   condition B. Both conditions retain the existing task documentation.
2. Select a recent, affordable OpenAI model and fix the agent setup used in both
   conditions.
3. Agree a small pilot size, equal per-run limits, and a total spending cap.
4. Agree how to summarize the final metric across repeated runs and report
   failed submissions.
5. Validate the proposal, then prepare the experiment. Launch paid trials only
   after the run settings and execution environment are ready.

Project implementation gaps and validation work remain in
[the OPCD TODO](../../docs/TODO.md); repository changes follow
[the development workflow](../../docs/WORKFLOW.md).
