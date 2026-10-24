# Hardware planning

Status, 2026-10-24: Komondor is the target cluster. SSH access to the greengoblin
gateway is verified, and the gateway's existing Komondor SSH alias reaches the
cluster's browser-based eduID authentication step. Cluster login has not yet
been completed in this session. No compute allocation, compute-node inventory,
or GPU validation has been performed; A100 availability remains an assumption.

## Access boundary

Follow the [protected-infrastructure rule](../AGENTS.md#protected-infrastructure-greengoblin)
for all access through greengoblin. Perform runtime setup and workload validation
on authorized Komondor resources. The gateway's hardware and software inventory
does not establish the cluster's available compute resources or runtime.

## A100 compatibility findings

- A100 has compute capability 8.0 ([NVIDIA](https://developer.nvidia.com/cuda/gpus)).
- The current Slime [Dockerfile](../slime/docker/Dockerfile) defaults native extension builds to `9.0 10.0 10.3`. Do not assume its default image works unchanged on A100.
- SGLang documents Ampere attention paths: FlashInfer/Triton for standard attention and Triton for MLA, depending on model and installed version ([backend guide](https://docs.sglang.io/docs/advanced_features/attention_backend)).
- FlashAttention-2 supports A100 and BF16 ([upstream requirements](https://github.com/Dao-AILab/flash-attention#nvidia-cuda-support)). This does not establish compatibility of the complete Slime stack.

## Proposed validation sequence

1. Complete Komondor authentication through the existing gateway setup; inspect project permissions, partitions, allocation limits, storage, and supported runtimes on the cluster. On an allocated compute node, confirm GPU model, VRAM, GPU count, driver, interconnect, and supported container runtime.
2. Select and pin a compatible runtime; validate required native extensions on A100.
3. Start with BF16, short sequences, and a small compatible model pair for a correctness check. Final DeepSeek checkpoints remain undecided.
4. Verify student generation, teacher token scoring, and one training update on one node, then repeat across nodes.

Local work can proceed on separate context construction, response-token alignment, the top-256 objective, and data transport. GPU execution requires cluster access and a validated runtime; final sizing remains deferred.
