#!/bin/bash
# Source inside the pinned Slime container before importing torch/TE.
# Both loaders must select PyTorch's cuDNN instead of the older system copy.
export CUDNN_HOME=/opt/sglang/lib/python3.12/site-packages/nvidia/cudnn
export LD_LIBRARY_PATH="$CUDNN_HOME/lib:${LD_LIBRARY_PATH:-}"
# Match the launcher's explicit FlashAttention backend in native-kernel probes.
export NVTE_FLASH_ATTN=1
export NVTE_FUSED_ATTN=0
export NVTE_UNFUSED_ATTN=0
