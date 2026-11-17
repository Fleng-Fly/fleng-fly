/** Restricted Markdown rendered as allowlisted DOM, never HTML parsing.
 * Sanitization is by construction: text nodes, fixed element names/attributes,
 * and URL protocol validation. Images/raw HTML/custom attributes are unsupported.
 */
export function safeMarkdownURL(value) {
  if (!value || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
  if (value.startsWith('//')) return null;
  try {
    const url = new URL(value, 'https://fleng.invalid');
    if (!['https:', 'http:', 'mailto:'].includes(url.protocol)) return null;
    if (url.username || url.password) return null;
    if (!/^(https?:|mailto:|\/|#)/i.test(value)) return null;
    return value;
  } catch { return null; }
}

function inline(target, source, depth = 0) {
  if (depth > 8) { target.append(document.createTextNode(source)); return; }
  let plain = '';
  const flush = () => { if (plain) target.append(document.createTextNode(plain)); plain = ''; };
  for (let i = 0; i < source.length;) {
    if (source[i] === '\\' && i + 1 < source.length) {
      plain += source[i + 1]; i += 2; continue;
    }
    if (source[i] === '`') {
      const end = source.indexOf('`', i + 1);
      if (end > i + 1) {
        flush(); const code = document.createElement('code');
        code.textContent = source.slice(i + 1, end); target.append(code); i = end + 1; continue;
      }
    }
    if (source[i] === '[' && source[i - 1] !== '!') {
      const match = /^\[([^\]\n]+)\]\(([^\s()]+)\)/.exec(source.slice(i));
      if (match) {
        flush(); const href = safeMarkdownURL(match[2]);
        if (href) {
          const link = document.createElement('a');
          link.setAttribute('href', href); link.setAttribute('rel', 'noopener noreferrer');
          link.setAttribute('target', '_blank');
          inline(link, match[1], depth + 1); target.append(link);
        } else target.append(document.createTextNode(match[1]));
        i += match[0].length; continue;
      }
    }
    const marker = source.startsWith('**', i) ? '**' : source.startsWith('__', i) ? '__'
      : ['*', '_'].includes(source[i]) ? source[i] : null;
    if (marker && (marker[0] !== '_' || !/[\p{L}\p{N}]/u.test(source[i - 1] || ''))) {
      const end = source.indexOf(marker, i + marker.length);
      const content = source.slice(i + marker.length, end);
      if (end > i + marker.length && content.trim() === content) {
        flush(); const node = document.createElement(marker.length === 2 ? 'strong' : 'em');
        inline(node, content, depth + 1); target.append(node); i = end + marker.length; continue;
      }
    }
    if (source[i] === '\n') { flush(); target.append(document.createElement('br')); }
    else plain += source[i];
    i++;
  }
  flush();
}

const listLine = (line) => /^(\s*)([-+*]|\d+[.)])\s+(.+)$/.exec(line);

export function renderMarkdown(target, value) {
  // The backend already bounds replies; retain a separate rendering work bound.
  const lines = String(value).slice(0, 64000).replace(/\r\n?/g, '\n').split('\n');
  target.replaceChildren();
  for (let i = 0; i < lines.length;) {
    if (!lines[i].trim()) { i++; continue; }
    const fence = /^\s*(`{3,}|~{3,})([\w+-]*)\s*$/.exec(lines[i]);
    if (fence) {
      const body = []; i++;
      while (i < lines.length && !new RegExp(`^\\s*${fence[1][0]}{${fence[1].length},}\\s*$`).test(lines[i])) body.push(lines[i++]);
      if (i < lines.length) i++;
      const pre = document.createElement('pre'), code = document.createElement('code');
      code.textContent = body.join('\n'); pre.append(code); target.append(pre); continue;
    }
    const heading = /^#{1,6}\s+(.+)$/.exec(lines[i]);
    if (heading) {
      const node = document.createElement('h3'); inline(node, heading[1]); target.append(node); i++; continue;
    }
    if (listLine(lines[i])) {
      const stack = [];
      while (i < lines.length && listLine(lines[i])) {
        const [, spaces, marker, content] = listLine(lines[i++]);
        const indent = spaces.replace(/\t/g, '    ').length;
        const tag = /^\d/.test(marker) ? 'ol' : 'ul';
        while (stack.length && (indent < stack.at(-1).indent || (indent === stack.at(-1).indent && tag !== stack.at(-1).tag))) stack.pop();
        if (!stack.length || indent > stack.at(-1).indent) {
          const node = document.createElement(tag);
          if (tag === 'ol') node.setAttribute('start', String(parseInt(marker, 10)));
          (stack.at(-1)?.item || target).append(node);
          stack.push({ indent, tag, node, item: null });
        }
        const item = document.createElement('li'); inline(item, content);
        stack.at(-1).node.append(item); stack.at(-1).item = item;
      }
      continue;
    }
    const paragraph = [lines[i++]];
    while (i < lines.length && lines[i].trim() && !listLine(lines[i]) && !/^\s*(`{3,}|~{3,})/.test(lines[i]) && !/^#{1,6}\s/.test(lines[i])) paragraph.push(lines[i++]);
    const node = document.createElement('p'); inline(node, paragraph.join('\n')); target.append(node);
  }
}
