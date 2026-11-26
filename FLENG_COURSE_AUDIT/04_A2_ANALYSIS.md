# Аудит A2 — Elementary

## Структура і статус

Курс **A2 — Elementary** (`fleng-a2`) має 10 уроків. Розділи в моделі й каталозі відсутні, уроки належать напряму курсу. Нижче подано порядок `position`, який збігається з ланцюжком `prerequisites` у джерелі. Перший урок спирається на `fleng-a1-yesterday`. Передумови описують авторську послідовність. Каталог відкриває опублікований урок за прямим URL.

- 100 базових і 100 додаткових словникових записів. У цих 200 записів поле `example` порожнє. Приклади є в теорії. Поля транскрипції у джерелі та БД немає.
- 220 вправ: 50 основних тренувальних, 30 базових перевірок лексики, 40 форматів додаткової практики і 100 згенерованих перевірок перекладу. За механізмом 180 `single_choice`, 30 `text`, 10 `self_check`.
- 10 доступних перших проходів тесту уроку. Незалежних контрольних тестів курсу — 0. За редакційними категоріями 90 тренувальних і 130 перевірочних пунктів, але плеєр запускає спільну послідовність із 22 завдань.
- Перший прохід закінчується після однієї відповіді або пропуску кожного пункту. Для повного завершення уроку потрібен правильний стан усіх 22 вправ, у тому числі підтверджена учнем самоперевірка. Курс завершено після всіх опублікованих уроків. [Технічні деталі](01_ARCHITECTURE.md).


| № | Урок | Slug | Тема |
| --- | --- | --- | --- |
| 1 | A weekend story | `fleng-a2-past-actions` | Розповідь у Past Simple |
| 2 | Choosing a place to stay | `fleng-a2-comparisons` | Порівняння житла |
| 3 | Plans and arrangements | `fleng-a2-plans` | Наміри й домовленості |
| 4 | Experiences and recent results | `fleng-a2-experiences` | Досвід і недавній результат |
| 5 | Health and practical advice | `fleng-a2-health` | Поради, обов’язок і заборона |
| 6 | Getting around a new city | `fleng-a2-directions` | Вказівки в місті |
| 7 | When the phone rang | `fleng-a2-background` | Минулий процес і подія |
| 8 | If the weather changes | `fleng-a2-conditions` | Умова і майбутній час |
| 9 | Which person do you mean? | `fleng-a2-descriptions` | Уточнення особи, речі або місця |
| 10 | Solving a travel problem | `fleng-a2-travel-problem` | Проблема під час подорожі |

## Аналіз усіх десяти уроків

### 1. A weekend story

