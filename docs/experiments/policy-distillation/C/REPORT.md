# C · Mid-response updates with rebuilt cache

Status, 26 October 2026: selected; no C training attempt has run.

Use the same overlap and one-publication lag bound as B, but permit Slime to
abort unfinished generation, flush KV cache, publish weights and resume partial
responses. Earlier tokens can come from a different student version. The teacher
remains frozen.

Use `MODE=fully_async` and a fresh original student checkpoint. Follow the
[common protocol](../README.md#separate-execution-checks-and-measurements); retain
separate condition-C manifests and outputs. Record mixed-version response counts:
zero means the mid-response shortcut was not exercised. Compare with B only
after establishing which behavior actually occurred.

No results or resource use yet. CPU regression and cluster startup checks precede
the bounded training smoke. Learning quality remains unmeasured.
