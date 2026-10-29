# EdotEnv documentation

Validate classical policy distillation in Slime with distributed execution,
focusing on correctness and quality loss from implementation shortcuts.
Project adapters and CPU checks are available; GPU training validation is not complete.
Cluster access and a single-GPU inventory probe are recorded in hardware planning.

- [Project scope and decisions](../AGENTS.md)
- [Documentation rules](DOCUMENTATION.md)
- [Development workflow and review integration](WORKFLOW.md)
- [Experiment guidance](EXPERIMENTS.md)
- [Experiment journal](experiments/LOG.md)
- [Policy distillation experiment design](experiments/policy-distillation/README.md)
- [Classical distillation implementation and execution](DISTILLATION.md)
- [Current work and context for continuing](TODO.md)
- [Komondor connection and session reuse](KOMONDOR.md)
- [Hardware planning and GPU validation sequence](HARDWARE.md)
- [Draft research guidance based on observed agent failure cases](RESEARCH_GUIDANCE.md)
- [Sol comparison of research judgment guidance](experiments/research-judgment-sol/README.md)

The upstream training framework is pinned through [the Slime submodule](../.gitmodules).
