"""
Cargo Announcement Bot v2.1 (aiogram 3.x)
==========================================
Парсит объявления о грузах из темы 1 канала @flexobo_logistic
и публикует в нужную тему по стране с кнопкой «Показать контакт».

Установка:
    pip install aiogram==3.7.0 python-dotenv

Запуск:
    python bot_new.py
"""

import asyncio
import logging
import os
import re
from typing import Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавь токен в .env файл")

# Username администратора (без @) — появляется в кнопке «Показать контакт»
ADMIN_USERNAME = "flexoboadmin"

# Канал и тема, откуда принимаем объявления
INPUT_CHANNEL_USERNAME = "@flexobo_logistic"
INPUT_TOPIC_ID = 1  # Тема 1 — «Общий» / первая тема

# ─── COUNTRY → CHANNEL TOPICS ────────────────────────────────────────────────

COUNTRY_CHANNELS: dict[str, tuple[str, int]] = {
    "Россия":      ("@flexobo_logistic", 1026),
    "Беларусь":    ("@flexobo_logistic", 1019),
    "Казахстан":   ("@flexobo_logistic", 1023),
    "Турция":      ("@flexobo_logistic", 1017),
    "Польша":      ("@flexobo_logistic", 1028),
    "Азербайджан": ("@flexobo_logistic", 1013),
    "Узбекистан":  ("@flexobo_logistic", 1040),
    "Китай":       ("@flexobo_logistic", 1038),
    "Литва":       ("@flexobo_logistic", 1036),
}

# ─── CITY DATABASE ───────────────────────────────────────────────────────────

