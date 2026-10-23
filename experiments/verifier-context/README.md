# Verifier context experiment

Status: the local pilot was stopped at the user’s request because it was too
slow. Its partial results are preserved. Daytona hosting is now authorized;
cloud reference integration is running with 20-sandbox capacity confirmed.
The completed comparison remains to validate.

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

Use Python 3.12. Local execution requires Docker with Compose; Daytona execution
uses Harbor’s native backend and requires no local Docker daemon. Install the pinned runner and
transport dependencies, including the host MCP SDK required by LiteLLM, in a
virtual environment. This SDK does not change the task containers' own locked
dependencies:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r experiments/verifier-context/requirements.txt
```

Prepare inputs without Docker, credentials, or any API calls. Replace
`MODEL_ID` with the chosen model; the current pilot uses `gpt-6-luna`. The runner
does not silently select a model. Run commands from the repository root:

```sh
.venv/bin/python experiments/verifier-context/compare.py prepare \
  --task data/autoresearch-feature-volume \
  --output experiments/verifier-context/runs/pilot-01 \
  --model openai/MODEL_ID --pairs 2 --max-turns 30 --agent-seconds 1800
```

These are editable pilot defaults, not validated success criteria. This creates
four fresh trials listed A, B, B, A. With parallel execution this is the
launch order, not a promise about completion order. A pair is an execution block, not a shared
random seed. The runner freezes a private task copy, the guidance, file hashes,
model, backend, concurrency, order, and resource settings in `plan.json`. It checks for changed task,
guidance, runner, or dependency declarations before execution and each trial.
Prepare a new directory to change these inputs. Use only the supplied trusted
task package; its Dockerfiles and Compose configuration execute on the selected backend.
The task package and `runs/` outputs are gitignored. Keep all run directories
private: they include hidden verifier data, submissions, and agent logs.
Daytona receives the task package in private sandboxes; keep it out of public
images, snapshots, repositories, and published artifacts.

Before running, expose `OPENAI_API_KEY` through the process environment. Do not
put its value in commands, files committed to Git, or chat. The repository's
Actions secret is separate and cannot supply a key to this local process.

```sh
.venv/bin/python experiments/verifier-context/compare.py check \
  experiments/verifier-context/runs/pilot-01
```

This checks frozen inputs, pinned dependencies, the Harbor task/config schema,
and key presence; Docker and Compose are checked only for the Docker backend. It does not call the model or verify API access,
billing, successful image builds, MCP connectivity, or artifact transfer. The local reference check has since validated image builds, MCP access,
submission transfer, and separate hidden scoring. The local paid agent path
has also produced one accepted baseline. Complete cloud submission/hidden-verifier
validation and the fresh A/B comparison remain pending. No host repository or hidden data
is added to the agent's mounts; access boundaries rely on the original task's
Docker allowlists and Harbor's separate verifier.

Only after validating the model and pilot limits, launch paid trials explicitly:

```sh
.venv/bin/python experiments/verifier-context/compare.py run \
  experiments/verifier-context/runs/pilot-01 \
  --allow-paid --max-total-cost-usd 2
```

The dollar value above is an example **stop threshold, not a hard billing cap**.
The runner checks accumulated reported cost before starting another wave; every
trial already in flight can cross the threshold. With concurrency four, all four
trials may start before any usage is reported. With concurrency twenty, the
entire 20-rollout batch can be in flight before the first completed-trial cost
check. Monitor live usage and stop the study if the spending target is at risk. Missing cost information stops further
trials. Each arm has the same 30-turn/30-minute defaults and a 4,096-output-token
limit per request. Harbor/provider retries may still incur spending within a
trial. There are no automatic trial retries or resumed conversations. An
execution marker prevents rerunning a partially billed comparison; inspect its
artifacts and prepare a new comparison deliberately if necessary. Running can
stop before all pairs finish; the report shows the unrun trials. Use an external
billing control if an absolute dollar limit is required.

## Daytona execution

Set `DAYTONA_API_KEY` and `OPENAI_API_KEY` in the launcher’s environment. The local
private `.env` can supply them through a dotenv-aware launcher; the runner does
not automatically load credential files or upload them into sandboxes.
Prepare a new study when switching backend; do not pool the aborted local pilot
with cloud results as if they shared identical execution conditions:

```sh
.venv/bin/python experiments/verifier-context/compare.py prepare \
  --task data/autoresearch-feature-volume \
  --output experiments/verifier-context/runs/daytona-01 \
  --model openai/gpt-6-luna --pairs 10 --max-turns 30 --agent-seconds 1800 \
  --backend daytona --concurrency 20 --cpus 4 --memory-gb 8 --storage-gb 10
