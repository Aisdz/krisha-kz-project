import asyncio
import logging
import os
import pandas as pd
from dotenv import load_dotenv  # Импортируем dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from predict import predict

# =====================================================
# CONFIG — автозагрузка секретов из .env
# =====================================================
load_dotenv()  # Загружает BOT_TOKEN из файла .env в переменные окружения

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Критическая ошибка: Переменная BOT_TOKEN не найдена в файле .env")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

TOTAL_STEPS_PREDICT = 9
TOTAL_STEPS_AUDIT   = 10


# =====================================================
# ДАННЫЕ ДЛЯ КНОПОК
# =====================================================

CITIES = ["Алматы", "Астана", "Шымкент", "Караганда"]

DISTRICTS = {
    "Алматы": [
        "Алмалинский", "Ауэзовский", "Бостандыкский",
        "Жетысуский", "Медеуский", "Наурызбайский",
        "Турксибский", "Алатауский"
    ],
    "Астана": [
        "Алматинский", "Байконыр", "Есиль",
        "Нура", "Сарыарка", "Алматы"
    ],
    "Шымкент": [
        "Аль-Фараби", "Енбекшинский", "Каратауский", "Туран"
    ],
    "Караганда": [
        "Казыбек би", "Октябрьский"
    ],
}

BUILDING_OPTIONS = [
    ("🧱 Кирпичный",    "кирпичный"),
    ("🏗 Панельный",    "панельный"),
    ("🏢 Монолитный",   "монолитный"),
    ("🪵 Деревянный",   "деревянный"),
    ("❓ Не знаю",      "неизвестно"),
]

TOILET_OPTIONS = [
    ("🚿 Раздельный",   "раздельный"),
    ("🛁 Совмещённый",  "совмещенный"),
    ("🚽 Два и более",  "два и более"),
]

RENOVATION_OPTIONS = [
    ("✨ Евроремонт",      "евроремонт"),
    ("👍 Хорошее",         "хорошее"),
    ("🔨 Среднее",         "среднее"),
    ("🏚 Требует ремонта", "требует ремонта"),
    ("🏗 Черновая",        "черновая отделка"),
]

YEAR_OPTIONS = [
    ("до 1970",   1960),
    ("1970–1990", 1980),
    ("1990–2000", 1995),
    ("2000–2010", 2005),
    ("2010–2015", 2012),
    ("2015–2019", 2017),
    ("2019–2023", 2021),
    ("2023+",     2024),
]

# =====================================================
# STATES
# =====================================================

class Form(StatesGroup):
    city         = State()
    district     = State()
    rooms        = State()
    square       = State()
    floor        = State()   # НОВОЕ: этаж и всего этажей
    building     = State()   # НОВОЕ: тип здания
    year         = State()   # НОВОЕ: год постройки
    toilet       = State()
    renovation   = State()
    seller_price = State()

# =====================================================
# KEYBOARDS
# =====================================================

def main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Оценить квартиру")
    kb.button(text="🕵️ Проверить цену")
    kb.button(text="ℹ️ О боте")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)

def city_keyboard():
    kb = InlineKeyboardBuilder()
    for city in CITIES:
        kb.button(text=city, callback_data=f"city_{city}")
    kb.adjust(2)
    return kb.as_markup()

def district_keyboard(city: str):
    kb = InlineKeyboardBuilder()
    for d in DISTRICTS.get(city, []):
        kb.button(text=d, callback_data=f"district_{d}")
    kb.button(text="🔍 Другой / не знаю", callback_data="district_неизвестно")
    kb.adjust(2)
    return kb.as_markup()

def rooms_keyboard():
    kb = InlineKeyboardBuilder()
    for r in ["1", "2", "3", "4", "5+"]:
        kb.button(text=r, callback_data=f"rooms_{r}")
    kb.adjust(5)
    return kb.as_markup()

