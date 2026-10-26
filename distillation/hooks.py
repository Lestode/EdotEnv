"""Strict teacher scoring and bounded policy age through Slime's public hooks."""

import math
import time


def response_log_probs(payload, tokens, response_length):
    """Check SGLang's token identities before extracting response scores."""
    if not 0 < response_length < len(tokens):
        raise ValueError("Expected a nonempty prompt and response")
    entries = payload["meta_info"]["input_token_logprobs"]
    if len(entries) != len(tokens):
        raise ValueError("Teacher score count does not match input token count")
    for token, entry in zip(tokens, entries, strict=True):
        if len(entry) < 2 or entry[1] != token:
            raise ValueError("Teacher returned a different token sequence")
    scores = [entry[0] for entry in entries[-response_length:]]
    if any(
        not isinstance(x, (int, float)) or not math.isfinite(x) or x > 0 for x in scores
    ):
        raise ValueError(
            "Teacher response log probabilities must be finite and nonpositive"
        )
    return scores


def policy_age(versions, current_version):
    if not versions or any(
        not str(v).isascii() or not str(v).isdigit() for v in versions
    ):
        raise ValueError("Missing or invalid generating policy version")
    numbers = [int(v) for v in versions]
    if max(numbers) > current_version:
        raise ValueError("Generating policy is newer than the training policy")
    return current_version - min(numbers)


async def score_teacher(args, sample, **kwargs):
    import aiohttp

    routers = getattr(args, "sglang_model_routers", {})
    if "teacher" not in routers:
        raise ValueError("A named frozen teacher router is required")
    host, port = routers["teacher"]
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    payload = {
        "input_ids": sample.tokens,
        "sampling_params": {"temperature": 1.0, "max_new_tokens": 0},
        "return_logprob": True,
        "logprob_start_len": 0,
    }
    start = time.monotonic()
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"http://{host}:{port}/generate", json=payload
        ) as response:
            response.raise_for_status()
            result = await response.json()
    scores = response_log_probs(result, sample.tokens, sample.response_length)
    return {"teacher_log_probs": scores, "teacher_seconds": time.monotonic() - start}


def post_process_rewards(args, samples, **kwargs):
    import torch

    if not samples:
        raise ValueError("Cannot train on an empty batch")
    for sample in samples:
        reward = sample.get_reward_value(args)
        scores = reward["teacher_log_probs"]
        if len(scores) != sample.response_length or not scores:
            raise ValueError("Teacher scores are not aligned with the response")
        if any(not math.isfinite(x) or x > 0 for x in scores):
            raise ValueError("Invalid teacher score")
        sample.teacher_log_probs = torch.tensor(scores, dtype=torch.float32)
    # Pure distillation: no scalar task reward and no reward normalization.
    return [0.0] * len(samples), [0.0] * len(samples)


def validate_sample_policy(versions, current_version, max_lag, *, complete_response):
    age = policy_age(versions, current_version)
    mixed = len({int(v) for v in versions}) > 1
    if complete_response and mixed:
        raise ValueError(
            "Response spans policy versions in a complete-response condition"
        )
    if age > max_lag:
        raise ValueError(f"Policy age {age} exceeds limit {max_lag}")
    return age, mixed


def _generate(args, rollout_id, data_buffer, *, asynchronous, complete_response=True):
    if asynchronous:
        from slime.rollout.fully_async_rollout import (
            generate_rollout_fully_async as generate,
        )
    else:
        from slime.rollout.sglang_rollout import generate_rollout as generate
    from slime.rollout.base_types import call_rollout_fn, iter_samples

    result = call_rollout_fn(generate, args, rollout_id, data_buffer, evaluation=False)
    # The pinned train.py publishes once at startup and after every rollout.
    # This launcher starts fresh, without recovery or skipped publications.
    current_version = rollout_id + 1
    ages = []
    mixed_responses = 0
    for sample in iter_samples(result.samples):
        age, mixed = validate_sample_policy(
            sample.weight_versions,
            current_version,
            args.distillation_max_policy_lag,
            complete_response=complete_response,
        )
        mixed_responses += mixed
        if (
            not sample.rollout_log_probs
            or len(sample.rollout_log_probs) != sample.response_length
        ):
            raise ValueError("Missing or misaligned sampling log probabilities")
        if any(not math.isfinite(x) for x in sample.rollout_log_probs):
            raise ValueError("Nonfinite sampling log probability")
        ages.append(age)
    if not ages:
        raise ValueError("No generated samples")
    result.metrics = dict(result.metrics or {})
    result.metrics.update(
        {
            "distillation/policy_age_max": max(ages),
            "distillation/policy_age_mean": sum(ages) / len(ages),
            "distillation/training_policy_version": current_version,
            "distillation/mixed_version_responses": mixed_responses,
            "distillation/response_count": len(ages),
            "distillation/stale_responses": sum(age > 0 for age in ages),
        }
    )
    return result


def synchronous(args, rollout_id, data_buffer, evaluation=False):
    if evaluation:
        raise ValueError("Use the separate frozen-checkpoint evaluator")
    return _generate(args, rollout_id, data_buffer, asynchronous=False)


def fully_async(args, rollout_id, data_buffer, evaluation=False):
    if evaluation:
        raise ValueError("Use the separate frozen-checkpoint evaluator")
    return _generate(
        args, rollout_id, data_buffer, asynchronous=True, complete_response=False
    )


def bounded_async(args, rollout_id, data_buffer, evaluation=False):
    if evaluation:
        raise ValueError("Use the separate frozen-checkpoint evaluator")
    from distillation.rollout import ensure_complete_response_worker

    ensure_complete_response_worker(args, data_buffer)
    return _generate(args, rollout_id, data_buffer, asynchronous=True)
