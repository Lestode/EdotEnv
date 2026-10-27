"""Wait for the dedicated two-node Ray cluster before allocating model roles."""

import os
import time


def main():
    import ray

    # Cold Apptainer startup plus native-kernel probes can exceed three minutes.
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        try:
            ray.init(address=os.environ["RAY_ADDRESS"], logging_level="ERROR")
            break
        except ConnectionError:
            time.sleep(2)
    else:
        raise TimeoutError("Ray head did not become ready")
    try:
        while time.monotonic() < deadline:
            nodes = [node for node in ray.nodes() if node["Alive"]]
            if len(nodes) == int(os.environ.get("DISTILLATION_NODES", "2")) and all(
                node["Resources"].get("GPU") == 4 for node in nodes
            ):
                return
            time.sleep(2)
        raise TimeoutError("Expected requested Ray node count with four GPUs each")
    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
