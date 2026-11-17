import { requestEmailChange, confirmEmailChange, changePassword, logout, setAccessToken, updateCurrentUser } from './api.js';
import { describeApiError } from './errors.js';
import { getLang, languageFromAccount, setLang, t } from './i18n.js';
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
    button.textContent = t('settings.show');
    button.setAttribute('aria-label', t('settings.showField', { field: input.labels[0].textContent.toLowerCase() }));
  }
}

function renderUser(nextUser, populateForm = true) {
  user = nextUser;
  $('settings-name').textContent = user.displayName;
  $('settings-email').textContent = user.email;
  $('settings-avatar').textContent = user.displayName.trim().charAt(0).toLocaleUpperCase() || 'F';
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
  if (languageFromAccount(user.preferredLanguage) !== getLang()) {
    select.value = getLang() === 'uk' ? 'Ukrainian' : 'English';
  }
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
      feedback('profile-feedback', t('settings.needNameEmail'), true);
      return;
    }
    const button = $('save-profile');
    button.disabled = true;
    button.textContent = t('settings.saving');
    feedback('profile-feedback', '');
    try {
      const changingEmail = email.toLowerCase() !== user.email;
      if (changingEmail) {
        const currentPassword = $('email-current-password').value;
        await requestEmailChange({ email, currentPassword });
        $('email-current-password').value = '';
      }
      renderUser(await updateCurrentUser({ displayName: name }), true);
      feedback('profile-feedback', changingEmail ? t('settings.emailPending') : t('settings.saved'));
    } catch (error) {
      feedback('profile-feedback', describeApiError(error), true);
    } finally {
      button.disabled = false;
      button.textContent = t('settings.save');
    }
  });
  $('language-select').addEventListener('change', async () => {
    const select = $('language-select');
    select.disabled = true;
    feedback('language-feedback', t('settings.saving'));
    try {
      renderUser(await updateCurrentUser({ preferredLanguage: select.value }), false);
      await setLang(languageFromAccount(select.value) || 'en');
      feedback('language-feedback', t('settings.langSaved'));
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
    $('password-toggle').textContent = opening ? t('common.cancel') : t('settings.changePw');
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
      button.textContent = shown ? t('settings.hide') : t('settings.show');
      button.setAttribute(
        'aria-label',
        t(shown ? 'settings.hideField' : 'settings.showField', { field: input.labels[0].textContent.toLowerCase() }),
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
        t('settings.pwRules'),
        true,
      );
      return;
    }
    if (newPassword !== $('confirm-password').value) {
      feedback('password-feedback', t('settings.pwMismatch'), true);
      return;
    }
    const button = $('save-password');
    button.disabled = true;
    button.textContent = t('settings.updating');
    feedback('password-feedback', '');
    try {
      await changePassword({ currentPassword, newPassword });
      clearPasswordForm();
      setAccessToken(null);
      window.alert(t('settings.pwDone'));
      window.location.assign('/login.html');
    } catch (error) {
      feedback('password-feedback', describeApiError(error), true);
    } finally {
      button.disabled = false;
      button.textContent = t('reset.submit');
    }
  });
  $('settings-logout').addEventListener('click', async () => {
    const button = $('settings-logout');
    button.disabled = true;
    button.textContent = t('settings.loggingOut');
    feedback('logout-feedback', '');
    try {
      await logout();
      setAccessToken(null);
      window.location.assign('/login.html');
    } catch (error) {
      feedback('logout-feedback', describeApiError(error), true);
      button.disabled = false;
      button.textContent = t('auth.logout');
    }
  });
}

async function main() {
  const token = new URLSearchParams(window.location.hash.slice(1)).get('email-change');
  if (token) {
    history.replaceState(null, '', window.location.pathname);
    try {
      await confirmEmailChange(token);
      setAccessToken(null);
      window.alert(t('settings.emailDone'));
      window.location.replace('/login.html');
      return;
    } catch (error) { window.alert(describeApiError(error)); }
  }
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
