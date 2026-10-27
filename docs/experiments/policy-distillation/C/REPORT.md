# C · Mid-response updates with rebuilt cache

Status, 27 October 2026: non-exclusive C-a3 job `14673436` completed three updates with finite losses and nonzero finite gradients, and saved its checkpoint. Of 24 consumed responses, 16 were one publication stale; none mixed policy versions. The execution smoke passed, but the distinctive mid-response shortcut was not exercised.

Use the same overlap and one-publication lag bound as B, but permit Slime to
abort unfinished generation, flush KV cache, publish weights and resume partial
responses. Earlier tokens can come from a different student version. The teacher
remains frozen.

Use `MODE=fully_async` and a fresh original student checkpoint. Follow the
[common protocol](../README.md#separate-execution-checks-and-measurements); retain
separate condition-C manifests and outputs. Record mixed-version response counts:
zero means the mid-response shortcut was not exercised. Compare with B only
after establishing which behavior actually occurred.

C-a3 took 6m55s on eight GPUs (about 0.922 GPU-hours). Earlier pending C submissions consumed no GPUs. Learning quality remains unmeasured. Source `04f7283`; evidence in private `C-a3/train/manifest.json`, `train.log`, rollouts and checkpoint. See the [journal](../../LOG.md).
