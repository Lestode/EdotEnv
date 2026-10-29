"""Verify checkpoint metadata and tokenizer identity before any model launch."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_LOCK = ROOT / "configs/distillation/models.json"


def fingerprint(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_models(student, teacher, lock_path=MODEL_LOCK, *, require_weights=True):
    lock = json.loads(Path(lock_path).read_text())
    reports = {}
    for role, directory in [("student", Path(student)), ("teacher", Path(teacher))]:
        expected = lock[role]
        for name, digest in expected["files"].items():
            if fingerprint(directory / name) != digest:
                raise ValueError(f"{role}/{name} differs from the pinned checkpoint")
        config = json.loads((directory / "config.json").read_text())
        tokenizer = json.loads((directory / "tokenizer.json").read_text())
        ids = list(tokenizer["model"]["vocab"].values())
        ids += [token["id"] for token in tokenizer.get("added_tokens", [])]
        if max(ids) >= config["vocab_size"]:
            raise ValueError(f"{role} tokenizer exceeds model vocabulary")
        weight_hashes = {}
        if require_weights:
            index = directory / "model.safetensors.index.json"
            files = (
                set(json.loads(index.read_text())["weight_map"].values())
                if index.exists()
                else {"model.safetensors"}
            )
            if not files or any(not (directory / f).is_file() for f in files):
                raise ValueError(f"{role} model weights are missing")
            for name in sorted(files):
                if Path(name).name != name or (directory / name).stat().st_size == 0:
                    raise ValueError(f"{role} has an invalid weight file")
                weight_hashes[name] = fingerprint(directory / name)
        reports[role] = {**expected, "model_vocab_size": config["vocab_size"]}
        if require_weights:
            reports[role]["weight_sha256"] = weight_hashes
    for name in ["tokenizer.json", "tokenizer_config.json", "generation_config.json"]:
        if fingerprint(Path(student) / name) != fingerprint(Path(teacher) / name):
            raise ValueError(f"Teacher and student {name} are incompatible")
    return {
        "models": reports,
        "tokenizer_identity": "exact",
        "weights_present": require_weights,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student", type=Path, required=True)
    parser.add_argument("--teacher", type=Path, required=True)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            verify_models(
                args.student, args.teacher, require_weights=not args.metadata_only
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
