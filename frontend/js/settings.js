import { mountHeader } from './layout.js';
import { requireSession } from './session.js';

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = String(value);
}

function renderProfile(user) {
  setText('user-name', user.displayName);
  setText('user-email', user.email);
  setText('user-level', user.level);
  setText('user-xp', user.xp);
}

async function main() {
  const user = await requireSession();
  if (!user) return;
  await mountHeader('settings', user);
  renderProfile(user);
}

main();
