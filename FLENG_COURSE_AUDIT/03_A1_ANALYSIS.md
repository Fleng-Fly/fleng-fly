# Аудит A1 — Beginner

## Структура і статус

Курс **A1 — Beginner** (`fleng-a1`) має 10 уроків. Розділи в моделі й каталозі відсутні, уроки належать напряму курсу. Нижче подано порядок `position`, який збігається з ланцюжком `prerequisites` у джерелі. Перший урок посилається на завершальну тему A0. Передумови описують авторську послідовність. Каталог відкриває опублікований урок за прямим URL.

- 100 базових і 100 додаткових словникових записів. У цих 200 записів поле `example` порожнє. Приклади є в теорії. Поля транскрипції у джерелі та БД немає.
- 220 вправ: 50 основних тренувальних, 30 базових перевірок лексики, 40 форматів додаткової практики і 100 згенерованих перевірок перекладу. За механізмом 180 `single_choice`, 30 `text`, 10 `self_check`.
- 10 доступних перших проходів тесту уроку. Незалежних контрольних тестів курсу — 0. За редакційними категоріями 90 тренувальних і 130 перевірочних пунктів, але плеєр запускає спільну послідовність із 22 завдань.
- Перший прохід закінчується після однієї відповіді або пропуску кожного пункту. Для повного завершення уроку потрібен правильний стан усіх 22 вправ, у тому числі підтверджена учнем самоперевірка. Курс завершено після всіх опублікованих уроків. [Технічні деталі](01_ARCHITECTURE.md).
- У каталозі також є окремий курс English Foundations. Його 3 уроки наведено нижче.


| № | Урок | Slug | Тема |
| --- | --- | --- | --- |
| 1 | My home and possessions | `fleng-a1-possessions` | Володіння та житло |
| 2 | A typical weekday | `fleng-a1-routines` | Звички й третя особа |
| 3 | Asking about habits | `fleng-a1-routine-questions` | Питання про звички й частотність |
| 4 | Time and schedules | `fleng-a1-time` | Час, дні, розклад |
| 5 | Places in my town | `fleng-a1-town` | Місто й there is/are |
| 6 | Food and simple quantities | `fleng-a1-food` | Їжа, кількість і замовлення |
| 7 | What can you do? | `fleng-a1-abilities` | Уміння з can |
| 8 | What is happening now? | `fleng-a1-right-now` | Дії зараз |
| 9 | Free time and preferences | `fleng-a1-likes` | Хобі, уподобання й причина |
| 10 | Where were you yesterday? | `fleng-a1-yesterday` | Минулий час be |

## Аналіз усіх десяти уроків

### 1. My home and possessions

