# Development workflow

## Branches, review, and acceptance

After the initial baseline, develop each coherent change on a `codex/` feature
branch and open a PR against `main`. Update that PR as work progresses. Do not
push changes directly to `main`. Agents may prepare and push changes within the
user's authorized task; merging requires explicit user acceptance of the PR.

EdotEnv adopts the shared [working agreement](https://github.com/Lestode/review-agents/blob/0b7cc867d1899bbdffcb1a93b1f41b5fe881fc65/WORKFLOW.md)
and [documentation review procedure](https://github.com/Lestode/review-agents/blob/0b7cc867d1899bbdffcb1a93b1f41b5fe881fc65/documentation-review/SKILL.md)
at the same revision as the action. Project scope remains in [AGENTS.md](../AGENTS.md).
Update the action pin and these links together through a reviewed PR.

Before merging:

1. `Project checks` must pass on the latest PR revision. It checks project file
   hygiene, Python lint/format, local documentation links, review configuration,
   and project CPU tests when present. Slime's upstream test suite is separate.
2. `Agent reviews completed` must pass on that exact PR head. It certifies that
   the configured documentation agent completed its review and published its
   report. Read and resolve its findings, or record the user's explicit acceptance
   of remaining findings. Completion is not model approval or human acceptance.
3. Run relevant implementation tests and record their commands, results, and
   coverage limits in the PR. Use [the OPCD TODO](TODO.md) for feature evidence
   and [hardware planning](HARDWARE.md) for GPU/distributed validation.
   CPU checks and model commentary alone cannot establish training correctness.
4. Obtain explicit user acceptance of the PR. Each new commit requires fresh
   checks, a completed review under [the reviewer operation policy](#reviewer-operation),
   and acceptance of the updated proposal.

The sole bootstrap exception is the initial commit containing the existing
project documents and pinned upstream Slime source. The review integration
itself is proposed through the first PR.

## Reviewer operation

The [workflow](../.github/workflows/documentation-review.yml) fetches the private
`Lestode/review-agents` repository at its pinned immutable revision, then invokes
its local composite action. Public-consumer support was accepted in
[shared reviewer PR #4](https://github.com/Lestode/review-agents/pull/4).
[Project settings](../.github/documentation-review.json) select this documentation
index and [project review instructions](../.github/documentation-review.md).
The shared action defines the model, collection limits, authorization, execution,
and publication behavior; see [its integration guide](https://github.com/Lestode/review-agents/blob/0b7cc867d1899bbdffcb1a93b1f41b5fe881fc65/README.md).

The action runs on a GitHub-hosted Ubuntu runner with `auth-mode: api-key` and
explicit public-repository opt-in. Fetch it with `REVIEW_AGENTS_READ_KEY`, a
dedicated SSH deploy key restricted to read-only access on `Lestode/review-agents`.
Store its private part as a repository Actions secret in
[EdotEnv settings](https://github.com/Lestode/EdotEnv/settings/secrets/actions).
Keep it separate from the model credential and disable persisted checkout
credentials. The private part is not stored in project files or retained locally.
Do not upload the private reviewer checkout as an artifact.
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
reopen, ready-for-review, and every `synchronize` update. An external contributor's
PR requires a human collaborator to request review with `/review-docs`.
Use `/review-docs <question>` for follow-up discussion or retries. A manual
workflow dispatch takes an open `pull_request_number`. The shared action
verifies the requester before invoking a paid model.
It also verifies authorization before creating a check, so an external comment
cannot overwrite a valid result. Follow-up questions in this gated workflow
require a full review of the captured revision as well as an answer.
This workflow authorizes the reviewer's PR reports and requested follow-up replies.

Each request captures the intended PR head. The action creates
`Agent reviews completed` on that exact commit, not on the workflow's base commit.
It passes only after a model review is completed and published, or an existing
completed report for the same request and revision is verified. Skipped, closed,
superseded, failed, and incomplete requests cannot pass. Missing read credentials
or a failed checkout leave the required check absent, which also blocks merging.
A new commit cannot inherit an older commit's passing check. Queued superseded
events do not review newer code under an older request, and duplicate completed
requests do not repeat billing. Legacy or incomplete response markers do not
count as completion evidence.

## Activation and enforcement status

The initial API-key support was accepted and merged in
[review-agents PR #2](https://github.com/Lestode/review-agents/pull/2). Its original
private-consumer pin was `f4db0e334f6fc2216c583fe796638b096a5abbfe`.
The new public-consumer pin above is the accepted merge commit of shared reviewer PR #4.

[EdotEnv PR #1](https://github.com/Lestode/EdotEnv/pull/1) activated the initial
private-repository workflow on the default branch. The repository's
`OPENAI_API_KEY` Actions secret is configured and live API model access is verified.
The accepted default branch's [Project checks](https://github.com/Lestode/EdotEnv/actions/runs/39946844008)
passed. Opening [validation PR #2](https://github.com/Lestode/EdotEnv/pull/2)
produced one [automatic API review report](https://github.com/Lestode/EdotEnv/pull/2#issuecomment-6363933978)
in a [successful review job](https://github.com/Lestode/EdotEnv/actions/runs/39946910380).
The report identifies OpenAI Responses API execution and API-key billing.
A [rerun of the same automatic request](https://github.com/Lestode/EdotEnv/actions/runs/39946910380/attempts/2)
passed without a model-input event and left exactly one matching report, verifying
same-request deduplication. After a later push, a fresh `/review-docs` request
produced a [successful follow-up report](https://github.com/Lestode/EdotEnv/pull/2#issuecomment-6363988681)
for revision `03420af` in a [passing comment-triggered job](https://github.com/Lestode/EdotEnv/actions/runs/39947308582).
The follow-up confirmed that the activation-checklist finding was resolved.
See [the activation tasks](TODO.md#repository-workflow-validation).

On 2026-10-23, EdotEnv was confirmed public and `main` protection was enabled.
GitHub requires both `Project checks` and `Agent reviews completed` from the
GitHub Actions app, requires the branch to be up to date, applies the requirements
to administrators, requires PRs and resolved conversations, and disallows force
pushes and deletion. No GitHub approving-review count is added; explicit human
acceptance still follows the policy above. The user manages repository access.

The read-only deploy key and `REVIEW_AGENTS_READ_KEY` secret were configured on
2026-10-23, with read-only scope verified through GitHub's API. The private part
was deleted locally after the secret was stored. Private checkout, API execution,
report publication, and an exact-head passing check were verified in a
[feature-branch bootstrap run](https://github.com/Lestode/EdotEnv/actions/runs/39959766619)
for `a6deb6646aee9849a8de7b1ec1a6c6ba07672cea`.

The required agent check is enforced. The shared dependency is merged and the
public-consumer runtime is validated on the feature branch. Automatic review
after updates on `main` still needs acceptance and merge of this consumer workflow.
The historical private API review evidence is separate from the bootstrap evidence.

For bootstrap validation of an authorized workflow upgrade, manually dispatch
this workflow from its feature branch for its own PR once the shared dependency
is accepted. The registered workflow path already exists on `main`. The job still
reads accepted default-branch project configuration and the accepted shared
reviewer, and must publish a real completed review before the required gate can
pass. This one-off validation does not activate automatic review on `main` or
authorize merging. Obtain user acceptance before merging. Do not remove
protection or fabricate a successful check to merge setup.
If manual dispatch is unavailable before merge, leave the gate blocking and
resolve bootstrap with the user. After acceptance and merge, validate automatic
reviews on updated PRs, exact-head association, duplicate handling, and failure
and stale-head blocking. See [the activation tasks](TODO.md#repository-workflow-validation).

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
