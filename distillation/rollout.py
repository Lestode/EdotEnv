"""Condition B using the pinned Slime producer and custom rollout hook."""

from slime.rollout.fully_async_rollout import AsyncRolloutWorker
from slime.utils.http_utils import get_rollout_num_engines

from distillation.policies import DrainBeforePublication


class CompleteResponseWorker(DrainBeforePublication, AsyncRolloutWorker):
    """A Slime worker whose admission pause also completes active responses."""


def ensure_complete_response_worker(args, data_source):
    if args.rollout_data_transport != "object-store" or hasattr(
        data_source, "reader_config"
    ):
        raise ValueError(
            "Condition B currently supports the object-store data source only"
        )
    worker = data_source.consumers.get("fully_async")
    if worker is None:
        worker = CompleteResponseWorker(
            args,
            data_source,
            concurrency=args.sglang_server_concurrency * get_rollout_num_engines(args),
        )
        data_source.register_consumer("fully_async", worker)
        worker.start()
    elif not isinstance(worker, CompleteResponseWorker):
        raise ValueError("Condition B found a producer without draining enforcement")
