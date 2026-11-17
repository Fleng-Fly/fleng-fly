import { login, requestPasswordReset, setAccessToken } from './api.js';
import { describeApiError } from './errors.js';
import { mountHeader } from './layout.js';

mountHeader('login');

const form = document.getElementById('login-form');
const errorBox = document.getElementById('form-error');
const submit = document.getElementById('submit-button');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorBox.classList.add('hidden');
  submit.disabled = true;
  submit.textContent = 'Logging in…';
  try {
    const result = await login(form.email.value.trim(), form.password.value);
    setAccessToken(result.accessToken);
    window.location.href = '/dashboard.html';
  } catch (error) {
    errorBox.textContent = describeApiError(error);
    errorBox.classList.remove('hidden');
    submit.disabled = false;
    submit.textContent = 'Log in';
  }
});

document.getElementById('reset-request-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('reset-request-button');
  const status = document.getElementById('reset-request-status');
  if (button.disabled) return;
  button.disabled = true;
  status.textContent = 'Sending…';
  try {
    await requestPasswordReset(document.getElementById('reset-email').value.trim());
    status.textContent = 'If the account exists and email delivery is enabled, a reset link will be sent. Check your inbox and spam folder.';
  } catch (error) {
    status.textContent = describeApiError(error);
  } finally {
    button.disabled = false;
  }
});