- **Теорія.** Коректний контраст have/has і присвійні визначники. Потрібна повна таблиця включно з its, your та чітке зіставлення з `I/you/she…`. `his/her` узгоджуються з власником, а не з предметом. Питання й заперечення логічно відкласти до do/does. У базовому матеріалі 3 приклади, текст на 23 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `flat` — типово BrE, пояснити пару `apartment`. `furniture` незлічуване — позначити, але не вимагати до теми кількості. У пріоритеті `living room`, `house`, `room`; `wardrobe` і `drawer` можуть бути рецептивними.
- **Завдання.** `practice-4` робить стать Anna припущенням; краще `Anna is my sister` або явний займенник. `extra-4` доречно застосовує have + my, зразок можна зберегти.
- **Рішення.** Зберегти тему. Повернути `my/your` з A0, зробити завдання на вибір нового власника.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 49 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| home | дім | — | База |
| flat | квартира | — | База |
| kitchen | кухня | — | База |
| bedroom | спальня | — | База |
| bathroom | ванна кімната | — | База |
| garden | сад | — | База |
| phone | телефон | — | База |
| bicycle | велосипед | — | База |
| balcony | балкон | — | База |
| sofa | диван | — | База |
| furniture | меблі | — | Доповнення |
| mirror | дзеркало | — | Доповнення |
| wardrobe | шафа для одягу | — | Доповнення |
| drawer | шухляда | — | Доповнення |
| stairs | сходи | — | Доповнення |
| fridge | холодильник | — | Доповнення |
| shower | душ | — | Доповнення |
| towel | рушник | — | Доповнення |
| blanket | ковдра | — | Доповнення |
| pillow | подушка | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-possessions-practice-1` | She ___ a bicycle. | has |
| `fleng-a1-possessions-practice-2` | They ___ a flat. | have |
| `fleng-a1-possessions-practice-3` | This phone belongs to me. It is ___ phone. | my |
| `fleng-a1-possessions-practice-4` | Anna has a garden. ___ garden is small. | Her |
| `fleng-a1-possessions-practice-5` | We have a kitchen. It is ___ kitchen. | our |
| `fleng-a1-possessions-check-1` | Choose the Ukrainian meaning of "kitchen" in this lesson. | кухня |
| `fleng-a1-possessions-check-2` | Choose the Ukrainian meaning of "garden" in this lesson. | сад |
| `fleng-a1-possessions-check-3` | Choose the Ukrainian meaning of "balcony" in this lesson. | балкон |
| `fleng-a1-possessions-extra-1` | My brother ___ a new bicycle. (have) | has |
| `fleng-a1-possessions-extra-2` | Put the words in order to make a sentence: have / We / a / garden / small | We have a small garden |
| `fleng-a1-possessions-extra-3` | Translate into English: «кухня» | kitchen |
| `fleng-a1-possessions-extra-4` | Write two sentences about your home. Use have or has and my. | I have a small flat. My kitchen has a big window. |
| `fleng-a1-possessions-vocabulary-1` | What is the Ukrainian translation of «furniture»? | меблі |
| `fleng-a1-possessions-vocabulary-2` | Which English expression means «дзеркало»? | mirror |
| `fleng-a1-possessions-vocabulary-3` | What is the Ukrainian translation of «wardrobe»? | шафа для одягу |
| `fleng-a1-possessions-vocabulary-4` | Which English expression means «шухляда»? | drawer |
| `fleng-a1-possessions-vocabulary-5` | What is the Ukrainian translation of «stairs»? | сходи |
| `fleng-a1-possessions-vocabulary-6` | Which English expression means «холодильник»? | fridge |
| `fleng-a1-possessions-vocabulary-7` | What is the Ukrainian translation of «shower»? | душ |
| `fleng-a1-possessions-vocabulary-8` | Which English expression means «рушник»? | towel |
| `fleng-a1-possessions-vocabulary-9` | What is the Ukrainian translation of «blanket»? | ковдра |
| `fleng-a1-possessions-vocabulary-10` | Which English expression means «подушка»? | pillow |

### 2. A typical weekday

- **Теорія.** Загальна послідовність вдала. `before/after` згадано без показу синтаксису. Чернетковий гід формулює -es після -o як універсальне правило. Дати частотні go/goes і do/does як конкретні форми, додати have/has як повторення. У базовому матеріалі 3 приклади, текст на 27 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `wake up` і `get up` корисно протиставити. `brush my teeth` позначити як шаблон зі змінним присвійним словом. `pack a bag` і `set the alarm` потребують прикладів. `work` краще мати окремо як дієслово й уживання `after work` як іменник.
- **Завдання.** `extra-1` щодо has є виправданим повторенням попереднього уроку. `extra-4` просить три речення про ранок, що узгоджується з метою. Додати продукцію про третю особу; MC на впізнавання форм цього не вимірюють.
- **Рішення.** Зберегти послідовність. Увести короткий сценарій про двох людей і варіативну практику.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 41 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| wake up | прокидатися | — | База |
| breakfast | сніданок | — | База |
| work | працювати | — | База |
| study | навчатися | — | База |
| walk | ходити пішки | — | База |
| cook | готувати їжу | — | База |
| dinner | вечеря | — | База |
| sleep | спати | — | База |
| wash | мити | — | База |
| weekday | будній день | — | База |
| get up | вставати з ліжка | — | Доповнення |
| brush my teeth | чистити зуби | — | Доповнення |
| get dressed | одягатися | — | Доповнення |
| take a shower | приймати душ | — | Доповнення |
| lunch | обід | — | Доповнення |
| go home | йти додому | — | Доповнення |
| go to bed | лягати спати | — | Доповнення |
| set the alarm | ставити будильник | — | Доповнення |
| feed the cat | годувати кота | — | Доповнення |
| pack a bag | складати речі в сумку | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-routines-practice-1` | She ___ at home. (work) | works |
| `fleng-a1-routines-practice-2` | I ___ breakfast at seven. (eat) | eat |
| `fleng-a1-routines-practice-3` | He ___ English. (study) | studies |
| `fleng-a1-routines-practice-4` | They ___ dinner. (cook) | cook |
| `fleng-a1-routines-practice-5` | She ___ her hands. (wash) | washes |
| `fleng-a1-routines-check-1` | Choose the Ukrainian meaning of "work" in this lesson. | працювати |
| `fleng-a1-routines-check-2` | Choose the Ukrainian meaning of "cook" in this lesson. | готувати їжу |
| `fleng-a1-routines-check-3` | Choose the Ukrainian meaning of "wash" in this lesson. | мити |
| `fleng-a1-routines-extra-1` | She ___ breakfast at seven. (have) | has |
| `fleng-a1-routines-extra-2` | Put the words in order to make a sentence: up / I / at / wake / six | I wake up at six |
| `fleng-a1-routines-extra-3` | Translate into English: «вечеря» | dinner |
| `fleng-a1-routines-extra-4` | Write three sentences about your weekday morning. | I wake up at seven. I have breakfast. I walk to work. |
| `fleng-a1-routines-vocabulary-1` | What is the Ukrainian translation of «get up»? | вставати з ліжка |
| `fleng-a1-routines-vocabulary-2` | Which English expression means «чистити зуби»? | brush my teeth |
| `fleng-a1-routines-vocabulary-3` | What is the Ukrainian translation of «get dressed»? | одягатися |
| `fleng-a1-routines-vocabulary-4` | Which English expression means «приймати душ»? | take a shower |
| `fleng-a1-routines-vocabulary-5` | What is the Ukrainian translation of «lunch»? | обід |
| `fleng-a1-routines-vocabulary-6` | Which English expression means «йти додому»? | go home |
| `fleng-a1-routines-vocabulary-7` | What is the Ukrainian translation of «go to bed»? | лягати спати |
| `fleng-a1-routines-vocabulary-8` | Which English expression means «ставити будильник»? | set the alarm |
| `fleng-a1-routines-vocabulary-9` | What is the Ukrainian translation of «feed the cat»? | годувати кота |
| `fleng-a1-routines-vocabulary-10` | Which English expression means «складати речі в сумку»? | pack a bag |

### 3. Asking about habits

