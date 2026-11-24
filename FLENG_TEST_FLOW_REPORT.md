# Fleng English — діагностика проходження уроку

## Результат

**FIFO-черги неправильних завдань у коді немає.** `nextUnfinished()` обчислює наступне завдання з порядку вправ і серверних полів `attempts` та `completed`. Спочатку функція шукає вправу без спроб, а потім циклічно обходить решту незавершених вправ. Вона не додає помилки у FIFO-чергу й не зберігає позицію учня в цій послідовності.

Перевірено у Chromium через Playwright на реальному FastAPI з окремою тимчасовою SQLite. Використано тестового учня та опубліковані уроки `present-perfect-practice` і `greetings-and-introductions`. Ввід, Enter, кнопки, перетягування та перезавантаження виконано в браузері. POST-запити й відповіді API спостерігалися без підміни. Перевірка стосується SQLite та Chromium. Конкурентні запити, інші браузери й PostgreSQL у цьому проході не тестувалися.

| № | Статус | Що відбулося |
|---|---|---|
| 1 | PASS | Після правильної відповіді відкрилася наступна незавершена вправа. |
| 2 | FAIL | Помилка відображається, перехід є, але порядок повторів залежить від позиції вправи. |
| 3 | PASS | Вправи з помилками повернулися після першого проходу й залишалися незавершеними до успіху. |
| 4 | PASS | Урок залишався незавершеним до 3/3. Для самооцінки сервер зараховує позначку учня. |
| 5 | PASS | Повторна правильна відповідь принесла 0 додаткових XP. |
| 6 | PASS | Автонадсилання приблизно через 1,5 с, Enter надсилає одразу. |
| 7 | PASS | Enter до спрацювання таймера дав один POST. |
| 8 | PASS | При недійсному скиданні плитка залишилася у джерелі поточного перетягування. |
| 9 | PASS | Після заповнення останньої комірки надійшов один POST. |
| 10 | PASS | Усі чотири форми входять у спільний механізм переходів. Його обмеження описано в пункті 2. |
| 11 | FAIL | Серверний прогрес відновлюється. Позиція вправи та порядок повторення після reload не відновлюються. |
| 12 | FAIL | Зразок з'явився лише після вибору самооцінки. |

## 1. Правильна відповідь — PASS

У `present-perfect-practice` правильний вибір `has` перевів з №1 до незавершеної №2. Після правильної текстової відповіді відкрилася наступна доступна за чинним алгоритмом вправа. Після останньої правильної відповіді сервер повернув завершення уроку.

**Код** [lesson.js:311](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:311)

```js
state.progress = result.lesson;
const next = nextUnfinished(state.index);
if (next !== -1 && next !== state.index) {
  // …зберігає відгук про попередню вправу…
  state.index = next;
}
```

**Причина і рекомендація.** Наступний індекс залежить від свіжого серверного прогресу, а успішна вправа виключається з пошуку. Для цього сценарію виправлення не потрібне.

## 2. Помилка, перехід і кінець черги — FAIL

Неправильний вибір показав `Incorrect`, правильний варіант `has` та пояснення, після чого браузер автоматично відкрив ще не виконану №3. Порядок повторення перевірено через дозволену навігацію. Спочатку помилився в №2, потім у №1, після чого правильно відповів на №3. Першою повернулася №1, хоча раніше помилка сталася у №2.

**Код** [lesson.js:117](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:117) · [Показ відгуку після переходу](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:319)

```js
const indices = exercises.map((_, index) => (after + 1 + index) % exercises.length);
const unfinished = indices.filter((index) => !records.get(exercises[index].id)?.completed);
return unfinished.find((index) => !records.get(exercises[index].id)?.attempts)
  ?? unfinished[0] ?? -1;
```

**Причина і рекомендація.** Вибір базується на індексах і кількості спроб. Зберігати впорядковані ID вправ для повторення. Після кожної нової помилки переносити її ID у кінець без дублювання, після правильної відповіді вилучати його. Показ відгуку можна залишити в наявному спільному обробнику.

