// Compare immutable pins without executing code from the private reviewer.
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');

const MARKER = '<!-- edotenv-reviewer-freshness -->';
const TITLE = 'Update the pinned review-agents revision';

function comparison(root = '.', upstream = '.review-agent') {
  const workflow = readFileSync(`${root}/.github/workflows/documentation-review.yml`, 'utf8');
  const pins = [...workflow.matchAll(/repository: Lestode\/review-agents\s*\n(?:\s*#.*\n)*\s*ref: ([0-9a-f]{40})\s*$/gm)];
  if (pins.length !== 1) throw new Error('Expected one immutable review-agents pin.');
  const pinned = pins[0][1];
  const git = (...args) => execFileSync('git', ['-C', upstream, ...args], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
  const latest = git('rev-parse', 'HEAD');
  if (!/^[0-9a-f]{40}$/.test(latest)) throw new Error('Invalid upstream revision.');
  if (pinned !== latest) {
    // A missing pin or rewritten history must fail, rather than suggest an update.
    git('merge-base', '--is-ancestor', pinned, latest);
  }
  return { pinned, latest };
}

async function report({ github, context, core, revisions }) {
  const { pinned, latest } = revisions;
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    ...context.repo, state: 'all', creator: 'github-actions[bot]', per_page: 100,
  });
  const tracked = issues.filter(issue => !issue.pull_request &&
    issue.user?.login === 'github-actions[bot]' && issue.body?.startsWith(MARKER));
  // Prefer an open alert, then reuse the latest closed alert for future updates.
  const issue = tracked.find(item => item.state === 'open') || tracked[0];
  if (pinned === latest) {
    for (const open of tracked.filter(item => item.state === 'open')) {
      await github.rest.issues.update({
        ...context.repo, issue_number: open.number, state: 'closed', state_reason: 'completed',
      });
    }
    core.info('The reviewer pin matches the upstream default branch.');
    return;
  }
  // Only revision identifiers and links are published; no private source or commit messages.
  const body = `${MARKER}\nThe pinned reviewer is behind the upstream default branch.\n\n` +
    `Current pin: \`${pinned}\`\nLatest revision: \`${latest}\`\n\n` +
    `[Compare revisions](https://github.com/Lestode/review-agents/compare/${pinned}...${latest}) ` +
    `(requires access to the private reviewer repository).\n\n` +
    'Prepare a reviewed PR updating the immutable checkout pin in ' +
    '`.github/workflows/documentation-review.yml` and the matching documentation links in ' +
    '`docs/WORKFLOW.md`. Inspect compatibility and run the required checks and agent review. ' +
    'Merging still requires explicit user acceptance.\n\n' +
    'This alert is updated only when revisions change and closes when the pin catches up. ' +
    'Closing it without updating the pin will cause the next check to reopen it.\n';
  if (!issue) {
    await github.rest.issues.create({ ...context.repo, title: TITLE, body });
  } else if (issue.body !== body || issue.title !== TITLE || issue.state !== 'open') {
    await github.rest.issues.update({
      ...context.repo, issue_number: issue.number, title: TITLE, body, state: 'open',
    });
  }
  core.info('A reviewer update is available; the tracking issue is current.');
}

module.exports = { comparison, report, MARKER };
