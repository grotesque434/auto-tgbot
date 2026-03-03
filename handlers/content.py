import os
import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from handlers.states import ContentCreation
from services import qwen_service, sora_service, elevenlabs_service, whisper_service
from services import gdrive_service, gsheets_service
from utils import ffmpeg_utils

router = Router()
TEMP_DIR = "temp"


# ── Entry point ───────────────────────────────────────────────────────────────

@router.message(F.text == "🎬 Создать контент")
async def start_content_creation(message: Message, state: FSMContext):
    await state.set_state(ContentCreation.waiting_for_prompt)
    await message.answer(
        "Опиши тему или идею для видео.\n"
        "Например: <i>лайфхаки для продуктивности</i> или <i>интересные факты о космосе</i>",
        parse_mode="HTML",
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import MAIN_MENU
    await message.answer("Действие отменено.", reply_markup=MAIN_MENU)


# ── Step 1: Topic search ──────────────────────────────────────────────────────

@router.message(ContentCreation.waiting_for_prompt)
async def handle_prompt(message: Message, state: FSMContext):
    prompt = message.text.strip()

    # Delete user's message and send single working message
    await message.delete()
    working = await message.answer("⏳ Ищу темы...")

    try:
        topics = await qwen_service.search_topics(prompt)
    except Exception as e:
        await working.edit_text(f"❌ Ошибка при поиске тем: {e}")
        return

    await state.update_data(topics=topics, user_prompt=prompt)
    await state.set_state(ContentCreation.choosing_topic)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{i + 1}. {t}", callback_data=f"topic_{i}")]
        for i, t in enumerate(topics)
    ])
    # Edit working message to show topics — no new message
    await working.edit_text("Выбери тему для видео:", reply_markup=keyboard)


# ── Step 2: Script creation ───────────────────────────────────────────────────

@router.callback_query(ContentCreation.choosing_topic, F.data.startswith("topic_"))
async def handle_topic_choice(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    topic = data["topics"][idx]

    await callback.message.edit_text("⏳ Создаю сценарий...")

    try:
        script = await qwen_service.create_script(topic)
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании сценария: {e}")
        return

    await state.update_data(topic=topic, script=script)
    await state.set_state(ContentCreation.reviewing_script)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data="script_ok"),
        InlineKeyboardButton(text="🔄 Пересоздать", callback_data="script_retry"),
    ]])
    await callback.message.edit_text(
        f"<b>Сценарий:</b>\n\n{script}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(ContentCreation.reviewing_script, F.data == "script_retry")
async def retry_script(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ Пересоздаю сценарий...")

    try:
        script = await qwen_service.create_script(data["topic"])
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
        return

    await state.update_data(script=script)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data="script_ok"),
        InlineKeyboardButton(text="🔄 Пересоздать", callback_data="script_retry"),
    ]])
    await callback.message.edit_text(
        f"<b>Сценарий:</b>\n\n{script}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ── Step 3: Storyboard prompt ─────────────────────────────────────────────────

@router.callback_query(ContentCreation.reviewing_script, F.data == "script_ok")
async def handle_script_ok(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ Создаю промпт раскадровки...")

    try:
        storyboard = await qwen_service.create_storyboard_prompt(data["topic"], data["script"])
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
        return

    await state.update_data(storyboard=storyboard)
    await state.set_state(ContentCreation.reviewing_storyboard)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data="storyboard_ok"),
        InlineKeyboardButton(text="🔄 Пересоздать", callback_data="storyboard_retry"),
    ]])
    await callback.message.edit_text(
        f"<b>Промпт для генерации видео:</b>\n\n<code>{storyboard}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(ContentCreation.reviewing_storyboard, F.data == "storyboard_retry")
async def retry_storyboard(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ Пересоздаю промпт...")

    try:
        storyboard = await qwen_service.create_storyboard_prompt(data["topic"], data["script"])
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
        return

    await state.update_data(storyboard=storyboard)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data="storyboard_ok"),
        InlineKeyboardButton(text="🔄 Пересоздать", callback_data="storyboard_retry"),
    ]])
    await callback.message.edit_text(
        f"<b>Промпт для генерации видео:</b>\n\n<code>{storyboard}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ── Step 4: Choose media type ─────────────────────────────────────────────────

@router.callback_query(ContentCreation.reviewing_storyboard, F.data == "storyboard_ok")
async def handle_storyboard_ok(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ContentCreation.choosing_media_type)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎥 Видео", callback_data="media_video"),
        InlineKeyboardButton(text="🖼 Изображение", callback_data="media_image"),
    ]])
    await callback.message.edit_text("Что генерируем?", reply_markup=keyboard)


