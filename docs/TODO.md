# Project TODO

Current context, 2026-10-28: the immediate focus is classical policy distillation
from a more capable frozen teacher. We want to establish that the implementation
works and that its shortcuts do not cause unacceptable quality loss. Slime
already supports synchronous and asynchronous execution; their availability
alone does not establish distillation correctness or stability on Komondor.

[AGENTS.md](../AGENTS.md) holds the project scope and decisions. This handoff
tracks outstanding outcomes; detailed evidence belongs in the linked records.

## Policy distillation validation

This remains exploratory work; learning benefit, acceptable shortcut loss and
broader correctness remain open.

The 1.5B-student / 7B-teacher MATH A/B/C pilot completed ten updates per
condition, model-only saving, HF export and matched checkpoint evaluation.
The original student scored 24/32; A/B each 20/32; C 24/32. C exercised mixed
versions in 38/80 accepted responses. Async lag stayed within one after stale
groups were discarded. Training truncation was 67-68/80 responses, and only
80 accepted responses were optimized per condition. Execution works on this
path; useful learning and acceptable quality loss remain unestablished.
See the [consolidated report](experiments/policy-distillation/reports/math-pilot-20261028/REPORT.md).
Training/evaluation metrics are synced to W&B. Before longer runs, calibrate
response budgets on development data and agree on quality-loss criteria.
Automatic monitoring was cancelled by the user; do not restart it implicitly.

Continue separate A/B/C experiments from recorded outcomes, retaining the strict
lag bound, discarded-work reporting, model-only saves and verified tracking.
The stale-group filter is implemented; its longer-run behavior still needs
experimental evidence. Baselines and training can proceed independently once
their own prerequisites hold, under the [dependency rule](EXPERIMENTS.md#run-independent-work-concurrently).
Matched baselines are needed before interpreting quality.

[Komondor](HARDWARE.md#access-boundary) is the execution target. Euler support is
retired under the [scope decision](../AGENTS.md#confirmed-decisions); its earlier
attempts remain [historical](experiments/policy-distillation/EULER.md). Missing
pinned Slime/Megatron interfaces still limit static implementation review. Keep
those evidence gaps distinct from observed runtime failures and quality results.
Do not infer authorization for a sustained run from smoke success.

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
experimental needs. The [compaction rollout](WORKFLOW.md#context-compaction-rollout)
records deployment evidence and pending live verification of adaptive summary allowances.
Proposed dependency contracts are supplied as data while executable reviewer code
stays on the accepted pin.

Keep implementation checks proportionate to the change, and distinguish CPU
checks, reviewer results, and measured GPU training evidence. Launched runs and
outcomes belong in the [experiment journal](experiments/LOG.md).
