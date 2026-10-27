# Hardware planning

Status, 2026-10-26: Komondor access and an eight-A100 BF16 NCCL all-reduce
across two nodes are verified. The successful layout uses one Slurm task per
node with four workers; per-GPU Slurm tasks failed during NCCL initialization.
The Slime runtime and distributed distillation training remain unvalidated.

## Access boundary

Follow the [protected-infrastructure rule](../AGENTS.md#protected-infrastructure-greengoblin)
for all access through greengoblin. Perform runtime setup and workload validation
on authorized Komondor resources. The gateway's hardware and software inventory
does not establish the cluster's available compute resources or runtime.

Manual tests, numerical checks, inference, and training run in authorized
Komondor compute allocations. Local editing and artifact preparation are allowed;
use uv for new project-managed Python environments. CI remains on GitHub runners.
The [distillation journal](experiments/LOG.md) records current CPU and runtime
qualification; historical single-GPU evidence below is not a training result.

## Allocation preference

Decision, 27 October 2026: fully idle nodes and whole-node exclusivity are not
requirements. Prefer using available GPUs on shared nodes when the job's CPU,
memory and placement needs can be met. Record the actual allocation and node
sharing in experiment evidence; sharing may affect timing comparisons.

The current A/B/C submissions requested exclusive nodes. This is a launcher
choice, not an experimental requirement. Future submissions should avoid that
restriction unless a concrete runtime or measurement need justifies it.
Removing exclusivity alone does not make a four-GPU-per-node layout fit
scattered single GPUs; placement must also be feasible.

A scheduler snapshot on 27 October showed 34 unallocated GPUs in `gpu`, one in
`ai`, and four in `test`, with no fully idle nodes. These are historical counts,
not a reservation or a guarantee of schedulability.

## Observed cluster resources and limits

- Slurm advertises four A100-SXM4-40GB GPUs per standard `gpu` node (one node
  currently advertises three), eight GPUs per `ai` node, and four A100 GPUs on
  the one-hour `test` partition. Both one-GPU `test` and two-node/eight-GPU `gpu`
  allocations have been run.
- The project association permits `normal` and `lowpri` QOS, with `normal` as
  the default, and reports GPU-hour balance available. The user delegated the
  initial validation budget; current training smoke
  attempts are bounded to 30 minutes across eight GPUs (at most four GPU-hours).
- `apptainer --version` reports 1.4.4. Module listings also expose Singularity,
  CUDA, and PyTorch environments, including PyTorch 2.4.1. Listing a module does
  not establish compatibility with the pinned Slime stack.
- Project storage has byte and file-count headroom. Scratch storage is at its
  hard file-count limit (330,000 files); new files there may fail. Establish a
  working cache, temporary-file, and output layout before staging software or
  model weights. Existing project data has not been removed.

## Single-GPU inventory evidence

Slurm job `14640312` used one GPU, two CPU cores, and 4 GiB RAM on `test`, with a
two-minute walltime limit. Accounting reports `COMPLETED`, elapsed `00:00:01`,
and exit code `0:0`. Substitute an authorized project account in the command:

```sh
srun --immediate=10 --account=<project-account> --partition=test \
  --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --gpus=1 \
  --time=00:02:00 --job-name=opcd-inventory \
  nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader
```

Observed output:

```text
0, NVIDIA A100-SXM4-40GB, 40960 MiB, 615.71.09
```

This verifies access to an allocated GPU and its driver, not model execution,
BF16 kernels, container GPU passthrough, Slime compatibility, or distillation correctness.

## A100 compatibility findings

- A100 has compute capability 8.0 ([NVIDIA](https://developer.nvidia.com/cuda/gpus)).
- The current Slime [Dockerfile](../slime/docker/Dockerfile) defaults native extension builds to `9.0 10.0 10.3`. Do not assume its default image works unchanged on A100.
- SGLang documents Ampere attention paths: FlashInfer/Triton for standard attention and Triton for MLA, depending on model and installed version ([backend guide](https://docs.sglang.io/docs/advanced_features/attention_backend)).
- FlashAttention-2 supports A100 and BF16 ([upstream requirements](https://github.com/Dao-AILab/flash-attention#nvidia-cuda-support)). This does not establish compatibility of the complete Slime stack.

## Proposed validation sequence

1. Complete the resource inventory beyond the single-GPU probe above: verify the intended node/GPU counts, interconnect, storage layout, and container GPU passthrough on allocated resources.
2. Select and pin a compatible runtime; validate required native extensions on A100.
3. Start with BF16 and short sequences for a correctness check using the [initial model pair](EXPERIMENTS.md#initial-policy-distillation-pair), after verifying tokenizer compatibility.
4. Verify student generation, teacher token scoring, and one training update on one node, then repeat across nodes.

GPU training still requires a validated runtime and storage layout; final sizing remains deferred.
