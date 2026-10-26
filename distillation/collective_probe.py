"""Small BF16 NCCL all-reduce launched by torchrun inside Slurm."""

import datetime
import json
import os
import socket


def main():
    import torch
    import torch.distributed as dist

    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Run inside a Slurm compute allocation")
    rank = int(os.environ["RANK"])
    world = int(os.environ["WORLD_SIZE"])
    local_rank = int(os.environ["LOCAL_RANK"])
    if not torch.cuda.is_available() or local_rank >= torch.cuda.device_count():
        raise RuntimeError("Each worker needs an allocated visible GPU")
    torch.cuda.set_device(local_rank)
    dist.init_process_group("nccl", timeout=datetime.timedelta(seconds=60))
    try:
        values = torch.full(
            (1024 * 1024,),
            rank + 1,
            device=f"cuda:{local_rank}",
            dtype=torch.bfloat16,
        )
        dist.all_reduce(values)
        torch.cuda.synchronize()
        expected = world * (world + 1) / 2
        if not torch.equal(values, torch.full_like(values, expected)):
            raise RuntimeError("NCCL all-reduce returned incorrect values")
        print(
            json.dumps(
                {
                    "rank": rank,
                    "world": world,
                    "host": socket.gethostname(),
                    "local_rank": local_rank,
                    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                    "gpu": torch.cuda.get_device_name(local_rank),
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "nccl": torch.cuda.nccl.version(),
                    "bf16_all_reduce": "passed",
                }
            ),
            flush=True,
        )
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
