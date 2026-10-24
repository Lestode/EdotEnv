const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { mkdtempSync, mkdirSync, writeFileSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { test } = require('node:test');
const { comparison, report, MARKER } = require('../scripts/reviewer_freshness.cjs');

test('compares real Git history and rejects missing pins or divergent history', t => {
  const root = mkdtempSync(join(tmpdir(), 'reviewer-freshness-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, '.github/workflows'), { recursive: true });
  const git = (...args) => execFileSync('git', ['-C', root, ...args], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
  git('init');
  git('config', 'user.name', 'Test');
  git('config', 'user.email', 'test@example.invalid');
  let sequence = 0;
  const commit = () => {
    git('-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-m', `Fixture ${sequence++}`);
    return git('rev-parse', 'HEAD');
  };
  const pin = sha => writeFileSync(join(root, '.github/workflows/documentation-review.yml'),
    `repository: Lestode/review-agents\n  # Accepted reviewer.\n  ref: ${sha}\n`);
  const first = commit();
  pin(first);
  assert.deepEqual(comparison(root, root), { pinned: first, latest: first });
  const second = commit();
  assert.deepEqual(comparison(root, root), { pinned: first, latest: second });
  pin('a'.repeat(40));
  assert.throws(() => comparison(root, root));
  git('checkout', '--orphan', 'unrelated');
  commit();
  pin(first);
  assert.throws(() => comparison(root, root));
  pin('main');
  assert.throws(() => comparison(root, root), /immutable/);
});

function fixture(issues = []) {
  const calls = [];
  const api = {
    listForRepo() {},
    async create(args) { calls.push({ action: 'create', ...args }); },
    async update(args) { calls.push({ action: 'update', ...args }); },
  };
  return {
    calls,
    github: { rest: { issues: api }, paginate: async () => issues },
    context: { repo: { owner: 'test', repo: 'consumer' } },
    core: { info() {} },
    revisions: { pinned: 'a'.repeat(40), latest: 'b'.repeat(40) },
  };
}

test('current pin creates no alert; outdated pin creates one with bounded content', async () => {
  const f = fixture();
  await report({ ...f, revisions: { pinned: 'a'.repeat(40), latest: 'a'.repeat(40) } });
  assert.equal(f.calls.length, 0);
  await report(f);
  assert.equal(f.calls.length, 1);
  assert.equal(f.calls[0].action, 'create');
  assert.ok(f.calls[0].body.startsWith(MARKER));
  assert.match(f.calls[0].body, /compare\/a{40}\.\.\.b{40}/);
  assert.match(f.calls[0].body, /explicit user acceptance/);
});

test('unchanged alert is quiet; changed revisions update it; closed alert reopens', async () => {
  const seed = fixture();
  await report(seed);
  const existing = { ...seed.calls[0], number: 42, state: 'open',
    user: { login: 'github-actions[bot]' } };
  const f = fixture([existing]);
  await report(f);
  assert.equal(f.calls.length, 0);
  f.revisions.latest = 'c'.repeat(40);
  await report(f);
  assert.equal(f.calls[0].issue_number, 42);
  assert.match(f.calls[0].body, /Latest revision: `c{40}`/);
  existing.body = f.calls[0].body;
  existing.state = 'closed';
  await report(f);
  assert.equal(f.calls[1].state, 'open');
  assert.equal(f.calls[1].issue_number, 42);
});

test('catching up closes only bot-authored tracking issues, excluding PRs', async () => {
  const bot = { login: 'github-actions[bot]' };
  const f = fixture([
    { number: 1, state: 'open', body: MARKER, user: bot },
    { number: 2, state: 'closed', body: MARKER, user: bot },
    { number: 3, state: 'open', body: MARKER, user: { login: 'someone' } },
    { number: 4, state: 'open', body: MARKER, user: bot, pull_request: {} },
    { number: 5, state: 'open', body: 'Unrelated issue', user: bot },
  ]);
  f.revisions.latest = f.revisions.pinned;
  await report(f);
  assert.deepEqual(f.calls.map(call => [call.issue_number, call.state]), [[1, 'closed']]);
});

test('an API read failure cannot be reported as current or cause an issue write', async () => {
  const f = fixture();
  f.github.paginate = async () => { throw new Error('Unavailable'); };
  await assert.rejects(report(f), /Unavailable/);
  assert.equal(f.calls.length, 0);
});
