# EdotEnv documentation review

Start at [the documentation index](../docs/README.md). Treat [AGENTS.md](../AGENTS.md)
as the authority for project intent and [the documentation rules](../docs/DOCUMENTATION.md)
as the authority for document ownership and consistency.

Check proposals against those requirements, with particular attention to teacher-only
context isolation, frozen-teacher behavior, response-token alignment, the exact OPCD
objective, and distributed validation. Use the [implementation TODO](../docs/TODO.md)
to distinguish planned capabilities from completed work. Do not reopen settled
choices because hardware, checkpoints, or later evaluations remain undecided.

Review documentation consistency and claims relevant to the proposed changes.
Use the supplied evidence to check consequential claims; identify specific missing
evidence when it prevents that assessment. Do not turn a documentation review
into a comprehensive code audit of unchanged CI or shared dependencies merely
because the documentation describes them. Implementation review checks code and
workflow changes against the accepted requirements and proposal.

For workflow changes, inspect [the development workflow](../docs/WORKFLOW.md).
Distinguish a completed documentation review, passing deterministic checks, human
acceptance, and evidence that training works. Highlight any proposal that conflates
them or claims branch protection or GPU validation without evidence.

The Slime source is a pinned submodule. Its internal Markdown is not part of this
repository's collected documentation snapshot; report that coverage limit when it
matters. Use project documentation to assess intent and avoid claiming a code audit.

This customization authorizes no edits, merges, or execution of proposed code.
