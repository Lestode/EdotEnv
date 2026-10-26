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

The [implementation](DISTILLATION.md) now supplies a sampled-token distillation
baseline, matched sync/async launch settings, frozen teacher serving, and strict
score/policy-age checks. Tokenizer metadata, CPU regression checks, and a separate
eight-GPU/two-node site collective passed on Komondor; these do not establish
Slime training correctness. Runtime qualification is recorded in the [journal](experiments/LOG.md).

Both frozen models completed the fixed development baseline; results and
truncation limits are in the [journal](experiments/LOG.md). The final study task
and acceptable quality loss remain open.
The study must establish that distillation improves the student and whether the
shortcuts preserve that benefit. Async stability and actual distributed Slime
training still need evidence.

The user has authorized separate execution checks for
[A, B and C](experiments/policy-distillation/README.md#concrete-comparisons), followed
by separate measurements. The previous checkpoint hold is lifted for this bounded
validation. Ray startup remains the shared blocker; diagnose it on allocated CPUs
before another GPU attempt. B now has a proposed draining worker adapter and
single-version enforcement, pending tests. Keep checkpoints and reports separate;
do not start a sustained learning run merely because smoke checks pass.

## Markdown guidance final-score comparison

The [comparison record](../experiments/verifier-context/README.md) preserves
completed pilots, unsuccessful attempts, and evidence locations. The stopped
Astra study's archive was downloaded and checksum-verified, and its cloud
resources were verified deleted. Its results, disclosure issue, and server/DNS
failures still need interpretation before a follow-up. No new run is implied.

## Repository workflow validation

The [development workflow](WORKFLOW.md) owns review policy, activation evidence,
and merge requirements. The restored latest-head policy passed its first normal
protected merge in PR #12; broader failure-injection validation remains deferred.
Use supported interfaces and keep further workflow work proportionate to
experimental needs.

Keep implementation checks proportionate to the change, and distinguish CPU
checks, reviewer results, and measured GPU training evidence. Launched runs and
outcomes belong in the [experiment journal](experiments/LOG.md).
