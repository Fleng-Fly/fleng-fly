# Аудит A0 — Absolute Beginner

## Структура і статус

Курс **A0 — Absolute Beginner** (`fleng-a0`) має 10 уроків. Розділи в моделі й каталозі відсутні, уроки належать напряму курсу. Нижче подано порядок `position`, який збігається з ланцюжком `prerequisites` у джерелі. Перший урок не має передумови. Передумови описують авторську послідовність. Каталог відкриває опублікований урок за прямим URL.

- 100 базових і 100 додаткових словникових записів. У цих 200 записів поле `example` порожнє. Приклади є в теорії. Поля транскрипції у джерелі та БД немає.
- 220 вправ: 50 основних тренувальних, 30 базових перевірок лексики, 40 форматів додаткової практики і 100 згенерованих перевірок перекладу. За механізмом 180 `single_choice`, 30 `text`, 10 `self_check`.
- 10 доступних перших проходів тесту уроку. Незалежних контрольних тестів курсу — 0. За редакційними категоріями 90 тренувальних і 130 перевірочних пунктів, але плеєр запускає спільну послідовність із 22 завдань.
- Перший прохід закінчується після однієї відповіді або пропуску кожного пункту. Для повного завершення уроку потрібен правильний стан усіх 22 вправ, у тому числі підтверджена учнем самоперевірка. Курс завершено після всіх опублікованих уроків. [Технічні деталі](01_ARCHITECTURE.md).
- Розширення має ще 5 неопублікованих уроків. Їх перелічено нижче.


| № | Урок | Slug | Тема |
| --- | --- | --- | --- |
| 1 | Words on the screen | `fleng-a0-classroom` | Наказовий спосіб і ввічливість |
| 2 | Letters and spelling | `fleng-a0-letters` | Літери, регістр і spelling |
| 3 | A first meeting | `fleng-a0-hello` | Привітання та ім’я |
| 4 | Numbers zero to twenty | `fleng-a0-numbers` | Числа й вік |
| 5 | One thing, two things | `fleng-a0-objects` | Артиклі й множина |
| 6 | People around me | `fleng-a0-people` | Займенники й родина |
| 7 | Colours and simple descriptions | `fleng-a0-describing` | Колір і позиція прикметника |
| 8 | Where is it? | `fleng-a0-where` | Місце й запитання Where |
| 9 | Yes, no and simple questions | `fleng-a0-questions` | Загальне питання, заперечення й стани |
| 10 | My first day: a short exchange | `fleng-a0-first-day` | Інтегрований перший день |

## Аналіз усіх десяти уроків

### 1. Words on the screen

- **Теорія.** Доступний шаблон із дієсловом на початку, `please` і `don't`. Англійська теорія потребує українського пояснення в релізі. Не плутати заборону з відповіддю «ні». Додати пари `open/close`, `speak/don't speak` і приклад `listen to`. У базовому матеріалі 3 приклади, текст на 16 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** 20 тематичних позицій, але `click` краще «клацати / натискати», `type` — «вводити текст», `look` навчати як `look at`, `stop` пояснити в контексті команди. Бракує `choose`, `answer`, `listen to` для навігації в завданнях.
- **Завдання.** `practice-1` дозволяє `Close it` після погляду на текст; уточнити що учень має зробити зі словами. `extra-2` вимагає `listen to the teacher`, хоча `listen to` окремо не подано. `check-2` просить згадати контекст `close`, якого в діалозі немає. Самоперевірка дає доречну продукцію, але потребує двох конкретних критеріїв.
- **Рішення.** Зберегти тему. Переписати неоднозначний пункт і дати мінітаблицю команд.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 20 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| read | читати | — | База |
| listen | слухати | — | База |
| write | писати | — | База |
| speak | говорити | — | База |
| open | відкривати | — | База |
| close | закривати | — | База |
| book | книга | — | База |
| name | ім’я | — | База |
| please | будь ласка | — | База |
| repeat | повторювати | — | База |
| screen | екран | — | Доповнення |
| text | текст | — | Доповнення |
| line | рядок | — | Доповнення |
| click | натискати | — | Доповнення |
| type | друкувати | — | Доповнення |
| look | дивитися | — | Доповнення |
| point | показувати пальцем | — | Доповнення |
| stop | зупинятися | — | Доповнення |
| start | починати | — | Доповнення |
| check | перевіряти | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-classroom-practice-1` | Look at the text. ___ it. | Read |
| `fleng-a0-classroom-practice-2` | Use a pen. ___ your name. | Write |
| `fleng-a0-classroom-practice-3` | Use your ears. ___. | Listen |
| `fleng-a0-classroom-practice-4` | Do not = ___. | Don't |
| `fleng-a0-classroom-practice-5` | Open your book, ___. (polite word) | please |
| `fleng-a0-classroom-check-1` | Choose the Ukrainian meaning of "write" in this lesson. | писати |
| `fleng-a0-classroom-check-2` | Choose the Ukrainian meaning of "close" in this lesson. | закривати |
| `fleng-a0-classroom-check-3` | Choose the Ukrainian meaning of "please" in this lesson. | будь ласка |
| `fleng-a0-classroom-extra-1` | Please ___ your book. (the opposite of close) | open |
| `fleng-a0-classroom-extra-2` | Put the words in order to make a sentence: the / Listen / to / teacher | Listen to the teacher |
| `fleng-a0-classroom-extra-3` | Translate into English: «писати» | write |
| `fleng-a0-classroom-extra-4` | Write two classroom instructions for a friend. Start each one with a verb. | Open your book. Repeat the word, please. |
| `fleng-a0-classroom-vocabulary-1` | What is the Ukrainian translation of «screen»? | екран |
| `fleng-a0-classroom-vocabulary-2` | Which English expression means «текст»? | text |
| `fleng-a0-classroom-vocabulary-3` | What is the Ukrainian translation of «line»? | рядок |
| `fleng-a0-classroom-vocabulary-4` | Which English expression means «натискати»? | click |
| `fleng-a0-classroom-vocabulary-5` | What is the Ukrainian translation of «type»? | друкувати |
| `fleng-a0-classroom-vocabulary-6` | Which English expression means «дивитися»? | look |
| `fleng-a0-classroom-vocabulary-7` | What is the Ukrainian translation of «point»? | показувати пальцем |
| `fleng-a0-classroom-vocabulary-8` | Which English expression means «зупинятися»? | stop |
| `fleng-a0-classroom-vocabulary-9` | What is the Ukrainian translation of «start»? | починати |
| `fleng-a0-classroom-vocabulary-10` | Which English expression means «перевіряти»? | check |

### 2. Letters and spelling

- **Теорія.** База коректно згадує голосну функцію `y` і розрізняє назви літер та звуки. Чернетковий гід в обох мовах і `extra-1` заперечують це. Порада для `practice-3` помилково прив’язує порядок літер до послідовності звуків. Бракує A–Z з назвами літер і показу верхнього/нижнього регістру. У базовому матеріалі 3 приклади, текст на 17 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `small` як «маленький» не пояснює `small letter`. Подати `capital letter`, `lower-case letter`, `letter name`; `spell` уточнити «називати/писати по літерах». `sound`, `space`, `dot` доречні за наявності прикладів.
- **Завдання.** `M-I-A` перевіряє копіювання за видимим написом. `extra-2` визнає два порядки `please`, але пояснення про дієслово на початку не охоплює `Please spell …`. Модель `extra-4` додає представлення, хоча запитано лише ім’я по літерах. Потрібне самостійне відтворення написання.
- **Рішення.** Повністю переписати пояснення й підказки. Спелінг без аудіо описувати як письмову вправу.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 29 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| letter | літера | — | База |
| alphabet | алфавіт | — | База |
| spell | називати по літерах | — | База |
| capital | велика літера | — | База |
| small | маленький | — | База |
| vowel | голосна літера | — | База |
| consonant | приголосна літера | — | База |
| word | слово | — | База |
| pen | ручка | — | База |
| page | сторінка | — | База |
| paper | папір | — | Доповнення |
| sound | звук | — | Доповнення |
| space | пробіл | — | Доповнення |
| dot | крапка | — | Доповнення |
| mark | позначка | — | Доповнення |
| card | картка | — | Доповнення |
| copy | копіювати | — | Доповнення |
| print | роздруковувати | — | Доповнення |
| say | казати | — | Доповнення |
| sign | знак | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-letters-practice-1` | Which letter is a vowel? | a |
| `fleng-a0-letters-practice-2` | Which letter is a consonant? | m |
| `fleng-a0-letters-practice-3` | Spell the name Mia: ___. | M-I-A |
| `fleng-a0-letters-practice-4` | A name starts with a ___ letter. | capital |
| `fleng-a0-letters-practice-5` | How do you ___ it? (ask for letters) | spell |
| `fleng-a0-letters-check-1` | Choose the Ukrainian meaning of "spell" in this lesson. | називати по літерах |
| `fleng-a0-letters-check-2` | Choose the Ukrainian meaning of "vowel" in this lesson. | голосна літера |
| `fleng-a0-letters-check-3` | Choose the Ukrainian meaning of "pen" in this lesson. | ручка |
| `fleng-a0-letters-extra-1` | A, E, I, O and U are ___ letters. (not consonants) | vowel |
| `fleng-a0-letters-extra-2` | Put the words in order to make a sentence: your / Spell / please / name | Spell your name please / Please spell your name |
| `fleng-a0-letters-extra-3` | Translate into English: «слово» | word |
| `fleng-a0-letters-extra-4` | Spell your first name letter by letter, with a dash between the letters. | A-N-N-A. My name is Anna. |
| `fleng-a0-letters-vocabulary-1` | What is the Ukrainian translation of «paper»? | папір |
| `fleng-a0-letters-vocabulary-2` | Which English expression means «звук»? | sound |
| `fleng-a0-letters-vocabulary-3` | What is the Ukrainian translation of «space»? | пробіл |
| `fleng-a0-letters-vocabulary-4` | Which English expression means «крапка»? | dot |
| `fleng-a0-letters-vocabulary-5` | What is the Ukrainian translation of «mark»? | позначка |
| `fleng-a0-letters-vocabulary-6` | Which English expression means «картка»? | card |
| `fleng-a0-letters-vocabulary-7` | What is the Ukrainian translation of «copy»? | копіювати |
| `fleng-a0-letters-vocabulary-8` | Which English expression means «роздруковувати»? | print |
| `fleng-a0-letters-vocabulary-9` | What is the Ukrainian translation of «say»? | казати |
| `fleng-a0-letters-vocabulary-10` | Which English expression means «знак»? | sign |

