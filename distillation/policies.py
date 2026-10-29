"""Serving-publication policy adapters; no model or framework imports."""

import logging
import time


class DrainBeforePublication:
    """Keep Slime's producer API, but finish active work before any pause returns."""

    def pause(self, *, drain=True):
        start = time.monotonic()
        was_paused = super().pause(drain=True)
        logging.getLogger(__name__).info(
            "distillation condition B: drained producer before publication in %.3fs",
            time.monotonic() - start,
        )
        return was_paused
