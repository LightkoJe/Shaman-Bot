import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keep_alive import keep_alive

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOKEN       = os.getenv("BOT_TOKEN")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "0"))
GROUP_LINK  = os.getenv("GROUP_LINK", "https://t.me/+XXXXXXXXXX")

# Claude API (подключается позже)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-sonnet-4-5"
MAX_HISTORY       = 8   # максимум сообщений в истории диалога
MAX_MESSAGES      = 50  # лимит сообщений в текстовом тарифе в месяц

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
bot    = Bot(token=TOKEN)
router = Router()

# ─── STATES ───────────────────────────────────────────────────────────────────
class Diagnosis(StatesGroup):
    q1 = State()   # Вопрос 1
    q2 = State()   # Вопрос 2
    q3 = State()   # Вопрос 3

class TextTariff(StatesGroup):
    chatting = State()  # Платный текстовый диалог

# ─── IN-MEMORY STORAGE ────────────────────────────────────────────────────────
# Хранит историю диалога и счётчики сообщений
# Формат: { user_id: { "history": [...], "msg_count": int } }
user_data: dict = {}

def get_user(user_id: int) -> dict:
    if user_id not in user_data:
        user_data[user_id] = {"history": [], "msg_count": 0, "paid": False}
    return user_data[user_id]

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────
def kb_main_menu():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🔮 Диагностика Сознания", callback_data="start_diagnosis"))
    b.row(types.InlineKeyboardButton(text="💬 Диалог с Евгением",    callback_data="info_text"))
    b.row(types.InlineKeyboardButton(text="🎙 Голос Евгения",        callback_data="info_audio"))
    b.row(types.InlineKeyboardButton(text="🎥 Послание Евгения",     callback_data="info_video"))
    b.row(types.InlineKeyboardButton(text="🔒 Круг Проводников",     callback_data="info_group"))
    return b.as_markup()

def kb_back():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu"))
    return b.as_markup()

def kb_after_diagnosis():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="💬 Продолжить в диалоге", callback_data="info_text"))
    b.row(types.InlineKeyboardButton(text="🎙 Продолжить голосом",   callback_data="info_audio"))
    b.row(types.InlineKeyboardButton(text="🎥 Продолжить в видео",   callback_data="info_video"))
    b.row(types.InlineKeyboardButton(text="⬅️ Главное меню",         callback_data="main_menu"))
    return b.as_markup()

def kb_pay_text():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="✅ Получить доступ (тест)", callback_data="pay_text_confirm"))
    b.row(types.InlineKeyboardButton(text="⬅️ Назад",                  callback_data="main_menu"))
    return b.as_markup()

def kb_pay_group():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="✅ Получить доступ (тест)", callback_data="pay_group_confirm"))
    b.row(types.InlineKeyboardButton(text="⬅️ Назад",                  callback_data="main_menu"))
    return b.as_markup()

def kb_stop_chat():
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🏁 Завершить диалог", callback_data="stop_chat"))
    return b.as_markup()

# ─── CLAUDE API (ЗАГЛУШКА) ────────────────────────────────────────────────────
async def ask_claude_diagnosis(answers: list[str]) -> str:
    """
    TODO: Подключить Claude API.
    Принимает 3 ответа пользователя из диагностики,
    возвращает персональное зеркало в стиле Евгения Чуклова.

    Когда будет готов промпт:
    1. Раскомментировать импорт anthropic
    2. Заменить заглушку на реальный вызов API
    3. Системный промпт — в SYSTEM_PROMPT ниже

    SYSTEM_PROMPT = '''
    Ты — Евгений Чуклов, проводник к открытию Сознания. Бренд Global Resonance.
    Твоя задача — дать человеку персональное зеркало на основе его трёх ответов.
    Говори тепло, глубоко, от сердца. Используй его лексику:
    Сознание, Božičb, АЗМЪ ЕСМЪ, Создатель, Свет, внутреннее начало, размотка, проводник.
    Зеркало — это НЕ решение проблемы, а отражение паттерна и направление.
    В конце — мягкий призыв к следующему шагу (платный формат).
    Подписывай: "Обнял сердцем 🫶"
    Максимум 200 слов.
    '''
    """

    # ── ЗАГЛУШКА (убрать когда подключим Claude) ──
    q1, q2, q3 = answers
    return (
        f"Я слышу тебя, Сознание ☀️\n\n"
        f"Ты сказал: *\"{q2}\"*\n\n"
        f"В этом я вижу глубокий паттерн — твоё внутреннее начало уже знает ответ, "
        f"но слои программ и отождествлений пока не дают ему проявиться полностью.\n\n"
        f"Это не слабость — это точка входа. Именно отсюда начинается настоящая размотка.\n\n"
        f"Ты готов идти глубже? Выбери формат продолжения — я здесь 🫶\n\n"
        f"Обнял сердцем 🫶"
    )


