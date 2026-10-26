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
import unittest
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
)
from distillation.launch import ROOT, serving_config, training_args, validate_options
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
            get_reward_value=lambda _: {"teacher_log_probs": [-0.4, -0.7]},
        )
        self.assertEqual(post_process_rewards(None, [sample]), ([0.0], [0.0]))
        torch.testing.assert_close(sample.teacher_log_probs, torch.tensor([-0.4, -0.7]))


class PolicyAgeTests(unittest.TestCase):
    def test_mixed_versions_use_oldest_prefix(self):
        self.assertEqual(policy_age(["2", "3"], 3), 1)
        self.assertEqual(policy_age(["3"], 3), 0)

    def test_unknown_future_and_negative_versions_fail(self):
        for versions in ([], ["?"], ["4"], ["-1"], ["２"]):
            with self.subTest(versions=versions), self.assertRaises(ValueError):
                policy_age(versions, 3)


class ConfigurationTests(unittest.TestCase):
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
        args = parser.parse_args([])
        self.assertIsNone(args.reward_key)
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

        sample = Sample(response_length=2, reward={"teacher_log_probs": [-0.4, -0.7]})
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
        self.assertIn("--untie-embeddings-and-output-weights", sync)
        self.assertNotIn("--use-rollout-logprobs", sync)
        self.assertEqual(sync[sync.index("--num-gpus-per-node") + 1], "4")

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
    def test_grading_failure_preserves_generated_answer_and_truncation(self):
        from distillation.evaluate import main

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tokenizer.json").write_text("{}")
            data = root / "eval.jsonl"
            data.write_text(json.dumps({"prompt": "2 + 2?", "answer": "4"}) + "\n")
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
            ]
            with (
                patch("sys.argv", argv),
                patch.dict("os.environ", {"SLURM_JOB_ID": "cpu-test"}),
                patch.dict("sys.modules", {"transformers": transformers}),
                patch(
                    "distillation.evaluate.request",
                    side_effect=[{"model_path": str(root)}, response],
                ) as request_mock,
                patch(
                    "distillation.evaluate.importlib.import_module", return_value=grader
                ),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                main()
            record = json.loads((root / "out/responses.jsonl").read_text())
            summary = json.loads((root / "out/summary.json").read_text())
            self.assertEqual(record["response"], response)
            self.assertEqual(record["error_stage"], "grading")
            self.assertTrue(record["truncated"])
            self.assertEqual(summary["truncated"], 1)
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["request_timeout_seconds"], 600)
            self.assertEqual(request_mock.call_args.kwargs["timeout"], 600)
            self.assertEqual(request_mock.call_args.args[1]["input_ids"], [1, 2])


if __name__ == "__main__":
    unittest.main()
