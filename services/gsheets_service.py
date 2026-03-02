from datetime import datetime
import gspread
from google.oauth2 import service_account
from config import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

HEADERS = [
    "ID",
    "ID изображения (Drive)",
    "ID видео (Drive)",
    "Тема",
    "Сюжет",
    "Промпт раскадровки",
    "Дата создания",
    "Статус",
    "Ссылка на видео",
]


def _get_sheet():
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.GOOGLE_SPREADSHEET_ID)
    try:
        worksheet = sh.worksheet(config.GOOGLE_SHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=config.GOOGLE_SHEET_NAME, rows=1000, cols=len(HEADERS))
        worksheet.append_row(HEADERS)
    return worksheet


def add_record(
    image_id: str,
    video_id: str,
    topic: str,
    script: str,
    storyboard_prompt: str,
    video_link: str = "",
) -> int:
    """Add a new content record. Returns the row number (used as content ID)."""
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()
    next_id = len(all_rows)  # header is row 1, so first record gets ID=1

    row = [
        next_id,
        image_id,
        video_id,
        topic,
        script,
        storyboard_prompt,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "В резерве",
        video_link,
    ]
    sheet.append_row(row)
    return next_id


def update_status(record_id: int, status: str, video_link: str = ""):
    """Update status and optionally the YouTube link for a record."""
    sheet = _get_sheet()
    all_rows = sheet.get_all_values()

    for i, row in enumerate(all_rows[1:], start=2):  # skip header
        if row and str(row[0]) == str(record_id):
            # Status is column 8 (index 7), link is column 9 (index 8)
            sheet.update_cell(i, 8, status)
            if video_link:
                sheet.update_cell(i, 9, video_link)
            return True
    return False


def get_all_records() -> list[dict]:
    """Return all records as list of dicts."""
    sheet = _get_sheet()
    return sheet.get_all_records()


def get_record_by_id(record_id: int) -> dict | None:
    """Return a single record by ID."""
    records = get_all_records()
    for rec in records:
        if str(rec.get("ID")) == str(record_id):
            return rec
    return None