# Ключ: нижний регистр, без лишних пробелов  →  Страна
CITY_TO_COUNTRY: dict[str, str] = {
    # ── Россия ───────────────────────────────────────────────
    "москва":            "Россия",
    "санкт-петербург":   "Россия",
    "петербург":         "Россия",
    "спб":               "Россия",
    "питер":             "Россия",
    "воронеж":           "Россия",
    "новосибирск":       "Россия",
    "екатеринбург":      "Россия",
    "краснодар":         "Россия",
    "ростов":            "Россия",
    "казань":            "Россия",
    "уфа":               "Россия",
    "пермь":             "Россия",
    "самара":            "Россия",
    "омск":              "Россия",
    "муром":             "Россия",
    "йошкар-ола":        "Россия",
    "йошкар":            "Россия",
    "нижний новгород":   "Россия",
    "нижний":            "Россия",
    "тюмень":            "Россия",
    "барнаул":           "Россия",
    "иркутск":           "Россия",
    "хабаровск":         "Россия",
    "владивосток":       "Россия",
    "красноярск":        "Россия",
    "саратов":           "Россия",
    "липецк":            "Россия",
    "тула":              "Россия",
    "рязань":            "Россия",
    "пенза":             "Россия",
    "курск":             "Россия",
    "белгород":          "Россия",
    "орёл":              "Россия",
    "орел":              "Россия",
    "брянск":            "Россия",
    "смоленск":          "Россия",
    "калуга":            "Россия",
    "тверь":             "Россия",
    "ярославль":         "Россия",
    "иваново":           "Россия",
    "кострома":          "Россия",
    "владимир":          "Россия",
    "челябинск":         "Россия",
    "магнитогорск":      "Россия",
    "оренбург":          "Россия",
    "ижевск":            "Россия",
    "киров":             "Россия",
    "чебоксары":         "Россия",
    "ульяновск":         "Россия",
    "волгоград":         "Россия",
    "астрахань":         "Россия",
    "сочи":              "Россия",
    "ставрополь":        "Россия",
    "махачкала":         "Россия",
    "нальчик":           "Россия",
    "владикавказ":       "Россия",
    "тольятти":          "Россия",
    "набережные челны":  "Россия",
    "набережные":        "Россия",

    # ── Беларусь ─────────────────────────────────────────────
    "минск":             "Беларусь",
    "брест":             "Беларусь",
    "гродно":            "Беларусь",
    "гомель":            "Беларусь",
    "витебск":           "Беларусь",
    "могилёв":           "Беларусь",
    "могилев":           "Беларусь",
    "борисов":           "Беларусь",
    "мосты":             "Беларусь",
    "лида":              "Беларусь",
    "барановичи":        "Беларусь",
    "бобруйск":          "Беларусь",
    "пинск":             "Беларусь",
    "орша":              "Беларусь",
    "слуцк":             "Беларусь",
    "молодечно":         "Беларусь",
    "жодино":            "Беларусь",
    "солигорск":         "Беларусь",

    # ── Казахстан ────────────────────────────────────────────
    "алматы":            "Казахстан",
    "алма-ата":          "Казахстан",
    "астана":            "Казахстан",
    "нур-султан":        "Казахстан",
    "нурсултан":         "Казахстан",
    "шымкент":           "Казахстан",
    "актобе":            "Казахстан",
    "актюбинск":         "Казахстан",
    "костанай":          "Казахстан",
    "павлодар":          "Казахстан",
    "усть-каменогорск":  "Казахстан",
    "семей":             "Казахстан",
    "тараз":             "Казахстан",
    "кызылорда":         "Казахстан",
    "атырау":            "Казахстан",
    "актау":             "Казахстан",
    "уральск":           "Казахстан",
    "петропавловск":     "Казахстан",
    "темиртау":          "Казахстан",
    "экибастуз":         "Казахстан",

    # ── Турция ───────────────────────────────────────────────
    "стамбул":           "Турция",
    "анкара":            "Турция",
    "измир":             "Турция",
    "коня":              "Турция",
    "бурса":             "Турция",
    "газиантеп":         "Турция",
    "мерсин":            "Турция",
    "адана":             "Турция",
    "трабзон":           "Турция",
    "анталья":           "Турция",
    "эскишехир":         "Турция",
    "кайсери":           "Турция",
    "самсун":            "Турция",

    # ── Польша ───────────────────────────────────────────────
    "варшава":           "Польша",
    "краков":            "Польша",
    "гданьск":           "Польша",
    "лодзь":             "Польша",
    "вроцлав":           "Польша",
    "познань":           "Польша",
    "катовице":          "Польша",
    "белосток":          "Польша",
    "люблин":            "Польша",
    "щецин":             "Польша",

    # ── Азербайджан ──────────────────────────────────────────
    "баку":              "Азербайджан",
    "гянджа":            "Азербайджан",
    "сумгаит":           "Азербайджан",
    "мингечаур":         "Азербайджан",
    "нахчыван":          "Азербайджан",
    "ленкорань":         "Азербайджан",
    "шамахы":            "Азербайджан",

    # ── Узбекистан ───────────────────────────────────────────
    "ташкент":           "Узбекистан",
    "тошкент":           "Узбекистан",
    "тошкэнт":           "Узбекистан",
    "самарканд":         "Узбекистан",
    "самарқанд":         "Узбекистан",
    "наманган":          "Узбекистан",
    "андижан":           "Узбекистан",
    "фергана":           "Узбекистан",
    "бухара":            "Узбекистан",
    "бухоро":            "Узбекистан",
    "ургенч":            "Узбекистан",
    "нукус":             "Узбекистан",
    "карши":             "Узбекистан",
    "хоразм":            "Узбекистан",
    "хорезм":            "Узбекистан",
    "навои":             "Узбекистан",
    "термез":            "Узбекистан",
    "гулистан":          "Узбекистан",
    "жиззах":            "Узбекистан",
    "сырдарья":          "Узбекистан",
    "коканд":            "Узбекистан",
    "маргилан":          "Узбекистан",
    "чирчик":            "Узбекистан",
    "ангрен":            "Узбекистан",
    "алмалык":           "Узбекистан",

    # ── Китай ────────────────────────────────────────────────
    "пекин":             "Китай",
    "шанхай":            "Китай",
    "гуанчжоу":          "Китай",
    "шэньчжэнь":         "Китай",
    "урумчи":            "Китай",
    "кашгар":            "Китай",
    "ухань":             "Китай",
    "чэнду":             "Китай",
    "чунцин":            "Китай",

    # ── Литва ────────────────────────────────────────────────
    "вильнюс":           "Литва",
    "каунас":            "Литва",
    "клайпеда":          "Литва",
    "шяуляй":            "Литва",
    "паневежис":         "Литва",
}

