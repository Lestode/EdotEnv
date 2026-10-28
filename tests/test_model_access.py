"""Regression coverage for reused model snapshots and inaccessible shards."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from distillation.model_access import check_access


class ModelAccessTests(unittest.TestCase):
    @patch("distillation.model_access.verify_models")
    def test_external_snapshot_and_missing_shard(self, verify):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "old"
            old.mkdir()
            models = root / "models"
            models.mkdir()
            student = models / "student"
            student.symlink_to(old, target_is_directory=True)
            teacher = models / "teacher"
            teacher.mkdir()
            (old / "model.safetensors").write_bytes(b"weights")
            (teacher / "model.safetensors.index.json").write_text(
                json.dumps({"weight_map": {"weight": "shard.safetensors"}})
            )
            shard = teacher / "shard.safetensors"
            shard.write_bytes(b"weights")
            self.assertEqual(
                check_access(student, teacher, "7b32b")["model_access"], "passed"
            )
            self.assertEqual(verify.call_args.args[2].name, "models-7b32b.json")
            shard.unlink()
            with self.assertRaises(FileNotFoundError):
                check_access(student, teacher, "7b32b")
            shard.touch()
            with self.assertRaisesRegex(ValueError, "Empty weight"):
                check_access(student, teacher, "7b32b")
