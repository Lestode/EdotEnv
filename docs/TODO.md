# OPCD implementation TODO

Status, 2026-10-24: source inspection and implementation plan, plus verified Komondor login and a completed single-GPU inventory probe. No OPCD-specific implementation or GPU training validation has been completed. Findings below refer to the local Slime checkout at `18868a79`; cluster evidence is in [hardware planning](HARDWARE.md).

Scope, decisions, assumptions, and open/deferred questions are maintained in [AGENTS.md](../AGENTS.md). Hardware findings and the GPU validation sequence are maintained in [HARDWARE.md](HARDWARE.md).

## What Slime already provides, and what is missing

Slime can be extended to use different teacher and student contexts. Its bundled OPD implementation does not construct those separate inputs automatically.

| Area | Existing local Slime behavior | OPCD adaptation |
| --- | --- | --- |
| Student rollouts | Student generation already produces response token IDs and log probabilities. | Preserve the student-only input; collect or compute the student top-256 IDs at each response prefix. |
| External teacher | The [OPD scorer](../slime/slime/rollout/on_policy_distillation.py) sends `sample.tokens` directly to the teacher. | Build a separate teacher prefix and append the exact student response token IDs. |
| Megatron teacher | The [actor](../slime/slime/backends/megatron_utils/actor.py) switches to teacher weights and reuses the student data iterator. | Separate teacher inputs would require additional batching work; an external teacher is the proposed initial route. |
| Objective | [Built-in OPD](../slime/slime/backends/megatron_utils/loss.py) subtracts a sampled-token student/teacher log-probability difference from advantages. | Add a differentiable top-256 reverse-KL loss through the custom loss hook. Changing the teacher prompt alone does not implement the requested objective. |
| Top-k data | [Sample](../slime/slime/utils/types.py) and score-centering code already support rollout top-k IDs/log probabilities. | Reuse suitable capture and tensor utilities after checking their probability semantics; add aligned teacher scores. Score centering itself is not the OPCD loss. |
| Distributed execution | Ray orchestration, rollout transport, and Megatron parallel training already exist. | Connect the new scoring stage and tensors to these paths and validate distributed alignment and gradients. |

## Implementation checklist

### 1. Separate contexts and preserve response alignment

- [ ] Define each dataset example with a stable sample ID, student messages, and a reference to the teacher-only context. Implement context lookup inside the teacher scorer. Student generation and training payloads must contain no resolved teacher-only text, including in metadata.
- [ ] Build the student prompt from the student messages, and the teacher prompt from those messages plus the resolved teacher-only context. Apply each model's chat template, including the assistant-start marker that precedes its answer. Store the teacher prompt separately; leave Slime's student fields, `sample.prompt` and `sample.tokens`, unchanged.
- [ ] Add a tokenizer compatibility check before generation or scoring. Verify that both models use the same token-ID-to-token mapping and compatible text encoding and special-token conventions; equal vocabulary sizes alone are insufficient. Fail with an explicit error for unsupported pairs.
- [ ] Construct the teacher scoring sequence as `teacher_prompt_ids + student_response_ids`, copying the response IDs directly from the student rollout without decoding and retokenizing them. Record the answer's start index separately for each sequence because the prompts can have different lengths. The teacher scores the student's continuation; it does not generate a replacement answer.
- [ ] Add alignment and boundary tests. For response token `i` (counting from zero), verify that both models' scores condition on their own prompt plus response tokens before `i`, never on token `i` or later tokens. Cover beginning/end-of-sequence (BOS/EOS) handling, loss masks that select scored answer positions, empty answers, and model context limits. Reject inputs that would require silently truncating either prompt or the scored response.

Completion evidence: captured student generation requests and student training inputs exclude a synthetic teacher-only marker; teacher requests include it; every scored row maps to the intended student response prefix.

### 2. Obtain teacher probabilities on student-selected support

