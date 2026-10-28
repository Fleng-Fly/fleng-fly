import { changePassword, logout, setAccessToken, updateCurrentUser } from './api.js';
import { describeApiError } from './errors.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
let user;

function feedback(id, message, error = false) {
  const node = $(id);
  node.textContent = message;
  node.classList.toggle('is-error', error);
}

function clearPasswordForm() {
  $('password-form').reset();
  for (const button of document.querySelectorAll('[data-password-target]')) {
    const input = $(button.dataset.passwordTarget);
    input.type = 'password';
    button.textContent = 'Show';
    button.setAttribute('aria-label', `Show ${input.labels[0].textContent.toLowerCase()}`);
  }
}

function renderUser(nextUser, populateForm = true) {
  user = nextUser;
  $('settings-name').textContent = user.displayName;
  $('settings-email').textContent = user.email;
  $('settings-avatar').textContent = user.displayName.trim().charAt(0).toLocaleUpperCase() || 'F';
  $('settings-level').textContent = `English level ${user.englishLevel || 'A1'}`;
  setWorkspaceUser(user);
  if (populateForm) {
    $('profile-name').value = user.displayName;
    $('profile-email').value = user.email;
  }
  const select = $('language-select');
  if (![...select.options].some((option) => option.value === user.preferredLanguage)) {
    select.add(new Option(user.preferredLanguage, user.preferredLanguage));
  }
  select.value = user.preferredLanguage;
}

function bindPage() {
  $('edit-profile').addEventListener('click', () => {
    $('account-information').scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
    });
    $('profile-name').focus({ preventScroll: true });
  });
  $('profile-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const name = $('profile-name').value.trim();
    const email = $('profile-email').value.trim();
    if (!name || name.length > 80 || !$('profile-email').checkValidity()) {
      feedback('profile-feedback', 'Enter a name and a valid email address.', true);
      return;
    }
    const button = $('save-profile');
    button.disabled = true;
    button.textContent = 'Saving…';
    feedback('profile-feedback', '');
    try {
      renderUser(await updateCurrentUser({ displayName: name, email }), true);
      feedback('profile-feedback', 'Account information saved.');
    } catch (error) {
      feedback('profile-feedback', describeApiError(error), true);
    } finally {
      button.disabled = false;
      button.textContent = 'Save Changes';
    }
  });
  $('language-select').addEventListener('change', async () => {
    const select = $('language-select');
    select.disabled = true;
    feedback('language-feedback', 'Saving…');
    try {
      renderUser(await updateCurrentUser({ preferredLanguage: select.value }), false);
      feedback('language-feedback', 'Language preference saved.');
    } catch (error) {
      select.value = user.preferredLanguage;
      feedback('language-feedback', describeApiError(error), true);
    } finally {
      select.disabled = false;
    }
  });
  $('password-toggle').addEventListener('click', () => {
    const opening = $('password-form').hidden;
    $('password-form').hidden = !opening;
    $('password-toggle').setAttribute('aria-expanded', String(opening));
    $('password-toggle').textContent = opening ? 'Cancel' : 'Change Password';
    if (opening) $('current-password').focus();
    else {
      clearPasswordForm();
      feedback('password-feedback', '');
    }
  });
  for (const button of document.querySelectorAll('[data-password-target]')) {
    button.addEventListener('click', () => {
      const input = $(button.dataset.passwordTarget);
      const shown = input.type === 'password';
      input.type = shown ? 'text' : 'password';
      button.textContent = shown ? 'Hide' : 'Show';
      button.setAttribute(
        'aria-label',
        `${shown ? 'Hide' : 'Show'} ${input.labels[0].textContent.toLowerCase()}`,
      );
    });
  }
  $('password-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const currentPassword = $('current-password').value;
    const newPassword = $('new-password').value;
    if (newPassword.length < 8 || newPassword.length > 128 || !currentPassword) {
      feedback(
        'password-feedback',
        'Enter your current password and a new password of 8–128 characters.',
        true,
      );
      return;
    }
    if (newPassword !== $('confirm-password').value) {
      feedback('password-feedback', 'New passwords do not match.', true);
      return;
    }
    const button = $('save-password');
    button.disabled = true;
    button.textContent = 'Updating…';
    feedback('password-feedback', '');
    try {
      await changePassword({ currentPassword, newPassword });
      clearPasswordForm();
      setAccessToken(null);
      window.alert('Password updated. Please sign in again.');
      window.location.assign('/login.html');
    } catch (error) {
      feedback('password-feedback', describeApiError(error), true);
    } finally {
      button.disabled = false;
      button.textContent = 'Update Password';
    }
  });
  $('settings-logout').addEventListener('click', async () => {
    const button = $('settings-logout');
    button.disabled = true;
    button.textContent = 'Logging out…';
    feedback('logout-feedback', '');
    try {
      await logout();
      setAccessToken(null);
      window.location.assign('/login.html');
    } catch (error) {
      feedback('logout-feedback', describeApiError(error), true);
      button.disabled = false;
      button.textContent = 'Log Out';
    }
  });
}

async function main() {
  mountWorkspace('settings');
  $('settings-retry').addEventListener('click', () => window.location.reload());
  try {
    const currentUser = await requireSession({ throwOnUnavailable: true });
    if (!currentUser) return;
    renderUser(currentUser);
    bindPage();
    $('settings-content').hidden = false;
  } catch (error) {
    $('settings-error-text').textContent = describeApiError(error);
    $('settings-error').hidden = false;
  }
}

main();
