# Development workflow

## Branches, review, and acceptance

After the initial baseline, develop each coherent change on a `codex/` feature
branch and open a PR against `main`. Update that PR as work progresses. Do not
push changes directly to `main`. Agents may prepare and push changes within the
user's authorized task; merging requires explicit user acceptance of the PR.

EdotEnv adopts the shared [working agreement](https://github.com/Lestode/review-agents/blob/f27e55e7cdc5e93deb2401355cd46b17cc0fd556/WORKFLOW.md),
[documentation review procedure](https://github.com/Lestode/review-agents/blob/f27e55e7cdc5e93deb2401355cd46b17cc0fd556/documentation-review/SKILL.md),
and [implementation review procedure](https://github.com/Lestode/review-agents/blob/f27e55e7cdc5e93deb2401355cd46b17cc0fd556/implementation-review/SKILL.md)
at the same revision as both actions. Project scope remains in [AGENTS.md](../AGENTS.md).
Update the action pin and these links together through a reviewed PR. EdotEnv uses
the user-selected latest-head merge policy below in place of the earlier shared
example's five-check/test-merge integration.

Before merging:

1. `Project checks` must pass on the latest PR revision. It checks project file
   hygiene, Python lint/format, local documentation links, review configuration,
   and project CPU tests when present. Slime's upstream test suite is separate.
2. `Documentation reviewer` and `Implementation reviewer` must both pass on
   the exact latest PR commit. Each reviewer must finish and have no unresolved
   blocking findings; a new commit requires fresh checks and reviews. Missing,
   running, failed, or unpublished reviews do not pass. Fix findings or have an
   authorized human dismiss specific findings with a recorded reason under the
   [finding-resolution and conflict policy](#finding-resolution-and-conflicts).
   There is no separate `Current review comparison` or completion-only merge gate.
   Human acceptance and training correctness remain separate from reviewer results.
3. Run relevant implementation tests and record their commands, results, and
   coverage limits in the PR. Use [the project TODO](TODO.md) for feature evidence
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
that its findings were resolved or dismissed. The target branch requirements are
`Project checks`, `Documentation reviewer`, and `Implementation reviewer`, on the
latest PR commit. Activation and historical requirements are recorded in
[activation and enforcement status](#activation-and-enforcement-status).
Remaining validation scenarios are tracked in
[the workflow TODO](TODO.md#repository-workflow-validation).

## Supported interfaces for user and company systems

When using tools or systems developed by the user or the company, use their
documented configuration and supported interfaces. This includes `review-agents`.
Do not change the underlying implementation or recreate or extend its capabilities
in a consuming project to work around a configuration or interface gap.

If the supported configuration or interfaces cannot express what is needed,
explain the limitation and any proposed shared change to the user before
proceeding with work that depends on it. Development explicitly requested for
the underlying tool or system remains within scope; this rule governs its use
from consuming projects. Keep reusable capabilities in the shared system so
other projects can use the same supported behavior.

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
and publication behavior; see [its integration guide](https://github.com/Lestode/review-agents/blob/f27e55e7cdc5e93deb2401355cd46b17cc0fd556/README.md).

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
Responses API review request using the same bounded context as its ChatGPT mode. Oversized inputs first receive lossless
Markdown patch deduplication where applicable, then bounded summaries of older
automated reports when needed. These extra model calls use the same API billing;
human discussion, current reports, source, and the original finding ledger remain
available under the [shared compaction contract](https://github.com/Lestode/review-agents/blob/f27e55e7cdc5e93deb2401355cd46b17cc0fd556/README.md#compacting-long-review-history).
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

Each request captures the intended PR head. Each shared action publishes its
named finding-blocking check on that exact commit. The check passes only after
its report is completed and finalized with no unresolved blocking findings.
Missing read credentials, skipped or failed review execution, missing reports,
and unpublished results cannot pass. A new commit has no reviewer checks until
reviewed; it cannot inherit the previous commit's success. Paid-review requests
remain authorized and serialized, with existing deduplication and finding-ledger
behavior unchanged. Incomplete assessments within the agreed scope remain
blocking; out-of-scope private audits are coverage notes rather than prerequisites.
No separate completion-only check is requested.

The combined workflow keeps its existing filename, but is named `API agent
reviews` and gives runs the title `Review PR #<number>`. One immutable private
checkout supplies both actions, serialized per PR. An implementation assessment
still runs when documentation findings fail the preceding action. Each agent's
own command selects that reviewer for comment requests.

Documentation-review scope is defined by its supported `instructionsPath`
configuration. It checks documentation consistency and consequential claims
relevant to the proposal; dependency evidence does not impose a comprehensive
audit of unchanged CI. Implementation review checks code and workflow changes
and receives relevant unchanged caller/configuration source through its supported
`contextPaths` setting. Missing evidence for a consequential requirement remains
blocking in either review.

Both reviews include the accepted shared runner input/output contracts,
integration and compaction contracts, known limitations, and upstream validation references in bounded private
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

The merge gate uses the shared actions' existing checks on the PR head. The
separate polling comparison workflow is disabled; there is no test-merge review
check or additional agent review. Strict up-to-date branch protection remains
enabled: when `main` advances, update the PR branch and obtain new reviews on
its resulting commit. Only the latest reviewed PR commit may merge.

Review scope is the public proposal and supplied interfaces. Operator-reported
private outcomes and unavailable private operations are explicitly unverified
coverage limits unless the PR includes that audit. Neither reviewer must prove
historical private experiments merely to complete a public implementation or
documentation review. Consequential requirements within the agreed public-change
scope still require evidence and blocking findings still prevent merging.

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
Public-consumer support arrived in shared reviewer PR #4. Shared reviewer PR #3
added the implementation reviewer and includes that support.
The current pin is the accepted squash merge of [shared reviewer PR #12](https://github.com/Lestode/review-agents/pull/12),
which allocates summary allowances from the remaining final review budget. The caller explicitly selects `execution-mode: runner`
and `check-target: head`; optional Daytona execution and test-merge checks are not
activated by this upgrade. The latest-head policy below still overrides the shared
legacy comparison requirement.

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

At that stage, `Project checks` and `Agent reviews completed` remained
enforced. The documentation-only consumer workflow was accepted and merged in
[EdotEnv PR #4](https://github.com/Lestode/EdotEnv/pull/4). The implementation
reviewer, comparison workflow, and daily update-alert workflow were adopted in
[EdotEnv PR #5](https://github.com/Lestode/EdotEnv/pull/5), merged on 2026-10-23
as `5ec1822c6cefee4717529cb4727ed139878b19b4`. Those workflows are present on
`main`. On 2026-10-24, the user authorized activation of finding-blocking
protection. GitHub's required-status-checks endpoint was updated with the
then-current five-check configuration:
`Project checks`, `Agent reviews completed`, `Documentation reviewer`,
`Implementation reviewer`, and `Current review comparison`, each bound to the
GitHub Actions app. Readback confirmed all five requirements, strict up-to-date
checking, and unchanged settings for every other branch protection, including
administrator enforcement, PRs, conversation resolution, and force-push/deletion
restrictions. The historical private API review evidence remains separate from
the public-consumer bootstrap evidence.

Live blocking was verified on [PR #6](https://github.com/Lestode/EdotEnv/pull/6)
at 08:36:46 UTC on 2026-10-24. Its head was `74004941c8294dfe1a0b70930fa13aed37f658a3`,
its base was `5ec1822c6cefee4717529cb4727ed139878b19b4`, and its test merge was
`057c6f19345d1f4c0f6d349a3cd640beb9b7c1c7`; the merge parents matched that head
and base. `Project checks` and `Implementation reviewer` passed, while the
[documentation check](https://github.com/Lestode/EdotEnv/runs/120827261236)
failed with [unresolved F1 and an incomplete assessment](https://github.com/Lestode/EdotEnv/pull/6#issuecomment-6382068184).
The completion check also failed and the current-comparison check remained
pending. GitHub reported the PR conflict-free but its merge state `blocked`.
No check was fabricated, no finding was dismissed, and no merge was attempted.
This verifies blocking for that combined unresolved/incomplete case; it does
not isolate a completed review with findings while completion passes, or verify
a successful human dismissal. The subsequent isolated test is recorded below.
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

The isolated completed-review case was subsequently verified on head
`5c2ac9163413d8d444f5a2774e8dce0eded91719` against base
`5ec1822c6cefee4717529cb4727ed139878b19b4`: [review da37c140caa8](https://github.com/Lestode/EdotEnv/pull/6#issuecomment-6382279321)
completed, `Agent reviews completed` passed, the named documentation check failed
with unresolved F1, and GitHub still reported `blocked`. After the user's merge
direction accepted the remaining testing limitation, the shared mechanism
recorded reasoned dismissals for [the earlier F1](https://github.com/Lestode/EdotEnv/pull/6#issuecomment-6382319182)
and [the complete review's F1](https://github.com/Lestode/EdotEnv/pull/6#issuecomment-6382321402).
After the first dismissal, [the dismissal run](https://github.com/Lestode/EdotEnv/actions/runs/40080491156)
still failed because the second finding remained unresolved.
The documentation check then passed and `Current review comparison` passed.
A normal protected merge was nevertheless rejected with “4 of 5 required status
checks are expected.” The four head checks were not published on the test
merge alongside the comparison check. That separate integration issue remains
open; no protection was weakened. PR #6 removes the unconditional caller audit
from documentation review, configures the relevant implementation source context,
and does not add custom reviewer capability or check-publication code. Route
any future shared capability change through documented configuration under the
[supported-interface policy](#supported-interfaces-for-user-and-company-systems).
The user subsequently selected the simpler latest-head policy below instead
of requiring this test-merge integration to be repaired for EdotEnv.

The activation above used the prepared required-check settings through the
existing required-status-checks endpoint. This five-check rollout is historical;
the latest-head policy below supersedes its check selection while preserving
other protections. A future reviewer or
comparison update still needs its own current-review evidence; the activation
snapshot does not certify later revisions. Track remaining live-validation work
in [the workflow TODO](TODO.md#repository-workflow-validation).

### Latest-head policy transition

On 2026-10-24, the user explicitly replaced the five-check/test-merge policy:
both reviewers must finish without blocking findings on the latest PR commit;
every new commit requires fresh reviews. The user explicitly accepted that a
change of target branch without a new commit need not invalidate existing head
reviews, because retargeting is not currently used; see the
[recorded owner decision](https://github.com/Lestode/EdotEnv/pull/8#issuecomment-6383893448).
This policy does not claim the previous current-target guarantee. The prepared
[required-check configuration](../.github/review-required-checks.json) contains
`Project checks`, `Documentation reviewer`, and `Implementation reviewer`, each
bound to GitHub Actions, with strict up-to-date checking. `Current review
comparison` and `Agent reviews completed` are no longer selected as requirements.
The polling workflow is disabled and the optional completion-check invocation is removed.
Private experiment audits are outside the public-change review unless explicitly
included; their unavailable evidence is reported as unverified coverage.

The three-check selection was activated on 2026-10-24 at the user's direction.
Readback confirmed all three names bound to GitHub Actions, strict up-to-date
checking, and identical settings for every other branch protection, including
administrator enforcement, PRs, resolved conversations, and force-push/deletion
restrictions. The obsolete comparison workflow was disabled through GitHub's
workflow configuration. Its unchanged source file remains available because the
accepted reviewer configuration still reads it during this transition; the new
configuration stops collecting that retired workflow. At that transition, the
shared reviewer implementation and pin remained unchanged. Updated scope
customization takes effect
only after this configuration PR is accepted on the default branch; an existing
incomplete report does not silently become successful.

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

Initialize Slime with `git submodule update --init slime`. Use Python 3.12 and
the [experiment’s virtual-environment setup](../experiments/verifier-context/README.md#running-the-comparison)
for the Harbor/Daytona dependencies required by the project tests. The reviewer
freshness tests also require Node.js. Then run:

```sh
.venv/bin/python -m pip install pre-commit==4.2.0 -r experiments/verifier-context/requirements.txt
.venv/bin/pre-commit run --all-files
.venv/bin/python scripts/check_project.py
node --test tests/*.test.cjs
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Add deterministic CPU tests under `tests/` using unittest as training code is implemented;
extend CI dependencies and test commands through the same PR when necessary.
Keep GPU and cluster jobs separate until compute access is confirmed. Changes
inside `slime/` need a published submodule commit and a reviewed pointer update;
the initial submodule URL is the upstream read source, not an authorized push target.

### Return to latest-head reviews

On 2026-10-26, test-merge checks and then paired check/status publication both
failed live protected merge attempts on PR #12 despite successful reviews.
The [paired-publication run](https://github.com/Lestode/EdotEnv/actions/runs/40319372070)
passed on head `de252c714837ba8a01ab1b0d55cea710c3876d75`, but GitHub still
returned “2 of 3 required status checks are expected.” No protection was bypassed.

The owner then explicitly [selected the simpler latest-head policy and accepted
both merges](https://github.com/Lestode/EdotEnv/pull/12#issuecomment-6415770108).
This supersedes EdotEnv's earlier test-merge adoption. Preserve head publication
when upgrading the accepted reviewer; the unsuccessful shared PR #9 proposal is
not adopted. Require `Project checks`, `Documentation reviewer`, and
`Implementation reviewer` from GitHub Actions. Strict up-to-date checking and
all unrelated protections remain required. No comparison or completion-only gate
is added, and findings or incomplete assessments are not waived.

Reviews bind to the latest PR commit. This explicitly overrides the shared
legacy head-mode comparison requirement; GitHub does not independently bind
those results to a synthetic merge or target-branch identity. The immediate
validation is a normal protected merge for this experimental repository.
Broader failure-injection validation remains deferred. If a metadata-only edit
hides a head check, publish a fresh PR commit and obtain fresh reviews before
merging; do not manufacture a replacement result.

The [PR #12 protected merge](https://github.com/Lestode/EdotEnv/pull/12) succeeded
on 2026-10-26 after project checks and both [latest-head reviews](https://github.com/Lestode/EdotEnv/actions/runs/40321514804)
passed on `7dcadc811ad227006f5efe993667708d7b1297fe`. The merge produced
`3c1277bba93278e434e455926e930be75727febe`; strict protection and all unrelated
settings were preserved. This verifies the normal merge path, not the deferred
failure-injection scenarios.

### Context-compaction rollout

On 2026-10-28, [consumer PR #16](https://github.com/Lestode/EdotEnv/pull/16)
deployed shared reviewer PR #10. The [first automatic run](https://github.com/Lestode/EdotEnv/actions/runs/40719052512)
verified the new pin and context preparation, but both agents stopped during
history compaction before a fresh assessment. The generic failure did not expose
whether the cause was response format, echoed IDs, byte size, or transport.

[Consumer PR #17](https://github.com/Lestode/EdotEnv/pull/17) deployed the response
repair from shared reviewer PR #11. Its [long-history run](https://github.com/Lestode/EdotEnv/actions/runs/40726737722)
rejected a 2,022-byte documentation summary against the fixed 2,000-byte cap.
Implementation compaction summarized 153 older reports in seven requests, then
the final review failed with an HTTP 520 API error. Neither result certified a
fresh review.

The current update adopts accepted shared reviewer PR #12. Summaries share the
remaining final review space, up to 20 KB each, with unused space available to
later summaries. The no-retry rule, 512 KB / 640 KB total input limits, protected
context, and original finding ledger remain unchanged. Private instruction
bundles must still fit 32 KB. A fresh long-history run is needed to verify the
new allowance policy after deployment.