## 3. Повторення до правильної відповіді — PASS

№1 повернулася після першого проходу. Друга помилка збільшила лічильник до двох спроб і дала 0 XP. Після правильної відповіді №1 зарахувалася. №2 залишалася незавершеною, доки не було зібрано `been`. Коли лишається тільки поточна незавершена вправа, код залишає її на екрані.

**Код** [service.py:330](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:330) · [lesson.js:319](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:319)

```python
submission.attempts += 1
submission.submitted_at = now
if will_complete and not submission.completed:
    submission.completed = True
```

**Причина і рекомендація.** Неправильна відповідь не встановлює `completed` для незавершеної вправи. Зберегти це серверне правило при додаванні FIFO. Якщо учень повторно відкриває вже зараховану вправу, пізніша помилка не скасовує її завершення.

## 4. Завершення після всіх обов'язкових вправ — PASS

Після правильних відповідей на №1 і №3 урок `present-perfect-practice` залишився незавершеним. Після правильного виконання №2 результат API став `completed: true`, `exercisesCompleted: 3`, `exercisesTotal: 3`. Сервер рахує всі вправи уроку. Для `self_check` критерієм є позначка учня `correct`. Зміст вільної відповіді сервер цим шляхом не оцінює.

**Код** [service.py:327](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:327) · [Підрахунок завершення](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:363)

```python
if exercise.type == "self_check":
    is_correct = self_assessment == "correct"
# …
if total > 0 and completed == total and record.status != "completed":
```

**Причина і рекомендація.** Сервер порівнює число зарахованих вправ конкретного учня із загальною кількістю. Виправлення для підрахунку не потрібне. Для вільної відповіді застосувати зміну з пункту 12, щоб учень міг оцінити себе після порівняння.

## 5. Одноразове нарахування XP — PASS

Для однієї вправи сервер повернув 0 XP за помилку, 1 XP за першу правильну відповідь і 0 XP після повторного правильного вводу через браузер.

**Код** [service.py:342](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:342) · [Унікальність запису учня і вправи](/C:/Users/Roman/Fleng-GitHub/backend/app/db/models.py:347)

```python
.where(
    ExerciseSubmission.id == submission.id,
    ExerciseSubmission.xp_awarded.is_(False),
)
.values(xp_awarded=True)
```

**Причина і рекомендація.** Бали додаються, коли умовний UPDATE змінює один рядок. Виправлення для перевіреного сценарію не потрібне.

## 6. Пауза 1,5 с або Enter — PASS

Після введення `never` через 750 мс запиту ще не було. POST зафіксовано через приблизно 1508–1515 мс від початку операції заповнення. В іншій вправі Enter до завершення таймера дав POST приблизно за 8–10 мс від початку операції натискання.

**Код** [auto-check.js:5](/C:/Users/Roman/Fleng-GitHub/frontend/js/auto-check.js:5) · [Підключення до текстової вправи](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:499)

```js
if (!composing && input.value.trim()) timer = setTimeout(checkNow, 1500);
// …
form.addEventListener('submit', (event) => {
  event.preventDefault();
  checkNow();
});
```

**Причина і рекомендація.** Подія `input` перевстановлює таймер, а submit форми запускає перевірку одразу. Виправлення не потрібне.

## 7. Один POST після Enter — PASS

У браузері ввів `likewise`, через приблизно пів секунди натиснув Enter і після переходу почекав ще 1,6 с. Зафіксовано один POST. Одночасне спрацювання на межі таймера та утримання Enter окремо не перевірялися.

**Код** [auto-check.js:5](/C:/Users/Roman/Fleng-GitHub/frontend/js/auto-check.js:5) · [lesson.js:296](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:296)

```js
clearTimeout(timer);
if (form.isConnected && !composing && input.value.trim()) check(input.value);
// lesson.js
if (state.busy) return;
```

**Причина і рекомендація.** Enter скасовує таймер, а `state.busy` блокує паралельний виклик. Для перевіреного сценарію виправлення не потрібне. Для повного регресійного покриття варто перевірити Enter біля межі таймера та з мережею, що відповідає із затримкою.

