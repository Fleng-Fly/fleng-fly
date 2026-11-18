import { register, setAccessToken } from './api.js';
import { describeApiError } from './errors.js';
import { mountHeader } from './layout.js';
import { t } from './i18n.js';
import { redirectIfSignedIn, setupGoogleSignIn } from './session.js';

if (await redirectIfSignedIn()) await new Promise(() => {});
mountHeader('register', null);

const form = document.getElementById('register-form');
const errorBox = document.getElementById('form-error');
const submit = document.getElementById('submit-button');

setupGoogleSignIn().then((message) => {
  if (!message) return;
  errorBox.textContent = message;
  errorBox.classList.remove('hidden');
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorBox.classList.add('hidden');
  submit.disabled = true;
  submit.textContent = t('register.submitting');
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
    submit.textContent = t('auth.register');
  }
});
