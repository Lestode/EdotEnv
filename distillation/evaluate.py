"""Evaluate a frozen SGLang checkpoint on a caller-selected, held-out math JSONL."""

import argparse
import importlib
import json
import os
import time
import urllib.request
from pathlib import Path

from distillation.preflight import fingerprint


def request(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument(
        "--scorer", default="slime.rollout.rm_hub.math_utils.grade_answer_verl"
    )
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Evaluation requires a Slurm compute allocation")
    if args.max_tokens < 1:
        raise ValueError("max-tokens must be positive")
    from transformers import AutoTokenizer

    endpoint = args.endpoint.rstrip("/")
    info = request(endpoint + "/get_model_info")
    if Path(info["model_path"]).resolve() != args.model.resolve():
        raise ValueError("Endpoint serves a different model")
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model), local_files_only=True, trust_remote_code=False
    )
    module, function = args.scorer.rsplit(".", 1)
    scorer = getattr(importlib.import_module(module), function)
    rows = [
        json.loads(line) for line in args.data.read_text().splitlines() if line.strip()
    ]
    if not rows or any("prompt" not in r or "answer" not in r for r in rows):
        raise ValueError("Evaluation JSONL requires prompt and answer for every row")
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False)
    summary = {
        "status": "running",
        "model_info": info,
        "data_sha256": fingerprint(args.data),
        "tokenizer_sha256": fingerprint(args.model / "tokenizer.json"),
        "generation": {"temperature": 0, "max_new_tokens": args.max_tokens},
        "scorer": args.scorer,
        "planned": len(rows),
        "attempted": 0,
        "failed": 0,
        "correct": 0,
        "truncated": 0,
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
    }
    summary_path = args.output / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    start = time.monotonic()
    try:
        with (args.output / "responses.jsonl").open("x") as log:
            for index, row in enumerate(rows):
                record = {"index": index}
                summary["attempted"] += 1
                stage = "generation"
                try:
                    messages = row["prompt"]
                    if isinstance(messages, str):
                        messages = [{"role": "user", "content": messages}]
                    ids = tokenizer.apply_chat_template(
                        messages, tokenize=True, add_generation_prompt=True
                    )
                    response = request(
                        endpoint + "/generate",
                        {"input_ids": ids, "sampling_params": summary["generation"]},
                    )
                    record["response"] = response
                    truncated = (
                        response["meta_info"].get("finish_reason", {}).get("type")
                        == "length"
                    )
                    record["truncated"] = truncated
                    summary["truncated"] += int(truncated)
                    stage = "grading"
                    correct = bool(scorer(response["text"], str(row["answer"])))
                    record["correct"] = correct
                    summary["correct"] += int(correct)
                except Exception as error:
                    record["error"] = f"{type(error).__name__}: {error}"
                    record["error_stage"] = stage
                    summary["failed"] += 1
                log.write(json.dumps(record) + "\n")
                log.flush()
        summary["status"] = (
            "completed" if summary["failed"] == 0 else "completed_with_errors"
        )
    except BaseException:
        summary["status"] = "interrupted"
        raise
    finally:
        summary["elapsed_seconds"] = time.monotonic() - start
        summary["accuracy_over_planned"] = summary["correct"] / len(rows)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
