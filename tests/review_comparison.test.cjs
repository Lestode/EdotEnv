const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');

const workflow = readFileSync(`${__dirname}/../.github/workflows/review-comparison.yml`, 'utf8');
const source = workflow.slice(workflow.lastIndexOf('          script: |\n') + '          script: |\n'.length)
  .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const verify = new AsyncFunction('github', 'context', 'core', 'setTimeout', source);

function fixture({ findings = false, missing = null, stale = false, finalized = true,
  projectFailed = false, wrongParents = false, moveDuringPublication = false,
  eventName = 'workflow_dispatch', permission = 'write' } = {}) {
  const pull = { number: 6, state: 'open', head: { sha: 'head' }, base: { sha: 'base', ref: 'main' }, merge_commit_sha: 'merge' };
  const names = ['Project checks', 'Agent reviews completed', 'Documentation reviewer', 'Implementation reviewer'];
  const checks = names.map((name, index) => ({ id: index + 1, name, head_sha: 'head',
    app: { slug: 'github-actions' }, status: 'completed', conclusion: 'success',
    external_id: `${name}:complete`, html_url: `https://github.com/example/checks/${index + 1}`,
    output: { text: JSON.stringify({ pullNumber: 6 }) } }));
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
    issues: { listComments: 'comments' },
    checks: { listForRef: 'checks', create: async value => {
      const check = { id: 100 + created.length, ...value };
      created.push(check);
      return { data: check };
    }, update: async value => { updated.push(value); return { data: value }; } },
  }, paginate: async (method, args) => {
    if (method === 'comments') return comments;
    assert.equal(method, 'checks');
    assert.equal(args.ref, 'head');
    return checks.filter(check => check.name !== missing);
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
    assert.equal(f.created.length, 1, missing);
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
