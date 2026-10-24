# Development workflow

## Branches, review, and acceptance

After the initial baseline, develop each coherent change on a `codex/` feature
branch and open a PR against `main`. Update that PR as work progresses. Do not
push changes directly to `main`. Agents may prepare and push changes within the
user's authorized task; merging requires explicit user acceptance of the PR.

EdotEnv adopts the shared [working agreement](https://github.com/Lestode/review-agents/blob/57e1e998e109d879f41c1872eb547e8502555e60/WORKFLOW.md),
[documentation review procedure](https://github.com/Lestode/review-agents/blob/57e1e998e109d879f41c1872eb547e8502555e60/documentation-review/SKILL.md),
and [implementation review procedure](https://github.com/Lestode/review-agents/blob/57e1e998e109d879f41c1872eb547e8502555e60/implementation-review/SKILL.md)
at the same revision as both actions. Project scope remains in [AGENTS.md](../AGENTS.md).
Update the action pin and these links together through a reviewed PR.

Before merging:

1. `Project checks` must pass on the latest PR revision. It checks project file
   hygiene, Python lint/format, local documentation links, review configuration,
   and project CPU tests when present. Slime's upstream test suite is separate.
2. `Agent reviews completed` must pass on that exact PR head. It certifies
   documentation-review completion and publication. Under the new blocking
   integration, `Documentation reviewer` and `Implementation reviewer` must
   also pass on the current head, and `Current review comparison` must pass on
   GitHub's current test merge commit. Fix findings or have an authorized human
   dismiss specific findings with a recorded reason under the
   [finding-resolution and conflict policy](#finding-resolution-and-conflicts). Incomplete reviews cannot
   be dismissed. See the activation transition below; publishing workflow files
   does not activate the new branch requirements. Completion and disposition of
   findings do not establish human acceptance or training correctness.
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

## Finding resolution and conflicts

Fix routine implementation findings autonomously when the agreed requirements
and evidence determine the correction without conflicting information.
Always bring conflicting instructions, requirements, documentation, or factual
claims to the user for review before choosing a resolution. This also applies
when a new user request conflicts with an established rule or assumption, or an
existing decision appears to resolve the conflict. Explain the affected sources,
likely consequences, and recommended correction. Obtain the user's decision
before dependent work proceeds; independent work may continue.

Flag significant consequences the user may not have intended before taking the
affected action. Do not silently change a high-level rule or accept an exception
to satisfy a review finding. Dismissing a finding requires the user's explicit
decision on that finding, including its rationale; general PR acceptance alone
is not a specific dismissal. Record the finding and review IDs when available,
the reviewed revision/comparison, the reason, and a reference to the user's
decision in the PR. Have an authorized human record the dismissal through the
shared mechanism for the applicable assessment and comparison, following
[reviewer operation](#reviewer-operation).
A proposed dismissal or prose record cannot substitute for a required check.

A completed review establishes that a report was published. It does not establish
that its findings were resolved or dismissed. This escalation policy does not
close the separate enforcement gap: the named reviewer and current-comparison
requirements still need live activation and verification, preserving existing
protection. This remains open in
[the workflow TODO](TODO.md#repository-workflow-validation).

## Reviewer operation

The [workflow](../.github/workflows/documentation-review.yml) fetches the private
`Lestode/review-agents` repository at its pinned immutable revision, then invokes
both local composite actions. Public-consumer support was accepted in
[shared reviewer PR #4](https://github.com/Lestode/review-agents/pull/4);
implementation review and finding-blocking checks were accepted in
[shared reviewer PR #3](https://github.com/Lestode/review-agents/pull/3).
[Documentation settings](../.github/documentation-review.json) select this documentation
index and [documentation instructions](../.github/documentation-review.md).
[Implementation settings](../.github/implementation-review.json) select the same
index, a separate command and marker, optional unchanged source paths, and
[implementation instructions](../.github/implementation-review.md).
The shared action defines the model, collection limits, authorization, execution,
and publication behavior; see [its integration guide](https://github.com/Lestode/review-agents/blob/57e1e998e109d879f41c1872eb547e8502555e60/README.md).

Both actions run on a GitHub-hosted Ubuntu runner with `auth-mode: api-key` and
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
local Mac runner or ChatGPT sign-in. Each shared action makes a tool-free
Responses API request using the same bounded review context as its ChatGPT mode.
Proposed PR code runs only in the separate verification job; the privileged
reviewer uses accepted default-branch settings and never executes PR code.
Keep the review job's per-PR concurrency group and queued execution so repeated
automatic events cannot invoke paid reviews concurrently for the same revision.

Human collaborators with write access receive both reviews on PR open,
reopen, ready-for-review, every `synchronize` update, and PR retargeting.
When the target branch advances, update the PR branch to obtain fresh automatic
assessments and satisfy strict up-to-date protection. Authorized review requests
can also reassess the current comparison; a target-branch push alone does not
start either reviewer.
Implementation includes any non-Markdown path, including tests, configuration,
and workflows. A PR changing only Markdown receives an explicit successful
not-applicable implementation assessment without a model call.
An external contributor's PR requires a human collaborator to request each
review with `/review-docs` and `/review-implementation`. Each command also
supports follow-up discussion, retries, and finding dismissals. Use the report's
copyable dismissal command with its review ID, selected finding IDs, and reason;
dismissals apply only to that assessment and exact head/base comparison.
A manual workflow dispatch takes an open `pull_request_number` and invokes both
reviewers. The shared actions verify the requester before invoking a paid model.
They also verify authorization before creating a check, so an external comment
cannot overwrite a valid result. Follow-up questions in this gated workflow
require a full review of the captured revision as well as an answer.
This workflow authorizes both reviewers' PR reports and requested follow-up replies.

Each request captures the intended PR head. The action creates
`Agent reviews completed` on that exact commit, not on the workflow's base commit.
It passes only after a model review is completed and published, or an existing
completed report for the same request and revision is verified. Skipped, closed,
superseded, failed, and incomplete requests cannot pass. Missing read credentials
or a failed checkout leave the required check absent, which also blocks merging.
A new commit cannot inherit an older commit's passing check. Queued superseded
events do not review newer code under an older request, and duplicate completed
requests do not repeat billing. Legacy or incomplete response markers do not
count as completion evidence. Interrupted runs and publication failures may
require a retry; serialization and deduplication are not an exactly-once billing
guarantee.

The combined workflow keeps its existing filename, but is named `API agent
reviews` and gives runs the title `Review PR #<number>`. One immutable private
checkout supplies both actions, serialized per PR. An implementation assessment
still runs when documentation findings fail the preceding action. Each agent's
own command selects that reviewer for comment requests.

Both reviews include the accepted shared action manifests, integration contract,
known limitations, and upstream validation references in bounded private
model context. Normal runs prepend accepted project customization; bootstrap runs
do not activate proposed customization. Temporary context/configuration stays in
the ignored private checkout and is never uploaded. Reports may cite dependency
paths and the pin but must not reproduce private source. This supplies evidence
for checking caller compatibility; the shared runtime remains a separately
reviewed dependency, not a new consumer audit of its internals. Missing caller
source or interface details needed for a consequential integration requirement
still make the assessment incomplete. If the evidence exceeds the shared 32 KB
instruction bound, preparation fails rather than silently truncating it.
Documentation review also receives the adopted implementation procedure and
accepted caller configuration/resolver. Both receive the narrow helper and
check-publication interfaces used by the caller. Both disclosures to the OpenAI API were explicitly authorized
by the user. The private checkout is never published as review context.

The [comparison workflow](../.github/workflows/review-comparison.yml) verifies
the two published assessments and named checks against the current head, target
commit, and target branch. It publishes `Current review comparison` only on a
test merge commit whose parents match that comparison. It makes no model calls,
uses no secrets, and executes no PR code. Authorized reviewer commands and
completion of `API agent reviews` refresh it automatically. Preserve the run
title, workflow path, and completion-trigger name together when renaming them.
The shared revision's [known limitations](https://github.com/Lestode/review-agents/blob/57e1e998e109d879f41c1872eb547e8502555e60/KNOWN_ISSUES.md)
remain upstream; this integration does not claim to fix them.

### Reviewer update alerts

The [freshness workflow](../.github/workflows/reviewer-freshness.yml) checks the
accepted pin against the private reviewer's default-branch head every day at
07:23 UTC, and can also be run manually from Actions. It reuses the read-only
deploy key and requires only project contents read access and issue write access.
It reads Git history without executing upstream code or calling the model API.

When the pin is an ancestor of a newer upstream revision, it creates one tracking
issue containing the two revisions and a private comparison link. Unchanged runs
do not edit the issue or add comments. Later upstream changes update that issue;
catching up closes it. Closing the alert while still behind causes the next run
to reopen it. Private source and commit messages are not published. Review and
update the pin and matching links through a PR under the acceptance policy above;
the alert does not install updates or establish compatibility.

Failed private checkout, a missing pin, unexpected Git history, or API errors fail
the workflow rather than reporting a successful freshness check. Inspect failed
Actions runs for these cases. The schedule activates only after this workflow is
merged to the default branch. GitHub may disable schedules in public repositories
after [60 days without repository activity](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows);
re-enable the workflow in Actions if needed.

## Activation and enforcement status

The initial API-key support was accepted and merged in
[review-agents PR #2](https://github.com/Lestode/review-agents/pull/2). Its original
private-consumer pin was `f4db0e334f6fc2216c583fe796638b096a5abbfe`.
Public-consumer support arrived in shared reviewer PR #4. The new pin above
is the accepted merge commit of shared reviewer PR #3, which includes that support.

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

The existing `Project checks` and `Agent reviews completed` requirements remain
enforced. The documentation-only consumer workflow was accepted and merged in
[EdotEnv PR #4](https://github.com/Lestode/EdotEnv/pull/4). The implementation
reviewer, comparison workflow, and daily update-alert workflow were adopted in
[EdotEnv PR #5](https://github.com/Lestode/EdotEnv/pull/5), merged on 2026-10-23
as `5ec1822c6cefee4717529cb4727ed139878b19b4`. Those workflows are present on
`main`; the additional named-reviewer and current-comparison requirements have
not yet been activated or verified. GitHub's required-status-checks API was
checked on 2026-10-24 and still listed only `Project checks` and
`Agent reviews completed`. The historical private API review evidence remains
separate from the public-consumer bootstrap evidence.
The accepted documentation-only workflow also produced a
[successful automatic run](https://github.com/Lestode/EdotEnv/actions/runs/39983355266)
after PR #5 was updated to `f22949c`, confirming that update-triggered review is
already active for that rollout.
The [initial dual-review bootstrap](https://github.com/Lestode/EdotEnv/actions/runs/39983388029)
on `f22949c` published both assessments and exact-head checks. Documentation
findings blocked its named check while completion passed; implementation
assessment was incomplete because private dependency contracts were unavailable.
Later revisions supplied bounded interface evidence; PR #5 preserves those
bootstrap and review records. Every new PR revision still requires complete,
clear assessments from both named reviewers before acceptance. The merged
workflow files alone do not establish finding-blocking branch protection.

With PR #5 merged, run both reviewers and the comparison workflow on an open PR
while preserving all existing branch protections. Then add the three new
required checks using the prepared
[required-check settings](../.github/review-required-checks.json), which retain
both existing requirements and bind all five checks to GitHub Actions. Apply
these settings to the existing required-status-checks endpoint; preserve all
other protections. Confirm the settings and live merge state before claiming
finding-blocking enforcement. Track these activation steps in
[the workflow TODO](TODO.md#repository-workflow-validation).

For bootstrap validation of an authorized workflow upgrade, manually dispatch
this workflow from its feature branch for its own PR once the shared dependency
is accepted. The registered workflow path already exists on `main`. The job still
reads accepted default-branch project configuration and the accepted shared
reviewer, and must publish a real completed review before the required gate can
pass. When bootstrapping implementation review before its configuration exists
on `main`, set `bootstrap_implementation: true`. This explicit mode derives only
the documentation index from accepted documentation settings and uses shared
implementation defaults with a separate command and marker. It does not load
proposed implementation customization or execute PR code. Once accepted
implementation configuration exists, bootstrap mode refuses to override it;
normal runs always require that accepted configuration and its instructions.
This one-off validation does not activate automatic review on `main` or
authorize merging. Obtain user acceptance before merging. Do not remove
protection or fabricate a successful check to merge setup.
If manual dispatch is unavailable before merge, leave the gate blocking and
resolve bootstrap with the user. After acceptance and merge, validate automatic
reviews on updated PRs, exact-head association, duplicate handling, and failure
and stale-head blocking. See [the activation tasks](TODO.md#repository-workflow-validation).

## Local verification

Initialize Slime with `git submodule update --init slime`. The reviewer freshness
tests require Node.js. Then run:

```sh
python -m pip install pre-commit==4.2.0
pre-commit run --all-files
python scripts/check_project.py
node --test tests/*.test.cjs
python -m unittest discover -s tests -p 'test_*.py' -v
```

Add deterministic CPU tests under `tests/` using unittest as OPCD is implemented;
extend CI dependencies and test commands through the same PR when necessary.
Keep GPU and cluster jobs separate until compute access is confirmed. Changes
inside `slime/` need a published submodule commit and a reviewed pointer update;
the initial submodule URL is the upstream read source, not an authorized push target.
