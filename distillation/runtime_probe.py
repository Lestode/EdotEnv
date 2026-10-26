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
    from megatron.core.optimizer import Adam
    from transformer_engine.pytorch import DotProductAttention, LayerNormLinear

    report = {
        "python": platform.python_version(),
        "cuda": torch.version.cuda,
        "flash_attention_implementation": flash_attn_func.__module__,
        "adam_implementation": f"{Adam.__module__}.{Adam.__name__}",
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
            # Student TP2: six query heads and one KV head per rank, head dim 128.
            qkv = [
                torch.randn(
                    (32, heads, 128),
                    device=f"cuda:{index}",
                    dtype=torch.bfloat16,
                    requires_grad=True,
                )
                for heads in (6, 1, 1)
            ]
            cumulative = torch.tensor([0, 9, 32], device=x.device, dtype=torch.int32)
            layer_attention = DotProductAttention(
                6,
                128,
                num_gqa_groups=1,
                qkv_format="thd",
                attn_mask_type="padding_causal",
            )
            attention = layer_attention(
                *qkv,
                cu_seqlens_q=cumulative,
                cu_seqlens_kv=cumulative,
                max_seqlen_q=23,
                max_seqlen_kv=23,
            )
            expected = []
            with torch.no_grad():
                for begin, end in ((0, 9), (9, 32)):
                    q, k, v = [value[begin:end].float() for value in qkv]
                    q = q.transpose(0, 1)
                    k = k.repeat_interleave(6, dim=1).transpose(0, 1)
                    v = v.repeat_interleave(6, dim=1).transpose(0, 1)
                    scores = (q @ k.transpose(-1, -2)) / (128**0.5)
                    mask = torch.ones(
                        end - begin, end - begin, device=x.device, dtype=torch.bool
                    ).triu(1)
                    expected.append(
                        (
                            scores.masked_fill(mask, float("-inf")).softmax(-1) @ v
                        ).transpose(0, 1)
                    )
                reference = torch.cat(expected)
                torch.testing.assert_close(
                    attention.reshape_as(reference).float(),
                    reference,
                    atol=0.025,
                    rtol=0.03,
                )
            attention.float().square().mean().backward()
            layer = LayerNormLinear(
                128,
                128,
                normalization="RMSNorm",
                params_dtype=torch.bfloat16,
                device=f"cuda:{index}",
            )
            inputs = torch.randn(
                (8, 128),
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
            # Megatron updates FP32 master parameters; exercise its selected optimizer.
            parameter = torch.nn.Parameter(torch.ones(16, device=x.device))
            optimizer = Adam(
                [parameter], lr=0.001, betas=(0.0, 0.0), weight_decay=0.0, eps=1e-8
            )
            parameter.grad = torch.full_like(parameter, 2)
            optimizer.step()
            torch.testing.assert_close(parameter, torch.full_like(parameter, 0.999))
            report["gpus"].append(
                {
                    "name": torch.cuda.get_device_name(index),
                    "capability": torch.cuda.get_device_capability(index),
                    "bf16_matmul": "passed",
                    "packed_gqa_reference_and_backward": "passed",
                    "rmsnorm_linear_forward_backward": "passed",
                    "adam_step": "passed",
                }
            )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
