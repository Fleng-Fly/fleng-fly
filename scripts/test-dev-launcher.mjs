import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { busyPortMessage, portInUse, primaryCheckout, resolveVenv } from './dev-helpers.mjs';

function fakeWorktree() {
  const base = mkdtempSync(join(tmpdir(), 'fleng-dev-'));
  const main = join(base, 'main');
  mkdirSync(join(main, '.git', 'worktrees', 'feature'), { recursive: true });
  const tree = join(base, 'tree');
  mkdirSync(tree);
  writeFileSync(join(tree, '.git'), `gitdir: ${main}/.git/worktrees/feature\n`);
  return { main, tree };
}
function addVenv(root) {
  const bin = join(root, 'backend', '.venv', 'bin');
  mkdirSync(bin, { recursive: true });
  writeFileSync(join(bin, 'uvicorn'), '');
  writeFileSync(join(bin, 'python'), '');
}

test('a linked worktree resolves its main checkout; a normal checkout does not', () => {
  const { main, tree } = fakeWorktree();
  assert.equal(primaryCheckout(tree), main);
  assert.equal(primaryCheckout(main), null);
});

test('a checkout uses its own virtualenv; a worktree may borrow only the interpreter of main', () => {
  const { main, tree } = fakeWorktree();
  assert.equal(resolveVenv(tree, 'linux'), null);
  addVenv(main);
  const borrowed = resolveVenv(tree, 'linux');
  assert.match(borrowed.source, /main checkout/);
  assert.ok(borrowed.uvicorn.startsWith(main));
  addVenv(tree);
  const own = resolveVenv(tree, 'linux');
  assert.equal(own.source, 'checkout');
  assert.ok(own.uvicorn.startsWith(tree));
});

test('a busy port is detected and reported with the owning checkout', async () => {
  const server = net.createServer().listen(0, '127.0.0.1');
  await new Promise((resolve) => server.once('listening', resolve));
  const { port } = server.address();
  assert.equal(await portInUse(port), true);
  const here = busyPortMessage(port, '/a', { checkout: '/b', mode: 'x' });
  assert.match(here, /another Fleng checkout: \/b/);
  assert.match(here, new RegExp(`PORT=${port + 1}`));
  assert.match(busyPortMessage(port, '/a', { checkout: '/a' }), /THIS checkout/);
  assert.match(busyPortMessage(port, '/a', { checkout: null }), /Another process/);
  await new Promise((resolve) => server.close(resolve));
  assert.equal(await portInUse(port), false);
});
