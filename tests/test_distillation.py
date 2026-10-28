"""CPU checks for project hooks; GPU runtime and learning are separate evidence."""

import argparse
import ast
import asyncio
import copy
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import torch
import yaml
from aiohttp import web

from distillation.hooks import (
    policy_age,
    post_process_rewards,
    response_log_probs,
    score_teacher,
    validate_sample_policy,
)
from distillation.layout import layout, nodes_match
from distillation.launch import ROOT, serving_config, training_args, validate_options
from distillation.policies import DrainBeforePublication
from distillation.preflight import fingerprint, verify_models


class ScoringTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_http_scoring_preserves_input_ids_and_checks_alignment(self):
        async def generate(request):
            payload = await request.json()
            self.assertEqual(payload["input_ids"], [11, 12, 13])
            self.assertEqual(
                payload["sampling_params"], {"temperature": 1.0, "max_new_tokens": 0}
            )
            return web.json_response(
                {
                    "meta_info": {
                        "input_token_logprobs": [[None, 11], [-0.4, 12], [-0.7, 13]]
                    }
                }
            )

        app = web.Application()
        app.router.add_post("/generate", generate)
        runner = web.AppRunner(app)
        await runner.setup()
        self.addAsyncCleanup(runner.cleanup)
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        args = SimpleNamespace(sglang_model_routers={"teacher": ("127.0.0.1", port)})
        sample = SimpleNamespace(tokens=[11, 12, 13], response_length=2)
        rewards = await asyncio.gather(*(score_teacher(args, sample) for _ in range(3)))
        for reward in rewards:
            self.assertEqual(reward["teacher_log_probs"], [-0.4, -0.7])
            self.assertEqual(reward["task_reward"], 0.0)
            self.assertGreaterEqual(reward["teacher_seconds"], 0)

    async def test_missing_teacher_does_not_fall_back_to_student(self):
        with self.assertRaisesRegex(ValueError, "teacher router"):
            await score_teacher(SimpleNamespace(sglang_model_routers={}), None)

    def test_scores_reject_shifted_truncated_nonfinite_and_empty_responses(self):
        valid = {
            "meta_info": {"input_token_logprobs": [[None, 11], [-0.4, 12], [-0.7, 13]]}
        }
        self.assertEqual(response_log_probs(valid, [11, 12, 13], 1), [-0.7])
        for entries, length in [
            ([[None, 11], [-0.4, 13], [-0.7, 12]], 2),
            ([[None, 11], [-0.4, 12]], 1),
            ([[None, 11], [-0.4, 12], [float("nan"), 13]], 1),
            ([[None, 11], [-0.4, 12], [0.1, 13]], 1),
            (valid["meta_info"]["input_token_logprobs"], 0),
        ]:
            with (
                self.subTest(entries=entries, length=length),
                self.assertRaises(ValueError),
            ):
                response_log_probs(
                    {"meta_info": {"input_token_logprobs": entries}},
                    [11, 12, 13],
                    length,
                )

    def test_postprocessing_does_not_inject_scalar_reward(self):
        sample = SimpleNamespace(
            response_length=2,
            reward={"task_reward": 0.0, "teacher_log_probs": [-0.4, -0.7]},
        )
        self.assertEqual(post_process_rewards(None, [sample]), ([0.0], [0.0]))
        torch.testing.assert_close(sample.teacher_log_probs, torch.tensor([-0.4, -0.7]))


