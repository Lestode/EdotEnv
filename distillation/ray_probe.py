"""Bounded CPU-only Ray startup and remote-task check on both allocated nodes."""

import json
import os
import time


def main():
    import ray
    from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("Run inside a compute allocation")
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            ray.init(address=os.environ["RAY_ADDRESS"], logging_level="ERROR")
            break
        except ConnectionError:
            time.sleep(2)
    else:
        raise TimeoutError("Ray head did not start")
    try:
        while time.monotonic() < deadline:
            nodes = [node for node in ray.nodes() if node["Alive"]]
            if len(nodes) == 2:
                break
            time.sleep(2)
        else:
            raise TimeoutError("Two Ray nodes did not register")

        @ray.remote
        def hostname():
            import socket

            return socket.gethostname()

        refs = [
            hostname.options(
                scheduling_strategy=NodeAffinitySchedulingStrategy(
                    node["NodeID"], soft=False
                )
            ).remote()
            for node in nodes
        ]
        hosts = ray.get(refs, timeout=30)
        if len(set(hosts)) != 2:
            raise RuntimeError("Tasks did not execute on two distinct nodes")
        print(json.dumps({"status": "passed", "hosts": hosts}), flush=True)
    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