- **Теорія.** Сильний перехід від `was/were` до дій. Є правильні й неправильні форми, `did/didn't`, маркери послідовності. Чотири нові операції одночасно, потрібне розділення на твердження та питання. Навчати `met`, `left`, `spent` до використання в тексті або дати глоси. У базовому матеріалі 3 приклади, текст на 39 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `leave` має значення «піти/виїхати» в історії, «залишати» в іншій конструкції. `stall` тут «ринковий прилавок / ятка», `vendor` може бути рецептивним. `market` доречно повертається з A1.
- **Завдання.** `extra-2` вже визнає два порядки `late`, це добрий зразок роботи з варіантністю, хоча формула у поясненні допускає лише місце перед часом. Власна історія доречна. Додати фактичні запитання до прочитаного.
- **Рішення.** Розділити виклад і зберегти сюжет ринку.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 58 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| market | ринок | — | База |
| vegetable | овоч | — | База |
| visit | відвідувати | — | База |
| buy | купувати | — | База |
| spend | витрачати | — | База |
| arrive | прибувати | — | База |
| leave | залишати | — | База |
| finally | нарешті | — | База |
| ticket | квиток | — | База |
| journey | подорож | — | База |
| stall | торговий кіоск | — | Доповнення |
| vendor | продавець на ринку | — | Доповнення |
| cash | готівка | — | Доповнення |
| change | решта | — | Доповнення |
| shopping list | список покупок | — | Доповнення |
| pick up | забирати когось або щось | — | Доповнення |
| miss the bus | запізнитися на автобус | — | Доповнення |
| get back | повертатися | — | Доповнення |
| a few hours later | через кілька годин | — | Доповнення |
| on the way | дорогою | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-past-actions-practice-1` | Yesterday she ___ vegetables. (buy) | bought |
| `fleng-a2-past-actions-practice-2` | Did he ___ the market? | visit |
| `fleng-a2-past-actions-practice-3` | We didn't ___ the bus. | take |
| `fleng-a2-past-actions-practice-4` | Last weekend they ___ home. (walk) | walked |
| `fleng-a2-past-actions-practice-5` | I ___ lunch at noon yesterday. (eat) | ate |
| `fleng-a2-past-actions-check-1` | Choose the Ukrainian meaning of "visit" in this lesson. | відвідувати |
| `fleng-a2-past-actions-check-2` | Choose the Ukrainian meaning of "arrive" in this lesson. | прибувати |
| `fleng-a2-past-actions-check-3` | Choose the Ukrainian meaning of "ticket" in this lesson. | квиток |
| `fleng-a2-past-actions-extra-1` | Last week I ___ a new jacket. (buy, past) | bought |
| `fleng-a2-past-actions-extra-2` | Put the words in order to make a sentence: arrived / We / late / at / the / station | We arrived at the station late / We arrived late at the station |
| `fleng-a2-past-actions-extra-3` | Translate into English: «квиток» | ticket |
| `fleng-a2-past-actions-extra-4` | Write three sentences about your last trip. Use the past simple. | I visited Lviv. I bought some souvenirs. We left on Sunday. |
| `fleng-a2-past-actions-vocabulary-1` | What is the Ukrainian translation of «stall»? | торговий кіоск |
| `fleng-a2-past-actions-vocabulary-2` | Which English expression means «продавець на ринку»? | vendor |
| `fleng-a2-past-actions-vocabulary-3` | What is the Ukrainian translation of «cash»? | готівка |
| `fleng-a2-past-actions-vocabulary-4` | Which English expression means «решта»? | change |
| `fleng-a2-past-actions-vocabulary-5` | What is the Ukrainian translation of «shopping list»? | список покупок |
| `fleng-a2-past-actions-vocabulary-6` | Which English expression means «забирати когось або щось»? | pick up |
| `fleng-a2-past-actions-vocabulary-7` | What is the Ukrainian translation of «miss the bus»? | запізнитися на автобус |
| `fleng-a2-past-actions-vocabulary-8` | Which English expression means «повертатися»? | get back |
| `fleng-a2-past-actions-vocabulary-9` | What is the Ukrainian translation of «a few hours later»? | через кілька годин |
| `fleng-a2-past-actions-vocabulary-10` | Which English expression means «дорогою»? | on the way |

### 2. Choosing a place to stay

- **Теорія.** Правило придатне як прототип. Відсутні `bad → worse/worst`, написання `big → bigger` і `noisy → noisier`, хоча `bigger` є в моделі і `noisy` у словнику. `ours/that one` ввести як опору або замінити знайомими формами. У базовому матеріалі 3 приклади, текст на 39 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `apartment` достатньо перекласти «квартира», `comfortable` — «комфортний», `convenient` — «зручний» у контексті розташування. `guesthouse`, `per night`, `included` мають практичну цінність із прикладом оголошення.
- **Завдання.** `extra-4` просить порівняти два місця і вжити найвищий ступінь. Зразок вводить flat, room і hotel та не задає групу. Дати картки трьох об’єктів та критерії ціни, місця й зручності.
- **Рішення.** Розділити вправи на порівняння двох і вибір із трьох.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 56 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| hostel | хостел | — | База |
| apartment | квартира для проживання | — | База |
| cheap | дешевий | — | База |
| expensive | дорогий | — | База |
| comfortable | зручний | — | База |
| price | ціна | — | База |
| clean | чистий | — | База |
| safe | безпечний | — | База |
| distance | відстань | — | База |
| choice | вибір | — | База |
| guesthouse | гостьовий будинок | — | Доповнення |
| shared room | спільна кімната | — | Доповнення |
| private bathroom | окрема ванна кімната | — | Доповнення |
| included | включений у вартість | — | Доповнення |
| convenient | зручний | — | Доповнення |
| spacious | просторий | — | Доповнення |
| central | розташований у центрі | — | Доповнення |
| noisy | галасливий | — | Доповнення |
| overnight stay | ночівля | — | Доповнення |
| per night | за ніч | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-comparisons-practice-1` | This hostel is ___ than that hotel. (cheap) | cheaper |
| `fleng-a2-comparisons-practice-2` | Of these three, this room is the ___. (small) | smallest |
| `fleng-a2-comparisons-practice-3` | This bed is ___ comfortable than that one. | more |
| `fleng-a2-comparisons-practice-4` | This kitchen is ___ than ours. (good) | better |
| `fleng-a2-comparisons-practice-5` | It is the ___ expensive hotel of the three. | most |
| `fleng-a2-comparisons-check-1` | Choose the Ukrainian meaning of "cheap" in this lesson. | дешевий |
| `fleng-a2-comparisons-check-2` | Choose the Ukrainian meaning of "price" in this lesson. | ціна |
| `fleng-a2-comparisons-check-3` | Choose the Ukrainian meaning of "distance" in this lesson. | відстань |
| `fleng-a2-comparisons-extra-1` | The hostel is ___ than the hotel. (cheap) | cheaper |
| `fleng-a2-comparisons-extra-2` | Put the words in order to make a sentence: is / most / This / the / comfortable / room | This is the most comfortable room |
| `fleng-a2-comparisons-extra-3` | Translate into English: «ціна» | price |
| `fleng-a2-comparisons-extra-4` | Compare two places to stay. Use a comparative and a superlative. | The flat is bigger than the room. The hotel is the most expensive. |
| `fleng-a2-comparisons-vocabulary-1` | What is the Ukrainian translation of «guesthouse»? | гостьовий будинок |
| `fleng-a2-comparisons-vocabulary-2` | Which English expression means «спільна кімната»? | shared room |
| `fleng-a2-comparisons-vocabulary-3` | What is the Ukrainian translation of «private bathroom»? | окрема ванна кімната |
| `fleng-a2-comparisons-vocabulary-4` | Which English expression means «включений у вартість»? | included |
| `fleng-a2-comparisons-vocabulary-5` | What is the Ukrainian translation of «convenient»? | зручний |
| `fleng-a2-comparisons-vocabulary-6` | Which English expression means «просторий»? | spacious |
| `fleng-a2-comparisons-vocabulary-7` | What is the Ukrainian translation of «central»? | розташований у центрі |
| `fleng-a2-comparisons-vocabulary-8` | Which English expression means «галасливий»? | noisy |
| `fleng-a2-comparisons-vocabulary-9` | What is the Ukrainian translation of «overnight stay»? | ночівля |
| `fleng-a2-comparisons-vocabulary-10` | Which English expression means «за ніч»? | per night |

### 3. Plans and arrangements

