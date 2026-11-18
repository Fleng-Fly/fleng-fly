"""One clear task instruction for every exercise, in English and Ukrainian.

Derived from the exercise type and the shape of its prompt, so every lesson (including
content authored before instructions existed) gets an explicit "what to do" line.
Instructions describe the task only; they never contain the answer.
"""

from app.db.models import Exercise
from app.modules.exercises.guidance import LocalizedText

_TEXT = {
    "choose_gap": (
        "Choose the word or words that fill the gap (___). Read the whole sentence first.",
        "Виберіть слово або слова, що заповнюють пропуск (___). Спочатку прочитайте все речення.",
    ),
    "choose_question": (
        "Read the question and choose the one correct answer.",
        "Прочитайте запитання й виберіть одну правильну відповідь.",
    ),
    "choose": (
        "Choose the one correct answer.",
        "Виберіть одну правильну відповідь.",
    ),
    "letters": (
        "Build the missing word: tap the letter tiles in the right order to fill each gap.",
        "Складіть пропущене слово: натискайте на літери в правильному порядку.",
    ),
    "type_gap": (
        "Type only the missing word or words for the gap (___). "
        "The hint in brackets tells you what to use.",
        "Введіть лише пропущене слово чи слова (___). Підказка в дужках пояснює, що потрібно.",
    ),
    "word_order": (
        "Use all the given words to write one correct sentence. "
        "Example: am / I / ready → I am ready.",
        "Використайте всі подані слова й напишіть одне правильне речення. "
        "Приклад: am / I / ready → I am ready.",
    ),
    "translate": (
        "Write this word in English. Use one of the new words from this lesson.",
        "Напишіть це слово англійською. Це одне з нових слів цього уроку.",
    ),
    "type": (
        "Type a short answer in English.",
        "Введіть коротку відповідь англійською.",
    ),
    "self_check": (
        "Write your own answer in English. Then compare it with the example "
        "and choose honestly whether you got it right.",
        "Напишіть власну відповідь англійською. Потім порівняйте її з прикладом "
        "і чесно оцініть, чи правильно у вас вийшло.",
    ),
}


def instruction_kind(exercise: Exercise) -> str:
    prompt = exercise.prompt
    if exercise.type == "single_choice":
        if "___" in prompt:
            return "choose_gap"
        return "choose_question" if prompt.rstrip().endswith("?") else "choose"
    if exercise.type == "text":
        if exercise.letter_tiles:
            return "letters"
        if prompt.startswith("Put the words in order"):
            return "word_order"
        if prompt.startswith("Translate into English"):
            return "translate"
        return "type_gap" if "___" in prompt else "type"
    return "self_check"


def instruction_for(exercise: Exercise) -> LocalizedText:
    en, uk = _TEXT[instruction_kind(exercise)]
    return LocalizedText(en=en, uk=uk)
