# Verifier context experiment

Status: high-level proposal. The first guidance text is agreed; the experiment
setup and agent runs await user validation.

## Goal

Determine whether additional Markdown about verification and research validation
improves agent results on this specific task, `autoresearch-feature-volume`.
Use this comparison to assess whether that extra context provides a useful
learning opportunity for OPCD.

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

## What to observe

Compare both the final outcome and the research process:

- Submission success: whether the agent produces an accepted model, including
  whether it passes the causal audit.
- Forecast quality: the official hidden weighted correlation for accepted
  models. Report rejected or missing submissions separately; their penalty is
  not a measured forecasting correlation.
- Research behavior: how the agent designs validation, compares experiments,
  interprets evidence, recovers from errors, and chooses its final model.
- Resource use: time, model usage, and cost under the same limits.

Keep full agent actions, tool responses, submitted code, and verifier outcomes
so that failure explanations can point to specific evidence. Distinguish agent
mistakes from infrastructure failures. Describe observed actions and stated
reasoning without assuming access to the model's internal reasoning.

## What this would tell us about OPCD

If condition B consistently improves outcomes, inspect which decisions changed
and whether those changes explain the improvement. This would support testing
whether an agent can learn the useful behavior without receiving the extra
Markdown at deployment.

For a later OPCD experiment, that Markdown could become teacher-only context,
while the student retains the baseline context. Keep it out of student inputs
and training payloads as required by the project scope. The teacher would score
student-generated continuations with the additional context; successful B
rollouts alone do not implement OPCD.

An improvement in this comparison would show that context helps, not prove
that it can be distilled. OpenAI API models can support the initial behavioral
comparison; suitability for the required teacher token scoring is a separate
validation. A null result is informative too: check for redundant guidance,
unclear guidance, or a task that is too easy or too difficult before concluding
that there is nothing to learn. This single task cannot establish general
quantitative research ability.

## Decisions before implementation and runs

1. Validate the baseline and how the agreed research guidance is supplied to
   condition B. Both conditions retain the existing task documentation.
2. Select a recent, affordable OpenAI model and fix the agent setup used in both
   conditions.
3. Agree a small pilot size, equal per-run limits, and a total spending cap.
4. Agree how much improvement and consistency would justify a larger comparison
   or an OPCD follow-up, including whether a gain in completion alone is enough.
5. Validate the proposal, then prepare the experiment. Launch paid trials only
   after the run settings and execution environment are ready.

Project implementation gaps and validation work remain in
[the OPCD TODO](../../docs/TODO.md); repository changes follow
[the development workflow](../../docs/WORKFLOW.md).
