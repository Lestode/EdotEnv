# A · Synchronous distillation

Status, 26 October 2026: selected for renewed execution validation. Earlier smoke
attempts stopped during distributed startup, before model loading or updates;
see the [checkpoint](../REPORT.md) and [journal](../../LOG.md).

Collect a batch, train, then publish weights. Each response must use one policy
version with zero lag. This is the learning reference if execution and subsequent
quality evaluation succeed.

Use `MODE=synchronous`. The [common protocol](../README.md#separate-execution-checks-and-measurements)
defines the initial model, workload and evidence requirements. Each attempt gets
a new output directory and manifest identifying condition A.

No new results or resource use yet. Before another GPU attempt, resolve the
shared Ray startup blocker with a bounded CPU check. Report training results,
elapsed time and resource use here after execution; learning quality remains
unmeasured.
