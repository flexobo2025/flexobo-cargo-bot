"""
Cargo Announcement Bot v2.2 (aiogram 3.x)
==========================================
- Поддержка флагов эмодзи для определения страны
- Несколько грузов в одном сообщении (разбивка на блоки)
- Расширенный словарь городов (альтернативные написания)
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

ADMIN_USERNAME = "flexoboadmin"
INPUT_CHANNEL_USERNAME = "@flexobo_logistic"
INPUT_TOPIC_ID = 1

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

# ─── FLAG EMOJI → COUNTRY ────────────────────────────────────────────────────

FLAG_TO_COUNTRY: dict[str, str] = {
    "🇷🇺": "Россия",
    "🇧🇾": "Беларусь",
    "🇰🇿": "Казахстан",
    "🇹🇷": "Турция",
    "🇵🇱": "Польша",
    "🇦🇿": "Азербайджан",
    "🇺🇿": "Узбекистан",
    "🇨🇳": "Китай",
    "🇱🇹": "Литва",
}

# ─── CITY DATABASE ───────────────────────────────────────────────────────────

CITY_TO_COUNTRY: dict[str, str] = {
    # ── Россия ───────────────────────────────────────────────
    "москва":            "Россия",
    "масква":            "Россия",   # узбекское произношение
    "мск":               "Россия",
    "московская":        "Россия",
    "санкт-петербург":   "Россия",
    "петербург":         "Россия",
    "спб":               "Россия",
    "питер":             "Россия",
    "зеленоград":        "Россия",
    "балашиха":          "Россия",
    "химки":             "Россия",
    "подольск":          "Россия",
    "мытищи":            "Россия",
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
    "тверская":          "Россия",
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
    "березайка":         "Россия",
    "вязьма":            "Россия",
    "клин":              "Россия",
    "тверь":             "Россия",
    "ногинск":           "Россия",
    "электросталь":      "Россия",
    "коломна":           "Россия",
    "серпухов":          "Россия",
    "обнинск":           "Россия",
    "калининград":       "Россия",
    "мурманск":          "Россия",
    "архангельск":       "Россия",
    "вологда":           "Россия",
    "псков":             "Россия",
    "новгород":          "Россия",
    "петрозаводск":      "Россия",
    "сыктывкар":         "Россия",
    "ухта":              "Россия",
    "стерлитамак":       "Россия",
    "шымкент":           "Россия",   # иногда пишут в РФ контексте

    # ── Беларусь ────────────────────────────────────────────
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
    "бобруйск":          "Беларрусь",
    "пинскк":            "Беларусь",
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
    "коnya":             "Турция",
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
    "кок۠­д":            "Узбекистан",
    "маргилан":          "Узбекистан",
    "чирчик":            "Узбекистан",
    "ангрен":            "Узбекистан",
    "алмалык":           "Узбекистан",

    # ── Китай ────────────────────────────────────────────────
    "пекин":             "Китай",
    "шанхаڹ":            "Китай",
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

STOP_WORDS = {
    "груз", "йук", "юк", "товар", "тент", "фура", "сцепка", "реф",
    "тн", "тона", "тонна", "тонн", "кг", "шт", "машин", "штука",
    "аванс", "оплат", "наличн", "срочно", "готов",
}


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_country(city: str) -> Optional[str]:
    norm = _normalize(city)
    if not norm or len(norm) < 2:
        return None
    if norm in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[norm]
    for known, country in CITY_TO_COUNTRY.items():
        if len(known) >= 4 and norm.startswith(known):
            return country
    if len(norm) >= 4:
        for known, country in CITY_TO_COUNTRY.items():
            if known.startswith(norm):
                return country
    return None


def find_flags_in_text(text: str) -> list[tuple[int, int, str, str]]:
    """Находит все флаги в тексте. Возвращает (start, end, flag, country)."""
    result = []
    for flag, country in FLAG_TO_COUNTRY.items():
        for m in re.finditer(re.escape(flag), text):
            result.append((m.start(), m.end(), flag, country))
    result.sort(key=lambda x: x[0])
    return result


def detect_country_from_flags(text: str) -> Optional[str]:
    """
    Определяет страну НАЗНАЧЕНИЯ по флагам в тексте.
    Последний флаг = пункт назначения.
    """
    flags = find_flags_in_text(text)
    if not flags:
        return None
    return flags[-1][3]  # страна последнего флага = куда


def extract_route_display(text: str) -> tuple[str, str]:
    """
    Извлекает откуда/куда используя позиции флагов.
    🇷🇺Березайка Тверская обл 🇺П��Ташкент → ("Березайка Тверская обл", "Ташкент")
    """
    flags = find_flags_in_text(text)

    if len(flags) >= 2:
        _, f1_end, _, _ = flags[0]
        f2_start, f2_end, _, _ = flags[1]

        from_part = text[f1_end:f2_start].strip()
        to_part = text[f2_end:].split("\n")[0].strip()

        from_part = re.sub(r"\s+", " ", from_part)[:60].strip()
        to_part = re.sub(r"\s+", " ", to_part)[:40].strip()

        return from_part or "—", to_part or "—"

    elif len(flags) == 1:
        _, f1_end, _, _ = flags[0]
        to_part = text[f1_end:].split("\n")[0].strip()[:40]
        return "—", to_part or "—"

    return "—", "—"


def split_into_blocks(text: str) -> list[str]:
    """
    Разбивает сообщение на отдельные блоки грузов.
    Сначала пробует по пустым строкам, потом по флагам.
    """
    # Пробуем разбить по пустым строкам
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) > 1:
        return blocks

    # Если пустых строк нет — разбиваем по строкам, начинающимся с флага
    flag_pattern = "|".join(re.escape(f) for f in FLAG_TO_COUNTRY.keys())
    lines = text.split("\n")
    current: list[str] = []
    result: list[str] = []

    for line in lines:
        stripped = line.strip()
        is_new_block = bool(re.match(f"^({flag_pattern})", stripped))
        if is_new_block and current:
            result.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        result.append("\n".join(current))

    blocks = [b.strip() for b in result if b.strip()]
    return blocks if blocks else [text]


# ─── PARSERS ─────────────────────────────────────────────────────────────────

def extract_cities(text: str) -> Optional[tuple[str, str]]:
    """
    Ищет маршрут по городам (без флагов).
    """
    # Убираем флаги и лишние эмодзи
    cleaned = re.sub(r"[\U0001F1E0-\U0001F1FF]", "", text)
    cleaned = re.sub(r"[^\w\s\-–—→\n\.,;:]", " ", cleaned, flags=re.UNICODE)

    lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
    block = "\n".join(lines[:6])

    patterns = [
        r"([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{1,30}?)\s*(?:→|–|—|-{1,2})\s*([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{1,30})(?:\n|$|,)",
        r"([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{1,20}?)\s*дан\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{1,20}?)\s*(?:га|шахрига)(?:\s|$)",
        r"^([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{2,28})\n([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]{2,28})$",
    ]

    for pattern in patterns:
        match = re.search(pattern, block, re.MULTILINE | re.IGNORECASE)
        if not match:
            continue

        from_c = match.group(1).strip().strip("-–— ").strip()
        to_c   = match.group(2).strip().strip("-–— ").strip()

        if from_c.lower() in STOP_WORDS or to_c.lower() in STOP_WORDS:
            continue
        if len(from_c) < 2 or len(to_c) < 2:
            continue
        if detect_country(from_c) is None and detect_country(to_c) is None:
            continue

        return from_c, to_c

    return None


def extract_weight(text: str) -> str:
    patterns = [
        r"(?:до\s+)?([\d]+[.,]?\d*)\s*(тонна|тонн|тона|тон|тн|т)\b",
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
    contacts: list[str] = []

    usernames = re.findall(r"@[a-zA-Z][a-zA-Z0-9_]{3,}", text)
    contacts.extend(usernames)

    phone_re = re.compile(
        r"(?<!\d)(\+\d{1,3}[\s\-]?)[\d][\d\s\-\(\)]{6,16}(?!\d)",
        re.VERBOSE,
    )
    for m in phone_re.finditer(text):
        phone = re.sub(r"\s+", " ", m.group().strip())
        contacts.append(phone)

    already_digits = {re.sub(r"\D", "", c) for c in contacts}
    local_re = re.compile(
        r"\b(8|998|375|994|90|48|370)\s*[\-\(]?\d{2,3}[\)\-\s]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b"
    )
    for m in local_re.finditer(text):
        num = re.sub(r"\s+", " ", m.group().strip())
        digits = re.sub(r"\D", "", num)
        if not any(digits in d or d in digits for d in already_digits):
            contacts.append(num)
            already_digits.add(digits)

    seen: set[str] = set()
    result: list[str] = []
    for c in contacts:
        key = re.sub(r"[\s\-\(\)]", "", c)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result[:3]


def extract_cargo_type(text: str) -> str:
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
    m = re.search(
        r"(\d+)\s*(?:шт\.?|машин[аы]?|фур[аы]?|сцепк[аи]?|та\b|дона\.?)",
        text, re.IGNORECASE,
    )
    return f"{m.group(1)} шт" if m else None


def extract_advance(text: str) -> str:
    tl = text.lower()
    if any(kw in tl for kw in ["аванс есть", "авансом", "с авансом", "аванси бор"]):
        return "✅ Аванс есть"
    if any(kw in tl for kw in ["без аванса", "аванса нет", "авансисиз"]):
        return "❌ Без аванса"
    return ""


def extract_payment(text: str) -> str:
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
    tl = text.lower()
    if any(kw in tl for kw in ["груз готов", "йук тайор", "тайор", "юк тайор"]):
        return "✅ Груз готов"
    if any(kw in tl for kw in ["срочно", "шошилик"]):
        return "🚨 Срочно"
    return ""


# ─── CORE PARSER ─────────────────────────────────────────────────────────────

def parse_cargo(text: str) -> Optional[dict]:
    """
    Парсит один блок объявления.
    Сначала использует флаги эмодзи, затем — базу городов.
    """
    # 1. Пробуем флаги (надёжно для определения страны)
    country_from_flags = detect_country_from_flags(text)

    # 2. Пробуем извлечь города (надёжно для отображения маршрута)
    cities = extract_cities(text)
    from_city = to_city = None
    country_from_cities = None

    if cities:
        from_city, to_city = cities
        country_from_cities = detect_country(from_city) or detect_country(to_city)

    # Итоговая страна
    country = country_from_flags or country_from_cities
    if not country:
        return None  # не можем определить страну — пропускаем

    # Если города не найдены через регексы, используем флаги для отображения
    if not from_city:
        if country_from_flags:
            from_city, to_city = extract_route_display(text)
        else:
            return None

    return {
        "from_city":  from_city,
        "to_city":    to_city or "—",
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
        "Поддерживаю до 8 грузов в одном сообщении!\n\n"
        "<b>Пример формата:</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🇷🇺Москва 🇺П��Ташкент\n"
        "Тент, 22 тн\n"
        "+998-97-713-00-13\n"
        "━━━━━━━━━━━━━━━━━━\n",
        parse_mode="HTML",
        reply_markup=admin_kb,
    )


async def process_message(message: Message, bot: Bot) -> None:
    """
    Обрабатывает сообщения.
    Поддерживает несколько грузов в одном сообщении.
    """
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

    # Разбиваем сообщение на блоки (один блок = один груз)
    blocks = split_into_blocks(message.text)
    logging.info("📦 Найдено блоков: %d", len(blocks))

    posted_count = 0
    for i, block in enumerate(blocks, 1):
        data = parse_cargo(block)
        if not data:
            logging.info("⚠️  Блок %d — маршрут не распознан, пропускаю", i)
            continue

        logging.info(
            "✅ Блок %d: %s → %s  |  Страна: %s",
            i, data["from_city"], data["to_city"], data["country"],
        )

        channel_data = COUNTRY_CHANNELS.get(data["country"])
        if not channel_data:
            logging.warning("❌ Страна '%s' не найдена в COUNTRY_CHANNELS", data["country"])
            continue

        channel, topic_id = channel_data

        try:
            await bot.send_message(
                chat_id=channel,
                message_thread_id=topic_id,
                text=format_post(data),
                parse_mode="HTML",
                reply_markup=contact_keyboard(),
            )
            logging.info(
                "✅ Опубликовано в '%s' (тема %d): %s → %s",
                data["country"], topic_id, data["from_city"], data["to_city"],
            )
            posted_count += 1
        except Exception as exc:
            logging.error("❌ Ошибка публикации в '%s': %s", data["country"], exc)

    if posted_count == 0:
        logging.info("⚠️  Ни один груз не опубликован из сообщения")
    else:
        logging.info("📊 Опубликовано %d/%d объявлений", posted_count, len(blocks))


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