### 3. A first meeting

- **Теорія.** Природні формули `I am`, `My name is`, `Nice to meet you`. У базі немає явного показу `you are → you're`, хоча це перевіряється. Чернетковий гід його додає. Розмежувати формулу `How are you?` і наступне навчання питань. У базовому матеріалі 3 приклади, текст на 23 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `hello/hi`, `goodbye/bye`, `thanks/thank you` — корисні пари регістру з однаковим перекладом. `good evening` — привітання, `good night` — прощання. `meet` у формулі першого знайомства означає «познайомитися», `student` — залежно від контексту учень або студент. `welcome` і `you're welcome` мають різні функції.
- **Завдання.** `practice-5` випереджає базовий виклад. `extra-1` приймає фрагмент `'m` після окремо надрукованого `I ___`, що візуально дає `I 'm`. `extra-4` просить два короткі речення, а зразок має три репліки/речення. Підказку про «одну річ» для `my name` замінити поясненням підмета.
- **Рішення.** Зберегти сценарій зустрічі. Інтегрувати споріднений матеріал English Foundations як повторення за змістом.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 36 слів, 10 глос мають власні приклади. У 6 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| hello | привіт | — | База |
| goodbye | до побачення | — | База |
| morning | ранок | — | База |
| evening | вечір | — | База |
| friend | друг | — | База |
| teacher | учитель | — | База |
| student | учень | — | База |
| meet | зустрічати | — | База |
| welcome | ласкаво просимо | — | База |
| thanks | дякую | — | База |
| hi | привіт | — | Доповнення |
| bye | бувай | — | Доповнення |
| welcome back | з поверненням | — | Доповнення |
| good morning | доброго ранку | — | Доповнення |
| good evening | добрий вечір | — | Доповнення |
| good night | на добраніч | — | Доповнення |
| thank you | дякую | — | Доповнення |
| how are you? | як справи? | — | Доповнення |
| fine | добре | — | Доповнення |
| nice to meet you | приємно познайомитися | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-hello-practice-1` | I ___ Eva. | am |
| `fleng-a0-hello-practice-2` | My name ___ Ben. | is |
| `fleng-a0-hello-practice-3` | I am = ___. | I'm |
| `fleng-a0-hello-practice-4` | Nice to meet you ___. (reply) | too |
| `fleng-a0-hello-practice-5` | You are = ___. | You're |
| `fleng-a0-hello-check-1` | Choose the Ukrainian meaning of "morning" in this lesson. | ранок |
| `fleng-a0-hello-check-2` | Choose the Ukrainian meaning of "teacher" in this lesson. | учитель |
| `fleng-a0-hello-check-3` | Choose the Ukrainian meaning of "welcome" in this lesson. | ласкаво просимо |
| `fleng-a0-hello-extra-1` | Hello, I ___ Tom. Nice to meet you. | am / 'm |
| `fleng-a0-hello-extra-2` | Put the words in order to make a sentence: you / Nice / meet / to | Nice to meet you |
| `fleng-a0-hello-extra-3` | Translate into English: «друг» | friend |
| `fleng-a0-hello-extra-4` | Introduce yourself in two short sentences: say hello and your name. | Hello! I am Olena. Nice to meet you. |
| `fleng-a0-hello-vocabulary-1` | What is the Ukrainian translation of «hi»? | привіт |
| `fleng-a0-hello-vocabulary-2` | Which English expression means «бувай»? | bye |
| `fleng-a0-hello-vocabulary-3` | What is the Ukrainian translation of «welcome back»? | з поверненням |
| `fleng-a0-hello-vocabulary-4` | Which English expression means «доброго ранку»? | good morning |
| `fleng-a0-hello-vocabulary-5` | What is the Ukrainian translation of «good evening»? | добрий вечір |
| `fleng-a0-hello-vocabulary-6` | Which English expression means «на добраніч»? | good night |
| `fleng-a0-hello-vocabulary-7` | What is the Ukrainian translation of «thank you»? | дякую |
| `fleng-a0-hello-vocabulary-8` | Which English expression means «як справи?»? | how are you? |
| `fleng-a0-hello-vocabulary-9` | What is the Ukrainian translation of «fine»? | добре |
| `fleng-a0-hello-vocabulary-10` | Which English expression means «приємно познайомитися»? | nice to meet you |

### 4. Numbers zero to twenty

- **Теорія.** Тема обіцяє повний ряд 0–20 і згадує диктування телефонного номера. Немає повного ряду, `seventeen` відсутнє навіть після доповнення, приклад телефону відсутній. Форма віку з `be` подана правильно. У базовому матеріалі 3 приклади, текст на 19 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Цифрові пари коректні. Додати `seventeen`, `number`, `phone number`, `years old`; уникати перевантаження через одночасне введення арифметики й сім’ї.
- **Завдання.** Три з п’яти основних питань відтворюють готові приклади `twelve/twenty/three`. `extra-4` потребує сімейної лексики та `There are` до уроків про сім’ю і A1 про існування. Сфокусувати результат на віці та номері.
- **Рішення.** Розділити навчання чисел і застосування в анкеті. Телефон перевіряти як запис цифр; для усного сприйняття вказати межі.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 23 слів, 10 глос мають власні приклади. У 6 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| zero | нуль | — | База |
| one | один | — | База |
| two | два | — | База |
| three | три | — | База |
| four | чотири | — | База |
| five | п’ять | — | База |
| ten | десять | — | База |
| twelve | дванадцять | — | База |
| nineteen | дев’ятнадцять | — | База |
| twenty | двадцять | — | База |
| six | шість | — | Доповнення |
| seven | сім | — | Доповнення |
| eight | вісім | — | Доповнення |
| nine | дев’ять | — | Доповнення |
| eleven | одинадцять | — | Доповнення |
| thirteen | тринадцять | — | Доповнення |
| fourteen | чотирнадцять | — | Доповнення |
| fifteen | п’ятнадцять | — | Доповнення |
| sixteen | шістнадцять | — | Доповнення |
| eighteen | вісімнадцять | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-numbers-practice-1` | Write 12 in words. | twelve |
| `fleng-a0-numbers-practice-2` | Write 20 in words. | twenty |
| `fleng-a0-numbers-practice-3` | Write 3 in words. | three |
| `fleng-a0-numbers-practice-4` | For age: I ___ twenty. | am |
| `fleng-a0-numbers-practice-5` | Write 0 in words. | zero |
| `fleng-a0-numbers-check-1` | Choose the Ukrainian meaning of "two" in this lesson. | два |
| `fleng-a0-numbers-check-2` | Choose the Ukrainian meaning of "five" in this lesson. | п’ять |
| `fleng-a0-numbers-check-3` | Choose the Ukrainian meaning of "nineteen" in this lesson. | дев’ятнадцять |
| `fleng-a0-numbers-extra-1` | Five and five is ___. (write the number as a word) | ten |
| `fleng-a0-numbers-extra-2` | Put the words in order to make a sentence: years / I / twenty / am / old | I am twenty years old |
| `fleng-a0-numbers-extra-3` | Translate into English: «дванадцять» | twelve |
| `fleng-a0-numbers-extra-4` | Write your age and the number of people in your family as words. | I am nineteen. There are four people in my family. |
| `fleng-a0-numbers-vocabulary-1` | What is the Ukrainian translation of «six»? | шість |
| `fleng-a0-numbers-vocabulary-2` | Which English expression means «сім»? | seven |
| `fleng-a0-numbers-vocabulary-3` | What is the Ukrainian translation of «eight»? | вісім |
| `fleng-a0-numbers-vocabulary-4` | Which English expression means «дев’ять»? | nine |
| `fleng-a0-numbers-vocabulary-5` | What is the Ukrainian translation of «eleven»? | одинадцять |
| `fleng-a0-numbers-vocabulary-6` | Which English expression means «тринадцять»? | thirteen |
| `fleng-a0-numbers-vocabulary-7` | What is the Ukrainian translation of «fourteen»? | чотирнадцять |
| `fleng-a0-numbers-vocabulary-8` | Which English expression means «п’ятнадцять»? | fifteen |
| `fleng-a0-numbers-vocabulary-9` | What is the Ukrainian translation of «sixteen»? | шістнадцять |
| `fleng-a0-numbers-vocabulary-10` | Which English expression means «вісімнадцять»? | eighteen |

