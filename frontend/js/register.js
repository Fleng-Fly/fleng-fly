import { register, setAccessToken } from './api.js';
import { describeApiError } from './errors.js';
import { mountHeader } from './layout.js';

mountHeader('register');

const form = document.getElementById('register-form');
const errorBox = document.getElementById('form-error');
const submit = document.getElementById('submit-button');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorBox.classList.add('hidden');
  submit.disabled = true;
  submit.textContent = 'Creating account…';
  try {
    const result = await register({
      email: form.email.value.trim(),
      password: form.password.value,
      displayName: form.displayName.value.trim(),
    });
    setAccessToken(result.accessToken);
    window.location.href = '/dashboard.html';
  } catch (error) {
    errorBox.textContent = describeApiError(error);
    errorBox.classList.remove('hidden');
    submit.disabled = false;
    submit.textContent = 'Create account';
  }
});
