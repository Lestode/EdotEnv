"""Serving-publication policy adapters; no model or framework imports."""

import logging
import time


class DrainBeforePublication:
    """Keep Slime's producer API, but finish active work before any pause returns."""

    def __init__(self, worker):
        self.worker = worker

    def __getattr__(self, name):
        return getattr(self.worker, name)

    def pause(self, *, drain=True):
        start = time.monotonic()
        was_paused = self.worker.pause(drain=True)
        logging.getLogger(__name__).info(
            "distillation condition B: drained producer before publication in %.3fs",
            time.monotonic() - start,
        )
        return was_paused
