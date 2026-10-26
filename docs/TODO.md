# Project TODO

Current context, 2026-10-26: the immediate focus is classical policy distillation
from a more capable frozen teacher. We want to establish that the implementation
works and that its shortcuts do not cause unacceptable quality loss. Slime
already supports synchronous and asynchronous execution; their availability
alone does not establish distillation correctness or stability on Komondor.

[AGENTS.md](../AGENTS.md) holds the project scope and decisions. This handoff
tracks outstanding outcomes; detailed evidence belongs in the linked records.

## Policy distillation validation

The [experiment design](experiments/policy-distillation/README.md) frames the
initial technical validation, with a provisional resource setup. Quality loss
relative to a trustworthy reference is the primary concern; speed and cost are
secondary. Distinguish shortcuts and confounders so that a failure can be
attributed to its cause, including differences between learning regimes.

The [initial model pair](EXPERIMENTS.md#initial-policy-distillation-pair) is
selected; tokenizer compatibility and both models' baseline quality still need
validation before training. The distillation objective, task, and acceptable
quality loss remain open. The study should establish
that distillation improves the student and whether the shortcuts preserve that
benefit. Async stability and the actual two-node runtime remain unvalidated.

## Markdown guidance final-score comparison

The [comparison record](../experiments/verifier-context/README.md) preserves
completed pilots, unsuccessful attempts, and evidence locations. The stopped
Astra study's archive was downloaded and checksum-verified, and its cloud
resources were verified deleted. Its results, disclosure issue, and server/DNS
failures still need interpretation before a follow-up. No new run is implied.

## Repository workflow validation

The [development workflow](WORKFLOW.md) owns review policy, activation evidence,
and merge requirements. Remaining confidence gaps concern fresh reviews after
changes, stale or missing review blocking, duplicate-request behavior, and
normal protected merges under the applicable policy. Verify behavior through
supported interfaces; do not weaken protection or substitute synthetic checks.

Keep implementation checks proportionate to the change, and distinguish CPU
checks, reviewer results, and measured GPU training evidence. Launched runs and
outcomes belong in the [experiment journal](experiments/LOG.md).
