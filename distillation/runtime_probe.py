"""Import the training stack and exercise BF16 before loading model weights."""

import importlib
import importlib.metadata
import json
import os
import platform


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Run the runtime probe in a Slurm compute allocation")
    for module in (
        "torch",
        "ray",
        "sglang",
        "megatron.core",
        "transformer_engine.pytorch",
        "flash_attn",
    ):
        importlib.import_module(module)
    import torch
    from flash_attn import flash_attn_func
    from transformer_engine.pytorch import LayerNormLinear

    report = {
        "python": platform.python_version(),
        "cuda": torch.version.cuda,
        "packages": {},
        "gpus": [],
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
    }
    for package in (
        "torch",
        "ray",
        "sglang",
        "transformers",
        "transformer-engine",
        "flash-attn",
    ):
        report["packages"][package] = importlib.metadata.version(package)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    report["torch_cuda_arches"] = torch.cuda.get_arch_list()
    for index in range(torch.cuda.device_count()):
        with torch.cuda.device(index):
            if not torch.cuda.is_bf16_supported():
                raise RuntimeError("BF16 is unavailable")
            x = torch.ones((64, 64), device=f"cuda:{index}", dtype=torch.bfloat16)
            if not torch.equal(x @ x, torch.full_like(x, 64)):
                raise RuntimeError("BF16 matrix multiplication failed")
            qkv = [
                torch.randn(
                    (1, 16, 2, 64),
                    device=f"cuda:{index}",
                    dtype=torch.bfloat16,
                    requires_grad=True,
                )
                for _ in range(3)
            ]
            attention = flash_attn_func(*qkv, causal=True)
            attention.float().square().mean().backward()
            layer = LayerNormLinear(
                64, 64, params_dtype=torch.bfloat16, device=f"cuda:{index}"
            )
            inputs = torch.randn(
                (8, 64),
                device=f"cuda:{index}",
                dtype=torch.bfloat16,
                requires_grad=True,
            )
            projected = layer(inputs)
            projected.float().square().mean().backward()
            checked = [
                attention,
                projected,
                inputs.grad,
                *(value.grad for value in qkv),
            ]
            if any(
                value is None or not torch.isfinite(value).all() for value in checked
            ):
                raise RuntimeError("Native attention/normalization probe was nonfinite")
            report["gpus"].append(
                {
                    "name": torch.cuda.get_device_name(index),
                    "capability": torch.cuda.get_device_capability(index),
                    "bf16_matmul": "passed",
                    "flash_attention_forward_backward": "passed",
                    "transformer_engine_forward_backward": "passed",
                }
            )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
