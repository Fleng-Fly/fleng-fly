import { el } from './layout.js';

export function letterTiles(config, savedAnswer, draft, onChange) {
  const pattern = [...config.pattern];
  const letters = config.letters;
  const assigned = draft ? [...draft] : Array(pattern.length).fill(null);
  const savedLetters = [...(savedAnswer || '').toLowerCase()];
  let selected = null;
  let dragged = null;

  if (!draft && savedLetters.length === pattern.length) {
    pattern.forEach((character, index) => {
      if (character !== '_') return;
      const tile = letters.findIndex((letter, id) => (
        letter.toLowerCase() === savedLetters[index] && !assigned.includes(id)
      ));
      if (tile !== -1) assigned[index] = tile;
    });
  }

  const field = el('fieldset', 'lesson-letter-tiles');
  field.append(
    el('legend', 'lesson-answer-label', 'Complete the word'),
    el('p', 'lesson-muted', 'Drag a letter into a blank, or select a letter and then select a blank. Select a filled blank to return its letter.'),
  );
  const word = el('div', 'lesson-tile-row');
  const bank = el('div', 'lesson-tile-row lesson-tile-bank');
  bank.setAttribute('role', 'group');
  bank.setAttribute('aria-label', 'Available letters');
  field.append(word, bank);

  const slots = new Map();
  const tiles = letters.map((letter, id) => {
    const button = el('button', 'lesson-tile', letter);
    button.type = 'button';
    button.addEventListener('click', () => {
      selected = selected === id ? null : id;
      refresh();
    });
    makeDraggable(button, () => id);
    bank.append(button);
    return button;
  });
  const readAnswer = () => (
    pattern.some((character, index) => character === '_' && assigned[index] === null)
      ? ''
      : pattern.map((character, index) => character === '_' ? letters[assigned[index]] : character).join('')
  );

  function makeDraggable(button, tileId) {
    button.draggable = true;
    button.addEventListener('dragstart', (event) => {
      dragged = tileId();
      if (button.disabled || dragged === null) {
        event.preventDefault();
        return;
      }
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', letters[dragged]);
    });
    button.addEventListener('dragend', () => { dragged = null; });
  }

  function refresh() {
    tiles.forEach((tile, id) => {
      tile.hidden = assigned.includes(id);
      tile.setAttribute('aria-pressed', String(selected === id));
    });
    for (const [index, slot] of slots) {
      const id = assigned[index];
      const label = `Blank ${index + 1}`;
      slot.textContent = id === null ? '' : letters[id];
      slot.draggable = id !== null;
      slot.setAttribute('aria-label', id === null ? `${label}, empty` : `${label}, ${letters[id]}`);
    }
  }

  function place(id, index) {
    if (id === null || assigned[index] !== null) return;
    const previous = assigned.indexOf(id);
    if (previous !== -1) assigned[previous] = null;
    assigned[index] = id;
    selected = null;
    refresh();
    onChange([...assigned]);
  }

  pattern.forEach((character, index) => {
    if (character !== '_') {
      word.append(el('span', 'lesson-tile lesson-tile-fixed', character));
      return;
    }
    const slot = el('button', 'lesson-tile lesson-tile-slot');
    slot.type = 'button';
    makeDraggable(slot, () => assigned[index]);
    slot.addEventListener('click', () => {
      if (assigned[index] === null) {
        place(selected, index);
        return;
      }
      assigned[index] = null;
      selected = null;
      refresh();
      onChange([...assigned]);
    });
    slot.addEventListener('dragover', (event) => {
      if (dragged === null || assigned[index] !== null) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
    });
    slot.addEventListener('drop', (event) => {
      event.preventDefault();
      place(dragged, index);
      dragged = null;
    });
    slots.set(index, slot);
    word.append(slot);
  });

  refresh();
  return { field, readAnswer };
}
