const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');

// Exercise the actual inline workflow script, without secrets or private source.
const workflow = readFileSync(`${__dirname}/../.github/workflows/documentation-review.yml`, 'utf8');
const step = workflow.split('        id: review_config\n')[1];
assert.ok(step, 'The context-preparation step must exist.');
const source = step.split('          script: |\n')[1].split(/\n {6}- /)[0]
  .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const prepare = new AsyncFunction('require', 'context', 'core', 'process', source);

function fixture({ bootstrap = false, acceptedImplementation = !bootstrap } = {}) {
  const accepted = {
    '.github/documentation-review.json': JSON.stringify({
      documentationIndex: 'docs/README.md', instructionsPath: '.github/documentation-review.md',
      command: '/review-docs', markerPrefix: 'documentation-fixture',
    }),
    '.github/documentation-review.md': 'Accepted documentation customization.',
    '.github/implementation-review.md': 'Accepted implementation customization.',
    '.github/workflows/documentation-review.yml': 'const number = Number(5);\nAccepted resolver fixture.\n      - uses: actions/checkout',
  };
  if (acceptedImplementation) accepted['.github/implementation-review.json'] = JSON.stringify({
    documentationIndex: 'docs/README.md', instructionsPath: '.github/implementation-review.md',
    command: '/review-implementation', markerPrefix: 'implementation-fixture', contextPaths: [],
  });
  const privateFiles = {
    'README.md': '### Test-merge review checks\nTest-merge contract fixture.\nFor an optional completion-only check\n## Required reviews before merge\nContract fixture.\n### Legacy head-based checks\n## Implementation review\nImplementation behavior fixture.\nThe collector reads the full accepted target-tip Markdown snapshot\n## Project settings\n',
    'documentation-review/action.yml': 'inputs:\nDocumentation action fixture.\noutputs:',
    'implementation-review/action.yml': 'inputs:\nImplementation action fixture.\noutputs:',
    'implementation-review/SKILL.md': 'Accepted implementation procedure fixture.',
    'KNOWN_ISSUES.md': 'Known limitations fixture.',
    'documentation-review/action.cjs': 'async function readProjectFile() { /* helper fixture */ }\nasync function runAction()',
    'documentation-review/review.cjs': 'const defaults = Object.freeze({});\nfunction projectSettings() {}\nfunction formatResponse()',
    'implementation-review/review.cjs': 'function projectSettings() { /* settings fixture */ }\nasync function collectContext()',
    'documentation-review/check.cjs': '  ledger(includeResult) { /* ledger fixture */ }\n  recover(checks) {}\n  finalized(check, report) { /* publication fixture */ }\n  async reuse(comment)',
  };
  const written = {}, outputs = {}, reads = [];
  const localRequire = name => {
    if (name === 'node:fs') return {
      existsSync: path => Object.hasOwn(accepted, path),
      readFileSync: path => {
        assert.ok(path.startsWith('.review-agent/'));
        const value = privateFiles[path.slice('.review-agent/'.length)];
        if (value === undefined) throw new Error(`Missing private fixture: ${path}`);
        return value;
      },
      writeFileSync: (path, value) => {
        assert.ok(path.startsWith('.review-agent/'), 'Generated context must stay in the ignored private checkout.');
        written[path] = value;
      },
    };
    if (name.endsWith('/documentation-review/action.cjs')) return {
      readProjectFile: async (root, path, limit) => {
        assert.equal(root, '/accepted');
        reads.push(path);
        if (!Object.hasOwn(accepted, path)) throw new Error('Missing accepted file');
        assert.ok(Buffer.byteLength(accepted[path]) <= limit);
        return accepted[path];
      },
    };
    if (name.endsWith('/review.cjs')) return { projectSettings: config => config };
    throw new Error(`Unexpected module: ${name}`);
  };
  return {
    accepted, privateFiles, written, outputs, reads,
    run: () => prepare(localRequire,
      { eventName: bootstrap ? 'workflow_dispatch' : 'pull_request_target',
        payload: { inputs: { bootstrap_implementation: 'true' } } },
      { setOutput: (key, value) => { outputs[key] = value; } },
      { env: { GITHUB_WORKSPACE: '/accepted' } }),
    config: name => JSON.parse(written[outputs[`${name}_path`]]),
  };
}