- **Теорія.** `do/does` та гола форма викладені коректно. Показати короткі відповіді явно, додати базову позицію `usually/never` з `be` і застерегти про гнучку позицію `sometimes`. Не змішувати правило частотності з правилами питання без прикладів. У базовому матеріалі 3 приклади, текст на 27 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `on sundays` слід показувати як `on Sundays`. `weekend/day off` корисно розрізнити, `take the bus`/`on foot` доречні. Новачку потрібні `by bus`, `go out` у контексті.
- **Завдання.** `extra-2` використовує `go out`, відсутнє в списку; дати зразок. `practice-5` вимірює значення `always`, а не позицію. Додати питання `How often…?` і відповідь для перенесення.
- **Рішення.** Розділити блоки do/does та частотність або зробити парні уроки.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 39 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| usually | зазвичай | — | База |
| often | часто | — | База |
| sometimes | іноді | — | База |
| never | ніколи | — | База |
| always | завжди | — | База |
| bus | автобус | — | База |
| train | поїзд | — | База |
| weekend | вихідні | — | База |
| habit | звичка | — | База |
| early | рано | — | База |
| every day | щодня | — | Доповнення |
| once a week | раз на тиждень | — | Доповнення |
| twice a month | двічі на місяць | — | Доповнення |
| how often? | як часто? | — | Доповнення |
| take the bus | їздити автобусом | — | Доповнення |
| on foot | пішки | — | Доповнення |
| go to work | йти на роботу | — | Доповнення |
| day off | вихідний день | — | Доповнення |
| on sundays | по неділях | — | Доповнення |
| before school | до початку занять | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-routine-questions-practice-1` | ___ you take the bus? | Do |
| `fleng-a1-routine-questions-practice-2` | Does she ___ early? | work |
| `fleng-a1-routine-questions-practice-3` | He ___ take the train. (negative) | doesn't |
| `fleng-a1-routine-questions-practice-4` | I ___ work on Sundays. (negative) | don't |
| `fleng-a1-routine-questions-practice-5` | They ___ walk to work. (every time) | always |
| `fleng-a1-routine-questions-check-1` | Choose the Ukrainian meaning of "sometimes" in this lesson. | іноді |
| `fleng-a1-routine-questions-check-2` | Choose the Ukrainian meaning of "bus" in this lesson. | автобус |
| `fleng-a1-routine-questions-check-3` | Choose the Ukrainian meaning of "habit" in this lesson. | звичка |
| `fleng-a1-routine-questions-extra-1` | ___ he usually take the train? (do or does?) | does |
| `fleng-a1-routine-questions-extra-2` | Put the words in order to make a sentence: often / go / you / Do / out | Do you often go out |
| `fleng-a1-routine-questions-extra-3` | Translate into English: «завжди» | always |
| `fleng-a1-routine-questions-extra-4` | Write one question about a friend's habits and one negative sentence about yours. | Does your friend often cook? I don't take the bus. |
| `fleng-a1-routine-questions-vocabulary-1` | What is the Ukrainian translation of «every day»? | щодня |
| `fleng-a1-routine-questions-vocabulary-2` | Which English expression means «раз на тиждень»? | once a week |
| `fleng-a1-routine-questions-vocabulary-3` | What is the Ukrainian translation of «twice a month»? | двічі на місяць |
| `fleng-a1-routine-questions-vocabulary-4` | Which English expression means «як часто?»? | how often? |
| `fleng-a1-routine-questions-vocabulary-5` | What is the Ukrainian translation of «take the bus»? | їздити автобусом |
| `fleng-a1-routine-questions-vocabulary-6` | Which English expression means «пішки»? | on foot |
| `fleng-a1-routine-questions-vocabulary-7` | What is the Ukrainian translation of «go to work»? | йти на роботу |
| `fleng-a1-routine-questions-vocabulary-8` | Which English expression means «вихідний день»? | day off |
| `fleng-a1-routine-questions-vocabulary-9` | What is the Ukrainian translation of «on sundays»? | по неділях |
| `fleng-a1-routine-questions-vocabulary-10` | Which English expression means «до початку занять»? | before school |

### 4. Time and schedules

- **Теорія.** `at/on/in` коректні для наведених прототипів. Бракує `at night`, `at noon` у теорії до `extra-2`, усіх днів, місяців і базового читання чверті до години. Час потрібний уже в попередніх рутинах. У базовому матеріалі 3 приклади, текст на 26 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `Monday/Friday/July` після імпорту втрачають велику літеру в словнику. `half past` перекладати конкретною парою `half past nine — пів на десяту`, `quarter to` — «за чверть до…» з прикладом. `appointment` потребує контексту.
- **Завдання.** `extra-4` просить два випадки, але три прийменники; модель містить три дії. `practice-1–3` повторюють теорію дослівно. Потрібен простий розклад із новими годинами й запитанням про фактичний час.
- **Рішення.** Перенести базові дні й години перед описом рутини. Винести години й розклад в окремий урок від календаря.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 41 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| hour | година | — | База |
| minute | хвилина | — | База |
| Monday | понеділок | — | База |
| Friday | п’ятниця | — | База |
| July | липень | — | База |
| noon | полудень | — | База |
| midnight | північ | — | База |
| break | перерва | — | База |
| timetable | розклад | — | База |
| appointment | зустріч за домовленістю | — | База |
| second | секунда | — | Доповнення |
| week | тиждень | — | Доповнення |
| month | місяць | — | Доповнення |
| year | рік | — | Доповнення |
| date | дата | — | Доповнення |
| a.m. | до полудня | — | Доповнення |
| p.m. | після полудня | — | Доповнення |
| half past | пів години після повної години | — | Доповнення |
| quarter to | за чверть до повної години | — | Доповнення |
| on time | вчасно | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-time-practice-1` | The lesson starts ___ nine o'clock. | at |
| `fleng-a1-time-practice-2` | We meet ___ Monday. | on |
| `fleng-a1-time-practice-3` | The course starts ___ July. | in |
| `fleng-a1-time-practice-4` | Half past nine is ___. | 9:30 |
| `fleng-a1-time-practice-5` | Quarter past ten is ___. | 10:15 |
| `fleng-a1-time-check-1` | Choose the Ukrainian meaning of "Monday" in this lesson. | понеділок |
| `fleng-a1-time-check-2` | Choose the Ukrainian meaning of "noon" in this lesson. | полудень |
| `fleng-a1-time-check-3` | Choose the Ukrainian meaning of "timetable" in this lesson. | розклад |
| `fleng-a1-time-extra-1` | The meeting is ___ Monday. (at, on or in?) | on |
| `fleng-a1-time-extra-2` | Put the words in order to make a sentence: at / starts / The / lesson / noon | The lesson starts at noon |
| `fleng-a1-time-extra-3` | Translate into English: «година» | hour |
| `fleng-a1-time-extra-4` | Write when you do two things. Use at, on and in. | I study at eight. I visit my parents on Sunday and travel in July. |
| `fleng-a1-time-vocabulary-1` | What is the Ukrainian translation of «second»? | секунда |
| `fleng-a1-time-vocabulary-2` | Which English expression means «тиждень»? | week |
| `fleng-a1-time-vocabulary-3` | What is the Ukrainian translation of «month»? | місяць |
| `fleng-a1-time-vocabulary-4` | Which English expression means «рік»? | year |
| `fleng-a1-time-vocabulary-5` | What is the Ukrainian translation of «date»? | дата |
| `fleng-a1-time-vocabulary-6` | Which English expression means «до полудня»? | a.m. |
| `fleng-a1-time-vocabulary-7` | What is the Ukrainian translation of «p.m.»? | після полудня |
| `fleng-a1-time-vocabulary-8` | Which English expression means «пів години після повної години»? | half past |
| `fleng-a1-time-vocabulary-9` | What is the Ukrainian translation of «quarter to»? | за чверть до повної години |
| `fleng-a1-time-vocabulary-10` | Which English expression means «вчасно»? | on time |

### 5. Places in my town

