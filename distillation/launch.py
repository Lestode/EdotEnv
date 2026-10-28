"""Prepare or run a fresh Slime distillation attempt on an existing Ray cluster."""

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from distillation.layout import layout
from distillation.preflight import ROOT, fingerprint, verify_models

SLIME_REVISION = "18868a79b0b083a093798a94ed0f8cb4f71b9c14"
CONDITIONS = {"synchronous": "A", "bounded_async": "B", "fully_async": "C"}


def serving_config(student, teacher, profile="smoke"):
    pilot = profile == "7b32b"
    return {
        "sglang": [
            {
                "name": name,
                "model_path": str(path),
                "update_weights": update,
                "server_groups": [
                    {
                        "worker_type": "regular",
                        "num_gpus": 4 if pilot else 2,
                        "num_gpus_per_engine": 4 if pilot and name == "teacher" else 2,
                        "overrides": {
                            "attention_backend": "triton",
                            "dtype": "bfloat16",
                            "mem_fraction_static": 0.65,
                            "context_length": 4096,
                        },
                    }
                ],
            }
            for name, path, update in [
                ("student", student, True),
                ("teacher", teacher, False),
            ]
        ]
    }


def training_args(args, output):
    allocation = layout(
        getattr(args, "profile", "smoke"), getattr(args, "gpus_per_node", 4)
    )
    command = [
        "--rollout-session-id",
        str(output),
        "--hf-checkpoint",
        str(args.student),
        "--ref-load",
        str(args.student),
        "--save",
        str(output / "checkpoints"),
        "--save-interval",
        str(args.rollouts),
        "--swiglu",
        "--num-layers",
        "28",
        "--hidden-size",
        "1536",
        "--ffn-hidden-size",
        "8960",
        "--num-attention-heads",
        "12",
        "--group-query-attention",
        "--num-query-groups",
        "2",
        "--use-rotary-position-embeddings",
        "--rotary-base",
        "10000",
        "--normalization",
        "RMSNorm",
        "--norm-epsilon",
        "1e-6",
        "--disable-bias-linear",
        "--add-qkv-bias",
        "--untie-embeddings-and-output-weights",
        "--vocab-size",
        "151936",
        "--max-position-embeddings",
        "131072",
        "--actor-num-nodes",
        str(allocation["training_nodes"]),
        "--actor-num-gpus-per-node",
        str(allocation["gpus_per_node"]),
        "--num-gpus-per-node",
        str(allocation["gpus_per_node"]),
        "--rollout-num-gpus",
        "4",
        "--tensor-model-parallel-size",
        "2",
        "--pipeline-model-parallel-size",
        "1",
        "--context-parallel-size",
        "1",
        "--sequence-parallel",
        "--attention-backend",
        "flash",
        "--recompute-granularity",
        "full",
        "--recompute-method",
        "uniform",
        "--recompute-num-layers",
        "1",
        "--sglang-config",
        str(output / "serving.json"),
        "--sglang-server-concurrency",
        "2",
        "--fully-async-group-prefetch-factor",
        "1",
        "--flush-cache-interval",
        "1",
        "--rollout-data-transport",
        "object-store",
        "--rollout-function-path",
        f"distillation.hooks.{args.mode}",
        "--custom-rm-path",
        "distillation.hooks.score_teacher",
        "--reward-key",
        "task_reward",
        "--custom-reward-post-process-path",
        "distillation.hooks.post_process_rewards",
        "--custom-config-path",
        str(output / "hooks.json"),
        "--prompt-data",
        str(args.data),
        "--input-key",
        "prompt",
        "--apply-chat-template",
        "--rollout-shuffle",
        "--rollout-seed",
        str(args.seed),
        "--seed",
        str(args.seed),
        "--num-rollout",
        str(args.rollouts),
        "--rollout-batch-size",
        "8",
        "--n-samples-per-prompt",
        "1",
        "--global-batch-size",
        "8",
        "--micro-batch-size",
        "1",
        "--rollout-max-response-len",
        str(args.response_tokens),
        "--rollout-max-context-len",
        "4096",
        "--rollout-max-prompt-len",
        str(4096 - args.response_tokens),
        "--rollout-temperature",
        "1",
        "--rollout-top-p",
        "1",
        "--rollout-top-k",
        "-1",
        "--advantage-estimator",
        "grpo",
        "--pg-loss-type",
        "reinforce",
        "--use-opd",
        "--opd-type",
        "sglang",
        "--opd-kl-coef",
        "1",
        "--disable-rewards-normalization",
        "--disable-grpo-std-normalization",
        "--calculate-per-token-loss",
        "--kl-coef",
        "0",
        "--kl-loss-coef",
        "0",
        "--entropy-coef",
        "0",
        "--optimizer",
        "adam",
        "--lr",
        "1e-6",
        "--lr-decay-style",
        "constant",
        "--weight-decay",
        "0",
        "--adam-beta1",
        "0.9",
        "--adam-beta2",
        "0.98",
        "--clip-grad",
        "1",
        "--attention-dropout",
        "0",
        "--hidden-dropout",
        "0",
        "--accumulate-allreduce-grads-in-fp32",
        "--attention-softmax-in-fp32",
        "--save-debug-rollout-data",
        str(output / "rollouts/{rollout_id}.pt"),
    ]
    if getattr(args, "profile", "smoke") == "7b32b":
        overrides = {
            "--hidden-size": "3584",
            "--ffn-hidden-size": "18944",
            "--num-attention-heads": "28",
            "--num-query-groups": "4",
            "--vocab-size": "152064",
            "--rollout-num-gpus": "8",
            "--tensor-model-parallel-size": "4",
            "--sglang-server-concurrency": "8",
            "--rollout-batch-size": "64",
            "--global-batch-size": "64",
        }
        if getattr(args, "save_interval", None):
            overrides["--save-interval"] = str(args.save_interval)
        # Leave GPU headroom for TP weight gathering after optimizer state exists.
        command += [
            "--optimizer-cpu-offload",
            "--optimizer-offload-fraction",
            "0.5",
            "--use-precision-aware-optimizer",
            "--main-grads-dtype",
            "fp32",
            "--main-params-dtype",
            "fp32",
            "--exp-avg-dtype",
            "fp32",
            "--exp-avg-sq-dtype",
            "fp32",
        ]
        command += ["--save-hf", str(output / "hf-checkpoints" / "{rollout_id}")]
        for option, value in overrides.items():
            command[command.index(option) + 1] = value
    if getattr(args, "checkpoint_mode", "full") == "model-only":
        command.append("--no-save-optim")
    return command


