"""Guard the independent commands, markers, and accepted reviewer entry points."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_project import ROOT, check_review_configuration


class ReviewConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / ".github").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs/README.md").write_text("Index")
        for reviewer in ("documentation", "implementation"):
            for extension in ("json", "md"):
                name = f".github/{reviewer}-review.{extension}"
                (self.root / name).write_text((ROOT / name).read_text())

    def test_both_accepted_configurations_are_valid(self):
        self.assertEqual(check_review_configuration(self.root), [])

    def test_missing_implementation_configuration_is_not_silently_optional(self):
        (self.root / ".github/implementation-review.json").unlink()
        errors = check_review_configuration(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("implementation-review.json", errors[0])

    def test_implementation_cannot_reuse_documentation_command_or_marker(self):
        path = self.root / ".github/implementation-review.json"
        config = json.loads(path.read_text())
        config.update(
            command="/review-docs", markerPrefix="edotenv-documentation-review"
        )
        path.write_text(json.dumps(config))
        self.assertTrue(check_review_configuration(self.root))

    def test_missing_instructions_or_documentation_index_are_reported(self):
        (self.root / ".github/implementation-review.md").unlink()
        (self.root / "docs/README.md").unlink()
        errors = check_review_configuration(self.root)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("implementation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
