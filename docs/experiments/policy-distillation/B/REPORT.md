# B · Bounded overlap with complete responses

Status, 26 October 2026: selected; CPU adapter regressions passed, but runtime
integration remains unvalidated. No B training attempt has run.

Generate and score while training, with at most one publication of lag. Before
publishing new weights, drain active work; reject any response spanning policy
versions. A custom rollout hook registers a subclass of Slime's worker,
without modifying Slime's source. Draining may reduce overlap and adds waiting time.

Use `MODE=bounded_async` and a fresh original student checkpoint. Follow the
[common protocol](../README.md#separate-execution-checks-and-measurements); retain
separate condition-B manifests and outputs. Check drain completion, version
counts and actual execution before comparing quality or elapsed time with A.

The [CI run on implementation revision `4ef52cb`](https://github.com/Lestode/EdotEnv/actions/runs/40343047802)
passed all 49 project Python tests, including 17 distillation tests. New checks
exercise the pinned worker's pause and dispatch methods, repeated rounds, and
mixed-version rejection. They isolate these contracts from GPU imports and do
not establish complete runtime behavior.

No B training results or GPU use yet. Fresh cluster authentication and the shared
startup check are pending. Learning quality remains unmeasured.
