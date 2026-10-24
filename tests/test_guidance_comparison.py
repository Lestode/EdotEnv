"""Offline regression tests: no market data, Docker, credentials, or API calls."""

import asyncio
from builtins import ExceptionGroup
import copy
import errno
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

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
        self.assertEqual(
            config_a.pop("extra_instruction_paths"),
            [str(self.root / "runtime-limits.md")],
        )
        self.assertEqual(
            config_b.pop("extra_instruction_paths"),
            [str(self.root / "guidance.md"), str(self.root / "runtime-limits.md")],
        )
        config_a.pop("trial_name")
        config_b.pop("trial_name")
        self.assertEqual(config_a, config_b)
        self.assertNotIn("mounts", config_a["environment"])

    def test_runtime_limits_match_enforced_settings_and_reject_drift(self):
        other = self.base / "different-limits"
        plan = comparison.prepare(
            self.source,
            other,
            "openai/test-model",
            turns=12,
            seconds=420,
            cpus=4,
            memory_gb=8,
            storage_gb=10,
        )
        notice = (other / "runtime-limits.md").read_text()
        config = comparison.trial_config(other, plan, plan["trials"][0])
        self.assertIn(
            f"Maximum agent turns: {config['agent']['kwargs']['max_turns']}", notice
        )
        self.assertIn(
            f"time limit: {config['agent']['override_timeout_sec']} seconds (7 minutes)",
            notice,
        )
        self.assertIn("output tokens per model response: 4096", notice)
        self.assertIn("sandbox CPUs: 4", notice)
        self.assertIn("sandbox memory in MiB: 8192", notice)
        self.assertIn("sandbox storage in MiB: 10240", notice)
        comparison.verify_frozen(other, plan)
        for field, value in (("max_turns", 13), ("agent_seconds", 600)):
            changed = copy.deepcopy(plan)
            changed[field] = value
            with self.assertRaisesRegex(ValueError, "Runtime limits"):
                comparison.verify_frozen(other, changed)
        changed = copy.deepcopy(plan)
        changed["environment"]["override_memory_mb"] = 16384
        with self.assertRaisesRegex(ValueError, "Runtime limits"):
            comparison.verify_frozen(other, changed)
        (other / "runtime-limits.md").write_text("Incorrect execution budget")
        with self.assertRaisesRegex(ValueError, "Runtime limits"):
            comparison.verify_frozen(other, plan)

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
            with self.assertRaises(ExceptionGroup):
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
            {"backend": "unknown"},
            {"concurrency": 0},
            {"concurrency": 5},
            {"memory_gb": 0},
        ):
            args = {
                "source": self.source,
                "destination": self.base / "bad",
                "model": "openai/test-model",
                **kwargs,
            }
            with self.assertRaises(ValueError):
                comparison.prepare(**args)

    def test_cloud_arms_share_resources_and_only_study_cleanup_label(self):
        plan = comparison.prepare(
            self.source,
            self.base / "cloud",
            "openai/test-model",
            backend="daytona",
            concurrency=2,
            cpus=4,
            memory_gb=8,
            storage_gb=20,
        )
        config = comparison.trial_config(self.root, plan, plan["trials"][0])
        self.assertEqual(config["environment"]["type"], "daytona")
        self.assertEqual(config["environment"]["override_memory_mb"], 8192)
        self.assertEqual(
            config["environment"]["kwargs"]["labels"], {"edot.study": plan["study_id"]}
        )
        self.assertTrue(config["environment"]["delete"])
        from harbor.models.trial.config import TrialConfig

        TrialConfig.model_validate(config)

    def test_concurrent_pool_overlaps_and_cost_stops_next_launch(self):
        self.plan["concurrency"] = 2
        active, peak = 0, 0

        async def fake_trial(root, plan, trial):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            self.result(trial, cost=0.15)
            active -= 1

        with (
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=fake_trial) as run,
        ):
            asyncio.run(comparison.execute(self.root, self.plan, 0.1))
        self.assertEqual(peak, 2)
        self.assertEqual(run.call_count, 2)
        execution = comparison.read_json(self.root / "execution.json")
        self.assertEqual(execution["state"], "cost_threshold_reached")
        self.assertAlmostEqual(execution["observed_cost_usd"], 0.3)

    def test_pool_reuses_first_available_slot_without_waiting_for_slow_trial(self):
        self.plan["concurrency"] = 2
        overlap = []

        async def exercise():
            release = asyncio.Event()

            async def fake_trial(root, plan, trial):
                if trial == plan["trials"][0]:
                    await release.wait()
                elif trial == plan["trials"][2]:
                    overlap.append(not release.is_set())
                    release.set()
                self.result(trial, cost=0.01)

            with (
                patch.object(comparison, "preflight"),
                patch.object(comparison, "run_trial", side_effect=fake_trial),
            ):
                await comparison.execute(self.root, self.plan, 1)

        asyncio.run(exercise())
        self.assertEqual(overlap, [True])
        self.assertEqual(
            comparison.read_json(self.root / "execution.json")["state"], "completed"
        )

    def test_failed_cloud_trial_cleans_up_and_counts_cancelled_usage(self):
        self.plan["environment"] = {"type": "daytona", "delete": True}

        async def fail(root, plan, trial):
            self.result(trial, cost=0.03, exception="CancelledError")
            raise RuntimeError("failed")

        with (
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=fail),
            patch.object(
                comparison, "cleanup_daytona", new_callable=AsyncMock
            ) as cleanup,
        ):
            with self.assertRaises(ExceptionGroup):
                asyncio.run(comparison.execute(self.root, self.plan, 1))
        cleanup.assert_awaited_once_with(self.root, self.plan)
        execution = comparison.read_json(self.root / "execution.json")
        self.assertAlmostEqual(execution["observed_cost_usd"], 0.03)

    def test_reporting_write_failures_still_clean_up_cloud_resources(self):
        open_path = Path.open
        for filename in ("execution.json", "summary.json", "summary.md", "scores.csv"):
            for trial_fails in (False, True):
                with self.subTest(filename=filename, trial_fails=trial_fails):
                    self.root = self.base / f"{filename}-{trial_fails}"
                    plan = comparison.prepare(
                        self.source, self.root, "openai/test-model", backend="daytona"
                    )
                    failed_path = self.root / filename

                    def fail_report(path, mode="r", *args, **kwargs):
                        # Allow the initial exclusive execution marker and trial
                        # artifacts; fail the real final report write only.
                        if path == failed_path and mode == "w":
                            raise OSError(errno.ENOSPC, "No space left", str(path))
                        return open_path(path, mode, *args, **kwargs)

                    async def fake_trial(root, plan, trial):
                        self.result(trial, cost=0.03)
                        if trial_fails:
                            raise RuntimeError("trial failed")

                    with (
                        patch.object(comparison, "preflight"),
                        patch.object(comparison, "run_trial", side_effect=fake_trial),
                        patch.object(Path, "open", new=fail_report),
                        patch.object(
                            comparison, "cleanup_daytona", new_callable=AsyncMock
                        ) as cleanup,
                    ):
                        with self.assertRaises(OSError) as raised:
                            asyncio.run(comparison.execute(self.root, plan, 0.01))
                    self.assertEqual(raised.exception.errno, errno.ENOSPC)
                    self.assertEqual(raised.exception.filename, str(failed_path))
                    if trial_fails:
                        self.assertIsInstance(
                            raised.exception.__context__, ExceptionGroup
                        )
                    cleanup.assert_awaited_once_with(self.root, plan)

    def test_final_result_collection_failure_still_cleans_up_cloud_resources(self):
        self.plan["environment"] = {"type": "daytona", "delete": True}
        collect_trial = comparison.collect_trial
        calls = 0

        def fail_final_collection(root, trial):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise OSError(errno.EIO, "Cannot read trial artifacts")
            return collect_trial(root, trial)

        async def fake_trial(root, plan, trial):
            self.result(trial, cost=0.03)

        with (
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=fake_trial),
            patch.object(
                comparison, "collect_trial", side_effect=fail_final_collection
            ),
            patch.object(
                comparison, "cleanup_daytona", new_callable=AsyncMock
            ) as cleanup,
        ):
            with self.assertRaisesRegex(OSError, "Cannot read trial artifacts"):
                asyncio.run(comparison.execute(self.root, self.plan, 0.01))
        cleanup.assert_awaited_once_with(self.root, self.plan)

    def test_cleanup_report_failure_still_closes_client_after_deletion(self):
        from types import SimpleNamespace

        sandbox = SimpleNamespace(
            id="owned-sandbox",
            delete=AsyncMock(),
            labels={"edot.study": self.plan["study_id"]},
        )
        calls = 0

        async def listed(query, request_timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield sandbox

        client = SimpleNamespace(list=listed, close=AsyncMock())
        with (
            patch("daytona.AsyncDaytona", return_value=client),
            patch.object(
                comparison,
                "write_json",
                side_effect=OSError(errno.ENOSPC, "No space left"),
            ),
        ):
            with self.assertRaises(OSError):
                asyncio.run(comparison.cleanup_daytona(self.root, self.plan))
        sandbox.delete.assert_awaited_once_with(timeout=60, wait=True)
        self.assertEqual(calls, 2)
        client.close.assert_awaited_once()

    def test_command_shows_deletion_failure_when_cleanup_report_also_fails(self):
        from types import SimpleNamespace

        self.plan["environment"] = {"type": "daytona", "delete": True}
        comparison.write_json(self.root / "plan.json", self.plan)
        sandbox = SimpleNamespace(
            id="owned-sandbox",
            labels={"edot.study": self.plan["study_id"]},
            delete=AsyncMock(side_effect=RuntimeError("sandbox deletion denied")),
        )

        async def listed(query, request_timeout):
            yield sandbox

        async def run_trial(root, plan, trial):
            self.result(trial)

        original_write = comparison.write_json

        def write_unless_cleanup_report(path, value):
            if path.name == "cloud-cleanup.json":
                raise OSError(errno.ENOSPC, "No space left")
            original_write(path, value)

        client = SimpleNamespace(list=listed, close=AsyncMock())
        stderr = io.StringIO()
        with (
            patch("daytona.AsyncDaytona", return_value=client),
            patch.object(comparison, "preflight"),
            patch.object(comparison, "run_trial", side_effect=run_trial),
            patch.object(
                comparison, "write_json", side_effect=write_unless_cleanup_report
            ),
            patch.object(comparison.sys, "stderr", stderr),
            patch.object(
                comparison.sys,
                "argv",
                [
                    str(SCRIPT),
                    "run",
                    str(self.root),
                    "--allow-paid",
                    "--max-total-cost-usd",
                    "0.1",
                ],
            ),
        ):
            with self.assertRaises(SystemExit) as caught:
                comparison.main()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("RuntimeError: sandbox deletion denied", stderr.getvalue())
        self.assertIn("No space left", stderr.getvalue())
        sandbox.delete.assert_awaited_once()
        client.close.assert_awaited_once()

    def test_daytona_cleanup_filters_study_and_verifies_deletion(self):
        from types import SimpleNamespace

        sandbox = SimpleNamespace(
            id="owned-sandbox",
            delete=AsyncMock(),
            labels={"edot.study": self.plan["study_id"]},
        )
        unrelated = SimpleNamespace(
            id="unrelated-sandbox",
            delete=AsyncMock(),
            labels={"edot.study": "other"},
        )
        queries = []

        async def listed(query, request_timeout):
            queries.append(query)
            if len(queries) == 1:
                yield sandbox
            yield unrelated

        client = SimpleNamespace(list=listed, close=AsyncMock())
        with patch("daytona.AsyncDaytona", return_value=client):
            asyncio.run(comparison.cleanup_daytona(self.root, self.plan))
        self.assertEqual(len(queries), 2)
        self.assertTrue(
            all(q.labels == {"edot.study": self.plan["study_id"]} for q in queries)
        )
        sandbox.delete.assert_awaited_once_with(timeout=60, wait=True)
        unrelated.delete.assert_not_awaited()
        client.close.assert_awaited_once()
        report = comparison.read_json(self.root / "cloud-cleanup.json")
        self.assertEqual(report["status"], "verified_empty")
        self.assertEqual(report["deleted"], ["owned-sandbox"])

    def test_daytona_cleanup_tolerates_already_deleted_sandbox(self):
        from types import SimpleNamespace
        from daytona.common.errors import DaytonaNotFoundError

        sandbox = SimpleNamespace(
            id="deleted-sandbox",
            labels={"edot.study": self.plan["study_id"]},
            delete=AsyncMock(side_effect=DaytonaNotFoundError("already deleted")),
        )
        calls = 0

        async def listed(query, request_timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield sandbox

        client = SimpleNamespace(list=listed, close=AsyncMock())
        with patch("daytona.AsyncDaytona", return_value=client):
            asyncio.run(comparison.cleanup_daytona(self.root, self.plan))
        report = comparison.read_json(self.root / "cloud-cleanup.json")
        self.assertEqual(report["status"], "verified_empty")

    def test_cancelled_cloud_worker_is_reaped_before_study_cleanup(self):
        from types import SimpleNamespace

        self.plan["environment"] = {"type": "daytona", "delete": True}
        trial = self.plan["trials"][0]
        (self.root / "trials" / trial["id"]).mkdir(parents=True)
        process = SimpleNamespace(
            returncode=None,
            send_signal=Mock(),
            kill=Mock(),
            wait=AsyncMock(side_effect=[asyncio.CancelledError(), TimeoutError(), 0]),
        )
        with patch.object(
            asyncio, "create_subprocess_exec", return_value=process
        ) as spawn:
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(comparison.run_trial(self.root, self.plan, trial))
        process.send_signal.assert_called_once_with(comparison.signal.SIGINT)
        process.kill.assert_called_once()
        self.assertEqual(process.wait.await_count, 3)
        self.assertIn("--allow-paid", spawn.call_args.args)

    def test_daytona_cleanup_retries_conflicting_state_transition(self):
        from types import SimpleNamespace
        from daytona.common.errors import DaytonaConflictError

        sandbox = SimpleNamespace(
            id="transitioning-sandbox",
            labels={"edot.study": self.plan["study_id"]},
            delete=AsyncMock(
                side_effect=[DaytonaConflictError("state change in progress"), None]
            ),
        )
        calls = 0

        async def listed(query, request_timeout):
            nonlocal calls
            calls += 1
            if calls <= 3:
                yield sandbox

        client = SimpleNamespace(list=listed, close=AsyncMock())
        with (
            patch("daytona.AsyncDaytona", return_value=client),
            patch.object(asyncio, "sleep", new_callable=AsyncMock),
        ):
            asyncio.run(comparison.cleanup_daytona(self.root, self.plan))
        self.assertEqual(sandbox.delete.await_count, 2)
        report = comparison.read_json(self.root / "cloud-cleanup.json")
        self.assertEqual(report["status"], "verified_empty")

    def test_daytona_cleanup_cannot_pass_while_owned_resource_remains(self):
        from types import SimpleNamespace
        from daytona.common.errors import DaytonaConflictError

        sandbox = SimpleNamespace(
            id="stuck-sandbox",
            labels={"edot.study": self.plan["study_id"]},
            delete=AsyncMock(side_effect=DaytonaConflictError("still transitioning")),
        )

        async def listed(query, request_timeout):
            yield sandbox

        client = SimpleNamespace(list=listed, close=AsyncMock())
        with (
            patch("daytona.AsyncDaytona", return_value=client),
            patch.object(asyncio, "sleep", new_callable=AsyncMock),
        ):
            with self.assertRaisesRegex(RuntimeError, "sandboxes remain"):
                asyncio.run(comparison.cleanup_daytona(self.root, self.plan))
        client.close.assert_awaited_once()
        report = comparison.read_json(self.root / "cloud-cleanup.json")
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["remaining"], ["stuck-sandbox"])

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
        limits = (self.root / "runtime-limits.md").read_text()
        self.assertEqual(task_a.instruction, "ORIGINAL TASK\n\n" + limits)
        self.assertEqual(
            task_b.instruction,
            "ORIGINAL TASK\n\n"
            + (self.root / "guidance.md").read_text()
            + "\n\n"
            + limits,
        )
        self.assertEqual(task_a.config, task_b.config)
        self.assertEqual(copy.deepcopy(config_a.agent), config_b.agent)

    def test_harbor_initial_prompts_disclose_override_to_both_arms(self):
        try:
            from harbor.agents.terminus_2.terminus_2 import Terminus2
            from harbor.models.task.task import Task
            from harbor.models.trial.config import TrialConfig
        except ImportError:
            self.skipTest("Optional Harbor dependency is not installed")

        original = "ORIGINAL TASK\nYou have 4 hours of wall-clock time."
        (self.source / "instruction.md").write_text(original)
        root = self.base / "prompt-check"
        plan = comparison.prepare(self.source, root, "openai/test-model")
        # Exercise Harbor's actual prompt template without constructing an LLM,
        # starting an environment, or making an API call.
        agent = object.__new__(Terminus2)
        agent._parser_name = "json"
        template = agent._get_prompt_template_path().read_text()
        prompts = {}
        for trial in plan["trials"][:2]:
            config = TrialConfig.model_validate(
                comparison.trial_config(root, plan, trial)
            )
            task = Task(
                config.task.path, extra_instruction_paths=config.extra_instruction_paths
            )
            prompt = template.format(
                instruction=task.instruction, terminal_state="/app$"
            )
            prompts[trial["arm"]] = prompt
            self.assertIn("Maximum agent turns: 30", prompt)
            self.assertIn("1800 seconds (30 minutes)", prompt)
            self.assertIn("override any different time or turn allowance", prompt)
            self.assertGreater(
                prompt.index("# Actual execution limits"),
                prompt.index("You have 4 hours"),
            )
            self.assertNotIn("HIDDEN", prompt)
            self.assertNotIn("ORACLE", prompt)
        guidance = (root / "guidance.md").read_text()
        self.assertEqual(prompts["B"].replace(guidance + "\n\n", ""), prompts["A"])
        self.assertEqual((root / "task/instruction.md").read_text(), original)

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
