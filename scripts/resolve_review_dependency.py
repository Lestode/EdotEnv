"""Read the supported reviewer checkout from untrusted workflow YAML as data."""

import re
import sys

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys rather than silently selecting one."""

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, (str, bool)) or key in result:
                raise ValueError("Duplicate or unsupported mapping key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def resolve(source: str) -> str:
    if len(source.encode()) > 20000:
        raise ValueError("Oversized workflow")
    # Unsupported aliases/tags must not disguise a checkout or expand input size.
    if any(
        isinstance(token, (yaml.AliasToken, yaml.AnchorToken, yaml.TagToken))
        for token in yaml.scan(source)
    ):
        raise ValueError("Unsupported YAML alias or tag")
    workflow = yaml.load(source, Loader=UniqueLoader)
    steps = workflow["jobs"]["review"]["steps"]
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise ValueError("Unsupported steps")
    candidates = [
        step
        for step in steps
        if step.get("name") == "Fetch the pinned private reviewer"
    ]
    if len(candidates) != 1:
        raise ValueError("Ambiguous checkout")
    step = candidates[0]
    expected_step = {
        "name": "Fetch the pinned private reviewer",
        "id": "shared_reviewer",
        "uses": "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    }
    if set(step) != {*expected_step, "with"} or any(
        step.get(key) != value for key, value in expected_step.items()
    ):
        raise ValueError("Unsupported checkout action")
    inputs = step["with"]
    expected_inputs = {
        "repository": "Lestode/review-agents",
        "path": ".review-agent",
        "ssh-key": "${{ secrets.REVIEW_AGENTS_READ_KEY }}",
        "persist-credentials": False,
    }
    if (
        not isinstance(inputs, dict)
        or set(inputs) != {*expected_inputs, "ref"}
        or any(inputs.get(key) != value for key, value in expected_inputs.items())
        or inputs.get("persist-credentials") is not False
        or not isinstance(inputs.get("ref"), str)
        or not re.fullmatch(r"[a-f0-9]{40}", inputs["ref"])
    ):
        raise ValueError("Unsupported checkout inputs")
    for other in steps:
        if other is step:
            continue
        if other.get("id") == "shared_reviewer" or (
            isinstance(other.get("with"), dict)
            and other["with"].get("path") == ".review-agent"
        ):
            raise ValueError("Ambiguous reviewer checkout destination")
    return inputs["ref"]


if __name__ == "__main__":
    try:
        print(resolve(sys.stdin.buffer.read(20001).decode()))
    except (yaml.YAMLError, ValueError, TypeError, KeyError, AttributeError):
        sys.exit("Unsupported or ambiguous reviewer checkout workflow.")