def validate_options(args):
    layout(getattr(args, "profile", "smoke"), getattr(args, "gpus_per_node", 4))
    if args.rollouts < 1 or not 1 <= args.response_tokens <= 2048:
        raise ValueError("Require positive rollouts and 1–2048 response tokens")
    if args.max_policy_lag < 0 or (
        args.mode == "synchronous" and args.max_policy_lag != 0
    ):
        raise ValueError(
            "Synchronous runs require lag zero; async lag must be nonnegative"
        )
    if not args.data.is_file():
        raise ValueError("Training JSONL does not exist")
    rows = [
        json.loads(line) for line in args.data.read_text().splitlines() if line.strip()
    ]
    if len(rows) < 8 or any(
        not isinstance(r.get("prompt"), (str, list)) or not r["prompt"] for r in rows
    ):
        raise ValueError("Training JSONL needs at least eight nonempty prompt records")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student", type=Path, required=True)
    parser.add_argument("--teacher", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, required=True, help="New private shared directory"
    )
    parser.add_argument("--mode", choices=list(CONDITIONS), default="synchronous")
    parser.add_argument("--max-policy-lag", type=int)
    parser.add_argument("--rollouts", type=int, default=3)
    parser.add_argument("--response-tokens", type=int, default=512)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument(
        "--checkpoint-mode",
        choices=("full", "model-only"),
        default="full",
        help="Model-only omits optimizer state; it cannot resume the same Adam trajectory.",
    )
    parser.add_argument("--profile", choices=["smoke", "7b32b"], default="smoke")
    parser.add_argument("--gpus-per-node", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    for key in ("student", "teacher", "data", "output"):
        setattr(args, key, getattr(args, key).resolve())
    if args.max_policy_lag is None:
        args.max_policy_lag = 0 if args.mode == "synchronous" else 1
    validate_options(args)
    model_lock = (
        ROOT
        / "configs/distillation"
        / ("models-7b32b.json" if args.profile == "7b32b" else "models.json")
    )
    models = verify_models(args.student, args.teacher, model_lock)
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT / "slime"), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != SLIME_REVISION:
        raise ValueError("Slime revision differs from the validated adapter contract")
    if subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT / "slime"),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
    ).strip():
        raise ValueError("Slime contains uncommitted changes")
    if args.execute and not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Execution requires a Slurm compute allocation")
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "serving.json").write_text(
        json.dumps(serving_config(args.student, args.teacher, args.profile), indent=2)
        + "\n"
    )
    (args.output / "hooks.json").write_text(
        json.dumps(
            {
                "distillation_max_policy_lag": args.max_policy_lag,
                "distillation_teacher_concurrency": 8 if args.profile == "7b32b" else 2,
            }
        )
        + "\n"
    )
    command = [
        sys.executable,
        str(ROOT / "slime/train.py"),
        *training_args(args, args.output),
    ]
    manifest = {
        "models": models,
        "profile": args.profile,
        "allocation": layout(args.profile, args.gpus_per_node),
        "slime_revision": revision,
        "adapter_sha256": {
            p.name: fingerprint(p) for p in sorted((ROOT / "distillation").glob("*.py"))
        },
        "project_revision": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "mode": args.mode,
        "condition": CONDITIONS[args.mode],
        "response_policy": (
            "abort_flush_resume" if args.mode == "fully_async" else "complete_response"
        ),
        "max_policy_lag": args.max_policy_lag,
        "data_sha256": fingerprint(args.data),
        "command": command,
        "objective": "sampled-token reverse-KL advantage with REINFORCE; no importance correction",
        "status": "prepared",
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(shlex.join(command), flush=True)
    if args.execute:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [str(ROOT), str(ROOT / "slime"), env.get("PYTHONPATH", "")]
        )
        env["CUDA_DEVICE_MAX_CONNECTIONS"] = "1"
        env["TOKENIZERS_PARALLELISM"] = "false"
        manifest["status"] = "running"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        try:
            with (args.output / "train.log").open("x") as log:
                result = subprocess.run(
                    command, env=env, stdout=log, stderr=subprocess.STDOUT, check=False
                )
            manifest.update(
                status="completed" if result.returncode == 0 else "failed",
                exit_code=result.returncode,
            )
        except BaseException:
            manifest["status"] = "interrupted"
            raise
        finally:
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
