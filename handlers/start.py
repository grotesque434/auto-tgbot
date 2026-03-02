from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Создать контент")],
        [KeyboardButton(text="📤 Опубликовать на YouTube")],
        [KeyboardButton(text="📊 База данных")],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для создания видеоконтента.\n\n"
        "Что умею:\n"
        "🎬 <b>Создать контент</b> — поиск темы, сценарий, видео, озвучка, субтитры\n"
        "📤 <b>Опубликовать на YouTube</b> — загрузить готовый материал с Google Drive\n"
        "📊 <b>База данных</b> — просмотр всех созданных материалов\n\n"
        "Выбери действие:",
        parse_mode="HTML",
        reply_markup=MAIN_MENU,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Справка</b>\n\n"
        "/start — главное меню\n"
        "/cancel — отменить текущее действие\n\n"
        "<b>Процесс создания контента:</b>\n"
        "1. Введи тему или идею\n"
        "2. Выбери одну из 5 предложенных тем\n"
        "3. Подтверди или отредактируй сценарий\n"
        "4. Подтверди промпт раскадровки\n"
        "5. Выбери тип медиа (видео/изображение)\n"
        "6. Дождись генерации — всё автоматически!\n",
        parse_mode="HTML",
    )
