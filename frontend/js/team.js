import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { describeApiError } from './errors.js';

mountWorkspace('team');
async function load() {
  const error = document.getElementById('team-error');
  error.hidden = true;
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    document.getElementById('team-content').hidden = false;
  } catch (failure) {
    document.getElementById('team-error-text').textContent = describeApiError(failure);
    error.hidden = false;
  }
}
document.getElementById('team-retry').addEventListener('click', load);
load();