- **Теорія.** Приклади існування й відмінність від `they` вдалі. Неповне охоплення `there is + незлічуваний` допустиме за явного обмеження теми. Правило some/any в гіді надто категоричне. Розрізнити формулу існування від `there` = «там». У базовому матеріалі 3 приклади, текст на 28 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Назви місць тематичні. `near` і `next to` не взаємозамінні в усіх ситуаціях, але відповіді «біля» й «поруч із» у `check-3` обидві можливі. `post office` — «поштове відділення», `station` потребує уточнення.
- **Завдання.** `check-3` має два природні переклади. `extra-2` допускає щонайменше `There is a station near the park` з тими самими словами, але список знає лише інший розподіл ролей. Дати контекст або прийняти обидва речення.
- **Рішення.** Переписати неоднозначні пункти. Додати короткий опис місцевості й запитання на деталі.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 48 слів, 10 глос мають власні приклади. У 6 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| library | бібліотека | — | База |
| shop | магазин | — | База |
| bank | банк | — | База |
| station | станція | — | База |
| hotel | готель | — | База |
| street | вулиця | — | База |
| park | парк | — | База |
| hospital | лікарня | — | База |
| near | біля | — | База |
| next to | поруч із | — | База |
| bakery | пекарня | — | Доповнення |
| supermarket | супермаркет | — | Доповнення |
| post office | пошта | — | Доповнення |
| bus stop | автобусна зупинка | — | Доповнення |
| playground | дитячий майданчик | — | Доповнення |
| pharmacy | аптека | — | Доповнення |
| police station | відділок поліції | — | Доповнення |
| market | ринок | — | Доповнення |
| sports centre | спортивний центр | — | Доповнення |
| town hall | ратуша | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-town-practice-1` | There ___ a library. | is |
| `fleng-a1-town-practice-2` | There ___ two banks. | are |
| `fleng-a1-town-practice-3` | ___ there a station? | Is |
| `fleng-a1-town-practice-4` | There aren't ___ hotels. | any |
| `fleng-a1-town-practice-5` | There are ___ shops. (positive) | some |
| `fleng-a1-town-check-1` | Choose the Ukrainian meaning of "bank" in this lesson. | банк |
| `fleng-a1-town-check-2` | Choose the Ukrainian meaning of "street" in this lesson. | вулиця |
| `fleng-a1-town-check-3` | Choose the Ukrainian meaning of "near" in this lesson. | біля |
| `fleng-a1-town-extra-1` | There ___ two banks on this street. (is or are?) | are |
| `fleng-a1-town-extra-2` | Put the words in order to make a sentence: a / near / There / station / is / the / park | There is a park near the station |
| `fleng-a1-town-extra-3` | Translate into English: «лікарня» | hospital |
| `fleng-a1-town-extra-4` | Write two sentences about places in your town. Use there is and there are. | There is a library near my home. There are two parks. |
| `fleng-a1-town-vocabulary-1` | What is the Ukrainian translation of «bakery»? | пекарня |
| `fleng-a1-town-vocabulary-2` | Which English expression means «супермаркет»? | supermarket |
| `fleng-a1-town-vocabulary-3` | What is the Ukrainian translation of «post office»? | пошта |
| `fleng-a1-town-vocabulary-4` | Which English expression means «автобусна зупинка»? | bus stop |
| `fleng-a1-town-vocabulary-5` | What is the Ukrainian translation of «playground»? | дитячий майданчик |
| `fleng-a1-town-vocabulary-6` | Which English expression means «аптека»? | pharmacy |
| `fleng-a1-town-vocabulary-7` | What is the Ukrainian translation of «police station»? | відділок поліції |
| `fleng-a1-town-vocabulary-8` | Which English expression means «ринок»? | market |
| `fleng-a1-town-vocabulary-9` | What is the Ukrainian translation of «sports centre»? | спортивний центр |
| `fleng-a1-town-vocabulary-10` | Which English expression means «ратуша»? | town hall |

### 6. Food and simple quantities

- **Теорія.** Ядро countable/uncountable коректне. `a little` є в діалозі без викладу, `I'd like` — без пояснення прагматики. Український гід «для незлічуваних вживаємо одиницю виміру» потребує обмеження «коли називаємо кількість одиницями». У базовому матеріалі 3 приклади, текст на 29 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `cheese` конкретизувати як відповідний продукт у контексті, `loaf` навчати у `a loaf of bread`. `potato` в контексті окремого овочу «картоплина», в загальному «картопля». Додати menu, cup, order як повторення в ситуації.
- **Завдання.** `practice-4` обмежений корисним контекстом `of water`. `extra-4` переносить some/any в нові рамки й потребує явної опори на уроки про have і do/does. Додати мініменю і замовлення, а не лише вибір суфікса.
- **Рішення.** Зберегти граматичний урок. Виділити покупки та замовлення в окремий сценарій.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 41 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| egg | яйце | — | База |
| rice | рис | — | База |
| bread | хліб | — | База |
| water | вода | — | База |
| milk | молоко | — | База |
| cheese | сир | — | База |
| bottle | пляшка | — | База |
| loaf | буханець | — | База |
| potato | картоплина | — | База |
| tomato | помідор | — | База |
| carrot | морква | — | Доповнення |
| onion | цибуля | — | Доповнення |
| cucumber | огірок | — | Доповнення |
| flour | борошно | — | Доповнення |
| sugar | цукор | — | Доповнення |
| salt | сіль | — | Доповнення |
| butter | вершкове масло | — | Доповнення |
| meat | м’ясо | — | Доповнення |
| a slice of | скибка чогось | — | Доповнення |
| a glass of | склянка чогось | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-food-practice-1` | How ___ eggs do we need? | many |
| `fleng-a1-food-practice-2` | How ___ water is there? | much |
| `fleng-a1-food-practice-3` | I'd like ___ rice. | some |
| `fleng-a1-food-practice-4` | Two ___ of water. | bottles |
| `fleng-a1-food-practice-5` | Choose the correct phrase. | a loaf of bread |
| `fleng-a1-food-check-1` | Choose the Ukrainian meaning of "bread" in this lesson. | хліб |
| `fleng-a1-food-check-2` | Choose the Ukrainian meaning of "cheese" in this lesson. | сир |
| `fleng-a1-food-check-3` | Choose the Ukrainian meaning of "potato" in this lesson. | картоплина |
| `fleng-a1-food-extra-1` | How ___ eggs do we need? (much or many?) | many |
| `fleng-a1-food-extra-2` | Put the words in order to make a sentence: much / is / How / there / milk | How much milk is there |
| `fleng-a1-food-extra-3` | Translate into English: «хліб» | bread |
| `fleng-a1-food-extra-4` | Write what is in your kitchen. Use some and any. | We have some rice, but we don't have any cheese. |
| `fleng-a1-food-vocabulary-1` | What is the Ukrainian translation of «carrot»? | морква |
| `fleng-a1-food-vocabulary-2` | Which English expression means «цибуля»? | onion |
| `fleng-a1-food-vocabulary-3` | What is the Ukrainian translation of «cucumber»? | огірок |
| `fleng-a1-food-vocabulary-4` | Which English expression means «борошно»? | flour |
| `fleng-a1-food-vocabulary-5` | What is the Ukrainian translation of «sugar»? | цукор |
| `fleng-a1-food-vocabulary-6` | Which English expression means «сіль»? | salt |
| `fleng-a1-food-vocabulary-7` | What is the Ukrainian translation of «butter»? | вершкове масло |
| `fleng-a1-food-vocabulary-8` | Which English expression means «м’ясо»? | meat |
| `fleng-a1-food-vocabulary-9` | What is the Ukrainian translation of «a slice of»? | скибка чогось |
| `fleng-a1-food-vocabulary-10` | Which English expression means «склянка чогось»? | a glass of |

### 7. What can you do?

- **Теорія.** Стисла й достатня модель ствердження, заперечення, питання та короткої відповіді. Дозвіл і прохання залишити окремими функціями. Українське «Ти вмієш водити?» зрозуміле, точніше «керувати авто». У базовому матеріалі 3 приклади, текст на 21 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Для `drive` потрібен об’єкт або контекст, `play the guitar/piano` і `play chess` утворюють корисний контраст. `fast/well` відповідають темі. `catch/throw` без об’єкта менш інформативні.
- **Завдання.** `extra-2` приймає повну форму `cannot` замість токена `can't`; це допустиме розширення, коли мета граматика, але суперечить буквальному «з поданих слів». `extra-4` збігається з результатом навчання.
- **Рішення.** Зберегти ядро без зміни граматичних правил. Додати завдання на повідомлення про вміння іншої людини.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 30 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| swim | плавати | — | База |
| drive | керувати автомобілем | — | База |
| dance | танцювати | — | База |
| sing | співати | — | База |
| run | бігати | — | База |
| draw | малювати | — | База |
| skill | навичка | — | База |
| guitar | гітара | — | База |
| fast | швидко | — | База |
| well | добре | — | База |
| jump | стрибати | — | Доповнення |
| skate | кататися на ковзанах | — | Доповнення |
| ski | кататися на лижах | — | Доповнення |
| ride a horse | їздити верхи | — | Доповнення |
| whistle | свистіти | — | Доповнення |
| play chess | грати в шахи | — | Доповнення |
| play the piano | грати на піаніно | — | Доповнення |
| catch | ловити | — | Доповнення |
| throw | кидати | — | Доповнення |
| slowly | повільно | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-abilities-practice-1` | She can ___ well. | swim |
| `fleng-a1-abilities-practice-2` | ___ you drive? | Can |
| `fleng-a1-abilities-practice-3` | He ___ sing. (not able) | can't |
| `fleng-a1-abilities-practice-4` | Can you dance? Yes, I ___. | can |
| `fleng-a1-abilities-practice-5` | They can ___ the guitar. | play |
| `fleng-a1-abilities-check-1` | Choose the Ukrainian meaning of "dance" in this lesson. | танцювати |
| `fleng-a1-abilities-check-2` | Choose the Ukrainian meaning of "draw" in this lesson. | малювати |
| `fleng-a1-abilities-check-3` | Choose the Ukrainian meaning of "fast" in this lesson. | швидко |
| `fleng-a1-abilities-extra-1` | I ___ swim, but I can't dance. (positive) | can |
| `fleng-a1-abilities-extra-2` | Put the words in order to make a sentence: drive / My / can't / sister | My sister can't drive / My sister cannot drive |
| `fleng-a1-abilities-extra-3` | Translate into English: «співати» | sing |
| `fleng-a1-abilities-extra-4` | Write two things you can do and one thing you can't do. | I can cook and draw. I can't play the guitar. |
| `fleng-a1-abilities-vocabulary-1` | What is the Ukrainian translation of «jump»? | стрибати |
| `fleng-a1-abilities-vocabulary-2` | Which English expression means «кататися на ковзанах»? | skate |
| `fleng-a1-abilities-vocabulary-3` | What is the Ukrainian translation of «ski»? | кататися на лижах |
| `fleng-a1-abilities-vocabulary-4` | Which English expression means «їздити верхи»? | ride a horse |
| `fleng-a1-abilities-vocabulary-5` | What is the Ukrainian translation of «whistle»? | свистіти |
| `fleng-a1-abilities-vocabulary-6` | Which English expression means «грати в шахи»? | play chess |
| `fleng-a1-abilities-vocabulary-7` | What is the Ukrainian translation of «play the piano»? | грати на піаніно |
| `fleng-a1-abilities-vocabulary-8` | Which English expression means «ловити»? | catch |
| `fleng-a1-abilities-vocabulary-9` | What is the Ukrainian translation of «throw»? | кидати |
| `fleng-a1-abilities-vocabulary-10` | Which English expression means «повільно»? | slowly |

### 8. What is happening now?

- **Теорія.** Основні форми коректні. У чернетковому гіді правило про подвоєння після короткого голосного занадто широке. Показати обмежений шаблон на `run/sit`, порівняти `works every day / is working now`, пояснити, що правило для вже відомих дієслів дії. У базовому матеріалі 3 приклади, текст на 27 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `rain` для учня природніше «йти (про дощ)» або приклад `It is raining — Іде дощ`. `make tea` — «заварювати чай» у контексті. `wear` викладати разом з одягом, принаймні `coat`, `shirt`, `shoes`.
- **Завдання.** `extra-1` приймає `'s` після розділеного `It ___`, хоча на письмі потрібне `It's`. `extra-2` вимагає `wait for`, яке не пояснено. `practice-5` перевіряє питання, якого український гід явно не формулює.
- **Рішення.** Доповнити контраст двох теперішніх часів і прикладами, перевіряти зміст короткої сцени.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 47 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| rain | дощити | — | База |
| sit | сидіти | — | База |
| waiter | офіціант | — | База |
| café | кафе | — | База |
| tea | чай | — | База |
| talk | розмовляти | — | База |
| make | робити | — | База |
| wait | чекати | — | База |
| wear | носити одяг | — | База |
| coat | пальто | — | База |
| serve | подавати страву | — | Доповнення |
| pour | наливати | — | Доповнення |
| order | замовляти | — | Доповнення |
| hold | тримати | — | Доповнення |
| carry | нести | — | Доповнення |
| stand | стояти | — | Доповнення |
| smile | усміхатися | — | Доповнення |
| laugh | сміятися | — | Доповнення |
| pay | платити | — | Доповнення |
| drink | пити | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-right-now-practice-1` | I ___ reading now. | am |
| `fleng-a1-right-now-practice-2` | She is ___ tea. (make) | making |
| `fleng-a1-right-now-practice-3` | They ___ talking. | are |
| `fleng-a1-right-now-practice-4` | He is ___. (run) | running |
| `fleng-a1-right-now-practice-5` | ___ she working now? | Is |
| `fleng-a1-right-now-check-1` | Choose the Ukrainian meaning of "waiter" in this lesson. | офіціант |
| `fleng-a1-right-now-check-2` | Choose the Ukrainian meaning of "talk" in this lesson. | розмовляти |
| `fleng-a1-right-now-check-3` | Choose the Ukrainian meaning of "wear" in this lesson. | носити одяг |
| `fleng-a1-right-now-extra-1` | Look! It ___ raining. (be) | is / 's |
| `fleng-a1-right-now-extra-2` | Put the words in order to make a sentence: are / We / for / waiting / bus / the | We are waiting for the bus |
| `fleng-a1-right-now-extra-3` | Translate into English: «чекати» | wait |
| `fleng-a1-right-now-extra-4` | Write two sentences about what people around you are doing now. | My brother is reading. I am sitting at my desk. |
| `fleng-a1-right-now-vocabulary-1` | What is the Ukrainian translation of «serve»? | подавати страву |
| `fleng-a1-right-now-vocabulary-2` | Which English expression means «наливати»? | pour |
| `fleng-a1-right-now-vocabulary-3` | What is the Ukrainian translation of «order»? | замовляти |
| `fleng-a1-right-now-vocabulary-4` | Which English expression means «тримати»? | hold |
| `fleng-a1-right-now-vocabulary-5` | What is the Ukrainian translation of «carry»? | нести |
| `fleng-a1-right-now-vocabulary-6` | Which English expression means «стояти»? | stand |
| `fleng-a1-right-now-vocabulary-7` | What is the Ukrainian translation of «smile»? | усміхатися |
| `fleng-a1-right-now-vocabulary-8` | Which English expression means «сміятися»? | laugh |
| `fleng-a1-right-now-vocabulary-9` | What is the Ukrainian translation of «pay»? | платити |
| `fleng-a1-right-now-vocabulary-10` | Which English expression means «пити»? | drink |

