import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])

    # OpenAI
    OPENAI_API_KEY: str = field(default_factory=lambda: os.environ["OPENAI_API_KEY"])
    OPENAI_MODEL: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))

    # NanaBanana
    NANABANANA_API_KEY: str = field(default_factory=lambda: os.getenv("NANABANANA_API_KEY", ""))
    NANABANANA_BASE_URL: str = field(default_factory=lambda: os.getenv("NANABANANA_BASE_URL", "https://api.nanabanana.ai"))

    # Google Flow
    GOOGLE_FLOW_API_KEY: str = field(default_factory=lambda: os.getenv("GOOGLE_FLOW_API_KEY", ""))
    GOOGLE_FLOW_PROJECT_ID: str = field(default_factory=lambda: os.getenv("GOOGLE_FLOW_PROJECT_ID", ""))

    # ElevenLabs
    ELEVENLABS_API_KEY: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    ELEVENLABS_VOICE_ID: str = field(default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", ""))

    # Google Drive
    GOOGLE_SERVICE_ACCOUNT_JSON: str = field(default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json"))
    GOOGLE_DRIVE_FOLDER_ID: str = field(default_factory=lambda: os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""))

    # Google Sheets
    GOOGLE_SPREADSHEET_ID: str = field(default_factory=lambda: os.getenv("GOOGLE_SPREADSHEET_ID", ""))
    GOOGLE_SHEET_NAME: str = field(default_factory=lambda: os.getenv("GOOGLE_SHEET_NAME", "База"))

    # YouTube
    YOUTUBE_CLIENT_ID: str = field(default_factory=lambda: os.getenv("YOUTUBE_CLIENT_ID", ""))
    YOUTUBE_CLIENT_SECRET: str = field(default_factory=lambda: os.getenv("YOUTUBE_CLIENT_SECRET", ""))
    YOUTUBE_REFRESH_TOKEN: str = field(default_factory=lambda: os.getenv("YOUTUBE_REFRESH_TOKEN", ""))


config = Config()