def building_keyboard():
    kb = InlineKeyboardBuilder()
    for label, value in BUILDING_OPTIONS:
        kb.button(text=label, callback_data=f"building_{value}")
    kb.adjust(2)
    return kb.as_markup()

def year_keyboard():
    kb = InlineKeyboardBuilder()
    for label, value in YEAR_OPTIONS:
        kb.button(text=label, callback_data=f"year_{value}")
    kb.adjust(2)
    return kb.as_markup()

def toilet_keyboard():
    kb = InlineKeyboardBuilder()
    for label, value in TOILET_OPTIONS:
        kb.button(text=label, callback_data=f"toilet_{value}")
    kb.adjust(1)
    return kb.as_markup()

def renovation_keyboard():
    kb = InlineKeyboardBuilder()
    for label, value in RENOVATION_OPTIONS:
        kb.button(text=label, callback_data=f"renovation_{value}")
    kb.adjust(2)
    return kb.as_markup()

def price_keyboard(current: int):
    kb = InlineKeyboardBuilder()
    increments = [
        ("+1М",   1_000_000),
        ("+5М",   5_000_000),
        ("+10М", 10_000_000),
        ("+50М", 50_000_000),
        ("-1М",  -1_000_000),
        ("-5М",  -5_000_000),
    ]
    for label, delta in increments:
        kb.button(text=label, callback_data=f"price_{delta}")
    kb.button(text="✅ Подтвердить", callback_data="price_confirm")
    kb.button(text="🔄 Сбросить",    callback_data="price_reset")
    kb.adjust(2)
    return kb.as_markup()

def fmt_price(val: int) -> str:
    return f"{val / 1_000_000:.1f}М ₸"

def step_header(step: int, total: int, emoji: str, title: str) -> str:
    bar = "▓" * step + "░" * (total - step)
    return f"{emoji} <b>Шаг {step}/{total}</b> — {title}\n<code>{bar}</code>\n\n"

# =====================================================
# START / HELP
# =====================================================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Krisha ML Bot</b>\n\n"
        "Оцениваю квартиры по данным krisha.kz с помощью XGBoost модели.\n\n"
        "Выберите режим:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ О боте")
