"""구글 드라이브에 블로그 원고를 구글 문서로 저장한다.

bank-ledger 프로젝트와 동일한 서비스 계정 자격증명 방식을 쓴다
(GOOGLE_SERVICE_ACCOUNT_JSON: 파일 경로 또는 JSON 원문).
해당 서비스 계정 이메일이 대상 폴더에 '편집자'로 공유되어 있어야 한다.
"""

import json
import os

from config import GDRIVE_MANUSCRIPT_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_JSON

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _load_credentials_dict() -> dict:
    raw = GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON 이 설정되지 않았습니다.")
    if os.path.isfile(raw):
        with open(raw, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(raw)


def _build_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        _load_credentials_dict(), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_manuscript(title: str, text: str, folder_id: str = GDRIVE_MANUSCRIPT_FOLDER_ID) -> str:
    """평문 원고를 구글 문서로 변환 업로드하고 webViewLink를 반환한다."""
    from googleapiclient.http import MediaInMemoryUpload

    service = _build_service()
    media = MediaInMemoryUpload(text.encode("utf-8"), mimetype="text/plain")
    file_metadata = {
        "name": title,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.document",
    }
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    return file["webViewLink"]
