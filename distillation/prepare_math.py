"""Prepare disjoint prompt-only training and held-out math development data."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import unicodedata
import urllib.request

REPO = "DigitalLearningGmbH/MATH-lighteval"
REVISION = "0530c78699ea5e8eb5530600900e1f328b48acad"
FILE = "data/train-00000-of-00001.parquet"
SUFFIX = "\nPlease reason step by step and put your final answer within \\boxed{}."


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def normalized(problem):
    return " ".join(unicodedata.normalize("NFKC", problem).split()).casefold()


def split_stratified(rows, count, salt):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["subject"], row["level"])].append(row)
    total = len(rows)
    quotas = {key: count * len(group) // total for key, group in groups.items()}
    order = sorted(groups, key=lambda k: (-(count * len(groups[k]) % total), k))
    for key in order[: count - sum(quotas.values())]:
        quotas[key] += 1
    chosen, remainder = [], []
    for key, group in sorted(groups.items()):
        group.sort(key=lambda row: digest(salt + row["id"]))
        chosen.extend(group[: quotas[key]])
        remainder.extend(group[quotas[key] :])
    return chosen, remainder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--math500", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    raw = args.output / "source-train.parquet"
    urllib.request.urlretrieve(
        f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{FILE}", raw
    )
    import pyarrow.parquet as pq
    from slime.rollout.rm_hub.math_utils import extract_boxed_answer

    evaluation = [json.loads(line) for line in args.math500.read_text().splitlines()]
    if len(evaluation) != 500 or any("problem" not in row for row in evaluation):
        raise ValueError("Overlap exclusion requires all 500 original MATH-500 rows")
    excluded = {normalized(row["problem"]) for row in evaluation}
    source = pq.read_table(raw).to_pylist()
    seen, rows, dropped = set(), [], Counter()
    for item in source:
        problem, solution = item["problem"], item["solution"]
        key = normalized(problem)
        if not key or key in excluded or key in seen:
            dropped["empty_overlap_or_duplicate"] += 1
            continue
        try:
            answer = extract_boxed_answer(solution)
        except (AssertionError, TypeError, ValueError):
            answer = None
        if not answer or not answer.strip():
            dropped["unextractable_answer"] += 1
            continue
        seen.add(key)
        rows.append(
            {
                "id": "math-train-" + digest(key),
                "problem": problem,
                "solution": solution,
                "answer": answer,
                "subject": item["type"],
                "level": item["level"],
            }
        )
    if len(rows) < 3256:
        raise ValueError("Insufficient valid unique rows")
    development, pool = split_stratified(rows, 256, "math-development-v1:")
    train, reserve = split_stratified(pool, 3000, "math-training-v1:")
    sets = [{row["id"] for row in split} for split in (train, development, reserve)]
    assert all(not sets[i] & sets[j] for i in range(3) for j in range(i))
    assert all(normalized(row["problem"]) not in excluded for row in rows)
    outputs = {
        "train.jsonl": [
            {
                "id": row["id"],
                "prompt": [{"role": "user", "content": row["problem"] + SUFFIX}],
            }
            for row in train
        ],
        "train-references.jsonl": train,
        "development.jsonl": [
            {**row, "prompt": [{"role": "user", "content": row["problem"] + SUFFIX}]}
            for row in development
        ],
        "reserve.jsonl": reserve,
    }
    for name, records in outputs.items():
        (args.output / name).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records)
        )
    manifest = {
        "source": {"repo": REPO, "revision": REVISION, "file": FILE},
        "source_rows": len(source),
        "dropped": dict(dropped),
        "splits": {
            "train": len(train),
            "development": len(development),
            "reserve": len(reserve),
        },
        "strata": {
            label: dict(Counter(row["subject"] + " / " + row["level"] for row in split))
            for label, split in [("train", train), ("development", development)]
        },
        "split_method": "proportional subject/level quotas, deterministic salted SHA256 ordering",
        "math500_rows_excluded": len(evaluation),
        "math500_source_sha256": hashlib.sha256(args.math500.read_bytes()).hexdigest(),
        "overlap_normalization": "NFKC, collapse whitespace, casefold; not semantic deduplication",
        "reference_visibility": "train.jsonl contains only id and prompt; answers/solutions stored separately",
        "pretraining_contamination": "unknown; split separation does not establish absence",
        "files_sha256": {
            name: hashlib.sha256((args.output / name).read_bytes()).hexdigest()
            for name in [*outputs, raw.name]
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"splits": manifest["splits"], "dropped": manifest["dropped"]}))


if __name__ == "__main__":
    main()