- **Теорія.** Вдале уточнення, що обидві форми іноді можливі. До прогнозу `going to` додати окремий приклад і відкласти змішування прогнозу/наміру/домовленості в одному контрольному блоці. Потрібний вступ до `will` перед умовними реченнями. У базовому матеріалі 3 приклади, текст на 42 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `book/reserve` мають однаковий переклад у цьому уроці. Подати колокації й контекст. `sail` для цього рівня природніше «плавати під вітрилом». `look forward to` потребує зразка на керування, його варто зробити рецептивним.
- **Завдання.** MC явно задають потрібну форму, тому наведені ключі коректні в межах варіантів, але мало перевіряють вибір форми за наміром. `extra-2` приймає `We are` замість `We're` попри токени. Дати діалог із календарем, де мета — домовитись.
- **Рішення.** Зберегти зіставлення, виділити плани й домовленості в різні етапи.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 62 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| arrangement | домовленість | — | База |
| plan | план | — | База |
| summer | літо | — | База |
| instructor | інструктор | — | База |
| book | бронювати | — | База |
| sail | ходити під вітрилом | — | База |
| tomorrow | завтра | — | База |
| cloud | хмара | — | База |
| intention | намір | — | База |
| calendar | календар | — | База |
| reserve | бронювати | — | Доповнення |
| sign up | записуватися | — | Доповнення |
| invite | запрошувати | — | Доповнення |
| prepare | готуватися | — | Доповнення |
| pack | пакувати речі | — | Доповнення |
| this weekend | цими вихідними | — | Доповнення |
| next month | наступного місяця | — | Доповнення |
| in advance | заздалегідь | — | Доповнення |
| meet up | зустрічатися | — | Доповнення |
| look forward to | з нетерпінням чекати | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-plans-practice-1` | Use going to: I ___ going to learn to sail. | am |
| `fleng-a2-plans-practice-2` | Use going to: She is going to ___ a room. | book |
| `fleng-a2-plans-practice-3` | Use present continuous: We are ___ the instructor tomorrow. | meeting |
| `fleng-a2-plans-practice-4` | Look at the clouds. It ___ going to rain. | is |
| `fleng-a2-plans-practice-5` | Use present continuous: He ___ leaving at six tomorrow. | is |
| `fleng-a2-plans-check-1` | Choose the Ukrainian meaning of "summer" in this lesson. | літо |
| `fleng-a2-plans-check-2` | Choose the Ukrainian meaning of "sail" in this lesson. | ходити під вітрилом |
| `fleng-a2-plans-check-3` | Choose the Ukrainian meaning of "intention" in this lesson. | намір |
| `fleng-a2-plans-extra-1` | I'm ___ to learn to sail this summer. (plan) | going |
| `fleng-a2-plans-extra-2` | Put the words in order to make a sentence: meeting / We're / tomorrow / the / instructor | We're meeting the instructor tomorrow / We are meeting the instructor tomorrow |
| `fleng-a2-plans-extra-3` | Translate into English: «завтра» | tomorrow |
| `fleng-a2-plans-extra-4` | Write one plan with going to and one arrangement with the present continuous. | I'm going to study more. I'm seeing my friend on Friday. |
| `fleng-a2-plans-vocabulary-1` | What is the Ukrainian translation of «reserve»? | бронювати |
| `fleng-a2-plans-vocabulary-2` | Which English expression means «записуватися»? | sign up |
| `fleng-a2-plans-vocabulary-3` | What is the Ukrainian translation of «invite»? | запрошувати |
| `fleng-a2-plans-vocabulary-4` | Which English expression means «готуватися»? | prepare |
| `fleng-a2-plans-vocabulary-5` | What is the Ukrainian translation of «pack»? | пакувати речі |
| `fleng-a2-plans-vocabulary-6` | Which English expression means «цими вихідними»? | this weekend |
| `fleng-a2-plans-vocabulary-7` | What is the Ukrainian translation of «next month»? | наступного місяця |
| `fleng-a2-plans-vocabulary-8` | Which English expression means «заздалегідь»? | in advance |
| `fleng-a2-plans-vocabulary-9` | What is the Ukrainian translation of «meet up»? | зустрічатися |
| `fleng-a2-plans-vocabulary-10` | Which English expression means «з нетерпінням чекати»? | look forward to |

### 4. Experiences and recent results

- **Теорія.** Зіставлення з yesterday правильне. Потрібно поділити досвід і `already/yet`, додати ланцюжки `see/saw/seen`, `try/tried/tried` і модель короткої відповіді `Yes, I have`. Вказати, що форму визначають часова рамка й комунікативна мета. У базовому матеріалі 3 приклади, текст на 38 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `yet` має різні переклади залежно від питання або заперечення, `ever` — «коли-небудь» у питанні, `so far` природніше «поки що / до цього моменту». Слова `safety harness`, `equipment`, `achievement` відволікають від повсякденного досвіду.
- **Завдання.** `practice-3` має природний цільовий `yet`; `already` у запереченні можливе в спеціальному контексті, якого завдання не задає. Обмежити вимогу «ще не». `extra-4` не оцінює перехід до Past Simple для подробиць.
- **Рішення.** Розділити на два уроки, замінити вузькоспеціалізований сюжет побутовим.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 48 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| climbing | скелелазіння | — | База |
| experience | досвід | — | База |
| already | вже | — | База |
| yet | ще | — | База |
| ever | коли-небудь | — | База |
| indoors | у приміщенні | — | База |
| session | заняття | — | База |
| finish | закінчувати | — | База |
| try | пробувати | — | База |
| recently | нещодавно | — | База |
| take part | брати участь | — | Доповнення |
| achievement | досягнення | — | Доповнення |
| challenge | випробування | — | Доповнення |
| beginner | початківець | — | Доповнення |
| outdoors | просто неба | — | Доповнення |
| equipment | спорядження | — | Доповнення |
| helmet | шолом | — | Доповнення |
| safety harness | страхувальна система | — | Доповнення |
| manage to | зуміти | — | Доповнення |
| so far | дотепер | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-experiences-practice-1` | Have you ever ___ a mountain? (see) | seen |
| `fleng-a2-experiences-practice-2` | She ___ already finished. | has |
| `fleng-a2-experiences-practice-3` | I haven't booked a session ___. | yet |
| `fleng-a2-experiences-practice-4` | I ___ it yesterday. (try) | tried |
| `fleng-a2-experiences-practice-5` | He has ___ climbed indoors. (at no time) | never |
| `fleng-a2-experiences-check-1` | Choose the Ukrainian meaning of "already" in this lesson. | вже |
| `fleng-a2-experiences-check-2` | Choose the Ukrainian meaning of "indoors" in this lesson. | у приміщенні |
| `fleng-a2-experiences-check-3` | Choose the Ukrainian meaning of "try" in this lesson. | пробувати |
| `fleng-a2-experiences-extra-1` | Have you ___ tried climbing? (at any time) | ever |
| `fleng-a2-experiences-extra-2` | Put the words in order to make a sentence: finished / already / I've / the / session | I've already finished the session / I have already finished the session |
| `fleng-a2-experiences-extra-3` | Translate into English: «досвід» | experience |
| `fleng-a2-experiences-extra-4` | Write one thing you have done and one thing you have never done. | I have visited Kyiv. I have never tried climbing. |
| `fleng-a2-experiences-vocabulary-1` | What is the Ukrainian translation of «take part»? | брати участь |
| `fleng-a2-experiences-vocabulary-2` | Which English expression means «досягнення»? | achievement |
| `fleng-a2-experiences-vocabulary-3` | What is the Ukrainian translation of «challenge»? | випробування |
| `fleng-a2-experiences-vocabulary-4` | Which English expression means «початківець»? | beginner |
| `fleng-a2-experiences-vocabulary-5` | What is the Ukrainian translation of «outdoors»? | просто неба |
| `fleng-a2-experiences-vocabulary-6` | Which English expression means «спорядження»? | equipment |
| `fleng-a2-experiences-vocabulary-7` | What is the Ukrainian translation of «helmet»? | шолом |
| `fleng-a2-experiences-vocabulary-8` | Which English expression means «страхувальна система»? | safety harness |
| `fleng-a2-experiences-vocabulary-9` | What is the Ukrainian translation of «manage to»? | зуміти |
| `fleng-a2-experiences-vocabulary-10` | Which English expression means «дотепер»? | so far |

