const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');

const workflow = readFileSync(`${__dirname}/../.github/workflows/review-comparison.yml`, 'utf8');
const source = workflow.slice(workflow.lastIndexOf('          script: |\n') + '          script: |\n'.length)
  .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const verify = new AsyncFunction('github', 'context', 'core', 'setTimeout', source);

function fixture({ findings = false, missing = null, stale = false, finalized = true,
  projectFailed = false, sourceChanged = false, wrongParents = false, moveDuringPublication = false,
  eventName = 'workflow_dispatch', permission = 'write' } = {}) {
  const pull = { number: 6, state: 'open', head: { sha: 'head' }, base: { sha: 'base', ref: 'main' }, merge_commit_sha: 'merge' };
  const names = ['Project checks', 'Agent reviews completed', 'Documentation reviewer', 'Implementation reviewer'];
  const checks = names.map((name, index) => ({ id: index + 1, name, head_sha: 'head',
    app: { slug: 'github-actions' }, status: 'completed', conclusion: 'success',
    external_id: `${name}:complete`, html_url: `https://github.com/example/checks/${index + 1}`,
    output: { text: JSON.stringify({ pullNumber: 6 }) } }));
  checks[0].output.text = JSON.stringify({ pullNumber: 6, sourceNativeCheckId: 10, base: 'base', baseRef: 'main' });
  const native = { id: sourceChanged ? 11 : 10, name: 'Run project verification', head_sha: 'head',
    app: { slug: 'github-actions' }, status: 'completed', conclusion: projectFailed ? 'failure' : 'success',
    html_url: 'https://github.com/example/native-project-result' };
  if (findings) checks[2].conclusion = 'failure';
  if (projectFailed) checks[0].conclusion = 'failure';
  if (!finalized) checks[2].external_id = 'unfinalized';
  const reports = checks.slice(2).map(check => ({ version: 1, kind: 'review', id: check.name,
    checkId: check.id, head: 'head', base: stale ? 'old-base' : 'base', baseRef: 'main',
    outcome: findings && check.name === 'Documentation reviewer' ? 'findings' : 'clear' }));
  const comments = reports.map(report => ({ user: { login: 'github-actions[bot]' },
    body: `<!-- review-agent-result:${Buffer.from(JSON.stringify(report)).toString('base64url')} -->` }));
  const created = [], updated = [], failures = [];
  let pullReads = 0, sleeps = 0;
  const github = { rest: {
    pulls: { get: async () => {
      pullReads++;
      return { data: moveDuringPublication && pullReads >= 3 ? { ...pull, head: { sha: 'new-head' } } : pull };
    } },
    git: { getCommit: async () => ({ data: { parents: (wrongParents ? ['old-base', 'head'] : ['base', 'head']).map(sha => ({ sha })) } }) },
    repos: { getCollaboratorPermissionLevel: async () => ({ data: { permission } }) },
    actions: { getJobForWorkflowRun: async () => ({ data: { id: native.id, name: native.name, run_id: 44,
      status: native.status, conclusion: native.conclusion } }),
    getWorkflowRun: async () => ({ data: { path: '.github/workflows/verify.yml', event: 'pull_request', head_sha: 'head',
      pull_requests: [{ number: 6, head: { sha: 'head' }, base: { sha: 'base', ref: 'main' } }] } }) },
    issues: { listComments: 'comments' },
    checks: { listForRef: 'checks', create: async value => {
      const check = { id: 100 + created.length, app: { slug: 'github-actions' }, conclusion: null, ...value };
      created.push(check);
      return { data: check };
    }, update: async value => { updated.push(value); return { data: value }; } },
  }, paginate: async (method, args) => {
    if (method === 'comments') return comments;
    assert.equal(method, 'checks');
    assert.equal(args.ref, 'head');
    return [...checks, ...(missing === 'Project checks' ? [] : [native])].filter(check => check.name !== missing);
  } };
  return { created, updated, failures, checks, get pullReads() { return pullReads; }, get sleeps() { return sleeps; },
    run: () => verify(github, { repo: { owner: 'example', repo: 'project' }, eventName,
      payload: { inputs: { pull_request_number: '6' }, issue: { number: 6 }, comment: { user: { login: 'human' } } } },
    { setFailed: message => { failures.push(message); } }, callback => { sleeps++; callback(); }) };
}

