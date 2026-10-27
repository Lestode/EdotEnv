# A · Synchronous distillation

Status, 27 October 2026: First attempt reached rollout processing, then failed on the shared scalar-reward contract before an optimizer update. The correction passed 17 CPU tests; retry `14673098` is submitted.

Collect a batch, train, then publish weights. Each response must use one policy
version with zero lag. This is the learning reference if execution and subsequent
quality evaluation succeed.

Use `MODE=synchronous`. The [common protocol](../README.md#separate-execution-checks-and-measurements)
defines the initial model, workload and evidence requirements. Each attempt gets
a new output directory and manifest identifying condition A.

First attempt used about 1.689 GPU-hours (12m40s on eight GPUs). The retry has an eight-GPU, 30-minute cap. No completed update or learning-quality result yet. See the [journal](../../LOG.md) for retained evidence.
