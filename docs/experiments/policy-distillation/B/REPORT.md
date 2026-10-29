# B · Bounded overlap with complete responses

Recorded smoke result, 27 October 2026: corrected B-a2 job `14673099` completed all three training updates and saved its checkpoint. Losses and nonzero gradient norms were finite. Across 24 consumed responses, 16 were one publication stale and none mixed policy versions. Producer-drain completion was logged before publication.

This preserves an earlier smoke checkpoint. Later attempts and the current
experimental direction are tracked in the [overview](../README.md#current-experimental-status)
and [journal](../../LOG.md).

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

B-a2 took 9m15s on eight GPUs (about 1.233 GPU-hours), including startup and checkpointing. The first cancelled attempt used about 0.636 GPU-hours. The bounded execution smoke and observed B invariants passed; learning quality and steady-state speed remain unmeasured. Retained logs include post-warmup `freeze_gc` connection failures before subsequent successful serving and training. Evidence: private `B-a2/train/manifest.json`, `train.log`, rollouts and checkpoint; see the [journal](../../LOG.md).
