# C · Mid-response updates with rebuilt cache

Status, 27 October 2026: First attempt was cancelled while pending after A exposed a shared reward-contract bug. Corrected retry `14673100` is submitted after all 17 CPU regressions passed.

Use the same overlap and one-publication lag bound as B, but permit Slime to
abort unfinished generation, flush KV cache, publish weights and resume partial
responses. Earlier tokens can come from a different student version. The teacher
remains frozen.

Use `MODE=fully_async` and a fresh original student checkpoint. Follow the
[common protocol](../README.md#separate-execution-checks-and-measurements); retain
separate condition-C manifests and outputs. Record mixed-version response counts:
zero means the mid-response shortcut was not exercised. Compare with B only
after establishing which behavior actually occurred.

The first attempt used no GPUs. The retry has an eight-GPU, 30-minute cap. Completed updates and mixed-version behavior remain unvalidated; learning quality is unmeasured. See the [journal](../../LOG.md) for retained evidence.
