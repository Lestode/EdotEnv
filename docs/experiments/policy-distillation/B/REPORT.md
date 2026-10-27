# B · Bounded overlap with complete responses

Status, 27 October 2026: First attempt was cancelled during serving startup after A exposed a shared reward-contract bug. Corrected retry `14673099` is submitted after all 17 CPU regressions passed.

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

First attempt used about 0.636 GPU-hours (4m46s on eight GPUs). The retry has an eight-GPU, 30-minute cap. Drain behavior and completed updates remain unvalidated on GPUs; learning quality is unmeasured. See the [journal](../../LOG.md) for retained evidence.
