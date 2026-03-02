# Auto Content TG Bot

Telegram-бот для автоматизированного создания и публикации видеоконтента на YouTube и TikTok.

## Возможности

- **Поиск темы** — 5 идей для видео по запросу пользователя (ChatGPT)
- **Создание сценария** — готовый скрипт диктора (ChatGPT)
- **Промпт раскадровки** — визуальный промпт для генерации видео (ChatGPT)
- **Генерация медиа** — видео или изображение (NanaBanana)
- **Озвучка** — голос диктора (ElevenLabs)
- **Субтитры** — автоматическая транскрипция и вшивание субтитров (Faster-Whisper + FFmpeg, бесплатно)
- **Хранилище** — готовые материалы сохраняются на Google Drive
- **База данных** — все записи хранятся в Google Sheets (ID, тема, сюжет, дата, статус)
- **Публикация** — загрузка видео на YouTube прямо из бота

## Структура проекта

```
Auto_TGBOT/
├── bot.py                    # Точка входа
├── config.py                 # Конфигурация (читает из .env)
├── requirements.txt
├── .env.example              # Шаблон переменных окружения
├── handlers/
│   ├── states.py             # FSM-состояния
│   ├── start.py              # /start, главное меню
│   ├── content.py            # Полный цикл создания контента
│   ├── database.py           # Просмотр Google Sheets
│   └── publish.py            # Публикация на YouTube
├── services/
│   ├── openai_service.py     # Тема / сценарий / промпт раскадровки
│   ├── nanabanana_service.py # Генерация видео и изображений
│   ├── elevenlabs_service.py # Озвучка
│   ├── whisper_service.py    # Субтитры (Faster-Whisper)
│   ├── gdrive_service.py     # Google Drive
│   ├── gsheets_service.py    # Google Sheets
│   └── youtube_service.py    # YouTube
└── utils/
    └── ffmpeg_utils.py       # Склейка видео/аудио, субтитры
```

## Установка

### 1. Системные зависимости

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. Клонировать репозиторий

```bash
git clone https://github.com/grotesque434/auto-tgbot.git
cd auto-tgbot
```

### 3. Создать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Настроить переменные окружения

```bash
cp .env.example .env
```

Заполни `.env` своими ключами (см. раздел [Необходимые API](#необходимые-api)).

### 6. Добавить Service Account для Google

Положи файл `service_account.json` в корень проекта.

### 7. Запустить бота

```bash
python bot.py
```

## Необходимые API

| Сервис | Что нужно |
|--------|-----------|
| [Telegram](https://t.me/BotFather) | `BOT_TOKEN` |
| [OpenAI](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` |
| [NanaBanana](https://nanabanana.ai) | `NANABANANA_API_KEY` |
| [ElevenLabs](https://elevenlabs.io) | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` |
| [Google Cloud](https://console.cloud.google.com) | Service Account JSON (Drive API + Sheets API) |
| [Google Drive](https://drive.google.com) | `GOOGLE_DRIVE_FOLDER_ID` |
| [Google Sheets](https://sheets.google.com) | `GOOGLE_SPREADSHEET_ID` |
| [YouTube](https://console.cloud.google.com) | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` |

## Структура Google Sheets

Бот автоматически создаёт лист с заголовками:

| ID | ID изображения (Drive) | ID видео (Drive) | Тема | Сюжет | Промпт раскадровки | Дата создания | Статус | Ссылка на видео |
|----|------------------------|------------------|------|-------|-------------------|---------------|--------|-----------------|

## Сценарий работы

```
/start
├── 🎬 Создать контент
│   ├── Введи запрос → 5 тем на выбор
│   ├── Выбор темы → генерация сценария
│   ├── Подтверждение сценария → промпт раскадровки
│   ├── Подтверждение промпта → выбор медиа (видео / изображение)
│   └── Генерация → озвучка → субтитры → Drive → Sheets
│
├── 📤 Опубликовать на YouTube
│   ├── Список материалов в резерве
│   ├── Выбор записи → выбор приватности
│   └── Скачать с Drive → загрузить на YouTube → обновить статус
│
└── 📊 База данных
    └── Постраничный просмотр Google Sheets с деталями
```