# Стоп-слова — никогда не считать их городами
STOP_WORDS = {
    "груз", "йук", "юк", "товар", "тент", "фура", "сцепка", "реф",
    "тн", "тона", "тонна", "тонн", "кг", "шт", "машин", "штука",
    "аванс", "оплат", "наличн", "срочно", "готов",
}


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Нижний регистр, убираем лишние пробелы и символы."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_country(city: str) -> Optional[str]:
    """
    Определяет страну по названию города.
    Использует точное совпадение, затем совпадение по префиксу (≥4 символа).
    Возвращает None, если город не найден.
    """
    norm = _normalize(city)
    if not norm or len(norm) < 2:
        return None

    # 1. Точное совпадение
    if norm in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[norm]

    # 2. Префиксный поиск: запрос начинается с известного города (≥4 симв.)
    for known, country in CITY_TO_COUNTRY.items():
        if len(known) >= 4 and norm.startswith(known):
            return country

    # 3. Префиксный поиск в обратную сторону: известный город начинается с запроса (≥4 симв.)
    if len(norm) >= 4:
        for known, country in CITY_TO_COUNTRY.items():
            if known.startswith(norm):
                return country

    return None


# ─── PARSERS ─────────────────────────────────────────────────────────────────

def extract_cities(text: str) -> Optional[tuple[str, str]]:
    """
    Ищет маршрут «откуда → куда» в первых 5 строках.
    Поддерживает: «-», «–», «—», «→», узбекский «дан … га».
    Возвращает (from_city, to_city) или None.
    """
    # Убираем Unicode-флаги и лишние эмодзи
    cleaned = re.sub(r"[\U0001F1E0-\U0001F1FF]", "", text)
    cleaned = re.sub(r"[^\w\s\-–—→\n\.,;:]", " ", cleaned, flags=re.UNICODE)

    lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
    block = "\n".join(lines[:6])

    patterns = [
        # Явный разделитель: «Город1 - Город2» / «Город1 → Город2»
        r"([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{1,30}?)\s*(?:→|–|—|-{1,2})\s*([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{1,30})(?:\n|$|,)",
        # Узбекский: «Ташкентдан Москвага» или «Ташкент дан Москва га»
        r"([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{1,20}?)\s*дан\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{1,20}?)\s*(?:га|шахрига)(?:\s|$)",
        # Два города на разных строках (только буквы+дефис, каждый ≥3 символа)
        r"^([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{2,28})\n([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{2,28})$",
    ]

    for pattern in patterns:
        match = re.search(pattern, block, re.MULTILINE | re.IGNORECASE)
        if not match:
            continue

        from_c = match.group(1).strip().strip("-–— ").strip()
        to_c   = match.group(2).strip().strip("-–— ").strip()

        # Фильтрация стоп-слов
        if from_c.lower() in STOP_WORDS or to_c.lower() in STOP_WORDS:
            continue
        if len(from_c) < 2 or len(to_c) < 2:
            continue

        # Хотя бы один город должен быть в базе
        if detect_country(from_c) is None and detect_country(to_c) is None:
            continue

        return from_c, to_c

    return None