### 5. One thing, two things

- **Теорія.** Основне правило про звук та обмеження на злічувану однину коректне. У чернетковому гіді фраза «після числа вживаємо множину» без уточнення суперечить `one pen`. Показати `one/two`, `a/an` і дати один зразок суто на звук, коли це методично підготовлено. У базовому матеріалі 3 приклади, текст на 14 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Предмети впізнавані, `shoe` завузько перекладено як «черевик» без контексту. Потрібні окремі пари типу `pen/pens`; `pen` уже в попередній лексиці, повтор доречний.
- **Завдання.** `extra-1` вводить `I have` до A1, `extra-2` — `This is` до пояснення в неопублікованому розширенні. `extra-4` спирається на `on your desk` до уроку місця. Залишити ці форми лише як явно дані шаблони.
- **Рішення.** Зберегти ядро. Розвести артикль і множину на два короткі блоки з контрольованою лексикою.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 30 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| bag | сумка | — | База |
| apple | яблуко | — | База |
| desk | письмовий стіл | — | База |
| chair | стілець | — | База |
| door | двері | — | База |
| window | вікно | — | База |
| cup | чашка | — | База |
| pencil | олівець | — | База |
| orange | апельсин | — | База |
| key | ключ | — | База |
| ball | м’яч | — | Доповнення |
| bottle | пляшка | — | Доповнення |
| plate | тарілка | — | Доповнення |
| spoon | ложка | — | Доповнення |
| fork | виделка | — | Доповнення |
| hat | капелюх | — | Доповнення |
| shoe | черевик | — | Доповнення |
| toy | іграшка | — | Доповнення |
| clock | годинник | — | Доповнення |
| lamp | лампа | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-objects-practice-1` | ___ apple | an |
| `fleng-a0-objects-practice-2` | ___ bag | a |
| `fleng-a0-objects-practice-3` | Two ___. (pen) | pens |
| `fleng-a0-objects-practice-4` | Three ___. (cup) | cups |
| `fleng-a0-objects-practice-5` | ___ orange | an |
| `fleng-a0-objects-check-1` | Choose the Ukrainian meaning of "desk" in this lesson. | письмовий стіл |
| `fleng-a0-objects-check-2` | Choose the Ukrainian meaning of "window" in this lesson. | вікно |
| `fleng-a0-objects-check-3` | Choose the Ukrainian meaning of "orange" in this lesson. | апельсин |
| `fleng-a0-objects-extra-1` | I have ___ apple in my bag. (a or an?) | an |
| `fleng-a0-objects-extra-2` | Put the words in order to make a sentence: is / This / a / pencil | This is a pencil |
| `fleng-a0-objects-extra-3` | Translate into English: «ключ» | key |
| `fleng-a0-objects-extra-4` | Name three things on your desk. Use a or an with each one. | a pen, an orange and a cup |
| `fleng-a0-objects-vocabulary-1` | What is the Ukrainian translation of «ball»? | м’яч |
| `fleng-a0-objects-vocabulary-2` | Which English expression means «пляшка»? | bottle |
| `fleng-a0-objects-vocabulary-3` | What is the Ukrainian translation of «plate»? | тарілка |
| `fleng-a0-objects-vocabulary-4` | Which English expression means «ложка»? | spoon |
| `fleng-a0-objects-vocabulary-5` | What is the Ukrainian translation of «fork»? | виделка |
| `fleng-a0-objects-vocabulary-6` | Which English expression means «капелюх»? | hat |
| `fleng-a0-objects-vocabulary-7` | What is the Ukrainian translation of «shoe»? | черевик |
| `fleng-a0-objects-vocabulary-8` | Which English expression means «іграшка»? | toy |
| `fleng-a0-objects-vocabulary-9` | What is the Ukrainian translation of «clock»? | годинник |
| `fleng-a0-objects-vocabulary-10` | Which English expression means «лампа»? | lamp |

### 6. People around me

- **Теорія.** Англійська база коректно обмежує вправи множинним `they` та формулює `he/she` через займенник людини. Додати таблицю `I/am` тощо і коротке введення `my`, яке потрібно для діалогу. `people` є лексичним винятком до -s. У базовому матеріалі 3 приклади, текст на 21 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `parent` природніше подати як «мати або батько; один із батьків». `cousin` потребує вказати обидва роди; набір родини доречний, `parents` і `children` необхідні як моделі.
- **Завдання.** `extra-1` пояснює `she` категоричним формулюванням «A sister is a woman», що неточно щодо дітей та вибору займенника. `extra-2` має неприродне `They goes with are`; редагувати метамову. `extra-4` просить 2 речення, придатний критерій — правильний підмет і форма `be`.
- **Рішення.** Зберегти тему, викласти `my/your` раніше й зменшити нові родинні назви.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 42 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| family | сім’я | — | База |
| sister | сестра | — | База |
| brother | брат | — | База |
| mother | мати | — | База |
| father | батько | — | База |
| person | людина | — | База |
| people | люди | — | База |
| child | дитина | — | База |
| photo | фотографія | — | База |
| parent | хтось із батьків | — | База |
| aunt | тітка | — | Доповнення |
| uncle | дядько | — | Доповнення |
| grandmother | бабуся | — | Доповнення |
| grandfather | дідусь | — | Доповнення |
| baby | немовля | — | Доповнення |
| boy | хлопчик | — | Доповнення |
| girl | дівчинка | — | Доповнення |
| man | чоловік | — | Доповнення |
| woman | жінка | — | Доповнення |
| cousin | двоюрідний брат або сестра | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-people-practice-1` | She ___ my sister. | is |
| `fleng-a0-people-practice-2` | We ___ students. | are |
| `fleng-a0-people-practice-3` | He ___ my brother. | is |
| `fleng-a0-people-practice-4` | They ___ teachers. | are |
| `fleng-a0-people-practice-5` | The photo: ___ is here. | It |
| `fleng-a0-people-check-1` | Choose the Ukrainian meaning of "brother" in this lesson. | брат |
| `fleng-a0-people-check-2` | Choose the Ukrainian meaning of "person" in this lesson. | людина |
| `fleng-a0-people-check-3` | Choose the Ukrainian meaning of "photo" in this lesson. | фотографія |
| `fleng-a0-people-extra-1` | This is my sister. ___ is a student. (he or she?) | she |
| `fleng-a0-people-extra-2` | Put the words in order to make a sentence: are / my / They / parents | They are my parents |
| `fleng-a0-people-extra-3` | Translate into English: «брат» | brother |
| `fleng-a0-people-extra-4` | Write two sentences about people in your family. Use he, she or they. | My mother is a teacher. She is kind. |
| `fleng-a0-people-vocabulary-1` | What is the Ukrainian translation of «aunt»? | тітка |
| `fleng-a0-people-vocabulary-2` | Which English expression means «дядько»? | uncle |
| `fleng-a0-people-vocabulary-3` | What is the Ukrainian translation of «grandmother»? | бабуся |
| `fleng-a0-people-vocabulary-4` | Which English expression means «дідусь»? | grandfather |
| `fleng-a0-people-vocabulary-5` | What is the Ukrainian translation of «baby»? | немовля |
| `fleng-a0-people-vocabulary-6` | Which English expression means «хлопчик»? | boy |
| `fleng-a0-people-vocabulary-7` | What is the Ukrainian translation of «girl»? | дівчинка |
| `fleng-a0-people-vocabulary-8` | Which English expression means «чоловік»? | man |
| `fleng-a0-people-vocabulary-9` | What is the Ukrainian translation of «woman»? | жінка |
| `fleng-a0-people-vocabulary-10` | Which English expression means «двоюрідний брат або сестра»? | cousin |

