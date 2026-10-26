# B · Bounded overlap with complete responses

Status, 26 October 2026: selected; the project adapter is prepared but not yet
validated. No B training attempt has run.

Generate and score while training, with at most one publication of lag. Before
publishing new weights, drain active work; reject any response spanning policy
versions. A custom rollout hook registers a subclass of Slime's worker,
without modifying Slime's source. Draining may reduce overlap and adds waiting time.

Use `MODE=bounded_async` and a fresh original student checkpoint. Follow the
[common protocol](../README.md#separate-execution-checks-and-measurements); retain
separate condition-B manifests and outputs. Check drain completion, version
counts and actual execution before comparing quality or elapsed time with A.

No results or resource use yet. CPU regression and cluster startup checks precede
the bounded training smoke. Learning quality remains unmeasured.