### 9. Free time and preferences

- **Теорія.** База розрізняє обов’язкове -ing після enjoy та можливе -ing після like/love. Sidecar і пояснення `practice-4` створюють хибне загальне правило. `love to listen` нормативне. Дати парні `but/because` і обмежити урок розмовою про активності. У базовому матеріалі 3 приклади, текст на 27 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `relaxing` краще «той, що допомагає розслабитися», `fun` розділити на «розвага» та «веселий/цікавий» залежно від функції. `camping` природніше «відпочинок у наметі / кемпінг».
- **Завдання.** `practice-5`: `I like cycling, and I don't like running` граматичне й може поєднувати контрастні факти. Позначка `(contrast)` задає цільовий сполучник, але не формулює однозначно «яке слово саме позначає контраст». `extra-4` добре вимірює вживання, потребує критеріїв.
- **Рішення.** Переписати спрощення в гіді. Зберегти урок про хобі, `because` повторити у сценаріях порівняння.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 43 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| cycling | їзда на велосипеді | — | База |
| painting | малювання фарбами | — | База |
| music | музика | — | База |
| shopping | покупки | — | База |
| relaxing | розслаблюючий | — | База |
| tiring | виснажливий | — | База |
| hobby | хобі | — | База |
| film | фільм | — | База |
| game | гра | — | База |
| free time | вільний час | — | База |
| reading | читання | — | Доповнення |
| gardening | садівництво | — | Доповнення |
| singing | спів | — | Доповнення |
| dancing | танці | — | Доповнення |
| photography | фотографія | — | Доповнення |
| camping | відпочинок із наметом | — | Доповнення |
| favourite | улюблений | — | Доповнення |
| boring | нудний | — | Доповнення |
| fun | веселий | — | Доповнення |
| interesting | цікавий | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-likes-practice-1` | I enjoy ___ books. | reading |
| `fleng-a1-likes-practice-2` | She ___ like shopping. (negative) | doesn't |
| `fleng-a1-likes-practice-3` | I like walking ___ it is relaxing. (reason) | because |
| `fleng-a1-likes-practice-4` | He loves ___ to music. | listening |
| `fleng-a1-likes-practice-5` | I like cycling, ___ I don't like running. (contrast) | but |
| `fleng-a1-likes-check-1` | Choose the Ukrainian meaning of "music" in this lesson. | музика |
| `fleng-a1-likes-check-2` | Choose the Ukrainian meaning of "tiring" in this lesson. | виснажливий |
| `fleng-a1-likes-check-3` | Choose the Ukrainian meaning of "game" in this lesson. | гра |
| `fleng-a1-likes-extra-1` | I enjoy ___ to music. (listen) | listening |
| `fleng-a1-likes-extra-2` | Put the words in order to make a sentence: love / They / films / watching | They love watching films |
| `fleng-a1-likes-extra-3` | Translate into English: «гра» | game |
| `fleng-a1-likes-extra-4` | Write about one hobby you like and one activity you don't like. Use -ing. | I love cycling, but I don't like shopping. |
| `fleng-a1-likes-vocabulary-1` | What is the Ukrainian translation of «reading»? | читання |
| `fleng-a1-likes-vocabulary-2` | Which English expression means «садівництво»? | gardening |
| `fleng-a1-likes-vocabulary-3` | What is the Ukrainian translation of «singing»? | спів |
| `fleng-a1-likes-vocabulary-4` | Which English expression means «танці»? | dancing |
| `fleng-a1-likes-vocabulary-5` | What is the Ukrainian translation of «photography»? | фотографія |
| `fleng-a1-likes-vocabulary-6` | Which English expression means «відпочинок із наметом»? | camping |
| `fleng-a1-likes-vocabulary-7` | What is the Ukrainian translation of «favourite»? | улюблений |
| `fleng-a1-likes-vocabulary-8` | Which English expression means «нудний»? | boring |
| `fleng-a1-likes-vocabulary-9` | What is the Ukrainian translation of «fun»? | веселий |
| `fleng-a1-likes-vocabulary-10` | Which English expression means «цікавий»? | interesting |

### 10. Where were you yesterday?

- **Теорія.** Урок добре готує до A2 Past Simple. Є заперечення та питання й явне застереження про `did`. Потрібна таблиця коротких відповідей і контраст `was/were` з базовим `am/is/are`. У базовому матеріалі 3 приклади, текст на 27 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Слова стану/місця й часу доречні. `last night` може бути «учора ввечері» або «минулої ночі» залежно від часу, так і в гіді та словнику. `warm` доречне повторення зі зміною контексту. `crowded` — «людний / переповнений».
- **Завдання.** Основні ключі однозначні в наданих варіантах. `extra-2` не потребує раніше не вивченої форми. `extra-4` корисний перехід до короткої розповіді; дати опору ситуацією, а не лише абстрактною вимогою.
- **Рішення.** Зберегти як місток A1→A2. Розширити вихід із шаблону на власний короткий опис.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 41 слів, 10 глос мають власні приклади. У 6 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| yesterday | вчора | — | База |
| museum | музей | — | База |
| beach | пляж | — | База |
| sunny | сонячний | — | База |
| cloudy | хмарний | — | База |
| last night | минулої ночі | — | База |
| trip | поїздка | — | База |
| weather | погода | — | База |
| busy | зайнятий | — | База |
| quiet | тихий | — | База |
| windy | вітряний | — | Доповнення |
| foggy | туманний | — | Доповнення |
| snowy | сніжний | — | Доповнення |
| warm | теплий | — | Доповнення |
| last week | минулого тижня | — | Доповнення |
| the day before yesterday | позавчора | — | Доповнення |
| zoo | зоопарк | — | Доповнення |
| concert | концерт | — | Доповнення |
| birthday party | вечірка з нагоди дня народження | — | Доповнення |
| crowded | людний | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a1-yesterday-practice-1` | I ___ at the museum yesterday. | was |
| `fleng-a1-yesterday-practice-2` | They ___ at the beach last night. | were |
| `fleng-a1-yesterday-practice-3` | ___ she at home yesterday? | Was |
| `fleng-a1-yesterday-practice-4` | We ___ at school yesterday. (negative) | weren't |
| `fleng-a1-yesterday-practice-5` | Was he busy? No, he ___. | wasn't |
| `fleng-a1-yesterday-check-1` | Choose the Ukrainian meaning of "beach" in this lesson. | пляж |
| `fleng-a1-yesterday-check-2` | Choose the Ukrainian meaning of "last night" in this lesson. | минулої ночі |
| `fleng-a1-yesterday-check-3` | Choose the Ukrainian meaning of "busy" in this lesson. | зайнятий |
| `fleng-a1-yesterday-extra-1` | Yesterday the weather ___ sunny. (be, past) | was |
| `fleng-a1-yesterday-extra-2` | Put the words in order to make a sentence: at / We / beach / were / the | We were at the beach |
| `fleng-a1-yesterday-extra-3` | Translate into English: «вчора» | yesterday |
| `fleng-a1-yesterday-extra-4` | Write two sentences about where you were last weekend. | I was at home on Saturday. On Sunday I was at the museum. |
| `fleng-a1-yesterday-vocabulary-1` | What is the Ukrainian translation of «windy»? | вітряний |
| `fleng-a1-yesterday-vocabulary-2` | Which English expression means «туманний»? | foggy |
| `fleng-a1-yesterday-vocabulary-3` | What is the Ukrainian translation of «snowy»? | сніжний |
| `fleng-a1-yesterday-vocabulary-4` | Which English expression means «теплий»? | warm |
| `fleng-a1-yesterday-vocabulary-5` | What is the Ukrainian translation of «last week»? | минулого тижня |
| `fleng-a1-yesterday-vocabulary-6` | Which English expression means «позавчора»? | the day before yesterday |
| `fleng-a1-yesterday-vocabulary-7` | What is the Ukrainian translation of «zoo»? | зоопарк |
| `fleng-a1-yesterday-vocabulary-8` | Which English expression means «концерт»? | concert |
| `fleng-a1-yesterday-vocabulary-9` | What is the Ukrainian translation of «birthday party»? | вечірка з нагоди дня народження |
| `fleng-a1-yesterday-vocabulary-10` | Which English expression means «людний»? | crowded |

