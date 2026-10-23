"""Check project Markdown links and the documentation review entry points."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


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

    config = json.loads((root / ".github/documentation-review.json").read_text())
    expected = {
        "documentationIndex": "docs/README.md",
        "instructionsPath": ".github/documentation-review.md",
        "command": "/review-docs",
        "markerPrefix": "edotenv-documentation-review",
    }
    if config != expected:
        errors.append(
            "Review configuration changed; update validation and workflow together."
        )
    for field in ("documentationIndex", "instructionsPath"):
        if not (root / config[field]).is_file():
            errors.append(f"Missing review entry point: {config[field]}")
    return errors


if __name__ == "__main__":
    failures = check_project(ROOT)
    if failures:
        raise SystemExit("\n".join(failures))
    print("Project documentation links and review configuration are valid.")
