"""Evaluate a frozen SGLang checkpoint on a caller-selected, held-out math JSONL."""

import argparse
import importlib
import json
import math
import os
import time
import urllib.request
from pathlib import Path

from distillation.preflight import fingerprint


def request(url, payload=None, *, timeout=180):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def generate_batch(tokenizer, rows, endpoint, generation, timeout):
    inputs = []
    for row in rows:
        messages = row["prompt"]
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        inputs.append(
            tokenizer.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True, return_dict=False
            )
        )
    response = request(
        endpoint + "/generate",
        {
            "input_ids": inputs[0] if len(inputs) == 1 else inputs,
            "sampling_params": generation,
        },
        timeout=timeout,
    )
    responses = [response] if len(inputs) == 1 else response
    if not isinstance(responses, list) or len(responses) != len(rows):
        raise ValueError("Generation response count differs from batch size")
    if any(not isinstance(response, dict) for response in responses):
        raise ValueError("Expected a generation response object for every example")
    return responses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--request-timeout", type=float, default=180)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument(
        "--scorer", default="slime.rollout.rm_hub.math_utils.grade_answer_verl"
    )
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Evaluation requires a Slurm compute allocation")
    if args.max_tokens < 1:
        raise ValueError("max-tokens must be positive")
    if not math.isfinite(args.request_timeout) or args.request_timeout <= 0:
        raise ValueError("request-timeout must be finite and positive")
    if args.batch_size < 1:
        raise ValueError("batch-size must be positive")
    from transformers import AutoTokenizer

    endpoint = args.endpoint.rstrip("/")
    info = request(endpoint + "/get_model_info", timeout=args.request_timeout)
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
        "request_timeout_seconds": args.request_timeout,
        "batch_size": args.batch_size,
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
            for offset in range(0, len(rows), args.batch_size):
                batch = rows[offset : offset + args.batch_size]
                summary["attempted"] += len(batch)
                generation_error = None
                try:
                    responses = generate_batch(
                        tokenizer,
                        batch,
                        endpoint,
                        summary["generation"],
                        args.request_timeout,
                    )
                except Exception as error:
                    generation_error = f"{type(error).__name__}: {error}"
                    responses = [None] * len(batch)
                for position, (row, response) in enumerate(
                    zip(batch, responses, strict=True)
                ):
                    record = {"index": offset + position}
                    if generation_error:
                        record.update(error=generation_error, error_stage="generation")
                        summary["failed"] += 1
                    else:
                        record["response"] = response
                        stage = "generation"
                        try:
                            truncated = (
                                response["meta_info"]
                                .get("finish_reason", {})
                                .get("type")
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
                summary["elapsed_seconds"] = time.monotonic() - start
                summary_path.write_text(json.dumps(summary, indent=2) + "\n")
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