## English Foundations

Окремий seed-курс (`english-foundations`, A1) готує три уроки за порядком нижче. Розділів немає. Рівень за етикеткою A1, фактична тематика значною мірою підготовча. На кожний урок штатне доповнення додає 10 слів із прикладами та 7 вправ до 3 seed-вправ. Разом 30 слів, 30 вправ (3 `single_choice`, 21 `text`, 6 `self_check`), 3 перші проходи. Окремого тесту курсу немає. Правила завершення спільні з основною серією. Seed виконується на порожньому каталозі, тому фактичну наявність у вже створеній БД не перевірено.

### 1. Greetings and introductions

- **Slug.** `greetings-and-introductions`.
- **Теорія.** Формули знайомства й прощання подано вдало, з регістром та кількома прикладами. Української теорії, таблиці й короткого зв’язаного діалогу немає.
- **Словник.** Список із десяти слів має приклади, але `meet` потребує поділу «зустрічати» і «знайомитися», `nice` у `Nice to meet you` працює як частина формули. Збіги з A0 становлять корисне повторення лише за новим контекстом.
- **Завдання.** q2 добре приймає `you too/likewise`. `extra-6` відхиляє `Hi, I'm Sam`, хоча урок сам учить цей шаблон. Уточнити вимогу `My name is` або доповнити відповіді. `extra-4` дублює послідовність слів з основного A0.
- **Рішення.** Зберегти як короткий повтор або додаткову практику. У головній програмі об’єднати зміст із A0-знайомством.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| hello | привіт; добрий день | Hello, my name is Alex. | Seed-доповнення |
| goodbye | до побачення | Goodbye. See you tomorrow. | Seed-доповнення |
| please | будь ласка | Please sit down. | Seed-доповнення |
| thank you | дякую | Thank you for your help. | Seed-доповнення |
| sorry | вибачте | Sorry, I am late. | Seed-доповнення |
| name | ім'я | What is your name? | Seed-доповнення |
| nice | приємний | Nice to meet you. | Seed-доповнення |
| meet | зустрічати; знайомитися | I meet my friends on Friday. | Seed-доповнення |
| morning | ранок | Good morning, Mrs Brown. | Seed-доповнення |
| friend | друг; подруга | Sam is my friend. | Seed-доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `greetings-and-introductions-q1` | Complete the greeting: '___, my name is Alex.' | Hello |
| `greetings-and-introductions-q2` | How do you usually reply to 'Nice to meet you'? | nice to meet you too / nice to meet you as well / it's nice to meet you too / pleased to meet you too / nice meeting you too / you too / likewise |
| `greetings-and-introductions-q3` | Write a greeting you would use in the morning. | Good morning! |
| `greetings-and-introductions-extra-1` | ___ morning, Mrs Brown. (a polite word for the start of the day) | good |
| `greetings-and-introductions-extra-2` | Nice to ___ you. (the verb for the first time you see someone) | meet |
| `greetings-and-introductions-extra-3` | Put the words in order to make a sentence: name / is / My / Alex | My name is Alex |
| `greetings-and-introductions-extra-4` | Put the words in order to make a sentence: you / Nice / meet / to | Nice to meet you |
| `greetings-and-introductions-extra-5` | Translate into English: «до побачення» | goodbye / bye |
| `greetings-and-introductions-extra-6` | Translate into English: «Привіт, мене звати Сем.» | hello, my name is sam / hi, my name is sam |
| `greetings-and-introductions-extra-7` | Introduce yourself in two short sentences. | Hello, my name is Anna. Nice to meet you. |