## 8. Скидання плитки поза доступною коміркою — PASS

Перетягування плитки `a` з банку на заголовок уроку залишило її в банку. Перетягування вже вставленої `e` на той самий заголовок залишило її у вихідній комірці. В обох випадках розкладка до початку перетягування збереглася. Якщо під «початковим місцем» мається на увазі банк навіть для вже вставленої плитки, поточна поведінка йому не відповідає. Плитку з комірки можна повернути в банк натисканням на комірку.

**Код** [letter-tiles.js:50](/C:/Users/Roman/Fleng-GitHub/frontend/js/letter-tiles.js:50) · [Обробники комірки](/C:/Users/Roman/Fleng-GitHub/frontend/js/letter-tiles.js:96)

```js
button.addEventListener('dragend', () => { dragged = null; });
// …
if (dragged === null || assigned[index] !== null) return;
event.preventDefault();
```

**Причина і рекомендація.** Призначення плитки змінюється лише після прийнятого переміщення. Для повернення до джерела перетягування виправлення не потрібне. Якщо потрібне повернення вставленої плитки у банк, це слід явно визначити для недійсного скидання й перевірити обидва джерела плитки.

## 9. Автоперевірка після останньої комірки — PASS

Після заповнення першої комірки в `b__n` запиту не було. Після другої був один POST без кнопки перевірки. Перевірено неправильну комбінацію `baon` і правильну `been`.

**Код** [letter-tiles.js:44](/C:/Users/Roman/Fleng-GitHub/frontend/js/letter-tiles.js:44) · [lesson.js:473](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:473) · [Серверна перевірка плиток](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:268)

```js
const answer = tiles.readAnswer();
if (answer) submit(exercise, answer);
```

**Причина і рекомендація.** `readAnswer()` повертає порожній рядок, поки є незаповнений пропуск. Виправлення не потрібне.

## 10. Спільні переходи для всіх типів — PASS

У браузері спостерігав відповіді через радіокнопку, текстове поле, плитки й кнопку самооцінки. Усі чотири викликають один `submit()`, оновлюють прогрес тим самим результатом API і використовують `nextUnfinished()`. Окремо перевірив хибну текстову відповідь і обидві кнопки самооцінки. Спроба з неправильним текстом повернула 0 XP. Позначка «I got it right» зарахувала вільний текст за правилом самооцінки. Різняться тригери та правило оцінювання. FIFO відсутня для всіх типів.

**Код** [Вибір](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:454) · [Плитки](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:473) · [Текст](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:499) · [Самооцінка](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:509)

```js
submit(exercise, input.value);                       // вибір
if (answer) submit(exercise, answer);                // плитки
autoCheckText(form, input, (answer) => submit(exercise, answer));
button.addEventListener('click', () => submit(exercise, readAnswer(), assessment));
```

**Причина і рекомендація.** Узгодженість забезпечує спільний обробник. Якщо додавати чергу, оновлювати її в цьому обробнику для всіх форматів.

## 11. Відновлення після перезавантаження — FAIL

JSON серверного прогресу до й після перезавантаження збігся. Збережені спроби та зараховані вправи лишилися доступні. У повторному запуску після помилки в №1 браузер перейшов до №2. Перезавантаження повернуло до №1 при ідентичному серверному прогресі. Позиція відновлюється через новий виклик `nextUnfinished()` від початку уроку. Незбережені текстова й плиткова чернетки скидаються. Окремої збереженої черги для відновлення немає.

**Код** [lesson.js:665](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:665) · [Побудова серверного прогресу](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:194)

```js
state.progress = progress;
state.index = Math.max(0, nextUnfinished());
state.drafts.clear();
state.tileDrafts.clear();
```

**Причина і рекомендація.** API повертає прогрес вправ, а фронтенд обчислює наступний індекс заново. Зберігати ID поточної вправи й порядок повторів для конкретного учня та уроку. На відновленні звіряти їх зі свіжим серверним прогресом. Для відновлення між пристроями ці дані мають бути доступні з сервера.

