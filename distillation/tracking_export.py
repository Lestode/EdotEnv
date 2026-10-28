"""Export numeric pilot metrics; optionally upload a historical W&B run.

Does not upload prompts, responses, raw logs, or checkpoint payloads.
Historical imports are distinct from native live Slime tracking.
"""

import argparse
import ast
import csv
import json
import math
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")
METRIC = re.compile(r"(?:step|rollout|perf) (\d+): (\{.*\})")
PREFIXES = ("train/", "rollout/", "perf/", "eval/")


def collect(run_dir):
    rows = {}
    log = run_dir / "train" / "train.log"
    if log.exists():
        for line in log.read_text(errors="replace").splitlines():
            match = METRIC.search(ANSI.sub("", line))
            if not match:
                continue
            try:
                values = ast.literal_eval(match[2])
            except (ValueError, SyntaxError):
                continue
            if not isinstance(values, dict):
                continue
            numeric = {
                key: value
                for key, value in values.items()
                if isinstance(key, str)
                and key.startswith(PREFIXES)
                and isinstance(value, (int, float))
                and math.isfinite(value)
            }
            rows.setdefault(int(match[1]), {}).update(numeric)
    gpu = []
    for path in sorted(run_dir.glob("gpu-*.csv")):
        with path.open() as handle:
            for row in csv.DictReader(handle):
                entry = {"node_index": path.stem.removeprefix("gpu-")}
                for key, value in row.items():
                    if key is None or value is None:
                        continue
                    key, value = key.strip(), value.strip()
                    if key == "timestamp":
                        entry[key] = value
                    elif key != "uuid":
                        try:
                            number = float(value.split()[0])
                        except (ValueError, IndexError):
                            continue
                        if math.isfinite(number):
                            entry[key] = number
                gpu.append(entry)
    return {
        "metrics": [{"source_step": k, **v} for k, v in sorted(rows.items())],
        "gpu_samples": gpu,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project")
    parser.add_argument("--entity")
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    data = collect(args.run_dir)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    if not args.upload:
        return
    if not args.project or not args.entity:
        parser.error("Upload requires an explicit W&B project and entity")
    import wandb

    with wandb.init(
        entity=args.entity,
        project=args.project,
        name=args.run_dir.name + "-historical",
        job_type="historical-import",
        tags=["historical", "execution-validation"],
        config={"source_attempt": args.run_dir.name, "live_tracking": False},
    ) as run:
        run.define_metric("source_step")
        for prefix in PREFIXES:
            run.define_metric(prefix + "*", step_metric="source_step")
        for row in data["metrics"]:
            run.log(row)
        if data["gpu_samples"]:
            columns = sorted({k for row in data["gpu_samples"] for k in row})
            run.log(
                {
                    "gpu_samples": wandb.Table(
                        columns=columns,
                        data=[
                            [row.get(k) for k in columns] for row in data["gpu_samples"]
                        ],
                    )
                }
            )
        run.summary["recorded_metric_steps"] = len(data["metrics"])
        run.summary["completed_update_records"] = sum(
            "train/loss" in row for row in data["metrics"]
        )
        print(run.url)


if __name__ == "__main__":
    main()
