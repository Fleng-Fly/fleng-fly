export function autoCheckText(form, input, check) {
  let timer;
  let composing = false;

  function checkNow() {
    clearTimeout(timer);
    if (form.isConnected && !composing && input.value.trim()) check(input.value);
  }

  function schedule() {
    clearTimeout(timer);
    if (!composing && input.value.trim()) timer = setTimeout(checkNow, 1500);
  }

  input.addEventListener('compositionstart', () => {
    composing = true;
    clearTimeout(timer);
  });
  input.addEventListener('compositionend', () => {
    composing = false;
    schedule();
  });
  input.addEventListener('input', schedule);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    checkNow();
  });
}