### 7. Colours and simple descriptions

- **Теорія.** Обидві позиції прикметника та незмінність подано правильно. Бракує пояснення, чому в `The bag is big` з’являється `the`, і матриці `a red bag / two red bags / the bag is red`. У базовому матеріалі 3 приклади, текст на 17 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Кольори й розмір відповідають рівню. `grey` — нормативне британське написання; варто додати `gray` як допустимий варіант, якщо його запитують. `light`/`dark` потребують кольорового контексту; `round` і `beautiful` менш пріоритетні за `small`.
- **Завдання.** `practice-2/4` вимірюють `be`, а не позицію прикметника; це корисне повторення за умови збереження окремих перевірок цільової навички. `extra-3`: «старий» без предмета допускає `old` у заданій лексиці, а контекст дав би ясніший сенс. `extra-4` модель використовує `and`, яке можна дати як явний шаблон.
- **Рішення.** Зберегти ядро. Додати завдання на зміну порядку й повторно використати назви предметів.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 25 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| red | червоний | — | База |
| blue | синій | — | База |
| green | зелений | — | База |
| black | чорний | — | База |
| white | білий | — | База |
| big | великий | — | База |
| old | старий | — | База |
| new | новий | — | База |
| yellow | жовтий | — | База |
| colour | колір | — | База |
| pink | рожевий | — | Доповнення |
| purple | фіолетовий | — | Доповнення |
| brown | коричневий | — | Доповнення |
| grey | сірий | — | Доповнення |
| dark | темний | — | Доповнення |
| light | світлий | — | Доповнення |
| long | довгий | — | Доповнення |
| short | короткий | — | Доповнення |
| round | круглий | — | Доповнення |
| beautiful | гарний | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-describing-practice-1` | A ___ bag. (colour) | red |
| `fleng-a0-describing-practice-2` | The bag ___ big. | is |
| `fleng-a0-describing-practice-3` | Two ___ cups. (colour) | blue |
| `fleng-a0-describing-practice-4` | The books ___ new. | are |
| `fleng-a0-describing-practice-5` | Choose the correct order. | a green book |
| `fleng-a0-describing-check-1` | Choose the Ukrainian meaning of "green" in this lesson. | зелений |
| `fleng-a0-describing-check-2` | Choose the Ukrainian meaning of "big" in this lesson. | великий |
| `fleng-a0-describing-check-3` | Choose the Ukrainian meaning of "yellow" in this lesson. | жовтий |
| `fleng-a0-describing-extra-1` | My bag is ___. (колір: червоний) | red |
| `fleng-a0-describing-extra-2` | Put the words in order to make a sentence: big / a / It / is / house | It is a big house |
| `fleng-a0-describing-extra-3` | Translate into English: «старий» | old |
| `fleng-a0-describing-extra-4` | Describe one thing in your room with two adjectives. | My chair is black and old. |
| `fleng-a0-describing-vocabulary-1` | What is the Ukrainian translation of «pink»? | рожевий |
| `fleng-a0-describing-vocabulary-2` | Which English expression means «фіолетовий»? | purple |
| `fleng-a0-describing-vocabulary-3` | What is the Ukrainian translation of «brown»? | коричневий |
| `fleng-a0-describing-vocabulary-4` | Which English expression means «сірий»? | grey |
| `fleng-a0-describing-vocabulary-5` | What is the Ukrainian translation of «dark»? | темний |
| `fleng-a0-describing-vocabulary-6` | Which English expression means «світлий»? | light |
| `fleng-a0-describing-vocabulary-7` | What is the Ukrainian translation of «long»? | довгий |
| `fleng-a0-describing-vocabulary-8` | Which English expression means «короткий»? | short |
| `fleng-a0-describing-vocabulary-9` | What is the Ukrainian translation of «round»? | круглий |
| `fleng-a0-describing-vocabulary-10` | Which English expression means «гарний»? | beautiful |

### 8. Where is it?

- **Теорія.** `in/on/under` та `Where is/are` придатні. Визначення `on` через верх поверхні надто вузьке для `on the wall`; спочатку показати типові значення й форму загального питання з `be`, а потім `where`. У базовому матеріалі 3 приклади, текст на 22 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** Достатньо трьох прийменників і кількох предметів. `inside`, `below`, `touches`, `surface` у поясненнях складніші за цільові слова і потребують перекладу. `above/behind/in front of` — окремий підблок. `corner` для кімнати природніше «куток / кут кімнати».
- **Завдання.** `practice-1–3` дослівно повторюють зразки і дають відповіді через парафрази складнішою англійською. `extra-1/2` повторюють правило контрольовано. Для перевірки читання дати нову коротку ситуацію і питання про місце.
- **Рішення.** Перенести після загальних питань. Поєднати з подальшою темою кімнати спіральним повторенням.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 44 слів, 10 глос мають власні приклади. У 7 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| in | у | — | База |
| on | на | — | База |
| under | під | — | База |
| here | тут | — | База |
| there | там | — | База |
| room | кімната | — | База |
| box | коробка | — | База |
| table | стіл | — | База |
| floor | підлога | — | База |
| wall | стіна | — | База |
| above | над | — | Доповнення |
| behind | позаду | — | Доповнення |
| next to | поруч із | — | Доповнення |
| inside | всередині | — | Доповнення |
| outside | зовні | — | Доповнення |
| shelf | полиця | — | Доповнення |
| bed | ліжко | — | Доповнення |
| rug | килимок | — | Доповнення |
| corner | кут | — | Доповнення |
| in front of | перед | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-where-practice-1` | The key is inside the bag: ___ the bag. | in |
| `fleng-a0-where-practice-2` | The cup touches the top of the desk: ___ the desk. | on |
| `fleng-a0-where-practice-3` | The ball is below the chair: ___ the chair. | under |
| `fleng-a0-where-practice-4` | Where ___ the key? | is |
| `fleng-a0-where-practice-5` | Where ___ the books? | are |
| `fleng-a0-where-check-1` | Choose the Ukrainian meaning of "under" in this lesson. | під |
| `fleng-a0-where-check-2` | Choose the Ukrainian meaning of "room" in this lesson. | кімната |
| `fleng-a0-where-check-3` | Choose the Ukrainian meaning of "floor" in this lesson. | підлога |
| `fleng-a0-where-extra-1` | The cat is ___ the box. (inside it) | in |
| `fleng-a0-where-extra-2` | Put the words in order to make a sentence: the / Where / keys / are | Where are the keys |
| `fleng-a0-where-extra-3` | Translate into English: «стіна» | wall |
| `fleng-a0-where-extra-4` | Write where two things in your room are. Use in, on or under. | My phone is on the table. My bag is under the chair. |
| `fleng-a0-where-vocabulary-1` | What is the Ukrainian translation of «above»? | над |
| `fleng-a0-where-vocabulary-2` | Which English expression means «позаду»? | behind |
| `fleng-a0-where-vocabulary-3` | What is the Ukrainian translation of «next to»? | поруч із |
| `fleng-a0-where-vocabulary-4` | Which English expression means «всередині»? | inside |
| `fleng-a0-where-vocabulary-5` | What is the Ukrainian translation of «outside»? | зовні |
| `fleng-a0-where-vocabulary-6` | Which English expression means «полиця»? | shelf |
| `fleng-a0-where-vocabulary-7` | What is the Ukrainian translation of «bed»? | ліжко |
| `fleng-a0-where-vocabulary-8` | Which English expression means «килимок»? | rug |
| `fleng-a0-where-vocabulary-9` | What is the Ukrainian translation of «corner»? | кут |
| `fleng-a0-where-vocabulary-10` | Which English expression means «перед»? | in front of |