### 2. The verb "to be"

- **Slug.** `the-verb-to-be`.
- **Теорія.** Добрі зразки am/is/are, усіх ствердних скорочень, заперечення й інверсії. Бракує таблиці та коротких відповідей. Українська теорія відсутня.
- **Словник.** `am/is/are` у перекладі як «є» потребують застереження про нульову зв’язку українською. `late` показати у фразі `I am late — Я запізнився/запізнилася`. Приклади є в усіх 10 записах.
- **Завдання.** q2 приймає орфографічно неправильне `im` для цільової вправи на скорочення; `extra-5/6` приймають `im tired` і `theyre at home`. Це свідомі варіанти списку, а не дія нормалізатора. Потрібно пояснити, коли апостроф оцінюється.
- **Рішення.** У навчальній лінії перенести ядро до A0 і зберегти seed-урок для чинних історій.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| am | є (з «I») | I am a student. | Seed-доповнення |
| is | є (з he, she, it) | She is from Spain. | Seed-доповнення |
| are | є (з you, we, they) | We are ready. | Seed-доповнення |
| student | студент; учень | I am a student. | Seed-доповнення |
| teacher | вчитель | He is a teacher. | Seed-доповнення |
| from | з; родом з | She is from Spain. | Seed-доповнення |
| ready | готовий | We are ready. | Seed-доповнення |
| tired | втомлений | I'm tired. | Seed-доповнення |
| late | запізнілий; пізно | I am not late. | Seed-доповнення |
| home | дім; вдома | They're at home. | Seed-доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `the-verb-to-be-q1` | She ___ from Spain. | is |
| `the-verb-to-be-q2` | Write the short form of 'I am'. | i'm / im |
| `the-verb-to-be-q3` | Write one sentence about yourself using 'to be'. | I am a student. |
| `the-verb-to-be-extra-1` | I ___ a student. (the form of «to be» for I) | am |
| `the-verb-to-be-extra-2` | They ___ at home. (the form of «to be» for they) | are |
| `the-verb-to-be-extra-3` | Put the words in order to make a sentence: she / from / is / Spain | She is from Spain |
| `the-verb-to-be-extra-4` | Put the words in order to make a sentence: you / Are / ready | Are you ready |
| `the-verb-to-be-extra-5` | Translate into English: «Я втомлений.» | i am tired / i'm tired / im tired |
| `the-verb-to-be-extra-6` | Translate into English: «Вони вдома.» | they are at home / they're at home / theyre at home |
| `the-verb-to-be-extra-7` | Write two sentences about yourself with am: your name and your job or study. | I am Anna. I am a student. |