```

The `check` and `run` commands above also apply to a Daytona study. Check the
account’s per-sandbox and total resource quotas first. Resource overrides
`--cpus`, `--memory-gb`, and `--storage-gb` are optional and frozen for both arms;
otherwise the original task’s allocation is used. This task stops its research
sandbox after collecting artifacts and then starts a separate hidden verifier
sandbox. Allow capacity for lifecycle transitions as well as the intended
concurrency. Concurrency must fit the available pool.

Harbor detects the task’s Compose definition and runs it inside Docker-in-Docker
on Daytona, including sidecar services and the separate verifier environment.
The original Compose files, worker restrictions, artifact transfer, and hidden
build boundaries remain in the snapshot. Native support is not evidence of a
successful cloud integration; validate this task’s complete submission/scoring
path before interpreting cloud agent results.

Every sandbox is labelled with its study ID and configured for deletion on
completion, with a 30-minute inactivity stop and immediate deletion after stop
as a fallback. On completion or interruption the runner also deletes remaining
sandboxes bearing that study’s label and verifies none remain, writing
`cloud-cleanup.json`. Cleanup failures must be resolved in Daytona. Auto-stop
measures inactivity, not total runtime, and is not a spending cap. A killed
launcher can leave resources until fallback cleanup occurs.

The reported dollar threshold and `cost_usd` cover model API usage only.
Daytona compute/storage charges are separate; consult its billing records.
No automatic snapshots are created by the runner. Cloud costs depend on
allocation, image builds, research time, verification time, and cleanup.

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

## Pilot settings and validation status

The authorized local pilot uses GPT-6 Luna, two trials per condition, 30 turns
and 1,800 seconds per agent, and the $2 between-trial spending stop threshold.
That local pilot used a dedicated Colima VM with eight CPUs and 8 GiB
of RAM; the task's declared 16 GiB memory ceiling is not a minimum requirement.
Monitor free host storage and reclaim only unused build cache from the dedicated
VM when necessary. Container images and research artifacts can occupy substantial
space even when the supplied task package is small.

On 2026-10-23, the original task's reference solution passed the complete local
Harbor flow: MCP training/evaluation, submission artifact transfer, and hidden
verification, with IC 0.5183129972318243. This was a pipeline check without model
API calls and is excluded from the A/B comparison.

The first pilot startup stopped with `APIConnectionError` wrapping a missing
host-side `mcp` dependency, before a model response was recorded. The failed
attempt remains in local run artifacts. LiteLLM's Responses gateway imports the
MCP SDK even without MCP tools in the API request; its pinned version also needs
MCP 2.x types. The requirements now pin the compatible host SDK, and an offline
regression test exercises the real adapter up to a mocked HTTP boundary. A
mocked LiteLLM response alone bypasses those imports and cannot check this path.
Prepare a new frozen run after the dependency correction; do not overwrite the
aborted attempt or interpret it as an agent's research performance.

The corrected local pilot was deliberately cancelled on 2026-10-23. One baseline
submission was accepted with IC 0.18275811917854118; the first guided trial was
interrupted before a final score, and two trials never started. Recorded model
usage totals about $0.0158, including the interrupted trial. This supplies no
complete A/B pair and cannot establish a guidance effect. The local VM is stopped.
The user then authorized paid Daytona hosting to run a fresh comparison faster.
The account rejected the original eight-CPU allocation and a 20 GiB disk
request; its observed per-sandbox limits are four CPUs and 10 GiB disk. A
four-CPU, 8 GiB RAM, 10 GiB disk sandbox started successfully, and a second
simultaneous sandbox with that allocation was created and deleted to check
capacity. A later scale check successfully created 19 additional simultaneous
sandboxes beside the reference run, then verified their deletion. The user
authorized scaling up to 20 and confirmed that the $2 model-API target excludes
modest hosting costs. The fresh cloud comparison uses 10 trials per arm, up to
20 in parallel, with the same four-CPU / 8 GiB / 10 GiB allocation for both arms.
Completed cloud A/B scores and failure counts remain to collect. A small pilot is not
a claim of statistical significance or evidence of OPCD distillability.

Offline tests use synthetic task and verifier fixtures. Run all project tests
with the installed runner dependencies to include the Harbor instruction/schema
contract test:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Project implementation gaps and validation work remain in
[the OPCD TODO](../../docs/TODO.md); repository changes follow
[the development workflow](../../docs/WORKFLOW.md).
