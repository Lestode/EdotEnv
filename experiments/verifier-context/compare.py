#!/usr/bin/env python3
"""Prepare, execute, and summarize the Markdown guidance comparison."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import traceback
from uuid import uuid4

HERE = Path(__file__).resolve().parent
HARBOR_VERSION = "0.20.0"
METRIC = "weighted_pearson_ic"
MAX_OUTPUT_TOKENS = 4096


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fingerprint(root):
    """Hash every file, rejecting links rather than following outside the task."""
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported: {path}")
        if path.is_file():
            if "__pycache__" in path.parts or path.name == ".DS_Store":
                continue
            with path.open("rb") as stream:
                files[str(path.relative_to(root))] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
    return files


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_limits_text(plan):
    """Common execution facts, independent of the research-guidance treatment."""
    lines = [
        "# Actual execution limits for this comparison",
        "",
        "These runner-enforced limits override any different time or turn "
        "allowance stated earlier in the task description.",
        "",
        f"- Maximum agent turns: {plan['max_turns']}.",
        f"- Agent execution time limit: {plan['agent_seconds']} seconds "
        f"({plan['agent_seconds'] / 60:g} minutes), starting when agent execution begins.",
        f"- Maximum output tokens per model response: {MAX_OUTPUT_TOKENS}.",
        "",
        "A turn is one agent response in the execution loop. Responses used to "
        "poll, wait, debug, or confirm completion count toward the same turn limit. "
        "A response can contain multiple shell commands. Model calls, commands, "
        "and waiting during agent execution consume the time budget. "
        "No automatic remaining-turn or remaining-time countdown is provided.",
        "",
        "Study-wide spending safeguards or infrastructure failures can interrupt "
        "a trial earlier. Such interruptions are reported separately from task outcomes.",
        "",
        "Register the final model with submit_model before either limit is reached. "
        "Research-tool attempt allowances are separate and do not extend these limits.",
    ]
    resources = plan.get("environment", {})
    for field, label in (
        ("override_cpus", "CPUs"),
        ("override_memory_mb", "memory in MiB"),
        ("override_storage_mb", "storage in MiB"),
    ):
        if field in resources:
            lines.append(f"- Configured sandbox {label}: {resources[field]}.")
    return "\n".join(lines) + "\n"


def prepare(
    source,
    destination,
    model,
    pairs=2,
    turns=30,
    seconds=1800,
    backend="docker",
    concurrency=1,
    cpus=None,
    memory_gb=None,
    storage_gb=None,
):
    source, destination = source.resolve(), destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError("Run directory must be outside the supplied task")
    if min(pairs, turns, seconds) < 1:
        raise ValueError("Pairs, turns and seconds must be positive")
    if backend not in ("docker", "daytona"):
        raise ValueError("Backend must be docker or daytona")
    if not 1 <= concurrency <= 2 * pairs:
        raise ValueError("Concurrency must be between one and the trial count")
    if any(v is not None and v < 1 for v in (cpus, memory_gb, storage_gb)):
        raise ValueError("Resource overrides must be positive")
    if not model.startswith("openai/") or len(model) <= len("openai/"):
        raise ValueError("Use an explicit LiteLLM OpenAI model, e.g. openai/MODEL_ID")
    for name in ("task.toml", "instruction.md", "environment", "tests"):
        if not (source / name).exists():
            raise ValueError(f"Missing task component: {name}")
    fingerprint(source)  # Reject links before copying anything.
    destination.mkdir(parents=True, exist_ok=False)
    task = destination / "task"
    task.mkdir()
    # Keep the original Docker build allowlists and separate verifier intact.
    # Do not copy the reference solution or any surrounding host workspace.
    for name in ("task.toml", "instruction.md", "environment", "tests"):
        src, dst = source / name, task / name
        if src.is_dir():
            shutil.copytree(
                src, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store")
            )
        else:
            shutil.copyfile(src, dst)
    shutil.copyfile(HERE / "research-guidance.md", destination / "guidance.md")
    study_id = uuid4().hex[:12]
    environment = {"type": backend, "delete": True}
    for name, value in (
        ("override_cpus", cpus),
        ("override_memory_mb", memory_gb * 1024 if memory_gb else None),
        ("override_storage_mb", storage_gb * 1024 if storage_gb else None),
    ):
        if value is not None:
            environment[name] = value
    if backend == "daytona":
        environment["kwargs"] = {
            "labels": {"edot.study": study_id},
            "auto_stop_interval_mins": 30,
            "auto_delete_interval_mins": 0,
        }
    trials = []
    for pair in range(1, pairs + 1):
        for arm in ("A", "B") if pair % 2 else ("B", "A"):
            trials.append(
                {"id": f"{study_id}-pair-{pair:02d}-{arm}", "pair": pair, "arm": arm}
            )
    plan = {
        "schema_version": 2,
        "study_id": study_id,
        "harbor_version": HARBOR_VERSION,
        "model": model,
        "max_turns": turns,
        "agent_seconds": seconds,
        "environment": environment,
        "concurrency": concurrency,
        "runner_sha256": digest(Path(__file__)),
        "requirements_sha256": digest(HERE / "requirements.txt"),
        "task_files": fingerprint(task),
        "guidance_sha256": digest(destination / "guidance.md"),
        "trials": trials,
    }
    runtime_limits = destination / "runtime-limits.md"
    runtime_limits.write_text(runtime_limits_text(plan))
    plan["runtime_limits_sha256"] = digest(runtime_limits)
    write_json(destination / "plan.json", plan)
    return plan


def verify_frozen(root, plan):
    if digest(Path(__file__)) != plan["runner_sha256"]:
        raise ValueError("Runner changed after preparation; prepare a new comparison")
    if digest(HERE / "requirements.txt") != plan["requirements_sha256"]:
        raise ValueError(
            "Dependencies changed after preparation; prepare a new comparison"
        )
    if fingerprint(root / "task") != plan["task_files"]:
        raise ValueError("Task changed after preparation; prepare a new comparison")
    if digest(root / "guidance.md") != plan["guidance_sha256"]:
        raise ValueError("Guidance changed after preparation; prepare a new comparison")
    limits = root / "runtime-limits.md"
    if (
        not limits.is_file()
        or digest(limits) != plan.get("runtime_limits_sha256")
        or limits.read_text() != runtime_limits_text(plan)
    ):
        raise ValueError(
            "Runtime limits changed or are not disclosed; prepare a new comparison"
        )


def trial_config(root, plan, trial):
    """The sole arm-dependent input is extra_instruction_paths."""
    return {
        "task": {"path": str(root / "task")},
        "trial_name": trial["id"],
        "trials_dir": str(root / "trials"),
        "agent": {
            "name": "terminus-2",
            "model_name": plan["model"],
            "override_timeout_sec": plan["agent_seconds"],
            "kwargs": {
                "max_turns": plan["max_turns"],
                "use_responses_api": True,
                "enable_summarize": False,
                "reasoning_effort": "low",
                "llm_call_kwargs": {"max_output_tokens": MAX_OUTPUT_TOKENS},
            },
        },
        "environment": plan.get("environment", {"type": "docker", "delete": True}),
        # Append the common correction last, after the original task and any
        # treatment, so neither arm retains a misleading task-level allowance.
        "extra_instruction_paths": (
            [str(root / "guidance.md")] if trial["arm"] == "B" else []
        )
        + [str(root / "runtime-limits.md")],
    }


def preflight(root, plan):
    verify_frozen(root, plan)
    for line in (HERE / "requirements.txt").read_text().splitlines():
        if "==" in line and not line.startswith("#"):
            package, version = line.split("==")
            if importlib.metadata.version(package) != version:
                raise ValueError(f"Install {package}=={version}")
    from harbor.models.task.task import Task
    from harbor.models.trial.config import TrialConfig

    for trial in plan["trials"]:
        TrialConfig.model_validate(trial_config(root, plan, trial))
    Task(task_dir=root / "task")
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY in the process environment")
    if plan.get("environment", {}).get("type", "docker") == "daytona":
        from harbor.environments.daytona.environment import DaytonaEnvironment

        if not os.environ.get("DAYTONA_API_KEY"):
            raise ValueError("Set DAYTONA_API_KEY in the process environment")
        DaytonaEnvironment.preflight()
    else:
        subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=30)
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            capture_output=True,
            timeout=30,
        )


def finite_number(value, low=None, high=None):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and (low is None or value >= low)
        and (high is None or value <= high)
    )


def collect_trial(root, trial):
    row = {**trial, "status": "not_run", "score": None, "cost_usd": None}
    directory = root / "trials" / trial["id"]
    if not directory.exists():
        return row
    row["status"] = "incomplete"
    try:
        result = read_json(directory / "result.json")
        cost = (result.get("agent_result") or {}).get("cost_usd")
        row["cost_usd"] = cost if finite_number(cost, low=0) else None
        exception = result.get("exception_info") or {}
        row["exception_type"] = exception.get("exception_type")
        metrics = read_json(directory / "verifier" / "metrics.json")
        reward = read_json(directory / "verifier" / "reward.json")
        if metrics.get("ok") is False:
            row.update(status="rejected", error_code=metrics.get("error_code"))
        elif metrics.get("ok") is True:
            score = metrics.get("metrics", {}).get(METRIC)
            if (
                finite_number(score, -1, 1)
                and score == metrics.get("primary_score")
                and score == reward.get(METRIC)
                and score == reward.get("primary_score")
            ):
                row.update(status="accepted", score=score)
            else:
                row["status"] = "invalid_score"
        else:
            row["status"] = "invalid_verifier_output"
    except FileNotFoundError:
        row["status"] = "execution_error" if row.get("exception_type") else "incomplete"
    except (ValueError, TypeError, AttributeError):
        row["status"] = "invalid_output"
    return row


def summarize(root, plan):
    rows = [collect_trial(root, trial) for trial in plan["trials"]]
    arms = {}
    for arm in ("A", "B"):
        selected = [row for row in rows if row["arm"] == arm]
        scores = [row["score"] for row in selected if row["status"] == "accepted"]
        arms[arm] = {
            "planned": len(selected),
            "status_counts": {
                status: sum(row["status"] == status for row in selected)
                for status in sorted({row["status"] for row in selected})
            },
            "accepted_mean_ic": statistics.mean(scores) if scores else None,
            "accepted_median_ic": statistics.median(scores) if scores else None,
        }
    deltas = []
    for pair in sorted({row["pair"] for row in rows}):
        scores = {
            row["arm"]: row["score"]
            for row in rows
            if row["pair"] == pair and row["status"] == "accepted"
        }
        if scores.keys() == {"A", "B"}:
            deltas.append({"pair": pair, "B_minus_A": scores["B"] - scores["A"]})
    report = {
        "metric": METRIC,
        "arms": arms,
        "complete_accepted_pairs": deltas,
        "mean_paired_delta": (
            statistics.mean(item["B_minus_A"] for item in deltas) if deltas else None
        ),
        "trials": rows,
    }
    write_json(root / "summary.json", report)
    lines = [
        "# Final-score comparison",
        "",
        f"Metric: `{METRIC}`",
        "",
        "| Arm | Planned | Accepted | Mean IC | Median IC | Status counts |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for arm, stats in arms.items():
        counts = stats["status_counts"]
        mean = stats["accepted_mean_ic"]
        median = stats["accepted_median_ic"]
        lines.append(
            f"| {arm} | {stats['planned']} | {counts.get('accepted', 0)} | "
            f"{mean if mean is not None else 'n/a'} | "
            f"{median if median is not None else 'n/a'} | {counts} |"
        )
    lines += [
        "",
        f"Pairs with accepted scores in both arms: {len(deltas)}.",
        f"Mean B − A across those pairs: {report['mean_paired_delta']}.",
        "",
        "Means include accepted submissions only. Read failure counts alongside "
        "them; missing/rejected submissions have no measured IC. Pairing marks "
        "execution blocks, not identical random seeds. A small pilot is descriptive "
        "and does not establish statistical significance.",
        "",
    ]
    (root / "summary.md").write_text("\n".join(lines))
    with (root / "scores.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["id", "pair", "arm", "status", "score", "cost_usd"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    return report


async def harbor_trial(root, plan, trial):
    from harbor.models.trial.config import TrialConfig
    from harbor.trial.trial import Trial

    config = TrialConfig.model_validate(trial_config(root, plan, trial))
    instance = await Trial.create(config)
    try:
        await instance.run()
    finally:
        if plan.get("environment", {}).get("type") == "daytona":
            from harbor.environments.daytona.environment import DaytonaClientManager

            manager = await DaytonaClientManager.get_instance()
            await manager._cleanup()


async def run_trial(root, plan, trial):
    if plan.get("environment", {}).get("type") != "daytona":
        return await harbor_trial(root, plan, trial)
    # Harbor synchronously compresses large upload trees. Separate processes
    # prevent one trial from starving another trial's RPC timeout/heartbeat.
    directory = root / "trials" / trial["id"]
    with (directory / "worker.log").open("wb") as stream:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(Path(__file__).resolve()),
            "_trial",
            str(root),
            trial["id"],
            "--allow-paid",
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
        try:
            code = await process.wait()
            if code:
                raise RuntimeError(f"Trial worker {trial['id']} exited with {code}")
        except asyncio.CancelledError:
            if process.returncode is None:
                try:
                    process.send_signal(signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(process.wait(), timeout=30)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            raise


async def cleanup_daytona(root, plan):
    """Delete only this study's remaining sandboxes; report failed cleanup."""
    from daytona import AsyncDaytona, ListSandboxesQuery
    from daytona.common.errors import DaytonaConflictError, DaytonaNotFoundError

    client = AsyncDaytona()
    deleted, remaining = [], []
    status = "failed"
    try:
        query = ListSandboxesQuery(labels={"edot.study": plan["study_id"]})
        # Lists can lag deletion, and a concurrent native stop can return 409.
        # Retry only owned resources and require an empty final listing.
        for attempt in range(6):
            async for sandbox in client.list(query, request_timeout=30):
                if sandbox.labels.get("edot.study") != plan["study_id"]:
                    continue
                try:
                    await sandbox.delete(timeout=60, wait=True)
                except DaytonaNotFoundError:
                    pass
                except DaytonaConflictError:
                    continue
                if sandbox.id not in deleted:
                    deleted.append(sandbox.id)
            remaining = [
                sandbox.id
                async for sandbox in client.list(query, request_timeout=30)
                if sandbox.labels.get("edot.study") == plan["study_id"]
            ]
            if not remaining:
                break
            if attempt < 5:
                await asyncio.sleep(2)
        if remaining:
            raise RuntimeError(f"Study sandboxes remain after cleanup: {remaining}")
        status = "verified_empty"
    finally:
        try:
            write_json(
                root / "cloud-cleanup.json",
                {
                    "status": status,
                    "deleted": deleted,
                    "remaining": remaining,
                },
            )
        finally:
            await client.close()