### 5. Health and practical advice

- **Теорія.** Сильне зіставлення `mustn't` і `don't have to`. Пояснити також `has to`, `Do I have to…?`, і відрізняти правило від дружньої поради. Винести обов’язок у сценарій правил установи, консультацію залишити як мовну роль. У базовому матеріалі 3 приклади, текст на 37 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `unwell` як «нездужий» зрозуміле, але `I feel unwell — Мені зле` доступніше. `dizzy` краще через «У мене паморочиться голова». `take a day off` — «взяти вихідний»; `dose/prescription` лишити рецептивними.
- **Завдання.** `extra-1` і `extra-4` оцінюють форму `should` у пораді. Для змісту краще нейтральний сценарій `Could I make an appointment?`; завдання з обов’язком краще оцінювати через однозначний напис/правило.
- **Рішення.** Зберегти модальний контраст. Розділити звернення по допомогу та правила.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 56 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| headache | головний біль | — | База |
| symptom | симптом | — | База |
| appointment | запис на прийом | — | База |
| pharmacist | фармацевт | — | База |
| rest | відпочинок | — | База |
| advice | порада | — | База |
| obligation | обов’язок | — | База |
| necessary | необхідний | — | База |
| prohibited | заборонений | — | База |
| unwell | нездужий | — | База |
| sore throat | біль у горлі | — | Доповнення |
| fever | підвищена температура | — | Доповнення |
| cough | кашель | — | Доповнення |
| dizzy | із запамороченням | — | Доповнення |
| medicine | ліки | — | Доповнення |
| prescription | рецепт лікаря | — | Доповнення |
| dose | доза | — | Доповнення |
| recover | одужувати | — | Доповнення |
| lie down | прилягти | — | Доповнення |
| take a day off | взяти вихідний | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-health-practice-1` | For advice: You ___ speak to a professional. | should |
| `fleng-a2-health-practice-2` | It is prohibited: You ___ smoke here. | mustn't |
| `fleng-a2-health-practice-3` | It is not necessary: You ___ book in advance. | don't have to |
| `fleng-a2-health-practice-4` | She ___ to wear a uniform at work. | has |
| `fleng-a2-health-practice-5` | You should ___ the notice. | read |
| `fleng-a2-health-check-1` | Choose the Ukrainian meaning of "appointment" in this lesson. | запис на прийом |
| `fleng-a2-health-check-2` | Choose the Ukrainian meaning of "advice" in this lesson. | порада |
| `fleng-a2-health-check-3` | Choose the Ukrainian meaning of "prohibited" in this lesson. | заборонений |
| `fleng-a2-health-extra-1` | You have a headache. You ___ rest. (advice) | should |
| `fleng-a2-health-extra-2` | Put the words in order to make a sentence: wear / You / a / must / helmet | You must wear a helmet |
| `fleng-a2-health-extra-3` | Translate into English: «порада» | advice |
| `fleng-a2-health-extra-4` | Give a friend with a cold two pieces of advice. Use should. | You should rest. You should drink warm tea. |
| `fleng-a2-health-vocabulary-1` | What is the Ukrainian translation of «sore throat»? | біль у горлі |
| `fleng-a2-health-vocabulary-2` | Which English expression means «підвищена температура»? | fever |
| `fleng-a2-health-vocabulary-3` | What is the Ukrainian translation of «cough»? | кашель |
| `fleng-a2-health-vocabulary-4` | Which English expression means «із запамороченням»? | dizzy |
| `fleng-a2-health-vocabulary-5` | What is the Ukrainian translation of «medicine»? | ліки |
| `fleng-a2-health-vocabulary-6` | Which English expression means «рецепт лікаря»? | prescription |
| `fleng-a2-health-vocabulary-7` | What is the Ukrainian translation of «dose»? | доза |
| `fleng-a2-health-vocabulary-8` | Which English expression means «одужувати»? | recover |
| `fleng-a2-health-vocabulary-9` | What is the Ukrainian translation of «lie down»? | прилягти |
| `fleng-a2-health-vocabulary-10` | Which English expression means «взяти вихідний»? | take a day off |

### 6. Getting around a new city

- **Теорія.** Коректні `along/across/past` з протиставленням. Потрібні `left/right`, прохання повторити і проста текстова схема маршруту. Додати базові напрямки раніше, поглибити рух тут. У базовому матеріалі 3 приклади, текст на 42 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `landmark`, `roundabout`, `pavement`, `alley` можуть бути рецептивними. `traffic lights` у контексті «світлофор», `go past` — «пройти/проїхати повз». `on your left` має відповідати вибраному тону «ліворуч від тебе/вас».
- **Завдання.** `practice-5` обирає `on` серед явно слабких варіантів. `extra-1` подає «через» з напрямом на інший бік, а природний `over` відхиляється. Уточнити конкретний прийменник або дозволити `over`, якщо завдання про зміст.
- **Рішення.** Зберегти як практичну тему. Перенести відразу після місць у місті або повторити з A1.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 42 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| bridge | міст | — | База |
| square | площа | — | База |
| cinema | кінотеатр | — | База |
| opposite | навпроти | — | База |
| straight | прямо | — | База |
| turn | повертати | — | База |
| cross | перетинати | — | База |
| along | уздовж | — | База |
| across | через | — | База |
| landmark | орієнтир | — | База |
| roundabout | кільцева розв’язка | — | Доповнення |
| pedestrian crossing | пішохідний перехід | — | Доповнення |
| traffic lights | світлофор | — | Доповнення |
| pavement | тротуар | — | Доповнення |
| alley | вузький провулок | — | Доповнення |
| go past | пройти повз | — | Доповнення |
| follow the signs | іти за вказівниками | — | Доповнення |
| on your left | ліворуч від вас | — | Доповнення |
| at the end of | у кінці | — | Доповнення |
| get lost | заблукати | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-directions-practice-1` | Follow this road: walk ___ it. | along |
| `fleng-a2-directions-practice-2` | From one side of the square to the other: go ___ it. | across |
| `fleng-a2-directions-practice-3` | ___ left at the cinema. | Turn |
| `fleng-a2-directions-practice-4` | Continue beyond the bank: walk ___ it. | past |
| `fleng-a2-directions-practice-5` | Do not turn: go straight ___. | on |
| `fleng-a2-directions-check-1` | Choose the Ukrainian meaning of "cinema" in this lesson. | кінотеатр |
| `fleng-a2-directions-check-2` | Choose the Ukrainian meaning of "turn" in this lesson. | повертати |
| `fleng-a2-directions-check-3` | Choose the Ukrainian meaning of "across" in this lesson. | через |
| `fleng-a2-directions-extra-1` | Go ___ the bridge to the other side. (через) | across |
| `fleng-a2-directions-extra-2` | Put the words in order to make a sentence: left / Turn / the / at / cinema | Turn left at the cinema |
| `fleng-a2-directions-extra-3` | Translate into English: «міст» | bridge |
| `fleng-a2-directions-extra-4` | Explain how to get from your home to a shop. Use two directions. | Go straight along the street. Turn right at the bank. |
| `fleng-a2-directions-vocabulary-1` | What is the Ukrainian translation of «roundabout»? | кільцева розв’язка |
| `fleng-a2-directions-vocabulary-2` | Which English expression means «пішохідний перехід»? | pedestrian crossing |
| `fleng-a2-directions-vocabulary-3` | What is the Ukrainian translation of «traffic lights»? | світлофор |
| `fleng-a2-directions-vocabulary-4` | Which English expression means «тротуар»? | pavement |
| `fleng-a2-directions-vocabulary-5` | What is the Ukrainian translation of «alley»? | вузький провулок |
| `fleng-a2-directions-vocabulary-6` | Which English expression means «пройти повз»? | go past |
| `fleng-a2-directions-vocabulary-7` | What is the Ukrainian translation of «follow the signs»? | іти за вказівниками |
| `fleng-a2-directions-vocabulary-8` | Which English expression means «ліворуч від вас»? | on your left |
| `fleng-a2-directions-vocabulary-9` | What is the Ukrainian translation of «at the end of»? | у кінці |
| `fleng-a2-directions-vocabulary-10` | Which English expression means «заблукати»? | get lost |

