"""Stage the exact selected model snapshots inside a compute allocation."""

import argparse
import json
import os
from pathlib import Path

from distillation.preflight import MODEL_LOCK, verify_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-lock", type=Path, default=MODEL_LOCK)
    parser.add_argument("--reuse-student", type=Path)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Stage model weights inside an authorized compute allocation")
    from huggingface_hub import snapshot_download

    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False)
    lock = json.loads(args.model_lock.read_text())
    for role, model in lock.items():
        if role == "student" and args.reuse_student:
            (args.output / role).symlink_to(
                args.reuse_student.resolve(), target_is_directory=True
            )
            continue
        snapshot_download(
            model["repo"],
            revision=model["revision"],
            local_dir=args.output / role,
            allow_patterns=[
                *model["files"],
                "*.safetensors",
                "model.safetensors.index.json",
            ],
        )
    report = verify_models(
        args.output / "student", args.output / "teacher", args.model_lock
    )
    (args.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
