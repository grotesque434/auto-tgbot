import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import config

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_service():
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_file(file_path: str, mime_type: str, folder_id: str = None) -> dict:
    """
    Upload a file to Google Drive.
    Returns dict with 'id', 'name', 'webViewLink'.
    """
    service = _get_service()
    folder_id = folder_id or config.GOOGLE_DRIVE_FOLDER_ID

    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id],
    }
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink",
        )
        .execute()
    )

    # Make file accessible via link
    service.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return file


def download_file(file_id: str, output_path: str) -> str:
    """Download a file from Google Drive by its ID."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    service = _get_service()
    request = service.files().get_media(fileId=file_id)

    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return output_path


def get_file_link(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"
