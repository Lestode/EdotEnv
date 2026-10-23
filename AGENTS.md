# Scope

Goal: implement [On-Policy Context Distillation for Language Models](https://arxiv.org/pdf/2602.12275) (OPCD) in Slime, with distributed execution.

- Use Slime (`slime/`) as the training framework.
- Support OPCD with different teacher and student contexts.
- Keep the teacher frozen during training, following the paper's default configuration and main experiments.
- Use the teacher to score student-generated responses with token-level probabilities for the paper's student-top-256 reverse KL objective.
- Hard constraint: keep teacher-only context out of student inputs. There is some context that the student SHOULD NOT have access to.
- Support distributed student generation, teacher evaluation, and student training.
- Prefer Slime's existing customization hooks and minimize core framework changes.

Keep supporting project documentation in `docs/` and follow [documentation rules](docs/DOCUMENTATION.md).

Track implementation gaps and validation work in [the OPCD TODO](docs/TODO.md).

## Development workflow

Use a `codex/` feature branch and a pull request for every change after the initial repository bootstrap. Follow [the development workflow](docs/WORKFLOW.md) for required checks, review requests, acceptance, and merge conditions. Do not push changes directly to `main` or merge without explicit user acceptance of the PR.

## Confirmed decisions

- The teacher will be an accessible model.
- For now, the user manages collaboration and access in this repository.
- The documentation reviewer will use the user's OpenAI API key on a GitHub-hosted runner; setup and activation are tracked in [the development workflow](docs/WORKFLOW.md).
- This repository is public. Keep the shared reviewer repository private and fetch its pinned source in CI using a dedicated read-only deploy key. Require completed agent reviews on the latest PR commit before merging; activation is tracked in [the development workflow](docs/WORKFLOW.md).

## Working assumptions

- A100 GPU nodes may be available; hardware and access are unconfirmed. See [hardware planning](docs/HARDWARE.md).

## Open questions

These do not block local design and implementation. Resolve each before the run or feature that depends on it.

- Models: which teacher/student checkpoints and compatible tokenizers? DeepSeek is a tentative starting point.
- Scope: system-prompt distillation, experiential-knowledge distillation, or both? If experiential, how is knowledge generated and accumulated?
- Context/data: which datasets and teacher-only contexts, who grants access, and where may they be processed and stored?
- Teacher scoring: which backend exposes probabilities for the student's top-256 token IDs at every response position? See [implementation work](docs/TODO.md). Is a separate scalar grading reward also wanted?
- Compute access: which cluster, GPU types/VRAM/count, allocation budget, job limits, SSH access, and scheduler permissions?
- Runtime: which GPU container runtime/images are permitted, and can we install modified code and fetch dependencies/model weights?
- Distribution: one managed cluster or independent sites? Are concurrent multi-node jobs and Ray/NCCL/teacher-service connections permitted?
- Storage: where do model caches, checkpoints, rollouts, and logs live? What quotas and worker access are available?

## Deferred decisions

- Sizing: maximum teacher-context and student-response lengths, batch size, and throughput target remain to be determined.
- Evaluation: benchmarks, baselines, held-out splits, and success criteria will be decided later.