- [ ] Establish when student top-256 support is selected and how it reaches the scorer. Keep support and targets consistent with the student policy used for the loss; record policy versions and refresh support/targets if updates make cached support stale.
- [ ] Verify the chosen teacher backend can return log probabilities for **arbitrary student-selected token IDs at each input position**, including IDs outside the teacher's own top 256. Sampled-token log probabilities or teacher top-k alone are insufficient.
- [ ] Implement a batched scoring adapter over teacher prefix plus student response. Return aligned `[response_length, 256]` teacher log probabilities and support IDs, with shape/ID/finite-value validation.
- [ ] If the selected SGLang version cannot supply these per-position scores efficiently, implement a teacher forward/scoring service that gathers them from logits. This capability is not established by Slime's existing OPD example.
- [ ] Run the teacher in evaluation mode without optimizer updates or student weight synchronization; pin its checkpoint/version.

Completion evidence: scores match a direct frozen-teacher forward on a small compatible model pair, including student-selected IDs that are absent from the teacher's top-k.

### 3. Implement the OPCD objective

- [ ] Add a custom loss that computes `sum(p_student * (log_p_student - log_p_teacher))` over the student-selected 256 IDs at each response position, then applies response masks and sequence averaging.
- [ ] Compute student probabilities from current differentiable logits. Cached rollout log probabilities may help select or validate support but cannot supply the student gradient.
- [ ] Document normalization and temperature conventions against [Equation 2 of the OPCD paper](https://arxiv.org/html/2602.12275v1); distinguish restricting the full-distribution sum from renormalizing the selected support. The paper does not explicitly describe a top-k renormalization step.
- [ ] Handle vocabulary-sharded logits correctly: global top-256 selection, full-vocabulary normalization, and probability gathering across tensor-parallel ranks.
- [ ] Configure the custom-loss path so built-in sampled-token OPD, task rewards, and unrelated policy-loss terms do not silently alter the intended pure distillation objective.

Completion evidence: loss and gradients match a small direct PyTorch reference, masked positions contribute zero, and teacher parameters remain unchanged after a student update.

### 4. Carry targets through distributed training

- [ ] Add explicit aligned support IDs and teacher-score tensors to sample conversion and training batches. Keep teacher-only text out of training data and student logs/debug dumps; audit serialization of metadata as well as prompts.
- [ ] Verify tensor serialization, DP partitioning, sample reordering, packed sequences, CP slicing, pipeline stages, and microbatch key selection preserve support/target alignment.
- [ ] Reuse existing top-k transport utilities where appropriate; add the missing fields and narrow plumbing changes rather than repurposing sampled-token `teacher_log_probs` with an incompatible shape.
- [ ] Batch and distribute teacher scoring with bounded concurrency and timeouts. Preserve sample identity on retries and fail explicitly on missing/incomplete scores.
- [ ] Provide a launch configuration for student rollout workers, student trainers, and a separately managed frozen teacher pool. Configure teacher parallelism/replicas independently of the student.

Completion evidence: single-worker and distributed runs agree on loss/gradients within numerical tolerance, including uneven sequence lengths and batches split across ranks.

### 5. Validate progressively

- [ ] Run local tests for context separation, alignment, objective gradients, and tensor transport using synthetic inputs and a mock scorer.
- [x] Complete Komondor authentication through the existing gateway setup under the [protected-infrastructure rule](../AGENTS.md#protected-infrastructure-greengoblin); inspect project access, balances, quotas, partitions, and runtime modules, and verify a one-GPU Slurm allocation. See [inventory evidence](HARDWARE.md#single-gpu-inventory-evidence).
- [ ] Establish a working container/cache/output layout that accommodates the scratch file-count limit; validate Slime dependencies and GPU passthrough on allocated Komondor resources before model execution.
- [ ] Execute the [GPU validation sequence](HARDWARE.md#proposed-validation-sequence), checking teacher immutability, fresh student rollouts, and context separation throughout.
- [ ] Record working commands, pinned dependencies/checkpoints, and measured memory/throughput.

## Proposed extension points

Use `--custom-generate-function-path` if rollout capture needs customization; `--custom-rm-path` for teacher scoring; `--custom-reward-post-process-path` for score extraction where useful; `--custom-convert-samples-to-train-data-path` for OPCD batch construction; and `--loss-type custom_loss --custom-loss-function-path ...` for the objective.

These are integration points, not a claim that hooks alone cover every requirement. The [batch builder](../slime/slime/data/batch_builder.py), [training batch loader](../slime/slime/backends/megatron_utils/model.py), and [actor tensor handling](../slime/slime/backends/megatron_utils/actor.py) have explicit field handling that must be checked when adding OPCD tensors.

## Markdown guidance final-score comparison

The [experiment](../experiments/verifier-context/README.md) defines the comparison,
execution commands, result semantics, and validation status. It is a task-level
pilot; it does not implement OPCD training or establish distillability.

- [x] Implement frozen task/guidance preparation, identical Harbor settings for
  both arms, alternating trial order, explicit paid execution, and cost stop
  handling without claiming a hard billing cap.
- [x] Add synthetic CPU tests for condition differences, changed inputs,
  rejected/missing/corrupt scores, valid zero/negative scores, cost stops, and
  repeat-execution refusal; validate the pinned Harbor instruction/config contract.
- [x] Isolate cloud cleanup from result collection and reporting; add offline
  regressions for disk-full execution/summary writes after successful and failed
  trials, result-collection errors, and client closure after cleanup-report failure.
- [x] Preserve chained cleanup failures in command output; test simultaneous
  sandbox-deletion and cleanup-report disk errors without cloud calls.
- [x] Implement collection of final hidden IC, failure counts, and per-trial evidence;
  keep the licensed task and private run outputs out of the public repository.
- [x] Validate Docker builds, MCP connectivity, submission artifact transfer, and
  separate verifier execution locally with the reference solution; record the
  host dependency startup failure and adapter regression test in the experiment.
- [x] Select GPT-6 Luna and obtain authorization for the small local pilot and
  API budget; the experiment records equal limits and the spending stop threshold.
- [x] Preserve the cancelled local pilot and stop its containers/VM; obtain
  authorization for paid Daytona hosting.
- [x] Validate Harbor’s native Daytona Compose path, artifact transfer, separate
  hidden verification, 20-sandbox capacity, and reference/probe cleanup for this
  task; record equal cloud allocations and the larger study’s API target.
- [x] Run and inspect the fresh 20-rollout cloud comparison: ten accepted
  submissions per arm, prompt/frozen-input audits passed, private results
  downloaded, and independent controller/trial deletion verified. Record and fix
  the final cleanup transition conflict without rewriting the completed study.
- [x] Prepare the separate Astra comparison with 20 rollouts per arm and a
  detached private cloud supervisor; validate controller disk retention across
  stop/start and archive verification before eventual deletion.
- [ ] Inspect the Astra comparison's scores, failures, usage, context conditions,
  and frozen inputs before any follow-up. The stopped study's archive is downloaded
  and checksum-verified, and all cloud resources are independently verified deleted;
  the experiment records the disclosure finding and incomplete comparison.
- [x] Correct execution-budget disclosure for newly prepared comparisons: freeze
  a common notice of actual turn/time/output/resource limits and append it last
  in both arms. Offline tests verify Harbor's assembled initial prompts and
  reject notice/configuration drift; preserve the historical pilot evidence.
- [ ] Diagnose the stopped study's server/DNS failures before a follow-up. In any
  newly authorized cloud validation, verify that the delivered prompt contains
  the corrected limits and that research tools work; distinguish undisclosed
  historical truncation from informed agent behavior. No new paid run is launched
  by the disclosure fix.

## Repository workflow validation

The authoritative policy and integration details are in [the development workflow](WORKFLOW.md).

- [x] Accept the shared action's API-key support PR, then pin its accepted full commit SHA in the consumer workflow and documentation links.
- [x] Provision the repository's `OPENAI_API_KEY` Actions secret with access to the pinned model; keep the value out of project files and PR discussion.
- [x] Merge the reviewed setup PR after explicit user acceptance, then verify `Project checks` on the accepted default branch.
- [x] Verify one automatic documentation-review response on a small PR after activation; record its PR and Actions URLs.
- [x] Verify `/review-docs <question>` produces a follow-up response, and a later push is reviewed after a fresh request.
- [x] Enable `main` protection after the repository becomes public: require `Project checks` and `Agent reviews completed` from GitHub Actions, up-to-date branches, PRs, resolved conversations, and administrator enforcement; disallow force pushes and deletion. Settings verified through GitHub's API on 2026-10-23; live rejection tests remain below.
- [x] Provision a read-only deploy key restricted to `Lestode/review-agents` and store its private part as `REVIEW_AGENTS_READ_KEY` in EdotEnv Actions secrets; verify scope and secret metadata without logging credentials.
- [x] Confirm shared reviewer PR #4 is merged and pin its accepted commit; verify its file tree matches the head that passed all 92 tests.
- [x] Validate private checkout, API execution, report publication, and a passing exact-head agent check through the feature-branch bootstrap run recorded in the development workflow.
- [x] Activate the documentation-only consumer workflow after user acceptance without bypassing its required completion gate; EdotEnv PR #4 was merged on 2026-10-23. The later automatic review on PR #5 confirms the accepted workflow runs after an update; see the activation record in the development workflow.
- [ ] Verify a real completed review passes only for its captured PR head, a new push automatically requests another review, duplicate completed requests do not repeat billing, and stale, skipped, failed, or unpublished reviews cannot allow merging. Confirm merge blocking through GitHub's merge state without attempting an unauthorized merge or direct push.
- [ ] Add CPU regression tests alongside each OPCD implementation step and extend CI for its dependencies; retain separate GPU/distributed run evidence.
- [ ] Run the merged reviewer freshness workflow manually and record its Actions URL; verify the scheduled run and the live alert lifecycle when an upstream update is available. Git-history and alert-lifecycle regression tests run in `Project checks`.
- [x] Exercise private checkout, execution, publication, and exact-head checks for both shared PR #3 reviewer actions on EdotEnv PR #5 using explicit bootstrap; the initial results and final-review requirement are recorded in the development workflow.
- [ ] Validate the two-reviewer integration merged in PR #5: automatic implementation review, a fresh review after an update, `/review-implementation` discussion, and the no-model implementation assessment for a Markdown-only PR.
- [x] Activate the prepared five-check protection on `main`, preserving every other branch-protection setting. Verify readback and live blocking of PR #6 with an unresolved finding and an incomplete documentation assessment; exact revisions, check/report links, and coverage limits are recorded in the [activation evidence](WORKFLOW.md#activation-and-enforcement-status).
- [x] Verify the isolated completed-review-with-findings case while completion passes, and user-authorized reasoned dismissals through the shared mechanism. The [activation evidence](WORKFLOW.md#activation-and-enforcement-status) records the real review, dismissal receipts, and check results.
- [x] Verify partial dismissal still blocks: the first recorded dismissal left the second finding unresolved and its run failed; see the [activation evidence](WORKFLOW.md#activation-and-enforcement-status).
- [ ] Finish live missing-review and stale-head scenarios under the latest-head policy. Keep incomplete reviews within the agreed scope blocking; do not fabricate checks or dismiss findings without authorization.
- [x] Activate the user-selected latest-head requirements and disable the obsolete comparison workflow: require project checks and both named reviewer checks, remove the comparison/completion-only requirements, and verify every other protection is unchanged; see [activation readback](WORKFLOW.md#latest-head-policy-transition). The earlier test-merge placement repair is superseded for this consumer, not claimed fixed upstream.
- [ ] After accepting the scope configuration, verify a fresh commit cannot inherit successful reviews and that out-of-scope private audits remain explicit coverage notes rather than blocking the public-change review. Verify a normal protected merge under the three-check policy.