### 9. Yes, no and simple questions

- **Теорія.** Правило інверсії і коротких відповідей придатне. `before the person` замінити на «перед підметом», оскільки приклад має `the room`. Додати три пари `Yes/No` і повні/скорочені форми, показати `I'm not`. У базовому матеріалі 3 приклади, текст на 21 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `late` як «той, хто запізнився» не відповідає прикметниковому вживанню `I am late`. `thirsty` — природніше «хоче пити» у фразі, `hot` і `cold` залежні від підмета, `who/what` вводити лише зі зразками.
- **Завдання.** Пункти граматично узгоджені, але `practice-1` і `extra-1` перевіряють ту саму форму. Самоперевірка доречна. Додати завдання на зміну перспективи `you → I` і нові стани без підстановки дослівно з теорії.
- **Рішення.** Зберегти граматичне ядро, перенести перед `Where` і відділити стани від питальних слів.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 21 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| ready | готовий | — | База |
| late | той, хто запізнився | — | База |
| happy | щасливий | — | База |
| tired | втомлений | — | База |
| cold | холодний | — | База |
| warm | теплий | — | База |
| yes | так | — | База |
| no | ні | — | База |
| question | запитання | — | База |
| answer | відповідь | — | База |
| sad | сумний | — | Доповнення |
| hungry | голодний | — | Доповнення |
| thirsty | спраглий | — | Доповнення |
| hot | гарячий | — | Доповнення |
| afraid | наляканий | — | Доповнення |
| sick | хворий | — | Доповнення |
| right | правильний | — | Доповнення |
| wrong | неправильний | — | Доповнення |
| who | хто | — | Доповнення |
| what | що | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-questions-practice-1` | ___ you ready? | Are |
| `fleng-a0-questions-practice-2` | Is she tired? Yes, she ___. | is |
| `fleng-a0-questions-practice-3` | I ___ not late. | am |
| `fleng-a0-questions-practice-4` | They are not = They ___. | aren't |
| `fleng-a0-questions-practice-5` | ___ the room warm? | Is |
| `fleng-a0-questions-check-1` | Choose the Ukrainian meaning of "happy" in this lesson. | щасливий |
| `fleng-a0-questions-check-2` | Choose the Ukrainian meaning of "warm" in this lesson. | теплий |
| `fleng-a0-questions-check-3` | Choose the Ukrainian meaning of "question" in this lesson. | запитання |
| `fleng-a0-questions-extra-1` | ___ you tired? — Yes, I am. | are |
| `fleng-a0-questions-extra-2` | Put the words in order to make a sentence: not / I / am / late | I am not late |
| `fleng-a0-questions-extra-3` | Translate into English: «щасливий» | happy |
| `fleng-a0-questions-extra-4` | Write one question with Are you…? and a short answer. | Are you cold? No, I am not. |
| `fleng-a0-questions-vocabulary-1` | What is the Ukrainian translation of «sad»? | сумний |
| `fleng-a0-questions-vocabulary-2` | Which English expression means «голодний»? | hungry |
| `fleng-a0-questions-vocabulary-3` | What is the Ukrainian translation of «thirsty»? | спраглий |
| `fleng-a0-questions-vocabulary-4` | Which English expression means «гарячий»? | hot |
| `fleng-a0-questions-vocabulary-5` | What is the Ukrainian translation of «afraid»? | наляканий |
| `fleng-a0-questions-vocabulary-6` | Which English expression means «хворий»? | sick |
| `fleng-a0-questions-vocabulary-7` | What is the Ukrainian translation of «right»? | правильний |
| `fleng-a0-questions-vocabulary-8` | Which English expression means «неправильний»? | wrong |
| `fleng-a0-questions-vocabulary-9` | What is the Ukrainian translation of «who»? | хто |
| `fleng-a0-questions-vocabulary-10` | Which English expression means «що»? | what |

### 10. My first day: a short exchange

- **Теорія.** Діалог справді повторює знайомство, місце й `be`. Демонстратив `This is` і присвійні `my/your` були ситуативними, але не систематизовані. Нова лексика у фіналі знижує чистоту діагностики. У базовому матеріалі 3 приклади, текст на 41 слів за пробілами, таблиць немає. Є чернетковий гід EN/UK з трьома парами прикладів та підказками до восьми базових вправ. Він недоступний за виробничого налаштування.
- **Словник.** `seat` природніше «місце», `partner` конкретизувати «напарник у парі», `class` має значення «заняття», «група», «клас». `help` уточнити як іменник або команду. `OK` у нормалізованому словнику стає `ok`.
- **Завдання.** `practice-1–5` відтворюють майже готові репліки. `extra-4` вводить `first` і `friendly` у моделі. Варто дати новий діалог і перевіряти факти з тексту, доповнити іншим сценарієм для продукції.
- **Рішення.** Зберегти як підсумковий урок. Переписати завдання й переносити нові слова раніше.
- **Архівна чернетка.** Той самий slug і граматичне ядро. Текст має 56 слів, 10 глос мають власні приклади. У 8 з 8 базових записів відрізняється принаймні одне поле. Ключі чернетки прив’язані до її власних варіантів.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| classroom | класна кімната | — | База |
| seat | місце для сидіння | — | База |
| notebook | зошит | — | База |
| school | школа | — | База |
| lesson | урок | — | База |
| today | сьогодні | — | База |
| now | зараз | — | База |
| partner | партнер | — | База |
| again | знову | — | База |
| OK | гаразд | — | База |
| class | клас | — | Доповнення |
| board | дошка | — | Доповнення |
| eraser | гумка | — | Доповнення |
| homework | домашнє завдання | — | Доповнення |
| classmate | однокласник | — | Доповнення |
| welcome to school | ласкаво просимо до школи | — | Доповнення |
| excuse me | перепрошую | — | Доповнення |
| sorry | вибачте | — | Доповнення |
| see you | до зустрічі | — | Доповнення |
| help | допомога | — | Доповнення |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-first-day-practice-1` | I ___ Ada. | am |
| `fleng-a0-first-day-practice-2` | This is ___ classroom. | a |
| `fleng-a0-first-day-practice-3` | Where ___ my notebook? | is |
| `fleng-a0-first-day-practice-4` | My notebook is ___ the desk. (on its top) | on |
| `fleng-a0-first-day-practice-5` | Are you ready? Yes, I ___. | am |
| `fleng-a0-first-day-check-1` | Choose the Ukrainian meaning of "notebook" in this lesson. | зошит |
| `fleng-a0-first-day-check-2` | Choose the Ukrainian meaning of "today" in this lesson. | сьогодні |
| `fleng-a0-first-day-check-3` | Choose the Ukrainian meaning of "again" in this lesson. | знову |
| `fleng-a0-first-day-extra-1` | This ___ my classroom. (be) | is |
| `fleng-a0-first-day-extra-2` | Put the words in order to make a sentence: is / notebook / My / the / on / desk | My notebook is on the desk |
| `fleng-a0-first-day-extra-3` | Translate into English: «урок» | lesson |
| `fleng-a0-first-day-extra-4` | Write two sentences about your first day at a new school or course. | Today is my first lesson. My partner is friendly. |
| `fleng-a0-first-day-vocabulary-1` | What is the Ukrainian translation of «class»? | клас |
| `fleng-a0-first-day-vocabulary-2` | Which English expression means «дошка»? | board |
| `fleng-a0-first-day-vocabulary-3` | What is the Ukrainian translation of «eraser»? | гумка |
| `fleng-a0-first-day-vocabulary-4` | Which English expression means «домашнє завдання»? | homework |
| `fleng-a0-first-day-vocabulary-5` | What is the Ukrainian translation of «classmate»? | однокласник |
| `fleng-a0-first-day-vocabulary-6` | Which English expression means «ласкаво просимо до школи»? | welcome to school |
| `fleng-a0-first-day-vocabulary-7` | What is the Ukrainian translation of «excuse me»? | перепрошую |
| `fleng-a0-first-day-vocabulary-8` | Which English expression means «вибачте»? | sorry |
| `fleng-a0-first-day-vocabulary-9` | What is the Ukrainian translation of «see you»? | до зустрічі |
| `fleng-a0-first-day-vocabulary-10` | Which English expression means «допомога»? | help |

