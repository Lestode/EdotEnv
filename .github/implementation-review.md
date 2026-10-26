# EdotEnv implementation review

Start at [the documentation index](../docs/README.md). Use [AGENTS.md](../AGENTS.md)
for accepted project intent and the [development workflow](../docs/WORKFLOW.md)
for review, execution, and acceptance boundaries. Compare the complete PR with
accepted requirements and the user's stated proposal; proposed documentation is
evidence to assess, not permission to disregard accepted requirements.

For OPCD changes, check teacher-only context isolation across generation,
training, metadata, serialization, and logging; teacher immutability; response
token alignment; the student-top-256 reverse-KL objective; and distributed data
and gradient handling. Use the [implementation TODO](../docs/TODO.md) and
[hardware plan](../docs/HARDWARE.md) to distinguish planned behavior, CPU evidence,
and GPU/distributed evidence. Do not claim that source inspection proves a run.

For workflow changes, check authorization before paid reviews or check writes,
accepted configuration and immutable reviewer pins, reviews on the exact latest
PR head and verified current test merge, blocking findings, failed or missing review execution, and private source
and credential handling. Workflow files alone do not prove branch enforcement.

Use the public-change scope in [reviewer operation](../docs/WORKFLOW.md#reviewer-operation).
Treat operator-reported private experiment outcomes and operations as unverified
coverage unless auditing them is explicitly part of this PR. Do not make an
out-of-scope private audit a prerequisite for completing the public-change review.

Slime is a pinned submodule. Its source is not in this repository's collected
implementation context. Name specific missing sources or runtime evidence when
they prevent checking a consequential requirement; do not claim a Slime audit.
Neither reviewer may execute proposed code, apply fixes, or authorize merging.