async def execute(root, plan, max_total_cost):
    """Bounded worker pool, no retries and no reuse of conversations."""
    if not finite_number(max_total_cost, low=0) or max_total_cost <= 0:
        raise ValueError("Cost stop threshold must be a positive finite number")
    preflight(root, plan)
    if (root / "trials").exists():
        raise ValueError("Trial output already exists; prepare a new comparison")
    # Exclusive creation prevents rerunning a partially billed comparison.
    with (root / "execution.json").open("x") as stream:
        json.dump({"max_total_cost_usd": max_total_cost, "state": "started"}, stream)
    spent = 0.0
    state = "completed"
    concurrency = plan.get("concurrency", 1)
    pending = iter(plan["trials"])

    async def worker():
        nonlocal spent, state
        while state == "completed":
            trial = next(pending, None)
            if trial is None:
                break
            if spent >= max_total_cost:
                state = "cost_threshold_reached"
                break
            verify_frozen(root, plan)
            print(f"Running {trial['id']}", flush=True)
            (root / "trials" / trial["id"]).mkdir(parents=True)
            await run_trial(root, plan, trial)
            row = collect_trial(root, trial)
            spent += row["cost_usd"] or 0
            if row["cost_usd"] is None:
                state = "stopped_unknown_cost"

    try:
        async with asyncio.TaskGroup() as group:
            for _ in range(concurrency):
                group.create_task(worker())
    except BaseException:
        state = "interrupted_or_failed"
        raise
    finally:
        try:
            rows = [collect_trial(root, trial) for trial in plan["trials"]]
            # Include calls made by a cancelled trial when Harbor saved its usage.
            spent = sum(row["cost_usd"] or 0 for row in rows)
            write_json(
                root / "execution.json",
                {
                    "max_total_cost_usd": max_total_cost,
                    "state": state,
                    "observed_cost_usd": spent,
                    "cost_scope": "reported model API usage only; excludes cloud hosting",
                    "unknown_cost_trials": [
                        row["id"]
                        for row in rows
                        if row["status"] != "not_run" and row["cost_usd"] is None
                    ],
                },
            )
            summarize(root, plan)
        finally:
            # Reporting can fail (for example, on a full controller disk).
            # Resource deletion must still run and surface any cleanup failure.
            if plan.get("environment", {}).get("type") == "daytona":
                await cleanup_daytona(root, plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Freeze inputs without calling an API")
    prep.add_argument("--task", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--model", required=True)
    prep.add_argument("--pairs", type=int, default=2)
    prep.add_argument("--max-turns", type=int, default=30)
    prep.add_argument("--agent-seconds", type=int, default=1800)
    prep.add_argument("--backend", choices=("docker", "daytona"), default="docker")
    prep.add_argument("--concurrency", type=int, default=1)
    prep.add_argument("--cpus", type=int)
    prep.add_argument("--memory-gb", type=int)
    prep.add_argument("--storage-gb", type=int)
    worker = sub.add_parser("_trial", help=argparse.SUPPRESS)
    worker.add_argument("directory", type=Path)
    worker.add_argument("trial_id")
    worker.add_argument("--allow-paid", action="store_true", required=True)
    for command in ("check", "run", "summarize"):
        cmd = sub.add_parser(command)
        cmd.add_argument("directory", type=Path)
        if command == "run":
            cmd.add_argument("--allow-paid", action="store_true", required=True)
            cmd.add_argument("--max-total-cost-usd", type=float, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            plan = prepare(
                args.task,
                args.output,
                args.model,
                args.pairs,
                args.max_turns,
                args.agent_seconds,
                backend=args.backend,
                concurrency=args.concurrency,
                cpus=args.cpus,
                memory_gb=args.memory_gb,
                storage_gb=args.storage_gb,
            )
            print(f"Prepared {len(plan['trials'])} trials; no API calls made.")
            return
        root = args.directory.resolve()
        plan = read_json(root / "plan.json")
        if args.command == "_trial":
            verify_frozen(root, plan)
            trial = next(t for t in plan["trials"] if t["id"] == args.trial_id)
            directory = root / "trials" / trial["id"]
            with (directory / "worker-started.json").open("x") as stream:
                json.dump({"pid": os.getpid()}, stream)
            asyncio.run(harbor_trial(root, plan, trial))
        elif args.command == "check":
            preflight(root, plan)
            print("Preflight passed; cloud quota and model/API access not tested.")
        elif args.command == "run":
            asyncio.run(execute(root, plan, args.max_total_cost_usd))
        else:
            print(json.dumps(summarize(root, plan), indent=2))
    except (
        ValueError,
        OSError,
        importlib.metadata.PackageNotFoundError,
        subprocess.SubprocessError,
    ) as exc:
        # Preserve chained failures, including a deletion error followed by a
        # full-disk error while saving the cleanup report.
        traceback.print_exception(exc)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
