"""Historical exports retain numerical evidence without rollout text."""

import tempfile
import unittest
from pathlib import Path

from distillation.tracking_export import collect


class TrackingExportTests(unittest.TestCase):
    def test_filter_merge_and_gpu_units(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / "train").mkdir()
            (run / "train/train.log").write_text(
                "step 0: {'train/loss': -0.2, 'prompt': 'PRIVATE', 'train/text': 'PRIVATE'}\n"
                "perf 0: {'perf/train_time': 3.0}\n"
                "step 1: malformed\n"
            )
            (run / "gpu-0.csv").write_text(
                "timestamp, uuid, index, memory.used [MiB]\n"
                "2026/10/28 12:00:00, PRIVATE-ID, 0, 1024 MiB\n"
            )
            result = collect(run)
        self.assertEqual(
            result["metrics"],
            [{"source_step": 0, "train/loss": -0.2, "perf/train_time": 3.0}],
        )
        self.assertEqual(result["gpu_samples"][0]["memory.used [MiB]"], 1024)
        self.assertNotIn("PRIVATE", repr(result))
