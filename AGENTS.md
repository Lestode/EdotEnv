# Scope

Goal: validate classical policy distillation in Slime with distributed execution. Establish whether the implementation works and whether its shortcuts preserve student quality within an acceptable loss.

- Use Slime (`slime/`) as the training framework.
- Distill from a more capable, frozen teacher into a trainable student.
- Use Slime's sampled-token on-policy distillation for the initial study, with teacher token-level scores on student-generated responses. Its implementation still needs validation.
- Support distributed student generation, teacher evaluation, and student training.
- Prefer Slime's existing customization hooks and minimize core framework changes.

Keep supporting project documentation in `docs/` and follow [documentation rules](docs/DOCUMENTATION.md).

Keep a concise handoff of current work and validation gaps in [the project TODO](docs/TODO.md).

Follow [experiment guidance](docs/EXPERIMENTS.md) when planning and running experiments.

## Protected infrastructure: greengoblin

**Never modify anything on greengoblin.** It is an existing SSH gateway to the
Komondor cluster, not a project execution host. Only read-only inspection and
transit through its existing SSH setup are permitted.

- Do not create, edit, or delete files on greengoblin, including temporary files,
  repositories, caches, SSH keys, known-hosts files, or SSH configuration.
- Do not install, update, or remove software; change accounts, permissions,
  services, containers, networking, or firewall settings; or restart services.
- Do not run builds, student generation, teacher scoring, or training workloads
  on greengoblin. Prepare artifacts locally and use authorized Komondor compute
  allocations for cluster execution.
- Always check for and reuse an existing authenticated Komondor session first; follow [connection guidance](docs/KOMONDOR.md).
- Use SSH transit settings that preserve gateway state; do not automatically
  add host keys or create persistent SSH control sockets on the gateway.
- If an operation would require a gateway change, stop that operation, report
  the limitation, and pursue an approach that respects this restriction.

## Development workflow

Use a `codex/` feature branch and a pull request for every change after the initial repository bootstrap. Follow [the development workflow](docs/WORKFLOW.md) for required checks, review requests, acceptance, and merge conditions. Do not push changes directly to `main` or merge without explicit user acceptance of the PR.

## Confirmed decisions

- OPCD is retired from the project scope. The user chose classical policy distillation because prompt engineering and context manipulation make the intended study difficult to evaluate scientifically. The earlier context-distillation requirements and paper-specific objective no longer apply.
- The primary question is whether the implementation works and its shortcuts preserve quality within an acceptable loss; synchronous/asynchronous execution is one comparison, with speed and cost secondary. The [experiment design](docs/experiments/policy-distillation/README.md) records the provisional validation setup; resource sizing may evolve.
- The teacher will be an accessible model.
- The initial classical distillation model pair is selected in [experiment guidance](docs/EXPERIMENTS.md#initial-policy-distillation-pair). Tokenizer metadata compatibility and both frozen-model development baselines completed on Komondor; teacher-score alignment through training remains to be validated. Results and limits are in the [run journal](docs/experiments/LOG.md).
- Komondor is the target compute cluster; authenticated access and an A100 Slurm allocation have been verified. See [hardware planning](docs/HARDWARE.md) for evidence and remaining validation.
- For now, the user manages collaboration and access in this repository.
- Always bring conflicting information to the user for review before resolving it, including conflicts introduced by a new request. Follow the [finding-resolution and conflict policy](docs/WORKFLOW.md#finding-resolution-and-conflicts) for review findings, consequences, and recorded decisions.
- When using tools or systems developed by the user or the company, use their documented configuration and supported interfaces. Report limitations before changing their implementation or adding local capabilities; follow the [supported-interface policy](docs/WORKFLOW.md#supported-interfaces-for-user-and-company-systems).
- The documentation and implementation reviewers use the user's OpenAI API key on a GitHub-hosted runner; setup and activation are tracked in [the development workflow](docs/WORKFLOW.md).
- This repository is public. Keep the shared reviewer repository private and fetch its pinned source in CI using a dedicated read-only deploy key. Require both named reviewer checks to pass on the latest PR commit before merging; new commits require fresh reviews, with no separate comparison gate. Activation is tracked in [the development workflow](docs/WORKFLOW.md).

## Open questions

These do not block local design and implementation. Resolve each before the run or feature that depends on it.

- Data: which training and evaluation datasets, who grants access, and where may they be processed and stored?
- Distillation: does the initial sampled-token baseline and its SGLang teacher-scoring path learn reliably, and which shortcuts preserve that benefit? See [implementation and evidence](docs/DISTILLATION.md).
- Compute sizing: which GPU/node counts and per-run budget should each experiment use within the verified Komondor project access? Multi-node execution remains unvalidated; see [hardware planning](docs/HARDWARE.md).
- Runtime: which GPU container runtime/images are permitted, and can we install modified code and fetch dependencies/model weights?
- Distribution: one managed cluster or independent sites? Are concurrent multi-node jobs and Ray/NCCL/teacher-service connections permitted?
- Storage: where do model caches, checkpoints, rollouts, and logs live? What quotas and worker access are available?

## Deferred decisions

- Sizing: maximum sequence lengths, batch size, and throughput target remain to be determined.
- Evaluation: benchmarks, baselines, held-out splits, and success criteria will be decided later.
