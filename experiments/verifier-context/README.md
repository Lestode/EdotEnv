# Verifier context experiment

Status: comparison runner implemented with offline tests. No paid trials have
been launched; final model choice, pilot limits, and live container validation
remain before the first comparison.

## Goal

Determine whether additional Markdown guidelines improve the final hidden
weighted Pearson correlation on this specific task,
`autoresearch-feature-volume`. Compare the baseline with the selected guidance
under the same conditions.

The task uses the local `data/autoresearch-feature-volume` package:
agents research features, train an Elastic Net model to forecast next-minute
volume changes, and submit it for evaluation on hidden market data. The package
contains reference baselines, but no completed agent trial results.

## Proposed comparison

| Condition | What the agent receives |
| --- | --- |
| A: baseline | The existing task instructions, public data, tools, and existing task documentation. |
| B: additional research guidance | Everything in A, plus the [research guidance](research-guidance.md). |

The baseline keeps the documentation already supplied with the task.
The comparison measures the value of additional guidance; it does not remove
the existing research or evaluation guides. Both conditions preserve that existing context.

Use the same model, agent execution loop, tools, data split, verifier, and
resource limits in both conditions. Start each rollout with a fresh environment
and conversation. Repeat both conditions so that one lucky or failed run does
not determine the conclusion.

The first treatment covers how to validate research findings. It adds research
advice to the existing task documentation, so any improvement would measure the
value of that advice. It would not isolate the benefit of explaining verifier
mechanics. Hidden labels and the reference solution remain outside both agents'
contexts. Freeze the Markdown before comparison runs; do not tune it against
hidden evaluation results.

## What to measure

The primary outcome is the final model's official hidden weighted Pearson
correlation (`weighted_pearson_ic`). Compare this metric across repeated runs
with and without the selected guidance.

Report rejected or missing submissions alongside the scores for accepted
models, so failed runs remain visible. Their penalty is not a measured
forecasting correlation. Keep the submitted models and verifier outcomes so
that reported results can be checked.

The current experiment asks whether the guidelines improve the final metric.
Detailed analysis of the agents' research process is potential future work.

## Potential future work

If the guidelines improve the final metric, future work could inspect which
agent decisions changed and whether those changes explain the improvement.
It could also test whether an agent can learn the useful behavior through OPCD
without receiving the extra Markdown at deployment.

These follow-ups are outside the current experiment. Any later OPCD work must
follow the teacher-only context separation required by the project scope.
A score improvement here would not by itself establish that the behavior can
be distilled or that the guidelines help on other tasks.

## Running the comparison

The [runner](compare.py) uses Harbor 0.20.0 and its existing Terminus 2 agent.
The agent has a terminal in the task container and receives the task's MCP
server address. Both arms use the OpenAI Responses API, low reasoning effort,
and the same loop. Harbor appends the frozen Markdown to B's task instruction;
A receives the original instruction. No extra behavioral coaching is added by
this runner. The original public-data Docker build and separate hidden verifier
are preserved. The reference solution is omitted from the snapshot.

Use Python 3.12 on a Docker host with Compose v2. Install the pinned runner and
transport dependencies in a virtual environment:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r experiments/verifier-context/requirements.txt
```

Prepare inputs without Docker, credentials, or any API calls. Replace
`MODEL_ID` with the affordable OpenAI model selected for the pilot; the runner
does not silently select a model. Run commands from the repository root:

```sh
.venv/bin/python experiments/verifier-context/compare.py prepare \
  --task data/autoresearch-feature-volume \
  --output experiments/verifier-context/runs/pilot-01 \
  --model openai/MODEL_ID --pairs 2 --max-turns 30 --agent-seconds 1800