test('bootstrap supplies the approved contracts to both agents without proposed implementation customization', async () => {
  const f = fixture({ bootstrap: true });
  await f.run();
  const documentation = f.config('documentation'), implementation = f.config('implementation');
  assert.equal(documentation.command, '/review-docs');
  assert.equal(documentation.markerPrefix, 'documentation-fixture');
  assert.equal(implementation.command, '/review-implementation');
  assert.equal(implementation.markerPrefix, 'edotenv-implementation-review');
  const docs = f.written[documentation.instructionsPath], impl = f.written[implementation.instructionsPath];
  assert.ok(docs.includes('Accepted documentation customization.'));
  assert.ok(docs.includes('Accepted implementation procedure fixture.'));
  assert.ok(impl.includes('publication fixture'));
  assert.ok(docs.includes('publication fixture'));
  assert.ok(docs.includes('Accepted resolver fixture.'));
  assert.ok(!impl.includes('Accepted implementation customization.'));
  assert.ok(!f.reads.includes('.github/implementation-review.md'));
  assert.ok(docs.includes('do not reproduce private source'));
  assert.ok(impl.includes('do not reproduce private source'));
  assert.ok(!docs.includes('Review EdotEnv caller integration'),
    'Dependency evidence must not widen the configured documentation assignment.');
  assert.ok(impl.includes('Review EdotEnv caller integration'));
  assert.ok(impl.includes('require an Incomplete assessment'));
});

test('normal mode uses accepted implementation settings and fails if customization is missing', async () => {
  const f = fixture();
  await f.run();
  const config = f.config('implementation');
  assert.equal(config.markerPrefix, 'implementation-fixture');
  assert.ok(f.written[config.instructionsPath].includes('Accepted implementation customization.'));
  delete f.accepted['.github/implementation-review.md'];
  await assert.rejects(f.run(), /Missing accepted file/);
});

test('bootstrap cannot override accepted implementation configuration', async () => {
  const f = fixture({ bootstrap: true, acceptedImplementation: true });
  await assert.rejects(f.run(), /Use the accepted implementation configuration/);
  assert.equal(Object.keys(f.written).length, 0);
});

test('missing and oversized private evidence fail without silent omission or truncation', async () => {
  const missing = fixture({ bootstrap: true });
  delete missing.privateFiles['implementation-review/SKILL.md'];
  await assert.rejects(missing.run(), /Missing private fixture/);
  const large = fixture({ bootstrap: true });
  large.privateFiles['KNOWN_ISSUES.md'] = 'x'.repeat(32000);
  await assert.rejects(large.run(), /instruction bound/);
});

test('both actions select the supported test-merge gates required by branch protection', () => {
  const required = JSON.parse(readFileSync(`${__dirname}/../.github/review-required-checks.json`, 'utf8'));
  assert.equal(required.strict, true);
  assert.deepEqual(required.checks, [
    { context: 'Project checks', app_id: 15368 },
    { context: 'Documentation reviewer (test merge)', app_id: 15368 },
    { context: 'Implementation reviewer (test merge)', app_id: 15368 },
  ]);
  for (const agent of ['documentation', 'implementation']) {
    const invocation = workflow.split(`        uses: ./.review-agent/${agent}-review\n`)[1]
      .split(/\n {6}- /)[0];
    assert.match(invocation, /\n          check-target: test-merge(?:\n|$)/);
    assert.match(invocation, /expected-head-sha: \$\{\{ steps\.reviewer\.outputs\.head \}\}/);
  }
});