async def ask_claude_chat(user_id: int, user_message: str) -> str:
    """
    TODO: Подключить Claude API для платного текстового тарифа.
    Берёт историю диалога пользователя (последние MAX_HISTORY сообщений),
    добавляет новое сообщение, возвращает ответ Claude.

    Когда будет готов:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=history[-MAX_HISTORY:]
    )
    return response.content[0].text
    """

    # ── ЗАГЛУШКА ──
    ud = get_user(user_id)
    count = ud["msg_count"]
    return (
        f"[Режим прототипа — Claude API будет подключён]\n\n"
        f"Ты написал: *\"{user_message}\"*\n\n"
        f"Здесь будет живой ответ в голосе Евгения Чуклова — "
        f"тёплый, глубокий, из внутреннего начала.\n\n"
        f"Сообщений использовано: {count} из {MAX_MESSAGES} 🌟"
    )


# ─── ВАЛИДАЦИЯ ОТВЕТОВ ДИАГНОСТИКИ ───────────────────────────────────────────
def is_relevant_answer(text: str) -> bool:
    """Простая проверка — ответ содержит хоть какой-то смысл."""
    if len(text.strip()) < 5:
        return False
    # Явно нерелевантные паттерны
    noise = ["я плаваю", "я ем", "я сплю", "тест", "привет", "hi", "hello", "123", "ааа"]
    low = text.lower().strip()
    for n in noise:
        if low == n:
            return False
    return True

def is_crisis_message(text: str) -> bool:
    """Проверка на медицинский/кризисный запрос."""
    crisis_words = ["рак", "онкология", "умираю", "умру", "суицид", "самоубийство",
                    "операция", "инфаркт", "инсульт", "скорая", "реанимация"]
    low = text.lower()
    return any(w in low for w in crisis_words)

# ─── HANDLERS: START & MENU ───────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет, Сознание ☀️\n\n"
        "Ко мне каждый день приходят люди с разными запросами — "
        "но корень всегда один: непонимание того, *Кто Ты Есть*.\n\n"
        "Это не просто слова. Это ключ ко всему — к здоровью, отношениям, деньгам, свободе.\n\n"
        "Я проводник. Моя задача — помочь тебе увидеть своё истинное начало и выйти на свой Путь Света.\n\n"
        "Начни с бесплатной *Диагностики Сознания* — три вопроса, и ты увидишь себя иначе.\n\n"
        "Обнял сердцем 🫶",
        reply_markup=kb_main_menu(),
        parse_mode="Markdown"
    )

@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выбери раздел 👇", reply_markup=kb_main_menu())

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Выбери раздел 👇", reply_markup=kb_main_menu())

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выбери раздел 👇",
        reply_markup=kb_main_menu()
    )
    await callback.answer()

