"""Offline regression tests: no market data, Docker, credentials, or API calls."""

import asyncio
import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/verifier-context/compare.py"
SPEC = importlib.util.spec_from_file_location("comparison", SCRIPT)
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        for name in ("environment", "tests", "solution"):
            (self.source / name).mkdir()
        (self.source / "task.toml").write_text('schema_version = "1.3"\n')
        (self.source / "instruction.md").write_text("ORIGINAL TASK")
        (self.source / "environment/public.txt").write_text("PUBLIC")
        (self.source / "tests/hidden.txt").write_text("HIDDEN")
        (self.source / "tests/test.sh").write_text("true\n")
        (self.source / "solution/solve.py").write_text("ORACLE")
        self.root = self.base / "run"
        self.plan = comparison.prepare(self.source, self.root, "openai/test-model")

    def result(self, trial, score=0.4, accepted=True, cost=0.1, exception=None):
        directory = self.root / "trials" / trial["id"]
        (directory / "verifier").mkdir(parents=True, exist_ok=True)
        comparison.write_json(
            directory / "result.json",
            {
                "agent_result": {"cost_usd": cost},
                "exception_info": {"exception_type": exception} if exception else None,
            },
        )
        metrics = {"weighted_pearson_ic": score}
        comparison.write_json(
            directory / "verifier/metrics.json",
            {
                "ok": accepted,
                "primary_score": score,
                "metrics": metrics,
                "error_code": None if accepted else "missing_submission",
            },
        )
        comparison.write_json(
            directory / "verifier/reward.json",
            {
                "primary_score": score,
                **metrics,
            },
        )

    def test_original_task_and_verifier_preserved_oracle_excluded(self):
        self.assertFalse((self.root / "task/solution").exists())
        self.assertEqual(
            (self.root / "task/instruction.md").read_text(), "ORIGINAL TASK"
        )
        self.assertEqual((self.root / "task/tests/hidden.txt").read_text(), "HIDDEN")
        self.assertFalse((self.root / "task/environment/guidance.md").exists())
        comparison.verify_frozen(self.root, self.plan)

    def test_only_treatment_input_differs_and_order_is_counterbalanced(self):
        a, b, b2, a2 = self.plan["trials"]
        self.assertEqual([t["arm"] for t in (a, b, b2, a2)], ["A", "B", "B", "A"])
        config_a = comparison.trial_config(self.root, self.plan, a)
        config_b = comparison.trial_config(self.root, self.plan, b)
        self.assertEqual(config_a.pop("extra_instruction_paths"), [])
        self.assertEqual(
            config_b.pop("extra_instruction_paths"), [str(self.root / "guidance.md")]
        )
        config_a.pop("trial_name")
        config_b.pop("trial_name")
        self.assertEqual(config_a, config_b)
        self.assertNotIn("mounts", config_a["environment"])

    def test_separate_studies_use_different_container_session_names(self):
        other = comparison.prepare(
            self.source, self.base / "another", "openai/test-model"
        )
        self.assertTrue(
            {t["id"] for t in self.plan["trials"]}.isdisjoint(
                t["id"] for t in other["trials"]
            )
        )

    def test_task_or_guidance_change_is_rejected(self):
        (self.root / "guidance.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "Guidance changed"):
            comparison.verify_frozen(self.root, self.plan)
        self.plan["guidance_sha256"] = comparison.digest(self.root / "guidance.md")
        (self.root / "task/tests/hidden.txt").write_text("changed")
        with self.assertRaisesRegex(ValueError, "Task changed"):
            comparison.verify_frozen(self.root, self.plan)

    def test_preparation_refuses_overwrite_nested_output_and_links(self):
        for destination in (self.root, self.source / "run"):
            with self.assertRaises((FileExistsError, ValueError)):
                comparison.prepare(self.source, destination, "openai/test-model")
        (self.source / "environment/link").symlink_to(self.source / "solution")
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            comparison.prepare(self.source, self.base / "other", "openai/test-model")

    def test_zero_and_negative_ic_retained_penalty_excluded(self):
        a, b, b2, a2 = self.plan["trials"]
        self.result(a, score=0.0)
        self.result(b, score=-0.2)
        self.result(b2, score=-100, accepted=False)
        report = comparison.summarize(self.root, self.plan)
        self.assertEqual(report["arms"]["A"]["accepted_mean_ic"], 0.0)
        self.assertEqual(report["arms"]["B"]["accepted_mean_ic"], -0.2)
        self.assertEqual(report["mean_paired_delta"], -0.2)
        self.assertEqual(report["trials"][2]["status"], "rejected")
        self.assertIsNone(report["trials"][2]["score"])
        self.assertEqual(report["trials"][3]["status"], "not_run")
        self.assertTrue((self.root / "scores.csv").exists())
        self.assertIn(
            "statistical significance", (self.root / "summary.md").read_text()
        )

    def test_corrupt_nonfinite_and_mismatched_scores_are_not_accepted(self):
        trial = self.plan["trials"][0]
        self.result(trial)
        path = self.root / "trials" / trial["id"] / "verifier/reward.json"
        comparison.write_json(path, {"weighted_pearson_ic": 0.8, "primary_score": 0.8})
        self.assertEqual(
            comparison.collect_trial(self.root, trial)["status"], "invalid_score"
        )
        path.write_text('{"weighted_pearson_ic": NaN, "primary_score": NaN}')
        self.assertEqual(
            comparison.collect_trial(self.root, trial)["status"], "invalid_score"
        )
        path.write_text("{")
        self.assertEqual(
            comparison.collect_trial(self.root, trial)["status"], "invalid_output"
        )

    def test_missing_outputs_and_execution_errors_remain_visible(self):
        trial = self.plan["trials"][0]
        self.result(trial, exception="AgentTimeoutError")
        self.assertEqual(
            comparison.collect_trial(self.root, trial)["status"], "accepted"
        )
        (self.root / "trials" / trial["id"] / "verifier/metrics.json").unlink()
        self.assertEqual(
            comparison.collect_trial(self.root, trial)["status"], "execution_error"
        )

    def test_cost_threshold_stops_before_next_trial_and_refuses_repeat(self):
        async def fake_trial(root, plan, trial):
            self.result(trial, cost=0.15)

        with (
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=fake_trial) as run,
        ):
            asyncio.run(comparison.execute(self.root, self.plan, 0.1))
            self.assertEqual(run.call_count, 1)
            self.assertEqual(
                comparison.read_json(self.root / "execution.json")["state"],
                "cost_threshold_reached",
            )
            with self.assertRaises(ValueError):
                asyncio.run(comparison.execute(self.root, self.plan, 0.1))
            self.assertEqual(run.call_count, 1)

    def test_unknown_cost_stops_and_exceptions_write_summary(self):
        async def fake_trial(root, plan, trial):
            self.result(trial, cost=None)

        with (
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=fake_trial) as run,
        ):
            asyncio.run(comparison.execute(self.root, self.plan, 1))
            self.assertEqual(run.call_count, 1)
            self.assertEqual(
                comparison.read_json(self.root / "execution.json")["state"],
                "stopped_unknown_cost",
            )
        other = self.base / "failed"
        plan = comparison.prepare(self.source, other, "openai/test-model")
        with (
            patch.object(comparison, "preflight"),
            patch.object(
                comparison,
                "run_trial",
                new=AsyncMock(side_effect=RuntimeError("failure")),
            ),
        ):
            with self.assertRaises(RuntimeError):
                asyncio.run(comparison.execute(other, plan, 1))
        self.assertTrue((other / "summary.json").exists())
        self.assertEqual(
            comparison.read_json(other / "execution.json")["state"],
            "interrupted_or_failed",
        )

    def test_reject_invalid_settings(self):
        for kwargs in (
            {"pairs": 0},
            {"turns": -1},
            {"seconds": 0},
            {"model": "oracle"},
        ):
            args = {
                "source": self.source,
                "destination": self.base / "bad",
                "model": "openai/test-model",
                **kwargs,
            }
            with self.assertRaises(ValueError):
                comparison.prepare(**args)

    def test_harbor_contract_when_dependency_installed(self):
        try:
            from harbor.models.task.task import Task
            from harbor.models.trial.config import TrialConfig
        except ImportError:
            self.skipTest("Optional Harbor dependency is not installed")
        config_a = TrialConfig.model_validate(
            comparison.trial_config(self.root, self.plan, self.plan["trials"][0])
        )
        config_b = TrialConfig.model_validate(
            comparison.trial_config(self.root, self.plan, self.plan["trials"][1])
        )
        task_a = Task(
            config_a.task.path, extra_instruction_paths=config_a.extra_instruction_paths
        )
        task_b = Task(
            config_b.task.path, extra_instruction_paths=config_b.extra_instruction_paths
        )
        self.assertEqual(task_a.instruction, "ORIGINAL TASK")
        self.assertEqual(
            task_b.instruction,
            task_a.instruction + "\n\n" + (self.root / "guidance.md").read_text(),
        )
        self.assertEqual(task_a.config, task_b.config)
        self.assertEqual(copy.deepcopy(config_a.agent), config_b.agent)

    def test_responses_adapter_reaches_http_boundary_without_network(self):
        # LiteLLM's mock_response shortcut skips MCP dispatch; intercept the
        # HTTP boundary instead so this covers the actual production imports.
        with patch.dict(os.environ, {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}):
            try:
                import litellm
            except ImportError:
                self.skipTest("Optional runner dependencies are not installed")
            import importlib

            responses = importlib.import_module("litellm.responses.main")
            response = responses.mock_responses_api_response("offline-ok")
            response.model = "gpt-6-luna"
            with patch.object(
                responses.base_llm_http_handler,
                "response_api_handler",
                return_value=response,
            ) as handler:
                result = asyncio.run(
                    litellm.aresponses(
                        model="openai/gpt-6-luna",
                        input="Offline adapter check",
                        api_key="offline-placeholder",
                        reasoning={"effort": "low"},
                        max_output_tokens=4096,
                    )
                )
            handler.assert_called_once()
            self.assertEqual(result.output[0].content[0].text, "offline-ok")


if __name__ == "__main__":
    unittest.main()