## Розширення A0

Чернетка додає позиції 11–15: країни → вказівні слова → календар → ціни → замовлення. На урок 12 слів із власними прикладами, 10 тестових виборів та 4 вправи додаткової практики, із них одна самоперевірка. Разом 60 словникових входжень і 70 вправ, 5 потенційних перших проходів. Статус штатного запуску — пропущено через порожній список дозволених SHA. Колізії зі словниковим доповненням потрібно виправити перед майбутнім імпортом.

### 11. Where are you from?

- **Тема.** Країни й походження (`fleng-a0-origins`).
- **Теорія та словник.** Зрозуміле `Where + be + from`, національність як прикметник і велика літера. 12 прикладів до слів, 4 навчальні зразки, довгий для A0 текст. `my/our/her` потрібні як опора. Текст на 81 слів, 4 приклади, таблиць і українського перекладу теорії немає.
- **Завдання.** Ключі коректні у своїх рамках. MC3 пропонує `I am from Spain. I am from Spain` як граматичну відповідь, яка повторює повідомлення. Попросити прямо назвати національність. У прикладі `Lucia is Spanish` українські глоси національностей потребують жіночих відповідників. `country/city` можна перенести в блок особистих даних.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| country | країна | Ukraine is my country. | Чернетка |
| city | місто | Kyiv is a big city. | Чернетка |
| from | з, родом із | I am from Lviv. | Чернетка |
| Ukraine | Україна | My friend is from Ukraine. | Чернетка |
| Ukrainian | український; українець | He is Ukrainian. | Чернетка |
| Poland | Польща | Marta is from Poland. | Чернетка |
| Polish | польський; поляк | She is Polish. | Чернетка |
| Germany | Німеччина | Our teacher is from Germany. | Чернетка |
| German | німецький; німець | Anna is German. | Чернетка |
| Spain | Іспанія | Lucia is from Spain. | Чернетка |
| Spanish | іспанський; іспанець | Lucia is Spanish. | Чернетка |
| American | американський; американець | Tom is American. | Чернетка |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-origins-practice-1` | Where ___ you from? | are |
| `fleng-a0-origins-practice-2` | She ___ from Poland. | is |
| `fleng-a0-origins-practice-3` | I am from Spain. I am ___. | Spanish |
| `fleng-a0-origins-practice-4` | Choose the correct sentence. | He is from Germany. |
| `fleng-a0-origins-practice-5` | Ukraine is a ___. | country |
| `fleng-a0-origins-practice-6` | Marta is Polish. Where is Marta from? | Poland |
| `fleng-a0-origins-check-1` | Choose the Ukrainian meaning of "country". | країна |
| `fleng-a0-origins-check-2` | Choose the English word for «місто». | city |
| `fleng-a0-origins-check-3` | Which word describes a person? | Polish |
| `fleng-a0-origins-check-4` | A: Where are you from? B: ___ | I am from Ukraine. |
| `fleng-a0-origins-extra-1` | Where ___ they from? (is or are) | are |
| `fleng-a0-origins-extra-2` | Put the words in order to make a sentence: from / is / She / Germany | She is from Germany |
| `fleng-a0-origins-extra-3` | Translate into English: «Я з України» | I am from Ukraine / I'm from Ukraine |
| `fleng-a0-origins-extra-4` | Write two sentences: where you are from and where a friend is from. | I am from Ukraine. My friend is from Poland. |

### 12. This, that, these, those

- **Тема.** Вказівні слова (`fleng-a0-this-that`).
- **Теорія та словник.** Гарна матриця близько/далеко × однина/множина. Правило -es після `ch` подане без обмежень, а є `stomachs`; навчати `watch/watches` як типовий приклад. `phone/lamp/bed/plate/clock/shoe` варто повторювати, не створюючи нові словникові рядки. Текст на 71 слів, 4 приклади, таблиць і українського перекладу теорії немає.
- **Завдання.** П’ять колізій з опублікованим словниковим доповненням: `shoe`, `clock`, `lamp`, `plate`, `bed`. Для `clock` і `shoe` розходяться глоси. `extra-3` приймає `This is/That is`, бо українське «це» не фіксує відстані. Добрий приклад прийняття варіантів, якщо дистанція не є об’єктом тесту.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| phone | телефон | This is my phone. | Чернетка |
| laptop | ноутбук | The laptop is on the desk. | Чернетка |
| shoe | черевик, взуття | This shoe is new. | Чернетка |
| watch | наручний годинник | That is a nice watch. | Чернетка |
| picture | картина, малюнок | That picture is big. | Чернетка |
| clock | настінний годинник | The clock is on the wall. | Чернетка |
| lamp | лампа | This lamp is small. | Чернетка |
| plate | тарілка | That plate is white. | Чернетка |
| towel | рушник | The towel is blue. | Чернетка |
| bed | ліжко | My bed is big. | Чернетка |
| jacket | куртка | Is that your jacket? | Чернетка |
| glasses | окуляри | These are my glasses. | Чернетка |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-this-that-practice-1` | ___ is my laptop. (It is near me.) | This |
| `fleng-a0-this-that-practice-2` | ___ are my shoes. (They are near me.) | These |
| `fleng-a0-this-that-practice-3` | ___ is a lamp on the wall. (It is far from me.) | That |
| `fleng-a0-this-that-practice-4` | Look at ___ pictures on the wall over there. | those |
| `fleng-a0-this-that-practice-5` | Choose the correct sentence. | These are my shoes. |
| `fleng-a0-this-that-practice-6` | one watch, two ___ | watches |
| `fleng-a0-this-that-check-1` | Choose the Ukrainian meaning of "towel". | рушник |
| `fleng-a0-this-that-check-2` | Choose the English word for «тарілка». | plate |
| `fleng-a0-this-that-check-3` | Which word do you use for ONE thing that is FAR from you? | that |
| `fleng-a0-this-that-check-4` | A: Is that your phone? B: ___ | Yes, it is. |
| `fleng-a0-this-that-extra-1` | ___ are my glasses. (They are near me.) | these |
| `fleng-a0-this-that-extra-2` | Put the words in order to make a sentence: is / my / That / jacket | That is my jacket |
| `fleng-a0-this-that-extra-3` | Translate into English: «Це мій телефон» | This is my phone / That is my phone |
| `fleng-a0-this-that-extra-4` | Write two sentences about things near you. Use this and these. | This is my phone. These are my shoes. |

