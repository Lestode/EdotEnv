# Retired Euler experiment attempts

Retired by the user on 28 October 2026. Euler is no longer an execution target;
its preparation, Ray-check and training entry points have been removed. The
[scope decision](../../../AGENTS.md#confirmed-decisions) keeps current execution
on Komondor. The observations below preserve earlier attempts and do not provide
an active procedure or permission for future Euler jobs.

The previous handoff reported an attempted cancellation of the last preparation
job that could not be confirmed after an SSH timeout; retirement does not change
that historical scheduler observation. No Euler training result was recorded.

## Historical observations, 26–27 October 2026

SSH and Slurm access worked. Euler advertised A100 40/80 GB nodes and provides
Apptainer 1.5.5 and uv. Eight GPUs were not immediately available: the inventory
request ended without allocation. An initial submission using per-node memory
was rejected; Euler requires per-CPU memory. An explicit GPU account was rejected;
the default account with automatic partition selection accepted the request.

Neither the selected DeepSeek checkpoints nor the prepared runtime was present
in the inspected user cache. The attempted bounded sequence was CPU runtime/model staging,
a two-node CPU Ray check, then separate A/B/C GPU smoke jobs. Each planned GPU job requested
four A100 80 GB GPUs on each of two nodes for at most 30 minutes. Dependencies were intended to prevent GPU work before prerequisite success.
No Euler training or learning-quality result was established.

The plan used the same pinned models, objective and three-update smoke configuration.
Euler's PCIe topology differs from Komondor's SXM setup: any measurements from the two sites would not have been directly comparable. Runtime/model/output files were staged
in a dedicated user scratch directory. Euler scratch is unbacked and may purge
files older than 15 days; important evidence needed separate retention.

Condition reports: [A](A/REPORT.md), [B](B/REPORT.md), [C](C/REPORT.md).
Submission IDs and outcomes belong in the [journal](../LOG.md).

The first preparation job failed connecting directly to Docker Hub. All dependent
Ray/A/B/C jobs were cancelled before allocation, consuming no GPU time. The
user's sparse adapters workflow confirms `eth_proxy`, uv environments, per-CPU
memory and automatic partition selection. Its CUDA 12.8 stack is not substituted
for Slime's pinned CUDA 13 runtime. The revised preparation loads the proxy and
uses an immutable public image with an external uv environment; this remains
unvalidated. This follows [Euler's container guidance](https://docs.hpc.ethz.ch/software/apptainer/)
without building a custom image on Euler. The inspected account lacked the
container-access group; the supported `get-access` workflow confirmed successful
addition and warned that propagation can take up to 90 minutes. Actual container
execution and the revised runtime remain unvalidated.

27 October: SSH works again and `ID-HPC-SINGULARITY` membership is present.
The CPU shell check `18477373` completed successfully. Preparation retry
`18523280` initially waited for the cluster-wide network/Slurm outage, then
hit its one-hour limit extracting the container on shared scratch. No SIF,
model preparation or GPU execution completed. The next bounded CPU retry
uses 150 GB of Slurm-managed node-local scratch and a two-hour cap. Euler's
[storage guidance](https://docs.hpc.ethz.ch/hardware/storage/#tmp) recommends
local storage for many small files; shared-scratch extraction is a suspected
bottleneck, not a demonstrated root cause. Failed artifacts remain preserved.

The local-scratch retry `18541043` completed the public SIF, then failed after
22m16s compiling FlashAttention: ccache tried to write to the read-only image.
A targeted correction moves compiler-cache writes to writable job storage and
allowed reuse of the completed image after provenance and container checks.
This was intended to avoid repeating extraction; neither training nor runtime
validation had succeeded in the recorded Euler attempts.