class PolicyAgeTests(unittest.TestCase):
    def test_b_preserves_slime_worker_dispatch_across_rounds(self):
        # The actual factory and entrypoint must agree on the worker's type.
        # A delegation-only wrapper incorrectly selects Slime's distributed path.
        class Worker:
            def __init__(self, args, source, *, concurrency):
                self.concurrency = concurrency
                self.start = Mock()

        upstream = ROOT / "slime/slime/rollout/fully_async_rollout.py"
        namespace = {
            "AsyncRolloutWorker": Worker,
            "DrainBeforePublication": DrainBeforePublication,
            "get_rollout_num_engines": lambda _: 1,
        }
        path = ROOT / "distillation/rollout.py"
        definitions = [
            n
            for n in ast.parse(path.read_text()).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef))
        ]
        exec(
            compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"),
            namespace,
        )
        entry = next(
            n
            for n in ast.parse(upstream.read_text()).body
            if isinstance(n, ast.FunctionDef)
            and n.name == "generate_rollout_fully_async"
        )
        source = SimpleNamespace(consumers={})
        source.register_consumer = Mock(side_effect=source.consumers.__setitem__)
        namespace.update(
            _get_worker=lambda args, data: data.consumers["fully_async"],
            _generate_rollout_async=lambda args, rollout_id, data: rollout_id,
            run=lambda output: output,
        )
        exec(
            compile(ast.Module(body=[entry], type_ignores=[]), str(upstream), "exec"),
            namespace,
        )
        args = SimpleNamespace(
            rollout_data_transport="object-store", sglang_server_concurrency=2
        )
        for rollout_id in (0, 1, 2):
            namespace["ensure_complete_response_worker"](args, source)
            self.assertEqual(
                namespace["generate_rollout_fully_async"](args, rollout_id, source),
                rollout_id,
            )
        source.register_consumer.assert_called_once()
        worker = source.consumers["fully_async"]
        worker.start.assert_called_once()
        self.assertIsInstance(worker, Worker)
        source.consumers["fully_async"] = Worker(args, source, concurrency=2)
        with self.assertRaisesRegex(ValueError, "without draining enforcement"):
            namespace["ensure_complete_response_worker"](args, source)

    def test_complete_responses_reject_mixed_versions_but_c_records_them(self):
        with self.assertRaisesRegex(ValueError, "spans policy versions"):
            validate_sample_policy(["2", "3"], 3, 1, complete_response=True)
        self.assertEqual(
            validate_sample_policy(["2", "3"], 3, 1, complete_response=False),
            (1, True),
        )
        self.assertEqual(
            validate_sample_policy(["2", "2"], 3, 1, complete_response=True),
            (1, False),
        )
        with self.assertRaisesRegex(ValueError, "exceeds limit"):
            validate_sample_policy(["1", "3"], 3, 1, complete_response=False)

    def test_b_waits_for_real_slime_pause_to_drain_and_preserves_pause_state(self):
        # Run the pinned worker's pause method without its GPU-only imports.
        path = ROOT / "slime/slime/rollout/fully_async_rollout.py"
        worker_class = next(
            n
            for n in ast.parse(path.read_text()).body
            if isinstance(n, ast.ClassDef) and n.name == "AsyncRolloutWorker"
        )
        pause = next(
            n
            for n in worker_class.body
            if isinstance(n, ast.FunctionDef) and n.name == "pause"
        )
        namespace = {}
        exec(
            compile(ast.Module(body=[pause], type_ignores=[]), str(path), "exec"),
            namespace,
        )
        entered = threading.Event()

        def real_pause(self, *, drain):
            entered.set()
            return namespace["pause"](self, drain=drain)

        base = type("PinnedWorkerPause", (), {"pause": real_pause})
        worker_type = type("CompleteResponseWorker", (DrainBeforePublication, base), {})
        policy = worker_type()
        policy.condition = threading.Condition()
        policy.paused = False
        policy.running = True
        policy.error = None
        policy.admission_paused = True
        policy.active = 1
        returned = threading.Event()
        results = []

        def publication_pause():
            results.append(policy.pause(drain=False))
            returned.set()

        thread = threading.Thread(target=publication_pause, daemon=True)
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertFalse(returned.wait(0.05))
        finally:
            with policy.condition:
                policy.active = 0
                policy.condition.notify_all()
            thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results, [False])
        self.assertTrue(policy.pause(drain=False))
        policy.error = RuntimeError("generation failed")
        with self.assertRaisesRegex(RuntimeError, "generation failed"):
            policy.pause(drain=False)

    def test_mixed_versions_use_oldest_prefix(self):
        self.assertEqual(policy_age(["2", "3"], 3), 1)
        self.assertEqual(policy_age(["3"], 3), 0)

    def test_unknown_future_and_negative_versions_fail(self):
        for versions in ([], ["?"], ["4"], ["-1"], ["２"]):
            with self.subTest(versions=versions), self.assertRaises(ValueError):
                policy_age(versions, 3)