async def help_handler(message: Message):
    await message.answer(
        "🤖 <b>Krisha ML Bot — справка</b>\n\n"
        "📊 <b>Оценить квартиру</b> — модель назовёт рыночную стоимость\n"
        "🕵️ <b>Проверить цену</b> — сравним цену продавца с оценкой модели\n\n"
        "<b>Как работает:</b>\n"
        "Модель обучена на объявлениях с krisha.kz. "
        "Точность: R²=0.87, средняя ошибка ~7М ₸.\n\n"
        "⚠️ Оценка является ориентировочной. "
        "Финальная цена зависит от конкретной локации и состояния квартиры.\n\n"
        "/start — вернуться в главное меню",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

# =====================================================
# MAIN MENU
# =====================================================

@dp.message(F.text == "📊 Оценить квартиру")
async def mode_predict(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(mode="predict")
    await state.set_state(Form.city)
    await message.answer(
        step_header(1, TOTAL_STEPS_PREDICT, "📍", "Выберите город"),
        reply_markup=city_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🕵️ Проверить цену")
async def mode_audit(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(mode="audit")
    await state.set_state(Form.city)
    await message.answer(
        step_header(1, TOTAL_STEPS_AUDIT, "📍", "Выберите город"),
        reply_markup=city_keyboard(),
        parse_mode="HTML"
    )

# =====================================================
# CITY → DISTRICT
# =====================================================

@dp.callback_query(F.data.startswith("city_"))
async def city_handler(callback: CallbackQuery, state: FSMContext):
    city = callback.data.replace("city_", "")
    await state.update_data(city=city)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    await state.set_state(Form.district)
    await callback.message.edit_text(
        f"✅ Город: <b>{city}</b>\n\n" +
        step_header(2, total, "📍", "Выберите район"),
        reply_markup=district_keyboard(city),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# DISTRICT → ROOMS
# =====================================================

@dp.callback_query(F.data.startswith("district_"))
async def district_handler(callback: CallbackQuery, state: FSMContext):
    district = callback.data.replace("district_", "")
    await state.update_data(district=district)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    label = district if district != "неизвестно" else "не указан"
    await state.set_state(Form.rooms)
    await callback.message.edit_text(
        f"✅ Район: <b>{label}</b>\n\n" +
        step_header(3, total, "🛏", "Количество комнат"),
        reply_markup=rooms_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# ROOMS → SQUARE
# =====================================================

@dp.callback_query(F.data.startswith("rooms_"))
async def rooms_handler(callback: CallbackQuery, state: FSMContext):
    rooms_str = callback.data.replace("rooms_", "")
    rooms = 5 if rooms_str == "5+" else int(rooms_str)
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    await state.set_state(Form.square)
    await callback.message.edit_text(
        f"✅ Комнат: <b>{rooms_str}</b>\n\n" +
        step_header(4, total, "📐", "Введите площадь в м²") +
        "Пример: <code>65.5</code>",
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# SQUARE → FLOOR
# =====================================================

@dp.message(Form.square)
async def square_handler(message: Message, state: FSMContext):
    try:
        square = float(message.text.replace(",", "."))
        if not (10 < square < 1000):
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(
            "❌ Введите корректную площадь от 10 до 1000 м²\n"
            "Пример: <code>65.5</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(square=square)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    await state.set_state(Form.floor)
    await message.answer(
        f"✅ Площадь: <b>{square} м²</b>\n\n" +
        step_header(5, total, "🏢", "Этаж квартиры") +
        "Введите через слэш: <b>этаж / всего этажей</b>\n"
        "Пример: <code>5/9</code>  или  <code>3/16</code>",
        parse_mode="HTML"
    )

# =====================================================
# FLOOR → BUILDING
# =====================================================

@dp.message(Form.floor)
async def floor_handler(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "")
    try:
        parts = text.replace("\\", "/").split("/")
        floor       = int(parts[0])
        total_floors = int(parts[1])
        if floor < 1 or total_floors < 1 or floor > total_floors or total_floors > 50:
            raise ValueError
    except (ValueError, TypeError, IndexError):
        await message.answer(
            "❌ Введите этаж в формате <b>этаж/всего</b>\n"
            "Пример: <code>5/9</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(floor=floor, total_floors=total_floors)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    await state.set_state(Form.building)
    await message.answer(
        f"✅ Этаж: <b>{floor} из {total_floors}</b>\n\n" +
        step_header(6, total, "🧱", "Тип здания"),
        reply_markup=building_keyboard(),
        parse_mode="HTML"
    )

# =====================================================
# BUILDING → YEAR
# =====================================================

@dp.callback_query(F.data.startswith("building_"))
async def building_handler(callback: CallbackQuery, state: FSMContext):
    building = callback.data.replace("building_", "")
    await state.update_data(building=building)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    label = next((l for l, v in BUILDING_OPTIONS if v == building), building)
    await state.set_state(Form.year)
    await callback.message.edit_text(
        f"✅ Здание: <b>{label}</b>\n\n" +
        step_header(7, total, "📅", "Год постройки дома"),
        reply_markup=year_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# YEAR → TOILET
# =====================================================

@dp.callback_query(F.data.startswith("year_"))
async def year_handler(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.replace("year_", ""))
    await state.update_data(year=year)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    label = next((l for l, v in YEAR_OPTIONS if v == year), str(year))
    await state.set_state(Form.toilet)
    await callback.message.edit_text(
        f"✅ Год постройки: <b>{label}</b>\n\n" +
        step_header(8, total, "🚽", "Санузел"),
        reply_markup=toilet_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# TOILET → RENOVATION
# =====================================================

@dp.callback_query(F.data.startswith("toilet_"))
async def toilet_handler(callback: CallbackQuery, state: FSMContext):
    toilet = callback.data.replace("toilet_", "")
    await state.update_data(toilet=toilet)
    data = await state.get_data()
    total = TOTAL_STEPS_AUDIT if data["mode"] == "audit" else TOTAL_STEPS_PREDICT
    label = next((l for l, v in TOILET_OPTIONS if v == toilet), toilet)
    await state.set_state(Form.renovation)
    await callback.message.edit_text(
        f"✅ Санузел: <b>{label}</b>\n\n" +
        step_header(9, total, "🔨", "Состояние ремонта"),
        reply_markup=renovation_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================
# RENOVATION → PRICE (audit) или PREDICT
# =====================================================

@dp.callback_query(F.data.startswith("renovation_"))
async def renovation_handler(callback: CallbackQuery, state: FSMContext):
    renovation = callback.data.replace("renovation_", "")
    await state.update_data(renovation=renovation)
    label = next((l for l, v in RENOVATION_OPTIONS if v == renovation), renovation)
    data = await state.get_data()

    if data["mode"] == "audit":
        await state.update_data(seller_price=10_000_000)
        await state.set_state(Form.seller_price)
        await callback.message.edit_text(
            f"✅ Ремонт: <b>{label}</b>\n\n"
            f"{step_header(10, TOTAL_STEPS_AUDIT, '💰', 'Цена продавца')}"
            f"Текущее значение: <b>{fmt_price(10_000_000)}</b>\n\n"
            "Используйте кнопки <b>или напишите сумму</b> (например: <code>35000000</code>):",
            reply_markup=price_keyboard(10_000_000),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"✅ Ремонт: <b>{label}</b>\n\n⏳ Считаю оценку...",
            parse_mode="HTML"
        )
        await run_prediction(callback.message, state)

    await callback.answer()

# =====================================================
# SELLER PRICE — кнопки инкремента + ввод текстом
# =====================================================

@dp.callback_query(Form.seller_price, F.data.startswith("price_"))
async def price_button_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("price_", "")
    data = await state.get_data()
    current = data.get("seller_price", 10_000_000)

    if action == "confirm":
        await callback.message.edit_text(
            f"✅ Цена продавца: <b>{fmt_price(current)}</b>\n\n⏳ Считаю...",
            parse_mode="HTML"
        )
        await run_prediction(callback.message, state)
        await callback.answer()
        return

    if action == "reset":
        current = 10_000_000
    else:
        delta = int(action)
        current = max(1_000_000, current + delta)

    await state.update_data(seller_price=current)
    await callback.message.edit_text(
        f"{step_header(10, TOTAL_STEPS_AUDIT, '💰', 'Цена продавца')}"
        f"Текущее значение: <b>{fmt_price(current)}</b>\n\n"
        "Используйте кнопки <b>или напишите сумму</b> (например: <code>35000000</code>):",
        reply_markup=price_keyboard(current),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(Form.seller_price)
async def price_text_handler(message: Message, state: FSMContext):
    """Ввод цены продавца текстом."""
    try:
        raw = message.text.replace(" ", "").replace(",", "").replace(".", "")
        val = int(raw)
        if not (500_000 <= val <= 5_000_000_000):
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(
            "❌ Введите сумму числом, например: <code>35000000</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(seller_price=val)
    await message.answer(
        f"✅ Принято: <b>{fmt_price(val)}</b>\n\n"
        "Нажмите <b>✅ Подтвердить</b> или продолжайте корректировать:",
        reply_markup=price_keyboard(val),
        parse_mode="HTML"
    )

# =====================================================
# PREDICT
# =====================================================

async def run_prediction(message: Message, state: FSMContext):
    data = await state.get_data()

    floor        = data.get("floor", 3)
    total_floors = data.get("total_floors", 9)
    floor_str    = f"{floor} из {total_floors}"

    city_district = f"{data['city']}, {data.get('district', 'неизвестно')}"

    df = pd.DataFrame({
        'комнаты':         [data['rooms']],
        'город':           [city_district],
        'flat.floor':      [floor_str],
        'live.square':     [f"{data['square']} м²"],
        'ceiling':         ['2.7 м'],
        'flat.security':   ['домофон'],
        'flat.building':   [data.get('building', 'монолитный')],
        'house.year':      [data.get('year', 2010)],
        'flat.toilet':     [data.get('toilet', 'совмещенный')],
        'flat.balcony':    ['балкон'],
        'flat.door':       ['металлическая'],
        'flat.parking':    ['рядом'],
        'live.furniture':  ['частично'],
        'flat.flooring':   ['ламинат'],
        'flat.priv_dorm':  ['нет'],
        'has_change':      ['нет'],
        'flat.renovation': [data.get('renovation', 'хорошее')],
    })

    try:
        pred = predict(df)
        predicted_price = int(pred[0])
    except Exception as e:
        logging.exception("Ошибка модели")
        await message.answer(
            f"❌ Ошибка модели:\n<code>{e}</code>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Диапазон ±10% (примерная погрешность модели)
    low  = int(predicted_price * 0.90)
    high = int(predicted_price * 1.10)

    district_label  = data.get('district', 'неизвестно')
    building_label  = next((l for l, v in BUILDING_OPTIONS  if v == data.get('building')),  data.get('building', '—'))
    toilet_label    = next((l for l, v in TOILET_OPTIONS    if v == data.get('toilet')),    data.get('toilet', '—'))
    renov_label     = next((l for l, v in RENOVATION_OPTIONS if v == data.get('renovation')), data.get('renovation', '—'))
    year_label      = next((l for l, v in YEAR_OPTIONS      if v == data.get('year')),      str(data.get('year', '—')))

    # Формируем базовый текст с характеристиками и ценой
    text = (
        "🏠 <b>РЕЗУЛЬТАТ ОЦЕНКИ</b>\n\n"
        f"📍 {data['city']}, {district_label}\n"
        f"🛏 Комнат: {data['rooms']}\n"
        f"📐 Площадь: {data['square']} м²\n"
        f"🏢 Этаж: {floor} из {total_floors}\n"
        f"🧱 Здание: {building_label}\n"
        f"📅 Год постройки: {year_label}\n"
        f"🚽 Санузел: {toilet_label}\n"
        f"🔨 Ремонт: {renov_label}\n\n"
        f"💎 <b>Оценка модели:</b>\n"
        f"<b>{fmt_price(predicted_price)}</b>  ({predicted_price:,} ₸)\n"
        f"<i>Диапазон: {fmt_price(low)} — {fmt_price(high)}</i>\n\n"
    )

    if data["mode"] == "audit":
        seller_price = data["seller_price"]
        percent = (seller_price - predicted_price) / predicted_price * 100
        text += f"\n\n💰 <b>Цена продавца:</b> {fmt_price(seller_price)}\n"

        if percent > 15:
            text += f"🔴 <b>ПЕРЕОЦЕНЕНО</b> на {percent:.1f}% — торгуйтесь!"
        elif percent > 5:
            text += f"🟠 Немного выше рынка (+{percent:.1f}%)"
        elif percent < -15:
            text += f"🟢 <b>ХОРОШАЯ ЦЕНА</b> — ниже рынка на {abs(percent):.1f}%!"
        elif percent < -5:
            text += f"🟢 Чуть ниже рынка ({percent:.1f}%)"
        else:
            text += "🟡 Цена соответствует рынку"

    await message.answer(text, reply_markup=main_keyboard(), parse_mode="HTML")
    await state.clear()

# =====================================================
# FALLBACK
# =====================================================

@dp.message()
async def fallback_handler(message: Message):
    await message.answer(
        "Выберите действие или нажмите /start",
        reply_markup=main_keyboard()
    )

# =====================================================
# MAIN
# =====================================================

async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())