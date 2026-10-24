# Verifier context experiment

Status: the fresh cloud comparison completed all 20 rollouts, with ten accepted
submissions per condition and no trial execution errors. Frozen inputs and all
20 initial prompt conditions were audited. Private results were downloaded;
independent checks verified deletion of every trial sandbox and the controller.
The local pilot and two aborted cloud startups remain separate evidence.

## Goal

Determine whether additional Markdown guidelines improve the final hidden
weighted Pearson correlation on this specific task,
`autoresearch-feature-volume`. Compare the baseline with the selected guidance
under the same conditions.

The task uses the local `data/autoresearch-feature-volume` package:
agents research features, train an Elastic Net model to forecast next-minute
volume changes, and submit it for evaluation on hidden market data. The package
contains reference baselines, but no completed agent trial results.

## Scope

This is a small exploratory experiment on one task. Keep implementation,
infrastructure, analysis, and validation simple and proportionate. Focus on a
fair A/B comparison, clear final scores and failure counts, modest costs, and
reliable sandbox cleanup. Reuse existing tools and fix issues that could
invalidate the comparison; broader infrastructure and deeper research remain
future work.

## Proposed comparison

| Condition | What the agent receives |
| --- | --- |
| A: baseline | The existing task instructions, public data, tools, existing task documentation, and a shared notice of actual execution limits. |
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
correlation (`weighted_pearson_ic`). Higher values are better. Compare this metric across repeated runs
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
and the same loop. Harbor appends the frozen research guidance only to B's task
instruction. Newly prepared studies append the same `runtime-limits.md` notice
last in both arms. It overrides conflicting task-level allowances and discloses
turns, agent time, output-token limits, and configured resource overrides, plus
how waiting and debugging consume the budget. No live countdown is provided.
The original public-data Docker build and separate hidden verifier
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
`MODEL_ID` with the chosen model; the completed pilot used `gpt-6-luna`. The runner
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
random seed. The runner freezes a private task copy, the guidance, the common
runtime notice, file hashes, model, backend, concurrency, order, and resource
settings in `plan.json`. It checks for changed task,
guidance, runtime notice, runner, or dependency declarations before execution
and each trial. It also checks that the notice matches the configured limits.
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
validation has since passed too. The fresh A/B comparison has since completed. No host repository or hidden data
is added to the agent's mounts; access boundaries rely on the original task's
Docker allowlists and Harbor's separate verifier.

Only after validating the model and pilot limits, launch paid trials explicitly:

```sh
.venv/bin/python experiments/verifier-context/compare.py run \
  experiments/verifier-context/runs/pilot-01 \
  --allow-paid --max-total-cost-usd 2
```

The dollar value above is an example **stop threshold, not a hard billing cap**.
The runner checks accumulated reported cost before starting another trial; every
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
  --backend daytona --concurrency 19 --cpus 4 --memory-gb 8 --storage-gb 10
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
`cloud-cleanup.json`. Result collection or report-writing failures cannot skip
this cleanup attempt; reporting errors still propagate, and a failed cleanup
report write cannot prevent the Daytona client from closing. Offline regression
tests inject disk-full failures for execution metadata and each summary output,
after successful and failed trials, plus result-collection and cleanup-report
failures. These tests do not establish live deletion during a controller disk
failure. Cleanup failures must be resolved in Daytona. Auto-stop
measures inactivity, not total runtime, and is not a spending cap. A killed
launcher can leave resources until fallback cleanup occurs.

The reported dollar threshold and `cost_usd` cover model API usage only.
Daytona compute/storage charges are separate; consult its billing records.
No automatic snapshots are created by the runner. Cloud costs depend on
allocation, image builds, research time, verification time, and cleanup.

## Reading the results

Private `runs/` folders include experiment data, controller operations, aborted
startups, and environment checks. They are not all separate experiments or A/B
conditions. The local `runs/README.md` indexes them: `daytona-03` is the completed
Luna comparison and `astra-02` is the stopped Astra study. Each study contains
both arms under `trials/`. Prefer its private `analysis-report.md` for the
expanded outcome, distribution, and cancellation analysis; original runner and
cohort reports remain preserved alongside it.

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

