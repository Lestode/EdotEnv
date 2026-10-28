# Project TODO

Current context, 2026-10-26: the immediate focus is classical policy distillation
from a more capable frozen teacher. We want to establish that the implementation
works and that its shortcuts do not cause unacceptable quality loss. Slime
already supports synchronous and asynchronous execution; their availability
alone does not establish distillation correctness or stability on Komondor.

[AGENTS.md](../AGENTS.md) holds the project scope and decisions. This handoff
tracks outstanding outcomes; detailed evidence belongs in the linked records.

## Policy distillation validation

The user now authorizes a larger 7B-student/32B-teacher throughput and learning
pilot with lightweight stage/queue/GPU measurements and checkpoint evaluation.
See the [pilot protocol](experiments/policy-distillation/THROUGHPUT.md).
Teacher baseline is complete: 29/32 correct versus the original student's
27/32 on the matched development set. Initial larger-model A/B/C attempts
failed before training because a reused model symlink escaped the container
mounts; all three passed the 12-rank collective. The corrected mounts passed
real-container model access and 20 CPU tests in job `14689413`.
Fresh retries A `14689447`, B `14689448`, C `14689449` each request 12 GPUs
on three nodes, with a 30-minute cap. They may run concurrently under the
user's revised concurrency decision. Per-node model access is now checked
before startup. Larger-model training and checkpoint evaluations remain
unvalidated; deliver the requested Markdown/PDF report before longer runs.
See the [journal](experiments/LOG.md) for retained failures and source provenance.

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
validation. The two-node CPU Ray check passed. A reached rollout processing but
failed because Slime metrics expected a scalar reward, not the teacher-score
dictionary. B/C were cancelled to avoid repeating the shared defect. The reward-key correction passed all 17 CPU regressions (`14673025`).
Corrected A/B/C retries `14673098`, `14673099`, `14673100` are submitted
concurrently with separate outputs and eight-GPU/30-minute caps. A completed three training updates and saved its checkpoint with zero reported lag and mixed versions. B also completed three updates, with logged draining, lag at most one and no mixed responses. Non-exclusive C-a3 `14673436` also completed three updates, but zero mixed-version responses means its mid-response shortcut remains unexercised. All three saved checkpoints; post-training quality evaluation and a representative workload remain outstanding. The smoke monitor is stopped now that all outcomes are known. B's draining worker adapter and single-version
enforcement passed CPU regressions in CI; full runtime integration remains
unvalidated. The user switched validation back to Komondor on 27 October;
[existing-session reuse](KOMONDOR.md) restored access without a fresh eduID prompt.
Reuse the staged Komondor runtime/models and validate the actual account and
project allocation before resuming. The Euler follow-up was deleted; cancellation
of its last preparation job was attempted but not confirmed because SSH timed out.
Earlier Euler attempts remain in the [Euler report](experiments/policy-distillation/EULER.md).
Keep checkpoints and reports separate;
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
