# Euler A/B/C smoke validation

26 October 2026. The user authorized Euler as the execution host while Komondor
authentication is unavailable, with separate cluster-specific Slurm scripts.
This overrides the earlier Komondor-only execution scope for these checks.

SSH and Slurm access work. Euler advertises A100 40/80 GB nodes and provides
Apptainer 1.5.5 and uv. Eight GPUs were not immediately available: the inventory
request ended without allocation. An initial submission using per-node memory
was rejected; Euler requires per-CPU memory. An explicit GPU account was rejected;
the default account with automatic partition selection accepted the request.

Neither the selected DeepSeek checkpoints nor the prepared runtime was present
in the inspected user cache. The bounded sequence is CPU runtime/model staging,
a two-node CPU Ray check, then separate A/B/C GPU smoke jobs. Each GPU job requests
four A100 80 GB GPUs on each of two nodes for at most 30 minutes. Dependencies
prevent GPU work before prerequisite success. There are no Euler training results
yet, and no learning-quality claim.

The same pinned models, objective and three-update smoke configuration apply.
Euler's PCIe topology differs from Komondor's SXM setup: performance measurements
must be reported by cluster, not pooled. All new runtime/model/output files live
in a dedicated user scratch directory. Euler scratch is unbacked and may purge
files older than 15 days; retain important evidence locally.

Condition reports: [A](A/REPORT.md), [B](B/REPORT.md), [C](C/REPORT.md).
Submission IDs and outcomes belong in the [journal](../LOG.md).