### 13. Days and months

- **Тема.** Дні й місяці (`fleng-a0-days-months`).
- **Теорія та словник.** Природні `on/in` і день народження. Є всі дні в теорії, але лише три місяці в словнику. Випадкові нові слова `free`/`busy` оперти на попередні стани. Правило капіталізації конфліктує з нормалізацією WordSpec. Текст на 60 слів, 4 приклади, таблиць і українського перекладу теорії немає.
- **Завдання.** MC «first month» потребує календарної опори, тоді зміст перевіряється через читання. `extra-3` визнає кілька природних варіантів. Тему календаря краще включити до переходу з A0 до A1 перед часом і розкладом.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| day | день | Today is a good day. | Чернетка |
| week | тиждень | This week is busy. | Чернетка |
| weekend | вихідні | Saturday and Sunday are the weekend. | Чернетка |
| month | місяць | May is a month. | Чернетка |
| birthday | день народження | My birthday is in May. | Чернетка |
| Monday | понеділок | My lesson is on Monday. | Чернетка |
| Wednesday | середа | The English class is on Wednesday. | Чернетка |
| Friday | п’ятниця | On Friday I am with my friends. | Чернетка |
| Sunday | неділя | I am free on Sunday. | Чернетка |
| January | січень | January is cold. | Чернетка |
| May | травень | My birthday is in May. | Чернетка |
| December | грудень | His birthday is in December. | Чернетка |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-days-months-practice-1` | My lesson is ___ Friday. | on |
| `fleng-a0-days-months-practice-2` | My birthday is ___ May. | in |
| `fleng-a0-days-months-practice-3` | Choose the correct sentence. | I am free on Sunday. |
| `fleng-a0-days-months-practice-4` | Saturday and Sunday are the ___. | weekend |
| `fleng-a0-days-months-practice-5` | A: What day is it today? B: ___ | It is Friday. |
| `fleng-a0-days-months-practice-6` | Monday and Friday are ___ of the week. | days |
| `fleng-a0-days-months-check-1` | Choose the Ukrainian meaning of "month". | місяць |
| `fleng-a0-days-months-check-2` | Choose the English word for «день народження». | birthday |
| `fleng-a0-days-months-check-3` | Which month is the first month of the year? | January |
| `fleng-a0-days-months-check-4` | A: Is your birthday in May? B: No, ___ in December. | it is |
| `fleng-a0-days-months-extra-1` | My English lesson is ___ Wednesday. (on or in) | on |
| `fleng-a0-days-months-extra-2` | Put the words in order to make a sentence: is / May / in / birthday / My | My birthday is in May |
| `fleng-a0-days-months-extra-3` | Translate into English: «Сьогодні п’ятниця» | Today is Friday / It is Friday today / It's Friday today / It is Friday / It's Friday |
| `fleng-a0-days-months-extra-4` | Write two sentences: one with on and a day, one with in and a month. | My lesson is on Friday. My birthday is in May. |

### 14. Numbers and prices

- **Тема.** Десятки й ціни (`fleng-a0-prices`).
- **Теорія та словник.** Правильно протиставлено `-teen/-ty` і `is/are` в ціні. У словнику бракує 70/80/90 і проміжних чисел. `one hundred` варто подати як вираз. Немає аудіозавдання на проблемний контраст. Текст на 74 слів, 4 приклади, таблиць і українського перекладу теорії немає.
- **Завдання.** Питання про дешевизну чашки за два євро спирається на суб’єктивну оцінку. Дати дві ціни або явну шкалу. `extra-3` визнає три займенникові чи вказівні рамки, однак пропускає природну форму `That's expensive`. Потрібно уточнити ціль перекладу.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| thirty | тридцять | The lamp is thirty euros. | Чернетка |
| forty | сорок | The bag is forty dollars. | Чернетка |
| fifty | п’ятдесят | The shoes are fifty euros. | Чернетка |
| sixty | шістдесят | The big bag is sixty euros. | Чернетка |
| hundred | сто | The phone is one hundred euros. | Чернетка |
| price | ціна | The price is on the wall. | Чернетка |
| cheap | дешевий | The cup is cheap. | Чернетка |
| expensive | дорогий | The laptop is expensive. | Чернетка |
| dollar | долар | The cup is five dollars. | Чернетка |
| euro | євро | The lamp is thirty euros. | Чернетка |
| money | гроші | This is my money. | Чернетка |
| shop | магазин | The shop is small. | Чернетка |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-prices-practice-1` | How much ___ the lamp? | is |
| `fleng-a0-prices-practice-2` | How much ___ the shoes? | are |
| `fleng-a0-prices-practice-3` | Thirty, forty, ___, sixty. | fifty |
| `fleng-a0-prices-practice-4` | The cup is two euros. It is ___. | cheap |
| `fleng-a0-prices-practice-5` | Choose the correct answer to "How much is it?" | It is sixty euros. |
| `fleng-a0-prices-practice-6` | Choose the number word for 100. | one hundred |
| `fleng-a0-prices-check-1` | Choose the Ukrainian meaning of "price". | ціна |
| `fleng-a0-prices-check-2` | Choose the English word for «дешевий». | cheap |
| `fleng-a0-prices-check-3` | Which number is the biggest? | sixty |
| `fleng-a0-prices-check-4` | A: How much are the shoes? B: ___ | They are fifty euros. |
| `fleng-a0-prices-extra-1` | How much ___ the cup? It is ten euros. (is or are) | is |
| `fleng-a0-prices-extra-2` | Put the words in order to make a sentence: is / much / How / it | How much is it |
| `fleng-a0-prices-extra-3` | Translate into English: «Це дорого» | It is expensive / It's expensive / That is expensive / This is expensive |
| `fleng-a0-prices-extra-4` | Write a price for a cup and a price for a phone. | The cup is ten euros. The phone is one hundred euros. |

### 15. At the café

- **Тема.** Замовлення в кав’ярні (`fleng-a0-cafe`).
- **Теорія та словник.** Сценарій корисний як формула; роз’яснити `a coffee` як порцію і `some water`, не зводити це лише до першого звука. `a cake` у закладі може означати цілий виріб, для порції дати `a slice/piece of cake`. Текст на 74 слів, 4 приклади, таблиць і українського перекладу теорії немає.
- **Завдання.** У `extra-1` `a` потрібне саме через задані варіанти і сенс порції, тоді як `Can I have coffee, please?` природне й дозволене в `extra-3`. Два пункти про відповідь `Thank you` майже дублюються. Практикувати замовлення, уточнення та рахунок у різних ситуаціях.

**Словник**

| EN | UK | Індивідуальний приклад | Джерело |
| --- | --- | --- | --- |
| café | кав’ярня | Anna is in a small café. | Чернетка |
| coffee | кава | Can I have a coffee, please? | Чернетка |
| tea | чай | The tea is good. | Чернетка |
| water | вода | Can I have water, please? | Чернетка |
| juice | сік | The juice is cold. | Чернетка |
| milk | молоко | Can I have milk, please? | Чернетка |
| sandwich | бутерброд | A sandwich is ten euros. | Чернетка |
| cake | торт, тістечко | The cake is good. | Чернетка |
| soup | суп | The soup is warm. | Чернетка |
| menu | меню | Here is the menu. | Чернетка |
| bill | рахунок | Can I have the bill, please? | Чернетка |
| waiter | офіціант | The waiter is happy. | Чернетка |

**Завдання й еталони**

Еталон для самоперевірки наведено як приклад. Повний масив варіантів, ключі та пояснення є у [вивантаженні](10_COURSE_CONTENT.json).

| Ідентифікатор | Завдання | Ключ або модель |
| --- | --- | --- |
| `fleng-a0-cafe-practice-1` | Can I ___ a coffee, please? | have |
| `fleng-a0-cafe-practice-2` | Someone gives you your tea. You say: ___ | Thank you. |
| `fleng-a0-cafe-practice-3` | Choose the polite question. | Can I have the menu, please? |
| `fleng-a0-cafe-practice-4` | At the end you ask for the ___. (It shows the price.) | bill |
| `fleng-a0-cafe-practice-5` | A: Hello. Here is the menu. B: ___ | Thank you. |
| `fleng-a0-cafe-practice-6` | Choose the correct sentence. | Can I have a sandwich, please? |
| `fleng-a0-cafe-check-1` | Choose the Ukrainian meaning of "waiter". | офіціант |
| `fleng-a0-cafe-check-2` | Choose the English word for «сік». | juice |
| `fleng-a0-cafe-check-3` | Which one is a drink? | juice |
| `fleng-a0-cafe-check-4` | A: Can I have a tea, please? B: ___ | Here you are. |
| `fleng-a0-cafe-extra-1` | Can I have ___ coffee, please? (a or an) | a |
| `fleng-a0-cafe-extra-2` | Put the words in order to make a sentence: have / I / Can / the / menu | Can I have the menu |
| `fleng-a0-cafe-extra-3` | Translate into English: «Можна каву, будь ласка?» | Can I have a coffee, please / Can I have coffee, please / Can I have a coffee please / Can I have coffee please |
| `fleng-a0-cafe-extra-4` | Write a short order for a drink and a cake. | Can I have a coffee, please? And can I have a cake, please? |

## Підсумок рівня

Детальні критерії пріоритету, повтори лексики й наскрізні проблеми наведено у [реєстрі проблем](06_PROBLEMS.md). Рекомендований порядок і цілі кожного майбутнього уроку подано в [новій програмі](07_NEW_CURRICULUM.md).