test('real successful head checks and finalized current reviews produce linked attestations only on the verified test merge', async () => {
  const f = fixture();
  await f.run();
  assert.deepEqual(f.failures, []);
  assert.equal(f.created.length, 5);
  assert.ok(f.created.every(check => check.head_sha === 'merge'));
  for (const source of f.checks) {
    const attestation = f.created.find(check => check.name === source.name);
    assert.equal(attestation.conclusion, 'success');
    assert.equal(attestation.details_url, source.html_url);
    assert.equal(JSON.parse(attestation.output.text).sourceCheckId, source.id);
  }
  assert.equal(f.updated.at(-1).conclusion, 'success');
});

test('completed review with unresolved findings cannot produce passing attestations even when completion passed', async () => {
  const f = fixture({ findings: true });
  await f.run();
  assert.equal(f.checks[1].conclusion, 'success');
  assert.equal(f.created.length, 1);
  assert.equal(f.updated.at(-1).conclusion, 'failure');
  assert.equal(f.sleeps, 0, 'A comparison must release the shared queue instead of waiting for a queued review.');
});

test('every required source check must be present and passing', async () => {
  for (const missing of ['Project checks', 'Agent reviews completed', 'Documentation reviewer', 'Implementation reviewer']) {
    const f = fixture({ missing });
    await f.run();
    assert.ok(!f.created.some(check => check.head_sha === 'merge' && check.conclusion === 'success'), missing);
    assert.equal(f.updated.at(-1).conclusion, 'failure', missing);
  }
  const failed = fixture({ projectFailed: true });
  await failed.run();
  assert.equal(failed.created.length, 1);
  assert.equal(failed.updated.at(-1).conclusion, 'failure');
});

test('stale comparison evidence and unfinalized review checks cannot pass', async () => {
  for (const options of [{ stale: true }, { finalized: false }]) {
    const f = fixture(options);
    await f.run();
    assert.equal(f.created.length, 1);
    assert.equal(f.updated.at(-1).conclusion, 'failure');
  }
});

test('wrong merge parents never receive a check or attestation', async () => {
  const f = fixture({ wrongParents: true });
  await f.run();
  assert.equal(f.created.length, 0);
  assert.equal(f.failures.length, 1);
});

test('a comparison that moves during publication cannot receive a successful comparison result', async () => {
  const f = fixture({ moveDuringPublication: true });
  await f.run();
  assert.equal(f.updated.at(-1).conclusion, 'failure');
  assert.ok(!f.updated.some(check => check.conclusion === 'success'));
});

test('unprivileged comment requests cannot publish checks', async () => {
  const f = fixture({ eventName: 'issue_comment', permission: 'read' });
  await f.run();
  assert.equal(f.created.length, 0);
});

test('comparison and reviewer publication use the same non-canceling queue', () => {
  const reviewer = readFileSync(`${__dirname}/../.github/workflows/documentation-review.yml`, 'utf8');
  assert.ok(reviewer.includes('group: documentation-review-${{ github.event.pull_request.number || github.event.issue.number || inputs.pull_request_number }}'));
  assert.ok(workflow.includes('group: documentation-review-${{ needs.authorize.outputs.number }}'));
  assert.ok(workflow.includes('queue: max\n      cancel-in-progress: false'));
});

const reviewerWorkflow = readFileSync(`${__dirname}/../.github/workflows/documentation-review.yml`, 'utf8');
const resolverSource = reviewerWorkflow.split('          script: |\n')[1].split(/\n {6}- /)[0]
  .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
const resolveReview = new AsyncFunction('github', 'context', 'core', resolverSource);

