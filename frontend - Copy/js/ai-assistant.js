import { getAIHistory, getAIStatus, listAIConversations, streamAIChat } from './api.js';
import { readAIEvents } from './ai-stream.js';
import { el } from './layout.js';

let widget;

export function unmountAIAssistant(options) {
  widget?.destroy(options);
}

/** One widget per authenticated workspace. The callback sends IDs only. */
export function mountAIAssistant(user, getContext = () => ({})) {
  if (!user?.id) return;
  if (widget && widget.userId !== user.id) widget.destroy({ clearSelection: true });
  if (widget) return widget;
  let destroyed = false;
  let controller;
  const css = el('link');
  css.rel = 'stylesheet';
  css.href = '/css/ai-assistant.css';
  document.head.append(css);
  const root = el('aside', 'fleng-ai');
  root.setAttribute('aria-label', 'Fleng AI learning assistant');
  const launcher = button('✦ Fleng AI', () => open());
  launcher.className = 'ai-launcher';
  launcher.setAttribute('aria-controls', 'ai-panel');
  launcher.setAttribute('aria-expanded', 'false');
  const panel = el('section', 'ai-panel');
  panel.id = 'ai-panel';
  panel.hidden = true;
  panel.setAttribute('role', 'region');
  panel.setAttribute('aria-label', 'Fleng AI chat');
  const header = el('header', 'ai-header');
  const title = el('div');
  title.append(el('strong', '', '✦ Fleng AI'));
  const availability = el('small', '', 'Checking availability');
  title.append(availability);
  header.append(
    title,
    button('−', () => hide('MINIMIZED'), 'Minimize chat'),
    button('×', () => hide('CLOSED'), 'Close chat'),
  );
  const tools = el('div', 'ai-tools');
  const select = el('select');
  select.setAttribute('aria-label', 'Conversation history');
  const fresh = button('New chat', () => {
    conversationId = null;
    initialized = true;
    needsReload = false;
    input.value = '';
    messages.replaceChildren();
    select.value = '';
    notice.textContent = available ? '' : 'Fleng AI is currently unavailable.';
    welcome();
    controls();
    phase(available ? visibility : 'UNAVAILABLE');
  });
  const reload = button('Reload', () => load());
  tools.append(select, fresh, reload);
  const contextLabel = el('p', 'ai-context');
  const messages = el('div', 'ai-messages');
  messages.tabIndex = 0;
  messages.setAttribute('aria-label', 'Messages');
  messages.setAttribute('role', 'log');
  messages.setAttribute('aria-live', 'polite');
  const notice = el('p', 'ai-notice');
  notice.setAttribute('role', 'status');
  const form = el('form', 'ai-composer');
  const input = el('textarea');
  input.rows = 2;
  input.maxLength = 4000;
  input.placeholder = 'Ask about English…';
  input.setAttribute('aria-label', 'Message to Fleng AI');
  const send = el('button', '', 'Send');
  send.type = 'submit';
  form.append(input, send);
  panel.append(header, tools, contextLabel, messages, notice, form);
  root.append(panel, launcher);
  document.body.append(root);
  let conversationId = null;
  let busy = false;
  let needsReload = false;
  let available = false;
  let initialized = false;
  let visibility = 'CLOSED';
  // Store only a user-scoped conversation identifier; never messages or auth tokens.
  const key = `fleng.ai.conversation.${user.id}`;
  function remember() {
    try {
      if (conversationId) localStorage.setItem(key, conversationId);
      else localStorage.removeItem(key);
    } catch {
      /* Storage is optional. */
    }
  }
  fresh.addEventListener('click', remember);
  function phase(value) {
    root.dataset.state = value;
  }
  function controls() {
    send.disabled = busy || !available || needsReload;
    input.disabled = !available;
    input.readOnly = busy;
    select.disabled = fresh.disabled = reload.disabled = busy;
    form.setAttribute('aria-busy', String(busy));
    messages.setAttribute('aria-busy', String(busy));
  }
  function welcome() {
    messages.append(
      el(
        'p',
        'ai-welcome',
        'Your English study assistant. Ask for a grammar explanation or a hint. AI can make mistakes; lesson grades come from Fleng.',
      ),
    );
  }
  function bubble(role, text) {
    const article = el('article', `ai-message ai-${role}`);
    article.append(el('small', '', role === 'user' ? 'You' : 'Fleng AI'));
    const content = el('p', '', text);
    article.append(content);
    messages.append(article);
    messages.scrollTop = messages.scrollHeight;
    return content;
  }
  function context() {
    const value = getContext() || {};
    contextLabel.textContent = value.lessonId
      ? 'Helping with your current lesson · hints first'
      : 'General English learning';
    return {
      ...(value.lessonId ? { lessonId: value.lessonId } : {}),
      ...(value.exerciseId ? { exerciseId: value.exerciseId } : {}),
    };
  }
  function hide(value) {
    visibility = value;
    panel.hidden = true;
    launcher.hidden = false;
    launcher.setAttribute('aria-expanded', 'false');
    launcher.focus();
    // Closing/minimizing deliberately keeps an active request running until saved.
    phase(value);
  }
  async function open() {
    visibility = 'OPEN';
    panel.hidden = false;
    launcher.hidden = true;
    launcher.setAttribute('aria-expanded', 'true');
    context();
    if (!initialized) await load();
    else phase(busy ? 'STREAMING' : available ? 'OPEN' : 'UNAVAILABLE');
    if (!panel.hidden) (input.disabled ? reload : input).focus();
  }
  async function history() {
    if (destroyed) return;
    messages.replaceChildren();
    if (!conversationId) {
      welcome();
      return;
    }
    let offset = 0;
    while (true) {
      const page = await getAIHistory(conversationId, offset);
      if (destroyed) return;
      for (const item of page) bubble(item.role === 'user' ? 'user' : 'assistant', item.content);
      if (page.length < 100) break;
      offset += page.length;
    }
  }
  async function load() {
    if (busy || destroyed) return;
    busy = true;
    phase('LOADING');
    notice.textContent = 'Loading conversation history…';
    controls();
    try {
      const [status, conversations] = await Promise.all([getAIStatus(), listAIConversations()]);
      if (destroyed) return;
      available = status.available;
      input.maxLength = status.maxInputChars;
      if (!initialized) {
        let saved;
        try {
          saved = localStorage.getItem(key);
        } catch {
          /* Optional. */
        }
        conversationId = conversations.some((item) => item.id === saved)
          ? saved
          : conversations[0]?.id || null;
      }
      select.replaceChildren(new Option('New conversation', ''));
      for (const item of conversations)
        select.append(new Option(`Chat · ${new Date(item.createdAt).toLocaleString()}`, item.id));
      select.value = conversationId || '';
      await history();
      if (destroyed) return;
      initialized = true;
      needsReload = false;
      remember();
      availability.textContent = available ? 'Ready to help' : 'Unavailable';
      notice.textContent = available
        ? ''
        : 'Fleng AI is currently unavailable. Your saved conversations are still accessible.';
      phase(available ? visibility : 'UNAVAILABLE');
    } catch (error) {
      if (destroyed) return;
      if (error.status === 401) {
        destroy({ clearSelection: true });
        return;
      }
      needsReload = true;
      notice.textContent = 'Unable to load the assistant. Check your connection and select Reload.';
      phase('ERROR');
    } finally {
      busy = false;
      controls();
    }
  }
  select.addEventListener('change', async () => {
    if (destroyed) return;
    conversationId = select.value || null;
    remember();
    busy = true;
    controls();
    phase('LOADING');
    try {
      await history();
      if (destroyed) return;
      needsReload = false;
      notice.textContent = available ? '' : 'Fleng AI is currently unavailable.';
      phase(available ? visibility : 'UNAVAILABLE');
    } catch (error) {
      if (destroyed) return;
      if (error.status === 401) {
        destroy({ clearSelection: true });
        return;
      }
      needsReload = true;
      notice.textContent = 'Unable to load history. Select Reload to try again.';
      phase('ERROR');
    } finally {
      busy = false;
      controls();
    }
  });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (destroyed || busy || !available || needsReload || !message) return;
    busy = true;
    controls();
    phase('STREAMING');
    input.focus();
    availability.textContent = 'Writing…';
    notice.textContent =
      'Generating… You can minimize or close; the answer will keep loading on this page.';
    bubble('user', message);
    const answer = bubble('assistant', '');
    let complete = false;
    controller = new AbortController();
    try {
      const response = await streamAIChat(
        {
          message,
          conversationId,
          ...context(),
          requestId: crypto.randomUUID(),
        },
        { signal: controller.signal },
      );
      if (destroyed) {
        await response.body?.cancel();
        return;
      }
      for await (const event of readAIEvents(response.body)) {
        if (destroyed) return;
        if (event.name === 'delta') {
          if (typeof event.data.content !== 'string') throw new Error('Invalid response');
          answer.textContent += event.data.content;
          messages.scrollTop = messages.scrollHeight;
        } else if (event.name === 'done') {
          if (!event.data.conversationId || typeof event.data.message?.content !== 'string')
            throw new Error('Invalid response');
          conversationId = event.data.conversationId;
          remember();
          answer.textContent = event.data.message.content;
          complete = true;
          if (![...select.options].some((item) => item.value === conversationId))
            select.append(new Option('Current conversation', conversationId));
          select.value = conversationId;
          input.value = '';
          notice.textContent = '';
          phase(visibility);
        } else if (event.name === 'error') {
          const error = new Error('Stream failed');
          error.code = event.data.code;
          throw error;
        }
      }
      if (!complete) throw new Error('Incomplete response');
    } catch (error) {
      if (destroyed) return;
      if (error.status === 401) {
        destroy({ clearSelection: true });
        return;
      }
      needsReload = true;
      initialized = false;
      answer.textContent =
        'Response interrupted. This provisional exchange may not have been saved.';
      const unavailable = error.code === 'AI_UNAVAILABLE';
      if (unavailable) available = false;
      notice.textContent = unavailable
        ? 'Fleng AI is currently unavailable. Select Reload to check again.'
        : ['AI_RATE_LIMITED', 'RATE_LIMITED', 'AI_BUSY', 'AI_BUDGET_LIMIT'].includes(error.code)
          ? 'AI limit reached. Please try later.'
          : 'The request did not complete. Reload history before sending again; no automatic retry was made.';
      phase(unavailable ? 'UNAVAILABLE' : 'ERROR');
    } finally {
      controller = null;
      busy = false;
      availability.textContent = available ? 'Ready to help' : 'Unavailable';
      controls();
      if (!panel.hidden && available && panel.contains(document.activeElement)) input.focus();
    }
  });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !panel.hidden) {
      event.stopPropagation();
      hide('CLOSED');
    }
  });
  function viewport() {
    const view = window.visualViewport;
    if (view) {
      root.classList.toggle('ai-keyboard', view.height < window.innerHeight * 0.75);
      root.style.setProperty('--ai-height', `${view.height}px`);
      root.style.setProperty(
        '--ai-bottom',
        `${Math.max(0, window.innerHeight - view.height - view.offsetTop)}px`,
      );
    }
  }
  window.visualViewport?.addEventListener('resize', viewport);
  window.visualViewport?.addEventListener('scroll', viewport);
  viewport();
  controls();
  phase('CLOSED');
  function onSessionEnd() {
    destroy({ clearSelection: true });
  }
  function onStorage(event) {
    if (event.key === 'fleng.session.logout') onSessionEnd();
  }
  function destroy({ clearSelection = false } = {}) {
    if (destroyed) return;
    destroyed = true;
    controller?.abort();
    messages.replaceChildren();
    input.value = '';
    conversationId = null;
    if (clearSelection) remember();
    root.remove();
    css.remove();
    window.visualViewport?.removeEventListener('resize', viewport);
    window.visualViewport?.removeEventListener('scroll', viewport);
    window.removeEventListener('fleng:session-ended', onSessionEnd);
    window.removeEventListener('storage', onStorage);
    widget = undefined;
  }
  window.addEventListener('fleng:session-ended', onSessionEnd);
  window.addEventListener('storage', onStorage);
  widget = { open, destroy, userId: user.id };
  return widget;
}

function button(text, action, label = text) {
  const node = el('button', '', text);
  node.type = 'button';
  node.setAttribute('aria-label', label);
  node.addEventListener('click', action);
  return node;
}