# ─── HANDLERS: ИНФО О ТАРИФАХ ────────────────────────────────────────────────
@router.callback_query(F.data == "info_text")
async def cb_info_text(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💬 *Диалог с Евгением*\n\n"
        "Не каждому я открываю этот формат.\n\n"
        "Это живой диалог — я отвечаю лично, из потока, без шаблонов. "
        "Ты пишешь свой запрос, я даю тебе точное зеркало — туда, где настоящая причина.\n\n"
        "Не совет. Не инструкция. Живое присутствие проводника рядом.\n\n"
        "• До 50 сообщений в месяц\n"
        "• Персональные ответы в моём голосе\n"
        "• Стоимость: уточняется\n\n"
        "_Доступ открывается — напиши первый вопрос_ 👇",
        reply_markup=kb_pay_text(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "info_audio")
async def cb_info_audio(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎙 *Голос Евгения*\n\n"
        "Есть вещи которые невозможно передать текстом.\n\n"
        "Голосовое послание — это моя интонация, моя энергия, мой поток. "
        "Ты слушаешь — и что-то внутри начинает резонировать. "
        "Так работает настоящая передача.\n\n"
        "• До 20 голосовых в месяц\n"
        "• Голос Евгения — живой, не записанный заранее\n"
        "• Стоимость: уточняется\n\n"
        "_Этот формат открывается скоро_ 🔜",
        reply_markup=kb_back(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "info_video")
async def cb_info_video(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎥 *Послание Евгения*\n\n"
        "Смотришь — и чувствуешь живое присутствие.\n\n"
        "Видео-послание это не контент. Это прямая передача через взгляд, слово и состояние. "
        "Я вижу тебя — и ты это почувствуешь.\n\n"
        "• До 10 посланий в месяц\n"
        "• Персональное видео от Евгения\n"
        "• Стоимость: уточняется\n\n"
        "_Этот формат открывается позже_ 🔜",
        reply_markup=kb_back(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "info_group")
async def cb_info_group(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔒 *Круг Проводников*\n\n"
        "Это не просто группа. Это пространство тех, кто уже сделал выбор — идти к Свету.\n\n"
        "Здесь я работаю с каждым напрямую. Практики, разборы, сонастройки. "
        "Те кто внутри — меняются. Я вижу это каждый раз.\n\n"
        "Попасть сюда — значит признать своё внутреннее начало и быть готовым к размотке.\n\n"
        "• Прямой доступ к Евгению\n"
        "• Практики пробуждения Сознания\n"
        "• Сообщество Проводников\n"
        "• Стоимость: уточняется\n\n",
        reply_markup=kb_pay_group(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ─── HANDLERS: ОПЛАТА (ЗАГЛУШКИ) ─────────────────────────────────────────────
@router.callback_query(F.data == "pay_text_confirm")
async def cb_pay_text(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    ud = get_user(user_id)
    ud["paid"] = True
    ud["msg_count"] = 0

    await callback.message.edit_text(
        "✅ *Доступ открыт.*\n\n"
        "Я здесь. Пиши — без фильтров, из глубины.\n"
        "Я отвечу из потока — точно и честно.\n\n"
        "_/menu — вернуться в меню_",
        parse_mode="Markdown"
    )
    await state.set_state(TextTariff.chatting)
    await callback.answer()

    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"💰 НОВЫЙ ДОСТУП (Текстовый тариф)\n"
            f"👤 @{callback.from_user.username or '—'} (ID: {user_id})"
        )

@router.callback_query(F.data == "pay_group_confirm")
async def cb_pay_group(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        f"✅ *Ты внутри.*\n\n"
        f"🔒 Ссылка на Круг Проводников:\n{GROUP_LINK}\n\n"
        f"До встречи в пространстве. Обнял сердцем 🫶"
    )
    await callback.answer()

    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"💰 НОВЫЙ ДОСТУП (Закрытая группа)\n"
            f"👤 @{callback.from_user.username or '—'} (ID: {user_id})"
        )

# ─── HANDLERS: ДИАГНОСТИКА ────────────────────────────────────────────────────
DIAGNOSIS_QUESTIONS = [
    "Скажи мне — *что в твоей жизни прямо сейчас ощущается как главный барьер или тяжесть?*\n\n"
    "_Напиши честно, как есть. Я здесь._",

    "Хорошо. Второй вопрос — *чего ты по-настоящему хочешь? Не снаружи, а изнутри?*\n\n"
    "_Что для тебя настоящая свобода и счастье?_",

    "И последнее — *что, как тебе кажется, мешает тебе быть тем, кем ты на самом деле являешься?*\n\n"
    "_Ответь так, как чувствуешь._"
]

@router.callback_query(F.data == "start_diagnosis")
async def cb_start_diagnosis(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔮 *Диагностика Сознания*\n\n"
        "Три вопроса — и ты увидишь себя иначе.\n"
        "Отвечай честно, из глубины. Нет правильных ответов.\n\n"
        + DIAGNOSIS_QUESTIONS[0],
        parse_mode="Markdown",
        reply_markup=kb_back()
    )
    await state.set_state(Diagnosis.q1)
    await callback.answer()

@router.message(Diagnosis.q1)
async def diag_q1(message: types.Message, state: FSMContext):
    text = message.text or ""

    if is_crisis_message(text):
        await message.answer(
            "Я слышу боль в твоих словах. 🙏\n\n"
            "Я не врач и не заменю медицинскую помощь — пожалуйста, обратись к специалисту.\n\n"
            "Но я здесь чтобы помочь тебе найти внутреннюю опору. "
            "Расскажи — *что сейчас происходит именно с тобой внутри?*",
            parse_mode="Markdown"
        )
        return

    if not is_relevant_answer(text):
        await message.answer(
            "Я хочу понять тебя по-настоящему 🙂\n\n"
            "*Что в твоей жизни прямо сейчас ощущается как главный барьер или тяжесть?*\n\n"
            "_Напиши своими словами, как есть._",
            parse_mode="Markdown"
        )
        return

    await state.update_data(q1=text)
    await message.answer(DIAGNOSIS_QUESTIONS[1], parse_mode="Markdown")
    await state.set_state(Diagnosis.q2)

@router.message(Diagnosis.q2)
async def diag_q2(message: types.Message, state: FSMContext):
    text = message.text or ""

    if is_crisis_message(text):
        await message.answer(
            "Слышу тебя. Сначала — позаботься о физическом здоровье, обратись к врачу.\n\n"
            "А пока — *чего ты по-настоящему хочешь изнутри?*",
            parse_mode="Markdown"
        )
        return

    if not is_relevant_answer(text):
        await message.answer(
            "Чувствую, ты ещё не до конца раскрылся 🙂\n\n"
            "*Чего ты по-настоящему хочешь? Не снаружи, а изнутри?*",
            parse_mode="Markdown"
        )
        return

    await state.update_data(q2=text)
    await message.answer(DIAGNOSIS_QUESTIONS[2], parse_mode="Markdown")
    await state.set_state(Diagnosis.q3)

@router.message(Diagnosis.q3)
async def diag_q3(message: types.Message, state: FSMContext):
    text = message.text or ""

    if is_crisis_message(text):
        await message.answer(
            "Слышу тебя. Позаботься о здоровье — это первично.\n\n"
            "*Что мешает тебе быть собой?* Ответь из внутреннего состояния.",
            parse_mode="Markdown"
        )
        return

    if not is_relevant_answer(text):
        await message.answer(
            "Ещё один шаг 🙂\n\n"
            "*Что, как тебе кажется, мешает тебе быть тем, кем ты на самом деле являешься?*",
            parse_mode="Markdown"
        )
        return

    await state.update_data(q3=text)
    data = await state.get_data()
    answers = [data.get("q1", ""), data.get("q2", ""), data.get("q3", "")]

    await message.answer("Принимаю... ☀️", parse_mode="Markdown")

    # Получаем ответ от Claude (или заглушку)
    response = await ask_claude_diagnosis(answers)

    await message.answer(
        response,
        reply_markup=kb_after_diagnosis(),
        parse_mode="Markdown"
    )
    await state.clear()

    # Уведомление админу
    if ADMIN_ID:
        user = message.from_user
        await bot.send_message(
            ADMIN_ID,
            f"🔮 ДИАГНОСТИКА ПРОЙДЕНА\n"
            f"👤 @{user.username or '—'} (ID: {user.id})\n\n"
            f"1️⃣ {answers[0]}\n"
            f"2️⃣ {answers[1]}\n"
            f"3️⃣ {answers[2]}"
        )

# ─── HANDLERS: ТЕКСТОВЫЙ ТАРИФ ───────────────────────────────────────────────
@router.callback_query(F.data == "stop_chat")
async def cb_stop_chat(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Диалог завершён ☀️\n\n"
        "Возвращайся когда будешь готов идти глубже.\n"
        "Обнял сердцем 🫶",
        reply_markup=kb_main_menu()
    )
    await callback.answer()

@router.message(TextTariff.chatting)
async def handle_chat(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    ud = get_user(user_id)

    # Проверка лимита
    if ud["msg_count"] >= MAX_MESSAGES:
        await message.answer(
            "☀️ На этот месяц твои сообщения исчерпаны.\n\n"
            "Это не конец — это точка паузы. Ты уже сделал шаг.\n"
            "Для продолжения — обнови доступ.",
            reply_markup=kb_main_menu()
        )
        await state.clear()
        return

    text = message.text or ""
    ud["msg_count"] += 1

    # Добавляем в историю
    ud["history"].append({"role": "user", "content": text})
    if len(ud["history"]) > MAX_HISTORY:
        ud["history"] = ud["history"][-MAX_HISTORY:]

    # Получаем ответ
    response = await ask_claude_chat(user_id, text)

    # Сохраняем ответ в историю
    ud["history"].append({"role": "assistant", "content": response})

    await message.answer(
        response,
        reply_markup=kb_stop_chat(),
        parse_mode="Markdown"
    )

# ─── FALLBACK ─────────────────────────────────────────────────────────────────
@router.message()
async def fallback(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer(
            "Выбери раздел 👇",
            reply_markup=kb_main_menu()
        )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    logging.info("Бот Global Resonance запущен...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Горячие кнопки (меню слева от поля ввода)
    await bot.set_my_commands([
        types.BotCommand(command="start",  description="☀️ Начать / Приветствие"),
        types.BotCommand(command="menu",   description="📋 Главное меню"),
        types.BotCommand(command="cancel", description="❌ Отменить действие"),
    ])

    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
