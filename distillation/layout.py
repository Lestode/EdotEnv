"""Uniform allocated-GPU layouts supported by the pinned Slime placement code."""

import argparse


def layout(profile, gpus_per_node, nodes=None):
    if profile not in ("smoke", "7b32b"):
        raise ValueError("Unknown distillation profile")
    if gpus_per_node not in (1, 2, 4):
        raise ValueError("Allocated GPUs per node must be 1, 2, or 4")
    total = 12 if profile == "7b32b" else 8
    expected_nodes = total // gpus_per_node
    if nodes is not None and nodes != expected_nodes:
        raise ValueError(
            f"{profile} requires {total} GPUs: expected {expected_nodes} nodes "
            f"with {gpus_per_node} GPUs each, got {nodes}"
        )
    return {
        "nodes": expected_nodes,
        "gpus_per_node": gpus_per_node,
        "total_gpus": total,
        "training_nodes": 4 // gpus_per_node,
    }


def nodes_match(nodes, expected_nodes, gpus_per_node):
    alive = [node for node in nodes if node["Alive"]]
    return len(alive) == expected_nodes and all(
        node["Resources"].get("GPU", 0) == gpus_per_node for node in alive
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "7b32b"), required=True)
    parser.add_argument("--gpus-per-node", type=int, required=True)
    parser.add_argument("--nodes", type=int)
    args = parser.parse_args()
    print(layout(args.profile, args.gpus_per_node, args.nodes)["nodes"])


if __name__ == "__main__":
    main()