# ── Step 5: Generate everything ───────────────────────────────────────────────

@router.callback_query(ContentCreation.choosing_media_type, F.data.startswith("media_"))
async def handle_media_choice(callback: CallbackQuery, state: FSMContext):
    media_type = callback.data.split("_")[1]  # "video" or "image"
    data = await state.get_data()
    await state.set_state(ContentCreation.generating)

    session_id = str(uuid.uuid4())[:8]
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Single progress message — edited through all steps
    progress = callback.message

    media_path = audio_path = merged_path = srt_path = final_path = None

    try:
        # 5a. Generate media
        await progress.edit_text("🎬 [1/6] Генерирую видео (Sora)..." if media_type == "video" else "🖼 [1/6] Генерирую изображение (DALL-E)...")
        if media_type == "video":
            media_path = os.path.join(TEMP_DIR, f"{session_id}_raw.mp4")
            await sora_service.generate_video(data["storyboard"], media_path)
        else:
            media_path = os.path.join(TEMP_DIR, f"{session_id}_image.png")
            await sora_service.generate_image(data["storyboard"], media_path)

        # 5b. Generate voiceover
        await progress.edit_text("🎙 [2/6] Генерирую озвучку (ElevenLabs)...")
        audio_path = os.path.join(TEMP_DIR, f"{session_id}_voice.mp3")
        await elevenlabs_service.generate_voiceover(data["script"], audio_path)

        # 5c. Merge audio + video
        await progress.edit_text("🔗 [3/6] Объединяю аудио и видео...")
        merged_path = os.path.join(TEMP_DIR, f"{session_id}_merged.mp4")
        if media_type == "video":
            await ffmpeg_utils.merge_audio_video(media_path, audio_path, merged_path)
        else:
            await ffmpeg_utils.images_to_video([media_path], audio_path, merged_path)

        # 5d. Subtitles
        await progress.edit_text("📝 [4/6] Генерирую субтитры (Whisper)...")
        segments = await whisper_service.transcribe_audio(audio_path)
        srt_content = whisper_service.segments_to_srt(segments)
        srt_path = os.path.join(TEMP_DIR, f"{session_id}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # 5e. Burn subtitles
        final_path = os.path.join(TEMP_DIR, f"{session_id}_final.mp4")
        await ffmpeg_utils.burn_subtitles(merged_path, srt_path, final_path)

        # 5f. Upload to Google Drive
        await progress.edit_text("☁️ [5/6] Загружаю на Google Drive...")
        image_drive_id = ""
        if media_type == "image":
            img_file = gdrive_service.upload_file(media_path, "image/png")
            image_drive_id = img_file["id"]

        video_file = gdrive_service.upload_file(final_path, "video/mp4")
        video_drive_id = video_file["id"]
        video_link = gdrive_service.get_file_link(video_drive_id)

        # 5g. Save to Google Sheets
        await progress.edit_text("📊 [6/6] Сохраняю в базу данных...")
        record_id = gsheets_service.add_record(
            image_id=image_drive_id,
            video_id=video_drive_id,
            topic=data["topic"],
            script=data["script"],
            storyboard_prompt=data["storyboard"],
            video_link=video_link,
        )

        # Final result — edit progress to result
        await progress.edit_text(
            f"✅ <b>Готово!</b>\n\n"
            f"📌 ID записи: <code>{record_id}</code>\n"
            f"🎬 Тема: {data['topic']}\n"
            f"☁️ <a href='{video_link}'>Видео на Google Drive</a>\n\n"
            f"Для публикации используй <b>📤 Опубликовать на YouTube</b>",
            parse_mode="HTML",
        )

    except Exception as e:
        await progress.edit_text(f"❌ Ошибка при генерации: {e}")

    finally:
        for path in [media_path, audio_path, merged_path, srt_path, final_path]:
            if path and os.path.exists(path):
                os.remove(path)
        await state.clear()