Do not assess a condition by its accepted-score mean alone. Analysis reports
must also show valid-submission rates with explicit denominators, all status
counts, median and range, and the individual accepted ICs. For a partial report,
separate running and unstarted positions from finished outcomes. For a completed
attempt, distinguish agent/submission failures, infrastructure errors, and
operator cancellations, and explain any externally imposed cutoff. Report the
official task rewards, including verifier-issued failure penalties, separately
when available, with their coverage. Do not invent rewards for execution errors
or unstarted trials, or present a penalty-inclusive reward as forecasting IC.

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
19 research/verifier sandboxes in parallel plus one trusted controller, with the same four-CPU / 8 GiB / 10 GiB allocation for both arms.
The complete cloud reference flow then passed, including separate hidden scoring,
with IC 0.518312997231824, matching the local reference to floating-point precision.
It made no model API calls and is excluded from A/B results. Reference and probe
sandbox deletion were verified before the cloud comparison started.

The first 20-rollout cloud startup was stopped before any model response was
observed: simultaneous trials hit Daytona session-command timeouts while
starting Docker. Harbor synchronously gzipped each large upload on a shared
controller event loop; one measured archive took 17 seconds, exceeding other
trials’ 10-second RPC timeouts. This is an infrastructure failure, not evidence
about either condition. Its artifacts are preserved, and deletion of all study
sandboxes was independently verified.

Cloud trials now run in separate controller processes through the same native
Harbor backend, so compression in one trial cannot block another trial’s RPCs.
Both arms use this execution path. Cancellation interrupts each child, waits
for cleanup, forcibly reaps a stalled child if needed, then audits study-wide
sandbox deletion. The process change requires a fresh frozen study.

A second startup with isolated workers passed Docker startup, but repeating a
260.5 MiB upload twenty times saturated the local connection. It was stopped
before any model usage was observed, and its independent cleanup watchdog
verified deletion. Preserve this staging failure separately too.

The next 20-rollout study places the trusted controller in its own Daytona
sandbox, transfers the frozen task once, and starts up to 19 independent trial
sandboxes from there. A worker pool starts the final queued rollout when a slot
frees, keeping at most 20 sandboxes including the controller. The controller holds
credentials and the full private task, just as the local controller did; neither
is mounted in research sandboxes. Research environments receive only their
original public build context, and hidden data is staged into separate verifier
sandboxes. Download private results before deleting the controller.

The cloud controller uses the same frozen runner, agent settings, and guidance. Its private launcher monitors reported
trajectory costs and cancels at $1.75 of observed API usage including the prior
local pilot and smoke request, leaving headroom below the $2 target. Reported
usage can lag in-flight requests, so this remains a guard rather than a hard cap.
Daytona charges remain separate.

The study completed all 20 accepted submissions on runner revision `6bf56cf`,
with reported model usage of $0.143722165 ($0.15949155 including the prior local
pilot and smoke request). Its frozen inputs, initial prompts, and official score
contracts passed the completion audit. Per-trial scores and the final comparison
remain in the private, ignored run artifacts; they are not published in this PR.
A small pilot does not establish statistical significance or OPCD distillability.

After all scores were saved, the controller's first cleanup audit encountered a
Daytona HTTP 409 because the last sandbox was already changing state. The host
supervisor downloaded results and verified deletion, and its independent watchdog
separately confirmed that both the controller and all trial sandboxes were gone.
The original failed remote audit is preserved. The runner now retries this
transient conflict, checks final absence, and fails if any owned resource remains.
This cleanup-only fix follows the completed study; prepare a fresh study for any
new paid run rather than rewriting its frozen runner hash.

### Corrected-budget Astra rerun

The user authorized a fresh Astra comparison on 2026-10-24: 20 rollouts per arm,
a $40 model-API spending target, and modest Daytona hosting extra. The private
study is `runs/astra-03`; its operator scripts, reference checks, and controller
records live together under `ops/`. Historical studies remain separate.

Both arms receive the corrected runtime notice, including possible study-wide
spending or infrastructure interruptions. Settings are 30 turns, 1,800 agent
seconds, 4,096 output tokens per response, and six concurrent trials. Each trial
uses 4 CPUs, 8 GiB RAM, and 10 GiB disk within the account's sandbox limits.
The reused detached supervisor monitors usage, checks actual initial prompts,
and retains results on the stopped controller until verified download and deletion.
Its live usage guard is $30 to leave room below the $40 target for in-flight
calls; neither amount is a hard billing cap. Reference validation must pass
before paid agent rollouts start. This preparation is not a claim of completed
rollouts or improved results.

