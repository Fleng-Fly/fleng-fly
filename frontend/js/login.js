import { login, setAccessToken } from './api.js';
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
