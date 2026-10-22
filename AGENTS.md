# AGENTS.md — Fleng Project Agent Rules

This file is the working contract for every agent and developer contributing to Fleng.
Read it before making any change, then read `README.md`, `docs/`, `project-map/`, and `plans/`.

> Project status: **M2 + catalog + graded lessons** (plain HTML/CSS/JS frontend
> served by FastAPI). Email/password auth, profiles, progress, the course/lesson
> catalog and a graded exercise flow work end to end. Vocabulary, streaks and AI
> are not implemented yet.

---

## Backend stack rules (non-negotiable)

- **Backend MUST use the existing Python + FastAPI stack.** Do not introduce
  NestJS, Express, Node.js backend frameworks, or TypeScript backend code.
- **TypeScript is not used anywhere.** The frontend is plain JavaScript; the
  backend is Python. Do not introduce TypeScript, a build step or a JS
  type-checker.
- The backend is `backend/`: Python, FastAPI, Pydantic, SQLAlchemy 2 (async),
  Alembic, pytest, Ruff, mypy. It has no Node/TypeScript dependency and also
  serves the static frontend files.
- The frontend is `frontend/`: plain **HTML5, CSS3 and vanilla JavaScript**
  (browser ES modules, `fetch`). It has **no** framework, **no** TypeScript,
  **no** build system and no bundler. It is served as static files by the
  FastAPI backend from the same origin as `/api/v1`. Do not reintroduce React,
  Next.js, Vue, Angular, Tailwind or a build step.
- The frontend talks to the backend only over REST/JSON at `/api/v1`; the backend
  is the only place allowed to touch the database or AI providers. The backend
  also serves the static frontend files.
- Historical note: the backend was originally sketched as NestJS + TypeScript but
  was implemented as FastAPI + Python. NestJS/TypeScript backend references must
  not be reintroduced into code, docs, project-map or plans.

---

## Project Agent Rules

### 1. Используй существующий стек

Всегда в первую очередь используй технологии, библиотеки, фреймворки и инструменты, которые уже присутствуют в проекте.

Не заменяй существующий стек просто потому, что тебе нравится другой.

Не добавляй новую технологию без реальной необходимости.

Если существующий стек позволяет решить задачу — используй его.

### 2. Не создавать костыли ради технологий

Никогда не добавляй технологию только ради того, чтобы она присутствовала в проекте.

Не создавай:

- ненужные abstraction layers
- fake implementations
- бесполезные wrappers
- дублирующие сервисы
- микросервисы без необходимости
- отдельные системы ради "масштабируемости"
- зависимости ради одной функции

Если проблема решается существующими средствами проекта — используй их.

Принцип:

`простое корректное решение > сложное решение ради архитектуры`

### 3. Сначала изучи существующий код

Перед изменением системы:

- изучи структуру проекта
- найди связанные модули
- изучи существующие interfaces
- проверь зависимости
- посмотри git history
- пойми существующие архитектурные решения

Не переписывай существующий код без необходимости.

### 4. Git commits обязательны

Работа должна выполняться небольшими логическими коммитами.

После завершения логического этапа делай commit.

Примеры:

`chore: initialize project structure`

`docs: add backend architecture`

`docs: add database model`

`feat: implement authentication`

`fix: resolve authentication validation`

Не объединяй несвязанные изменения в один огромный commit.

Перед commit обязательно проверь:

- git diff
- git status
- отсутствие случайных файлов
- отсутствие секретов
- отсутствие debug-кода

НЕ делай `git push`, если пользователь явно не попросил.

### 5. Обновляй карту проекта

После значимых архитектурных изменений обязательно обновляй:

`project-map/`

и связанные документы в:

`docs/`

`plans/`

Карта проекта никогда не должна сильно отставать от реального состояния репозитория.

Если появился новый модуль — он должен появиться на карте.

Если изменился data flow — обнови его.

Если изменился API — обнови API map.

### 6. Обновляй план

После завершения каждого крупного этапа обновляй:

`plans/`

Отмечай:

- completed
- in progress
- blocked
- next

Не оставляй roadmap в состоянии, которое противоречит реальному проекту.

### 7. Независимый взгляд

После завершения значимого изменения обязательно проведи отдельный self-review.

Представь, что ты независимый senior engineer, который впервые видит этот pull request.

Проверь:

- архитектуру
- безопасность
- дублирование
- сложность
- потенциальные баги
- неправильные зависимости
- нарушение существующих conventions
- неиспользуемый код
- документацию
- тестируемость
- соответствие плану

Не считай свою первую реализацию автоматически правильной.

Сначала реализуй → затем отойди от решения → проверь его "с независимым взглядом" → исправь найденные проблемы.

### 8. Не скрывай проблемы

Если обнаружена проблема в существующем проекте — сообщи о ней.

Не маскируй архитектурную проблему костылем.

Если решение требует изменения архитектуры — сначала объясни почему.

### 9. Не overengineer

Не проектируй систему так, будто у неё уже миллион пользователей.

Начинай с простого и расширяемого решения.

Предпочтительно:

`Modular Monolith`

вместо преждевременных микросервисов.

### 10. Definition of Done

Задача считается завершённой только если:

- код/документация работают
- структура проекта актуальна
- tests/checks выполнены, если применимо
- project-map обновлена
- plans обновлены
- документация соответствует реализации
- проведён независимый self-review
- изменения сохранены логическими git commits

---

## Project Context (quick reference)

- **Product:** Fleng — a premium dark English-learning web platform.
- **Architecture:** modular monolith. One backend deployable, one frontend deployable, one shared AI layer. No microservices.
- **Frontend:** plain HTML5, CSS3 and vanilla JavaScript (ES modules, `fetch`), served statically by the backend.
- **Backend:** Python — FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic.
- **Repository:** one backend deployable that also serves the static frontend; the backend is a Python project with its own virtualenv. Orchestrated by root Node scripts.
- **Database:** PostgreSQL.
- **AI:** a future Python layer consumed by the backend AI module. Not a separate service.
- **Source of truth:**
  - Architecture → `docs/architecture.md`
  - Stack + rationale → `docs/development.md`
  - Modules → `project-map/modules.md`
  - Data model → `docs/database.md`
  - API → `docs/api.md` + `project-map/api-map.md`
  - Auth → `docs/authentication.md`
  - Security → `docs/security.md`
  - Roadmap/status → `plans/roadmap.md` + `plans/milestones.md`
  - Visual language → `design/`

## Repository layout

```
/
├── frontend/     # static HTML/CSS/JS user interface (served by FastAPI)
├── backend/      # FastAPI API (Python, modular monolith)
├── ai/           # future Python AI layer (docs only)
├── docs/         # durable architecture + engineering documentation
├── plans/        # roadmap, per-area plans, milestones
├── design/       # design system + UX documentation
├── project-map/  # living map of modules and flows
├── scripts/      # root tooling (dev orchestration, backend setup)
├── AGENTS.md     # this file
├── README.md     # entry point for newcomers
└── .gitignore
```

## Change workflow

Follow this loop for every meaningful stage:

`ANALYZE → PLAN → IMPLEMENT → TEST → INDEPENDENT REVIEW → FIX → UPDATE DOCS → UPDATE PROJECT MAP → UPDATE PLAN → COMMIT`
