"""Check pinned metadata and shard readability inside each training container."""

import json
import os
import socket
from pathlib import Path

from distillation.preflight import ROOT, verify_models


def check_access(student, teacher, profile):
    lock = (
        ROOT
        / "configs/distillation"
        / ("models-7b32b.json" if profile == "7b32b" else "models.json")
    )
    verify_models(student, teacher, lock, require_weights=False)
    for directory in (Path(student), Path(teacher)):
        index = directory / "model.safetensors.index.json"
        names = (
            set(json.loads(index.read_text())["weight_map"].values())
            if index.exists()
            else {"model.safetensors"}
        )
        if not names:
            raise ValueError(f"No weight shards in {directory}")
        for name in names:
            if Path(name).name != name:
                raise ValueError(f"Invalid shard name: {name}")
            with (directory / name).open("rb") as handle:
                if not handle.read(1):
                    raise ValueError(f"Empty weight shard: {directory / name}")
    return {"host": socket.gethostname(), "model_access": "passed"}


if __name__ == "__main__":
    print(
        json.dumps(
            check_access(
                os.environ["STUDENT_MODEL"],
                os.environ["TEACHER_MODEL"],
                os.environ["DISTILLATION_PROFILE"],
            )
        ),
        flush=True,
    )
