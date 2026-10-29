"""Wait for the allocated Ray cluster before allocating model roles."""

import os
import time

from distillation.layout import layout, nodes_match


def main():
    import ray

    allocation = layout(
        os.environ.get("DISTILLATION_PROFILE", "smoke"),
        int(os.environ["DISTILLATION_GPUS_PER_NODE"]),
        int(os.environ["DISTILLATION_NODES"]),
    )
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
            if nodes_match(
                ray.nodes(), allocation["nodes"], allocation["gpus_per_node"]
            ):
                return
            time.sleep(2)
        raise TimeoutError(
            "Ray resources do not match the requested uniform allocation"
        )
    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
