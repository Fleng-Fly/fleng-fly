// Display control only; auth requests remain in the existing API modules.
const toggle = document.querySelector('.auth-password-toggle');
const password = document.getElementById('password');
if (toggle && password) toggle.addEventListener('click', () => {
  const show = password.type === 'password';
  password.type = show ? 'text' : 'password';
  toggle.textContent = show ? 'Hide' : 'Show';
  toggle.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
  toggle.setAttribute('aria-pressed', String(show));
});