class ConfigurationTests(unittest.TestCase):
    def test_larger_profile_resource_layout(self):
        args = SimpleNamespace(
            student=Path("/student"),
            teacher=Path("/teacher"),
            data=Path("/data"),
            mode="bounded_async",
            rollouts=20,
            response_tokens=2048,
            seed=42,
            profile="7b32b",
        )
        command = training_args(args, Path("/run"))
        self.assertIn("--use-precision-aware-optimizer", command)
        for option, expected in [
            ("--hidden-size", "3584"),
            ("--num-attention-heads", "28"),
            ("--tensor-model-parallel-size", "4"),
            ("--global-batch-size", "64"),
            ("--rollout-num-gpus", "8"),
            ("--sglang-server-concurrency", "8"),
            ("--optimizer-offload-fraction", "0.5"),
        ]:
            self.assertEqual(command[command.index(option) + 1], expected)
        self.assertEqual(
            command[command.index("--save-hf") + 1].format(rollout_id=9),
            "/run/hf-checkpoints/9",
        )
        self.assertNotIn("--no-save-optim", command)
        args.checkpoint_mode = "model-only"
        model_only = training_args(args, Path("/run"))
        self.assertIn("--no-save-optim", model_only)
        self.assertIn("--save-hf", model_only)
        config = serving_config(args.student, args.teacher, args.profile)["sglang"]
        self.assertEqual([m["server_groups"][0]["num_gpus"] for m in config], [4, 4])
        self.assertEqual(
            [m["server_groups"][0]["num_gpus_per_engine"] for m in config], [2, 4]
        )
        self.assertEqual([m["update_weights"] for m in config], [True, False])

    def test_fragmented_layout_preserves_gpu_roles_and_rejects_mismatch(self):
        args = SimpleNamespace(
            student=Path("/student"),
            teacher=Path("/teacher"),
            data=Path("/data"),
            mode="bounded_async",
            rollouts=20,
            response_tokens=2048,
            seed=42,
            profile="7b32b",
        )
        for per_node in (1, 2, 4):
            args.gpus_per_node = per_node
            allocation = layout(args.profile, per_node)
            self.assertEqual(allocation["nodes"] * per_node, 12)
            command = training_args(args, Path("/run"))

            def option(key):
                return int(command[command.index(key) + 1])

            self.assertEqual(
                option("--actor-num-nodes") * option("--actor-num-gpus-per-node"), 4
            )
            self.assertEqual(option("--num-gpus-per-node"), per_node)
            self.assertEqual(option("--rollout-num-gpus"), 8)
            self.assertEqual(option("--tensor-model-parallel-size"), 4)
            nodes = [
                {"Alive": True, "Resources": {"GPU": per_node}}
                for _ in range(allocation["nodes"])
            ]
            self.assertTrue(nodes_match(nodes, allocation["nodes"], per_node))
            nodes[0]["Resources"]["GPU"] = per_node + 1
            self.assertFalse(nodes_match(nodes, allocation["nodes"], per_node))
            with self.assertRaises(ValueError):
                layout(args.profile, per_node, allocation["nodes"] + 1)
        for invalid in (0, 3, 8):
            with self.assertRaises(ValueError):
                layout("7b32b", invalid)

    def test_real_slime_reward_accessor_and_custom_config_contract(self):
        # Exercise the pinned accessor and configuration statements without
        # importing the GPU-only argument parser. This is a bounded contract check.
        source = ROOT / "slime/slime/utils/arguments.py"
        tree = ast.parse(source.read_text())
        reward_argument = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "--reward-key"
        )
        parser = argparse.ArgumentParser()
        definition = ast.Module(
            body=[ast.Expr(value=copy.deepcopy(reward_argument))], type_ignores=[]
        )
        exec(
            compile(ast.fix_missing_locations(definition), str(source), "exec"),
            {"parser": parser},
        )
        args = parser.parse_args(["--reward-key", "task_reward"])
        self.assertEqual(args.reward_key, "task_reward")
        loader = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Attribute)
            and node.test.attr == "custom_config_path"
        )
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "hooks.json"
            config.write_text(json.dumps({"distillation_max_policy_lag": 1}))
            args.custom_config_path = str(config)
            block = ast.Module(body=[copy.deepcopy(loader)], type_ignores=[])
            exec(
                compile(ast.fix_missing_locations(block), str(source), "exec"),
                {"args": args, "yaml": yaml, "logger": Mock()},
            )
        self.assertEqual(args.distillation_max_policy_lag, 1)
        with patch.object(sys, "path", [str(ROOT / "slime"), *sys.path]):
            from slime.utils.types import Sample

        sample = Sample(
            response_length=2,
            group_index=0,
            reward={"task_reward": 0.0, "teacher_log_probs": [-0.4, -0.7]},
        )
        self.assertEqual(sample.get_reward_value(args), 0.0)
        # Slime logs scalar rewards before invoking our postprocessing hook.
        namespace = {"Sample": Sample, "defaultdict": defaultdict}
        for relative, function in [
            ("slime/utils/misc.py", "group_by"),
            ("slime/observability/rollout_metrics.py", "_compute_zero_std_metrics"),
        ]:
            path = ROOT / "slime" / relative
            node = next(
                n
                for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == function
            )
            exec(
                compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
                namespace,
            )
        args.advantage_estimator = "grpo"
        self.assertEqual(
            namespace["_compute_zero_std_metrics"](args, [sample]),
            {"zero_std/count_0.0": 1},
        )
        self.assertEqual(post_process_rewards(args, [sample]), ([0.0], [0.0]))
        torch.testing.assert_close(sample.teacher_log_probs, torch.tensor([-0.4, -0.7]))

    def test_real_slime_serving_parser_keeps_teacher_frozen(self):
        path = ROOT / "slime/slime/backends/sglang_utils/sglang_config.py"
        spec = importlib.util.spec_from_file_location(
            "distillation_test_sglang_config", path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        self.addCleanup(sys.modules.pop, spec.name)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "serving.json"
            config_path.write_text(json.dumps(serving_config("/student", "/teacher")))
            config = module.SglangConfig.from_yaml(config_path)
            for model in config.models:
                model.resolve(
                    SimpleNamespace(
                        rollout_num_gpus_per_engine=2, hf_checkpoint="/student"
                    )
                )
            self.assertEqual(config.total_num_gpus, 4)
            self.assertEqual([m.update_weights for m in config.models], [True, False])
            self.assertEqual(
                config.models[1].server_groups[0].overrides["model_path"], "/teacher"
            )

    def test_sync_async_only_change_scheduling_in_training_command(self):
        args = SimpleNamespace(
            student=Path("/models/student"),
            teacher=Path("/models/teacher"),
            data=Path("/data/train.jsonl"),
            mode="synchronous",
            rollouts=3,
            response_tokens=512,
            seed=42,
        )
        sync = training_args(args, Path("/run"))
        args.mode = "fully_async"
        asynchronous = training_args(args, Path("/run"))
        args.mode = "bounded_async"
        bounded = training_args(args, Path("/run"))
        self.assertEqual(
            [(a, b) for a, b in zip(asynchronous, bounded, strict=True) if a != b],
            [("distillation.hooks.fully_async", "distillation.hooks.bounded_async")],
        )
        changes = [(a, b) for a, b in zip(sync, asynchronous, strict=True) if a != b]
        self.assertEqual(
            changes,
            [("distillation.hooks.synchronous", "distillation.hooks.fully_async")],
        )
        config = serving_config(args.student, args.teacher)
        student, teacher = config["sglang"]
        self.assertTrue(student["update_weights"])
        self.assertFalse(teacher["update_weights"])
        self.assertEqual(
            sum(m["server_groups"][0]["num_gpus"] for m in config["sglang"]), 4
        )
        self.assertEqual(sync[sync.index("--reward-key") + 1], "task_reward")
        self.assertIn("--untie-embeddings-and-output-weights", sync)
        self.assertNotIn("--use-rollout-logprobs", sync)
        self.assertEqual(sync[sync.index("--num-gpus-per-node") + 1], "4")
        self.assertEqual(sync[sync.index("--flush-cache-interval") + 1], "1")
        self.assertEqual(sync[sync.index("--sglang-server-concurrency") + 1], "2")

    def test_bad_lag_fails_before_io(self):
        args = SimpleNamespace(
            rollouts=3, response_tokens=512, max_policy_lag=1, mode="synchronous"
        )
        with self.assertRaisesRegex(ValueError, "lag zero"):
            validate_options(args)


class TokenizerTests(unittest.TestCase):
    def test_fingerprints_and_vocab_check_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = {}
            for role in ("student", "teacher"):
                directory = root / role
                directory.mkdir()
                for name, value in {
                    "config.json": {"vocab_size": 4},
                    "tokenizer.json": {
                        "model": {"vocab": {"hello": 0}},
                        "added_tokens": [{"id": 1}],
                    },
                    "tokenizer_config.json": {"eos_token": "<eos>"},
                    "generation_config.json": {"eos_token_id": 1},
                }.items():
                    (directory / name).write_text(json.dumps(value))
                lock[role] = {
                    "files": {p.name: fingerprint(p) for p in directory.iterdir()}
                }
            lock_path = root / "lock.json"
            lock_path.write_text(json.dumps(lock))
            result = verify_models(
                root / "student", root / "teacher", lock_path, require_weights=False
            )
            self.assertEqual(result["tokenizer_identity"], "exact")
            with self.assertRaisesRegex(ValueError, "weights are missing"):
                verify_models(root / "student", root / "teacher", lock_path)
            (root / "teacher/tokenizer.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "differs"):
                verify_models(
                    root / "student", root / "teacher", lock_path, require_weights=False
                )


class ObjectiveTests(unittest.TestCase):
    def test_upstream_sampled_advantage_matches_exact_reverse_kl_gradient_in_expectation(
        self,
    ):
        # Execute the actual pinned helper without importing Megatron/CUDA. This
        # checks its algebra, not Slime's distributed forward/backward execution.
        source = ROOT / "slime/slime/backends/megatron_utils/loss.py"
        tree = ast.parse(source.read_text())
        function = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "apply_opd_kl_to_advantages"
        )
        module = ast.Module(
            body=[
                ast.ImportFrom(
                    module="__future__", names=[ast.alias(name="annotations")], level=0
                ),
                copy.deepcopy(function),
            ],
            type_ignores=[],
        )
        namespace = {"torch": torch}
        exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
        logits = torch.tensor([0.1, 0.7, -0.3], dtype=torch.float64, requires_grad=True)
        teacher = torch.tensor([0.2, 0.3, 0.5], dtype=torch.float64).log()
        logp = logits.log_softmax(-1)
        probabilities = logp.exp()
        exact = (probabilities * (logp - teacher)).sum()
        expected_gradient = torch.autograd.grad(exact, logits, retain_graph=True)[0]
        advantages = [torch.zeros_like(logp)]
        data = {"teacher_log_probs": [teacher]}
        namespace["apply_opd_kl_to_advantages"](
            SimpleNamespace(opd_type="sglang", opd_kl_coef=1.0),
            data,
            advantages,
            [logp.detach()],
        )
        sampled_expectation = -(
            probabilities.detach() * advantages[0].detach() * logp
        ).sum()
        actual = torch.autograd.grad(sampled_expectation, logits)[0]
        torch.testing.assert_close(actual, expected_gradient)
        updated = (logits.detach() - 0.1 * actual).log_softmax(-1)
        self.assertLess(
            (updated.exp() * (updated - teacher)).sum().item(), exact.item()
        )


class EvaluationTests(unittest.TestCase):
    def test_batch_response_count_mismatch_is_rejected(self):
        from distillation.evaluate import generate_batch

        tokenizer = Mock()
        tokenizer.apply_chat_template.return_value = [1, 2]
        with (
            patch("distillation.evaluate.request", return_value=[{"text": "one"}]),
            self.assertRaisesRegex(ValueError, "response count"),
        ):
            generate_batch(
                tokenizer,
                [{"prompt": "one"}, {"prompt": "two"}],
                "http://127.0.0.1:1",
                {},
                1,
            )

    def test_grading_failure_preserves_generated_answer_and_truncation(self):
        from distillation.evaluate import main

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tokenizer.json").write_text("{}")
            data = root / "eval.jsonl"
            data.write_text(
                (json.dumps({"prompt": "2 + 2?", "answer": "4"}) + "\n") * 3
            )
            response = {
                "text": "partial answer",
                "meta_info": {"finish_reason": {"type": "length"}},
            }
            tokenizer = Mock()

            # Transformers 5 defaults to a BatchEncoding; exercise the explicit
            # token-ID request rather than silently assuming the old default.
            def chat_template(messages, **kwargs):
                return [1, 2] if kwargs.get("return_dict") is False else object()

            tokenizer.apply_chat_template.side_effect = chat_template
            transformers = SimpleNamespace(AutoTokenizer=Mock())
            transformers.AutoTokenizer.from_pretrained.return_value = tokenizer
            grader = SimpleNamespace(grade=Mock(side_effect=ValueError("bad grade")))
            argv = [
                "evaluate",
                "--endpoint",
                "http://127.0.0.1:1",
                "--model",
                str(root),
                "--data",
                str(data),
                "--output",
                str(root / "out"),
                "--scorer",
                "fixture.grade",
                "--request-timeout",
                "600",
                "--batch-size",
                "2",
            ]
            with (
                patch("sys.argv", argv),
                patch.dict("os.environ", {"SLURM_JOB_ID": "cpu-test"}),
                patch.dict("sys.modules", {"transformers": transformers}),
                patch(
                    "distillation.evaluate.request",
                    side_effect=[
                        {"model_path": str(root)},
                        [response, response],
                        response,
                    ],
                ) as request_mock,
                patch(
                    "distillation.evaluate.importlib.import_module", return_value=grader
                ),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                main()
            records = [
                json.loads(line)
                for line in (root / "out/responses.jsonl").read_text().splitlines()
            ]
            self.assertEqual([record["index"] for record in records], [0, 1, 2])
            record = records[0]
            summary = json.loads((root / "out/summary.json").read_text())
            self.assertEqual(record["response"], response)
            self.assertEqual(record["error_stage"], "grading")
            self.assertTrue(record["truncated"])
            self.assertEqual(summary["truncated"], 3)
            self.assertEqual(summary["failed"], 3)
            self.assertEqual(summary["attempted"], 3)
            self.assertEqual(summary["batch_size"], 2)
            self.assertEqual(summary["request_timeout_seconds"], 600)
            self.assertEqual(request_mock.call_args.kwargs["timeout"], 600)
            self.assertEqual(request_mock.call_args.args[1]["input_ids"], [1, 2])
            self.assertEqual(
                request_mock.call_args_list[1].args[1]["input_ids"], [[1, 2], [1, 2]]
            )


if __name__ == "__main__":
    unittest.main()
