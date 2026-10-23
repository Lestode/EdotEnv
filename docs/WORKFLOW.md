# Development workflow

## Branches, review, and acceptance

After the initial baseline, develop each coherent change on a `codex/` feature
branch and open a PR against `main`. Update that PR as work progresses. Do not
push changes directly to `main`. Agents may prepare and push changes within the
user's authorized task; merging requires explicit user acceptance of the PR.

EdotEnv adopts the shared [working agreement](https://github.com/Lestode/review-agents/blob/f4db0e334f6fc2216c583fe796638b096a5abbfe/WORKFLOW.md)
and [documentation review procedure](https://github.com/Lestode/review-agents/blob/f4db0e334f6fc2216c583fe796638b096a5abbfe/documentation-review/SKILL.md)
at the same revision as the action. Project scope remains in [AGENTS.md](../AGENTS.md).
Update the action pin and these links together through a reviewed PR.

Before merging:

1. `Project checks` must pass on the latest PR revision. It checks project file
   hygiene, Python lint/format, local documentation links, review configuration,
   and project CPU tests when present. Slime's upstream test suite is separate.
2. Obtain a completed documentation review for that revision. Read and resolve
   its findings, or record the user's explicit acceptance of remaining findings.
   A green review job means collection, model execution, and publication completed;
   it does not mean the model approved the proposal. Incomplete reviews block merge.
3. Run relevant implementation tests and record their commands, results, and
   coverage limits in the PR. Use [the OPCD TODO](TODO.md) for feature evidence
   and [hardware planning](HARDWARE.md) for GPU/distributed validation.
   CPU checks and model commentary alone cannot establish training correctness.
4. Obtain explicit user acceptance of the PR. After another push, rerun checks,
   request a fresh review, and obtain acceptance of the updated proposal.

The sole bootstrap exception is the initial commit containing the existing
project documents and pinned upstream Slime source. The review integration
itself is proposed through the first PR.

## Reviewer operation

The [workflow](../.github/workflows/documentation-review.yml) pins
`Lestode/review-agents` at `f4db0e334f6fc2216c583fe796638b096a5abbfe`.
[Project settings](../.github/documentation-review.json) select this documentation
index and [project review instructions](../.github/documentation-review.md).
The shared action defines the model, collection limits, authorization, execution,
and publication behavior; see [its integration guide](https://github.com/Lestode/review-agents/blob/f4db0e334f6fc2216c583fe796638b096a5abbfe/README.md).

The action runs on a GitHub-hosted Ubuntu runner with `auth-mode: api-key`.
Create an `OPENAI_API_KEY` repository Actions secret in
[GitHub settings](https://github.com/Lestode/EdotEnv/settings/secrets/actions).
Pass it only through the action's `openai-api-key` input. Do not put the key in
project files or PR comments. The API project needs billing and access to the
shared action's pinned model; this mode uses OpenAI API billing and needs no
local Mac runner or ChatGPT sign-in. The shared action makes a tool-free
Responses API request using the same bounded review context as its ChatGPT mode.
Proposed PR code runs only in the separate verification job; the privileged
reviewer uses accepted default-branch settings and never executes PR code.
Keep the review job's per-PR concurrency group and queued execution so repeated
automatic events cannot invoke paid reviews concurrently for the same revision.

Human collaborators with write access receive an automatic review on PR open,
reopen, or ready-for-review when that revision lacks an automatic response.
Later pushes require an explicit `/review-docs` comment. Use
`/review-docs <question>` in the PR Conversation tab for follow-up discussion.
This workflow authorizes the reviewer's PR reports and requested follow-up replies.

## Activation and enforcement status

As of 2026-10-23, API-key support is accepted and merged in
[review-agents PR #2](https://github.com/Lestode/review-agents/pull/2). The workflow
and documentation links pin its accepted full commit SHA. Private action sharing
is enabled for repositories under the same owner.

[EdotEnv PR #1](https://github.com/Lestode/EdotEnv/pull/1) installs the consumer
workflow; default-branch review triggers become active after it is merged.
Provision the repository secret, then open a small PR or reopen an existing PR,
verify exactly one report, and test a follow-up command. A live API call and
publication have not yet been verified.
See [the activation tasks](TODO.md#repository-workflow-validation).

GitHub rejected private-repository branch protection on the current account
with `Upgrade to GitHub Pro or make this repository public` (HTTP 403).
The PR-first policy therefore binds agents through AGENTS.md and maintainers
through this workflow, but GitHub does not yet block direct pushes or merges.
Keep the repository private; the shared action requires it. If the account is
upgraded, enable protection for `main`: require a PR, the latest `Project checks`
status, resolved conversations, and enforcement for administrators; disable force
pushes and deletion. Human acceptance and the latest documentation-review findings
remain manual merge conditions because the shared action does not emit an approval
verdict and does not automatically review every push. The user manages repository access.

## Local verification

Initialize Slime with `git submodule update --init slime`, then run:

```sh
python -m pip install pre-commit==4.2.0
pre-commit run --all-files
python scripts/check_project.py
# Once project CPU tests exist:
python -m unittest discover -s tests -p 'test_*.py' -v
```

Add deterministic CPU tests under `tests/` using unittest as OPCD is implemented;
extend CI dependencies and test commands through the same PR when necessary.
Keep GPU and cluster jobs separate until compute access is confirmed. Changes
inside `slime/` need a published submodule commit and a reviewed pointer update;
the initial submodule URL is the upstream read source, not an authorized push target.
