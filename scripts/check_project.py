"""Check project Markdown links and the documentation review entry points."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check_review_configuration(root: Path) -> list[str]:
    errors = []
    for reviewer, command in (
        ("documentation", "/review-docs"),
        ("implementation", "/review-implementation"),
    ):
        path = root / f".github/{reviewer}-review.json"
        expected = {
            "documentationIndex": "docs/README.md",
            "instructionsPath": f".github/{reviewer}-review.md",
            "command": command,
            "markerPrefix": f"edotenv-{reviewer}-review",
        }
        if reviewer == "implementation":
            expected["contextPaths"] = [
                ".github/documentation-review.json",
                ".github/implementation-review.json",
                ".github/review-required-checks.json",
                ".github/workflows/documentation-review.yml",
                ".github/workflows/verify.yml",
                "scripts/check_project.py",
            ]
        try:
            config = json.loads(path.read_text())
        except (OSError, ValueError):
            errors.append(f"Missing or invalid review configuration: {path.name}")
            continue
        if config != expected:
            errors.append(
                f"{reviewer.capitalize()} review configuration changed; "
                "update validation and workflow together."
            )
        for field in ("documentationIndex", "instructionsPath"):
            target = config.get(field) if isinstance(config, dict) else None
            if not isinstance(target, str) or not (root / target).is_file():
                errors.append(f"Missing {reviewer} review entry point: {field}")
    return errors


def check_project(root: Path) -> list[str]:
    errors = []
    documents = [root / "AGENTS.md", *sorted((root / "docs").rglob("*.md"))]
    documents += sorted((root / ".github").rglob("*.md"))
    for document in documents:
        if not document.is_file():
            errors.append(f"Missing document: {document.relative_to(root)}")
            continue
        text = re.sub(r"```.*?```", "", document.read_text(), flags=re.S)
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            path = (document.parent / unquote(url.path)).resolve()
            if not path.is_relative_to(root) or not path.exists():
                errors.append(
                    f"{document.relative_to(root)}: missing local target {target}"
                )

    errors.extend(check_review_configuration(root))
    return errors


if __name__ == "__main__":
    failures = check_project(ROOT)
    if failures:
        raise SystemExit("\n".join(failures))
    print("Project documentation links and review configuration are valid.")