def extract_weight(text: str) -> str:
    """
    Извлекает вес груза. Единица измерения ОБЯЗАТЕЛЬНА —
    иначе возвращает «не указан» (во избежание ложных срабатываний на телефоны).
    """
    patterns = [
        # «22 тн», «5.5 тонна», «22.5 тоннa», «до 20 тон»
        r"(?:до\s+)?([\d]+[.,]?\d*)\s*(тонна|тонн|тона|тон|тн|т)\b",
        # «100 кг»
        r"([\d]+[.,]?\d*)\s*(кг|kg)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val  = m.group(1).replace(",", ".")
            unit = "кг" if re.search(r"кг|kg", m.group(2), re.IGNORECASE) else "т"
            return f"{val} {unit}"
    return "не указан"


def extract_phones(text: str) -> list[str]:
    """
    Извлекает телефоны и @username.
    Требует чёткий формат телефона — не ловит вес, даты и пр.
    """
    contacts: list[str] = []

    # @username (≥4 символа после @, начинается с буквы)
    usernames = re.findall(r"@[a-zA-Z][a-zA-Z0-9_]{3,}", text)
    contacts.extend(usernames)

    # Телефоны с + или с кодом страны (7, 8, 998, 375, 994, 90, 48, 370...)
    phone_re = re.compile(
        r"(?<!\d)"                          # нет цифры перед
        r"(\+\d{1,3}[\s\-]?)"              # код страны с +
        r"[\d][\d\s\-\(\)]{6,16}"          # тело номера
        r"(?!\d)",                          # нет цифры после
        re.VERBOSE,
    )
    for m in phone_re.finditer(text):
        phone = re.sub(r"\s+", " ", m.group().strip())
        contacts.append(phone)

    # Номера без +: 8xxxxxxxxxx или 998xxxxxxx
    # Пропускаем если этот же номер уже есть (с учётом + в начале)
    already_digits = {re.sub(r"\D", "", c) for c in contacts}
    local_re = re.compile(
        r"\b(8|998|375|994|90|48|370)\s*[\-\(]?\d{2,3}[\)\-\s]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b"
    )
    for m in local_re.finditer(text):
        num = re.sub(r"\s+", " ", m.group().strip())
        digits = re.sub(r"\D", "", num)
        # Не добавляем если уже есть (совпадение хвоста номера)
        if not any(digits in d or d in digits for d in already_digits):
            contacts.append(num)
            already_digits.add(digits)

    # Убираем дубликаты
    seen: set[str] = set()
    result: list[str] = []
    for c in contacts:
        key = re.sub(r"[\s\-\(\)]", "", c)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result[:3]


def extract_cargo_type(text: str) -> str:
    """Определяет тип кузова/транспорта."""
    tl = text.lower()
    types = [
        ("Сцепка",       ["сцепка", "сцепки"]),
        ("Рефрижератор", ["рефрижератор", "рефка", "реф "]),
        ("Тент",         ["тент"]),
        ("Открытый",     ["открытый", "открыт"]),
        ("Контейнер",    ["контейнер"]),
        ("Фура",         ["фура", "паровоз", "паравоз"]),
    ]
    for name, keywords in types:
        if any(kw in tl for kw in keywords):
            return name
    return "Груз"


def extract_quantity(text: str) -> Optional[str]:
    """Извлекает количество машин/единиц."""
    m = re.search(
        r"(\d+)\s*(?:шт\.?|машин[аы]?|фур[аы]?|сцепк[аи]?|та\b|дона\.?)",
        text, re.IGNORECASE,
    )
    return f"{m.group(1)} шт" if m else None


def extract_advance(text: str) -> str:
    """Определяет наличие аванса."""
    tl = text.lower()
    if any(kw in tl for kw in ["аванс есть", "авансом", "с авансом", "аванси бор"]):
        return "✅ Аванс есть"
    if any(kw in tl for kw in ["без аванса", "аванса нет", "авансисиз"]):
        return "❌ Без аванса"
    return ""


def extract_payment(text: str) -> str:
    """Извлекает тип оплаты."""
    tl = text.lower()
    if "100%" in text:
        if "перечисл" in tl:
            return "💳 100% перечисление"
        if "нал" in tl:
            return "💰 100% наличные"
        return "💵 100% оплата"
    if any(kw in tl for kw in ["наличн", "нал", "нақд"]):
        return "💰 Наличные"
    if any(kw in tl for kw in ["перечисл", "безнал"]):
        return "💳 Перечисление"
    return ""


def extract_status(text: str) -> str:
    """Извлекает статус срочности."""
    tl = text.lower()
    if any(kw in tl for kw in ["груз готов", "йук тайор", "тайор"]):
        return "✅ Груз готов"
    if any(kw in tl for kw in ["срочно", "шошилик"]):
        return "🚨 Срочно"
    return ""


# ─── CORE PARSER ─────────────────────────────────────────────────────────────

def parse_cargo(text: str) -> Optional[dict]:
    """
    Главная функция: разбирает текст объявления.
    Возвращает словарь с данными или None, если маршрут не распознан.
    """
    cities = extract_cities(text)
    if not cities:
        return None

    from_city, to_city = cities

    # Страна: сначала по городу отправления, затем — назначения
    country = detect_country(from_city) or detect_country(to_city)
    if not country:
        return None  # не угадываем — лучше пропустить

    return {
        "from_city":  from_city,
        "to_city":    to_city,
        "country":    country,
        "cargo_type": extract_cargo_type(text),
        "weight":     extract_weight(text),
        "quantity":   extract_quantity(text),
        "contacts":   extract_phones(text),
        "advance":    extract_advance(text),
        "payment":    extract_payment(text),
        "status":     extract_status(text),
    }


# ─── FORMATTER ───────────────────────────────────────────────────────────────

_CARGO_EMOJI = {
    "Сцепка":       "🚛",
    "Рефрижератор": "❄️",
    "Тент":         "🏕️",
    "Открытый":     "📦",
    "Контейнер":    "🟦",
    "Фура":         "🚚",
    "Груз":         "📦",
}


def format_post(data: dict) -> str:
    """Формирует красивый пост для публикации в канале."""
    from_city  = data["from_city"].title()
    to_city    = data["to_city"].title()
    cargo_type = data["cargo_type"]
    emoji      = _CARGO_EMOJI.get(cargo_type, "📦")

    lines = [
        f"🗺 <b>{from_city} → {to_city}</b>\n",
        f"{emoji} <b>Кузов:</b> {cargo_type}",
    ]

    if data["quantity"]:
        lines.append(f"🔢 <b>Кол-во:</b> {data['quantity']}")

    lines.append(f"⚖️ <b>Вес:</b> {data['weight']}")

    if data["status"]:
        lines.append(f"📋 {data['status']}")

    if data["payment"]:
        lines.append(f"{data['payment']}")

    if data["advance"]:
        lines.append(data["advance"])

    if data["contacts"]:
        lines.append(f"\n📞 {'  |  '.join(data['contacts'][:2])}")

    tag = re.sub(r"[^\w]", "", from_city, flags=re.UNICODE)
    lines.append(f"\n#{tag} #груз #логистика")

    return "\n".join(lines)


def contact_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопка «Показать контакт» → аккаунт администратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="📞 Показать контакт",
                url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}",
            )
        ]]
    )


# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def cmd_start(message: Message) -> None:
    """Команда /start."""
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="👨‍💼 Связаться с администратором",
                url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}",
            )
        ]]
    )
    await message.answer(
        "👋 <b>Привет!</b> Я бот для публикации объявлений о грузоперевозках.\n\n"
        f"📍 Отправляй объявления в тему 1 канала:\n"
        f"https://t.me/flexobo_logistic/1\n\n"
        "Я автоматически:\n"
        "✅ Распознаю города и страну\n"
        "✅ Опубликую в правильную тему канала\n\n"
        "<b>Пример формата:</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Ташкент - Воронеж\n"
        "Сцепка\n"
        "22 тн\n"
        "+998-97-713-00-13\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 Просто отправляй текст в тему 1!",
        parse_mode="HTML",
        reply_markup=admin_kb,
    )


async def process_message(message: Message, bot: Bot) -> None:
    """
    Обрабатывает сообщения из темы 1 канала.

    Важно про thread_id в Telegram:
      - Тема «Общий» (первая) — message_thread_id == 1 или None
      - Остальные темы — message_thread_id == их ID (1013, 1017, ...)
    """
    # Только super-группы (каналы с темами)
    if message.chat.type != "supergroup":
        return

    thread_id = message.message_thread_id

    # Принимаем только из входящей темы (1 или None = "Общий")
    if thread_id is not None and thread_id != INPUT_TOPIC_ID:
        return

    if not message.text:
        return

    logging.info(
        "📨 msg_id=%s  thread=%s  chat=%s",
        message.message_id, thread_id, message.chat.username,
    )

    data = parse_cargo(message.text)
    if not data:
        logging.info("⚠️  Не удалось распознать маршрут — пропускаю")
        return

    logging.info(
        "✅ Маршрут: %s → %s  |  Страна: %s",
        data["from_city"], data["to_city"], data["country"],
    )

    channel_data = COUNTRY_CHANNELS.get(data["country"])
    if not channel_data:
        logging.warning("❌ Страна '%s' не найдена в COUNTRY_CHANNELS", data["country"])
        return

    channel, topic_id = channel_data

    try:
        await bot.send_message(
            chat_id=channel,
            message_thread_id=topic_id,
            text=format_post(data),
            parse_mode="HTML",
            reply_markup=contact_keyboard(),   # ← кнопка «Показать контакт»
        )
        logging.info(
            "✅ Опубликовано в '%s' (тема %d): %s → %s",
            data["country"], topic_id, data["from_city"], data["to_city"],
        )
    except Exception as exc:
        logging.error("❌ Ошибка публикации в '%s': %s", data["country"], exc)


# ─── MAIN ────────────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(process_message)

    logging.info("🤖 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Бот запущен! Ожидаю сообщений из темы %d...", INPUT_TOPIC_ID)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
