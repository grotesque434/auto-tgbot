from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from services import gsheets_service

router = Router()

PAGE_SIZE = 5


@router.message(F.text == "📊 База данных")
async def show_database(message: Message):
    await message.answer("Загружаю данные... ⏳")

    try:
        records = gsheets_service.get_all_records()
    except Exception as e:
        await message.answer(f"Ошибка при загрузке базы: {e}")
        return

    if not records:
        await message.answer("База данных пуста.")
        return

    await _send_records_page(message, records, page=0)


async def _send_records_page(message: Message, records: list[dict], page: int):
    total = len(records)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_records = records[start:end]

    lines = [f"<b>📊 База данных</b> (всего: {total})\n"]
    for rec in page_records:
        status_icon = "✅" if rec.get("Статус") == "Опубликован" else "🗂"
        lines.append(
            f"{status_icon} <b>ID {rec.get('ID')}</b> — {rec.get('Тема', '—')}\n"
            f"   📅 {rec.get('Дата создания', '—')} | {rec.get('Статус', '—')}"
        )

    text = "\n\n".join(lines)

    buttons = []
    # Detail buttons for current page
    detail_row = [
        InlineKeyboardButton(text=f"#{rec.get('ID')}", callback_data=f"db_detail_{rec.get('ID')}")
        for rec in page_records
    ]
    buttons.append(detail_row)

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"db_page_{page - 1}"))
    if end < total:
        nav.append(InlineKeyboardButton(text="Вперёд ▶", callback_data=f"db_page_{page + 1}"))
    if nav:
        buttons.append(nav)

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("db_page_"))
async def handle_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await callback.message.delete()

    try:
        records = gsheets_service.get_all_records()
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        return

    await _send_records_page(callback.message, records, page)


@router.callback_query(F.data.startswith("db_detail_"))
async def handle_detail(callback: CallbackQuery):
    record_id = callback.data.split("_")[-1]

    try:
        rec = gsheets_service.get_record_by_id(record_id)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return

    if not rec:
        await callback.answer("Запись не найдена.", show_alert=True)
        return

    video_id = rec.get("ID видео (Drive)", "")
    from services.gdrive_service import get_file_link
    drive_link = get_file_link(video_id) if video_id else "—"
    yt_link = rec.get("Ссылка на видео", "—") or "—"

    text = (
        f"<b>Запись #{rec.get('ID')}</b>\n\n"
        f"🎬 <b>Тема:</b> {rec.get('Тема', '—')}\n"
        f"📅 <b>Дата:</b> {rec.get('Дата создания', '—')}\n"
        f"📌 <b>Статус:</b> {rec.get('Статус', '—')}\n\n"
        f"☁️ <b>Drive:</b> {drive_link}\n"
        f"▶️ <b>YouTube:</b> {yt_link}\n\n"
        f"<b>Сюжет:</b>\n{rec.get('Сюжет', '—')[:500]}..."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ Назад", callback_data="db_back")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "db_back")
async def handle_back(callback: CallbackQuery):
    await callback.message.delete()
    try:
        records = gsheets_service.get_all_records()
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        return
    await _send_records_page(callback.message, records, page=0)
