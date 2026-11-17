# Виправлення запуску — 2026-11-17

Поточний архів: вебверсія 2026.11.17-web.3.1, на основі web.3 нижче.
`START-WINDOWS.cmd` запускає існуючі setup/dev напряму через Node.js із
абсолютними шляхами. Перевіряє Node.js 20+, наявність scripts/backend/frontend,
зупиняється при помилці setup та повертає код завершення сервера.
Це усуває залежність запуску від відсутнього npm-скрипту у змішаній локальній
копії. У збереженому package.json `setup` уже був присутній; локальний файл
користувача тут недоступний, тому причина його відмінності не підтверджена.
Поточна перевірка: 49/49 frontend-тестів; node --check для setup/dev;
перевірено наявність цільових файлів, порядок preflight/зупинки після setup
та git diff --check. Windows CMD тут не виконувався.
Дизайн, API, авторизацію та дані не змінено.
Нових commit, push та розгортання не виконано.

Нижче — попередній звіт web.3; наведені там перевірки історичні.

# Fleng — результат для перевірки

Підготовлено вебверсію 2026.11.16-web.3: дизайн за PNG-експортами Figma та
пакетне завантаження прогресу курсу. Додатка, EXE чи встановлення PWA немає.
Нових commit, push або розгортання на хостингу не виконано.

## Пакетний API

`GET /api/v1/courses/{slug}/progress` — Bearer-авторизація.

Видає лише статуси поточного користувача для опублікованого курсу та його
опублікованих уроків. userId у запиті не змінює власника даних. Відсутній або
неопублікований курс: 404; немає авторизації: 401. Заголовок відповіді:
`Cache-Control: private, no-store`. Видача виконує два SQL SELECT незалежно від
кількості уроків, окрім існуючих запитів авторизації.

```json
{
  "courseId": "00000000-0000-4000-8000-000000000001",
  "lessonsTotal": 3,
  "lessonsStarted": 2,
  "lessonsCompleted": 1,
  "lessons": [
    {"lessonId": "00000000-0000-4000-8000-000000000002", "slug": "lesson-one", "status": "completed"},
    {"lessonId": "00000000-0000-4000-8000-000000000003", "slug": "lesson-two", "status": "in_progress"},
    {"lessonId": "00000000-0000-4000-8000-000000000004", "slug": "lesson-three", "status": "not_started"}
  ]
}
```

Це приклад структури, а не записи реальної бази. lessonsStarted включає завершені
уроки. Для порожнього курсу всі лічильники нульові та lessons порожній.
Детальний `GET /api/v1/lessons/{slug}/progress` збережено. Алгоритми XP, перевірки
відповідей, запису прогресу, auth/refresh та AI не змінені оптимізацією.

Сторінка курсу спочатку показує каталог, потім робить один запит прогресу.
Помилка прогресу залишає всі уроки та посилання; невідомий статус позначається
як недоступний, а не як Not Started. Є повторне завантаження.

## Ізоляція змін

Оптимізація виконана без комітів у гілці `feat/course-progress-batch` та окремому
worktree `fleng-progress`. Її робочий diff містить тільки:

- backend/app/modules/catalog/router.py
- backend/app/modules/catalog/schemas.py
- backend/app/modules/catalog/service.py
- backend/tests/test_course_progress_batch.py
- frontend/js/course.js
- scripts/test-courses.mjs

Модуль progress і міграції не змінені. Оформлення, навігація, Dashboard та Words
змінені окремо лише на виконання твого завдання про дизайн. Обидві частини
поєднані для перевірки в гілці `review/fleng-web3`, також без нового коміту.

## Перевірки

- 88 цільових backend-тестів пройшли, у тому числі 8 нових для пакетного API:
  порожній / нерозпочатий / частковий / завершений курс, авторизація,
  ізоляція іншого користувача, приховані чернетки, незмінна кількість SQL-запитів
  і збережений детальний API.
- 49 frontend-тестів пройшли: один пакетний запит, доступність уроків після збою,
  повторне завантаження та попередні сценарії курсів, AI і словника.
- Ruff пройшов для зміненого Python-коду й нового тесту.
- mypy пройшов для всіх 82 файлів застосунку.
- git diff --check пройшов.
- Перевірка документації: 43 операції API, 50 схем, 0 помилок.
- Прибирання старого service worker та відсутність встановлення перевірені.
- У браузері перевірено оформлення команди, головної, входу, налаштувань і
  словника, перехід картки → тест → підсумок 50% → повторення однієї помилки.
- Вузькі екрани 390 px: словник, команда та налаштування без горизонтального
  переповнення. Це перевірка адаптації в iframe, не на фізичному телефоні.

Windows-скрипт, реальний вхід у браузері, PostgreSQL та публічний хостинг тут не
перевірені. Кнопки соціального входу позначені недоступними; аватар David умовний.
Справжній пароль не відображається. Верстка відтворена за PNG, без заяви про
перевірку редагованих шарів чи точний збіг кожного пікселя Figma.

## Усі файли поточної зміни

- README.md
- backend/app/modules/catalog/router.py
- backend/app/modules/catalog/schemas.py
- backend/app/modules/catalog/service.py
- backend/tests/test_course_progress_batch.py
- backend/tests/test_frontend.py
- docs/03-backend/api-schemas.md
- docs/03-backend/catalog-api.md
- docs/figma-export-web3.md
- docs/website-release.md
- frontend/assets/figma/mail.svg
- frontend/assets/figma/password.svg
- frontend/assets/figma/profile.svg
- frontend/course-words.html
- frontend/course.html
- frontend/courses.html
- frontend/css/figma-reference.css
- frontend/css/team.css
- frontend/dashboard.html
- frontend/index.html
- frontend/js/auth-controls.js
- frontend/js/course-words.js
- frontend/js/course.js
- frontend/js/dashboard.js
- frontend/js/letter-tiles.js
- frontend/js/practice.js
- frontend/js/vocabulary.js
- frontend/js/workspace.js
- frontend/leaderboard.html
- frontend/lesson.html
- frontend/login.html
- frontend/practice.html
- frontend/register.html
- frontend/settings.html
- frontend/team.html
- frontend/version.json
- frontend/vocabulary.html
- plans/roadmap.md
- project-map/api-map.md
- project-map/modules.md
- scripts/test-courses.mjs
- scripts/test-study.mjs
- scripts/update-website.ps1