### 7. When the phone rang

- **Теорія.** Добре застереження, що when/while не визначають час автоматично. Відсутні паралельні процеси й наочна часовá вісь. Пояснити відмінність між подією всередині процесу та паралельними процесами. У базовому матеріалі 3 приклади, текст на 38 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `cooker` — «плита» (BrE), `ring` у контексті телефону «задзвонити», `boil over` і `afterwards` вжиті у матеріалі без пояснення. `pick up the phone` точніше «відповісти на дзвінок» у цьому сценарії.
- **Завдання.** `extra-2` допускає інший синтаксичний розподіл і перевіряє лише один рядок. Приклад `while it rained` можливий, але не демонструє коротку подію-переривання, якою пояснено правило. Краще зробити окрему вправу на дві паралельні дії.
- **Рішення.** Перенести ближче до першої розповіді Past Simple. Переписати пояснення до порядку слів.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 59 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| phone call | телефонний дзвінок | — | База |
| interrupt | переривати | — | База |
| background | тло | — | База |
| soup | суп | — | База |
| cooker | кухонна плита | — | База |
| noise | шум | — | База |
| spill | розливати | — | База |
| ring | дзвонити | — | База |
| while | поки | — | База |
| instead | натомість | — | База |
| doorbell | дверний дзвінок | — | Доповнення |
| knock | стукати | — | Доповнення |
| stir | помішувати | — | Доповнення |
| boil | кипіти | — | Доповнення |
| drop | впускати | — | Доповнення |
| suddenly | раптом | — | Доповнення |
| at that moment | тієї миті | — | Доповнення |
| switch off | вимикати | — | Доповнення |
| burn | підгоріти | — | Доповнення |
| pick up the phone | підняти слухавку | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-background-practice-1` | I ___ cooking when the phone rang. | was |
| `fleng-a2-background-practice-2` | They were ___ when I arrived. | studying |
| `fleng-a2-background-practice-3` | The phone ___ while I was cooking. (ring) | rang |
| `fleng-a2-background-practice-4` | While she ___ reading, I made tea. | was |
| `fleng-a2-background-practice-5` | We ___ the cooker afterwards. (clean) | cleaned |
| `fleng-a2-background-check-1` | Choose the Ukrainian meaning of "background" in this lesson. | тло |
| `fleng-a2-background-check-2` | Choose the Ukrainian meaning of "noise" in this lesson. | шум |
| `fleng-a2-background-check-3` | Choose the Ukrainian meaning of "while" in this lesson. | поки |
| `fleng-a2-background-extra-1` | I was cooking when the phone ___ . (ring, past) | rang |
| `fleng-a2-background-extra-2` | Put the words in order to make a sentence: were / They / dinner / having / while / it / rained | They were having dinner while it rained |
| `fleng-a2-background-extra-3` | Translate into English: «шум» | noise |
| `fleng-a2-background-extra-4` | Write one sentence with was/were + -ing and when. | I was walking home when it started to rain. |
| `fleng-a2-background-vocabulary-1` | What is the Ukrainian translation of «doorbell»? | дверний дзвінок |
| `fleng-a2-background-vocabulary-2` | Which English expression means «стукати»? | knock |
| `fleng-a2-background-vocabulary-3` | What is the Ukrainian translation of «stir»? | помішувати |
| `fleng-a2-background-vocabulary-4` | Which English expression means «кипіти»? | boil |
| `fleng-a2-background-vocabulary-5` | What is the Ukrainian translation of «drop»? | впускати |
| `fleng-a2-background-vocabulary-6` | Which English expression means «раптом»? | suddenly |
| `fleng-a2-background-vocabulary-7` | What is the Ukrainian translation of «at that moment»? | тієї миті |
| `fleng-a2-background-vocabulary-8` | Which English expression means «вимикати»? | switch off |
| `fleng-a2-background-vocabulary-9` | What is the Ukrainian translation of «burn»? | підгоріти |
| `fleng-a2-background-vocabulary-10` | Which English expression means «підняти слухавку»? | pick up the phone |

### 8. If the weather changes

- **Теорія.** Модель першої умови коректна як базова. Додати окремий `will` для рішення/обіцянки, перш ніж вводити if і when. Показати кому при першій умові. `in case` в тексті ще не пояснено і має іншу функцію. У базовому матеріалі 3 приклади, текст на 43 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `shower` тут «короткий дощ», в A1 — «душ»; позначити обидва сенси з прикладами. `forecast` — «прогноз погоди» в темі. `waterproof`, `postpone`, `backup plan` потребують опори.
- **Завдання.** `extra-1` приймає `'ll` у розділеному шаблоні `we ___`. `extra-2` допускає `I will` замість `I'll`, але інструкція каже користуватися даними словами. Дати повідомлення з планом і перенесенням як результат, прибрати `in case` з контрольного читання.
- **Рішення.** Розділити умови та часові речення. `when` лишити для перенесення після окремих зразків.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 69 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| picnic | пікнік | — | База |
| lake | озеро | — | База |
| dry | сухий | — | База |
| wet | мокрий | — | База |
| jacket | куртка | — | База |
| message | повідомлення | — | База |
| condition | умова | — | База |
| result | результат | — | База |
| forecast | прогноз | — | База |
| cancel | скасовувати | — | База |
| shower | короткочасний дощ | — | Доповнення |
| thunderstorm | гроза | — | Доповнення |
| wind | вітер | — | Доповнення |
| shelter | укриття | — | Доповнення |
| waterproof | водонепроникний | — | Доповнення |
| bring along | взяти із собою | — | Доповнення |
| take place | відбуватися | — | Доповнення |
| go ahead | відбутися за планом | — | Доповнення |
| postpone | відкладати | — | Доповнення |
| backup plan | запасний план | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-conditions-practice-1` | If it ___, we will stay inside. (rain) | rains |
| `fleng-a2-conditions-practice-2` | If it is dry, we ___ have a picnic. | will |
| `fleng-a2-conditions-practice-3` | I will call when I ___. (arrive) | arrive |
| `fleng-a2-conditions-practice-4` | If she comes, I will ___ her. | tell |
| `fleng-a2-conditions-practice-5` | We will cancel if the lake ___ frozen. | is |
| `fleng-a2-conditions-check-1` | Choose the Ukrainian meaning of "dry" in this lesson. | сухий |
| `fleng-a2-conditions-check-2` | Choose the Ukrainian meaning of "message" in this lesson. | повідомлення |
| `fleng-a2-conditions-check-3` | Choose the Ukrainian meaning of "forecast" in this lesson. | прогноз |
| `fleng-a2-conditions-extra-1` | If it rains, we ___ cancel the picnic. (future) | will / 'll |
| `fleng-a2-conditions-extra-2` | Put the words in order to make a sentence: send / I'll / you / a / message / when / arrive / I | I'll send you a message when I arrive / I will send you a message when I arrive |
| `fleng-a2-conditions-extra-3` | Translate into English: «прогноз» | forecast |
| `fleng-a2-conditions-extra-4` | Write one first-conditional sentence about the weekend. | If it is sunny, we will go to the lake. |
| `fleng-a2-conditions-vocabulary-1` | What is the Ukrainian translation of «shower»? | короткочасний дощ |
| `fleng-a2-conditions-vocabulary-2` | Which English expression means «гроза»? | thunderstorm |
| `fleng-a2-conditions-vocabulary-3` | What is the Ukrainian translation of «wind»? | вітер |
| `fleng-a2-conditions-vocabulary-4` | Which English expression means «укриття»? | shelter |
| `fleng-a2-conditions-vocabulary-5` | What is the Ukrainian translation of «waterproof»? | водонепроникний |
| `fleng-a2-conditions-vocabulary-6` | Which English expression means «взяти із собою»? | bring along |
| `fleng-a2-conditions-vocabulary-7` | What is the Ukrainian translation of «take place»? | відбуватися |
| `fleng-a2-conditions-vocabulary-8` | Which English expression means «відбутися за планом»? | go ahead |
| `fleng-a2-conditions-vocabulary-9` | What is the Ukrainian translation of «postpone»? | відкладати |
| `fleng-a2-conditions-vocabulary-10` | Which English expression means «запасний план»? | backup plan |