### Historical Astra follow-up

The user requested a separate comparison with `openai/gpt-6-astra`: 20 baseline
rollouts and 20 with the same research Markdown. The fresh study preserves the
task and guidance hashes, 30-turn / 1,800-second agent limits, low reasoning,
4,096 output tokens per request, and equal cloud resources. It uses up to 19
trial sandboxes plus one trusted controller. Its API spending target is $40,
with the private launcher cancelling at $30 of observed usage to leave room for
in-flight calls; hosting is separate. Neither threshold is a hard billing cap.

This follow-up uses a detached private supervisor in the controller, including
its usage monitor, two-hour execution deadline, and a separate cloud watchdog.
The laptop uploads and starts the study, then is not required for execution or
trial cleanup. Trial sandboxes are deleted; the controller stops after saving
the results and a checksummed archive on its own disk. Its automatic deletion
is disabled, so it can retain the private results while the laptop is closed.
Retrieve and verify the archive before deleting that final sandbox. A stopped
controller continues to incur storage charges until deletion. This retention
policy applies to this private launcher; `compare.py run` alone does not provide
detached supervision or retain a controller.

Daytona denied persistent-volume creation with the available key (HTTP 403);
no volume was created. Following the user's choice to use sandboxes, a real
controller stop/start test verified that its files survive. Offline supervisor
checks verified archive checksums, exclusion of the frozen hidden task from the
download archive, and preservation of cleanup-failure evidence. These checks
do not establish completion of the 40 paid rollouts. The detached study was
launched on 2026-10-23, and its supervisor, cloud watchdog, usage monitor, and 19
worker processes were observed running. That established launch, not completion.
The study was later stopped after the
budget-disclosure audit below. Its archive has been downloaded and checksum
verified, and independent checks confirm deletion of every trial/cohort sandbox
and the retained controller. It did not complete the planned 40-rollout
comparison; private reports distinguish completed, cancelled, incomplete, and
unstarted positions.

One initial sandbox failed to start its Docker daemon before agent setup or any
model execution. Its missing usage record correctly stopped further launches in
that cohort. Preserve that failed trial and its raw result; a separate cost
attestation records the environment-preparation traceback as evidence of zero
model calls. A controlled handover prepared a continuation of only unstarted
original pair/arm positions under the shared budget and deadline. A subsequent
budget-disclosure audit identified the mismatch below. One continuation cohort
had already started before the supervisor handover; it was gracefully cancelled
to stop further paid execution. Further cohort launches were disabled. Preserve
completed results, cancelled attempts, and unstarted positions separately, with
their spending, cleanup, and retention records. No failed or previously billed
trial is restarted.

### Execution-budget disclosure finding

The original task tells the agent it has four hours. Both historical pilots enforced
30 agent turns and a 1,800-second agent timeout. The observed prompts disclose
neither those actual limits nor a remaining-turn countdown. Harbor's artificial
turn-limit warning is operator logging, not a message to the model. Keeping the
same hidden cap in both conditions does not establish that either agent knew it.

All four initially inspected Astra `missing_submission` rejections reached the
30-turn cutoff while still researching or waiting for operations. Those failures
must not be described as ignoring a known turn budget. Preserve the pilot's plans,
prompts, and raw outcomes with this qualification.

The updated runner prepares schema-version-2 studies with the shared runtime
notice described above. Offline tests assemble both initial prompts using the
pinned Harbor task loader and Terminus 2 prompt template. They verify that the
actual limits override the four-hour allowance and that only research guidance
differs between arms. Existing pilot records remain unchanged; prepare a new
directory to use the corrected runner. This follows the
[agent-awareness documentation rules](../../docs/DOCUMENTATION.md).

This change addresses disclosure. It has not been validated in a fresh paid
cloud rollout, and it does not repair the server/DNS failures observed in the
stopped study. Diagnose those failures and verify the delivered prompt in any
authorized follow-up before interpreting its results.

Offline tests use synthetic task and verifier fixtures. Run all project tests
with the installed runner dependencies to include the Harbor instruction/schema
contract test:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Project implementation gaps and validation work remain in
[the OPCD TODO](../../docs/TODO.md); repository changes follow
[the development workflow](../../docs/WORKFLOW.md).
