# Передача змін другому розробнику

Дата роботи — 2026-11-11. Основа — наданий `fleng-fly-main(1).zip`.
Вхідний архів збігається з початковою версією до реалізації повторів і плиток.

## Реалізація

`frontend/js/lesson.js` після успішного запиту `/submit` використовує прогрес
із сервера, відкриває наступну незавершену вправу і показує попередній feedback.
Питання без спроб мають пріоритет. Після них незавершені спроби повторюються
циклічно. Practice і Test використовують один порядок і спільний прогрес.
Помилка мережі залишає поточне завдання для повторного надсилання.

`frontend/js/letter-tiles.js` відповідає за плитки. Кожна літера має свій індекс,
тому однакові літери є окремими плитками. Позиції змінюються лише після
скидання у вільну комірку або вибору натисканням. Можна перетягувати плитку
між комірками. Частково заповнені позиції зберігаються до виходу зі сторінки.

## Контракт API та БД

Літерна вправа використовує тип `text` і необов'язковий JSON `letter_tiles`
у таблиці `exercises`. Міграція `20261114_1200` залежить від `20261110_1400`.

Приклад конфігурації у seed

```python
{
    "type": "text",
    "prompt": "Fill the blanks: Have you ever ___ to Ireland?",
    "letter_tiles": {"pattern": "b__n", "letters": ["a", "e", "o", "e"]},
    "accepted_answers": ["been"],
}
```

Публічна відповідь містить `letterTiles` з `pattern` та `letters`.
Ключ відповіді прихований до надсилання. POST `/lessons/{slug}/submit`
отримує `exerciseId` і повне слово в `answer`.
Сервер перевіряє незмінні літери, кількість доступних плиток і очікувану
відповідь. Неповне або неможливе складання повертає 422. Неправильне слово
з доступних літер записується як звичайна невдала спроба.

Фіксовані письмові відповіді використовують `text` з `accepted_answers`.
Нормалізація враховує регістр і пробіли. Для нової вправи з однією відповіддю
достатньо одного елемента в списку.

Для Self-check позначення `incorrect` тепер залишає вправу незавершеною
та дає 0 XP. Позначення `correct` завершує її. Уже завершені вправи зберігають
попереднє завершення. Усі типи використовують наявний атомарний механізм XP.

## Запуск і синхронізація

`tzdata` додано до залежностей для підтримки Windows.
`START-WINDOWS.cmd` запускає наявні `setup` і `dev`.
Інструкція користувача — `ЗАПУСК-У-WINDOWS.md`.
Демонстраційний урок — `present-perfect-practice`.

Перед об'єднанням перевірте поточну Alembic head іншої гілки. Якщо там є
нова незалежна міграція, узгодьте граф міграцій. Нові вправи варто додавати
новим уроком, щоб зберегти зміст уже завершених уроків.

Для обміну наступною роботою передавайте актуальний архів або Git-гілку
разом зі списком змінених файлів, міграціями та результатами перевірок.
Прямий канал зв'язку з іншим розробником у цьому запиті не надано.

## Перевірки цієї передачі

- Backend pytest — 291 passed, 15 skipped. Серед пропусків є перевірки,
  що потребують PostgreSQL або інших умов середовища.
- Ruff та mypy — успішно.
- Інтеграційний прогін JS DOM із реальним локальним API — успішно.
  Перевірено відкладене повторення choice, tiles і text, Practice,
  повернення при скиданні поза коміркою, часткову чернетку, однакові літери,
  правильну відповідь і одноразове XP.
- ZoneInfo з порожнім системним TZPATH знаходить UTC та Europe/Kyiv через tzdata.
- Перевірено міграції й початковий запуск SQLite на Linux. Сам CMD-лаунчер
  у Windows потребує локального запуску другим розробником або користувачем.

## Windows npm command correction

The user reported `.venv is not recognized` while running `npm run db:seed`.
The root npm scripts still used `.venv/bin/...`. `scripts/backend.mjs` now runs
all backend modules with the platform-specific virtualenv Python and a fixed
backend working directory. Copy both updated `package.json` and
`scripts/backend.mjs` when integrating this correction. `backend:dev` uses the
existing cross-platform development launcher.

Validation of this correction passed for real npm migrate, seed (twice), prepare
and backend lint on Linux. The database has seven lessons and one copy of the
new practice lesson. An executable fixture verified Windows path selection,
working directory, arguments, paths with spaces and propagation of nonzero exit
codes. Native Windows execution remains a local verification step.