```

These are editable pilot defaults, not validated success criteria. This creates
four fresh trials ordered A, B, B, A. A pair is an execution block, not a shared
random seed. The runner freezes a private task copy, the guidance, file hashes,
model, order, and resource settings in `plan.json`. It checks for changed task,
guidance, runner, or dependency declarations before execution and each trial.
Prepare a new directory to change these inputs. Use only the supplied trusted
task package; its Dockerfiles and Compose configuration execute locally.
The task package and `runs/` outputs are gitignored. Keep all run directories
local: they include hidden verifier data, submissions, and agent logs.

Before running, expose `OPENAI_API_KEY` through the process environment. Do not
put its value in commands, files committed to Git, or chat. The repository's
Actions secret is separate and cannot supply a key to this local process.

```sh
.venv/bin/python experiments/verifier-context/compare.py check \
  experiments/verifier-context/runs/pilot-01
```

This checks frozen inputs, the Harbor task/config schema, key presence, Docker,
and Compose availability. It does not call the model or verify API access,
billing, successful image builds, MCP connectivity, or artifact transfer. Those
still need a live trial on the selected host. No host repository or hidden data
is added to the agent's mounts; access boundaries rely on the original task's
Docker allowlists and Harbor's separate verifier.

Only after validating the model and pilot limits, launch paid trials explicitly:

```sh
.venv/bin/python experiments/verifier-context/compare.py run \
  experiments/verifier-context/runs/pilot-01 \
  --allow-paid --max-total-cost-usd 2
```

The dollar value above is an example **stop threshold, not a hard billing cap**.
The runner checks accumulated reported cost before starting another trial; an
in-flight trial can cross the threshold. Missing cost information stops further
trials. Each arm has the same 30-turn/30-minute defaults and a 4,096-output-token
limit per request. Harbor/provider retries may still incur spending within a
trial. There are no automatic trial retries or resumed conversations. An
execution marker prevents rerunning a partially billed comparison; inspect its
artifacts and prepare a new comparison deliberately if necessary. Running can
stop before all pairs finish; the report shows the unrun trials. Use an external
billing control if an absolute dollar limit is required.

## Reading the results

The runner writes `summary.md`, `summary.json`, and `scores.csv` after execution.
You can regenerate the report without credentials or Docker:

```sh
python3 experiments/verifier-context/compare.py summarize \
  experiments/verifier-context/runs/pilot-01
```

Reports include each planned trial, its status, measured IC if accepted, and
reported cost. They show accepted-score means and medians for A and B, plus
B-minus-A differences for pairs with accepted submissions in both arms. These
conditional summaries must be read alongside all failure counts; a condition
that submits fewer models can have a misleadingly high accepted-score mean.
No failure penalty is averaged into forecasting IC. Zero and negative accepted
ICs are retained. A small pilot is descriptive, without a significance claim.

The collector reads Harbor's `trials/<id>/result.json` and the official verifier's
`verifier/metrics.json` and `verifier/reward.json`. It requires acceptance,
finite IC in [-1, 1], and matching primary/metric rewards. Rejections, missing or
corrupt output, execution errors, and unrun trials remain distinct. A valid
submission scored after an agent timeout still counts, with its exception
recorded. Harbor keeps the trajectory, verifier outputs, and fitted submission
artifacts under each trial directory for later checks. The guidance is advisory:
the verifier does not enforce the research advice itself.

## Validation before the first paid comparison

- Select and record an affordable OpenAI model and confirm the chosen account
  can use it; exact model choice remains open.
- Validate image builds, MCP access, submission collection, and separate hidden
  scoring on a Docker host. This machine currently has no Docker executable;
  container integration and live model execution have not been demonstrated.
- Agree pilot repetitions, time/turn limits, and spending threshold. Two pairs
  and the command above are starting examples, not approved paid execution.
- Check the saved reports and failure counts before increasing the pilot size.

Offline tests use synthetic task and verifier fixtures. Run all project tests
with the installed runner dependencies to include the Harbor instruction/schema
contract test:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Project implementation gaps and validation work remain in
[the OPCD TODO](../../docs/TODO.md); repository changes follow
[the development workflow](../../docs/WORKFLOW.md).