### 9. Which person do you mean?

- **Теорія.** Теорія викладає `who/which/where` і відсутність ком, але замовчує `that`, яке приймає `extra-1` і вимагає `extra-4` як можливість. Пояснити обов’язковість підмета та `the café where we meet` проти `the café which we like`. У базовому матеріалі 3 приклади, текст на 40 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `hold` — корисне повторення з A1. `identify` для учня зрозуміліше «визначати, про кого/що йдеться», `spotted` у темі одягу «у плямку / у цятку». `mine` і `ours` потребують попереднього короткого викладу.
- **Завдання.** MC коректні серед наявних опцій. `extra-2` дозволяє лише `This is the path where we walked`, хоча `This is where we walked the path` граматично можливе за іншого акценту. Задати «почни з This is the path».
- **Рішення.** Зберегти ближче до кінця A2 як уточнення в практичній ситуації.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 65 слів, 10 глос мають власні приклади. У 5 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| guide | гід | — | База |
| umbrella | парасоля | — | База |
| map | карта | — | База |
| path | стежка | — | База |
| tool | інструмент | — | База |
| identify | ідентифікувати | — | База |
| describe | описувати | — | База |
| hold | тримати | — | База |
| entrance | вхід | — | База |
| visitor | відвідувач | — | База |
| backpack | наплічник | — | Доповнення |
| beard | борода | — | Доповнення |
| curly hair | кучеряве волосся | — | Доповнення |
| striped | смугастий | — | Доповнення |
| spotted | у цятку | — | Доповнення |
| badge | значок | — | Доповнення |
| lead | вести | — | Доповнення |
| point out | вказувати | — | Доповнення |
| recognise | впізнавати | — | Доповнення |
| in the crowd | у натовпі | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-descriptions-practice-1` | The woman ___ works here is our guide. | who |
| `fleng-a2-descriptions-practice-2` | The map ___ is on the table is mine. | which |
| `fleng-a2-descriptions-practice-3` | This is the café ___ we meet. | where |
| `fleng-a2-descriptions-practice-4` | A guide is a person ___ helps visitors. | who |
| `fleng-a2-descriptions-practice-5` | A key is a thing ___ opens a lock. | which |
| `fleng-a2-descriptions-check-1` | Choose the Ukrainian meaning of "map" in this lesson. | карта |
| `fleng-a2-descriptions-check-2` | Choose the Ukrainian meaning of "identify" in this lesson. | ідентифікувати |
| `fleng-a2-descriptions-check-3` | Choose the Ukrainian meaning of "entrance" in this lesson. | вхід |
| `fleng-a2-descriptions-extra-1` | This is the guide ___ showed us the park. (person) | who / that |
| `fleng-a2-descriptions-extra-2` | Put the words in order to make a sentence: is / the / This / where / we / path / walked | This is the path where we walked |
| `fleng-a2-descriptions-extra-3` | Translate into English: «парасоля» | umbrella |
| `fleng-a2-descriptions-extra-4` | Describe a useful object with which or that. | An umbrella is a thing which keeps you dry. |
| `fleng-a2-descriptions-vocabulary-1` | What is the Ukrainian translation of «backpack»? | наплічник |
| `fleng-a2-descriptions-vocabulary-2` | Which English expression means «борода»? | beard |
| `fleng-a2-descriptions-vocabulary-3` | What is the Ukrainian translation of «curly hair»? | кучеряве волосся |
| `fleng-a2-descriptions-vocabulary-4` | Which English expression means «смугастий»? | striped |
| `fleng-a2-descriptions-vocabulary-5` | What is the Ukrainian translation of «spotted»? | у цятку |
| `fleng-a2-descriptions-vocabulary-6` | Which English expression means «значок»? | badge |
| `fleng-a2-descriptions-vocabulary-7` | What is the Ukrainian translation of «lead»? | вести |
| `fleng-a2-descriptions-vocabulary-8` | Which English expression means «вказувати»? | point out |
| `fleng-a2-descriptions-vocabulary-9` | What is the Ukrainian translation of «recognise»? | впізнавати |
| `fleng-a2-descriptions-vocabulary-10` | Which English expression means «у натовпі»? | in the crowd |

### 10. Solving a travel problem

- **Теорія.** Корисна комунікативна схема «що сталося → прохання → підтвердження». У контрольних пунктах є нові `Could you tell me when …?` і пасив `was delayed`, яких теорія не формує. `Could you + base` варто опрацювати раніше окремо. У базовому матеріалі 3 приклади, текст на 51 слів за пробілами, таблиць немає. Двомовний гід у sidecar відсутній. Правило та приклади подано англійською.
- **Словник.** `connection` уточнити «стикувальний рейс / пересадка» за контекстом, `reception` — «стійка реєстрації / рецепція». `file a claim`, `travel insurance`, `lost property` другорядні для базового прохання. Додати `room number`, `problem`, `help`, `another room`.
- **Завдання.** `practice-5` перевіряє вбудоване питання без пояснення порядку, `extra-2` — пасив до його викладу. `extra-4` модель ставить прохання перед проблемою, що прийнятно, але суперечить заявленій єдиній послідовності. Дати рубрику з трьома компонентами замість вимоги фіксованого порядку.
- **Рішення.** Повністю переписати фінальне оцінювання. Зберегти сценарій і використовувати вивчені форми.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 74 слів, 10 глос мають власні приклади. У 6 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| booking | бронювання | — | База |
| confirmation | підтвердження | — | База |
| surname | прізвище | — | База |
| passport | паспорт | — | База |
| reception | стійка реєстрації | — | База |
| delay | затримка | — | База |
| luggage | багаж | — | База |
| receipt | квитанція | — | База |
| solution | рішення | — | База |
| available | доступний | — | База |
| boarding pass | посадковий талон | — | Доповнення |
| check in | реєструватися на рейс | — | Доповнення |
| refund | повернення коштів | — | Доповнення |
| rebook | перебронювати | — | Доповнення |
| lost property | загублені речі | — | Доповнення |
| help desk | довідкова стійка | — | Доповнення |
| connection | пересадка | — | Доповнення |
| fully booked | без вільних місць | — | Доповнення |
| travel insurance | туристичне страхування | — | Доповнення |
| file a claim | подати вимогу про відшкодування | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a2-travel-problem-practice-1` | Yesterday I ___ my confirmation. (lose) | lost |
| `fleng-a2-travel-problem-practice-2` | Could you ___ my name? | check |
| `fleng-a2-travel-problem-practice-3` | If you show your passport, I ___ give you the key. | will |
| `fleng-a2-travel-problem-practice-4` | I have ___ the booking. (find) | found |
| `fleng-a2-travel-problem-practice-5` | Could you tell me when breakfast ___? | starts |
| `fleng-a2-travel-problem-check-1` | Choose the Ukrainian meaning of "surname" in this lesson. | прізвище |
| `fleng-a2-travel-problem-check-2` | Choose the Ukrainian meaning of "delay" in this lesson. | затримка |
| `fleng-a2-travel-problem-check-3` | Choose the Ukrainian meaning of "solution" in this lesson. | рішення |
| `fleng-a2-travel-problem-extra-1` | Could you ___ my booking, please? (check) | check |
| `fleng-a2-travel-problem-extra-2` | Put the words in order to make a sentence: was / My / delayed / luggage | My luggage was delayed |
| `fleng-a2-travel-problem-extra-3` | Translate into English: «паспорт» | passport |
| `fleng-a2-travel-problem-extra-4` | Write a polite request to a hotel receptionist about a problem. | Could you help me, please? My room is not available. |
| `fleng-a2-travel-problem-vocabulary-1` | What is the Ukrainian translation of «boarding pass»? | посадковий талон |
| `fleng-a2-travel-problem-vocabulary-2` | Which English expression means «реєструватися на рейс»? | check in |
| `fleng-a2-travel-problem-vocabulary-3` | What is the Ukrainian translation of «refund»? | повернення коштів |
| `fleng-a2-travel-problem-vocabulary-4` | Which English expression means «перебронювати»? | rebook |
| `fleng-a2-travel-problem-vocabulary-5` | What is the Ukrainian translation of «lost property»? | загублені речі |
| `fleng-a2-travel-problem-vocabulary-6` | Which English expression means «довідкова стійка»? | help desk |
| `fleng-a2-travel-problem-vocabulary-7` | What is the Ukrainian translation of «connection»? | пересадка |
| `fleng-a2-travel-problem-vocabulary-8` | Which English expression means «без вільних місць»? | fully booked |
| `fleng-a2-travel-problem-vocabulary-9` | What is the Ukrainian translation of «travel insurance»? | туристичне страхування |
| `fleng-a2-travel-problem-vocabulary-10` | Which English expression means «подати вимогу про відшкодування»? | file a claim |

## Підсумок рівня

Детальні критерії пріоритету, повтори лексики й наскрізні проблеми наведено у [реєстрі проблем](06_PROBLEMS.md). Рекомендований порядок і цілі кожного майбутнього уроку подано в [новій програмі](07_NEW_CURRICULUM.md).
