import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from handlers.states import Publishing
from services import gsheets_service, gdrive_service, youtube_service

router = Router()
TEMP_DIR = "temp"


@router.message(F.text == "📤 Опубликовать на YouTube")
async def start_publish(message: Message, state: FSMContext):
    await message.answer("Загружаю список материалов... ⏳")

    try:
        records = gsheets_service.get_all_records()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return

    # Show only unreleased records
    pending = [r for r in records if r.get("Статус") != "Опубликован" and r.get("ID видео (Drive)")]

    if not pending:
        await message.answer("Нет материалов для публикации.\nВсе уже опубликованы или нет готовых видео.")
        return

    await state.set_state(Publishing.choosing_record)
    await state.update_data(records=records)

    lines = ["<b>Выбери материал для публикации:</b>\n"]
    buttons = []
    for rec in pending[:10]:
        lines.append(f"<code>#{rec['ID']}</code> — {rec.get('Тема', '—')}")
        buttons.append([
            InlineKeyboardButton(
                text=f"#{rec['ID']} {rec.get('Тема', '')[:30]}",
                callback_data=f"pub_{rec['ID']}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(Publishing.choosing_record, F.data.startswith("pub_"))
async def handle_record_choice(callback: CallbackQuery, state: FSMContext):
    record_id = callback.data.split("_")[1]
    rec = gsheets_service.get_record_by_id(record_id)

    if not rec:
        await callback.answer("Запись не найдена.", show_alert=True)
        return

    await state.update_data(chosen_record=rec)
    await state.set_state(Publishing.setting_privacy)

    text = (
        f"<b>Публикация #{rec['ID']}</b>\n\n"
        f"🎬 {rec.get('Тема', '—')}\n\n"
        f"Выбери приватность:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 Публичное", callback_data="priv_public"),
            InlineKeyboardButton(text="🔒 Приватное", callback_data="priv_private"),
            InlineKeyboardButton(text="🔗 По ссылке", callback_data="priv_unlisted"),
        ]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(Publishing.setting_privacy, F.data.startswith("priv_"))
async def handle_privacy(callback: CallbackQuery, state: FSMContext):
    privacy = callback.data.split("_")[1]  # public / private / unlisted
    data = await state.get_data()
    rec = data["chosen_record"]

    await callback.message.edit_text(
        f"Загружаю видео с Google Drive и публикую на YouTube...\n"
        f"Приватность: <b>{privacy}</b> ⏳",
        parse_mode="HTML",
    )

    video_id = rec.get("ID видео (Drive)", "")
    if not video_id:
        await callback.message.answer("❌ Видео не найдено в Google Drive.")
        await state.clear()
        return

    os.makedirs(TEMP_DIR, exist_ok=True)
    local_path = os.path.join(TEMP_DIR, f"yt_upload_{rec['ID']}.mp4")

    try:
        # Download from Google Drive
        await callback.message.answer("⬇️ Скачиваю с Google Drive...")
        gdrive_service.download_file(video_id, local_path)

        # Upload to YouTube
        await callback.message.answer("⬆️ Загружаю на YouTube...")
        result = youtube_service.upload_video(
            video_path=local_path,
            title=rec.get("Тема", "Видео"),
            description=rec.get("Сюжет", "")[:5000],
            privacy=privacy,
        )

        # Update Google Sheets
        gsheets_service.update_status(
            record_id=rec["ID"],
            status="Опубликован",
            video_link=result["url"],
        )

        await callback.message.answer(
            f"✅ <b>Опубликовано!</b>\n\n"
            f"▶️ <a href='{result['url']}'>Смотреть на YouTube</a>\n"
            f"📱 <a href='{result['shorts_url']}'>YouTube Shorts</a>",
            parse_mode="HTML",
        )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при публикации: {e}")

    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
        await state.clear()
