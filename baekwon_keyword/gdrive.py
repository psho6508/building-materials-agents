"""구글 드라이브 읽기/쓰기 — Apps Script 웹앱을 경유한다.

서비스 계정은 개인 Gmail 드라이브에서 저장용량 0GB 문제로 새 파일을 못 만들기
때문에(storageQuotaExceeded), 본인 계정 권한으로 실행되는 구글 Apps Script
웹앱을 '다리'로 사용한다. 설정 방법은 apps_script/Code.gs 참고.
"""

import requests

from config import APPS_SCRIPT_SECRET, APPS_SCRIPT_URL, GDRIVE_MANUSCRIPT_FOLDER_ID


def call_apps_script(action: str, **kwargs) -> dict:
    if not APPS_SCRIPT_URL:
        raise RuntimeError("APPS_SCRIPT_URL 이 설정되지 않았습니다.")

    resp = requests.post(
        APPS_SCRIPT_URL,
        json={"secret": APPS_SCRIPT_SECRET, "action": action, **kwargs},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Apps Script 오류: {data['error']}")
    return data


def upload_manuscript(title: str, text: str, folder_id: str = GDRIVE_MANUSCRIPT_FOLDER_ID) -> str:
    data = call_apps_script("save_manuscript", title=title, text=text, folderId=folder_id)
    return data["url"]