### 3. Numbers, days and dates

- **Slug.** `numbers-and-days`.
- **Теорія.** Блок надто широкий для 12 хвилин. Є всі дні, але число 0 і значна частина 1–20 відсутні в таблиці, 21–99 поза десятками, місяці лише в прикладах. Пояснення про BrE/AmE узагальнює типовий формат і не описує варіативність.
- **Словник.** 10 слів мають приклади, але лише три дні, немає жодного місяця та порядкових числівників як словникових одиниць. Потрібні `first/second/third`, повні календарні опори та регулярне закінчення в складених датах.
- **Завдання.** q2 і `extra-1` обидва ведуть до `twelve`. `extra-6` не вимагає великої літери попри пояснення, бо перевірка ігнорує регістр. `extra-7` має фіксовану дату в моделі без пояснення, що це лише приклад.
- **Рішення.** Розділити числа, дні/місяці й дати. Підтягнути числа в A0, застосування розкладу в A1.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| one | один | I have one book. | Seed-доповнення |
| two | два | We have two cats. | Seed-доповнення |
| ten | десять | Ten students are here. | Seed-доповнення |
| twelve | дванадцять | There are twelve months in a year. | Seed-доповнення |
| twenty | двадцять | I am twenty years old. | Seed-доповнення |
| Monday | понеділок | The lesson is on Monday. | Seed-доповнення |
| Friday | п'ятниця | The meeting is on Friday. | Seed-доповнення |
| Sunday | неділя | We rest on Sunday. | Seed-доповнення |
| week | тиждень | There are seven days in a week. | Seed-доповнення |
| date | дата | What is the date today? | Seed-доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `numbers-and-days-q1` | Which day comes after Tuesday? | Wednesday |
| `numbers-and-days-q2` | Write the number 12 as a word. | twelve |
| `numbers-and-days-q3` | Write a date in English, for example your birthday. | My birthday is on the eleventh of October. |
| `numbers-and-days-extra-1` | Ten and two is ___. (write the number as a word) | twelve |
| `numbers-and-days-extra-2` | The day after Friday is ___. | saturday |
| `numbers-and-days-extra-3` | Put the words in order to make a sentence: meeting / The / is / on / Friday | The meeting is on Friday |
| `numbers-and-days-extra-4` | Put the words in order to make a sentence: birthday / is / My / on / the / first / of / June | My birthday is on the first of June |
| `numbers-and-days-extra-5` | Translate into English: «двадцять» | twenty |
| `numbers-and-days-extra-6` | Translate into English: «понеділок» | monday |
| `numbers-and-days-extra-7` | Write today's date and the day of the week in English. | Today is Monday, the eleventh of October. |

## Підсумок рівня

Детальні критерії пріоритету, повтори лексики й наскрізні проблеми наведено у [реєстрі проблем](06_PROBLEMS.md). Рекомендований порядок і цілі кожного майбутнього уроку подано в [новій програмі](07_NEW_CURRICULUM.md).
