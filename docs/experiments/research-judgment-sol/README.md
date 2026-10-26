# Sol research-guidance comparison

Test whether the three rules in [Keep research informative](../../RESEARCH_GUIDANCE.md)
improve results on `autoresearch-feature-volume`. This is a small exploratory
experiment on one task, not an OPCD training run.

- **A:** original task and shared execution-limit notice.
- **B:** everything in A, plus the guidance's heading and three numbered rules,
  copied verbatim. Its provenance/status section is excluded from agent inputs.
- **Both:** `gpt-6.1-sol`, low reasoning effort, fresh conversations and sandboxes;
  20 planned rollouts per condition, six concurrent, 30 turns and 30 minutes per
  agent, with 4 CPUs, 8 GiB RAM, and 10 GiB disk per trial.
- **Spending:** prioritize completing all 40 rollouts; $40 is indicative, with
  no early cancellation at $30. Report actual model usage and Daytona hosting
  separately. A generous $100 reported-usage safeguard stops new trials if
  spending is unexpectedly high; active trials finish. This is not a hard
  billing cap. Turn/time limits and the fixed rollout count still apply.

Compare final hidden weighted Pearson IC (higher is better), submission counts
and rates, failure reasons, medians, ranges, and individual scores. Keep official
failure penalties separate from IC and report interrupted/unstarted positions
separately. Accepted-score means alone do not establish an improvement.

Freeze the guidance, task, runner, and settings before launch; check delivered
prompts to confirm that only B receives the extra guidance. Task requirements
still apply, including the Elastic Net final-model restriction. Results from
Astra or earlier guidance versions remain separate.

Reuse the existing Harbor/Daytona runner and its previously validated task path.
Delete trial sandboxes after use; stop the controller when finished, retain its
results until a verified local download, then delete it. Private inputs and run
artifacts belong in `experiments/verifier-context/runs/sol-01/` (gitignored),
with operator records under `ops/`.
