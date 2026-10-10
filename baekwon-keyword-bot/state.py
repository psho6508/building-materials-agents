"""상태 파일(JSON) 로드/저장.

GitHub Actions 러너는 실행마다 초기화되므로, pending_candidates.json과
telegram_offset.json을 저장소에 커밋해두고 다음 실행에서 다시 읽어온다.
"""

import json

from config import OFFSET_PATH, PENDING_PATH, STATE_DIR


def load_pending() -> dict:
    STATE_DIR.mkdir(exist_ok=True)
    if not PENDING_PATH.exists():
        return {"candidates": {}}
    with open(PENDING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(data: dict):
    STATE_DIR.mkdir(exist_ok=True)
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_offset() -> int:
    if not OFFSET_PATH.exists():
        return 0
    with open(OFFSET_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("offset", 0)


def save_offset(offset: int):
    STATE_DIR.mkdir(exist_ok=True)
    with open(OFFSET_PATH, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f, ensure_ascii=False, indent=2)
