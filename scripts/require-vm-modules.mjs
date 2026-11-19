// vm.SourceTextModule exists only when Node starts with --experimental-vm-modules. The frontend
// unit tests load the real browser ES modules through it, so a test file imported without the
// flag would crash ("vm.SourceTextModule is not a constructor"). Import this module FIRST: if the
// flag is missing it re-runs the same script with the flag and mirrors its exit status, so both
// `node --test scripts/test-x.mjs` and `npm run frontend:test` work on any supported Node.js.
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';

if (typeof vm.SourceTextModule !== 'function') {
  const { status, signal } = spawnSync(
    process.execPath,
    ['--experimental-vm-modules', '--disable-warning=ExperimentalWarning', ...process.argv.slice(1)],
    { stdio: 'inherit' },
  );
  process.exit(signal ? 1 : (status ?? 1));
}
