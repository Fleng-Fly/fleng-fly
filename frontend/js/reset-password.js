import { confirmPasswordReset, setAccessToken } from './api.js';
import { describeApiError } from './errors.js';
import { t } from './i18n.js';

let token = new URLSearchParams(location.search).get('token');
// Keep the bearer reset secret out of subsequent history/referrer URLs and storage.
history.replaceState(null, '', location.pathname);
const form = document.getElementById('reset-password-form');
const status = document.getElementById('reset-status');
const submit = document.getElementById('reset-submit');
if (!token) status.textContent = t('reset.missingToken');
else form.hidden = false;

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (submit.disabled || !token) return;
  const password = document.getElementById('new-password');
  const confirmation = document.getElementById('confirm-password');
  if (password.value !== confirmation.value) {
    status.textContent = t('reset.mismatch');
    return;
  }
  if (!form.reportValidity()) return;
  submit.disabled = true;
  status.textContent = t('reset.updating');
  try {
    await confirmPasswordReset(token, password.value);
    token = null;
    form.reset();
    form.hidden = true;
    setAccessToken(null);
    status.textContent = t('reset.done');
  } catch (error) {
    if (error.code === 'INVALID_RESET_TOKEN') {
      token = null;
      form.reset();
      form.hidden = true;
      status.textContent = t('reset.expired');
    } else {
      status.textContent = describeApiError(error);
      submit.disabled = false;
    }
  }
});