## 12. Зразок до самооцінки — FAIL

У `greetings-and-introductions` після введення `Good morning!` були кнопки `I got it right` та `I need practice`, але зразка не було. Після `I need practice` API повернув `modelAnswer: "Good morning!"`, який з'явився у відгуку. Це суперечить інструкції спочатку порівняти відповідь зі зразком.

**Код** [Інструкція](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/instructions.py:47) · [Кнопки](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:505) · [Рендеринг зразка](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:268) · [Відповідь сервера](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:425)

```js
if (result.modelAnswer) box.append(labelled(t('lesson.modelAnswer'), result.modelAnswer));
```

```python
model_answer=exercise.model_answer if exercise.type == "self_check" else None,
```

**Причина і рекомендація.** Кнопки надсилають остаточну самооцінку, а зразок доступний у результаті цього запиту. Додати крок «Показати зразок» після непорожньої відповіді. Відкриття зразка має обходитися без зарахування вправи, спроби та XP. Кнопки самооцінки показувати після відкриття зразка.

## Повний шлях від дії учня до збереження і переходу

1. **Подія в браузері.** Вибір варіанта викликає `checkChoice`. Плитки викликають callback, коли `readAnswer()` повертає слово. Текст викликає `autoCheckText` через таймер або Enter. Самооцінка передає `correct` чи `incorrect` разом із текстом. [lesson.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:443) · [auto-check.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/auto-check.js:1) · [letter-tiles.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/letter-tiles.js:44)
2. **Підготовка запиту.** `submit()` відсікає порожню відповідь і блокує одночасне надсилання. `submitAnswer()` через `apiFetch()` виконує `POST /api/v1/lessons/{slug}/submit` з `exerciseId`, `answer` і, для самооцінки, `selfAssessment`. [lesson.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:296) · [api.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/api.js:385)
3. **Маршрутизація.** FastAPI отримує учня та сесію БД через залежності. `SubmissionRequest` визначає форму запиту. Роутер знаходить опублікований урок та вправу в ньому й передає дані сервісу. [router.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/router.py:45) · [schemas.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/schemas.py:48)
4. **Валідація й оцінка.** Сервіс перевіряє ID варіанта, непорожній текст, допустимі плитки чи ознаку самооцінки. У транзакції блокує зміни для учня, отримує агрегований прогрес і записи уроку та вправи. `grade_objective()` порівнює ID або нормалізований текст. Для самооцінки зарахування визначає вибір учня. [service.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:261) · [grading.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/grading.py:40) · [lock_learner](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/gamification/service.py:64)
5. **Запис результату.** Сервіс оновлює останню відповідь, ознаку правильності, число спроб і час. При першому зарахуванні встановлює `completed` і умовно нараховує XP. Перераховує завершені вправи. Коли зараховано всі, одноразово змінює стан уроку та оновлює агрегований прогрес і словник. Записує навчальну активність і виконує `db.commit()`. [service.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:332) · [Завершення і коміт](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:383) · [Збирання слів](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/vocabulary/service.py:117)
6. **Відповідь і перехід.** Після коміту API повертає результат і знімок `lesson`. Фронтенд оновлює `state.progress` і поточний відгук. Якщо `nextUnfinished()` обирає іншу вправу, відгук залишається в `#lesson-last-answer`, а наступна картка рендериться після завершення запиту. Після HTTP-помилки показується можливість повторити перевірку, індекс не просувається. [Відповідь сервісу](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:408) · [Переходи та відгук](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:311)
7. **Повторне відкриття.** `loadLesson()` отримує каталог вправ і `GET /lessons/{slug}/progress`. Сервер будує знімок зі збережених записів конкретного учня. Фронтенд з нього перевибирає вправу, тому опублікований порядок і спроби впливають на відновлення. [lesson.js](/C:/Users/Roman/Fleng-GitHub/frontend/js/lesson.js:658) · [router.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/router.py:34) · [service.py](/C:/Users/Roman/Fleng-GitHub/backend/app/modules/exercises/service.py:194)