async function invalidate({ permission = 'write', stale = false, wrongParents = false } = {}) {
  const created = [];
  const github = { rest: {
    pulls: { get: async () => ({ data: { state: 'open', head: { sha: 'head' },
      base: { sha: 'base' }, merge_commit_sha: 'merge' } }) },
    repos: { getBranch: async () => ({ data: { commit: { sha: 'accepted' } } }),
      getCollaboratorPermissionLevel: async () => ({ data: { permission } }) },
    git: { getCommit: async () => ({ data: { parents: (wrongParents ? ['head', 'old-base'] : ['head', 'base']).map(sha => ({ sha })) } }) },
    checks: { create: async value => { created.push(value); return { data: value }; } },
  } };
  const head = stale ? 'b'.repeat(40) : 'a'.repeat(40);
  github.rest.pulls.get = async () => ({ data: { state: 'open', head: { sha: 'a'.repeat(40) },
    base: { sha: 'base' }, merge_commit_sha: 'merge' } });
  github.rest.git.getCommit = async () => ({ data: { parents: [
    { sha: 'a'.repeat(40) }, { sha: wrongParents ? 'old-base' : 'base' },
  ] } });
  await resolveReview(github, { repo: { owner: 'example', repo: 'project' }, eventName: 'pull_request_target',
    payload: { pull_request: { number: 6, head: { sha: head } }, sender: { type: 'User', login: 'human' },
      repository: { default_branch: 'main' } } }, { setOutput() {} });
  return created;
}

test('authorized reassessment invalidates all five merge checks before changing any head result', async () => {
  const created = await invalidate();
  assert.equal(created.length, 5);
  assert.ok(created.every(check => check.head_sha === 'merge' && check.status === 'in_progress' && !check.conclusion));
  assert.ok(created.some(check => check.name === 'Current review comparison'));
});

test('unauthorized or stale requests and wrong merge parents cannot invalidate merge checks', async () => {
  for (const options of [{ permission: 'read' }, { stale: true }, { wrongParents: true }]) {
    assert.deepEqual(await invalidate(options), []);
  }
});

test('completion of project verification refreshes comparison after tests finish last', async () => {
  assert.ok(workflow.includes('workflows: [API agent reviews, Verify project]'));
  const authorizationSource = workflow.split('          script: |\n')[1].split(/\n\s*comparison:/)[0]
    .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
  const authorize = new AsyncFunction('github', 'context', 'core', authorizationSource);
  const outputs = {};
  await authorize({ rest: { pulls: { get: async () => ({ data: { state: 'open', head: { sha: 'head' } } }) },
    repos: { getCollaboratorPermissionLevel: async () => ({ data: { permission: 'write' } }) } } },
    { repo: { owner: 'example', repo: 'project' }, eventName: 'workflow_run', payload: {
      workflow_run: { path: '.github/workflows/verify.yml', event: 'pull_request', head_sha: 'head',
        pull_requests: [{ number: 6 }], actor: { type: 'User', login: 'human' } },
    } }, { setOutput: (key, value) => { outputs[key] = value; } });
  assert.equal(outputs.number, '6');
  assert.equal(outputs.allowed, 'true');
});

test('project reassessment invalidates merge copies before changing its required head result', async () => {
  const f = fixture({ projectFailed: true, sourceChanged: true });
  await f.run();
  const headUpdate = f.created.findIndex(check => check.name === 'Project checks' && check.head_sha === 'head');
  assert.ok(headUpdate > 0);
  assert.equal(f.created[headUpdate].conclusion, 'failure');
  for (const name of ['Project checks', 'Agent reviews completed', 'Documentation reviewer', 'Implementation reviewer']) {
    assert.ok(f.created.slice(0, headUpdate).some(check => check.name === name && check.head_sha === 'merge' && check.status === 'in_progress'));
  }
  assert.equal(f.updated.at(-1).conclusion, 'failure');
  const verification = readFileSync(`${__dirname}/../.github/workflows/verify.yml`, 'utf8');
  assert.ok(verification.includes('name: Run project verification'));
  assert.ok(!verification.includes('checks: write'), 'Untrusted test execution must retain read-only permissions.');
});
